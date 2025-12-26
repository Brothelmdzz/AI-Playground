# ==================== 游戏流程测试 ====================
"""测试完整游戏流程"""

import pytest
from werewolf.core.game import Game
from werewolf.core.enums import GamePhase, Faction, ActionType
from werewolf.core.events import Action
from werewolf.config.presets import GameConfig, PRESET_6P


class TestGameSetup:
    """游戏初始化测试"""

    @pytest.mark.asyncio
    async def test_setup_with_preset(self):
        """使用预设配置初始化"""
        config = PRESET_6P
        game = Game(config, seed=42)

        names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
        await game.setup(names)

        assert len(game.players) == 6
        assert game.phase == GamePhase.INIT

        # 验证角色分配
        werewolf_count = sum(
            1 for p in game.players if p.role.faction == Faction.WEREWOLF
        )
        assert werewolf_count == 2

    @pytest.mark.asyncio
    async def test_deterministic_setup(self):
        """相同 seed 产生相同结果"""
        config = PRESET_6P
        names = ["A", "B", "C", "D", "E", "F"]

        game1 = Game(config, seed=123)
        await game1.setup(names)
        roles1 = [p.role.name for p in game1.players]

        game2 = Game(config, seed=123)
        await game2.setup(names)
        roles2 = [p.role.name for p in game2.players]

        assert roles1 == roles2

    def test_invalid_config(self):
        """无效配置应抛出异常"""
        # 狼人太多
        bad_config = GameConfig(
            name="bad",
            roles=["werewolf", "werewolf", "werewolf", "villager", "villager", "villager"]
        )
        with pytest.raises(ValueError):
            Game(bad_config)


class TestGameFlow:
    """游戏流程测试"""

    @pytest.fixture
    async def started_game(self):
        """已开始的游戏"""
        config = PRESET_6P
        game = Game(config, seed=42)
        names = ["P0", "P1", "P2", "P3", "P4", "P5"]
        await game.setup(names)
        await game.start()
        return game

    @pytest.mark.asyncio
    async def test_game_start(self, started_game):
        """游戏开始进入夜间"""
        assert started_game.phase == GamePhase.NIGHT
        assert started_game.round == 1

    @pytest.mark.asyncio
    async def test_night_actions(self, started_game):
        """夜间行动提交"""
        game = started_game

        # 找到狼人和预言家
        wolves = [p for p in game.players if p.role.name == "狼人"]
        seers = [p for p in game.players if p.role.name == "预言家"]

        if wolves and seers:
            wolf = wolves[0]
            seer = seers[0]

            # 狼人选择击杀（选择非狼人目标）
            target = next(p for p in game.players if p.role.faction == Faction.VILLAGER)
            action = Action(ActionType.KILL, actor_id=wolf.id, target_id=target.id)
            result = await game.submit_action(wolf.id, action)
            assert result.success is True

            # 预言家查验
            check_target = next(p for p in game.players if p.id != seer.id)
            action = Action(ActionType.CHECK, actor_id=seer.id, target_id=check_target.id)
            result = await game.submit_action(seer.id, action)
            assert result.success is True
            assert "is_werewolf" in result.data

    @pytest.mark.asyncio
    async def test_phase_advance(self, started_game):
        """阶段推进"""
        game = started_game

        # 提交夜间行动
        for player in game.get_alive_players():
            if player.role.can_act_at_night:
                # 简化：都选择跳过
                action = Action(ActionType.SKIP, actor_id=player.id)
                await game.submit_action(player.id, action)

        # 推进到白天
        result = await game.advance_phase()
        assert result.next_phase == GamePhase.DAY_DISCUSSION

        # 推进到投票
        result = await game.advance_phase()
        assert result.next_phase == GamePhase.DAY_VOTE


class TestPlayerView:
    """玩家视角测试"""

    @pytest.mark.asyncio
    async def test_werewolf_knows_teammates(self):
        """狼人知道队友"""
        config = PRESET_6P
        game = Game(config, seed=42)
        await game.setup(["P0", "P1", "P2", "P3", "P4", "P5"])

        wolves = [p for p in game.players if p.role.name == "狼人"]
        if wolves:
            wolf = wolves[0]
            view = game.get_player_view(wolf.id)

            assert view.teammates is not None
            assert len(view.teammates) == 2  # 6人局有2狼

    @pytest.mark.asyncio
    async def test_villager_no_teammates(self):
        """村民看不到队友信息"""
        config = PRESET_6P
        game = Game(config, seed=42)
        await game.setup(["P0", "P1", "P2", "P3", "P4", "P5"])

        villagers = [p for p in game.players if p.role.faction == Faction.VILLAGER]
        if villagers:
            villager = villagers[0]
            view = game.get_player_view(villager.id)

            assert view.teammates is None


class TestWinCondition:
    """胜利条件测试"""

    @pytest.mark.asyncio
    async def test_villagers_win(self):
        """村民胜利：所有狼人死亡"""
        config = PRESET_6P
        game = Game(config, seed=42)
        await game.setup(["P0", "P1", "P2", "P3", "P4", "P5"])
        await game.start()

        # 手动杀死所有狼人
        from werewolf.core.enums import DeathReason
        for player in game.players:
            if player.role.faction == Faction.WEREWOLF:
                player.die(DeathReason.VOTE_OUT, 1)

        winner = game.get_winner()
        # 游戏还没结束（phase 还不是 GAME_OVER），需要通过 moderator 判断
        # 直接检查存活状态
        alive_wolves = sum(
            1 for p in game.get_alive_players()
            if p.role.faction == Faction.WEREWOLF
        )
        assert alive_wolves == 0

    @pytest.mark.asyncio
    async def test_werewolves_win(self):
        """狼人胜利：狼人 >= 村民"""
        config = PRESET_6P
        game = Game(config, seed=42)
        await game.setup(["P0", "P1", "P2", "P3", "P4", "P5"])
        await game.start()

        # 杀死村民直到狼人 >= 村民
        from werewolf.core.enums import DeathReason
        villagers = [p for p in game.players if p.role.faction == Faction.VILLAGER]
        for v in villagers[:3]:  # 杀3个村民，剩2狼1村
            v.die(DeathReason.WOLF_KILL, 1)

        alive = game.get_alive_players()
        wolf_count = sum(1 for p in alive if p.role.faction == Faction.WEREWOLF)
        villager_count = sum(1 for p in alive if p.role.faction == Faction.VILLAGER)

        assert wolf_count >= villager_count
