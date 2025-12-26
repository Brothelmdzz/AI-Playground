# ==================== 人类 Agent ====================
"""通过 CLI 输入的人类玩家"""

from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING, Optional

from werewolf.agents.base import BaseAgent
from werewolf.core.enums import ActionType
from werewolf.core.events import Action
from werewolf.prompts.templates import (
    format_game_state,
    format_player_info,
    format_action_prompt,
)

if TYPE_CHECKING:
    from werewolf.core.game import Game


class HumanAgent(BaseAgent):
    """
    人类 Agent

    通过命令行与人类玩家交互
    """

    def __init__(
        self,
        player_id: int,
        game: Game,
        name: Optional[str] = None,
    ):
        super().__init__(player_id, game, name or "Human")

    async def decide_action(self) -> Action:
        """通过 CLI 获取人类决策"""
        view = self.get_view()

        # 显示游戏状态
        print("\n" + "=" * 50)
        print(format_game_state(view))
        print()
        print(format_player_info(view))
        print()
        print(format_action_prompt(view))
        print("=" * 50)

        # 获取可用行动
        available = view.available_actions
        if not available:
            print("你没有可用行动，自动跳过")
            return Action(ActionType.SKIP, actor_id=self.player_id)

        # 显示选项
        print("\n可用行动:")
        action_map = {}
        for i, action in enumerate(available):
            action_map[str(i + 1)] = action
            print(f"  {i + 1}. {action.value}")

        # 获取行动选择
        while True:
            choice = await self._async_input("请选择行动 (输入数字): ")
            if choice in action_map:
                action_type = action_map[choice]
                break
            print("无效选择，请重新输入")

        # 获取目标（如果需要）
        target_id = None
        if action_type not in (ActionType.SKIP, ActionType.SAVE):
            alive_players = [
                p for p in view.alive_players
                if p["is_alive"] and p["id"] != self.player_id
            ]

            if alive_players:
                print("\n选择目标:")
                for p in alive_players:
                    print(f"  {p['id']}. {p['name']}")

                while True:
                    target_input = await self._async_input("请输入目标ID: ")
                    try:
                        target_id = int(target_input)
                        if any(p["id"] == target_id for p in alive_players):
                            break
                    except ValueError:
                        pass
                    print("无效ID，请重新输入")

        elif action_type == ActionType.SAVE:
            # 女巫解药目标是被狼杀的人
            target_id = view.wolf_target_tonight

        return Action(
            action_type=action_type,
            actor_id=self.player_id,
            target_id=target_id
        )

    async def speak(self) -> str:
        """获取人类发言"""
        view = self.get_view()

        print("\n" + "=" * 50)
        print("现在是白天讨论阶段")
        print(format_game_state(view))
        print("=" * 50)

        content = await self._async_input("\n请输入你的发言: ")
        return content if content else "我暂时没有什么想说的。"

    async def _async_input(self, prompt: str) -> str:
        """异步获取用户输入"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: input(prompt))
