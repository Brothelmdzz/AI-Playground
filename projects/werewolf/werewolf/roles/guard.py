# ==================== 守卫 ====================
"""守卫角色：夜间可以保护一名玩家免受狼人袭击"""

from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional

from werewolf.roles.base import Role
from werewolf.core.enums import Faction, ActionType, GamePhase

if TYPE_CHECKING:
    from werewolf.core.game import Game
    from werewolf.core.player import Player
    from werewolf.core.events import Action, ActionResult


class Guard(Role):
    """
    守卫

    - 阵营：村民（神职）
    - 夜间能力：保护一名玩家，使其今晚不会被狼人杀死
    - 规则：
        - 每晚可以守护一人（包括自己）
        - 不能连续两晚守护同一人
        - 守护只能防狼刀，不能防女巫毒药
        - 守卫的保护和女巫的解药同时生效不会导致问题
    - 胜利条件：与村民阵营共同胜利
    """

    name = "守卫"
    faction = Faction.VILLAGER
    priority = 5  # 守卫最先行动（需要在狼刀之前确定保护）
    can_act_at_night = True

    def __init__(self):
        super().__init__()
        self.last_protected_id: Optional[int] = None  # 上一晚守护的目标

    def get_available_actions(self, player: Player, game: Game) -> List[ActionType]:
        """守卫可以保护或跳过"""
        if game.phase == GamePhase.NIGHT and player.is_alive:
            return [ActionType.PROTECT, ActionType.SKIP]
        return []

    def validate_action(
        self, action: Action, player: Player, game: Game
    ) -> tuple[bool, str]:
        """验证守卫行动"""
        valid, msg = super().validate_action(action, player, game)
        if not valid:
            return valid, msg

        if action.action_type == ActionType.PROTECT:
            if action.target_id is None:
                return False, "保护必须指定目标"
            # 不能连续两晚守护同一人
            if action.target_id == self.last_protected_id:
                target = game.get_player(action.target_id)
                return False, f"不能连续两晚守护同一人: {target.name}"

        elif action.action_type != ActionType.SKIP:
            return False, f"守卫不能执行此行动: {action.action_type}"

        return True, ""

    async def execute_action(
        self, action: Action, player: Player, game: Game
    ) -> ActionResult:
        """执行守卫行动"""
        from werewolf.core.events import ActionResult

        if action.action_type == ActionType.SKIP:
            self.last_protected_id = None  # 跳过时重置
            return ActionResult.ok("守卫选择不守护任何人")

        if action.action_type == ActionType.PROTECT:
            target = game.get_player(action.target_id)
            self.last_protected_id = action.target_id
            return ActionResult.ok(
                f"守卫保护了 {target.name}",
                target_id=action.target_id,
                protected=True
            )

        return ActionResult.fail("未知行动")

    def reset_protection(self) -> None:
        """重置守护状态（用于游戏重置）"""
        self.last_protected_id = None
