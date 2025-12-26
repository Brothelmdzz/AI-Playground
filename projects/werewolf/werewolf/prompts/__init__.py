# ==================== Prompts Module ====================
"""Prompt 模板模块"""

from werewolf.prompts.system import SYSTEM_PROMPT, build_system_prompt
from werewolf.prompts.role_prompts import get_role_prompt, ROLE_PROMPTS
from werewolf.prompts.templates import (
    format_game_state,
    format_player_info,
    format_history,
    format_action_prompt,
)

__all__ = [
    # 系统提示词
    "SYSTEM_PROMPT",
    "build_system_prompt",
    # 角色提示词
    "get_role_prompt",
    "ROLE_PROMPTS",
    # 模板工具
    "format_game_state",
    "format_player_info",
    "format_history",
    "format_action_prompt",
]
