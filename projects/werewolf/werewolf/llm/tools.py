# ==================== 工具定义 ====================
"""狼人杀游戏工具定义"""

from typing import List
from werewolf.llm.base import ToolDefinition


# ==================== 游戏工具定义 ====================

TOOL_GET_GAME_STATE = ToolDefinition(
    name="get_game_state",
    description="获取当前游戏状态，包括：当前阶段、回合数、存活玩家列表",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)

TOOL_GET_MY_INFO = ToolDefinition(
    name="get_my_info",
    description="获取我的详细信息，包括：我的角色、我的队友（如果是狼人）、当前可用的行动选项",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)

TOOL_GET_HISTORY = ToolDefinition(
    name="get_history",
    description="获取游戏历史记录，包括：死亡记录、投票记录、发言记录等",
    parameters={
        "type": "object",
        "properties": {
            "event_type": {
                "type": "string",
                "enum": ["all", "death", "vote", "speech"],
                "description": "要查询的事件类型，默认为 all"
            }
        },
        "required": []
    }
)

TOOL_SUBMIT_ACTION = ToolDefinition(
    name="submit_action",
    description="提交行动决策。根据你的角色和当前阶段，选择合适的行动。",
    parameters={
        "type": "object",
        "properties": {
            "action_type": {
                "type": "string",
                "enum": ["kill", "check", "save", "poison", "protect", "vote", "skip", "shoot"],
                "description": "行动类型：kill(狼人击杀), check(预言家查验), save(女巫解药), poison(女巫毒药), protect(守卫保护), vote(投票), skip(跳过), shoot(猎人开枪)"
            },
            "target_id": {
                "type": "integer",
                "description": "目标玩家的ID。skip行动可以不指定目标。"
            },
            "reason": {
                "type": "string",
                "description": "行动理由（可选，用于记录决策过程）"
            }
        },
        "required": ["action_type"]
    }
)

TOOL_SPEAK = ToolDefinition(
    name="speak",
    description="在白天讨论阶段发言。你可以发表观点、指控他人、为自己辩护等。",
    parameters={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "发言内容"
            }
        },
        "required": ["content"]
    }
)

# 所有工具列表
WEREWOLF_TOOLS: List[ToolDefinition] = [
    TOOL_GET_GAME_STATE,
    TOOL_GET_MY_INFO,
    TOOL_GET_HISTORY,
    TOOL_SUBMIT_ACTION,
    TOOL_SPEAK,
]

# 按阶段分组的工具
NIGHT_TOOLS: List[ToolDefinition] = [
    TOOL_GET_GAME_STATE,
    TOOL_GET_MY_INFO,
    TOOL_GET_HISTORY,
    TOOL_SUBMIT_ACTION,
]

DAY_DISCUSSION_TOOLS: List[ToolDefinition] = [
    TOOL_GET_GAME_STATE,
    TOOL_GET_MY_INFO,
    TOOL_GET_HISTORY,
    TOOL_SPEAK,
]

DAY_VOTE_TOOLS: List[ToolDefinition] = [
    TOOL_GET_GAME_STATE,
    TOOL_GET_MY_INFO,
    TOOL_GET_HISTORY,
    TOOL_SUBMIT_ACTION,
]


def get_tool_definitions(phase: str = "all") -> List[ToolDefinition]:
    """
    根据游戏阶段获取可用工具

    Args:
        phase: 游戏阶段 ("night" | "day_discussion" | "day_vote" | "all")

    Returns:
        工具定义列表
    """
    if phase == "night":
        return NIGHT_TOOLS
    elif phase == "day_discussion":
        return DAY_DISCUSSION_TOOLS
    elif phase == "day_vote":
        return DAY_VOTE_TOOLS
    else:
        return WEREWOLF_TOOLS
