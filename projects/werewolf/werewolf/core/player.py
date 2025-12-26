# ==================== 玩家模型 ====================
"""玩家和夜间状态定义"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from werewolf.core.enums import DeathReason

if TYPE_CHECKING:
    from werewolf.roles.base import Role


@dataclass
class NightState:
    """
    夜间状态，每晚开始时重置。
    用于追踪夜间各种行动的效果，在夜间结算时统一处理。
    """
    killed_by_wolf: bool = False        # 被狼人选为击杀目标
    wolf_target_id: Optional[int] = None  # 狼刀目标玩家ID
    protected: bool = False             # 被守卫保护
    saved: bool = False                 # 被女巫解药救了
    poisoned: bool = False              # 被女巫毒药毒了

    def reset(self) -> None:
        """重置夜间状态"""
        self.killed_by_wolf = False
        self.wolf_target_id = None
        self.protected = False
        self.saved = False
        self.poisoned = False


@dataclass
class Player:
    """
    玩家模型

    Attributes:
        id: 玩家唯一标识（座位号，从0开始）
        name: 玩家名称
        role: 角色实例
        is_alive: 是否存活
        death_reason: 死亡原因（存活时为None）
        death_round: 死亡回合（存活时为None）
        night_state: 当前夜间状态
    """
    id: int
    name: str
    role: Optional[Role] = None
    is_alive: bool = True
    death_reason: Optional[DeathReason] = None
    death_round: Optional[int] = None
    night_state: NightState = field(default_factory=NightState)

    def die(self, reason: DeathReason, round_num: int) -> None:
        """玩家死亡"""
        self.is_alive = False
        self.death_reason = reason
        self.death_round = round_num

    def reset_night_state(self) -> None:
        """重置夜间状态（每晚开始时调用）"""
        self.night_state.reset()

    @property
    def role_name(self) -> str:
        """获取角色名称"""
        return self.role.name if self.role else "未分配"

    def __repr__(self) -> str:
        status = "存活" if self.is_alive else f"死亡({self.death_reason.value if self.death_reason else '?'})"
        return f"Player({self.id}, {self.name}, {self.role_name}, {status})"
