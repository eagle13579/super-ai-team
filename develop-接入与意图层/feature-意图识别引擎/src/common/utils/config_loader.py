"""
意图识别引擎 - 配置加载器

提供YAML配置文件加载功能，包括：
- 意图模板加载
- 配置文件解析
- 配置验证

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

import os
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path


class ConfigLoader:
    """
    配置加载器
    
    负责加载和管理YAML配置文件
    
    使用示例:
        loader = ConfigLoader("templates/intent")
        config = loader.load("code_intent.yaml")
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        初始化配置加载器
        
        Args:
            base_path: 配置文件基础路径，默认为templates/intent目录
        """
        if base_path is None:
            # 自动推断路径
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent.parent
            base_path = project_root / "templates" / "intent"
        
        self.base_path = Path(base_path)
        self._cache: Dict[str, Any] = {}
    
    def load(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        加载单个YAML配置文件
        
        Args:
            filename: 配置文件名
            
        Returns:
            配置字典或None（如果文件不存在）
        """
        # 检查缓存
        if filename in self._cache:
            return self._cache[filename]
        
        file_path = self.base_path / filename
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self._cache[filename] = config
                return config
        except yaml.YAMLError as e:
            print(f"Error loading {filename}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error loading {filename}: {e}")
            return None
    
    def load_all(self) -> Dict[str, Dict[str, Any]]:
        """
        加载所有YAML配置文件
        
        Returns:
            文件名到配置的字典映射
        """
        configs = {}
        
        if not self.base_path.exists():
            return configs
        
        for file_path in self.base_path.glob("*.yaml"):
            filename = file_path.name
            config = self.load(filename)
            if config:
                configs[filename] = config
        
        return configs
    
    def clear_cache(self) -> None:
        """清空配置缓存"""
        self._cache.clear()
    
    def reload(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        重新加载配置文件（绕过缓存）
        
        Args:
            filename: 配置文件名
            
        Returns:
            配置字典或None
        """
        if filename in self._cache:
            del self._cache[filename]
        return self.load(filename)


def load_yaml_config(file_path: str) -> Optional[Dict[str, Any]]:
    """
    加载YAML配置文件（独立函数）
    
    Args:
        file_path: 配置文件完整路径
        
    Returns:
        配置字典或None
        
    使用示例:
        config = load_yaml_config("templates/intent/code_intent.yaml")
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Config file not found: {file_path}")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        return None
    except Exception as e:
        print(f"Error loading config: {e}")
        return None


def load_intent_templates(templates_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    加载所有意图模板
    
    Args:
        templates_dir: 模板目录路径，默认为项目templates/intent目录
        
    Returns:
        意图定义列表
        
    使用示例:
        intents = load_intent_templates()
        for intent in intents:
            print(f"Intent: {intent['name']}")
    """
    if templates_dir is None:
        # 自动推断路径 - 从utils目录向上两级到feature目录，再找到templates
        current_file = Path(__file__).resolve()
        # src/utils/config_loader.py -> src/ -> feature-意图识别引擎/ -> templates/intent/
        feature_dir = current_file.parent.parent.parent
        templates_dir = feature_dir / "templates" / "intent"
    
    templates_path = Path(templates_dir)
    
    if not templates_path.exists():
        print(f"模板目录不存在: {templates_path}")
        return []
    
    all_intents = []
    
    for file_path in templates_path.glob("*.yaml"):
        config = load_yaml_config(str(file_path))
        if config and "intents" in config:
            all_intents.extend(config["intents"])
    
    return all_intents


def parse_intent_definition(intent_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    解析意图定义数据
    
    将YAML中的意图定义转换为标准格式
    
    Args:
        intent_data: 意图定义原始数据
        
    Returns:
        标准化的意图定义字典
    """
    return {
        "name": intent_data.get("name", ""),
        "description": intent_data.get("description", ""),
        "keywords": intent_data.get("keywords", []),
        "patterns": intent_data.get("patterns", []),
        "examples": intent_data.get("examples", []),
        "entity_schema": intent_data.get("entity_schema", {}),
        "priority": intent_data.get("priority", 1),
        "threshold": intent_data.get("threshold", 0.7)
    }


def get_template_path(filename: Optional[str] = None) -> Path:
    """
    获取模板文件路径
    
    Args:
        filename: 可选的文件名
        
    Returns:
        模板文件或目录的Path对象
    """
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent
    template_dir = project_root / "templates" / "intent"
    
    if filename:
        return template_dir / filename
    return template_dir
