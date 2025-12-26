# ==================== LLM Module ====================
"""LLM 客户端模块"""

from werewolf.llm.base import (
    Message,
    ToolCall,
    ToolDefinition,
    LLMResponse,
    BaseLLMClient,
)
from werewolf.llm.openai_client import OpenAIClient
from werewolf.llm.anthropic_client import AnthropicClient
from werewolf.llm.tools import WEREWOLF_TOOLS, get_tool_definitions

__all__ = [
    # 基础类
    "Message",
    "ToolCall",
    "ToolDefinition",
    "LLMResponse",
    "BaseLLMClient",
    # 客户端
    "OpenAIClient",
    "AnthropicClient",
    # 工具
    "WEREWOLF_TOOLS",
    "get_tool_definitions",
]
