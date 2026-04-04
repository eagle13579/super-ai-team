"""
意图识别引擎 - 识别策略接口

定义所有识别策略的统一接口，支持异步操作
参考 @reference/intent_engine.py 中的逻辑设计

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from enum import Enum


class IntentStrategyType(str, Enum):
    """识别策略类型"""
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    FEW_SHOT = "few_shot"
    FUSION = "fusion"


class MatchResult(BaseModel):
    """匹配结果"""
    intent: str
    confidence: float
    matched_text: str = ""
    strategy: IntentStrategyType
    metadata: Dict[str, Any] = {}


class BaseStrategy(ABC):
    """
    识别策略基类
    
    所有具体识别策略的抽象接口
    """
    
    @property
    @abstractmethod
    def strategy_type(self) -> IntentStrategyType:
        """
        策略类型
        
        Returns:
            策略类型枚举值
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        策略名称
        
        Returns:
            策略名称字符串
        """
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """
        策略优先级
        
        Returns:
            优先级数值，越小优先级越高
        """
        pass
    
    @abstractmethod
    async def recognize(self, query: str, context: Optional[Dict[str, Any]] = None) -> Optional[MatchResult]:
        """
        异步识别方法
        
        Args:
            query: 用户输入文本
            context: 上下文信息
            
        Returns:
            匹配结果或None
        """
        pass
    
    @abstractmethod
    def recognize_sync(self, query: str, context: Optional[Dict[str, Any]] = None) -> Optional[MatchResult]:
        """
        同步识别方法
        
        Args:
            query: 用户输入文本
            context: 上下文信息
            
        Returns:
            匹配结果或None
        """
        pass
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        初始化策略
        
        Args:
            config: 策略配置
        """
        pass
    
    def shutdown(self) -> None:
        """
        关闭策略
        """
        pass
