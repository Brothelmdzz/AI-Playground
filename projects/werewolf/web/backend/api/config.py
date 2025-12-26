# ==================== 配置 API ====================
"""配置管理 API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

import sys
sys.path.insert(0, str(__file__).replace("\\", "/").rsplit("/web/", 1)[0])

from werewolf.config.settings import get_settings, reload_settings

router = APIRouter(prefix="/api/config", tags=["config"])


class LLMProviderUpdate(BaseModel):
    """LLM 提供商更新"""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None


class ConfigUpdate(BaseModel):
    """配置更新请求"""
    default_provider: Optional[str] = None
    openai: Optional[LLMProviderUpdate] = None
    anthropic: Optional[LLMProviderUpdate] = None
    deepseek: Optional[LLMProviderUpdate] = None
    custom: Optional[LLMProviderUpdate] = None


@router.get("")
async def get_config():
    """获取当前配置（API Key 已脱敏）"""
    settings = get_settings()
    return settings.to_dict()


@router.post("")
async def update_config(update: ConfigUpdate):
    """更新配置（运行时）"""
    settings = get_settings()

    if update.default_provider:
        settings.llm.default_provider = update.default_provider

    if update.openai:
        if update.openai.api_key:
            settings.llm.openai.api_key = update.openai.api_key
        if update.openai.base_url is not None:
            settings.llm.openai.base_url = update.openai.base_url or None
        if update.openai.model:
            settings.llm.openai.model = update.openai.model

    if update.anthropic:
        if update.anthropic.api_key:
            settings.llm.anthropic.api_key = update.anthropic.api_key
        if update.anthropic.model:
            settings.llm.anthropic.model = update.anthropic.model

    if update.deepseek:
        if update.deepseek.api_key:
            settings.llm.deepseek.api_key = update.deepseek.api_key
        if update.deepseek.model:
            settings.llm.deepseek.model = update.deepseek.model

    if update.custom:
        if update.custom.api_key:
            settings.llm.custom.api_key = update.custom.api_key
        if update.custom.base_url is not None:
            settings.llm.custom.base_url = update.custom.base_url or None
        if update.custom.model:
            settings.llm.custom.model = update.custom.model

    return {"message": "配置已更新", "config": settings.to_dict()}


@router.post("/reload")
async def reload_config():
    """重新加载配置文件"""
    settings = reload_settings()
    return {"message": "配置已重新加载", "config": settings.to_dict()}


@router.post("/test")
async def test_llm(provider: str = None):
    """测试 LLM 连接"""
    settings = get_settings()
    provider = provider or settings.llm.default_provider

    try:
        client = settings.get_llm_client(provider)

        # 简单测试请求
        from werewolf.llm.base import Message
        response = await client.chat([
            Message(role="user", content="Say 'Hello' in one word.")
        ], max_tokens=10)

        return {
            "success": True,
            "provider": provider,
            "response": response.content,
            "usage": response.usage,
        }
    except Exception as e:
        return {
            "success": False,
            "provider": provider,
            "error": str(e),
        }
