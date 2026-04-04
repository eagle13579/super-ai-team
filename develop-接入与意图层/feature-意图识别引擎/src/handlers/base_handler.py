"""
意图识别引擎 - 基础意图处理器

提供意图处理的基础类和示例实现，包括：
- 基础意图处理器抽象类
- 处理器注册表
- 具体意图处理器示例

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass


@dataclass
class HandlerResult:
    """处理器结果"""
    success: bool
    message: str
    data: Dict[str, Any] = None
    error: Optional[str] = None


class BaseIntentHandler(ABC):
    """
    基础意图处理器抽象类
    
    所有具体意图处理器的基类，定义统一的处理接口
    
    使用示例:
        class MyHandler(BaseIntentHandler):
            @property
            def intent_name(self) -> str:
                return "my_intent"
            
            def handle(self, query: str, entities: Dict[str, Any]) -> HandlerResult:
                # 处理逻辑
                return HandlerResult(success=True, message="处理成功")
    """
    
    def __init__(self, name: Optional[str] = None):
        self._name = name
        self._metadata: Dict[str, Any] = {}
    
    @property
    def name(self) -> str:
        """处理器名称"""
        return self._name or self.__class__.__name__
    
    @property
    @abstractmethod
    def intent_name(self) -> str:
        """
        处理的意图名称
        
        Returns:
            意图标识符字符串
        """
        pass
    
    @abstractmethod
    def handle(self, query: str, entities: Dict[str, Any]) -> HandlerResult:
        """
        处理意图请求
        
        Args:
            query: 用户原始输入
            entities: 提取的实体信息
            
        Returns:
            处理结果
        """
        pass
    
    async def handle_async(self, query: str, entities: Dict[str, Any]) -> HandlerResult:
        """
        异步处理意图请求
        
        默认实现调用同步handle方法，子类可覆盖实现真正的异步处理
        
        Args:
            query: 用户原始输入
            entities: 提取的实体信息
            
        Returns:
            处理结果
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.handle, query, entities)
    
    def can_handle(self, intent_name: str) -> bool:
        """
        检查是否能处理指定意图
        
        Args:
            intent_name: 意图名称
            
        Returns:
            是否能处理
        """
        return intent_name == self.intent_name
    
    def validate_entities(self, entities: Dict[str, Any]) -> bool:
        """
        验证实体信息是否完整
        
        Args:
            entities: 实体信息
            
        Returns:
            验证是否通过
        """
        return True
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        self._metadata[key] = value
    
    def get_metadata(self, key: str) -> Optional[Any]:
        """获取元数据"""
        return self._metadata.get(key)


class IntentHandlerRegistry:
    """
    意图处理器注册表
    
    管理所有意图处理器的注册和查找
    
    使用示例:
        registry = IntentHandlerRegistry()
        registry.register(CodeGenerationHandler())
        
        handler = registry.get_handler("code_generation")
        result = handler.handle(query, entities)
    """
    
    def __init__(self):
        self._handlers: Dict[str, BaseIntentHandler] = {}
        self._fallback_handler: Optional[BaseIntentHandler] = None
    
    def register(self, handler: BaseIntentHandler) -> None:
        """
        注册处理器
        
        Args:
            handler: 意图处理器实例
        """
        self._handlers[handler.intent_name] = handler
    
    def unregister(self, intent_name: str) -> bool:
        """
        注销处理器
        
        Args:
            intent_name: 意图名称
            
        Returns:
            是否成功注销
        """
        if intent_name in self._handlers:
            del self._handlers[intent_name]
            return True
        return False
    
    def get_handler(self, intent_name: str) -> Optional[BaseIntentHandler]:
        """
        获取处理器
        
        Args:
            intent_name: 意图名称
            
        Returns:
            处理器实例或None
        """
        return self._handlers.get(intent_name)
    
    def set_fallback_handler(self, handler: BaseIntentHandler) -> None:
        """
        设置默认处理器
        
        当找不到对应意图的处理器时使用
        
        Args:
            handler: 默认处理器
        """
        self._fallback_handler = handler
    
    def handle(self, intent_name: str, query: str, entities: Dict[str, Any]) -> HandlerResult:
        """
        处理意图请求
        
        Args:
            intent_name: 意图名称
            query: 用户输入
            entities: 实体信息
            
        Returns:
            处理结果
        """
        handler = self.get_handler(intent_name)
        
        if handler:
            return handler.handle(query, entities)
        
        if self._fallback_handler:
            return self._fallback_handler.handle(query, entities)
        
        return HandlerResult(
            success=False,
            message="未找到对应的处理器",
            error=f"No handler found for intent: {intent_name}"
        )
    
    async def handle_async(self, intent_name: str, query: str, entities: Dict[str, Any]) -> HandlerResult:
        """
        异步处理意图请求
        
        Args:
            intent_name: 意图名称
            query: 用户输入
            entities: 实体信息
            
        Returns:
            处理结果
        """
        handler = self.get_handler(intent_name)
        
        if handler:
            return await handler.handle_async(query, entities)
        
        if self._fallback_handler:
            return await self._fallback_handler.handle_async(query, entities)
        
        return HandlerResult(
            success=False,
            message="未找到对应的处理器",
            error=f"No handler found for intent: {intent_name}"
        )
    
    def list_handlers(self) -> List[str]:
        """
        列出所有已注册的意图名称
        
        Returns:
            意图名称列表
        """
        return list(self._handlers.keys())
    
    def clear(self) -> None:
        """清空所有处理器"""
        self._handlers.clear()
        self._fallback_handler = None


# ==================== 具体意图处理器示例 ====================

class CodeGenerationHandler(BaseIntentHandler):
    """
    代码生成意图处理器
    
    处理代码生成相关请求
    """
    
    @property
    def intent_name(self) -> str:
        return "code_generation"
    
    def handle(self, query: str, entities: Dict[str, Any]) -> HandlerResult:
        """
        处理代码生成请求
        
        Args:
            query: 用户输入，如"帮我写一个Python排序函数"
            entities: 提取的实体，如{"language": "Python", "function_name": "排序"}
            
        Returns:
            处理结果
        """
        language = entities.get("language", "Python")
        
        # 模拟代码生成逻辑
        generated_code = self._generate_code(query, language)
        
        return HandlerResult(
            success=True,
            message=f"已生成{language}代码",
            data={
                "code": generated_code,
                "language": language,
                "description": query
            }
        )
    
    def _generate_code(self, query: str, language: str) -> str:
        """生成代码（模拟实现）"""
        # 实际项目中应调用代码生成模型
        return f"# {language}代码生成示例\n# 请求: {query}\n\ndef example():\n    pass"


class CodeReviewHandler(BaseIntentHandler):
    """
    代码审查意图处理器
    
    处理代码审查相关请求
    """
    
    @property
    def intent_name(self) -> str:
        return "code_review"
    
    def handle(self, query: str, entities: Dict[str, Any]) -> HandlerResult:
        """
        处理代码审查请求
        
        Args:
            query: 用户输入
            entities: 提取的实体
            
        Returns:
            处理结果
        """
        return HandlerResult(
            success=True,
            message="代码审查完成",
            data={
                "review_points": [
                    "代码结构清晰",
                    "建议添加异常处理",
                    "命名规范良好"
                ],
                "suggestions": ["考虑使用类型提示", "添加单元测试"]
            }
        )


class SearchHandler(BaseIntentHandler):
    """
    搜索意图处理器
    
    处理信息搜索相关请求
    """
    
    @property
    def intent_name(self) -> str:
        return "information_search"
    
    def handle(self, query: str, entities: Dict[str, Any]) -> HandlerResult:
        """
        处理搜索请求
        
        Args:
            query: 用户输入，如"搜索Python教程"
            entities: 提取的实体，如{"query": "Python教程", "category": "tutorial"}
            
        Returns:
            处理结果
        """
        search_query = entities.get("query", query)
        
        return HandlerResult(
            success=True,
            message=f"搜索完成: {search_query}",
            data={
                "query": search_query,
                "results": [
                    {"title": "Python入门教程", "url": "https://example.com/python-intro"},
                    {"title": "Python进阶指南", "url": "https://example.com/python-advanced"}
                ]
            }
        )


class ChatHandler(BaseIntentHandler):
    """
    聊天意图处理器
    
    处理闲聊相关请求
    """
    
    @property
    def intent_name(self) -> str:
        return "general_chat"
    
    def handle(self, query: str, entities: Dict[str, Any]) -> HandlerResult:
        """
        处理聊天请求
        
        Args:
            query: 用户输入
            entities: 提取的实体
            
        Returns:
            处理结果
        """
        # 简单的回复逻辑
        responses = {
            "你好": "你好！很高兴为您服务。",
            "谢谢": "不客气！",
            "再见": "再见！祝您有愉快的一天！"
        }
        
        response = "收到您的消息，有什么可以帮助您的吗？"
        for key, value in responses.items():
            if key in query:
                response = value
                break
        
        return HandlerResult(
            success=True,
            message=response,
            data={"response": response}
        )


class FallbackHandler(BaseIntentHandler):
    """
    默认处理器
    
    当无法识别意图时使用
    """
    
    @property
    def intent_name(self) -> str:
        return "unknown"
    
    def handle(self, query: str, entities: Dict[str, Any]) -> HandlerResult:
        """
        处理未知意图
        
        Args:
            query: 用户输入
            entities: 提取的实体
            
        Returns:
            处理结果
        """
        return HandlerResult(
            success=False,
            message="抱歉，我不太理解您的请求。",
            data={
                "suggestions": [
                    "尝试使用更清晰的表达",
                    "提供更多上下文信息",
                    "使用关键词如'写代码'、'搜索'等"
                ]
            },
            error="Intent not recognized"
        )


# ==================== 使用示例 ====================

def example_usage():
    """使用示例"""
    
    # 创建注册表
    registry = IntentHandlerRegistry()
    
    # 注册处理器
    registry.register(CodeGenerationHandler())
    registry.register(CodeReviewHandler())
    registry.register(SearchHandler())
    registry.register(ChatHandler())
    
    # 设置默认处理器
    registry.set_fallback_handler(FallbackHandler())
    
    # 测试处理
    test_cases = [
        ("code_generation", "帮我写一个Python函数", {"language": "Python"}),
        ("information_search", "搜索Python教程", {"query": "Python教程"}),
        ("general_chat", "你好", {}),
        ("unknown_intent", "这是一个未知意图", {})
    ]
    
    print("=== 意图处理器测试 ===\n")
    
    for intent_name, query, entities in test_cases:
        result = registry.handle(intent_name, query, entities)
        print(f"意图: {intent_name}")
        print(f"输入: '{query}'")
        print(f"成功: {result.success}")
        print(f"消息: {result.message}")
        if result.data:
            print(f"数据: {result.data}")
        if result.error:
            print(f"错误: {result.error}")
        print()


if __name__ == "__main__":
    example_usage()
