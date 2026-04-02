from typing import Dict, Optional, Any
from dataclasses import dataclass
import redis
import json
from datetime import datetime


@dataclass
class Context:
    """上下文数据结构"""
    # 基础信息
    session_id: str
    user_id: str
    timestamp: str
    
    # 环境信息
    current_page: Optional[str] = None
    location: Optional[str] = None
    device: Optional[str] = None
    
    # 会话历史
    conversation_history: list = None
    
    # 工作记忆
    working_memory: Dict[str, Any] = None
    
    # 项目上下文
    project_context: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
        if self.working_memory is None:
            self.working_memory = {}


class ContextManager:
    """上下文管理器"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
        except:
            # 如果Redis不可用，使用内存存储
            self.redis = None
            self.memory_store = {}
    
    async def get_context(self, session_id: str) -> Optional[Context]:
        """获取上下文"""
        try:
            if self.redis:
                context_data = self.redis.get(f"context:{session_id}")
                if context_data:
                    return self._deserialize_context(json.loads(context_data))
            else:
                # 使用内存存储
                if session_id in self.memory_store:
                    return self._deserialize_context(self.memory_store[session_id])
        except Exception as e:
            print(f"Error getting context: {e}")
        return None
    
    async def set_context(self, context: Context):
        """设置上下文"""
        try:
            context_data = self._serialize_context(context)
            if self.redis:
                self.redis.setex(
                    f"context:{context.session_id}",
                    3600,  # 1小时过期
                    json.dumps(context_data)
                )
            else:
                # 使用内存存储
                self.memory_store[context.session_id] = context_data
        except Exception as e:
            print(f"Error setting context: {e}")
    
    async def update_context(self, session_id: str, updates: Dict[str, Any]):
        """更新上下文"""
        context = await self.get_context(session_id)
        if context:
            # 更新上下文属性
            for key, value in updates.items():
                if hasattr(context, key):
                    setattr(context, key, value)
            # 保存更新后的上下文
            await self.set_context(context)
    
    async def add_message(self, session_id: str, message: Dict[str, Any]):
        """添加消息到会话历史"""
        context = await self.get_context(session_id)
        if context:
            context.conversation_history.append({
                "content": message.get("content", ""),
                "role": message.get("role", "user"),
                "timestamp": datetime.now().isoformat()
            })
            # 限制会话历史长度
            if len(context.conversation_history) > 50:
                context.conversation_history = context.conversation_history[-50:]
            await self.set_context(context)
    
    def _serialize_context(self, context: Context) -> Dict[str, Any]:
        """序列化上下文"""
        return {
            "session_id": context.session_id,
            "user_id": context.user_id,
            "timestamp": context.timestamp,
            "current_page": context.current_page,
            "location": context.location,
            "device": context.device,
            "conversation_history": context.conversation_history,
            "working_memory": context.working_memory,
            "project_context": context.project_context
        }
    
    def _deserialize_context(self, data: Dict[str, Any]) -> Context:
        """反序列化上下文"""
        return Context(
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            timestamp=data.get("timestamp"),
            current_page=data.get("current_page"),
            location=data.get("location"),
            device=data.get("device"),
            conversation_history=data.get("conversation_history", []),
            working_memory=data.get("working_memory", {}),
            project_context=data.get("project_context")
        )
