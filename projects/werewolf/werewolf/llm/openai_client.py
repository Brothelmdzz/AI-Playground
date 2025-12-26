# ==================== OpenAI 客户端 ====================
"""OpenAI API 客户端实现"""

from __future__ import annotations
import os
import json
from typing import List, Optional

from werewolf.llm.base import (
    BaseLLMClient,
    Message,
    ToolCall,
    ToolDefinition,
    LLMResponse,
)


class OpenAIClient(BaseLLMClient):
    """
    OpenAI API 客户端

    支持所有 OpenAI 兼容的 API（包括 Azure OpenAI、本地部署等）
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Args:
            model: 模型名称，如 "gpt-4o", "gpt-4o-mini"
            api_key: API 密钥，默认从 OPENAI_API_KEY 环境变量读取
            base_url: API 基础 URL，用于兼容其他 OpenAI 格式 API
        """
        super().__init__(model, api_key)
        self.base_url = base_url
        self._client = None

    def _get_client(self):
        """延迟初始化客户端"""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError:
                raise ImportError(
                    "请安装 openai: pip install openai>=1.0"
                )

            kwargs = {}
            if self.api_key:
                kwargs["api_key"] = self.api_key
            if self.base_url:
                kwargs["base_url"] = self.base_url

            self._client = AsyncOpenAI(**kwargs)

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

        # 转换消息格式
        openai_messages = [msg.to_openai_format() for msg in messages]

        # 构建请求参数
        kwargs = {
            "model": self.model,
            "messages": openai_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # 添加工具
        if tools:
            kwargs["tools"] = [tool.to_openai_format() for tool in tools]
            kwargs["tool_choice"] = "auto"

        # 发送请求
        response = await client.chat.completions.create(**kwargs)

        # 解析响应
        choice = response.choices[0]
        message = choice.message

        # 解析工具调用
        tool_calls = None
        if message.tool_calls:
            tool_calls = []
            for tc in message.tool_calls:
                try:
                    arguments = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=arguments
                ))

        # 构建响应
        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "stop",
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            }
        )
