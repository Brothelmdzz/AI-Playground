# ==================== Anthropic 客户端 ====================
"""Anthropic API 客户端实现"""

from __future__ import annotations
from typing import List, Optional

from werewolf.llm.base import (
    BaseLLMClient,
    Message,
    ToolCall,
    ToolDefinition,
    LLMResponse,
)


class AnthropicClient(BaseLLMClient):
    """
    Anthropic API 客户端

    支持 Claude 系列模型
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: Optional[str] = None,
    ):
        """
        Args:
            model: 模型名称，如 "claude-sonnet-4-20250514", "claude-3-5-haiku-20241022"
            api_key: API 密钥，默认从 ANTHROPIC_API_KEY 环境变量读取
        """
        super().__init__(model, api_key)
        self._client = None

    def _get_client(self):
        """延迟初始化客户端"""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
            except ImportError:
                raise ImportError(
                    "请安装 anthropic: pip install anthropic>=0.18"
                )

            kwargs = {}
            if self.api_key:
                kwargs["api_key"] = self.api_key

            self._client = AsyncAnthropic(**kwargs)

        return self._client

    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """发送对话请求"""
        client = self._get_client()

        # 提取 system 消息
        system_content = None
        non_system_messages = []

        for msg in messages:
            if msg.role == "system":
                system_content = msg.content
            else:
                non_system_messages.append(msg)

        # 转换消息格式（需要合并连续的 tool 消息）
        anthropic_messages = self._convert_messages(non_system_messages)

        # 构建请求参数
        kwargs = {
            "model": self.model,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if system_content:
            kwargs["system"] = system_content

        # 添加工具
        if tools:
            kwargs["tools"] = [tool.to_anthropic_format() for tool in tools]

        # 发送请求
        response = await client.messages.create(**kwargs)

        # 解析响应
        content = None
        tool_calls = None

        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input if isinstance(block.input, dict) else {}
                ))

        # 映射 stop_reason
        finish_reason_map = {
            "end_turn": "stop",
            "tool_use": "tool_calls",
            "max_tokens": "length",
        }
        finish_reason = finish_reason_map.get(response.stop_reason, "stop")

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
            }
        )

    def _convert_messages(self, messages: List[Message]) -> List[dict]:
        """
        转换消息列表为 Anthropic 格式

        Anthropic 要求：
        1. 消息必须 user/assistant 交替
        2. tool_result 必须在 user 消息中
        """
        result = []
        pending_tool_results = []

        for msg in messages:
            if msg.role == "tool":
                # 收集 tool 结果，稍后合并到 user 消息
                pending_tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": msg.tool_call_id,
                    "content": msg.content or ""
                })
            elif msg.role == "assistant":
                # 先添加 pending tool results 作为 user 消息
                if pending_tool_results:
                    result.append({
                        "role": "user",
                        "content": pending_tool_results
                    })
                    pending_tool_results = []

                # 添加 assistant 消息
                content_blocks = []
                if msg.content:
                    content_blocks.append({"type": "text", "text": msg.content})
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        content_blocks.append({
                            "type": "tool_use",
                            "id": tc.id,
                            "name": tc.name,
                            "input": tc.arguments
                        })

                if content_blocks:
                    result.append({
                        "role": "assistant",
                        "content": content_blocks
                    })
            else:
                # user 消息
                if pending_tool_results:
                    # 合并 tool results 和 user 消息
                    content = pending_tool_results.copy()
                    if msg.content:
                        content.append({"type": "text", "text": msg.content})
                    result.append({"role": "user", "content": content})
                    pending_tool_results = []
                else:
                    result.append({
                        "role": "user",
                        "content": msg.content or ""
                    })

        # 处理剩余的 tool results
        if pending_tool_results:
            result.append({
                "role": "user",
                "content": pending_tool_results
            })

        return result
