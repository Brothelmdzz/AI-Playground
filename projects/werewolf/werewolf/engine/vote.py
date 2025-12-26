# ==================== 投票逻辑 ====================
"""处理白天投票的逻辑"""

from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Optional
from collections import Counter

from werewolf.core.enums import ActionType
from werewolf.core.events import Action, VoteResult

if TYPE_CHECKING:
    from werewolf.core.game import Game


class VoteManager:
    """
    投票管理器

    负责处理白天投票逻辑：
    - 收集所有玩家投票
    - 统计得票数
    - 判定是否平票
    - 确定被处决者
    """

    def __init__(self, tie_policy: str = "no_elimination"):
        """
        Args:
            tie_policy: 平票处理策略
                - "no_elimination": 平票不处决（默认）
                - "random": 平票随机选择
                - "revote": 平票重新投票（需外部处理）
        """
        self.tie_policy = tie_policy

    async def resolve(
        self, game: Game, vote_actions: List[Action]
    ) -> VoteResult:
        """
        结算投票

        Args:
            game: 游戏实例
            vote_actions: 投票行动列表

        Returns:
            VoteResult: 投票结果
        """
        result = VoteResult()

        # 收集投票 {voter_id: target_id}
        votes: Dict[int, Optional[int]] = {}
        for action in vote_actions:
            if action.action_type == ActionType.VOTE:
                votes[action.actor_id] = action.target_id
            elif action.action_type == ActionType.SKIP:
                votes[action.actor_id] = None  # 弃权

        result.votes = votes

        # 统计得票（排除弃权）
        valid_votes = [t for t in votes.values() if t is not None]
        vote_counts = Counter(valid_votes)
        result.vote_counts = dict(vote_counts)

        if not vote_counts:
            # 所有人都弃权
            result.is_tie = False
            result.eliminated_id = None
            return result

        # 找出最高票
        most_common = vote_counts.most_common()
        top_count = most_common[0][1]
        tied_players = [player_id for player_id, count in most_common if count == top_count]

        if len(tied_players) == 1:
            # 无平票，处决最高票者
            result.eliminated_id = tied_players[0]
            result.is_tie = False
        else:
            # 平票
            result.is_tie = True
            if self.tie_policy == "no_elimination":
                result.eliminated_id = None
            elif self.tie_policy == "random":
                # 实际实现时应使用游戏的随机数生成器
                result.eliminated_id = tied_players[0]
            # "revote" 策略需要外部处理

        return result

    def format_vote_summary(self, result: VoteResult, game: Game) -> str:
        """
        格式化投票摘要

        Returns:
            人类可读的投票结果字符串
        """
        lines = ["投票结果:"]

        # 按得票数排序
        sorted_counts = sorted(
            result.vote_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        for player_id, count in sorted_counts:
            player = game.get_player(player_id)
            name = player.name if player else f"P{player_id}"
            lines.append(f"  {name}: {count} 票")

        # 弃权统计
        abstain_count = sum(1 for t in result.votes.values() if t is None)
        if abstain_count > 0:
            lines.append(f"  弃权: {abstain_count} 人")

        # 结果
        if result.is_tie:
            lines.append("结果: 平票，无人被处决")
        elif result.eliminated_id is not None:
            player = game.get_player(result.eliminated_id)
            name = player.name if player else f"P{result.eliminated_id}"
            lines.append(f"结果: {name} 被处决")
        else:
            lines.append("结果: 无人被处决")

        return "\n".join(lines)
