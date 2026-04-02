from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class StandardMessage:
    """标准化消息格式"""
    user_id: str
    content: str
    platform: str
    timestamp: str
    message_id: str
    metadata: Optional[dict] = None


class PlatformAdapter(ABC):
    """平台适配器抽象类"""
    
    @abstractmethod
    async def normalize_message(self, raw_msg) -> StandardMessage:
        """将平台特定消息转为标准格式"""
        pass
    
    @abstractmethod
    async def send_response(self, user_id: str, content: str):
        """发送响应到指定平台"""
        pass
    
    @abstractmethod
    async def start_listener(self):
        """启动消息监听器"""
        pass
    
    @abstractmethod
    async def stop_listener(self):
        """停止消息监听器"""
        pass
