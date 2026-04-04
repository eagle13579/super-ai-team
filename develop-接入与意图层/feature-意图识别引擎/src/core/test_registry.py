"""
测试插件注册表

验证 Registry 类、装饰器和自动发现机制

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

import sys
import os
from pathlib import Path

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from core.registry import get_registry, register_strategy, register_handler, discover_plugins
from interfaces.base_strategy import BaseStrategy, IntentStrategyType, MatchResult
from interfaces.base_handler import BaseHandler, HandlerResult


# 测试装饰器
@register_strategy
class TestStrategy(BaseStrategy):
    """测试策略"""
    
    @property
    def strategy_type(self) -> IntentStrategyType:
        return IntentStrategyType.KEYWORD
    
    @property
    def name(self) -> str:
        return "test_strategy"
    
    @property
    def priority(self) -> int:
        return 1
    
    async def recognize(self, query: str, context=None):
        return self.recognize_sync(query, context)
    
    def recognize_sync(self, query: str, context=None):
        if "test" in query:
            return MatchResult(
                intent="test_intent",
                confidence=0.9,
                matched_text=query,
                strategy=self.strategy_type,
                metadata={}
            )
        return None


@register_handler
class TestHandler(BaseHandler):
    """测试处理器"""
    
    @property
    def intent_name(self) -> str:
        return "test_intent"
    
    async def handle(self, query: str, entities=None, context=None):
        return self.handle_sync(query, entities, context)
    
    def handle_sync(self, query: str, entities=None, context=None):
        return HandlerResult(
            success=True,
            message="Test handler executed",
            data={"query": query},
            intent=self.intent_name
        )


def test_registry():
    """
    测试插件注册表
    """
    print("=" * 60)
    print("测试插件注册表")
    print("=" * 60)
    print()
    
    # 测试 1: 装饰器注册
    print("1. 测试装饰器注册")
    registry = get_registry()
    strategies = registry.get_all_strategies()
    handlers = registry.get_all_handlers()
    print(f"   注册的策略数量: {len(strategies)}")
    print(f"   注册的处理器数量: {len(handlers)}")
    for strategy in strategies:
        print(f"   - 策略: {strategy.name}")
    for handler in handlers:
        print(f"   - 处理器: {handler.intent_name}")
    print()
    
    # 测试 2: 自动发现
    print("2. 测试自动发现")
    # 使用相对于当前文件的路径
    plugins_path = src_path / "plugins"
    loaded_plugins = discover_plugins(str(plugins_path))
    print(f"   自动发现的插件数量: {len(loaded_plugins)}")
    for plugin in loaded_plugins:
        print(f"   - {plugin}")
    print()
    
    # 测试 3: 获取策略和处理器
    print("3. 测试获取策略和处理器")
    strategies = registry.get_all_strategies()
    handlers = registry.get_all_handlers()
    print(f"   策略数量: {len(strategies)}")
    print(f"   处理器数量: {len(handlers)}")
    
    # 测试 4: 按类型获取策略
    print("4. 测试按类型获取策略")
    keyword_strategies = registry.get_strategies_by_type("keyword")
    print(f"   关键词策略数量: {len(keyword_strategies)}")
    for strategy in keyword_strategies:
        print(f"   - {strategy.name}")
    print()
    
    # 测试 5: 注销插件
    print("5. 测试注销插件")
    if strategies:
        strategy = strategies[0]
        print(f"   注销策略: {strategy.name}")
        registry.unregister_strategy(strategy.strategy_type.value, strategy.name)
        print(f"   注销后策略数量: {len(registry.get_all_strategies())}")
    
    if handlers:
        handler = handlers[0]
        print(f"   注销处理器: {handler.intent_name}")
        registry.unregister_handler(handler.intent_name)
        print(f"   注销后处理器数量: {len(registry.get_all_handlers())}")
    print()
    
    # 测试 6: 清空注册表
    print("6. 测试清空注册表")
    registry.clear()
    print(f"   清空后策略数量: {len(registry.get_all_strategies())}")
    print(f"   清空后处理器数量: {len(registry.get_all_handlers())}")
    print()
    
    print("=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_registry()
