# AI 狼人杀 - 游戏框架设计

> 基于网络调研整理，作为后续开发的设计基础

---

## 一、游戏本质

**核心博弈模型**: 信息不对称的多人社交推理游戏

| 阵营 | 信息量 | 目标 |
|------|--------|------|
| 狼人 (Informed Minority) | 知道同伴是谁 | 杀光村民或数量相等 |
| 村民 (Uninformed Majority) | 只知道自己身份 | 找出并处决所有狼人 |

**胜负条件**:
- 狼人胜: 存活狼人 >= 存活村民
- 村民胜: 所有狼人被处决

---

## 二、角色设计

### 2.1 基础配置（推荐）

| 人数 | 狼人 | 神职 | 平民 |
|------|------|------|------|
| 9人  | 3    | 预言家、女巫、猎人 | 3 |
| 12人 | 4    | 预言家、女巫、猎人、守卫 | 4 |

### 2.2 角色能力表

```
┌─────────┬──────────────────────────────────────────────────────┐
│  角色   │                        能力                           │
├─────────┼──────────────────────────────────────────────────────┤
│  狼人   │ 夜间睁眼，集体选择杀一人（可空刀）                      │
│  预言家 │ 夜间查验一人身份（狼人/好人）                          │
│  女巫   │ 一瓶解药（救人）+ 一瓶毒药（杀人），全局各一次           │
│  猎人   │ 正常死亡时可开枪带走一人（被毒死不能开枪）              │
│  守卫   │ 夜间守护一人免受狼人袭击（不能连续守护同一人）           │
│  白痴   │ 被投票出局后可翻牌自证，继续存活但失去投票权             │
│  平民   │ 无特殊能力，依靠发言和投票参与游戏                      │
└─────────┴──────────────────────────────────────────────────────┘
```

### 2.3 警长机制（可选）

- 第一个白天竞选产生
- 投票权重 1.5 票
- 死亡时可移交警徽

---

## 三、游戏流程（状态机）

```
                    ┌──────────────────────────────────────┐
                    │             GAME_INIT                │
                    │  - 分配角色                          │
                    │  - 初始化玩家状态                     │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
               ┌───►│             NIGHT                    │
               │    │  1. 狼人行动 (选择击杀目标)           │
               │    │  2. 女巫行动 (解药/毒药)              │
               │    │  3. 预言家行动 (查验身份)             │
               │    │  4. 守卫行动 (守护目标)               │
               │    └──────────────┬───────────────────────┘
               │                   │
               │    ┌──────────────▼───────────────────────┐
               │    │          NIGHT_RESULT                │
               │    │  - 结算死亡（狼刀 vs 守护 vs 解药）    │
               │    │  - 公布夜间死亡玩家                   │
               │    │  - 猎人死亡判定                       │
               │    └──────────────┬───────────────────────┘
               │                   │
               │                   ▼
               │         ┌─────────────────┐
               │         │  CHECK_WIN      │──────► GAME_OVER
               │         └────────┬────────┘
               │                  │ (游戏继续)
               │    ┌─────────────▼────────────────────────┐
               │    │              DAY                     │
               │    │  1. 遗言阶段 (死者发言)               │
               │    │  2. 自由发言 (按座位顺序)             │
               │    │  3. 投票阶段 (公开投票)               │
               │    │  4. 处决宣布                         │
               │    │  5. 遗言阶段 (被处决者)               │
               │    └──────────────┬───────────────────────┘
               │                   │
               │                   ▼
               │         ┌─────────────────┐
               └─────────┤  CHECK_WIN      │──────► GAME_OVER
                         └─────────────────┘
```

---

## 四、系统架构

### 4.1 模块划分

```
werewolf/
├── core/                    # 核心游戏逻辑
│   ├── game.py              # 游戏主控制器（状态机）
│   ├── player.py            # 玩家模型
│   ├── roles/               # 角色定义
│   │   ├── base.py          # 角色基类
│   │   ├── werewolf.py      # 狼人
│   │   ├── seer.py          # 预言家
│   │   ├── witch.py         # 女巫
│   │   ├── hunter.py        # 猎人
│   │   └── villager.py      # 平民
│   └── phases/              # 游戏阶段
│       ├── night.py         # 夜间阶段处理
│       ├── day.py           # 白天阶段处理
│       └── vote.py          # 投票逻辑
│
├── agents/                  # AI 代理（后续扩展）
│   ├── base_agent.py        # Agent 基类
│   ├── llm_agent.py         # LLM 驱动的 Agent
│   └── strategies/          # 策略模块
│
├── engine/                  # 运行时引擎
│   ├── moderator.py         # 主持人（法官）
│   ├── message_bus.py       # 消息传递系统
│   └── logger.py            # 游戏日志记录
│
├── interface/               # 用户界面
│   ├── cli.py               # 命令行界面
│   └── web/                 # Web 可视化（可选）
│
└── config/                  # 配置文件
    ├── game_config.yaml     # 游戏配置（人数、角色）
    └── llm_config.yaml      # LLM API 配置
```

### 4.2 核心类设计

```python
# ==================== 游戏状态 ====================
class GameState(Enum):
    INIT = "init"
    NIGHT = "night"
    DAY_DISCUSSION = "day_discussion"
    DAY_VOTE = "day_vote"
    GAME_OVER = "game_over"

# ==================== 玩家模型 ====================
class Player:
    id: int
    name: str
    role: Role
    is_alive: bool
    is_poisoned: bool      # 被女巫毒死
    is_protected: bool     # 被守卫保护

# ==================== 角色基类 ====================
class Role(ABC):
    name: str
    faction: Faction       # WEREWOLF / VILLAGER / THIRD_PARTY
    can_act_at_night: bool

    @abstractmethod
    def night_action(self, game: Game, target: Player) -> ActionResult:
        pass

# ==================== 游戏控制器 ====================
class Game:
    players: List[Player]
    state: GameState
    round: int
    history: List[GameEvent]

    def run(self): ...
    def next_phase(self): ...
    def check_win_condition(self) -> Optional[Faction]: ...
```

### 4.3 消息系统设计

```python
# 玩家之间的信息隔离是核心
class Message:
    sender: Player
    recipients: List[Player]   # 空 = 广播
    content: str
    visibility: Visibility     # PUBLIC / PRIVATE / WEREWOLF_ONLY
    phase: GameState
    round: int
```

---

## 五、关键设计决策

### 5.1 确定性 vs 随机性

| 要素 | 建议 |
|------|------|
| 角色分配 | 使用 seed，保证可复现 |
| 发言顺序 | 固定（按座位）或随机（需 seed） |
| 平票处理 | 可选：重新投票 / 随机 / 不处决 |

### 5.2 信息可见性矩阵

```
           │ 自己角色 │ 队友角色 │ 他人角色 │ 夜间行动 │ 历史发言 │
───────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
  狼人     │    ✓     │    ✓     │    ✗     │  狼队    │    ✓     │
  预言家   │    ✓     │    ✗     │ 查验结果 │  自己    │    ✓     │
  女巫     │    ✓     │    ✗     │    ✗     │ 死者+自己│    ✓     │
  平民     │    ✓     │    ✗     │    ✗     │    ✗     │    ✓     │
```

### 5.3 游戏平衡性参考

来自 [博弈论研究](https://arxiv.org/html/2408.17177v1):
- 无预言家: 狼人数量 ≈ √(总人数) 时双方胜率接近
- 有预言家: 狼人数量与总人数呈线性关系时平衡

---

## 六、现有开源项目参考

| 项目 | 特点 | 链接 |
|------|------|------|
| **werewolf_ai_agents** | 基于 MetaGPT，完整多Agent实现 | [GitHub](https://github.com/WuJunde/werewolf_ai_agents) |
| **KylJin/Werewolf** | NeurIPS 2024，RL+LLM框架，One Night版本 | [GitHub](https://github.com/KylJin/Werewolf) |
| **xuyuzhuang11/Werewolf** | 基于 ChatArena，无需微调LLM | [GitHub](https://github.com/xuyuzhuang11/Werewolf) |
| **sentient-agi/werewolf-template** | Hackathon模板，Llama 70B | [GitHub](https://github.com/sentient-agi/werewolf-template) |

---

## 七、开发路线图（建议）

```
Phase 1: 游戏引擎
├── 实现状态机和角色系统
├── 实现主持人逻辑
├── CLI 交互界面
└── 人类 vs 人类 可玩

Phase 2: AI Agent
├── 接入 LLM API
├── 设计 Prompt 模板
├── 实现信息注入机制
└── 人类 vs AI 可玩

Phase 3: 多 Agent 博弈
├── Agent 间通信
├── 策略多样性（不同 persona）
├── 完整 AI vs AI 对局
└── 评估指标体系

Phase 4: 可视化 & Benchmark
├── Web 可视化界面
├── 对局回放系统
├── 多模型对比测试
└── 榜单发布
```

---

## 参考资料

- [狼人杀官方标准规则](https://www.gameres.com/753084.html)
- [Mafia (party game) - Wikipedia](https://en.wikipedia.org/wiki/Mafia_(party_game))
- [Optimal Strategy in Werewolf: A Game Theoretic Perspective](https://arxiv.org/html/2408.17177v1)
- [One Night Ultimate Werewolf 设计分析](https://mechanicsofmagic.com/2024/04/09/critical-play-social-deduction-one-night-werewolf/)
