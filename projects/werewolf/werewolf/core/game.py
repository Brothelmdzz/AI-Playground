# ==================== 游戏主控制器 ====================
"""Game 类：游戏状态机和核心接口"""

from __future__ import annotations
import random
from typing import List, Optional, Dict, Callable, Awaitable

from werewolf.core.enums import GamePhase, Faction, ActionType
from werewolf.core.player import Player
from werewolf.core.events import GameEvent, Action, ActionResult, PhaseResult
from werewolf.config.presets import GameConfig
from werewolf.roles import create_role, Role


class Game:
    """
    游戏主控制器

    提供游戏的核心接口：
    - setup(): 初始化游戏，分配角色
    - submit_action(): 提交玩家行动
    - advance_phase(): 推进游戏阶段
    - get_player_view(): 获取玩家视角（信息隔离）

    Attributes:
        config: 游戏配置
        players: 玩家列表
        phase: 当前阶段
        round: 当前回合
        history: 游戏事件历史
    """

    def __init__(self, config: GameConfig, seed: Optional[int] = None):
        """
        Args:
            config: 游戏配置
            seed: 随机种子（用于确定性复现）
        """
        # 验证配置
        valid, msg = config.validate()
        if not valid:
            raise ValueError(f"配置无效: {msg}")

        self.config = config
        self.seed = seed
        self.rng = random.Random(seed)

        self.players: List[Player] = []
        self.phase: GamePhase = GamePhase.INIT
        self.round: int = 0
        self.history: List[GameEvent] = []

        self._moderator: Optional["Moderator"] = None

    async def setup(self, player_names: List[str]) -> None:
        """
        初始化游戏，分配角色

        Args:
            player_names: 玩家名称列表（长度必须与配置人数一致）
        """
        if len(player_names) != self.config.player_count:
            raise ValueError(
                f"玩家数量不匹配: 需要 {self.config.player_count}，"
                f"实际 {len(player_names)}"
            )

        # 创建角色并随机分配
        roles = [create_role(role_type) for role_type in self.config.roles]
        self.rng.shuffle(roles)

        # 创建玩家
        self.players = [
            Player(id=i, name=name, role=role)
            for i, (name, role) in enumerate(zip(player_names, roles))
        ]

        # 初始化主持人
        from werewolf.engine.moderator import Moderator
        self._moderator = Moderator(self)

    async def start(self) -> None:
        """开始游戏"""
        if self._moderator is None:
            raise RuntimeError("游戏未初始化，请先调用 setup()")
        await self._moderator.start_game()

    async def submit_action(self, player_id: int, action: Action) -> ActionResult:
        """
        提交玩家行动

        Args:
            player_id: 玩家ID
            action: 行动

        Returns:
            行动结果
        """
        if self._moderator is None:
            return ActionResult.fail("游戏未初始化")
        return await self._moderator.submit_action(player_id, action)

    async def advance_phase(self) -> PhaseResult:
        """
        推进到下一阶段

        Returns:
            阶段结算结果
        """
        if self._moderator is None:
            raise RuntimeError("游戏未初始化")
        return await self._moderator.advance_phase()

    # ==================== 查询接口 ====================

    def get_player(self, player_id: int) -> Optional[Player]:
        """获取玩家"""
        if 0 <= player_id < len(self.players):
            return self.players[player_id]
        return None

    def get_alive_players(self) -> List[Player]:
        """获取所有存活玩家"""
        return [p for p in self.players if p.is_alive]

    def get_players_by_faction(self, faction: Faction) -> List[Player]:
        """获取指定阵营的玩家"""
        return [p for p in self.players if p.role.faction == faction]

    def get_players_by_role(self, role_name: str) -> List[Player]:
        """获取指定角色的玩家"""
        return [p for p in self.players if p.role.name == role_name]

    def get_active_players(self) -> List[int]:
        """
        获取当前阶段需要行动的玩家ID列表

        Returns:
            玩家ID列表
        """
        if self.phase == GamePhase.NIGHT:
            # 夜间：所有存活且可以夜间行动的玩家
            return [
                p.id for p in self.get_alive_players()
                if p.role.can_act_at_night
            ]
        elif self.phase == GamePhase.DAY_VOTE:
            # 投票：所有存活玩家
            return [p.id for p in self.get_alive_players()]
        else:
            return []

    def get_pending_actions(self) -> List[Action]:
        """获取待处理的行动"""
        if self._moderator:
            return self._moderator.get_pending_actions()
        return []

    def get_winner(self) -> Optional[Faction]:
        """获取胜利阵营（游戏结束时）"""
        if self.phase != GamePhase.GAME_OVER:
            return None

        alive = self.get_alive_players()
        wolf_count = sum(1 for p in alive if p.role.faction == Faction.WEREWOLF)

        if wolf_count == 0:
            return Faction.VILLAGER
        return Faction.WEREWOLF

    # ==================== 信息隔离 ====================

    def get_player_view(self, player_id: int) -> "PlayerView":
        """
        获取玩家可见的游戏信息

        实现信息隔离：每个玩家只能看到自己应该知道的信息。

        Args:
            player_id: 玩家ID

        Returns:
            PlayerView: 该玩家的视角
        """
        player = self.get_player(player_id)
        if player is None:
            raise ValueError(f"玩家不存在: {player_id}")

        return PlayerView(self, player)

    # ==================== 事件系统 ====================

    def add_event(self, event: GameEvent) -> None:
        """添加游戏事件"""
        self.history.append(event)

    def get_visible_events(self, player_id: int) -> List[GameEvent]:
        """获取玩家可见的事件"""
        events = []
        for event in self.history:
            if event.visible_to is None:
                continue  # 仅系统可见
            if len(event.visible_to) == 0:
                events.append(event)  # 全体可见
            elif player_id in event.visible_to:
                events.append(event)  # 该玩家可见
        return events


class PlayerView:
    """
    玩家视角

    封装玩家可见的游戏信息，实现信息隔离。
    """

    def __init__(self, game: Game, player: Player):
        self._game = game
        self._player = player

    @property
    def my_id(self) -> int:
        """我的ID"""
        return self._player.id

    @property
    def my_name(self) -> str:
        """我的名称"""
        return self._player.name

    @property
    def my_role(self) -> Role:
        """我的角色"""
        return self._player.role

    @property
    def phase(self) -> GamePhase:
        """当前阶段"""
        return self._game.phase

    @property
    def round(self) -> int:
        """当前回合"""
        return self._game.round

    @property
    def alive_players(self) -> List[Dict]:
        """
        存活玩家列表（只有基础信息）

        Returns:
            [{"id": 0, "name": "Alice", "is_alive": True}, ...]
        """
        return [
            {"id": p.id, "name": p.name, "is_alive": p.is_alive}
            for p in self._game.players
        ]

    @property
    def teammates(self) -> Optional[List[Dict]]:
        """
        队友信息（仅狼人可见）

        Returns:
            狼人阵营玩家列表，或None
        """
        if self._player.role.faction != Faction.WEREWOLF:
            return None

        return [
            {"id": p.id, "name": p.name, "role": p.role.name}
            for p in self._game.get_players_by_faction(Faction.WEREWOLF)
        ]

    @property
    def available_actions(self) -> List[ActionType]:
        """当前可用的行动"""
        return self._player.role.get_available_actions(
            self._player, self._game
        )

    @property
    def wolf_target_tonight(self) -> Optional[int]:
        """
        今晚被狼杀的目标（仅女巫可见）

        Returns:
            被杀玩家ID，或None
        """
        if self._player.role.name != "女巫":
            return None

        for action in self._game.get_pending_actions():
            if action.action_type == ActionType.KILL:
                return action.target_id
        return None

    def get_visible_history(self) -> List[GameEvent]:
        """获取可见的历史事件"""
        return self._game.get_visible_events(self._player.id)
