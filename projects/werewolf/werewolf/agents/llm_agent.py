# ==================== LLM Agent ====================
"""基于 LLM 的智能 Agent"""

from __future__ import annotations
import json
import logging
from typing import TYPE_CHECKING, Optional, List, Dict, Any

from werewolf.agents.base import BaseAgent
from werewolf.core.enums import ActionType
from werewolf.core.events import Action
from werewolf.llm.base import BaseLLMClient, Message, ToolCall
from werewolf.llm.tools import get_tool_definitions
from werewolf.prompts.system import build_system_prompt
from werewolf.prompts.role_prompts import get_role_prompt
from werewolf.prompts.templates import (
    format_game_state,
    format_player_info,
    format_history,
    format_action_prompt,
)

if TYPE_CHECKING:
    from werewolf.core.game import Game

logger = logging.getLogger(__name__)


class LLMAgent(BaseAgent):
    """
    LLM Agent

    使用大语言模型进行决策的智能 Agent。
    支持 ReAct 模式：多轮思考 + 工具调用。
    """

    def __init__(
        self,
        player_id: int,
        game: Game,
        llm_client: BaseLLMClient,
        name: Optional[str] = None,
        persona: Optional[str] = None,
        max_turns: int = 5,
        temperature: float = 0.7,
    ):
        """
        Args:
            player_id: 玩家ID
            game: 游戏实例
            llm_client: LLM 客户端
            name: Agent 名称
            persona: 个性化设定
            max_turns: 最大对话轮次
            temperature: LLM 温度参数
        """
        super().__init__(player_id, game, name)
        self.llm = llm_client
        self.persona = persona
        self.max_turns = max_turns
        self.temperature = temperature

        # 对话历史（可选保留跨阶段记忆）
        self.memory: List[Dict[str, Any]] = []

    async def decide_action(self) -> Action:
        """
        使用 ReAct 模式决定行动

        流程：
        1. 构建系统提示词
        2. LLM 思考 + 调用工具获取信息
        3. 执行工具，返回结果
        4. 重复直到 LLM 调用 submit_action
        """
        view = self.get_view()
        phase = view.phase.value

        # 构建消息
        messages = [
            self._build_system_message(),
            self._build_action_request_message(),
        ]

        # 获取当前阶段可用工具
        tools = get_tool_definitions(phase)

        # ReAct 循环
        for turn in range(self.max_turns):
            logger.debug(f"[{self.name}] Turn {turn + 1}/{self.max_turns}")

            response = await self.llm.chat(
                messages=messages,
                tools=tools,
                temperature=self.temperature,
            )

            # 处理响应 - 必须先添加 assistant 消息
            if response.content or response.has_tool_calls:
                if response.content:
                    logger.debug(f"[{self.name}] LLM: {response.content[:100]}...")
                messages.append(Message(
                    role="assistant",
                    content=response.content or "",
                    tool_calls=response.tool_calls
                ))

            if response.has_tool_calls:
                for tool_call in response.tool_calls:
                    result = await self._execute_tool(tool_call)

                    # 如果是 submit_action，返回 Action
                    if tool_call.name == "submit_action":
                        if isinstance(result, Action):
                            logger.info(f"[{self.name}] 决策: {result}")
                            return result

                    # 添加工具结果到消息
                    messages.append(Message(
                        role="tool",
                        content=result if isinstance(result, str) else json.dumps(result, ensure_ascii=False),
                        tool_call_id=tool_call.id,
                        name=tool_call.name
                    ))
            else:
                # 没有工具调用，提示需要行动
                messages.append(Message(
                    role="user",
                    content="请使用 submit_action 工具提交你的决策。"
                ))

        # 超时，默认跳过
        logger.warning(f"[{self.name}] 达到最大轮次，默认跳过")
        return Action(ActionType.SKIP, actor_id=self.player_id)

    async def speak(self) -> str:
        """白天发言"""
        view = self.get_view()

        messages = [
            self._build_system_message(),
            Message(
                role="user",
                content=f"""现在是白天讨论阶段，请发表你的观点。

{format_game_state(view)}

{format_player_info(view)}

请使用 speak 工具发表你的发言。"""
            )
        ]

        tools = get_tool_definitions("day_discussion")

        for turn in range(self.max_turns):
            response = await self.llm.chat(
                messages=messages,
                tools=tools,
                temperature=self.temperature,
            )

            if response.has_tool_calls:
                for tool_call in response.tool_calls:
                    if tool_call.name == "speak":
                        content = tool_call.arguments.get("content", "")
                        if content:
                            logger.info(f"[{self.name}] 发言: {content[:50]}...")
                            return content

                    # 其他工具 - 先添加 assistant 消息再添加 tool 结果
                    result = await self._execute_tool(tool_call)
                    if not any(m.role == "assistant" and m.tool_calls for m in messages[-2:]):
                        messages.append(Message(
                            role="assistant",
                            content=response.content or "",
                            tool_calls=[tool_call]
                        ))
                    messages.append(Message(
                        role="tool",
                        content=result if isinstance(result, str) else json.dumps(result, ensure_ascii=False),
                        tool_call_id=tool_call.id,
                        name=tool_call.name
                    ))
            else:
                messages.append(Message(
                    role="user",
                    content="请使用 speak 工具发表你的发言。"
                ))

        return "我暂时没有什么想说的。"

    def _build_system_message(self) -> Message:
        """构建系统消息"""
        view = self.get_view()
        role_name = view.my_role.name

        # 基础系统提示 + 角色策略
        system_content = build_system_prompt(self.persona)
        system_content += "\n\n" + get_role_prompt(role_name)

        return Message(role="system", content=system_content)

    def _build_action_request_message(self) -> Message:
        """构建行动请求消息"""
        view = self.get_view()

        content = f"""{format_game_state(view)}

{format_player_info(view)}

{format_action_prompt(view)}

请先使用工具了解情况，然后做出决策。"""

        return Message(role="user", content=content)

    async def _execute_tool(self, tool_call: ToolCall) -> Any:
        """执行工具调用"""
        name = tool_call.name
        args = tool_call.arguments
        view = self.get_view()

        logger.debug(f"[{self.name}] 调用工具: {name}({args})")

        if name == "get_game_state":
            return format_game_state(view)

        elif name == "get_my_info":
            return format_player_info(view)

        elif name == "get_history":
            event_type = args.get("event_type", "all")
            events = view.get_visible_history()
            return format_history(events, event_type)

        elif name == "submit_action":
            return self._parse_action(args)

        elif name == "speak":
            return args.get("content", "")

        else:
            return f"未知工具: {name}"

    def _parse_action(self, args: Dict[str, Any]) -> Action:
        """解析 submit_action 参数为 Action 对象"""
        action_type_str = args.get("action_type", "skip")
        target_id = args.get("target_id")

        # 映射行动类型
        action_map = {
            "kill": ActionType.KILL,
            "check": ActionType.CHECK,
            "save": ActionType.SAVE,
            "poison": ActionType.POISON,
            "protect": ActionType.PROTECT,
            "vote": ActionType.VOTE,
            "skip": ActionType.SKIP,
            "shoot": ActionType.SHOOT,
        }

        action_type = action_map.get(action_type_str.lower(), ActionType.SKIP)

        return Action(
            action_type=action_type,
            actor_id=self.player_id,
            target_id=target_id,
            extra={"reason": args.get("reason", "")}
        )
