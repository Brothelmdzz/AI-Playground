# ==================== 游戏事件 ====================
"""行动、事件和结果定义"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, List
from datetime import datetime

from werewolf.core.enums import ActionType, GamePhase, DeathReason, Faction


@dataclass
class Action:
    """
    玩家行动

    Attributes:
        action_type: 行动类型
        actor_id: 行动者玩家ID
        target_id: 目标玩家ID（可选，如弃权时无目标）
        extra: 额外数据（扩展用）
    """
    action_type: ActionType
    actor_id: int
    target_id: Optional[int] = None
    extra: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        target = f" -> {self.target_id}" if self.target_id is not None else ""
        return f"Action({self.action_type.value}, P{self.actor_id}{target})"


@dataclass
class ActionResult:
    """
    行动结果

    Attributes:
        success: 行动是否成功提交
        message: 结果消息
        data: 附加数据（如预言家查验结果）
    """
    success: bool
    message: str = ""
    data: dict = field(default_factory=dict)

    @classmethod
    def ok(cls, message: str = "", **data) -> ActionResult:
        return cls(success=True, message=message, data=data)

    @classmethod
    def fail(cls, message: str) -> ActionResult:
        return cls(success=False, message=message)


@dataclass
class GameEvent:
    """
    游戏事件（用于历史记录和回放）

    Attributes:
        event_type: 事件类型
        round_num: 回合数
        phase: 发生阶段
        timestamp: 时间戳
        data: 事件数据
        visible_to: 可见玩家ID列表（空列表=全体可见，None=仅系统）
    """
    event_type: str
    round_num: int
    phase: GamePhase
    data: dict = field(default_factory=dict)
    visible_to: Optional[List[int]] = None
    timestamp: datetime = field(default_factory=datetime.now)

    # 事件类型常量
    GAME_START = "game_start"
    PHASE_CHANGE = "phase_change"
    PLAYER_ACTION = "player_action"
    PLAYER_DEATH = "player_death"
    VOTE_RESULT = "vote_result"
    GAME_END = "game_end"


@dataclass
class PhaseResult:
    """
    阶段结算结果

    Attributes:
        phase: 刚结束的阶段
        deaths: 本阶段死亡的玩家ID列表
        messages: 公开消息
        next_phase: 下一阶段
        winner: 胜利阵营（游戏结束时）
    """
    phase: GamePhase
    deaths: List[int] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)
    next_phase: Optional[GamePhase] = None
    winner: Optional[Faction] = None


@dataclass
class NightResult:
    """
    夜间结算结果

    Attributes:
        deaths: 死亡玩家列表 [(player_id, death_reason), ...]
        hunter_can_shoot: 猎人是否可以开枪（正常死亡时可以）
        messages: 结算消息
    """
    deaths: List[tuple[int, DeathReason]] = field(default_factory=list)
    hunter_can_shoot: bool = False
    hunter_id: Optional[int] = None
    messages: List[str] = field(default_factory=list)


@dataclass
class VoteResult:
    """
    投票结算结果

    Attributes:
        votes: 投票详情 {voter_id: target_id}
        vote_counts: 得票统计 {target_id: count}
        eliminated_id: 被处决玩家ID（平票时为None）
        is_tie: 是否平票
    """
    votes: dict[int, Optional[int]] = field(default_factory=dict)
    vote_counts: dict[int, int] = field(default_factory=dict)
    eliminated_id: Optional[int] = None
    is_tie: bool = False
