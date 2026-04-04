"""
意图识别引擎 - 插件注册表

负责插件的注册、发现和管理

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

import importlib
import importlib.util
import os
import sys
import pkgutil
from typing import Dict, List, Optional, Type, Any, Callable
from pathlib import Path

from interfaces.base_strategy import BaseStrategy
from interfaces.base_handler import BaseHandler


class PluginRegistry:
    """
    插件注册表
    
    负责管理所有插件的注册、发现和加载
    """
    
    def __init__(self):
        """
        初始化插件注册表
        """
        self._strategies: Dict[str, BaseStrategy] = {}
        self._handlers: Dict[str, BaseHandler] = {}
        self._plugins: Dict[str, Any] = {}
    
    def register_strategy(self, strategy: BaseStrategy) -> None:
        """
        注册识别策略
        
        Args:
            strategy: 策略实例
        """
        key = f"{strategy.strategy_type.value}:{strategy.name}"
        self._strategies[key] = strategy
        self._plugins[key] = strategy
    
    def register_handler(self, handler: BaseHandler) -> None:
        """
        注册意图处理器
        
        Args:
            handler: 处理器实例
        """
        key = handler.intent_name
        self._handlers[key] = handler
        self._plugins[key] = handler
    
    def get_strategy(self, strategy_type: str, name: str) -> Optional[BaseStrategy]:
        """
        获取策略
        
        Args:
            strategy_type: 策略类型
            name: 策略名称
            
        Returns:
            策略实例或None
        """
        key = f"{strategy_type}:{name}"
        return self._strategies.get(key)
    
    def get_handler(self, intent_name: str) -> Optional[BaseHandler]:
        """
        获取处理器
        
        Args:
            intent_name: 意图名称
            
        Returns:
            处理器实例或None
        """
        return self._handlers.get(intent_name)
    
    def get_all_strategies(self) -> List[BaseStrategy]:
        """
        获取所有策略
        
        Returns:
            策略实例列表
        """
        return list(self._strategies.values())
    
    def get_all_handlers(self) -> List[BaseHandler]:
        """
        获取所有处理器
        
        Returns:
            处理器实例列表
        """
        return list(self._handlers.values())
    
    def get_strategies_by_type(self, strategy_type: str) -> List[BaseStrategy]:
        """
        根据类型获取策略
        
        Args:
            strategy_type: 策略类型
            
        Returns:
            策略实例列表
        """
        return [s for k, s in self._strategies.items() if k.startswith(f"{strategy_type}:")]
    
    def load_plugins_from_directory(self, plugins_dir: str) -> List[str]:
        """
        从目录加载插件
        
        Args:
            plugins_dir: 插件目录
            
        Returns:
            加载的插件名称列表
        """
        loaded_plugins = []
        
        # 尝试多种路径
        possible_paths = [
            Path(plugins_dir),  # 直接路径
            Path("..") / plugins_dir,  # 向上一级
            Path(".") / plugins_dir  # 当前目录
        ]
        
        plugins_path = None
        for path in possible_paths:
            if path.exists():
                plugins_path = path
                break
        
        if not plugins_path:
            print(f"未找到插件目录: {plugins_dir}")
            return loaded_plugins
        
        print(f"正在从 {plugins_path} 加载插件...")
        
        # 遍历插件目录
        for root, dirs, files in os.walk(plugins_path):
            for file in files:
                if file.endswith(".py") and not file.startswith("_"):
                    # 计算模块路径
                    relative_path = Path(root).relative_to(plugins_path)
                    module_path = "plugins"
                    if relative_path != Path("."):
                        module_path += "." + ".".join(relative_path.parts)
                    module_path += "." + file[:-3]
                    
                    try:
                        # 导入模块
                        module = importlib.import_module(module_path)
                        
                        # 查找并注册插件
                        for name in dir(module):
                            obj = getattr(module, name)
                            if isinstance(obj, type):
                                # 注册策略
                                if issubclass(obj, BaseStrategy) and obj != BaseStrategy:
                                    try:
                                        strategy = obj()
                                        self.register_strategy(strategy)
                                        loaded_plugins.append(f"strategy:{strategy.name}")
                                        print(f"✓ 注册策略: {strategy.name}")
                                    except Exception as e:
                                        print(f"✗ 注册策略 {name} 失败: {e}")
                                # 注册处理器
                                elif issubclass(obj, BaseHandler) and obj != BaseHandler:
                                    try:
                                        handler = obj()
                                        self.register_handler(handler)
                                        loaded_plugins.append(f"handler:{handler.intent_name}")
                                        print(f"✓ 注册处理器: {handler.intent_name}")
                                    except Exception as e:
                                        print(f"✗ 注册处理器 {name} 失败: {e}")
                    except Exception as e:
                        print(f"✗ 加载模块 {module_path} 失败: {e}")
        
        return loaded_plugins
    
    def unregister_strategy(self, strategy_type: str, name: str) -> bool:
        """
        注销策略
        
        Args:
            strategy_type: 策略类型
            name: 策略名称
            
        Returns:
            是否成功注销
        """
        key = f"{strategy_type}:{name}"
        if key in self._strategies:
            del self._strategies[key]
            if key in self._plugins:
                del self._plugins[key]
            return True
        return False
    
    def unregister_handler(self, intent_name: str) -> bool:
        """
        注销处理器
        
        Args:
            intent_name: 意图名称
            
        Returns:
            是否成功注销
        """
        if intent_name in self._handlers:
            del self._handlers[intent_name]
            if intent_name in self._plugins:
                del self._plugins[intent_name]
            return True
        return False
    
    def clear(self) -> None:
        """
        清空所有插件
        """
        self._strategies.clear()
        self._handlers.clear()
        self._plugins.clear()


# 全局插件注册表实例
_registry = None


def get_registry() -> PluginRegistry:
    """
    获取全局插件注册表
    
    Returns:
        插件注册表实例
    """
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


def register_strategy(cls: Type[BaseStrategy]) -> Type[BaseStrategy]:
    """
    注册策略的装饰器
    
    在类定义时自动注册策略实例
    
    Args:
        cls: 策略类
        
    Returns:
        原始策略类
    """
    try:
        # 尝试创建实例并注册
        instance = cls()
        get_registry().register_strategy(instance)
        print(f"✓ 装饰器注册策略: {instance.name}")
    except Exception as e:
        print(f"✗ 装饰器注册策略失败: {e}")
    
    # 标记为已注册
    setattr(cls, '_is_registered', True)
    
    return cls


def register_handler(cls: Type[BaseHandler]) -> Type[BaseHandler]:
    """
    注册处理器的装饰器
    
    在类定义时自动注册处理器实例
    
    Args:
        cls: 处理器类
        
    Returns:
        原始处理器类
    """
    try:
        # 尝试创建实例并注册
        instance = cls()
        get_registry().register_handler(instance)
        print(f"✓ 装饰器注册处理器: {instance.intent_name}")
    except Exception as e:
        print(f"✗ 装饰器注册处理器失败: {e}")
    
    # 标记为已注册
    setattr(cls, '_is_registered', True)
    
    return cls


def discover_plugins(plugins_dir: str) -> List[str]:
    """
    自动发现并加载插件
    
    使用 pkgutil 扫描插件目录，自动导入所有模块
    
    Args:
        plugins_dir: 插件目录
        
    Returns:
        加载的插件名称列表
    """
    loaded_plugins = []
    registry = get_registry()
    
    # 尝试多种路径
    possible_paths = [
        Path(plugins_dir),  # 直接路径
        Path("..") / plugins_dir,  # 向上一级
        Path(".") / plugins_dir,  # 当前目录
        Path(__file__).parent.parent / plugins_dir  # 相对于当前文件
    ]
    
    plugins_path = None
    for path in possible_paths:
        if path.exists():
            plugins_path = path
            break
    
    if not plugins_path:
        print(f"未找到插件目录: {plugins_dir}")
        return loaded_plugins
    
    print(f"正在从 {plugins_path} 加载插件...")
    
    # 添加 src 目录到 Python 路径
    src_path = plugins_path.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    # 递归扫描所有子目录
    for root, dirs, files in os.walk(plugins_path):
        # 跳过 __pycache__ 目录
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py') and not file.startswith('_'):
                # 计算相对路径
                relative_path = Path(root).relative_to(plugins_path.parent)
                module_path = '.'.join(relative_path.parts)
                module_name = module_path + '.' + file[:-3]
                
                try:
                    # 导入模块
                    module = importlib.import_module(module_name)
                    print(f"✓ 加载模块: {module_name}")
                    
                    # 处理模块
                    for name in dir(module):
                        obj = getattr(module, name)
                        if isinstance(obj, type):
                            # 注册策略
                            if issubclass(obj, BaseStrategy) and obj != BaseStrategy:
                                try:
                                    strategy = obj()
                                    registry.register_strategy(strategy)
                                    loaded_plugins.append(f"strategy:{strategy.name}")
                                    print(f"✓ 注册策略: {strategy.name}")
                                except Exception as e:
                                    print(f"✗ 注册策略 {name} 失败: {e}")
                            # 注册处理器
                            elif issubclass(obj, BaseHandler) and obj != BaseHandler:
                                try:
                                    handler = obj()
                                    registry.register_handler(handler)
                                    loaded_plugins.append(f"handler:{handler.intent_name}")
                                    print(f"✓ 注册处理器: {handler.intent_name}")
                                except Exception as e:
                                    print(f"✗ 注册处理器 {name} 失败: {e}")
                except Exception as e:
                    print(f"✗ 加载模块 {module_name} 失败: {e}")
    
    return loaded_plugins


def _scan_subpackage(package_name: str, package_path: Path, loaded_plugins: List[str], registry: PluginRegistry) -> None:
    """
    扫描子包
    
    Args:
        package_name: 包名
        package_path: 包路径
        loaded_plugins: 加载的插件列表
        registry: 插件注册表
    """
    for finder, name, ispkg in pkgutil.iter_modules([str(package_path)]):
        full_name = f"{package_name}.{name}"
        if ispkg:
            # 递归扫描子包
            subpackage_path = package_path / name
            _scan_subpackage(full_name, subpackage_path, loaded_plugins, registry)
        else:
            # 加载模块
            try:
                module = importlib.import_module(full_name)
                _process_module(module, loaded_plugins, registry)
            except Exception as e:
                print(f"✗ 加载模块 {full_name} 失败: {e}")


def _process_module(module: Any, loaded_plugins: List[str], registry: PluginRegistry) -> None:
    """
    处理模块，注册插件
    
    Args:
        module: 模块对象
        loaded_plugins: 加载的插件列表
        registry: 插件注册表
    """
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type):
            # 注册策略
            if issubclass(obj, BaseStrategy) and obj != BaseStrategy:
                try:
                    strategy = obj()
                    registry.register_strategy(strategy)
                    loaded_plugins.append(f"strategy:{strategy.name}")
                    print(f"✓ 注册策略: {strategy.name}")
                except Exception as e:
                    print(f"✗ 注册策略 {name} 失败: {e}")
            # 注册处理器
            elif issubclass(obj, BaseHandler) and obj != BaseHandler:
                try:
                    handler = obj()
                    registry.register_handler(handler)
                    loaded_plugins.append(f"handler:{handler.intent_name}")
                    print(f"✓ 注册处理器: {handler.intent_name}")
                except Exception as e:
                    print(f"✗ 注册处理器 {name} 失败: {e}")
