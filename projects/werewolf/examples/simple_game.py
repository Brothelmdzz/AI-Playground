#!/usr/bin/env python3
# ==================== 简单游戏示例 ====================
"""
演示如何使用狼人杀游戏引擎

这个示例展示了：
1. 创建游戏配置
2. 初始化游戏
3. 模拟一个完整的游戏回合（夜间 + 白天）
4. 获取玩家视角信息
"""

import asyncio
from werewolf.core.game import Game
from werewolf.core.enums import GamePhase, Faction, ActionType
from werewolf.core.events import Action
from werewolf.config.presets import PRESET_6P, GameConfig


async def simple_game_demo():
    """简单游戏演示"""
    print("=" * 60)
    print("狼人杀游戏引擎演示")
    print("=" * 60)

    # 1. 创建游戏（使用6人简化局）
    config = PRESET_6P
    game = Game(config, seed=42)  # 固定 seed 保证可复现

    print(f"\n配置: {config.name}")
    print(f"角色: {config.roles}")

    # 2. 初始化玩家
    player_names = ["爱丽丝", "鲍勃", "查理", "戴安娜", "伊芙", "弗兰克"]
    await game.setup(player_names)

    print("\n玩家角色分配:")
    for player in game.players:
        print(f"  {player.id}: {player.name} - {player.role.name}")

    # 3. 开始游戏
    await game.start()
    print(f"\n游戏开始! 当前阶段: {game.phase.value}, 回合: {game.round}")

    # 4. 展示狼人视角
    wolves = [p for p in game.players if p.role.faction == Faction.WEREWOLF]
    if wolves:
        wolf = wolves[0]
        view = game.get_player_view(wolf.id)
        print(f"\n{wolf.name}（狼人）的视角:")
        print(f"  我的角色: {view.my_role.name}")
        print(f"  队友: {view.teammates}")
        print(f"  可用行动: {[a.value for a in view.available_actions]}")

    # 5. 模拟夜间行动
    print("\n--- 夜间阶段 ---")

    # 狼人选择击杀
    if len(wolves) >= 1:
        wolf = wolves[0]
        # 选择一个村民作为目标
        target = next(p for p in game.players if p.role.faction == Faction.VILLAGER)
        action = Action(ActionType.KILL, actor_id=wolf.id, target_id=target.id)
        result = await game.submit_action(wolf.id, action)
        print(f"  {wolf.name}（狼人）选择击杀 {target.name}: {result.message}")

    # 预言家查验
    seers = [p for p in game.players if p.role.name == "预言家"]
    if seers:
        seer = seers[0]
        # 查验第一个狼人
        check_target = wolves[0] if wolves else game.players[0]
        action = Action(ActionType.CHECK, actor_id=seer.id, target_id=check_target.id)
        result = await game.submit_action(seer.id, action)
        is_wolf = result.data.get("is_werewolf", False)
        print(f"  {seer.name}（预言家）查验 {check_target.name}: {'狼人' if is_wolf else '好人'}")

    # 女巫行动（跳过）
    witches = [p for p in game.players if p.role.name == "女巫"]
    if witches:
        witch = witches[0]
        action = Action(ActionType.SKIP, actor_id=witch.id)
        result = await game.submit_action(witch.id, action)
        print(f"  {witch.name}（女巫）选择不使用药水")

    # 6. 推进到白天
    night_result = await game.advance_phase()
    print(f"\n夜间结算:")
    for msg in night_result.messages:
        print(f"  {msg}")
    print(f"死亡玩家: {night_result.deaths}")
    print(f"下一阶段: {night_result.next_phase.value if night_result.next_phase else 'N/A'}")

    # 7. 检查胜负
    if night_result.winner:
        print(f"\n游戏结束! 胜利阵营: {night_result.winner.value}")
        return

    # 8. 白天讨论
    print("\n--- 白天讨论阶段 ---")
    print("（玩家发言环节，本示例跳过）")

    # 推进到投票
    await game.advance_phase()
    print(f"当前阶段: {game.phase.value}")

    # 9. 模拟投票
    print("\n--- 投票阶段 ---")
    alive_players = game.get_alive_players()

    # 所有人投票给第一个活着的玩家（简化演示）
    vote_target = alive_players[0]
    for player in alive_players:
        action = Action(ActionType.VOTE, actor_id=player.id, target_id=vote_target.id)
        await game.submit_action(player.id, action)
        print(f"  {player.name} 投票给 {vote_target.name}")

    # 投票结算
    vote_result = await game.advance_phase()
    print(f"\n投票结算:")
    for msg in vote_result.messages:
        print(f"  {msg}")

    # 最终状态
    print(f"\n当前阶段: {game.phase.value}")
    print(f"当前回合: {game.round}")
    if vote_result.winner:
        print(f"游戏结束! 胜利阵营: {vote_result.winner.value}")


async def custom_config_demo():
    """自定义配置演示"""
    print("\n" + "=" * 60)
    print("自定义配置演示")
    print("=" * 60)

    # 创建自定义配置
    config = GameConfig.custom(
        werewolves=3,
        seers=1,
        witches=1,
        hunters=1,
        guards=1,
        villagers=2,
    )

    print(f"配置: {config.name}")
    print(f"总人数: {config.player_count}")
    print(f"狼人: {config.werewolf_count}, 村民阵营: {config.villager_count}")
    print(f"角色列表: {config.roles}")

    # 验证配置
    valid, msg = config.validate()
    print(f"配置验证: {'通过' if valid else f'失败 - {msg}'}")


if __name__ == "__main__":
    print("运行简单游戏演示...\n")
    asyncio.run(simple_game_demo())
    asyncio.run(custom_config_demo())
    print("\n演示完成!")
