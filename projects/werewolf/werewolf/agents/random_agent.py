# ==================== 随机 Agent ====================
"""随机决策的 Agent，用作基线对比"""

from __future__ import annotations
import random
from typing import TYPE_CHECKING, Optional, List

from werewolf.agents.base import BaseAgent
from werewolf.core.enums import ActionType
from werewolf.core.events import Action

if TYPE_CHECKING:
    from werewolf.core.game import Game


class RandomAgent(BaseAgent):
    """
    随机 Agent

    随机选择可用行动和目标，用于：
    - 基线对比
    - 快速测试
    - 填充玩家
    """

    def __init__(
        self,
        player_id: int,
        game: Game,
        name: Optional[str] = None,
        seed: Optional[int] = None,
    ):
        """
        Args:
            player_id: 玩家ID
            game: 游戏实例
            name: Agent 名称
            seed: 随机种子
        """
        super().__init__(player_id, game, name or f"RandomBot_{player_id}")
        self.rng = random.Random(seed)

    async def decide_action(self) -> Action:
        """随机选择行动"""
        view = self.get_view()
        available_actions = view.available_actions

        if not available_actions:
            return Action(ActionType.SKIP, actor_id=self.player_id)

        # 随机选择行动类型
        action_type = self.rng.choice(available_actions)

        # 确定目标
        target_id = None
        if action_type in (ActionType.KILL, ActionType.CHECK, ActionType.POISON,
                           ActionType.PROTECT, ActionType.VOTE, ActionType.SHOOT):
            # 需要选择目标
            alive_players = [
                p["id"] for p in view.alive_players
                if p["is_alive"] and p["id"] != self.player_id
            ]
            if alive_players:
                target_id = self.rng.choice(alive_players)
            else:
                # 没有可选目标，跳过
                action_type = ActionType.SKIP

        elif action_type == ActionType.SAVE:
            # 女巫解药：目标是被狼杀的人
            target_id = view.wolf_target_tonight

        return Action(
            action_type=action_type,
            actor_id=self.player_id,
            target_id=target_id
        )

    async def speak(self) -> str:
        """随机发言"""
        phrases = [
            "我没什么特别想说的。",
            "我觉得大家都挺可疑的。",
            "我是好人，请相信我。",
            "让我再观察一下。",
            "我同意上一位的发言。",
            "我觉得应该投那个发言最少的人。",
            "我暂时没有确切的线索。",
            "请大家理性分析。",
        ]
        return self.rng.choice(phrases)
