# ==================== CLI 运行器 ====================
"""支持人类参与的 CLI 交互运行器"""

from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING, Optional, List, Dict

from werewolf.core.game import Game
from werewolf.core.enums import GamePhase, Faction
from werewolf.agents.base import BaseAgent
from werewolf.agents.human_agent import HumanAgent
from werewolf.agents.random_agent import RandomAgent
from werewolf.runner.game_runner import GameRunner, GameResult

if TYPE_CHECKING:
    from werewolf.config.presets import GameConfig
    from werewolf.llm.base import BaseLLMClient


class CLIRunner:
    """
    CLI 运行器

    支持人类玩家参与的命令行交互游戏
    """

    def __init__(
        self,
        config: GameConfig,
        human_player_id: int = 0,
        llm_client: Optional[BaseLLMClient] = None,
        seed: Optional[int] = None,
    ):
        """
        Args:
            config: 游戏配置
            human_player_id: 人类玩家的ID（位置）
            llm_client: LLM 客户端（用于其他玩家），如果为None则使用随机Agent
            seed: 随机种子
        """
        self.config = config
        self.human_player_id = human_player_id
        self.llm_client = llm_client
        self.seed = seed

    async def run(self) -> GameResult:
        """运行游戏"""
        # 获取人类玩家名称
        print("\n" + "=" * 60)
        print("欢迎来到狼人杀！")
        print("=" * 60)

        human_name = input("请输入你的名字: ").strip() or "Human"

        # 生成玩家名称
        player_names = []
        ai_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank",
                    "Grace", "Henry", "Ivy", "Jack", "Kate", "Leo"]
        ai_index = 0

        for i in range(self.config.player_count):
            if i == self.human_player_id:
                player_names.append(human_name)
            else:
                player_names.append(ai_names[ai_index % len(ai_names)])
                ai_index += 1

        # 创建 Agent 工厂
        def agent_factory(player_id: int, game: Game) -> BaseAgent:
            if player_id == self.human_player_id:
                return HumanAgent(player_id, game, name=human_name)
            elif self.llm_client:
                from werewolf.agents.llm_agent import LLMAgent
                return LLMAgent(
                    player_id, game, self.llm_client,
                    name=player_names[player_id]
                )
            else:
                return RandomAgent(
                    player_id, game,
                    name=player_names[player_id],
                    seed=self.seed
                )

        # 使用 GameRunner 运行
        runner = GameRunner(
            config=self.config,
            agent_factory=agent_factory,
            player_names=player_names,
            seed=self.seed,
            verbose=True
        )

        return await runner.run()


async def quick_play(
    config: Optional[GameConfig] = None,
    llm_client: Optional[BaseLLMClient] = None,
):
    """
    快速开始一局游戏

    Args:
        config: 游戏配置，默认6人局
        llm_client: LLM 客户端
    """
    from werewolf.config.presets import PRESET_6P

    if config is None:
        config = PRESET_6P

    runner = CLIRunner(
        config=config,
        human_player_id=0,
        llm_client=llm_client,
    )

    result = await runner.run()

    print("\n感谢游玩！")
    return result


if __name__ == "__main__":
    asyncio.run(quick_play())
