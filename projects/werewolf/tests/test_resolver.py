# ==================== 结算器测试 ====================
"""测试夜间结算和投票结算逻辑"""

import pytest
from werewolf.engine.resolver import NightResolver
from werewolf.engine.vote import VoteManager
from werewolf.core.enums import ActionType, DeathReason
from werewolf.core.events import Action
from werewolf.core.player import Player
from werewolf.roles import Villager, Werewolf, Witch, Guard


class MockGame:
    """测试用 Mock Game"""

    def __init__(self, players):
        self.players = players

    def get_player(self, player_id):
        for p in self.players:
            if p.id == player_id:
                return p
        return None

    def get_alive_players(self):
        return [p for p in self.players if p.is_alive]


class TestNightResolver:
    """夜间结算测试"""

    @pytest.fixture
    def resolver(self):
        return NightResolver()

    @pytest.fixture
    def basic_game(self):
        """基础游戏设置：1狼人、1平民"""
        players = [
            Player(id=0, name="Wolf", role=Werewolf()),
            Player(id=1, name="Villager", role=Villager()),
        ]
        return MockGame(players)

    @pytest.mark.asyncio
    async def test_wolf_kill_success(self, resolver, basic_game):
        """狼人击杀成功"""
        actions = [
            Action(ActionType.KILL, actor_id=0, target_id=1)
        ]

        result = await resolver.resolve(basic_game, actions)

        assert len(result.deaths) == 1
        assert result.deaths[0] == (1, DeathReason.WOLF_KILL)

    @pytest.mark.asyncio
    async def test_guard_protection(self, resolver):
        """守卫保护阻止狼刀"""
        players = [
            Player(id=0, name="Wolf", role=Werewolf()),
            Player(id=1, name="Villager", role=Villager()),
            Player(id=2, name="Guard", role=Guard()),
        ]
        game = MockGame(players)

        actions = [
            Action(ActionType.PROTECT, actor_id=2, target_id=1),
            Action(ActionType.KILL, actor_id=0, target_id=1),
        ]

        result = await resolver.resolve(game, actions)

        # 被保护，不应死亡
        assert len(result.deaths) == 0
        assert players[1].night_state.protected is True

    @pytest.mark.asyncio
    async def test_witch_save(self, resolver):
        """女巫解药救人"""
        players = [
            Player(id=0, name="Wolf", role=Werewolf()),
            Player(id=1, name="Villager", role=Villager()),
            Player(id=2, name="Witch", role=Witch()),
        ]
        game = MockGame(players)

        actions = [
            Action(ActionType.KILL, actor_id=0, target_id=1),
            Action(ActionType.SAVE, actor_id=2),
        ]

        result = await resolver.resolve(game, actions)

        # 被救了，不应死亡
        assert len(result.deaths) == 0
        assert players[1].night_state.saved is True

    @pytest.mark.asyncio
    async def test_witch_poison(self, resolver):
        """女巫毒药杀人"""
        players = [
            Player(id=0, name="Wolf", role=Werewolf()),
            Player(id=1, name="Villager1", role=Villager()),
            Player(id=2, name="Villager2", role=Villager()),
            Player(id=3, name="Witch", role=Witch()),
        ]
        game = MockGame(players)

        actions = [
            Action(ActionType.KILL, actor_id=0, target_id=1),
            Action(ActionType.POISON, actor_id=3, target_id=2),
        ]

        result = await resolver.resolve(game, actions)

        # 两人死亡
        assert len(result.deaths) == 2
        death_dict = dict(result.deaths)
        assert death_dict[1] == DeathReason.WOLF_KILL
        assert death_dict[2] == DeathReason.WITCH_POISON

    @pytest.mark.asyncio
    async def test_multi_wolf_vote(self, resolver):
        """多狼投票：多数决"""
        players = [
            Player(id=0, name="Wolf1", role=Werewolf()),
            Player(id=1, name="Wolf2", role=Werewolf()),
            Player(id=2, name="Wolf3", role=Werewolf()),
            Player(id=3, name="Villager1", role=Villager()),
            Player(id=4, name="Villager2", role=Villager()),
        ]
        game = MockGame(players)

        # 2狼选3号，1狼选4号
        actions = [
            Action(ActionType.KILL, actor_id=0, target_id=3),
            Action(ActionType.KILL, actor_id=1, target_id=3),
            Action(ActionType.KILL, actor_id=2, target_id=4),
        ]

        result = await resolver.resolve(game, actions)

        # 3号死亡（多数决）
        assert len(result.deaths) == 1
        assert result.deaths[0][0] == 3


class TestVoteManager:
    """投票结算测试"""

    @pytest.fixture
    def vote_manager(self):
        return VoteManager()

    @pytest.fixture
    def basic_game(self):
        players = [
            Player(id=0, name="P0", role=Villager()),
            Player(id=1, name="P1", role=Villager()),
            Player(id=2, name="P2", role=Villager()),
            Player(id=3, name="P3", role=Villager()),
        ]
        return MockGame(players)

    @pytest.mark.asyncio
    async def test_clear_majority(self, vote_manager, basic_game):
        """明确多数票"""
        vote_actions = [
            Action(ActionType.VOTE, actor_id=0, target_id=1),
            Action(ActionType.VOTE, actor_id=1, target_id=2),
            Action(ActionType.VOTE, actor_id=2, target_id=1),
            Action(ActionType.VOTE, actor_id=3, target_id=1),
        ]

        result = await vote_manager.resolve(basic_game, vote_actions)

        assert result.eliminated_id == 1
        assert result.is_tie is False
        assert result.vote_counts[1] == 3

    @pytest.mark.asyncio
    async def test_tie_no_elimination(self, vote_manager, basic_game):
        """平票不处决"""
        vote_actions = [
            Action(ActionType.VOTE, actor_id=0, target_id=1),
            Action(ActionType.VOTE, actor_id=1, target_id=0),
            Action(ActionType.VOTE, actor_id=2, target_id=1),
            Action(ActionType.VOTE, actor_id=3, target_id=0),
        ]

        result = await vote_manager.resolve(basic_game, vote_actions)

        assert result.is_tie is True
        assert result.eliminated_id is None

    @pytest.mark.asyncio
    async def test_abstain_votes(self, vote_manager, basic_game):
        """弃权投票"""
        vote_actions = [
            Action(ActionType.VOTE, actor_id=0, target_id=1),
            Action(ActionType.SKIP, actor_id=1),
            Action(ActionType.SKIP, actor_id=2),
            Action(ActionType.VOTE, actor_id=3, target_id=1),
        ]

        result = await vote_manager.resolve(basic_game, vote_actions)

        assert result.eliminated_id == 1
        assert result.vote_counts[1] == 2
