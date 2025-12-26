# ==================== 配置管理 ====================
"""统一配置管理，支持环境变量和配置文件"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class LLMProviderConfig:
    """LLM 提供商配置"""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = ""


@dataclass
class LLMConfig:
    """LLM 配置"""
    default_provider: str = "openai"
    openai: LLMProviderConfig = field(default_factory=lambda: LLMProviderConfig(model="gpt-4o-mini"))
    anthropic: LLMProviderConfig = field(default_factory=lambda: LLMProviderConfig(model="claude-3-5-haiku-20241022"))
    deepseek: LLMProviderConfig = field(default_factory=lambda: LLMProviderConfig(
        base_url="https://api.deepseek.com",
        model="deepseek-chat"
    ))
    custom: LLMProviderConfig = field(default_factory=LLMProviderConfig)


@dataclass
class GameConfig:
    """游戏配置"""
    default_preset: str = "6p"
    default_speed: float = 1.0
    max_rounds: int = 20


@dataclass
class ServerConfig:
    """服务器配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list = field(default_factory=lambda: ["http://localhost:3000"])


@dataclass
class Settings:
    """全局配置"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    game: GameConfig = field(default_factory=GameConfig)
    server: ServerConfig = field(default_factory=ServerConfig)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Settings":
        """
        加载配置

        优先级：环境变量 > config.yaml > 默认值
        """
        settings = cls()

        # 1. 尝试加载 YAML 配置文件
        if config_path is None:
            # 查找配置文件
            search_paths = [
                Path.cwd() / "config.yaml",
                Path.cwd() / "config.yml",
                Path(__file__).parent.parent.parent / "config.yaml",
            ]
            for p in search_paths:
                if p.exists():
                    config_path = str(p)
                    break

        if config_path and Path(config_path).exists():
            settings._load_yaml(config_path)

        # 2. 环境变量覆盖
        settings._load_env()

        return settings

    def _load_yaml(self, path: str):
        """从 YAML 文件加载配置"""
        try:
            import yaml
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data:
                return

            # LLM 配置
            if 'llm' in data:
                llm = data['llm']
                if 'default_provider' in llm:
                    self.llm.default_provider = llm['default_provider']
                if 'openai' in llm:
                    self.llm.openai = LLMProviderConfig(**llm['openai'])
                if 'anthropic' in llm:
                    self.llm.anthropic = LLMProviderConfig(**llm['anthropic'])
                if 'deepseek' in llm:
                    self.llm.deepseek = LLMProviderConfig(**llm['deepseek'])
                if 'custom' in llm:
                    self.llm.custom = LLMProviderConfig(**llm['custom'])

            # 游戏配置
            if 'game' in data:
                game = data['game']
                if 'default_preset' in game:
                    self.game.default_preset = game['default_preset']
                if 'default_speed' in game:
                    self.game.default_speed = game['default_speed']
                if 'max_rounds' in game:
                    self.game.max_rounds = game['max_rounds']

            # 服务器配置
            if 'server' in data:
                server = data['server']
                if 'host' in server:
                    self.server.host = server['host']
                if 'port' in server:
                    self.server.port = server['port']
                if 'cors_origins' in server:
                    self.server.cors_origins = server['cors_origins']

        except ImportError:
            print("警告: PyYAML 未安装，跳过配置文件加载")
        except Exception as e:
            print(f"警告: 加载配置文件失败: {e}")

    def _load_env(self):
        """从环境变量加载配置"""
        # OpenAI
        if os.getenv("OPENAI_API_KEY"):
            self.llm.openai.api_key = os.getenv("OPENAI_API_KEY")
        if os.getenv("OPENAI_BASE_URL"):
            self.llm.openai.base_url = os.getenv("OPENAI_BASE_URL")
        if os.getenv("OPENAI_MODEL"):
            self.llm.openai.model = os.getenv("OPENAI_MODEL")

        # Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            self.llm.anthropic.api_key = os.getenv("ANTHROPIC_API_KEY")
        if os.getenv("ANTHROPIC_MODEL"):
            self.llm.anthropic.model = os.getenv("ANTHROPIC_MODEL")

        # DeepSeek
        if os.getenv("DEEPSEEK_API_KEY"):
            self.llm.deepseek.api_key = os.getenv("DEEPSEEK_API_KEY")
        if os.getenv("DEEPSEEK_MODEL"):
            self.llm.deepseek.model = os.getenv("DEEPSEEK_MODEL")

        # 默认提供商
        if os.getenv("LLM_PROVIDER"):
            self.llm.default_provider = os.getenv("LLM_PROVIDER")

    def get_llm_client(self, provider: Optional[str] = None):
        """
        获取 LLM 客户端

        Args:
            provider: 指定提供商，默认使用 default_provider
        """
        provider = provider or self.llm.default_provider

        if provider == "openai":
            from werewolf.llm.openai_client import OpenAIClient
            cfg = self.llm.openai
            return OpenAIClient(
                model=cfg.model,
                api_key=cfg.api_key,
                base_url=cfg.base_url,
            )
        elif provider == "anthropic":
            from werewolf.llm.anthropic_client import AnthropicClient
            cfg = self.llm.anthropic
            return AnthropicClient(
                model=cfg.model,
                api_key=cfg.api_key,
            )
        elif provider == "deepseek":
            from werewolf.llm.openai_client import OpenAIClient
            cfg = self.llm.deepseek
            return OpenAIClient(
                model=cfg.model,
                api_key=cfg.api_key,
                base_url=cfg.base_url or "https://api.deepseek.com",
            )
        elif provider == "custom":
            from werewolf.llm.openai_client import OpenAIClient
            cfg = self.llm.custom
            return OpenAIClient(
                model=cfg.model,
                api_key=cfg.api_key,
                base_url=cfg.base_url,
            )
        else:
            raise ValueError(f"未知的 LLM 提供商: {provider}")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（隐藏敏感信息）"""
        def mask_key(key: Optional[str]) -> Optional[str]:
            if not key:
                return None
            if len(key) <= 8:
                return "***"
            return key[:4] + "***" + key[-4:]

        return {
            "llm": {
                "default_provider": self.llm.default_provider,
                "openai": {
                    "api_key": mask_key(self.llm.openai.api_key),
                    "base_url": self.llm.openai.base_url,
                    "model": self.llm.openai.model,
                },
                "anthropic": {
                    "api_key": mask_key(self.llm.anthropic.api_key),
                    "model": self.llm.anthropic.model,
                },
                "deepseek": {
                    "api_key": mask_key(self.llm.deepseek.api_key),
                    "base_url": self.llm.deepseek.base_url,
                    "model": self.llm.deepseek.model,
                },
                "custom": {
                    "api_key": mask_key(self.llm.custom.api_key),
                    "base_url": self.llm.custom.base_url,
                    "model": self.llm.custom.model,
                },
            },
            "game": {
                "default_preset": self.game.default_preset,
                "default_speed": self.game.default_speed,
                "max_rounds": self.game.max_rounds,
            },
            "server": {
                "host": self.server.host,
                "port": self.server.port,
            },
        }


# 全局单例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取全局配置单例"""
    global _settings
    if _settings is None:
        _settings = Settings.load()
    return _settings


def reload_settings(config_path: Optional[str] = None) -> Settings:
    """重新加载配置"""
    global _settings
    _settings = Settings.load(config_path)
    return _settings
