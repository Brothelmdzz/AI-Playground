# ==================== 角色测试 ====================
"""测试各角色的能力和行为"""

import pytest
from werewolf.roles import Villager, Werewolf, Seer, Witch, Hunter, Guard
from werewolf.core.enums import Faction, ActionType, GamePhase, DeathReason
from werewolf.core.player import Player
from werewolf.core.events import Action


class TestVillager:
    """平民测试"""

    def test_basic_properties(self):
        villager = Villager()
        assert villager.name == "平民"
        assert villager.faction == Faction.VILLAGER
        assert villager.can_act_at_night is False

    def test_no_night_actions(self):
        villager = Villager()
        player = Player(id=0, name="TestPlayer", role=villager)
        # 平民没有夜间行动
        actions = villager.get_available_actions(player, None)
        assert actions == []


class TestWerewolf:
    """狼人测试"""

    def test_basic_properties(self):
        wolf = Werewolf()
        assert wolf.name == "狼人"
        assert wolf.faction == Faction.WEREWOLF
        assert wolf.can_act_at_night is True
        assert wolf.priority == 10

    def test_validate_kill_action(self):
        wolf = Werewolf()
        player = Player(id=0, name="Wolf", role=wolf)
        target = Player(id=1, name="Target", role=Villager())

        # 创建一个 mock game
        class MockGame:
            phase = GamePhase.NIGHT
            def get_player(self, pid):
                if pid == 1:
                    return target
                return None

        game = MockGame()

        # 有效的击杀行动
        action = Action(ActionType.KILL, actor_id=0, target_id=1)
        valid, msg = wolf.validate_action(action, player, game)
        assert valid is True

        # 无目标
        action = Action(ActionType.KILL, actor_id=0, target_id=None)
        valid, msg = wolf.validate_action(action, player, game)
        assert valid is False
        assert "必须指定目标" in msg


class TestSeer:
    """预言家测试"""

    def test_basic_properties(self):
        seer = Seer()
        assert seer.name == "预言家"
        assert seer.faction == Faction.VILLAGER
        assert seer.can_act_at_night is True

    @pytest.mark.asyncio
    async def test_check_werewolf(self):
        seer = Seer()
        player = Player(id=0, name="Seer", role=seer)
        wolf = Player(id=1, name="Wolf", role=Werewolf())

        class MockGame:
            phase = GamePhase.NIGHT
            def get_player(self, pid):
                if pid == 1:
                    return wolf
                return None

        game = MockGame()
        action = Action(ActionType.CHECK, actor_id=0, target_id=1)

        result = await seer.execute_action(action, player, game)
        assert result.success is True
        assert result.data["is_werewolf"] is True

    @pytest.mark.asyncio
    async def test_check_villager(self):
        seer = Seer()
        player = Player(id=0, name="Seer", role=seer)
        villager = Player(id=1, name="Villager", role=Villager())

        class MockGame:
            phase = GamePhase.NIGHT
            def get_player(self, pid):
                if pid == 1:
                    return villager
                return None

        game = MockGame()
        action = Action(ActionType.CHECK, actor_id=0, target_id=1)

        result = await seer.execute_action(action, player, game)
        assert result.success is True
        assert result.data["is_werewolf"] is False


class TestWitch:
    """女巫测试"""

    def test_basic_properties(self):
        witch = Witch()
        assert witch.name == "女巫"
        assert witch.faction == Faction.VILLAGER
        assert witch.state.has_save_potion is True
        assert witch.state.has_poison_potion is True

    @pytest.mark.asyncio
    async def test_use_save_potion(self):
        witch = Witch()
        player = Player(id=0, name="Witch", role=witch)
        target = Player(id=1, name="Target", role=Villager())

        class MockGame:
            phase = GamePhase.NIGHT
            _pending = [Action(ActionType.KILL, actor_id=2, target_id=1)]

            def get_player(self, pid):
                if pid == 1:
                    return target
                return None

            def get_pending_actions(self):
                return self._pending

        game = MockGame()
        action = Action(ActionType.SAVE, actor_id=0)

        result = await witch.execute_action(action, player, game)
        assert result.success is True
        assert witch.state.has_save_potion is False

    @pytest.mark.asyncio
    async def test_use_poison_potion(self):
        witch = Witch()
        player = Player(id=0, name="Witch", role=witch)
        target = Player(id=1, name="Target", role=Villager())

        class MockGame:
            phase = GamePhase.NIGHT
            def get_player(self, pid):
                if pid == 1:
                    return target
                return None
            def get_pending_actions(self):
                return []

        game = MockGame()
        action = Action(ActionType.POISON, actor_id=0, target_id=1)

        result = await witch.execute_action(action, player, game)
        assert result.success is True
        assert witch.state.has_poison_potion is False


class TestHunter:
    """猎人测试"""

    def test_basic_properties(self):
        hunter = Hunter()
        assert hunter.name == "猎人"
        assert hunter.faction == Faction.VILLAGER
        assert hunter.can_shoot is True

    def test_can_shoot_when_killed_by_wolf(self):
        hunter = Hunter()
        player = Player(id=0, name="Hunter", role=hunter)
        player.death_reason = DeathReason.WOLF_KILL

        trigger = hunter.on_death(player, None)
        assert trigger == ActionType.SHOOT

    def test_cannot_shoot_when_poisoned(self):
        hunter = Hunter()
        player = Player(id=0, name="Hunter", role=hunter)
        player.death_reason = DeathReason.WITCH_POISON

        trigger = hunter.on_death(player, None)
        assert trigger is None
        assert hunter.can_shoot is False


class TestGuard:
    """守卫测试"""

    def test_basic_properties(self):
        guard = Guard()
        assert guard.name == "守卫"
        assert guard.faction == Faction.VILLAGER
        assert guard.can_act_at_night is True
        assert guard.priority == 5  # 最先行动

    def test_cannot_protect_same_player_twice(self):
        guard = Guard()
        player = Player(id=0, name="Guard", role=guard)
        target = Player(id=1, name="Target", role=Villager())

        class MockGame:
            phase = GamePhase.NIGHT
            def get_player(self, pid):
                if pid == 1:
                    return target
                return None

        game = MockGame()

        # 第一次保护
        guard.last_protected_id = 1

        # 尝试再次保护同一人
        action = Action(ActionType.PROTECT, actor_id=0, target_id=1)
        valid, msg = guard.validate_action(action, player, game)
        assert valid is False
        assert "不能连续两晚" in msg
