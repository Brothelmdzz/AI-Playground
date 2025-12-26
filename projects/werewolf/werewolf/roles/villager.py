# ==================== 平民 ====================
"""平民角色：无特殊能力，依靠发言和投票参与游戏"""

from werewolf.roles.base import Role
from werewolf.core.enums import Faction


class Villager(Role):
    """
    平民

    - 阵营：村民
    - 夜间能力：无
    - 特殊技能：无
    - 胜利条件：与村民阵营共同胜利
    """

    name = "平民"
    faction = Faction.VILLAGER
    priority = 100  # 无夜间行动
    can_act_at_night = False
