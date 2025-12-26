# ==================== Benchmark 服务 ====================
"""运行多局游戏的 Benchmark"""

from __future__ import annotations
import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict

import sys
sys.path.insert(0, str(__file__).replace("\\", "/").rsplit("/web/", 1)[0])

from werewolf.core.game import Game
from werewolf.core.enums import Faction
from werewolf.config.presets import PRESET_6P, PRESET_9P, PRESET_12P
from werewolf.agents.random_agent import RandomAgent
from werewolf.runner.game_runner import GameRunner

from ..models.schemas import BenchmarkRequest, BenchmarkResult


PRESETS = {
    "6p": PRESET_6P,
    "9p": PRESET_9P,
    "12p": PRESET_12P,
}


@dataclass
class BenchmarkSession:
    """Benchmark 会话"""
    benchmark_id: str
    request: BenchmarkRequest
    status: str = "running"  # running, completed, error
    created_at: datetime = field(default_factory=datetime.now)

    # 进度
    total_games: int = 0
    completed_games: int = 0

    # 结果
    results: Dict[str, Any] = field(default_factory=dict)
    game_logs: List[Dict[str, Any]] = field(default_factory=list)

    # 任务
    task: Optional[asyncio.Task] = None


class BenchmarkService:
    """Benchmark 服务"""

    def __init__(self):
        self.sessions: Dict[str, BenchmarkSession] = {}

    async def start_benchmark(self, request: BenchmarkRequest) -> BenchmarkSession:
        """启动 Benchmark"""
        benchmark_id = str(uuid.uuid4())[:8]

        session = BenchmarkSession(
            benchmark_id=benchmark_id,
            request=request,
            total_games=request.num_games,
        )

        self.sessions[benchmark_id] = session

        # 启动后台任务
        session.task = asyncio.create_task(self._run_benchmark(session))

        return session

    async def _run_benchmark(self, session: BenchmarkSession):
        """运行 Benchmark"""
        request = session.request
        config = PRESETS.get(request.preset, PRESET_6P)

        # 统计数据
        wins = defaultdict(int)  # faction -> count
        round_counts = []
        game_durations = []

        try:
            for i in range(request.num_games):
                seed = (request.seed or 0) + i

                # 创建游戏
                def agent_factory(player_id, game):
                    return RandomAgent(player_id, game, seed=seed + player_id)

                runner = GameRunner(
                    config=config,
                    agent_factory=agent_factory,
                    seed=seed,
                    verbose=False,
                )

                start_time = datetime.now()
                result = await runner.run()
                duration = (datetime.now() - start_time).total_seconds()

                # 记录结果
                wins[result.winner.value] += 1
                round_counts.append(result.rounds)
                game_durations.append(duration)

                session.game_logs.append({
                    "game_index": i,
                    "winner": result.winner.value,
                    "rounds": result.rounds,
                    "duration": duration,
                    "seed": seed,
                })

                session.completed_games = i + 1

            # 计算统计
            total = session.total_games
            session.results = {
                "win_rates": {
                    faction: count / total
                    for faction, count in wins.items()
                },
                "wins": dict(wins),
                "avg_rounds": sum(round_counts) / len(round_counts) if round_counts else 0,
                "min_rounds": min(round_counts) if round_counts else 0,
                "max_rounds": max(round_counts) if round_counts else 0,
                "avg_duration": sum(game_durations) / len(game_durations) if game_durations else 0,
                "total_duration": sum(game_durations),
            }

            session.status = "completed"

        except asyncio.CancelledError:
            session.status = "cancelled"
        except Exception as e:
            session.status = "error"
            session.results["error"] = str(e)

    async def get_session(self, benchmark_id: str) -> Optional[BenchmarkSession]:
        """获取 Benchmark 会话"""
        return self.sessions.get(benchmark_id)

    def get_result(self, session: BenchmarkSession) -> BenchmarkResult:
        """获取 Benchmark 结果"""
        return BenchmarkResult(
            benchmark_id=session.benchmark_id,
            status=session.status,
            total_games=session.total_games,
            completed_games=session.completed_games,
            results=session.results if session.status == "completed" else None,
        )

    async def cancel_benchmark(self, benchmark_id: str) -> bool:
        """取消 Benchmark"""
        session = await self.get_session(benchmark_id)
        if session and session.task:
            session.task.cancel()
            return True
        return False


# 全局单例
benchmark_service = BenchmarkService()
