"""
意图识别引擎 - 主入口

这是意图识别引擎的主入口文件，负责：
1. 初始化引擎和配置
2. 加载意图模板
3. 注册处理器
4. 运行示例演示

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

import asyncio
from typing import Optional

# 导入核心模块
from core.engine import IntentEngine, IntentConfig, IntentDefinition
from utils.config_loader import load_intent_templates, parse_intent_definition
from handlers.base_handler import (
    IntentHandlerRegistry,
    CodeGenerationHandler,
    CodeReviewHandler,
    SearchHandler,
    ChatHandler,
    FallbackHandler
)


def initialize_engine(config: Optional[IntentConfig] = None) -> IntentEngine:
    """
    初始化意图识别引擎
    
    Args:
        config: 引擎配置，使用默认配置如果未提供
        
    Returns:
        初始化后的引擎实例
    """
    # 创建引擎
    engine = IntentEngine(config)
    
    # 加载意图模板
    intent_templates = load_intent_templates()
    
    # 注册意图定义
    for intent_data in intent_templates:
        parsed = parse_intent_definition(intent_data)
        intent_def = IntentDefinition(**parsed)
        engine.register_intent(intent_def)
    
    return engine


def initialize_handlers() -> IntentHandlerRegistry:
    """
    初始化意图处理器注册表
    
    Returns:
        配置好的处理器注册表
    """
    registry = IntentHandlerRegistry()
    
    # 注册处理器
    registry.register(CodeGenerationHandler())
    registry.register(CodeReviewHandler())
    registry.register(SearchHandler())
    registry.register(ChatHandler())
    
    # 设置默认处理器
    registry.set_fallback_handler(FallbackHandler())
    
    return registry


async def process_query(
    engine: IntentEngine,
    handler_registry: IntentHandlerRegistry,
    query: str
) -> None:
    """
    处理用户查询
    
    Args:
        engine: 意图识别引擎
        handler_registry: 处理器注册表
        query: 用户输入
    """
    # 1. 识别意图
    result = await engine.recognize(query)
    
    print(f"输入: '{query}'")
    print(f"识别意图: {result.intent}")
    print(f"置信度: {result.confidence:.2f}")
    print(f"策略: {result.strategy}")
    print(f"处理时间: {result.processing_time_ms:.2f}ms")
    
    # 2. 处理意图
    handler_result = handler_registry.handle(
        result.intent,
        query,
        result.entities
    )
    
    print(f"处理结果: {handler_result.message}")
    if handler_result.data:
        print(f"数据: {handler_result.data}")
    print()


async def main():
    """
    主函数 - 演示意图识别引擎的使用
    """
    print("=" * 50)
    print("意图识别引擎 - 演示")
    print("=" * 50)
    print()
    
    # 初始化配置
    config = IntentConfig(
        keyword_match_threshold=0.8,
        semantic_match_threshold=0.75,
        cache_enabled=True,
        enable_early_termination=True,
        early_termination_threshold=0.85
    )
    
    # 初始化引擎
    print("正在初始化引擎...")
    engine = initialize_engine(config)
    print(f"已注册 {len(engine.get_intent_definitions())} 个意图定义")
    print()
    
    # 初始化处理器
    print("正在初始化处理器...")
    handler_registry = initialize_handlers()
    print(f"已注册处理器: {handler_registry.list_handlers()}")
    print()
    
    # 测试查询
    test_queries = [
        "帮我写一个Python排序函数",
        "检查一下这段代码",
        "搜索Python教程",
        "你好",
        "什么是装饰器？"
    ]
    
    print("=" * 50)
    print("开始测试")
    print("=" * 50)
    print()
    
    for query in test_queries:
        await process_query(engine, handler_registry, query)
    
    # 打印性能指标
    print("=" * 50)
    print("性能指标")
    print("=" * 50)
    metrics = engine.get_metrics()
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")
    
    # 健康检查
    print()
    print("=" * 50)
    print("健康检查")
    print("=" * 50)
    health = engine.health_check()
    print(f"状态: {health['status']}")
    print(f"注册意图数: {health['registered_intents']}")
    print(f"组件状态: {health['components']}")


if __name__ == "__main__":
    asyncio.run(main())
