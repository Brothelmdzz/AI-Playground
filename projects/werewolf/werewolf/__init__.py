# ==================== AI Werewolf Game Engine ====================
"""
AI 狼人杀游戏引擎

纯游戏逻辑实现，提供完整的狼人杀规则和 API。
"""

from werewolf.core.enums import GamePhase, Faction, ActionType, DeathReason
from werewolf.core.player import Player, NightState
from werewolf.core.events import GameEvent, Action, ActionResult
from werewolf.core.game import Game, GameConfig

__version__ = "0.1.0"

__all__ = [
    # 枚举
    "GamePhase",
    "Faction",
    "ActionType",
    "DeathReason",
    # 模型
    "Player",
    "NightState",
    # 事件
    "GameEvent",
    "Action",
    "ActionResult",
    # 游戏
    "Game",
    "GameConfig",
]
