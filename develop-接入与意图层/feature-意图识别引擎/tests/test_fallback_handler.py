"""
意图识别引擎 - 兜底处理器测试

测试 FallbackHandler 的功能

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

import sys
import os
from pathlib import Path

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest
import asyncio
from plugins.handlers.fallback_handler import FallbackHandler
from interfaces.base_handler import HandlerResult


class TestFallbackHandler:
    """
    测试 FallbackHandler 类
    
    包含以下测试场景：
    1. 验证是否能捕捉任何 intent_name
    2. 验证返回的 HandlerResult 是否包含预期的引导性话术
    3. 验证兜底回复的多样性
    4. 验证异常情况处理
    """
    
    def setup_method(self):
        """设置测试环境"""
        self.handler = FallbackHandler()
    
    def test_can_handle_any_intent(self):
        """
        测试场景1：验证是否能捕捉任何 intent_name
        
        期望：对于任何意图名称，can_handle 都返回 True
        """
        # 测试各种意图名称
        test_intents = [
            "unknown",
            "weather_query",
            "code_generation",
            "information_search",
            "general_chat",
            "anything",
            "random_intent",
            ""
        ]
        
        for intent in test_intents:
            assert self.handler.can_handle(intent) is True, f"应该能处理意图: {intent}"
    
    def test_result_contains_guidance(self):
        """
        测试场景2：验证返回的 HandlerResult 是否包含预期的引导性话术
        
        期望：
        - 返回成功状态
        - 消息中包含引导提示（天气或搜索相关）
        - 数据中包含建议列表
        """
        # 测试同步方法
        result = self.handler.handle_sync("未知查询", {})
        
        # 验证结果类型
        assert isinstance(result, HandlerResult)
        assert result.success is True
        assert result.intent == "fallback"
        
        # 验证消息中包含引导提示
        assert result.message is not None
        assert len(result.message) > 0
        
        # 验证消息中包含关键词（天气或搜索）
        assert "天气" in result.message or "搜索" in result.message, \
            f"消息应包含引导关键词，实际消息: {result.message}"
        
        # 验证数据中包含建议
        assert result.data is not None
        assert "suggestions" in result.data
        assert len(result.data["suggestions"]) > 0
        
        # 验证建议中包含天气或搜索相关
        suggestions = result.data["suggestions"]
        has_weather_or_search = any(
            "天气" in s or "搜索" in s for s in suggestions
        )
        assert has_weather_or_search, "建议列表应包含天气或搜索相关"
    
    def test_fallback_response_diversity(self):
        """
        测试场景3：验证兜底回复的多样性
        
        期望：多次调用返回不同的兜底回复
        """
        responses = set()
        
        # 多次调用，收集不同的回复
        for _ in range(10):
            result = self.handler.handle_sync("测试查询", {})
            responses.add(result.message)
        
        # 验证至少有两种不同的回复（随机性）
        assert len(responses) > 1, "应该有多种不同的兜底回复"
    
    def test_async_handle(self):
        """
        测试场景4：验证异步处理方法
        
        期望：异步方法返回与同步方法相同的结果
        """
        async def test_async():
            result = await self.handler.handle("异步测试", {})
            
            assert isinstance(result, HandlerResult)
            assert result.success is True
            assert result.intent == "fallback"
            assert "天气" in result.message or "搜索" in result.message
            assert result.data is not None
            assert "suggestions" in result.data
        
        asyncio.run(test_async())
    
    def test_empty_query(self):
        """
        测试场景5：验证空查询处理
        
        期望：即使查询为空，也能返回友好的兜底回复
        """
        result = self.handler.handle_sync("", {})
        
        assert isinstance(result, HandlerResult)
        assert result.success is True
        assert result.intent == "fallback"
        assert result.message is not None
        assert len(result.message) > 0
    
    def test_data_structure(self):
        """
        测试场景6：验证返回数据的结构
        
        期望：返回的数据包含所有预期的字段
        """
        result = self.handler.handle_sync("测试", {"some": "entity"})
        
        # 验证数据结构
        assert "original_query" in result.data
        assert "fallback_response" in result.data
        assert "guidance" in result.data
        assert "suggestions" in result.data
        
        # 验证原始查询被正确保存
        assert result.data["original_query"] == "测试"
        
        # 验证建议列表不为空
        assert isinstance(result.data["suggestions"], list)
        assert len(result.data["suggestions"]) > 0
    
    def test_add_custom_response(self):
        """
        测试场景7：验证添加自定义回复
        
        期望：可以添加新的兜底回复话术
        """
        custom_response = "这是一个自定义回复"
        self.handler.add_response(custom_response)
        
        # 验证新回复已添加
        assert custom_response in self.handler.FALLBACK_RESPONSES
    
    def test_add_custom_example(self):
        """
        测试场景8：验证添加自定义示例
        
        期望：可以添加新的示例问题
        """
        custom_example = "自定义示例问题"
        self.handler.add_example(custom_example)
        
        # 验证新示例已添加
        assert custom_example in self.handler.EXAMPLE_QUESTIONS


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
