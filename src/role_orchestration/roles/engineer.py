from .base import Role
from typing import Dict


class EngineerRole(Role):
    """工程师角色"""
    
    def __init__(self, context=None):
        super().__init__(
            name="engineer",
            profile={
                "style": "严谨、专业、注重细节",
                "experience": "5年软件开发经验",
                "expertise": "Python、JavaScript、系统架构"
            },
            goals=[
                "编写高质量的代码",
                "解决技术问题",
                "优化系统性能"
            ],
            rules=[
                "代码必须通过测试",
                "遵循代码规范",
                "考虑系统可扩展性"
            ],
            skills=[
                "coding",
                "debugging",
                "performance_optimization",
                "system_design"
            ],
            workflows=[
                "需求分析",
                "设计方案",
                "编码实现",
                "测试验证",
                "部署上线"
            ],
            context=context
        )
    
    async def execute(self, task: Dict) -> Dict:
        """执行任务"""
        task_type = task.get("type", "coding")
        task_content = task.get("content", "")
        
        # 模拟执行任务
        if task_type == "coding":
            result = {
                "status": "completed",
                "output": f"已完成代码编写: {task_content}",
                "details": {
                    "language": "Python",
                    "quality": "high",
                    "tested": True
                }
            }
        elif task_type == "debugging":
            result = {
                "status": "completed",
                "output": f"已修复bug: {task_content}",
                "details": {
                    "issue": "bug fixed",
                    "tested": True
                }
            }
        else:
            result = {
                "status": "completed",
                "output": f"已完成任务: {task_content}",
                "details": {}
            }
        
        return result
