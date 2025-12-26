# ==================== 主持人 ====================
"""游戏主持人，负责驱动游戏流程"""

from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Callable, Awaitable

from werewolf.core.enums import GamePhase, ActionType, DeathReason, Faction
from werewolf.core.events import Action, ActionResult, PhaseResult, GameEvent
from werewolf.engine.resolver import NightResolver
from werewolf.engine.vote import VoteManager

if TYPE_CHECKING:
    from werewolf.core.game import Game
    from werewolf.core.player import Player


class Moderator:
    """
    游戏主持人

    职责：
    - 驱动游戏阶段转换
    - 收集和验证玩家行动
    - 调用结算器处理行动
    - 判定游戏胜负
    - 记录游戏事件
    """

    def __init__(self, game: Game):
        self.game = game
        self.night_resolver = NightResolver()
        self.vote_manager = VoteManager()
        self._pending_actions: List[Action] = []
        self._hunter_pending: bool = False  # 猎人是否需要开枪

    async def start_game(self) -> None:
        """开始游戏"""
        if self.game.phase != GamePhase.INIT:
            raise RuntimeError("游戏已经开始")

        # 记录游戏开始事件
        self.game.add_event(GameEvent(
            event_type=GameEvent.GAME_START,
            round_num=0,
            phase=GamePhase.INIT,
            data={"player_count": len(self.game.players)}
        ))

        # 进入第一个夜晚
        await self._transition_to(GamePhase.NIGHT)
        self.game.round = 1

    async def submit_action(self, player_id: int, action: Action) -> ActionResult:
        """
        提交玩家行动

        Args:
            player_id: 玩家ID
            action: 行动

        Returns:
            行动结果
        """
        player = self.game.get_player(player_id)
        if player is None:
            return ActionResult.fail(f"玩家不存在: {player_id}")

        # 验证行动
        valid, msg = player.role.validate_action(action, player, self.game)
        if not valid:
            return ActionResult.fail(msg)

        # 执行行动（可能返回即时结果，如预言家查验）
        result = await player.role.execute_action(action, player, self.game)

        # 记录行动
        if result.success:
            self._pending_actions.append(action)
            self.game.add_event(GameEvent(
                event_type=GameEvent.PLAYER_ACTION,
                round_num=self.game.round,
                phase=self.game.phase,
                data={"player_id": player_id, "action": action.action_type.value},
                visible_to=[player_id]  # 只有自己可见
            ))

        return result

    async def advance_phase(self) -> PhaseResult:
        """
        推进到下一阶段

        Returns:
            阶段结算结果
        """
        current_phase = self.game.phase

        if current_phase == GamePhase.NIGHT:
            return await self._resolve_night()
        elif current_phase == GamePhase.DAY_DISCUSSION:
            return await self._end_discussion()
        elif current_phase == GamePhase.DAY_VOTE:
            return await self._resolve_vote()
        elif current_phase == GamePhase.GAME_OVER:
            return PhaseResult(phase=GamePhase.GAME_OVER)
        else:
            raise RuntimeError(f"无法从此阶段推进: {current_phase}")

    async def _resolve_night(self) -> PhaseResult:
        """结算夜间"""
        result = PhaseResult(phase=GamePhase.NIGHT)

        # 调用夜间结算器
        night_result = await self.night_resolver.resolve(self.game, self._pending_actions)
        self._pending_actions.clear()

        # 处理死亡
        for player_id, death_reason in night_result.deaths:
            player = self.game.get_player(player_id)
            if player:
                player.die(death_reason, self.game.round)
                result.deaths.append(player_id)
                result.messages.append(f"{player.name} 死亡 ({death_reason.value})")

                # 记录死亡事件
                self.game.add_event(GameEvent(
                    event_type=GameEvent.PLAYER_DEATH,
                    round_num=self.game.round,
                    phase=GamePhase.NIGHT,
                    data={
                        "player_id": player_id,
                        "reason": death_reason.value
                    }
                ))

        # 检查猎人
        if night_result.hunter_can_shoot:
            self._hunter_pending = True
            # 实际游戏中这里需要等待猎人选择目标
            # 简化处理：标记后由外部处理

        # 检查胜负
        winner = self._check_winner()
        if winner:
            result.winner = winner
            result.next_phase = GamePhase.GAME_OVER
            await self._transition_to(GamePhase.GAME_OVER)
        else:
            result.next_phase = GamePhase.DAY_DISCUSSION
            await self._transition_to(GamePhase.DAY_DISCUSSION)

        # 重置所有玩家的夜间状态
        for player in self.game.players:
            player.reset_night_state()

        return result

    async def _end_discussion(self) -> PhaseResult:
        """结束讨论阶段，进入投票"""
        result = PhaseResult(phase=GamePhase.DAY_DISCUSSION)
        result.next_phase = GamePhase.DAY_VOTE
        await self._transition_to(GamePhase.DAY_VOTE)
        return result

    async def _resolve_vote(self) -> PhaseResult:
        """结算投票"""
        result = PhaseResult(phase=GamePhase.DAY_VOTE)

        # 筛选投票行动
        vote_actions = [a for a in self._pending_actions
                       if a.action_type in (ActionType.VOTE, ActionType.SKIP)]
        self._pending_actions.clear()

        # 调用投票管理器
        vote_result = await self.vote_manager.resolve(self.game, vote_actions)

        # 记录投票事件
        self.game.add_event(GameEvent(
            event_type=GameEvent.VOTE_RESULT,
            round_num=self.game.round,
            phase=GamePhase.DAY_VOTE,
            data={
                "votes": {str(k): v for k, v in vote_result.votes.items()},
                "eliminated": vote_result.eliminated_id
            }
        ))

        # 处理处决
        if vote_result.eliminated_id is not None:
            player = self.game.get_player(vote_result.eliminated_id)
            if player:
                player.die(DeathReason.VOTE_OUT, self.game.round)
                result.deaths.append(vote_result.eliminated_id)
                result.messages.append(f"{player.name} 被投票处决")

                # 检查猎人
                if player.role and player.role.name == "猎人":
                    trigger = player.role.on_death(player, self.game)
                    if trigger == ActionType.SHOOT:
                        self._hunter_pending = True

        # 检查胜负
        winner = self._check_winner()
        if winner:
            result.winner = winner
            result.next_phase = GamePhase.GAME_OVER
            await self._transition_to(GamePhase.GAME_OVER)
        else:
            # 进入下一个夜晚
            self.game.round += 1
            result.next_phase = GamePhase.NIGHT
            await self._transition_to(GamePhase.NIGHT)

        return result

    async def _transition_to(self, phase: GamePhase) -> None:
        """切换阶段"""
        old_phase = self.game.phase
        self.game.phase = phase

        self.game.add_event(GameEvent(
            event_type=GameEvent.PHASE_CHANGE,
            round_num=self.game.round,
            phase=phase,
            data={"from": old_phase.value, "to": phase.value}
        ))

    def _check_winner(self) -> Optional[Faction]:
        """
        检查胜负条件

        Returns:
            胜利阵营，或None（游戏继续）
        """
        alive_players = self.game.get_alive_players()

        wolf_count = sum(1 for p in alive_players if p.role.faction == Faction.WEREWOLF)
        villager_count = sum(1 for p in alive_players if p.role.faction == Faction.VILLAGER)

        # 狼人全灭 -> 村民胜
        if wolf_count == 0:
            return Faction.VILLAGER

        # 狼人 >= 村民 -> 狼人胜
        if wolf_count >= villager_count:
            return Faction.WEREWOLF

        return None

    def get_pending_actions(self) -> List[Action]:
        """获取待处理的行动（用于女巫查看狼刀目标等）"""
        return self._pending_actions.copy()

    def is_hunter_pending(self) -> bool:
        """检查是否有猎人需要开枪"""
        return self._hunter_pending

    def clear_hunter_pending(self) -> None:
        """清除猎人待开枪状态"""
        self._hunter_pending = False
