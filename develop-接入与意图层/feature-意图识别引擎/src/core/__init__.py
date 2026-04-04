"""
意图识别引擎 - 核心模块

提供意图识别的核心引擎实现，包括：
- 多策略级联识别
- 结果融合与冲突解决
- 性能监控与缓存优化

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

from .engine import IntentEngine, IntentConfig, PerformanceMetrics

__all__ = ["IntentEngine", "IntentConfig", "PerformanceMetrics"]
