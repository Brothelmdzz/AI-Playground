# ==================== 狼人 ====================
"""狼人角色：夜间可以集体选择击杀一名玩家"""

from __future__ import annotations
from typing import TYPE_CHECKING, List

from werewolf.roles.base import Role
from werewolf.core.enums import Faction, ActionType, GamePhase

if TYPE_CHECKING:
    from werewolf.core.game import Game
    from werewolf.core.player import Player
    from werewolf.core.events import Action, ActionResult


class Werewolf(Role):
    """
    狼人

    - 阵营：狼人
    - 夜间能力：与其他狼人一起选择击杀一名玩家
    - 规则：
        - 狼人之间知道彼此身份
        - 可以选择空刀（不杀人）
        - 多个狼人需要统一目标（本引擎采用多数决）
    - 胜利条件：狼人数量 >= 存活村民数量
    """

    name = "狼人"
    faction = Faction.WEREWOLF
    priority = 10  # 狼人较早行动（守卫之后）
    can_act_at_night = True

    def get_available_actions(self, player: Player, game: Game) -> List[ActionType]:
        """狼人可以选择击杀或跳过"""
        if game.phase == GamePhase.NIGHT and player.is_alive:
            return [ActionType.KILL, ActionType.SKIP]
        return []

    def validate_action(
        self, action: Action, player: Player, game: Game
    ) -> tuple[bool, str]:
        """验证狼人行动"""
        # 基础验证
        valid, msg = super().validate_action(action, player, game)
        if not valid:
            return valid, msg

        # 验证行动类型
        if action.action_type not in (ActionType.KILL, ActionType.SKIP):
            return False, f"狼人不能执行此行动: {action.action_type}"

        # 击杀需要有目标
        if action.action_type == ActionType.KILL:
            if action.target_id is None:
                return False, "击杀必须指定目标"
            # 不能杀自己的狼队友（可选规则，这里允许自刀）

        return True, ""

    async def execute_action(
        self, action: Action, player: Player, game: Game
    ) -> ActionResult:
        """
        执行狼人行动

        注意：这里只是记录行动，实际击杀在 NightResolver 中结算
        """
        from werewolf.core.events import ActionResult

        if action.action_type == ActionType.SKIP:
            return ActionResult.ok("狼人选择空刀")

        if action.action_type == ActionType.KILL:
            target = game.get_player(action.target_id)
            return ActionResult.ok(
                f"狼人 {player.name} 选择击杀 {target.name}",
                target_id=action.target_id
            )

        return ActionResult.fail("未知行动")
