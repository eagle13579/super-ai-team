from typing import Dict, Optional, Any
from .base import Role
from .engineer import EngineerRole
import yaml
import os


class RoleFactory:
    """角色工厂"""
    
    def __init__(self):
        self.role_classes = {
            "engineer": EngineerRole,
            # 可以添加更多角色类
        }
        self.role_configs = {}
        self._load_role_configs()
    
    def _load_role_configs(self):
        """加载角色配置"""
        config_dir = os.path.join(os.path.dirname(__file__), "configs")
        if os.path.exists(config_dir):
            for file in os.listdir(config_dir):
                if file.endswith(".yaml") or file.endswith(".yml"):
                    role_name = file.split(".")[0]
                    config_path = os.path.join(config_dir, file)
                    with open(config_path, "r", encoding="utf-8") as f:
                        self.role_configs[role_name] = yaml.safe_load(f)
    
    def create_role(self, role_name: str, context: Optional[Dict[str, Any]] = None) -> Role:
        """创建角色实例"""
        if role_name in self.role_classes:
            # 使用硬编码的角色类
            return self.role_classes[role_name](context)
        elif role_name in self.role_configs:
            # 从配置文件创建角色
            config = self.role_configs[role_name]
            # 这里可以根据配置动态创建角色
            # 目前简化实现，返回工程师角色
            return EngineerRole(context)
        else:
            # 默认返回工程师角色
            return EngineerRole(context)
    
    def list_roles(self) -> list:
        """列出所有可用角色"""
        return list(set(list(self.role_classes.keys()) + list(self.role_configs.keys())))
