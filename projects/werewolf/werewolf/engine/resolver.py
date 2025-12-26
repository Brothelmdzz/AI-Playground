# ==================== 夜间结算器 ====================
"""处理夜间行动的结算逻辑"""

from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Optional
from collections import Counter

from werewolf.core.enums import ActionType, DeathReason, Faction
from werewolf.core.events import Action, NightResult

if TYPE_CHECKING:
    from werewolf.core.game import Game
    from werewolf.core.player import Player


class NightResolver:
    """
    夜间结算器

    负责处理夜间所有行动的结算，按优先级处理：
    1. 守卫保护 (priority: 5)
    2. 狼人击杀 (priority: 10)
    3. 女巫行动 (priority: 20)
    4. 预言家查验 (priority: 30) - 查验结果在行动时已返回

    结算流程：
    1. 收集所有行动
    2. 应用守卫保护标记
    3. 确定狼刀目标（多狼投票取众数）
    4. 判断狼刀是否被守卫挡住
    5. 判断女巫解药/毒药
    6. 生成最终死亡列表
    7. 检查猎人是否触发
    """

    async def resolve(self, game: Game, actions: List[Action]) -> NightResult:
        """
        结算夜间行动

        Args:
            game: 游戏实例
            actions: 本夜所有行动列表

        Returns:
            NightResult: 结算结果
        """
        result = NightResult()

        # 按行动类型分组
        action_map = self._group_actions(actions)

        # 1. 处理守卫保护
        protected_id = self._resolve_protection(action_map.get(ActionType.PROTECT, []))
        if protected_id is not None:
            player = game.get_player(protected_id)
            if player:
                player.night_state.protected = True
                result.messages.append(f"守卫保护了 {player.name}")

        # 2. 处理狼刀（多狼投票）
        wolf_target_id = self._resolve_wolf_kill(action_map.get(ActionType.KILL, []))
        wolf_kill_success = False

        if wolf_target_id is not None:
            target = game.get_player(wolf_target_id)
            if target:
                target.night_state.killed_by_wolf = True
                target.night_state.wolf_target_id = wolf_target_id

                # 检查是否被守卫保护
                if target.night_state.protected:
                    result.messages.append(f"{target.name} 被狼刀但被守卫保护")
                else:
                    wolf_kill_success = True
                    result.messages.append(f"狼人选择击杀 {target.name}")

        # 3. 处理女巫解药
        save_actions = action_map.get(ActionType.SAVE, [])
        if save_actions:
            # 女巫只能救今晚被狼杀的人
            if wolf_target_id is not None:
                target = game.get_player(wolf_target_id)
                if target:
                    target.night_state.saved = True
                    wolf_kill_success = False
                    result.messages.append(f"女巫使用解药救了 {target.name}")

        # 4. 处理女巫毒药
        poison_actions = action_map.get(ActionType.POISON, [])
        for action in poison_actions:
            if action.target_id is not None:
                target = game.get_player(action.target_id)
                if target:
                    target.night_state.poisoned = True
                    result.messages.append(f"女巫使用毒药毒杀 {target.name}")

        # 5. 生成死亡列表
        deaths = []

        # 狼刀死亡（未被救且未被守护）
        if wolf_kill_success and wolf_target_id is not None:
            target = game.get_player(wolf_target_id)
            if target and not target.night_state.saved:
                deaths.append((wolf_target_id, DeathReason.WOLF_KILL))

        # 毒药死亡
        for player in game.get_alive_players():
            if player.night_state.poisoned:
                deaths.append((player.id, DeathReason.WITCH_POISON))

        result.deaths = deaths

        # 6. 检查猎人触发
        for player_id, death_reason in deaths:
            player = game.get_player(player_id)
            if player and player.role and player.role.name == "猎人":
                # 被毒死不能开枪
                if death_reason != DeathReason.WITCH_POISON:
                    result.hunter_can_shoot = True
                    result.hunter_id = player_id
                    result.messages.append(f"猎人 {player.name} 可以开枪")
                else:
                    result.messages.append(f"猎人 {player.name} 被毒死，无法开枪")

        return result

    def _group_actions(self, actions: List[Action]) -> Dict[ActionType, List[Action]]:
        """按行动类型分组"""
        groups: Dict[ActionType, List[Action]] = {}
        for action in actions:
            if action.action_type not in groups:
                groups[action.action_type] = []
            groups[action.action_type].append(action)
        return groups

    def _resolve_protection(self, protect_actions: List[Action]) -> Optional[int]:
        """
        结算守卫保护

        Returns:
            被保护玩家的ID，或None
        """
        for action in protect_actions:
            if action.target_id is not None:
                return action.target_id
        return None

    def _resolve_wolf_kill(self, kill_actions: List[Action]) -> Optional[int]:
        """
        结算狼人击杀

        多个狼人时采用多数决：
        - 统计每个目标的票数
        - 取票数最多的目标
        - 平票时随机选择（或不杀人，可配置）

        Returns:
            被击杀玩家的ID，或None（空刀）
        """
        if not kill_actions:
            return None

        # 统计目标票数
        targets = [a.target_id for a in kill_actions if a.target_id is not None]
        if not targets:
            return None

        # 多数决
        counter = Counter(targets)
        most_common = counter.most_common()

        if not most_common:
            return None

        # 检查是否平票
        top_count = most_common[0][1]
        tied_targets = [t for t, c in most_common if c == top_count]

        if len(tied_targets) == 1:
            return tied_targets[0]

        # 平票时取第一个（可改为随机或空刀）
        return tied_targets[0]
