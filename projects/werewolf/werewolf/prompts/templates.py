# ==================== 格式化模板 ====================
"""用于格式化游戏信息的模板工具"""

from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional

if TYPE_CHECKING:
    from werewolf.core.game import Game, PlayerView
    from werewolf.core.events import GameEvent


def format_game_state(view: PlayerView) -> str:
    """
    格式化游戏状态

    Args:
        view: 玩家视角

    Returns:
        格式化的游戏状态字符串
    """
    lines = [
        f"## 当前游戏状态",
        f"",
        f"- **阶段**: {_phase_name(view.phase.value)}",
        f"- **回合**: 第 {view.round} 回合",
        f"",
        f"### 玩家列表",
        f"",
    ]

    for p in view.alive_players:
        status = "存活" if p["is_alive"] else "死亡"
        lines.append(f"- **{p['id']}号** {p['name']}: {status}")

    # 统计
    alive_count = sum(1 for p in view.alive_players if p["is_alive"])
    lines.append(f"")
    lines.append(f"存活人数: {alive_count}")

    return "\n".join(lines)


def format_player_info(view: PlayerView) -> str:
    """
    格式化玩家个人信息

    Args:
        view: 玩家视角

    Returns:
        格式化的个人信息字符串
    """
    lines = [
        f"## 我的信息",
        f"",
        f"- **ID**: {view.my_id}号",
        f"- **名称**: {view.my_name}",
        f"- **角色**: {view.my_role.name}",
        f"- **阵营**: {_faction_name(view.my_role.faction.value)}",
    ]

    # 狼人队友
    if view.teammates:
        lines.append(f"")
        lines.append(f"### 我的队友（狼人）")
        for t in view.teammates:
            lines.append(f"- **{t['id']}号** {t['name']}")

    # 可用行动
    if view.available_actions:
        lines.append(f"")
        lines.append(f"### 当前可用行动")
        for action in view.available_actions:
            lines.append(f"- {_action_name(action.value)}")

    # 女巫专属：今晚被狼杀的人
    if view.wolf_target_tonight is not None:
        lines.append(f"")
        lines.append(f"### 今晚被狼人杀害的玩家")
        lines.append(f"- **{view.wolf_target_tonight}号** 玩家被狼人选中")

    return "\n".join(lines)


def format_history(
    events: List[GameEvent],
    event_type: str = "all"
) -> str:
    """
    格式化游戏历史

    Args:
        events: 事件列表
        event_type: 事件类型过滤 ("all" | "death" | "vote" | "speech")

    Returns:
        格式化的历史记录字符串
    """
    if not events:
        return "暂无历史记录"

    lines = ["## 游戏历史", ""]

    # 过滤事件
    if event_type != "all":
        type_map = {
            "death": "player_death",
            "vote": "vote_result",
            "speech": "player_speech",
        }
        target_type = type_map.get(event_type, event_type)
        events = [e for e in events if e.event_type == target_type]

    if not events:
        return f"没有找到类型为 '{event_type}' 的历史记录"

    # 按回合分组
    rounds: Dict[int, List[GameEvent]] = {}
    for event in events:
        if event.round_num not in rounds:
            rounds[event.round_num] = []
        rounds[event.round_num].append(event)

    for round_num in sorted(rounds.keys()):
        lines.append(f"### 第 {round_num} 回合")
        for event in rounds[round_num]:
            lines.append(f"- {_format_event(event)}")
        lines.append("")

    return "\n".join(lines)


def format_action_prompt(view: PlayerView) -> str:
    """
    格式化行动提示

    Args:
        view: 玩家视角

    Returns:
        行动提示字符串
    """
    phase = view.phase.value

    if phase == "night":
        return _format_night_prompt(view)
    elif phase == "day_discussion":
        return _format_discussion_prompt(view)
    elif phase == "day_vote":
        return _format_vote_prompt(view)
    else:
        return "当前阶段无需行动"


def _format_night_prompt(view: PlayerView) -> str:
    """夜间行动提示"""
    role = view.my_role.name
    actions = [a.value for a in view.available_actions]

    prompts = {
        "狼人": "现在是夜间，作为狼人，你需要选择一名玩家作为击杀目标。使用 `submit_action` 工具，设置 action_type 为 'kill'，并指定 target_id。",
        "预言家": "现在是夜间，作为预言家，你可以查验一名玩家的身份。使用 `submit_action` 工具，设置 action_type 为 'check'，并指定 target_id。",
        "女巫": "现在是夜间，作为女巫，你可以选择使用解药(save)救人或毒药(poison)杀人，或者跳过(skip)。",
        "守卫": "现在是夜间，作为守卫，你可以选择守护一名玩家。使用 `submit_action` 工具，设置 action_type 为 'protect'，并指定 target_id。注意：不能连续两晚守护同一人。",
        "猎人": "现在是夜间，猎人没有夜间行动。",
        "平民": "现在是夜间，平民没有夜间行动。",
    }

    base = prompts.get(role, "请根据你的角色进行夜间行动。")

    if not actions or actions == ["skip"]:
        return "现在是夜间，你没有需要执行的夜间行动。"

    return base


def _format_discussion_prompt(view: PlayerView) -> str:
    """讨论阶段提示"""
    return """现在是白天讨论阶段。

你可以：
1. 使用 `get_game_state` 查看当前存活玩家
2. 使用 `get_history` 查看历史记录
3. 使用 `speak` 工具发表你的观点

请根据你的角色和掌握的信息，发表有策略性的发言。"""


def _format_vote_prompt(view: PlayerView) -> str:
    """投票阶段提示"""
    return """现在是投票阶段。

你需要选择一名玩家进行投票，或者弃权(skip)。

使用 `submit_action` 工具：
- action_type: "vote"
- target_id: 你要投票的玩家ID

请根据讨论内容和你的判断，投出关键的一票。"""


# ==================== 辅助函数 ====================

def _phase_name(phase: str) -> str:
    """阶段名称映射"""
    names = {
        "init": "初始化",
        "night": "夜间",
        "night_resolve": "夜间结算",
        "day_discussion": "白天讨论",
        "day_vote": "白天投票",
        "day_resolve": "投票结算",
        "game_over": "游戏结束",
    }
    return names.get(phase, phase)


def _faction_name(faction: str) -> str:
    """阵营名称映射"""
    names = {
        "werewolf": "狼人阵营",
        "villager": "村民阵营",
    }
    return names.get(faction, faction)


def _action_name(action: str) -> str:
    """行动名称映射"""
    names = {
        "kill": "击杀 (kill)",
        "check": "查验 (check)",
        "save": "使用解药 (save)",
        "poison": "使用毒药 (poison)",
        "protect": "守护 (protect)",
        "vote": "投票 (vote)",
        "skip": "跳过 (skip)",
        "shoot": "开枪 (shoot)",
    }
    return names.get(action, action)


def _format_event(event: GameEvent) -> str:
    """格式化单个事件"""
    data = event.data
    event_type = event.event_type

    if event_type == "player_death":
        return f"{data.get('player_id', '?')}号玩家死亡（{data.get('reason', '未知原因')}）"
    elif event_type == "vote_result":
        eliminated = data.get("eliminated")
        if eliminated is not None:
            return f"投票结果：{eliminated}号玩家被处决"
        return "投票结果：无人被处决（平票）"
    elif event_type == "phase_change":
        return f"阶段变更：{_phase_name(data.get('from', '?'))} → {_phase_name(data.get('to', '?'))}"
    elif event_type == "game_start":
        return f"游戏开始，共 {data.get('player_count', '?')} 名玩家"
    elif event_type == "game_end":
        return f"游戏结束，{_faction_name(data.get('winner', '?'))} 获胜"
    else:
        return f"{event_type}: {data}"
