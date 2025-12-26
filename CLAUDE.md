# Playground 项目

> AI 玩具试验田 - 探索有趣的 AI Agent 项目

## 目录结构

```
playground/
├── CLAUDE.md                       # 项目说明（本文件）
├── docs/
│   ├── ai-toys-ideas.md            # AI 玩具创意库
│   └── werewolf-game-framework.md  # 狼人杀框架设计文档
└── projects/                       # 具体项目实现（待创建）
    └── werewolf/                   # AI 狼人杀
```

## 当前状态

- **灵感来源**: [Silicon Rider Bench](https://github.com/KCORES/silicon-rider-bench)
- **核心思路**: 真实场景模拟 + 工具调用 + 资源约束 = AI 决策能力测试
- **AI 狼人杀**: ✅ Phase 3 完成（Web 可视化界面）
  - 支持 OpenAI + Anthropic 双接口
  - ReAct + Tool 多轮推理模式
  - AI vs AI 自动对战 + CLI 人类参与
  - Web 界面：观战 / 人机对战 / Benchmark 仪表盘

## 优先项目

1. 🎯 **AI 狼人杀** - 多 Agent 社交推理博弈
2. **AI 侦探** - 推理链可视化
3. **AI 急诊室** - 道德困境 + 资源调度

## 开发规范

- 参考 Silicon Rider Bench 的设计模式
- 使用 seed 保证可复现性
- 提供终端 + Web 双模式可视化
- 兼容 OpenAI SDK 工具调用接口
