"""
意图识别引擎 - 处理器模块

提供意图处理的基础类和示例实现，包括：
- 基础意图处理器
- 具体意图处理器示例
- 处理器注册与管理

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

from .base_handler import BaseIntentHandler, IntentHandlerRegistry, CodeGenerationHandler

__all__ = ["BaseIntentHandler", "IntentHandlerRegistry", "CodeGenerationHandler"]
