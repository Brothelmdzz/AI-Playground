# ==================== 枚举定义 ====================
"""游戏核心枚举类型"""

from enum import Enum, auto


class GamePhase(Enum):
    """游戏阶段"""
    INIT = "init"                       # 初始化，分配角色
    NIGHT = "night"                     # 夜间，玩家行动
    NIGHT_RESOLVE = "night_resolve"     # 夜间结算
    DAY_DISCUSSION = "day_discussion"   # 白天讨论
    DAY_VOTE = "day_vote"               # 白天投票
    DAY_RESOLVE = "day_resolve"         # 投票结算
    GAME_OVER = "game_over"             # 游戏结束


class Faction(Enum):
    """阵营"""
    WEREWOLF = "werewolf"   # 狼人阵营
    VILLAGER = "villager"   # 村民阵营（含神职）


class ActionType(Enum):
    """行动类型"""
    # 夜间行动
    KILL = "kill"           # 狼人击杀
    CHECK = "check"         # 预言家查验
    SAVE = "save"           # 女巫解药
    POISON = "poison"       # 女巫毒药
    PROTECT = "protect"     # 守卫保护
    # 死亡触发
    SHOOT = "shoot"         # 猎人开枪
    # 白天行动
    VOTE = "vote"           # 投票
    SKIP = "skip"           # 跳过（弃权）


class DeathReason(Enum):
    """死亡原因"""
    WOLF_KILL = "wolf_kill"     # 被狼人杀死
    WITCH_POISON = "poison"     # 被女巫毒死
    VOTE_OUT = "vote_out"       # 被投票出局
    HUNTER_SHOT = "shot"        # 被猎人射杀


class RoleType(Enum):
    """角色类型"""
    VILLAGER = "villager"       # 平民
    WEREWOLF = "werewolf"       # 狼人
    SEER = "seer"               # 预言家
    WITCH = "witch"             # 女巫
    HUNTER = "hunter"           # 猎人
    GUARD = "guard"             # 守卫
