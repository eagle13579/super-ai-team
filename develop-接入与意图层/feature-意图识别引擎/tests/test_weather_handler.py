"""
意图识别引擎 - 天气处理器测试

测试 WeatherHandler 的功能

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
from plugins.handlers.weather_handler_v2 import WeatherHandler
from interfaces.base_handler import HandlerResult


class TestWeatherHandler:
    """
    测试 WeatherHandler 类
    
    包含三个测试用例：
    1. 正常情况：传入包含 '北京' 实体的匹配结果
    2. 异常情况：传入实体为空的结果
    3. 边界情况：验证 can_handle 方法
    """
    
    def setup_method(self):
        """设置测试环境"""
        self.handler = WeatherHandler()
    
    def test_case1_normal_beijing(self):
        """
        测试用例1：正常情况 - 传入包含 '北京' 实体的匹配结果
        
        期望：返回成功的结果，包含北京的天气信息
        """
        # 测试同步方法
        result = self.handler.handle_sync("北京天气", {"city": "北京"})
        
        # 验证结果
        assert isinstance(result, HandlerResult)
        assert result.success is True
        assert "北京今日晴，15-25度" in result.message
        assert result.data is not None
        assert result.data["city"] == "北京"
        assert result.data["weather"] == "晴"
        assert result.data["temperature"] == "15-25度"
        assert result.intent == "weather_query"
        
        # 测试异步方法
        async def test_async():
            async_result = await self.handler.handle("北京天气", {"city": "北京"})
            assert isinstance(async_result, HandlerResult)
            assert async_result.success is True
            assert "北京今日晴，15-25度" in async_result.message
            assert async_result.intent == "weather_query"
        
        asyncio.run(test_async())
    
    def test_case2_empty_entities(self):
        """
        测试用例2：异常情况 - 传入实体为空的结果
        
        期望：返回错误的结果，提示请提供城市信息
        """
        # 测试同步方法 - 空实体
        result = self.handler.handle_sync("天气怎么样", {})
        
        # 验证结果
        assert isinstance(result, HandlerResult)
        assert result.success is False
        assert "请提供城市信息" in result.message
        assert result.intent == "weather_query"
        
        # 测试同步方法 - 无 city 键的实体
        result2 = self.handler.handle_sync("天气怎么样", {"other": "value"})
        assert isinstance(result2, HandlerResult)
        assert result2.success is False
        assert "请提供城市信息" in result2.message
        
        # 测试异步方法
        async def test_async():
            async_result = await self.handler.handle("天气怎么样", {})
            assert isinstance(async_result, HandlerResult)
            assert async_result.success is False
            assert "请提供城市信息" in async_result.message
            assert async_result.intent == "weather_query"
        
        asyncio.run(test_async())
    
    def test_case3_can_handle(self):
        """
        测试用例3：边界情况 - 验证 can_handle 方法
        
        期望：
        - 对于 weather_query 意图，返回 True
        - 对于其他意图，返回 False
        """
        # 测试 weather_query 意图
        assert self.handler.can_handle("weather_query") is True
        
        # 测试其他意图
        assert self.handler.can_handle("code_generation") is False
        assert self.handler.can_handle("information_search") is False
        assert self.handler.can_handle("general_chat") is False
        assert self.handler.can_handle("unknown_intent") is False
    
    def test_other_city(self):
        """
        测试其他城市的情况
        
        期望：返回错误的结果，提示暂未获取该城市天气
        """
        # 测试同步方法
        result = self.handler.handle_sync("上海天气", {"city": "上海"})
        
        # 验证结果
        assert isinstance(result, HandlerResult)
        assert result.success is False
        assert "暂未获取该城市天气" in result.message
        assert result.data is not None
        assert result.data["city"] == "上海"
        assert result.intent == "weather_query"
    
    def test_query_extraction(self):
        """
        测试从查询中提取城市的情况
        
        期望：当 entities 中没有 city 时，从 query 中提取
        """
        # 测试同步方法 - 从查询中提取城市
        result = self.handler.handle_sync("北京天气怎么样", {})
        
        # 验证结果
        assert isinstance(result, HandlerResult)
        assert result.success is True
        assert "北京今日晴，15-25度" in result.message
        assert result.data is not None
        assert result.data["city"] == "北京"
        assert result.intent == "weather_query"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
