# ==================== Roles Module ====================
"""角色系统模块"""

from werewolf.roles.base import Role
from werewolf.roles.villager import Villager
from werewolf.roles.werewolf import Werewolf
from werewolf.roles.seer import Seer
from werewolf.roles.witch import Witch
from werewolf.roles.hunter import Hunter
from werewolf.roles.guard import Guard

__all__ = [
    "Role",
    "Villager",
    "Werewolf",
    "Seer",
    "Witch",
    "Hunter",
    "Guard",
]

# 角色注册表（用于配置解析）
ROLE_REGISTRY: dict[str, type[Role]] = {
    "villager": Villager,
    "werewolf": Werewolf,
    "seer": Seer,
    "witch": Witch,
    "hunter": Hunter,
    "guard": Guard,
}


def create_role(role_type: str) -> Role:
    """根据角色类型创建角色实例"""
    if role_type not in ROLE_REGISTRY:
        raise ValueError(f"未知角色类型: {role_type}")
    return ROLE_REGISTRY[role_type]()
