# ==================== Agent 测试 ====================
"""测试 Agent 模块"""

import pytest
from werewolf.core.game import Game
from werewolf.core.enums import ActionType, GamePhase
from werewolf.config.presets import PRESET_6P
from werewolf.agents.random_agent import RandomAgent


class TestRandomAgent:
    """随机 Agent 测试"""

    @pytest.fixture
    async def game_with_agent(self):
        """创建带 Agent 的游戏"""
        game = Game(PRESET_6P, seed=42)
        await game.setup(["P0", "P1", "P2", "P3", "P4", "P5"])
        await game.start()
        return game

    @pytest.mark.asyncio
    async def test_random_agent_creation(self, game_with_agent):
        """测试随机 Agent 创建"""
        game = game_with_agent
        agent = RandomAgent(0, game, seed=42)

        assert agent.player_id == 0
        assert agent.name == "RandomBot_0"

    @pytest.mark.asyncio
    async def test_random_agent_decide_action(self, game_with_agent):
        """测试随机 Agent 决策"""
        game = game_with_agent
        agent = RandomAgent(0, game, seed=42)

        action = await agent.decide_action()

        assert action is not None
        assert action.actor_id == 0
        assert isinstance(action.action_type, ActionType)

    @pytest.mark.asyncio
    async def test_random_agent_speak(self, game_with_agent):
        """测试随机 Agent 发言"""
        game = game_with_agent
        agent = RandomAgent(0, game, seed=42)

        speech = await agent.speak()

        assert isinstance(speech, str)
        assert len(speech) > 0

    @pytest.mark.asyncio
    async def test_random_agent_deterministic(self, game_with_agent):
        """测试相同 seed 产生相同结果"""
        game = game_with_agent

        agent1 = RandomAgent(0, game, seed=123)
        agent2 = RandomAgent(0, game, seed=123)

        speech1 = await agent1.speak()
        speech2 = await agent2.speak()

        assert speech1 == speech2


class TestAgentIntegration:
    """Agent 集成测试"""

    @pytest.mark.asyncio
    async def test_full_round_with_random_agents(self):
        """使用随机 Agent 运行完整回合"""
        from werewolf.runner.game_runner import GameRunner

        config = PRESET_6P

        def agent_factory(player_id, game):
            return RandomAgent(player_id, game, seed=42 + player_id)

        runner = GameRunner(
            config=config,
            agent_factory=agent_factory,
            seed=42,
            verbose=False
        )

        result = await runner.run()

        # 游戏应该正常结束
        assert result.winner is not None
        assert result.rounds > 0
        assert len(result.history) > 0
