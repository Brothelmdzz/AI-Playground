# ==================== 猎人 ====================
"""猎人角色：正常死亡时可以开枪带走一人"""

from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional

from werewolf.roles.base import Role
from werewolf.core.enums import Faction, ActionType, GamePhase, DeathReason

if TYPE_CHECKING:
    from werewolf.core.game import Game
    from werewolf.core.player import Player
    from werewolf.core.events import Action, ActionResult


class Hunter(Role):
    """
    猎人

    - 阵营：村民（神职）
    - 夜间能力：无主动技能
    - 死亡技能：正常死亡时可以开枪带走一名玩家
    - 规则：
        - 被狼人杀死：可以开枪
        - 被投票出局：可以开枪
        - 被女巫毒死：不能开枪
        - 开枪目标立即死亡，不触发连锁
    - 胜利条件：与村民阵营共同胜利
    """

    name = "猎人"
    faction = Faction.VILLAGER
    priority = 100  # 无夜间主动行动
    can_act_at_night = False

    def __init__(self):
        super().__init__()
        self.can_shoot = True  # 是否可以开枪

    def get_available_actions(self, player: Player, game: Game) -> List[ActionType]:
        """
        猎人在死亡时可以开枪

        注意：这个方法在猎人死亡触发时被调用
        """
        if self.can_shoot and not player.is_alive:
            return [ActionType.SHOOT, ActionType.SKIP]
        return []

    def validate_action(
        self, action: Action, player: Player, game: Game
    ) -> tuple[bool, str]:
        """验证猎人行动"""
        if action.action_type == ActionType.SHOOT:
            if not self.can_shoot:
                return False, "猎人无法开枪（可能被毒死）"
            if action.target_id is None:
                return False, "开枪必须指定目标"
            target = game.get_player(action.target_id)
            if target is None:
                return False, f"目标玩家不存在: {action.target_id}"
            if not target.is_alive:
                return False, f"目标玩家已死亡: {target.name}"
            if action.target_id == player.id:
                return False, "不能射杀自己"
            return True, ""

        elif action.action_type == ActionType.SKIP:
            return True, ""

        return False, f"猎人不能执行此行动: {action.action_type}"

    async def execute_action(
        self, action: Action, player: Player, game: Game
    ) -> ActionResult:
        """执行猎人开枪"""
        from werewolf.core.events import ActionResult

        if action.action_type == ActionType.SKIP:
            return ActionResult.ok("猎人选择不开枪")

        if action.action_type == ActionType.SHOOT:
            target = game.get_player(action.target_id)
            self.can_shoot = False  # 开枪后不能再开
            return ActionResult.ok(
                f"猎人 {player.name} 射杀了 {target.name}",
                target_id=action.target_id,
                shot=True
            )

        return ActionResult.fail("未知行动")

    def on_death(self, player: Player, game: Game) -> Optional[ActionType]:
        """
        猎人死亡时检查是否可以开枪

        Returns:
            如果可以开枪返回 SHOOT，否则返回 None
        """
        # 检查死亡原因
        if player.death_reason == DeathReason.WITCH_POISON:
            self.can_shoot = False
            return None

        # 被狼杀或被投票，可以开枪
        if self.can_shoot:
            return ActionType.SHOOT

        return None
