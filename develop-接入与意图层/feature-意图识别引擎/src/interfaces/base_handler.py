"""
意图识别引擎 - 意图处理接口

定义所有意图处理器的统一接口，支持异步操作
参考 @reference/intent_engine.py 中的逻辑设计

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class HandlerResult(BaseModel):
    """处理器结果"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    intent: str


class BaseHandler(ABC):
    """
    意图处理器基类
    
    所有具体意图处理器的抽象接口
    """
    
    @property
    @abstractmethod
    def intent_name(self) -> str:
        """
        处理的意图名称
        
        Returns:
            意图名称字符串
        """
        pass
    
    @property
    def name(self) -> str:
        """
        处理器名称
        
        Returns:
            处理器名称
        """
        return self.__class__.__name__
    
    @abstractmethod
    async def handle(self, query: str, entities: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> HandlerResult:
        """
        异步处理方法
        
        Args:
            query: 用户输入文本
            entities: 提取的实体信息
            context: 上下文信息
            
        Returns:
            处理结果
        """
        pass
    
    @abstractmethod
    def handle_sync(self, query: str, entities: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> HandlerResult:
        """
        同步处理方法
        
        Args:
            query: 用户输入文本
            entities: 提取的实体信息
            context: 上下文信息
            
        Returns:
            处理结果
        """
        pass
    
    def can_handle(self, intent_name: str) -> bool:
        """
        检查是否能处理指定意图
        
        Args:
            intent_name: 意图名称
            
        Returns:
            是否能处理
        """
        return intent_name == self.intent_name
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        初始化处理器
        
        Args:
            config: 处理器配置
        """
        pass
    
    def shutdown(self) -> None:
        """
        关闭处理器
        """
        pass
