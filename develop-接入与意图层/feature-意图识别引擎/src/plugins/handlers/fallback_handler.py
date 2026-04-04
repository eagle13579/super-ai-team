"""
意图识别引擎 - 兜底处理器

处理所有无法识别的意图，提供友好的引导提示

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

import asyncio
import random
from typing import Dict, Optional, Any

from interfaces.base_handler import BaseHandler, HandlerResult


class FallbackHandler(BaseHandler):
    """
    兜底意图处理器
    
    处理所有无法识别的意图，返回友好的引导提示。
    提供多种随机回复话术，引导用户尝试已知功能。
    
    Attributes:
        intent_name: 处理的意图名称，固定为 "fallback"
        name: 处理器名称
        
    Example:
        >>> handler = FallbackHandler()
        >>> result = handler.handle_sync("未知查询", {})
        >>> print(result.success)
        True
        >>> print("天气" in result.message or "搜索" in result.message)
        True
    """
    
    # 随机回复话术库
    FALLBACK_RESPONSES = [
        "抱歉，我不太明白您的意思。",
        "这个功能我还在学习中，您可以换个方式问我。",
        "抱歉，我没有理解您的问题。",
        "我对这个话题还不太熟悉，能否换个问题？",
        "这个有点超出我的能力范围了。"
    ]
    
    # 引导提示话术
    GUIDANCE_TEMPLATES = [
        "您可以尝试问我：'{example}'",
        "建议您可以这样问我：'{example}'",
        "您可以试试：'{example}'",
        "也许您想了解：'{example}'",
        "我可以帮您：'{example}'"
    ]
    
    # 示例问题
    EXAMPLE_QUESTIONS = [
        "北京今天的天气怎么样",
        "帮我搜索一下最新资讯",
        "查询明天的天气",
        "搜索Python教程",
        "今天的天气如何"
    ]
    
    @property
    def intent_name(self) -> str:
        """
        处理的意图名称
        
        Returns:
            意图名称字符串，固定返回 "fallback"
        """
        return "fallback"
    
    async def handle(
        self, 
        query: str, 
        entities: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> HandlerResult:
        """
        异步处理兜底意图
        
        将同步处理逻辑委托给 handle_sync 方法执行
        
        Args:
            query: 用户输入文本
            entities: 提取的实体信息
            context: 上下文信息，可选
            
        Returns:
            HandlerResult: 处理结果，包含引导性话术
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.handle_sync, query, entities, context)
    
    def handle_sync(
        self, 
        query: str, 
        entities: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> HandlerResult:
        """
        同步处理兜底意图
        
        生成随机的兜底回复，并引导用户尝试已知功能。
        
        Args:
            query: 用户输入文本
            entities: 提取的实体信息
            context: 上下文信息，可选
            
        Returns:
            HandlerResult: 处理结果
                - success: 是否成功处理（始终为 True）
                - message: 兜底回复话术
                - data: 包含原始查询和建议
                - intent: 意图名称
                
        Example:
            >>> handler = FallbackHandler()
            >>> result = handler.handle_sync("未知查询", {})
            >>> result.success
            True
            >>> result.message
            '抱歉，我不太明白您的意思。您可以尝试问我：'北京今天的天气怎么样''
        """
        try:
            # 生成随机兜底回复
            fallback_response = self._get_random_fallback()
            
            # 生成引导提示
            guidance = self._get_guidance()
            
            # 组合完整回复
            full_message = f"{fallback_response}{guidance}"
            
            return HandlerResult(
                success=True,
                message=full_message,
                data={
                    "original_query": query,
                    "fallback_response": fallback_response,
                    "guidance": guidance,
                    "suggestions": self.EXAMPLE_QUESTIONS[:3]  # 提供前3个建议
                },
                intent=self.intent_name
            )
            
        except Exception as e:
            # 异常情况下也返回友好的提示
            return HandlerResult(
                success=True,
                message="抱歉，服务遇到了一些问题。请您稍后再试。",
                error=str(e),
                intent=self.intent_name
            )
    
    def _get_random_fallback(self) -> str:
        """
        获取随机兜底回复
        
        Returns:
            随机选择的兜底回复话术
        """
        return random.choice(self.FALLBACK_RESPONSES)
    
    def _get_guidance(self) -> str:
        """
        获取引导提示
        
        Returns:
            格式化后的引导提示，包含示例问题
        """
        template = random.choice(self.GUIDANCE_TEMPLATES)
        example = random.choice(self.EXAMPLE_QUESTIONS)
        return template.format(example=example)
    
    def can_handle(self, intent_name: str) -> bool:
        """
        检查是否能处理指定意图
        
        FallbackHandler 可以处理任何意图，作为最后的兜底方案
        
        Args:
            intent_name: 意图名称
            
        Returns:
            始终返回 True
            
        Example:
            >>> handler = FallbackHandler()
            >>> handler.can_handle("unknown")
            True
            >>> handler.can_handle("weather_query")
            True
            >>> handler.can_handle("anything")
            True
        """
        return True
    
    def get_fallback_message(self, query: str) -> str:
        """
        获取针对特定查询的兜底消息
        
        Args:
            query: 用户查询
            
        Returns:
            完整的兜底消息
        """
        fallback = self._get_random_fallback()
        guidance = self._get_guidance()
        return f"{fallback}{guidance}"
    
    def add_response(self, response: str) -> None:
        """
        添加新的兜底回复话术
        
        Args:
            response: 新的回复话术
        """
        if response and response not in self.FALLBACK_RESPONSES:
            self.FALLBACK_RESPONSES.append(response)
    
    def add_example(self, example: str) -> None:
        """
        添加新的示例问题
        
        Args:
            example: 新的示例问题
        """
        if example and example not in self.EXAMPLE_QUESTIONS:
            self.EXAMPLE_QUESTIONS.append(example)
