from .base import PlatformAdapter, StandardMessage
from datetime import datetime
import uuid


class WebhookAdapter(PlatformAdapter):
    """Webhook适配器"""
    
    def __init__(self):
        self.platform = "webhook"
        self.listeners = []
    
    async def normalize_message(self, raw_msg) -> StandardMessage:
        """将Webhook消息转为标准格式"""
        user_id = raw_msg.get("user_id", str(uuid.uuid4()))
        content = raw_msg.get("content", "")
        message_id = raw_msg.get("message_id", str(uuid.uuid4()))
        timestamp = raw_msg.get("timestamp", datetime.now().isoformat())
        metadata = raw_msg.get("metadata", {})
        
        return StandardMessage(
            user_id=user_id,
            content=content,
            platform=self.platform,
            timestamp=timestamp,
            message_id=message_id,
            metadata=metadata
        )
    
    async def send_response(self, user_id: str, content: str):
        """发送响应到Webhook"""
        # 这里只是模拟实现，实际应该根据webhook配置发送响应
        print(f"Sending response to {user_id}: {content}")
        return {"status": "success", "content": content}
    
    async def start_listener(self):
        """启动Webhook监听器"""
        print("Webhook listener started")
    
    async def stop_listener(self):
        """停止Webhook监听器"""
        print("Webhook listener stopped")
