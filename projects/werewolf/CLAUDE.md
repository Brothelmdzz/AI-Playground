# AI 狼人杀游戏引擎

> Phase 3 完成：Web 可视化界面

## 项目结构

```
werewolf/
├── pyproject.toml              # 项目配置（含 llm/dev 可选依赖）
├── README.md                   # 说明文档
├── CLAUDE.md                   # 架构说明（本文件）
│
├── werewolf/                   # 主包
│   ├── __init__.py             # 导出核心 API
│   │
│   ├── core/                   # 核心模型层
│   │   ├── enums.py            # GamePhase, Faction, ActionType, DeathReason, RoleType
│   │   ├── player.py           # Player 和 NightState 数据模型
│   │   ├── events.py           # Action, ActionResult, GameEvent, PhaseResult
│   │   └── game.py             # Game 状态机 + PlayerView 信息隔离
│   │
│   ├── roles/                  # 角色系统（6种角色）
│   │   ├── base.py             # Role 抽象基类
│   │   ├── villager.py         # 平民
│   │   ├── werewolf.py         # 狼人
│   │   ├── seer.py             # 预言家
│   │   ├── witch.py            # 女巫
│   │   ├── hunter.py           # 猎人
│   │   └── guard.py            # 守卫
│   │
│   ├── engine/                 # 引擎层
│   │   ├── moderator.py        # 主持人（驱动阶段流转）
│   │   ├── resolver.py         # NightResolver 夜间结算器
│   │   └── vote.py             # VoteManager 投票管理器
│   │
│   ├── config/                 # 配置
│   │   └── presets.py          # GameConfig + PRESET_6P/9P/12P
│   │
│   ├── llm/                    # LLM 客户端抽象（Phase 2）
│   │   ├── __init__.py
│   │   ├── base.py             # Message, ToolCall, ToolDefinition, BaseLLMClient
│   │   ├── openai_client.py    # OpenAI API 实现
│   │   ├── anthropic_client.py # Anthropic API 实现
│   │   └── tools.py            # WEREWOLF_TOOLS 工具定义
│   │
│   ├── prompts/                # Prompt 模板（Phase 2）
│   │   ├── __init__.py
│   │   ├── system.py           # 系统提示词 SYSTEM_PROMPT
│   │   ├── role_prompts.py     # 角色专属策略提示
│   │   └── templates.py        # 格式化工具函数
│   │
│   ├── agents/                 # Agent 实现（Phase 2）
│   │   ├── __init__.py
│   │   ├── base.py             # BaseAgent 抽象基类
│   │   ├── random_agent.py     # RandomAgent 随机基线
│   │   ├── llm_agent.py        # LLMAgent ReAct + Tool
│   │   └── human_agent.py      # HumanAgent CLI 交互
│   │
│   └── runner/                 # 运行器（Phase 2）
│       ├── __init__.py
│       ├── game_runner.py      # GameRunner AI vs AI 对战
│       └── cli_runner.py       # CLIRunner 人类参与
│
├── tests/                      # 测试（51 个用例，全部通过）
│   ├── test_game.py            # 游戏流程测试
│   ├── test_roles.py           # 角色能力测试
│   ├── test_resolver.py        # 结算逻辑测试
│   ├── test_llm.py             # LLM 模块测试
│   └── test_agents.py          # Agent 测试
│
├── examples/
│   ├── simple_game.py          # 基础引擎示例
│   └── ai_battle.py            # AI 对战示例
│
└── web/                        # Web 可视化（Phase 3）
    ├── README.md               # Web 架构说明
    ├── backend/
    │   ├── main.py             # FastAPI 入口
    │   ├── api/                # REST + WebSocket
    │   ├── services/           # 游戏服务 + Benchmark
    │   └── models/             # Pydantic 模型
    └── frontend/
        ├── package.json        # React + TypeScript
        ├── src/
        │   ├── App.tsx
        │   ├── pages/          # 首页/游戏/Benchmark
        │   ├── components/     # 游戏面板/玩家卡片/聊天
        │   └── hooks/          # WebSocket/API
        └── public/
```

## 核心设计

### 状态机流转

```
INIT → NIGHT → (resolve) → DAY_DISCUSSION → DAY_VOTE → (resolve) → NIGHT ...
                  ↓                                        ↓
              GAME_OVER                                GAME_OVER
```

### 信息隔离

- `PlayerView`: 封装玩家可见信息
- 狼人可见队友，村民只知自己身份
- 女巫可见今晚狼刀目标

### 行动-结算分离

1. 玩家通过 `submit_action()` 提交行动
2. 行动存入 `_pending_actions`
3. `advance_phase()` 时统一结算

### LLM Agent 架构

```
┌─────────────────────────────────────────────────────┐
│                    LLMAgent                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ LLM Client  │  │   Prompts   │  │    Tools    │ │
│  │ (OpenAI /   │  │ (System +   │  │ (get_state, │ │
│  │  Anthropic) │  │  Role-based)│  │  submit_action)│
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
│         └────────────────┼────────────────┘        │
│                          ▼                          │
│                   ReAct Loop                        │
│         (思考 → 工具调用 → 观察 → 行动)              │
└─────────────────────────────────────────────────────┘
```

### 工具定义

| 工具名 | 功能 | 适用阶段 |
|--------|------|----------|
| `get_game_state` | 获取游戏状态 | 全阶段 |
| `get_my_info` | 获取自身信息 | 全阶段 |
| `get_history` | 获取历史记录 | 全阶段 |
| `submit_action` | 提交行动 | 夜间/投票 |
| `speak` | 白天发言 | 讨论阶段 |

## 开发命令

```bash
# 安装（仅核心）
pip install -e .

# 安装（含 LLM 支持）
pip install -e ".[llm]"

# 安装（含开发依赖）
pip install -e ".[all]"

# 测试
pytest tests/ -v

# 随机 Agent 对战
python examples/ai_battle.py --mode random --seed 42

# LLM Agent 对战（需 API Key）
export OPENAI_API_KEY=sk-xxx
python examples/ai_battle.py --mode llm --provider openai

# 混合对战（狼人用 LLM，其他随机）
python examples/ai_battle.py --mode mixed
```

## 启动 Web 界面

```bash
# 一键启动（推荐）
python run.py

# 或分别启动
python run.py --prod   # 生产模式
python run.py --build  # 打包前端
```

访问:
- 前端: http://localhost:3000
- 后端: http://localhost:8000
- 配置: http://localhost:3000/settings
- API 文档: http://localhost:8000/docs

## 后续扩展

- Phase 4: 多模型 Benchmark（GPT-4 vs Claude vs Llama）
- Phase 5: 自定义角色 + MOD 支持
- Phase 6: 联机对战 + 房间系统
