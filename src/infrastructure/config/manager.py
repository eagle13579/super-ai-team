import os
import dotenv
from typing import Dict, Optional, Any, List, Callable
import json


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = ".env"):
        # 加载.env文件
        dotenv.load_dotenv(config_path)
        self.config: Dict[str, Any] = {}
        self._watchers: List[Callable] = []
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        # 系统级配置
        self.config["system"] = {
            "database_url": os.getenv("DATABASE_URL", "postgresql://localhost:5432/super_ai_team"),
            "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            "message_queue_url": os.getenv("MESSAGE_QUEUE_URL", "redis://localhost:6379/1"),
            "storage_path": os.getenv("STORAGE_PATH", "./storage")
        }
        
        # Agent级配置
        self.config["agent"] = {
            "model_api_key": os.getenv("MODEL_API_KEY", ""),
            "default_model": os.getenv("DEFAULT_MODEL", "claude-3.5-sonnet"),
            "max_tokens": int(os.getenv("MAX_TOKENS", "4096")),
            "temperature": float(os.getenv("TEMPERATURE", "0.7"))
        }
        
        # 用户级配置
        self.config["user"] = {
            "default_language": os.getenv("DEFAULT_LANGUAGE", "zh-CN"),
            "max_conversation_history": int(os.getenv("MAX_CONVERSATION_HISTORY", "50"))
        }
        
        # 工作流级配置
        self.config["workflow"] = {
            "execution_timeout": int(os.getenv("EXECUTION_TIMEOUT", "300")),
            "max_retries": int(os.getenv("MAX_RETRIES", "3")),
            "audit_enabled": os.getenv("AUDIT_ENABLED", "true").lower() == "true"
        }
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """获取配置"""
        # 支持点号分隔的路径
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置"""
        # 支持点号分隔的路径
        keys = key.split(".")
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        
        # 通知监听器
        self._notify_watchers()
    
    def watch(self, callback: Callable):
        """注册配置变更监听器"""
        self._watchers.append(callback)
    
    def reload(self):
        """重新加载配置"""
        self._load_config()
        self._notify_watchers()
    
    def _notify_watchers(self):
        """通知配置变更监听器"""
        for callback in self._watchers:
            try:
                callback(self.config)
            except Exception as e:
                print(f"Error notifying watcher: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """返回配置字典"""
        return self.config
