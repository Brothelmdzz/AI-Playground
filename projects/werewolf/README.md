# AI 狼人杀游戏引擎

> Phase 1: 纯游戏逻辑引擎，提供完整的狼人杀规则和 API

## 特性

- **纯引擎设计**: 只提供游戏逻辑，不含交互界面
- **可配置**: 支持自定义角色配置和游戏规则
- **异步架构**: 基于 asyncio，为后续 LLM Agent 做准备
- **确定性复现**: 使用 seed 保证相同输入产生相同结果
- **信息隔离**: 通过 PlayerView 实现玩家视角分离

## 安装

```bash
cd projects/werewolf
pip install -e .

# 开发环境
pip install -e ".[dev]"
```

## 快速开始

```python
import asyncio
from werewolf import Game, GameConfig, Action, ActionType

async def main():
    # 1. 创建游戏
    config = GameConfig.preset_9p()  # 9人标准局
    game = Game(config, seed=42)

    # 2. 初始化玩家
    players = ["Alice", "Bob", "Charlie", "David", "Eve",
               "Frank", "Grace", "Henry", "Ivy"]
    await game.setup(players)

    # 3. 开始游戏
    await game.start()

    # 4. 游戏循环
    while game.phase != GamePhase.GAME_OVER:
        # 获取需要行动的玩家
        for player_id in game.get_active_players():
            view = game.get_player_view(player_id)
            # 根据 view 决定行动...
            action = Action(ActionType.SKIP, actor_id=player_id)
            await game.submit_action(player_id, action)

        # 推进阶段
        await game.advance_phase()

    # 5. 获取胜者
    print(f"Winner: {game.get_winner()}")

asyncio.run(main())
```

## 项目结构

```
werewolf/
├── core/           # 核心模型
│   ├── enums.py    # 枚举定义
│   ├── player.py   # 玩家模型
│   ├── events.py   # 事件和行动
│   └── game.py     # 游戏主控制器
├── roles/          # 角色实现
│   ├── base.py     # 角色基类
│   ├── villager.py # 平民
│   ├── werewolf.py # 狼人
│   ├── seer.py     # 预言家
│   ├── witch.py    # 女巫
│   ├── hunter.py   # 猎人
│   └── guard.py    # 守卫
├── engine/         # 游戏引擎
│   ├── moderator.py # 主持人
│   ├── resolver.py  # 夜间结算
│   └── vote.py      # 投票逻辑
└── config/         # 配置
    └── presets.py  # 预设配置
```

## 支持的角色

| 角色 | 阵营 | 能力 |
|------|------|------|
| 平民 | 村民 | 无特殊能力 |
| 狼人 | 狼人 | 夜间击杀一人 |
| 预言家 | 村民 | 夜间查验一人身份 |
| 女巫 | 村民 | 解药救人/毒药杀人（各一次） |
| 猎人 | 村民 | 正常死亡时可开枪带走一人 |
| 守卫 | 村民 | 夜间守护一人（不能连续守同一人） |

## 预设配置

- **6人简化局**: 2狼 + 预言家 + 女巫 + 2平民
- **9人标准局**: 3狼 + 预言家 + 女巫 + 猎人 + 3平民
- **12人标准局**: 4狼 + 预言家 + 女巫 + 猎人 + 守卫 + 4平民

## 运行测试

```bash
pytest tests/ -v
```

## 运行示例

```bash
python examples/simple_game.py
```

## 后续计划

- **Phase 2**: CLI 交互界面 + 简单 AI Bot
- **Phase 3**: LLM Agent 集成
- **Phase 4**: Web 可视化 + Benchmark

## License

MIT
