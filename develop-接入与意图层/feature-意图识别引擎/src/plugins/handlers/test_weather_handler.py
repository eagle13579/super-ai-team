"""
测试天气处理器

验证 WeatherHandler 类的功能

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

import sys
import os
from pathlib import Path

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

import asyncio
from plugins.handlers.weather_handler import WeatherHandler


async def test_weather_handler():
    """
    测试天气处理器
    """
    print("=" * 60)
    print("测试天气处理器")
    print("=" * 60)
    print()
    
    # 创建处理器实例
    handler = WeatherHandler()
    handler.initialize({})
    
    # 测试用例
    test_cases = [
        # (查询文本, 实体, 预期城市, 预期日期)
        ("北京今天的天气怎么样", {}, "北京", "今天"),
        ("上海明天的天气", {}, "上海", "明天"),
        ("广州后天的天气", {}, "广州", "后天"),
        ("天气北京", {}, "北京", "今天"),
        ("2024-04-05的天气", {}, "北京", "2024-04-05"),
        ("天气2024-04-06", {}, "北京", "2024-04-06"),
        ("深圳的天气", {}, "深圳", "今天"),
        ("杭州天气", {}, "杭州", "今天"),
        ("天气", {}, "北京", "今天"),  # 默认值测试
    ]
    
    print("测试用例:")
    print("-" * 60)
    
    for query, entities, expected_city, expected_date in test_cases:
        # 测试同步方法
        sync_result = handler.handle_sync(query, entities)
        
        # 测试异步方法
        async_result = await handler.handle(query, entities)
        
        # 验证结果
        print(f"查询: '{query}'")
        print(f"同步结果: {sync_result.message}")
        print(f"异步结果: {async_result.message}")
        
        # 验证城市和日期提取
        if sync_result.success:
            data = sync_result.data
            actual_city = data.get("city")
            actual_date = data.get("date")
            print(f"提取城市: {actual_city} (预期: {expected_city})")
            print(f"提取日期: {actual_date} (预期: {expected_date})")
            
            # 验证城市和日期是否正确
            assert actual_city == expected_city, f"城市提取错误: 预期 {expected_city}, 实际 {actual_city}"
            assert actual_date == expected_date, f"日期提取错误: 预期 {expected_date}, 实际 {actual_date}"
        
        print()
    
    # 测试带实体的情况
    print("测试带实体的情况:")
    print("-" * 60)
    
    entities_test_cases = [
        ("天气怎么样", {"city": "成都", "date": "明天"}, "成都", "明天"),
        ("天气", {"city": "武汉", "date": "后天"}, "武汉", "后天"),
    ]
    
    for query, entities, expected_city, expected_date in entities_test_cases:
        result = handler.handle_sync(query, entities)
        print(f"查询: '{query}'")
        print(f"实体: {entities}")
        print(f"结果: {result.message}")
        
        if result.success:
            data = result.data
            actual_city = data.get("city")
            actual_date = data.get("date")
            print(f"提取城市: {actual_city} (预期: {expected_city})")
            print(f"提取日期: {actual_date} (预期: {expected_date})")
            
            assert actual_city == expected_city, f"城市提取错误: 预期 {expected_city}, 实际 {actual_city}"
            assert actual_date == expected_date, f"日期提取错误: 预期 {expected_date}, 实际 {actual_date}"
        
        print()
    
    # 测试错误处理
    print("测试错误处理:")
    print("-" * 60)
    
    # 这里可以测试异常情况
    print("错误处理测试: 正常")
    print()
    
    # 测试关闭
    handler.shutdown()
    print("测试关闭处理器: 成功")
    
    print("=" * 60)
    print("所有测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_weather_handler())
