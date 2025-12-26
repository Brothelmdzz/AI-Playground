# ==================== LLM 模块测试 ====================
"""测试 LLM 客户端和工具"""

import pytest
from werewolf.llm.base import Message, ToolCall, ToolDefinition, LLMResponse
from werewolf.llm.tools import WEREWOLF_TOOLS, get_tool_definitions


class TestMessage:
    """消息类测试"""

    def test_basic_message(self):
        """测试基本消息"""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.tool_calls is None

    def test_to_openai_format(self):
        """测试转换为 OpenAI 格式"""
        msg = Message(role="user", content="Hello")
        openai_msg = msg.to_openai_format()

        assert openai_msg["role"] == "user"
        assert openai_msg["content"] == "Hello"

    def test_tool_message(self):
        """测试工具消息"""
        msg = Message(
            role="tool",
            content="Result",
            tool_call_id="call_123",
            name="get_game_state"
        )
        openai_msg = msg.to_openai_format()

        assert openai_msg["role"] == "tool"
        assert openai_msg["tool_call_id"] == "call_123"


class TestToolCall:
    """工具调用测试"""

    def test_basic_tool_call(self):
        """测试基本工具调用"""
        tc = ToolCall(
            id="call_123",
            name="submit_action",
            arguments={"action_type": "vote", "target_id": 1}
        )

        assert tc.id == "call_123"
        assert tc.name == "submit_action"
        assert tc.arguments["action_type"] == "vote"

    def test_to_openai_format(self):
        """测试转换为 OpenAI 格式"""
        tc = ToolCall(
            id="call_123",
            name="submit_action",
            arguments={"action_type": "vote"}
        )
        openai_tc = tc.to_openai_format()

        assert openai_tc["id"] == "call_123"
        assert openai_tc["type"] == "function"
        assert openai_tc["function"]["name"] == "submit_action"


class TestToolDefinition:
    """工具定义测试"""

    def test_basic_definition(self):
        """测试基本工具定义"""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {}}
        )

        assert tool.name == "test_tool"
        assert tool.description == "A test tool"

    def test_to_openai_format(self):
        """测试转换为 OpenAI 格式"""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool"
        )
        openai_tool = tool.to_openai_format()

        assert openai_tool["type"] == "function"
        assert openai_tool["function"]["name"] == "test_tool"

    def test_to_anthropic_format(self):
        """测试转换为 Anthropic 格式"""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool"
        )
        anthropic_tool = tool.to_anthropic_format()

        assert anthropic_tool["name"] == "test_tool"
        assert "input_schema" in anthropic_tool


class TestLLMResponse:
    """LLM 响应测试"""

    def test_basic_response(self):
        """测试基本响应"""
        response = LLMResponse(content="Hello", finish_reason="stop")

        assert response.content == "Hello"
        assert response.finish_reason == "stop"
        assert not response.has_tool_calls

    def test_response_with_tool_calls(self):
        """测试带工具调用的响应"""
        tool_calls = [
            ToolCall(id="1", name="test", arguments={})
        ]
        response = LLMResponse(tool_calls=tool_calls, finish_reason="tool_calls")

        assert response.has_tool_calls
        assert len(response.tool_calls) == 1


class TestWerewolfTools:
    """狼人杀工具测试"""

    def test_tools_exist(self):
        """测试工具定义存在"""
        assert len(WEREWOLF_TOOLS) > 0

        tool_names = [t.name for t in WEREWOLF_TOOLS]
        assert "get_game_state" in tool_names
        assert "get_my_info" in tool_names
        assert "submit_action" in tool_names
        assert "speak" in tool_names

    def test_get_tool_definitions_by_phase(self):
        """测试按阶段获取工具"""
        night_tools = get_tool_definitions("night")
        vote_tools = get_tool_definitions("day_vote")
        discussion_tools = get_tool_definitions("day_discussion")

        # 夜间应该有 submit_action
        night_names = [t.name for t in night_tools]
        assert "submit_action" in night_names

        # 讨论阶段应该有 speak
        discussion_names = [t.name for t in discussion_tools]
        assert "speak" in discussion_names

    def test_submit_action_parameters(self):
        """测试 submit_action 参数定义"""
        submit_tool = next(t for t in WEREWOLF_TOOLS if t.name == "submit_action")

        props = submit_tool.parameters.get("properties", {})
        assert "action_type" in props
        assert "target_id" in props

        # action_type 应该有 enum
        action_type_def = props["action_type"]
        assert "enum" in action_type_def
        assert "vote" in action_type_def["enum"]
        assert "kill" in action_type_def["enum"]
