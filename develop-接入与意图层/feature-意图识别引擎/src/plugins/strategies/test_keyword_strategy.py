"""
测试关键词匹配策略

验证 KeywordStrategy 类的功能

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
from plugins.strategies.keyword_strategy import KeywordStrategy


async def test_keyword_strategy():
    """
    测试关键词匹配策略
    """
    print("=" * 60)
    print("测试关键词匹配策略")
    print("=" * 60)
    print()
    
    # 创建策略实例
    strategy = KeywordStrategy()
    strategy.initialize()
    
    # 测试用例
    test_cases = [
        # (输入文本, 预期意图, 预期置信度范围)
        ("你好", "general_chat", (0.7, 1.0)),
        ("谢谢你", "general_chat", (0.6, 1.0)),
        ("再见", "general_chat", (0.6, 1.0)),
        ("帮我写代码", "code_generation", (0.6, 1.0)),
        ("写Python代码", "code_generation", (0.5, 1.0)),
        ("搜索信息", "information_search", (0.6, 1.0)),
        ("查找资料", "information_search", (0.5, 1.0)),
        ("天气怎么样", "question_answering", (0.5, 0.7)),  # 应该匹配到问答意图
        ("", None, (0.0, 0.0)),  # 空输入
    ]
    
    print("测试用例:")
    print("-" * 60)
    
    for query, expected_intent, confidence_range in test_cases:
        # 测试同步方法
        sync_result = strategy.recognize_sync(query)
        
        # 测试异步方法
        async_result = await strategy.recognize(query)
        
        # 验证结果
        print(f"输入: '{query}'")
        print(f"同步结果: {sync_result.intent if sync_result else 'None'}")
        print(f"异步结果: {async_result.intent if async_result else 'None'}")
        
        if sync_result:
            print(f"置信度: {sync_result.confidence:.2f}")
            print(f"匹配关键词: {sync_result.metadata.get('matched_keywords', [])}")
        
        # 验证意图是否正确
        if expected_intent:
            assert sync_result and sync_result.intent == expected_intent, f"同步方法预期意图 {expected_intent}, 实际 {sync_result.intent if sync_result else 'None'}"
            assert async_result and async_result.intent == expected_intent, f"异步方法预期意图 {expected_intent}, 实际 {async_result.intent if async_result else 'None'}"
            
            # 验证置信度范围
            if sync_result:
                assert confidence_range[0] <= sync_result.confidence <= confidence_range[1], \
                    f"置信度不在预期范围内: {sync_result.confidence:.2f} 不在 {confidence_range}"
        else:
            assert not sync_result, f"同步方法预期无结果, 实际 {sync_result.intent if sync_result else 'None'}"
            assert not async_result, f"异步方法预期无结果, 实际 {async_result.intent if async_result else 'None'}"
        
        print()
    
    # 测试实体提取
    print("测试实体提取:")
    print("-" * 60)
    
    entity_test_cases = [
        "帮我写10行Python代码",
        "搜索2024-04-04的天气",
    ]
    
    for query in entity_test_cases:
        result = strategy.recognize_sync(query)
        if result:
            print(f"输入: '{query}'")
            print(f"意图: {result.intent}")
            print(f"匹配关键词: {result.metadata.get('matched_keywords', [])}")
            print()
    
    # 测试关闭
    strategy.shutdown()
    print("测试关闭策略: 成功")
    
    print("=" * 60)
    print("所有测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_keyword_strategy())
