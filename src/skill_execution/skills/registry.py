from typing import Dict, Optional, List
from .base import Skill
from .web_search import WebSearchSkill
from .file_operations import FileOperationsSkill
import json
import os


class SkillRegistry:
    """技能注册中心"""
    
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self._load_skills()
    
    def _load_skills(self):
        """加载技能"""
        # 注册内置技能
        self.register_skill(WebSearchSkill())
        self.register_skill(FileOperationsSkill())
        
        # 加载自定义技能
        self._load_custom_skills()
    
    def _load_custom_skills(self):
        """加载自定义技能"""
        skills_dir = os.path.join(os.path.dirname(__file__), "custom")
        if os.path.exists(skills_dir):
            for file in os.listdir(skills_dir):
                if file.endswith(".py") and not file.startswith("_"):
                    try:
                        # 动态导入技能
                        module_name = f"skills.custom.{file[:-3]}"
                        module = __import__(module_name, fromlist=["*"])
                        # 查找Skill子类
                        for name, obj in module.__dict__.items():
                            if isinstance(obj, type) and issubclass(obj, Skill) and obj != Skill:
                                skill_instance = obj()
                                self.register_skill(skill_instance)
                    except Exception as e:
                        print(f"Failed to load custom skill {file}: {e}")
    
    def register_skill(self, skill: Skill):
        """注册技能"""
        self.skills[skill.name] = skill
    
    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """获取技能"""
        return self.skills.get(skill_name)
    
    def list_skills(self) -> List[str]:
        """列出所有技能"""
        return list(self.skills.keys())
    
    def get_skill_info(self, skill_name: str) -> Optional[Dict]:
        """获取技能信息"""
        skill = self.get_skill(skill_name)
        if skill:
            return {
                "name": skill.name,
                "version": skill.version,
                "description": skill.description,
                "input_schema": skill.input_schema,
                "output_schema": skill.output_schema,
                "timeout": skill.timeout,
                "retry": skill.retry
            }
        return None
