# ==================== 游戏配置 ====================
"""预设游戏配置"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class GameConfig:
    """
    游戏配置

    Attributes:
        name: 配置名称
        roles: 角色列表（按类型名称），如 ["werewolf", "werewolf", "seer", ...]
        rules: 规则配置
    """
    name: str
    roles: List[str]
    rules: Dict[str, Any] = field(default_factory=dict)

    @property
    def player_count(self) -> int:
        """玩家人数"""
        return len(self.roles)

    @property
    def werewolf_count(self) -> int:
        """狼人数量"""
        return sum(1 for r in self.roles if r == "werewolf")

    @property
    def villager_count(self) -> int:
        """村民阵营数量（含神职）"""
        return sum(1 for r in self.roles if r != "werewolf")

    def validate(self) -> tuple[bool, str]:
        """
        验证配置是否合法

        Returns:
            (是否合法, 错误信息)
        """
        if len(self.roles) < 6:
            return False, "玩家人数不能少于6人"

        if self.werewolf_count == 0:
            return False, "至少需要1个狼人"

        if self.werewolf_count >= self.villager_count:
            return False, "狼人数量不能大于等于村民数量"

        # 检查角色类型是否有效
        valid_roles = {"villager", "werewolf", "seer", "witch", "hunter", "guard"}
        for role in self.roles:
            if role not in valid_roles:
                return False, f"未知角色类型: {role}"

        return True, ""

    @classmethod
    def preset_6p(cls) -> GameConfig:
        """6人简化局"""
        return PRESET_6P

    @classmethod
    def preset_9p(cls) -> GameConfig:
        """9人标准局"""
        return PRESET_9P

    @classmethod
    def preset_12p(cls) -> GameConfig:
        """12人标准局"""
        return PRESET_12P

    @classmethod
    def custom(
        cls,
        werewolves: int = 3,
        seers: int = 1,
        witches: int = 1,
        hunters: int = 1,
        guards: int = 0,
        villagers: int = 3,
        **rules
    ) -> GameConfig:
        """
        自定义配置

        Args:
            werewolves: 狼人数量
            seers: 预言家数量
            witches: 女巫数量
            hunters: 猎人数量
            guards: 守卫数量
            villagers: 平民数量
            **rules: 额外规则配置

        Returns:
            游戏配置
        """
        roles = (
            ["werewolf"] * werewolves +
            ["seer"] * seers +
            ["witch"] * witches +
            ["hunter"] * hunters +
            ["guard"] * guards +
            ["villager"] * villagers
        )
        return cls(
            name=f"自定义{len(roles)}人局",
            roles=roles,
            rules=rules
        )


# ==================== 预设配置 ====================

# 6人简化局：快速验证，适合测试
PRESET_6P = GameConfig(
    name="6人简化局",
    roles=[
        "werewolf", "werewolf",  # 2狼
        "seer",                   # 预言家
        "witch",                  # 女巫
        "villager", "villager",   # 2平民
    ],
    rules={
        "witch_can_self_save": False,  # 女巫不能自救
        "first_night_no_kill": False,  # 首夜可以杀人
    }
)

# 9人标准局：经典配置
PRESET_9P = GameConfig(
    name="9人标准局",
    roles=[
        "werewolf", "werewolf", "werewolf",  # 3狼
        "seer",                               # 预言家
        "witch",                              # 女巫
        "hunter",                             # 猎人
        "villager", "villager", "villager",   # 3平民
    ],
    rules={
        "witch_can_self_save": False,
        "first_night_no_kill": False,
    }
)

# 12人标准局：完整配置
PRESET_12P = GameConfig(
    name="12人标准局",
    roles=[
        "werewolf", "werewolf", "werewolf", "werewolf",  # 4狼
        "seer",                                           # 预言家
        "witch",                                          # 女巫
        "hunter",                                         # 猎人
        "guard",                                          # 守卫
        "villager", "villager", "villager", "villager",   # 4平民
    ],
    rules={
        "witch_can_self_save": False,
        "first_night_no_kill": False,
        "guard_can_self_protect": True,  # 守卫可以守自己
    }
)
