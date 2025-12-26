# ==================== 游戏运行器 ====================
"""自动运行 AI vs AI 对战"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Optional, List, Dict, Any

from werewolf.core.game import Game
from werewolf.core.enums import GamePhase, Faction
from werewolf.core.events import GameEvent
from werewolf.agents.base import BaseAgent

if TYPE_CHECKING:
    from werewolf.config.presets import GameConfig

logger = logging.getLogger(__name__)


@dataclass
class GameResult:
    """
    游戏结果

    Attributes:
        winner: 胜利阵营
        rounds: 总回合数
        history: 游戏事件历史
        speeches: 发言记录
        agent_logs: Agent 决策日志
    """
    winner: Optional[Faction] = None
    rounds: int = 0
    history: List[GameEvent] = field(default_factory=list)
    speeches: List[Dict[str, Any]] = field(default_factory=list)
    agent_logs: List[Dict[str, Any]] = field(default_factory=list)


class GameRunner:
    """
    游戏运行器

    驱动 AI vs AI 自动对战
    """

    def __init__(
        self,
        config: GameConfig,
        agent_factory: Callable[[int, Game], BaseAgent],
        player_names: Optional[List[str]] = None,
        seed: Optional[int] = None,
        verbose: bool = True,
    ):
        """
        Args:
            config: 游戏配置
            agent_factory: Agent 工厂函数 (player_id, game) -> BaseAgent
            player_names: 玩家名称列表
            seed: 随机种子
            verbose: 是否输出详细日志
        """
        self.config = config
        self.agent_factory = agent_factory
        self.player_names = player_names or [
            f"Player_{i}" for i in range(config.player_count)
        ]
        self.seed = seed
        self.verbose = verbose

    async def run(self) -> GameResult:
        """运行完整游戏"""
        result = GameResult()

        # 创建游戏
        game = Game(self.config, seed=self.seed)
        await game.setup(self.player_names)

        # 创建 Agents
        agents: Dict[int, BaseAgent] = {}
        for player in game.players:
            agent = self.agent_factory(player.id, game)
            agents[player.id] = agent

        if self.verbose:
            self._print_game_start(game)

        # 开始游戏
        await game.start()
        result.rounds = game.round

        # 游戏主循环
        while game.phase != GamePhase.GAME_OVER:
            if self.verbose:
                self._print_phase(game)

            if game.phase == GamePhase.NIGHT:
                await self._run_night(game, agents, result)
            elif game.phase == GamePhase.DAY_DISCUSSION:
                await self._run_discussion(game, agents, result)
            elif game.phase == GamePhase.DAY_VOTE:
                await self._run_vote(game, agents, result)

            # 推进阶段
            phase_result = await game.advance_phase()

            if self.verbose:
                self._print_phase_result(game, phase_result)

            # 检查游戏结束
            if phase_result.winner:
                result.winner = phase_result.winner
                break

            result.rounds = game.round

        # 保存历史
        result.history = game.history

        if self.verbose:
            self._print_game_end(result)

        return result

    async def _run_night(
        self,
        game: Game,
        agents: Dict[int, BaseAgent],
        result: GameResult
    ) -> None:
        """运行夜间阶段"""
        for player in game.get_alive_players():
            if not player.role.can_act_at_night:
                continue

            agent = agents.get(player.id)
            if not agent:
                continue

            try:
                action = await agent.decide_action()
                action_result = await game.submit_action(player.id, action)

                result.agent_logs.append({
                    "round": game.round,
                    "phase": "night",
                    "player_id": player.id,
                    "player_name": player.name,
                    "role": player.role.name,
                    "action": action.action_type.value,
                    "target": action.target_id,
                    "success": action_result.success,
                })

                if self.verbose:
                    logger.info(
                        f"  [{player.name}({player.role.name})] "
                        f"{action.action_type.value} -> {action.target_id}"
                    )

            except Exception as e:
                logger.error(f"Agent {player.id} 决策失败: {e}")

    async def _run_discussion(
        self,
        game: Game,
        agents: Dict[int, BaseAgent],
        result: GameResult
    ) -> None:
        """运行讨论阶段"""
        for player in game.get_alive_players():
            agent = agents.get(player.id)
            if not agent:
                continue

            try:
                speech = await agent.speak()

                result.speeches.append({
                    "round": game.round,
                    "player_id": player.id,
                    "player_name": player.name,
                    "content": speech,
                })

                if self.verbose:
                    print(f"  [{player.name}]: {speech[:80]}{'...' if len(speech) > 80 else ''}")

            except Exception as e:
                logger.error(f"Agent {player.id} 发言失败: {e}")

    async def _run_vote(
        self,
        game: Game,
        agents: Dict[int, BaseAgent],
        result: GameResult
    ) -> None:
        """运行投票阶段"""
        for player in game.get_alive_players():
            agent = agents.get(player.id)
            if not agent:
                continue

            try:
                action = await agent.decide_action()
                await game.submit_action(player.id, action)

                result.agent_logs.append({
                    "round": game.round,
                    "phase": "vote",
                    "player_id": player.id,
                    "player_name": player.name,
                    "action": action.action_type.value,
                    "target": action.target_id,
                })

                if self.verbose:
                    target_name = "弃权"
                    if action.target_id is not None:
                        target = game.get_player(action.target_id)
                        target_name = target.name if target else str(action.target_id)
                    print(f"  [{player.name}] 投票 -> {target_name}")

            except Exception as e:
                logger.error(f"Agent {player.id} 投票失败: {e}")

    def _print_game_start(self, game: Game) -> None:
        """打印游戏开始信息"""
        print("\n" + "=" * 60)
        print("狼人杀游戏开始")
        print("=" * 60)
        print(f"配置: {self.config.name}")
        print(f"玩家数: {len(game.players)}")
        print("\n角色分配:")
        for p in game.players:
            print(f"  {p.id}. {p.name} - {p.role.name} ({p.role.faction.value})")
        print()

    def _print_phase(self, game: Game) -> None:
        """打印阶段信息"""
        phase_names = {
            GamePhase.NIGHT: "夜间",
            GamePhase.DAY_DISCUSSION: "白天讨论",
            GamePhase.DAY_VOTE: "白天投票",
        }
        phase_name = phase_names.get(game.phase, game.phase.value)
        print(f"\n--- 第 {game.round} 回合 {phase_name} ---")

    def _print_phase_result(self, game: Game, phase_result) -> None:
        """打印阶段结果"""
        if phase_result.deaths:
            print(f"\n死亡玩家: {phase_result.deaths}")
        for msg in phase_result.messages:
            print(f"  {msg}")

    def _print_game_end(self, result: GameResult) -> None:
        """打印游戏结束信息"""
        print("\n" + "=" * 60)
        print("游戏结束")
        print("=" * 60)
        winner_name = "狼人" if result.winner == Faction.WEREWOLF else "村民"
        print(f"胜利阵营: {winner_name}")
        print(f"总回合数: {result.rounds}")
        print()
