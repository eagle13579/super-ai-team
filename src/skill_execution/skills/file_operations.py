from .base import Skill
from typing import Dict, Any
import os


class FileOperationsSkill(Skill):
    """文件操作技能"""
    
    def __init__(self):
        super().__init__(
            name="file_operations",
            version="1.0.0",
            description="执行文件读写操作",
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["read", "write"],
                        "description": "操作类型"
                    },
                    "path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "content": {
                        "type": "string",
                        "description": "文件内容（仅写操作需要）"
                    }
                },
                "required": ["operation", "path"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "status": { "type": "string" },
                    "content": { "type": "string" },
                    "size": { "type": "integer" }
                }
            }
        )
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行文件操作"""
        operation = parameters.get("operation", "read")
        path = parameters.get("path", "")
        content = parameters.get("content", "")
        
        if operation == "read":
            # 读取文件
            try:
                with open(path, "r", encoding="utf-8") as f:
                    file_content = f.read()
                size = os.path.getsize(path)
                return {
                    "status": "success",
                    "content": file_content,
                    "size": size
                }
            except Exception as e:
                return {
                    "status": "error",
                    "content": str(e),
                    "size": 0
                }
        elif operation == "write":
            # 写入文件
            try:
                # 确保目录存在
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                size = os.path.getsize(path)
                return {
                    "status": "success",
                    "content": "File written successfully",
                    "size": size
                }
            except Exception as e:
                return {
                    "status": "error",
                    "content": str(e),
                    "size": 0
                }
        else:
            return {
                "status": "error",
                "content": "Invalid operation",
                "size": 0
            }
