from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class Role:
    """角色基础类"""
    name: str
    profile: Dict[str, str]
    goals: List[str]
    rules: List[str]
    skills: List[str]
    workflows: List[str]
    context: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    @abstractmethod
    async def execute(self, task: Dict) -> Dict:
        """执行任务"""
        pass
    
    async def get_context(self) -> Dict[str, Any]:
        """获取角色上下文"""
        return self.context
    
    async def set_context(self, context: Dict[str, Any]):
        """设置角色上下文"""
        self.context = context
