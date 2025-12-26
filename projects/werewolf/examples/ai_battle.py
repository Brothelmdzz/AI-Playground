#!/usr/bin/env python3
# ==================== AI 对战示例 ====================
"""
演示 AI vs AI 对战

使用方法:
1. 设置环境变量 OPENAI_API_KEY 或 ANTHROPIC_API_KEY
2. 运行: python examples/ai_battle.py

可选参数:
- --provider: openai 或 anthropic (默认 openai)
- --model: 模型名称
- --seed: 随机种子
"""

import asyncio
import argparse
import logging
import os

from werewolf.config.presets import PRESET_6P, PRESET_9P
from werewolf.runner.game_runner import GameRunner
from werewolf.agents.random_agent import RandomAgent
from werewolf.agents.llm_agent import LLMAgent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_llm_client(provider: str, model: str = None):
    """创建 LLM 客户端"""
    if provider == "openai":
        from werewolf.llm.openai_client import OpenAIClient
        return OpenAIClient(model=model or "gpt-4o-mini")
    elif provider == "anthropic":
        from werewolf.llm.anthropic_client import AnthropicClient
        return AnthropicClient(model=model or "claude-3-5-haiku-20241022")
    else:
        raise ValueError(f"未知 provider: {provider}")


async def run_llm_battle(
    provider: str = "openai",
    model: str = None,
    seed: int = 42,
):
    """运行 LLM 对战"""
    print(f"\n使用 {provider} ({model or 'default'}) 进行对战\n")

    try:
        llm_client = create_llm_client(provider, model)
    except ImportError as e:
        print(f"缺少依赖: {e}")
        print("请安装: pip install werewolf[llm]")
        return None

    config = PRESET_6P

    def agent_factory(player_id, game):
        return LLMAgent(
            player_id, game, llm_client,
            name=f"AI_{player_id}",
            temperature=0.7
        )

    runner = GameRunner(
        config=config,
        agent_factory=agent_factory,
        seed=seed,
        verbose=True
    )

    result = await runner.run()
    return result


async def run_random_battle(seed: int = 42):
    """运行随机 Agent 对战（用于测试）"""
    print("\n使用随机 Agent 进行对战\n")

    config = PRESET_6P

    def agent_factory(player_id, game):
        return RandomAgent(player_id, game, seed=seed + player_id)

    runner = GameRunner(
        config=config,
        agent_factory=agent_factory,
        seed=seed,
        verbose=True
    )

    result = await runner.run()
    return result


async def run_mixed_battle(seed: int = 42):
    """混合对战：部分 LLM，部分随机"""
    print("\n混合对战: 狼人使用 LLM，村民使用随机\n")

    # 尝试创建 LLM 客户端
    llm_client = None
    try:
        if os.getenv("OPENAI_API_KEY"):
            from werewolf.llm.openai_client import OpenAIClient
            llm_client = OpenAIClient(model="gpt-4o-mini")
        elif os.getenv("ANTHROPIC_API_KEY"):
            from werewolf.llm.anthropic_client import AnthropicClient
            llm_client = AnthropicClient(model="claude-3-5-haiku-20241022")
    except ImportError:
        pass

    if not llm_client:
        print("未找到 API Key，回退到纯随机对战")
        return await run_random_battle(seed)

    config = PRESET_6P

    def agent_factory(player_id, game):
        player = game.get_player(player_id)
        # 狼人使用 LLM
        if player.role.name == "狼人":
            return LLMAgent(
                player_id, game, llm_client,
                name=f"LLM_Wolf_{player_id}"
            )
        else:
            return RandomAgent(player_id, game, seed=seed + player_id)

    runner = GameRunner(
        config=config,
        agent_factory=agent_factory,
        seed=seed,
        verbose=True
    )

    result = await runner.run()
    return result


def main():
    parser = argparse.ArgumentParser(description="AI 狼人杀对战")
    parser.add_argument(
        "--mode",
        choices=["llm", "random", "mixed"],
        default="random",
        help="对战模式: llm(纯LLM), random(纯随机), mixed(混合)"
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic"],
        default="openai",
        help="LLM 提供商"
    )
    parser.add_argument("--model", type=str, help="模型名称")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")

    args = parser.parse_args()

    if args.mode == "llm":
        asyncio.run(run_llm_battle(args.provider, args.model, args.seed))
    elif args.mode == "random":
        asyncio.run(run_random_battle(args.seed))
    elif args.mode == "mixed":
        asyncio.run(run_mixed_battle(args.seed))


if __name__ == "__main__":
    main()
