# ==================== Runner Module ====================
"""游戏运行器模块"""

from werewolf.runner.game_runner import GameRunner, GameResult
from werewolf.runner.cli_runner import CLIRunner

__all__ = [
    "GameRunner",
    "GameResult",
    "CLIRunner",
]
