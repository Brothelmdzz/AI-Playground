# ==================== 预言家 ====================
"""预言家角色：夜间可以查验一名玩家的身份"""

from __future__ import annotations
from typing import TYPE_CHECKING, List

from werewolf.roles.base import Role
from werewolf.core.enums import Faction, ActionType, GamePhase

if TYPE_CHECKING:
    from werewolf.core.game import Game
    from werewolf.core.player import Player
    from werewolf.core.events import Action, ActionResult


class Seer(Role):
    """
    预言家

    - 阵营：村民（神职）
    - 夜间能力：查验一名玩家，得知其是否为狼人
    - 规则：
        - 每晚可以查验一人
        - 查验结果只有「狼人」或「好人」两种
        - 查验结果立即可知
    - 胜利条件：与村民阵营共同胜利
    """

    name = "预言家"
    faction = Faction.VILLAGER
    priority = 30  # 预言家在狼人之后行动
    can_act_at_night = True

    def get_available_actions(self, player: Player, game: Game) -> List[ActionType]:
        """预言家可以查验或跳过"""
        if game.phase == GamePhase.NIGHT and player.is_alive:
            return [ActionType.CHECK, ActionType.SKIP]
        return []

    def validate_action(
        self, action: Action, player: Player, game: Game
    ) -> tuple[bool, str]:
        """验证预言家行动"""
        valid, msg = super().validate_action(action, player, game)
        if not valid:
            return valid, msg

        if action.action_type not in (ActionType.CHECK, ActionType.SKIP):
            return False, f"预言家不能执行此行动: {action.action_type}"

        if action.action_type == ActionType.CHECK:
            if action.target_id is None:
                return False, "查验必须指定目标"
            # 不能查验自己
            if action.target_id == player.id:
                return False, "不能查验自己"

        return True, ""

    async def execute_action(
        self, action: Action, player: Player, game: Game
    ) -> ActionResult:
        """
        执行预言家查验

        查验结果立即返回（与其他夜间行动不同，预言家可以立即得知结果）
        """
        from werewolf.core.events import ActionResult

        if action.action_type == ActionType.SKIP:
            return ActionResult.ok("预言家选择不查验")

        if action.action_type == ActionType.CHECK:
            target = game.get_player(action.target_id)
            is_werewolf = target.role.faction == Faction.WEREWOLF
            result_text = "狼人" if is_werewolf else "好人"

            return ActionResult.ok(
                f"查验结果：{target.name} 是 {result_text}",
                target_id=action.target_id,
                is_werewolf=is_werewolf
            )

        return ActionResult.fail("未知行动")
