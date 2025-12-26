# ==================== 角色基类 ====================
"""角色抽象基类定义"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

from werewolf.core.enums import Faction, ActionType

if TYPE_CHECKING:
    from werewolf.core.game import Game
    from werewolf.core.player import Player
    from werewolf.core.events import Action, ActionResult


class Role(ABC):
    """
    角色抽象基类

    所有具体角色都必须继承此类并实现抽象方法。

    Attributes:
        name: 角色名称（中文）
        faction: 所属阵营
        priority: 夜间行动优先级（数字越小越先行动）
        can_act_at_night: 是否可以在夜间行动
    """

    name: str = "未知角色"
    faction: Faction = Faction.VILLAGER
    priority: int = 100  # 默认最低优先级
    can_act_at_night: bool = False

    def get_available_actions(self, player: Player, game: Game) -> List[ActionType]:
        """
        获取当前可用的行动类型

        Args:
            player: 拥有此角色的玩家
            game: 游戏实例

        Returns:
            可用行动类型列表
        """
        return []

    def validate_action(self, action: Action, player: Player, game: Game) -> tuple[bool, str]:
        """
        验证行动是否合法

        Args:
            action: 待验证的行动
            player: 行动者
            game: 游戏实例

        Returns:
            (是否合法, 错误信息)
        """
        # 基础验证：玩家必须存活
        if not player.is_alive:
            return False, "死亡玩家无法行动"

        # 验证目标存在且存活（如果有目标）
        if action.target_id is not None:
            target = game.get_player(action.target_id)
            if target is None:
                return False, f"目标玩家不存在: {action.target_id}"
            if not target.is_alive:
                return False, f"目标玩家已死亡: {target.name}"

        return True, ""

    async def execute_action(
        self, action: Action, player: Player, game: Game
    ) -> ActionResult:
        """
        执行行动

        注意：此方法不应直接修改游戏状态，而是返回行动结果。
        实际状态修改由 Resolver 在结算阶段统一处理。

        Args:
            action: 要执行的行动
            player: 行动者
            game: 游戏实例

        Returns:
            行动结果
        """
        from werewolf.core.events import ActionResult
        return ActionResult.ok("行动已记录")

    def on_death(self, player: Player, game: Game) -> Optional[ActionType]:
        """
        死亡时触发

        某些角色（如猎人）在死亡时有特殊能力。

        Args:
            player: 死亡的玩家
            game: 游戏实例

        Returns:
            需要额外执行的行动类型（如猎人开枪），或None
        """
        return None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name}, {self.faction.value})"
