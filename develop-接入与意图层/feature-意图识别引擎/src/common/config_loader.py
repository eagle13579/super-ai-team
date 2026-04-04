"""
意图识别引擎 - 配置加载器

负责加载和管理配置文件

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigLoader:
    """
    配置加载器
    
    负责加载YAML配置文件并提供配置访问接口
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径，默认为 config/settings.yaml
        """
        if config_path is None:
            # 自动推断配置文件路径
            current_file = Path(__file__).resolve()
            feature_dir = current_file.parent.parent.parent
            config_path = feature_dir / "config" / "settings.yaml"
        
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._loaded = False
    
    def load(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            配置字典
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
                self._loaded = True
                return self._config
        except yaml.YAMLError as e:
            raise Exception(f"配置文件解析错误: {e}")
        except Exception as e:
            raise Exception(f"加载配置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的路径
            default: 默认值
            
        Returns:
            配置值
        """
        if not self._loaded:
            self.load()
        
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置
        
        Returns:
            完整配置字典
        """
        if not self._loaded:
            self.load()
        return self._config
    
    def reload(self) -> Dict[str, Any]:
        """
        重新加载配置
        
        Returns:
            重新加载后的配置字典
        """
        self._loaded = False
        return self.load()


# 全局配置加载器实例
_config_loader = None


def get_config() -> ConfigLoader:
    """
    获取全局配置加载器
    
    Returns:
        配置加载器实例
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
        _config_loader.load()
    return _config_loader


def get_setting(key: str, default: Any = None) -> Any:
    """
    获取配置值（便捷函数）
    
    Args:
        key: 配置键
        default: 默认值
        
    Returns:
        配置值
    """
    return get_config().get(key, default)
