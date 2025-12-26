# ==================== Agent 基类 ====================
"""Agent 抽象基类定义"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from werewolf.core.game import Game, PlayerView
    from werewolf.core.events import Action


class BaseAgent(ABC):
    """
    Agent 抽象基类

    所有 Agent（LLM、随机、人类）都必须继承此类并实现核心方法。

    Attributes:
        player_id: 玩家ID
        game: 游戏实例
        name: Agent 名称（用于日志）
    """

    def __init__(self, player_id: int, game: Game, name: Optional[str] = None):
        """
        Args:
            player_id: 玩家ID
            game: 游戏实例
            name: Agent 名称
        """
        self.player_id = player_id
        self.game = game
        self.name = name or f"Agent_{player_id}"

    @abstractmethod
    async def decide_action(self) -> Action:
        """
        决定行动（夜间技能或投票）

        Returns:
            Action: 决策的行动
        """
        pass

    @abstractmethod
    async def speak(self) -> str:
        """
        白天发言

        Returns:
            str: 发言内容
        """
        pass

    def get_view(self) -> PlayerView:
        """
        获取玩家视角

        Returns:
            PlayerView: 当前玩家可见的游戏信息
        """
        return self.game.get_player_view(self.player_id)

    def get_player(self):
        """获取玩家对象"""
        return self.game.get_player(self.player_id)

    def is_alive(self) -> bool:
        """检查玩家是否存活"""
        player = self.get_player()
        return player.is_alive if player else False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.player_id}, name={self.name})"
