# ==================== 游戏服务 ====================
"""管理游戏实例的生命周期"""

from __future__ import annotations
import asyncio
import uuid
import logging
import traceback
from typing import Dict, List, Optional, Callable, Any, Coroutine
from datetime import datetime
from dataclasses import dataclass, field

import sys
sys.path.insert(0, str(__file__).replace("\\", "/").rsplit("/web/", 1)[0])

from werewolf.core.game import Game
from werewolf.core.enums import GamePhase, Faction, ActionType
from werewolf.config.presets import PRESET_6P, PRESET_9P, PRESET_12P, GameConfig
from werewolf.agents.base import BaseAgent
from werewolf.agents.random_agent import RandomAgent
from werewolf.agents.llm_agent import LLMAgent
from werewolf.runner.game_runner import GameRunner, GameResult
from werewolf.config.settings import get_settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from ..models.schemas import (
    GameMode, PlayerType, GameState, PlayerInfo, GameEvent,
    CreateGameRequest, GameListItem
)


PRESETS = {
    "6p": PRESET_6P,
    "9p": PRESET_9P,
    "12p": PRESET_12P,
}


@dataclass
class GameSession:
    """游戏会话"""
    game_id: str
    game: Optional[Game] = None
    config: Optional[GameConfig] = None
    mode: GameMode = GameMode.AI_VS_AI
    status: str = "waiting"  # waiting, running, finished
    created_at: datetime = field(default_factory=datetime.now)

    # 玩家映射
    human_players: Dict[int, str] = field(default_factory=dict)  # seat_id -> connection_id
    player_names: List[str] = field(default_factory=list)
    player_types: Dict[int, PlayerType] = field(default_factory=dict)

    # 游戏控制
    speed: float = 1.0
    is_paused: bool = False
    runner: Optional[GameRunner] = None
    runner_task: Optional[asyncio.Task] = None

    # 事件历史
    events: List[GameEvent] = field(default_factory=list)

    # 回调
    on_state_change: Optional[Callable[[GameState], Any]] = None
    on_event: Optional[Callable[[GameEvent], Any]] = None


class GameService:
    """游戏服务 - 管理所有游戏实例"""

    def __init__(self):
        self.sessions: Dict[str, GameSession] = {}
        self._lock = asyncio.Lock()

    async def create_game(self, request: CreateGameRequest) -> GameSession:
        """创建新游戏"""
        game_id = str(uuid.uuid4())[:8]

        config = PRESETS.get(request.preset, PRESET_6P)

        session = GameSession(
            game_id=game_id,
            config=config,
            mode=request.mode,
            speed=request.speed,
        )

        # 初始化玩家名称
        session.player_names = [f"Player_{i}" for i in range(config.player_count)]

        # 根据模式设置玩家类型
        for i in range(config.player_count):
            if request.mode == GameMode.AI_VS_AI:
                session.player_types[i] = PlayerType.AI_RANDOM
            else:
                # 第一个位置留给人类
                session.player_types[i] = PlayerType.HUMAN if i == 0 else PlayerType.AI_RANDOM

        async with self._lock:
            self.sessions[game_id] = session

        return session

    async def get_session(self, game_id: str) -> Optional[GameSession]:
        """获取游戏会话"""
        return self.sessions.get(game_id)

    async def list_games(self) -> List[GameListItem]:
        """列出所有游戏"""
        items = []
        for session in self.sessions.values():
            items.append(GameListItem(
                game_id=session.game_id,
                status=session.status,
                mode=session.mode,
                player_count=session.config.player_count if session.config else 0,
                created_at=session.created_at,
            ))
        return items

    async def join_game(
        self,
        game_id: str,
        player_name: str,
        connection_id: str,
        seat_id: Optional[int] = None,
    ) -> Optional[int]:
        """加入游戏，返回座位号"""
        session = await self.get_session(game_id)
        if not session or session.status != "waiting":
            return None

        # 找空位
        if seat_id is not None:
            if seat_id in session.human_players:
                return None  # 座位已占
        else:
            # 找第一个空的人类座位
            for i, ptype in session.player_types.items():
                if ptype == PlayerType.HUMAN and i not in session.human_players:
                    seat_id = i
                    break

        if seat_id is None:
            return None

        session.human_players[seat_id] = connection_id
        session.player_names[seat_id] = player_name

        return seat_id

    async def start_game(self, game_id: str, seed: Optional[int] = None) -> bool:
        """开始游戏"""
        print(f"[Game {game_id}] start_game called, seed={seed}", flush=True)
        session = await self.get_session(game_id)
        if not session:
            logger.error(f"[Game {game_id}] Session not found")
            return False
        if session.status != "waiting":
            logger.error(f"[Game {game_id}] Session status is {session.status}, expected 'waiting'")
            return False

        # 创建游戏实例
        print(f"[Game {game_id}] Creating game instance with config: {session.config}", flush=True)
        session.game = Game(session.config, seed=seed)
        await session.game.setup(session.player_names)
        print(f"[Game {game_id}] Game setup complete, players: {session.player_names}", flush=True)

        await session.game.start()
        print(f"[Game {game_id}] Game started, phase: {session.game.phase.value}, round: {session.game.round}", flush=True)

        session.status = "running"

        # AI vs AI 模式：自动运行
        if session.mode == GameMode.AI_VS_AI or session.mode == GameMode.SPECTATE:
            logger.info(f"[Game {game_id}] Mode is {session.mode.value}, starting AI game task...")
            session.runner_task = asyncio.create_task(
                self._run_ai_game(session)
            )
            logger.info(f"[Game {game_id}] AI game task created")
        else:
            logger.info(f"[Game {game_id}] Mode is {session.mode.value}, waiting for human input")

        return True

    async def _run_ai_game(self, session: GameSession):
        """运行 AI 对战"""
        print(f"[Game {session.game_id}] === AI GAME LOOP STARTED ===", flush=True)
        game = session.game

        # 尝试获取 LLM 客户端
        llm_client = None
        try:
            settings = get_settings()
            provider = settings.llm.default_provider
            print(f"[Game {session.game_id}] Default LLM provider: {provider}", flush=True)

            # 获取对应提供商的配置
            provider_config = getattr(settings.llm, provider, None)
            if provider_config and provider_config.api_key:
                logger.info(f"[Game {session.game_id}] API key found for {provider}, creating LLM client...")
                llm_client = settings.get_llm_client()
                logger.info(f"[Game {session.game_id}] LLM client created successfully")
            else:
                logger.warning(f"[Game {session.game_id}] No API key for {provider}, using RandomAgent")
        except Exception as e:
            logger.error(f"[Game {session.game_id}] LLM client error: {e}")
            logger.error(traceback.format_exc())

        # 创建 agents
        agents: Dict[int, BaseAgent] = {}
        for i in range(session.config.player_count):
            if llm_client:
                agents[i] = LLMAgent(i, game, llm_client, name=f"AI_{i}")
            else:
                agents[i] = RandomAgent(i, game, seed=42 + i)

        agent_type = "LLMAgent" if llm_client else "RandomAgent"
        logger.info(f"[Game {session.game_id}] Created {len(agents)} {agent_type} agents")

        try:
            loop_count = 0
            while game.phase != GamePhase.GAME_OVER:
                loop_count += 1
                print(f"[Game {session.game_id}] Loop #{loop_count}, Phase: {game.phase.value}, Round: {game.round}", flush=True)

                if session.is_paused:
                    await asyncio.sleep(0.1)
                    continue

                # 广播状态
                await self._broadcast_state(session)

                # 处理当前阶段
                if game.phase == GamePhase.NIGHT:
                    logger.info(f"[Game {session.game_id}] Processing NIGHT phase...")
                    await self._process_night(session, agents)
                elif game.phase == GamePhase.DAY_DISCUSSION:
                    logger.info(f"[Game {session.game_id}] Processing DAY_DISCUSSION phase...")
                    await self._process_discussion(session, agents)
                elif game.phase == GamePhase.DAY_VOTE:
                    logger.info(f"[Game {session.game_id}] Processing DAY_VOTE phase...")
                    await self._process_vote(session, agents)
                else:
                    logger.warning(f"[Game {session.game_id}] Unhandled phase: {game.phase.value}")

                # 推进阶段
                logger.info(f"[Game {session.game_id}] Advancing phase...")
                result = await game.advance_phase()
                logger.info(f"[Game {session.game_id}] Phase advanced to: {game.phase.value}")

                # 记录事件
                event = GameEvent(
                    round=game.round,
                    phase=game.phase.value,
                    event_type="phase_change",
                    description=f"进入 {game.phase.value} 阶段",
                )
                session.events.append(event)
                if session.on_event:
                    try:
                        result = session.on_event(event)
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception as e:
                        logger.error(f"[Game {session.game_id}] Event callback error: {e}")

                # 控制速度
                await asyncio.sleep(1.0 / session.speed)

            # 游戏结束
            logger.info(f"[Game {session.game_id}] Game finished! Winner: {game.get_winner()}")
            session.status = "finished"
            await self._broadcast_state(session)

        except asyncio.CancelledError:
            logger.info(f"[Game {session.game_id}] Game cancelled")
        except Exception as e:
            session.status = "error"
            logger.error(f"[Game {session.game_id}] Game error: {e}")
            logger.error(traceback.format_exc())

    async def _process_night(self, session: GameSession, agents: Dict[int, BaseAgent]):
        """处理夜间阶段"""
        game = session.game
        alive_players = game.get_alive_players()
        logger.info(f"[Game {session.game_id}] Night: {len(alive_players)} alive players")

        for player in alive_players:
            if player.id in agents:
                logger.info(f"[Game {session.game_id}] Player {player.id} ({player.name}) deciding action...")
                try:
                    action = await agents[player.id].decide_action()
                    if action:
                        result = await game.submit_action(player.id, action)
                        logger.info(f"[Game {session.game_id}] Player {player.id} action: {action.action_type.value}, result: {result.success}")

                        event = GameEvent(
                            round=game.round,
                            phase="night",
                            event_type="action",
                            description=f"{player.name} 执行了夜间行动",
                        )
                        session.events.append(event)
                    else:
                        logger.info(f"[Game {session.game_id}] Player {player.id} skipped action")
                except Exception as e:
                    logger.error(f"[Game {session.game_id}] Player {player.id} action error: {e}")
                    logger.error(traceback.format_exc())

    async def _process_discussion(self, session: GameSession, agents: Dict[int, BaseAgent]):
        """处理讨论阶段"""
        game = session.game
        alive_players = game.get_alive_players()
        logger.info(f"[Game {session.game_id}] Discussion: {len(alive_players)} players speaking")

        for player in alive_players:
            if player.id in agents:
                try:
                    logger.info(f"[Game {session.game_id}] Player {player.id} speaking...")
                    speech = await agents[player.id].speak()
                    logger.info(f"[Game {session.game_id}] Player {player.id} said: {speech[:50]}...")

                    event = GameEvent(
                        round=game.round,
                        phase="day_discussion",
                        event_type="speech",
                        description=f"{player.name}: {speech}",
                        details={"player_id": player.id, "content": speech},
                    )
                    session.events.append(event)
                    if session.on_event:
                        try:
                            result = session.on_event(event)
                            if asyncio.iscoroutine(result):
                                await result
                        except Exception as e:
                            logger.error(f"[Game {session.game_id}] Event callback error: {e}")

                    await asyncio.sleep(0.5 / session.speed)
                except Exception as e:
                    logger.error(f"[Game {session.game_id}] Player {player.id} speak error: {e}")
                    logger.error(traceback.format_exc())

    async def _process_vote(self, session: GameSession, agents: Dict[int, BaseAgent]):
        """处理投票阶段"""
        game = session.game
        alive_players = game.get_alive_players()
        logger.info(f"[Game {session.game_id}] Vote: {len(alive_players)} players voting")

        for player in alive_players:
            if player.id in agents:
                try:
                    logger.info(f"[Game {session.game_id}] Player {player.id} voting...")
                    action = await agents[player.id].decide_action()
                    if action:
                        result = await game.submit_action(player.id, action)
                        logger.info(f"[Game {session.game_id}] Player {player.id} voted: {action.target_id}, result: {result.success}")
                except Exception as e:
                    logger.error(f"[Game {session.game_id}] Player {player.id} vote error: {e}")
                    logger.error(traceback.format_exc())

    async def _broadcast_state(self, session: GameSession):
        """广播游戏状态"""
        if session.on_state_change:
            state = self.get_game_state(session)
            try:
                result = session.on_state_change(state)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"[Game {session.game_id}] Broadcast state error: {e}")

    def get_game_state(self, session: GameSession, viewer_id: Optional[int] = None) -> GameState:
        """获取游戏状态"""
        game = session.game

        if not game:
            return GameState(
                game_id=session.game_id,
                status=session.status,
                phase="waiting",
                round=0,
                players=[],
                alive_count=0,
            )

        # 构建玩家列表
        players = []
        for p in game.players:
            # 角色信息可见性
            show_role = (
                session.status == "finished" or  # 游戏结束
                viewer_id == p.id  # 自己
            )

            players.append(PlayerInfo(
                id=p.id,
                name=p.name,
                is_alive=p.is_alive,
                player_type=session.player_types.get(p.id, PlayerType.AI_RANDOM),
                role=p.role.name if show_role else None,
                faction=p.role.faction.value if show_role else None,
            ))

        return GameState(
            game_id=session.game_id,
            status=session.status,
            phase=game.phase.value,
            round=game.round,
            players=players,
            alive_count=len(game.get_alive_players()),
            events=session.events[-20:],  # 最近20条事件
            winner=game.get_winner().value if game.phase == GamePhase.GAME_OVER else None,
        )

    async def pause_game(self, game_id: str) -> bool:
        """暂停游戏"""
        session = await self.get_session(game_id)
        if session and session.status == "running":
            session.is_paused = True
            return True
        return False

    async def resume_game(self, game_id: str) -> bool:
        """恢复游戏"""
        session = await self.get_session(game_id)
        if session and session.status == "running":
            session.is_paused = False
            return True
        return False

    async def set_speed(self, game_id: str, speed: float) -> bool:
        """设置游戏速度"""
        session = await self.get_session(game_id)
        if session:
            session.speed = max(0.1, min(10.0, speed))
            return True
        return False


# 全局单例
game_service = GameService()
