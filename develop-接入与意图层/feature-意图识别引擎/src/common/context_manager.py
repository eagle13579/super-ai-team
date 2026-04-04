"""
意图识别引擎 - 上下文管理器

维护多轮对话上下文，支持会话状态跟踪

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class Session:
    """会话定义"""
    session_id: str
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    intent_history: List[Dict[str, Any]] = field(default_factory=list)
    entities: Dict[str, Any] = field(default_factory=dict)
    context_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity = time.time()
    
    def add_intent(self, intent: str, entities: Dict[str, Any], confidence: float):
        """添加意图到历史"""
        self.intent_history.append({
            'intent': intent,
            'entities': entities,
            'confidence': confidence,
            'timestamp': time.time()
        })
        self.update_activity()
    
    def get_last_intent(self) -> Optional[Dict[str, Any]]:
        """获取上一个意图"""
        if self.intent_history:
            return self.intent_history[-1]
        return None
    
    def is_expired(self, timeout_seconds: int = 1800) -> bool:
        """检查会话是否过期"""
        return time.time() - self.last_activity > timeout_seconds


class ContextManager:
    """
    上下文管理器
    
    维护多轮对话上下文，支持会话状态跟踪
    """
    
    def __init__(self, session_timeout: int = 1800, max_history: int = 10):
        """
        初始化上下文管理器
        
        Args:
            session_timeout: 会话超时时间（秒）
            max_history: 最大历史记录数
        """
        self.sessions: Dict[str, Session] = {}
        self.session_timeout = session_timeout
        self.max_history = max_history
    
    def get_or_create_session(self, session_id: str) -> Session:
        """
        获取或创建会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话对象
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = Session(session_id=session_id)
        
        session = self.sessions[session_id]
        session.update_activity()
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        获取会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话对象或None
        """
        return self.sessions.get(session_id)
    
    def update_context(
        self,
        session_id: str,
        intent: str,
        entities: Dict[str, Any],
        confidence: float,
        context_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        更新上下文
        
        Args:
            session_id: 会话ID
            intent: 意图名称
            entities: 实体信息
            confidence: 置信度
            context_data: 额外的上下文数据
        """
        session = self.get_or_create_session(session_id)
        
        # 添加意图到历史
        session.add_intent(intent, entities, confidence)
        
        # 限制历史记录数
        if len(session.intent_history) > self.max_history:
            session.intent_history = session.intent_history[-self.max_history:]
        
        # 更新实体（合并新实体）
        session.entities.update(entities)
        
        # 更新上下文数据
        if context_data:
            session.context_data.update(context_data)
    
    def get_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取上下文
        
        Args:
            session_id: 会话ID
            
        Returns:
            上下文数据或None
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        return {
            'session_id': session.session_id,
            'intent_history': session.intent_history,
            'entities': session.entities,
            'context_data': session.context_data,
            'last_intent': session.get_last_intent()
        }
    
    def get_recent_intents(self, session_id: str, n: int = 3) -> List[Dict[str, Any]]:
        """
        获取最近的意图
        
        Args:
            session_id: 会话ID
            n: 最近n个意图
            
        Returns:
            意图列表
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        return session.intent_history[-n:]
    
    def clear_session(self, session_id: str) -> bool:
        """
        清除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功清除
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def clear_expired_sessions(self) -> int:
        """
        清除过期会话
        
        Returns:
            清除的会话数量
        """
        expired_sessions = [
            sid for sid, session in self.sessions.items()
            if session.is_expired(self.session_timeout)
        ]
        
        for sid in expired_sessions:
            del self.sessions[sid]
        
        return len(expired_sessions)
    
    def clear_all_sessions(self) -> None:
        """清除所有会话"""
        self.sessions.clear()
    
    def get_session_count(self) -> int:
        """获取会话数量"""
        return len(self.sessions)
    
    def enhance_query(
        self,
        query: str,
        session_id: str,
        current_intent: Optional[str] = None
    ) -> str:
        """
        增强查询（添加上下文信息）
        
        Args:
            query: 用户查询
            session_id: 会话ID
            current_intent: 当前意图
            
        Returns:
            增强后的查询
        """
        session = self.get_session(session_id)
        if not session:
            return query
        
        # 获取上一个意图
        last_intent = session.get_last_intent()
        if not last_intent:
            return query
        
        # 如果当前查询缺少实体，尝试从上下文中补充
        enhanced_query = query
        
        # 示例：如果查询是"明天呢"，添加上下文
        if query in ['明天呢', '后天呢', '昨天呢'] and 'date' in last_intent['entities']:
            enhanced_query = f"{query}（参考：{last_intent['intent']}）"
        
        return enhanced_query
    
    def resolve_entity(
        self,
        entity_name: str,
        session_id: str,
        current_entities: Dict[str, Any]
    ) -> Any:
        """
        解析实体（处理指代消解）
        
        Args:
            entity_name: 实体名称
            session_id: 会话ID
            current_entities: 当前提取的实体
            
        Returns:
            解析后的实体值
        """
        # 如果当前实体已存在，直接返回
        if entity_name in current_entities:
            return current_entities[entity_name]
        
        # 从上下文中查找
        session = self.get_session(session_id)
        if session and entity_name in session.entities:
            return session.entities[entity_name]
        
        return None
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        获取会话统计信息
        
        Returns:
            统计信息
        """
        total_sessions = len(self.sessions)
        expired_sessions = sum(
            1 for session in self.sessions.values()
            if session.is_expired(self.session_timeout)
        )
        active_sessions = total_sessions - expired_sessions
        
        return {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'expired_sessions': expired_sessions,
            'session_timeout': self.session_timeout
        }


# 全局上下文管理器实例
_context_manager = None


def get_context_manager() -> ContextManager:
    """
    获取全局上下文管理器实例
    
    Returns:
        上下文管理器实例
    """
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager


def get_session_context(session_id: str) -> Optional[Dict[str, Any]]:
    """
    获取会话上下文的便捷函数
    
    Args:
        session_id: 会话ID
        
    Returns:
        上下文数据或None
    """
    return get_context_manager().get_context(session_id)
