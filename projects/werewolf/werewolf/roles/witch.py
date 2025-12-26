# ==================== 女巫 ====================
"""女巫角色：拥有一瓶解药和一瓶毒药"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

from werewolf.roles.base import Role
from werewolf.core.enums import Faction, ActionType, GamePhase

if TYPE_CHECKING:
    from werewolf.core.game import Game
    from werewolf.core.player import Player
    from werewolf.core.events import Action, ActionResult


@dataclass
class WitchState:
    """女巫状态：追踪药水使用情况"""
    has_save_potion: bool = True    # 是否还有解药
    has_poison_potion: bool = True  # 是否还有毒药


class Witch(Role):
    """
    女巫

    - 阵营：村民（神职）
    - 夜间能力：
        - 解药：救活当晚被狼人杀死的玩家（全局一次）
        - 毒药：毒杀一名玩家（全局一次）
    - 规则：
        - 女巫会被告知当晚谁被狼杀
        - 同一晚不能同时使用两瓶药（可配置）
        - 女巫能否自救（可配置，默认不能）
    - 胜利条件：与村民阵营共同胜利
    """

    name = "女巫"
    faction = Faction.VILLAGER
    priority = 20  # 女巫在狼人之后、预言家之前（需要知道狼刀目标）
    can_act_at_night = True

    def __init__(self):
        super().__init__()
        self.state = WitchState()

    def get_available_actions(self, player: Player, game: Game) -> List[ActionType]:
        """女巫可以使用解药、毒药或跳过"""
        if game.phase != GamePhase.NIGHT or not player.is_alive:
            return []

        actions = [ActionType.SKIP]

        # 有解药且今晚有人被狼杀
        if self.state.has_save_potion and self._get_wolf_target(game) is not None:
            actions.append(ActionType.SAVE)

        # 有毒药
        if self.state.has_poison_potion:
            actions.append(ActionType.POISON)

        return actions

    def _get_wolf_target(self, game: Game) -> Optional[int]:
        """获取今晚被狼杀的玩家ID"""
        # 从待处理行动中查找狼刀目标
        for action in game.get_pending_actions():
            if action.action_type == ActionType.KILL and action.target_id is not None:
                return action.target_id
        return None

    def validate_action(
        self, action: Action, player: Player, game: Game
    ) -> tuple[bool, str]:
        """验证女巫行动"""
        valid, msg = super().validate_action(action, player, game)
        if not valid:
            return valid, msg

        if action.action_type == ActionType.SAVE:
            if not self.state.has_save_potion:
                return False, "解药已用完"
            wolf_target = self._get_wolf_target(game)
            if wolf_target is None:
                return False, "今晚没有人被狼杀，无法使用解药"
            # 女巫不能自救（标准规则）
            if wolf_target == player.id:
                return False, "女巫不能自救"

        elif action.action_type == ActionType.POISON:
            if not self.state.has_poison_potion:
                return False, "毒药已用完"
            if action.target_id is None:
                return False, "毒药必须指定目标"
            if action.target_id == player.id:
                return False, "不能毒自己"

        elif action.action_type != ActionType.SKIP:
            return False, f"女巫不能执行此行动: {action.action_type}"

        return True, ""

    async def execute_action(
        self, action: Action, player: Player, game: Game
    ) -> ActionResult:
        """执行女巫行动"""
        from werewolf.core.events import ActionResult

        if action.action_type == ActionType.SKIP:
            return ActionResult.ok("女巫选择不使用药水")

        if action.action_type == ActionType.SAVE:
            self.state.has_save_potion = False
            wolf_target = self._get_wolf_target(game)
            target = game.get_player(wolf_target)
            return ActionResult.ok(
                f"女巫使用解药救了 {target.name}",
                target_id=wolf_target,
                saved=True
            )

        if action.action_type == ActionType.POISON:
            self.state.has_poison_potion = False
            target = game.get_player(action.target_id)
            return ActionResult.ok(
                f"女巫使用毒药毒杀 {target.name}",
                target_id=action.target_id,
                poisoned=True
            )

        return ActionResult.fail("未知行动")

    def reset_potions(self) -> None:
        """重置药水状态（用于游戏重置）"""
        self.state = WitchState()
