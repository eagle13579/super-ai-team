"""
意图识别引擎 - 综合测试

验证所有核心组件的功能

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

import sys
import os
from pathlib import Path

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

import asyncio
from plugins.strategies.semantic_strategy import SemanticStrategy
from plugins.strategies.keyword_strategy import KeywordStrategy
from common.entity_extractor import EntityExtractor, extract_entities
from common.context_manager import ContextManager, get_context_manager
from core.result_fusion import ResultFusion, FusionStrategy, FusionConfig
from common.monitoring import MonitoringSystem, MetricType
from interfaces.base_strategy import MatchResult, IntentStrategyType


async def test_semantic_strategy():
    """测试语义检索策略"""
    print("=" * 60)
    print("测试语义检索策略")
    print("=" * 60)
    
    strategy = SemanticStrategy()
    strategy.initialize()
    
    test_queries = [
        "帮我写代码",
        "搜索信息",
        "你好",
        "北京天气怎么样"
    ]
    
    for query in test_queries:
        result = await strategy.recognize(query)
        if result:
            print(f"查询: '{query}'")
            print(f"  意图: {result.intent}")
            print(f"  置信度: {result.confidence:.2f}")
            print(f"  策略: {result.strategy.value}")
        else:
            print(f"查询: '{query}' - 未匹配")
    
    print()


def test_entity_extractor():
    """测试实体提取器"""
    print("=" * 60)
    print("测试实体提取器")
    print("=" * 60)
    
    test_queries = [
        "北京今天的天气怎么样",
        "帮我写10行Python代码",
        "搜索2024-04-05的信息",
        "明天下午3点开会",
        "价格是100元",
        "联系邮箱是test@example.com"
    ]
    
    for query in test_queries:
        entities = extract_entities(query)
        print(f"查询: '{query}'")
        print(f"  实体: {entities}")
    
    print()


def test_context_manager():
    """测试上下文管理器"""
    print("=" * 60)
    print("测试上下文管理器")
    print("=" * 60)
    
    manager = ContextManager()
    session_id = "test_session_001"
    
    # 模拟多轮对话
    conversations = [
        ("北京今天的天气怎么样", "weather_query", {"city": "北京", "date": "今天"}, 0.9),
        ("明天呢", "weather_query", {"city": "北京", "date": "明天"}, 0.85),
        ("上海呢", "weather_query", {"city": "上海", "date": "今天"}, 0.88),
    ]
    
    for query, intent, entities, confidence in conversations:
        manager.update_context(session_id, intent, entities, confidence)
        context = manager.get_context(session_id)
        print(f"查询: '{query}'")
        print(f"  意图历史: {[h['intent'] for h in context['intent_history']]}")
        print(f"  当前实体: {context['entities']}")
    
    # 测试实体解析
    current_entities = {"date": "后天"}
    resolved_city = manager.resolve_entity("city", session_id, current_entities)
    print(f"\n实体解析: city = {resolved_city}")
    
    print()


def test_result_fusion():
    """测试结果融合器"""
    print("=" * 60)
    print("测试结果融合器")
    print("=" * 60)
    
    fusion = ResultFusion()
    
    # 模拟多个策略的结果
    results = [
        MatchResult(
            intent="weather_query",
            confidence=0.8,
            matched_text="北京天气",
            strategy=IntentStrategyType.KEYWORD,
            metadata={}
        ),
        MatchResult(
            intent="weather_query",
            confidence=0.9,
            matched_text="北京天气怎么样",
            strategy=IntentStrategyType.SEMANTIC,
            metadata={}
        ),
        MatchResult(
            intent="information_search",
            confidence=0.6,
            matched_text="搜索天气",
            strategy=IntentStrategyType.KEYWORD,
            metadata={}
        )
    ]
    
    # 测试不同融合策略
    strategies = [
        FusionStrategy.WEIGHTED_AVERAGE,
        FusionStrategy.VOTING,
        FusionStrategy.MAX_CONFIDENCE,
        FusionStrategy.PRIORITY
    ]
    
    for strategy in strategies:
        result = fusion.fuse(results, strategy)
        if result:
            print(f"策略: {strategy.value}")
            print(f"  意图: {result.intent}")
            print(f"  置信度: {result.confidence:.2f}")
            print(f"  元数据: {result.metadata}")
        print()


def test_monitoring_system():
    """测试监控系统"""
    print("=" * 60)
    print("测试监控系统")
    print("=" * 60)
    
    monitoring = MonitoringSystem(enable_logging=False)
    
    # 记录一些请求
    test_requests = [
        ("你好", "general_chat", 0.95, 10.5, "keyword", True),
        ("帮我写代码", "code_generation", 0.88, 25.3, "semantic", True),
        ("搜索信息", "information_search", 0.92, 15.2, "keyword", True),
        ("北京天气", "weather_query", 0.85, 20.1, "semantic", True),
    ]
    
    for query, intent, confidence, latency, strategy, success in test_requests:
        monitoring.record_request(query, intent, confidence, latency, strategy, success)
    
    # 记录指标
    monitoring.record_metric("requests_per_second", 10.5, MetricType.GAUGE)
    monitoring.record_metric("cache_hit_rate", 0.75, MetricType.GAUGE)
    
    # 获取统计信息
    stats = monitoring.get_stats()
    print("统计信息:")
    print(f"  总请求数: {stats['total_requests']}")
    print(f"  成功请求: {stats['successful_requests']}")
    print(f"  平均延迟: {stats['avg_latency_ms']:.2f}ms")
    print(f"  成功率: {stats['success_rate']:.2%}")
    print(f"  策略分布: {stats['strategy_distribution']}")
    print(f"  意图分布: {stats['intent_distribution']}")
    
    print()


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("意图识别引擎 - 综合测试")
    print("=" * 60 + "\n")
    
    # 运行所有测试
    await test_semantic_strategy()
    test_entity_extractor()
    test_context_manager()
    test_result_fusion()
    test_monitoring_system()
    
    print("=" * 60)
    print("所有测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
