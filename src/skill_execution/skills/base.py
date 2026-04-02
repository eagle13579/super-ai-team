from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Optional, Any


@dataclass
class Skill:
    """技能基础类"""
    name: str
    version: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    timeout: int = 30
    retry: int = 3
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行技能"""
        pass
