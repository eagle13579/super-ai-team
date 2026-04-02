from typing import Dict, Optional, Any
from dataclasses import dataclass
import asyncio


@dataclass
class ToolCall:
    """工具调用"""
    tool_name: str
    parameters: Dict[str, Any]
    timeout: int = 30
    retry: int = 3


@dataclass
class Observation:
    """观察结果"""
    success: bool
    result: Any
    error: Optional[str] = None
    recoverable: bool = True
    
    @classmethod
    def success(cls, result: Any) -> "Observation":
        return cls(success=True, result=result)
    
    @classmethod
    def error(cls, error: str, recoverable: bool = True) -> "Observation":
        return cls(success=False, result=None, error=error, recoverable=recoverable)


class ToolExecutor:
    """工具执行器"""
    
    def __init__(self, skill_registry):
        self.skill_registry = skill_registry
    
    async def execute(self, tool_call: ToolCall) -> Observation:
        """执行工具"""
        try:
            # 1. 获取技能
            skill = self.skill_registry.get_skill(tool_call.tool_name)
            if not skill:
                return Observation.error(f"Skill not found: {tool_call.tool_name}")
            
            # 2. 验证参数
            validated_params = self._validate_params(tool_call.parameters, skill.input_schema)
            if not validated_params:
                return Observation.error("Invalid parameters")
            
            # 3. 执行技能
            for attempt in range(tool_call.retry + 1):
                try:
                    # 设置超时
                    result = await asyncio.wait_for(
                        skill.execute(validated_params),
                        timeout=tool_call.timeout
                    )
                    return Observation.success(result)
                except asyncio.TimeoutError:
                    if attempt < tool_call.retry:
                        await asyncio.sleep(1)  # 等待1秒后重试
                        continue
                    return Observation.error(f"Tool execution timed out after {tool_call.timeout} seconds")
                except Exception as e:
                    if attempt < tool_call.retry:
                        await asyncio.sleep(1)  # 等待1秒后重试
                        continue
                    return Observation.error(str(e))
        except Exception as e:
            return Observation.error(str(e))
    
    def _validate_params(self, params: Dict[str, Any], schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """验证参数"""
        # 简化实现，实际应该使用JSON Schema验证
        required = schema.get("required", [])
        for field in required:
            if field not in params:
                return None
        return params
