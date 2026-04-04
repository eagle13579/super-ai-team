"""
意图识别引擎 - 模板解析器

负责解析 @templates/intent/ 下的意图模板文件

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

import os
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path


class TemplateParser:
    """
    模板解析器
    
    负责解析意图模板文件
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        初始化模板解析器
        
        Args:
            templates_dir: 模板目录路径，默认为 templates/intent
        """
        if templates_dir is None:
            # 自动推断模板目录路径
            current_file = Path(__file__).resolve()
            feature_dir = current_file.parent.parent.parent
            templates_dir = feature_dir / "templates" / "intent"
        
        self.templates_dir = Path(templates_dir)
        self._templates: Dict[str, Any] = {}
        self._loaded = False
    
    def load_templates(self) -> Dict[str, Any]:
        """
        加载所有模板文件
        
        Returns:
            模板字典，键为文件名，值为模板内容
        """
        if not self.templates_dir.exists():
            raise FileNotFoundError(f"模板目录不存在: {self.templates_dir}")
        
        templates = {}
        
        # 查找所有 YAML 文件
        for file_path in self.templates_dir.glob("*.yaml"):
            filename = file_path.name
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    template = yaml.safe_load(f)
                    templates[filename] = template
            except yaml.YAMLError as e:
                print(f"解析模板文件 {filename} 错误: {e}")
            except Exception as e:
                print(f"加载模板文件 {filename} 失败: {e}")
        
        self._templates = templates
        self._loaded = True
        return templates
    
    def get_intents(self) -> List[Dict[str, Any]]:
        """
        获取所有意图定义
        
        Returns:
            意图定义列表
        """
        if not self._loaded:
            self.load_templates()
        
        all_intents = []
        
        for template in self._templates.values():
            if isinstance(template, dict) and "intents" in template:
                intents = template["intents"]
                if isinstance(intents, list):
                    all_intents.extend(intents)
        
        return all_intents
    
    def get_intent_by_name(self, intent_name: str) -> Optional[Dict[str, Any]]:
        """
        根据意图名称获取意图定义
        
        Args:
            intent_name: 意图名称
            
        Returns:
            意图定义或None
        """
        intents = self.get_intents()
        for intent in intents:
            if isinstance(intent, dict) and intent.get("name") == intent_name:
                return intent
        return None
    
    def get_templates(self) -> Dict[str, Any]:
        """
        获取所有模板
        
        Returns:
            模板字典
        """
        if not self._loaded:
            self.load_templates()
        return self._templates
    
    def reload(self) -> Dict[str, Any]:
        """
        重新加载模板
        
        Returns:
            重新加载后的模板字典
        """
        self._loaded = False
        return self.load_templates()


# 全局模板解析器实例
_template_parser = None


def get_template_parser() -> TemplateParser:
    """
    获取全局模板解析器
    
    Returns:
        模板解析器实例
    """
    global _template_parser
    if _template_parser is None:
        _template_parser = TemplateParser()
        _template_parser.load_templates()
    return _template_parser


def get_all_intents() -> List[Dict[str, Any]]:
    """
    获取所有意图定义（便捷函数）
    
    Returns:
        意图定义列表
    """
    return get_template_parser().get_intents()


def get_intent(intent_name: str) -> Optional[Dict[str, Any]]:
    """
    根据名称获取意图定义（便捷函数）
    
    Args:
        intent_name: 意图名称
        
    Returns:
        意图定义或None
    """
    return get_template_parser().get_intent_by_name(intent_name)
