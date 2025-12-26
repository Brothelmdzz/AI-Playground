# ==================== LLM 客户端基类 ====================
"""LLM 客户端抽象层"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict


@dataclass
class Message:
    """
    对话消息

    Attributes:
        role: 角色 ("system" | "user" | "assistant" | "tool")
        content: 消息内容
        tool_calls: 工具调用列表（assistant 消息）
        tool_call_id: 工具调用ID（tool 消息）
        name: 工具名称（tool 消息）
    """
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List["ToolCall"]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

    def to_openai_format(self) -> Dict[str, Any]:
        """转换为 OpenAI 格式"""
        msg: Dict[str, Any] = {"role": self.role}

        if self.content is not None:
            msg["content"] = self.content

        if self.tool_calls:
            msg["tool_calls"] = [tc.to_openai_format() for tc in self.tool_calls]

        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id

        if self.name and self.role == "tool":
            msg["name"] = self.name

        return msg

    def to_anthropic_format(self) -> Dict[str, Any]:
        """转换为 Anthropic 格式"""
        if self.role == "system":
            # Anthropic 的 system 消息单独处理
            return {"type": "text", "text": self.content or ""}

        msg: Dict[str, Any] = {"role": self.role}
        content_blocks = []

        if self.content:
            content_blocks.append({"type": "text", "text": self.content})

        if self.tool_calls:
            for tc in self.tool_calls:
                content_blocks.append({
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.arguments
                })

        if self.tool_call_id:
            # tool 消息在 Anthropic 中是 user 消息的一部分
            return {
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": self.tool_call_id,
                    "content": self.content or ""
                }]
            }

        if content_blocks:
            msg["content"] = content_blocks
        else:
            msg["content"] = self.content or ""

        return msg


@dataclass
class ToolCall:
    """
    工具调用

    Attributes:
        id: 调用ID
        name: 工具名称
        arguments: 参数字典
    """
    id: str
    name: str
    arguments: Dict[str, Any]

    def to_openai_format(self) -> Dict[str, Any]:
        """转换为 OpenAI 格式"""
        import json
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": json.dumps(self.arguments, ensure_ascii=False)
            }
        }


@dataclass
class ToolDefinition:
    """
    工具定义

    Attributes:
        name: 工具名称
        description: 工具描述
        parameters: JSON Schema 参数定义
    """
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=lambda: {
        "type": "object",
        "properties": {},
        "required": []
    })

    def to_openai_format(self) -> Dict[str, Any]:
        """转换为 OpenAI 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    def to_anthropic_format(self) -> Dict[str, Any]:
        """转换为 Anthropic 格式"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters
        }


@dataclass
class LLMResponse:
    """
    LLM 响应

    Attributes:
        content: 文本内容
        tool_calls: 工具调用列表
        finish_reason: 结束原因 ("stop" | "tool_calls" | "length")
        usage: token 使用统计
    """
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: str = "stop"
    usage: Optional[Dict[str, int]] = None

    @property
    def has_tool_calls(self) -> bool:
        """是否有工具调用"""
        return bool(self.tool_calls)


class BaseLLMClient(ABC):
    """
    LLM 客户端抽象基类

    所有 LLM 客户端都必须继承此类并实现 chat 方法。
    """

    def __init__(self, model: str, api_key: Optional[str] = None):
        """
        Args:
            model: 模型名称
            api_key: API 密钥（可选，默认从环境变量读取）
        """
        self.model = model
        self.api_key = api_key

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """
        发送对话请求

        Args:
            messages: 对话消息列表
            tools: 可用工具列表
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            LLMResponse: LLM 响应
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model})"
