from typing import Dict, List, Optional
import json
import os


class ToolHarness:
    """工具装配器"""
    
    def __init__(self):
        self.tools: Dict[str, Dict] = {}
        self._load_tools()
    
    def _load_tools(self):
        """加载工具定义"""
        # 加载内置工具
        self._load_builtin_tools()
        
        # 加载自定义工具
        self._load_custom_tools()
    
    def _load_builtin_tools(self):
        """加载内置工具"""
        # 定义内置工具
        builtin_tools = [
            {
                "name": "read_file",
                "description": "读取指定路径的文件内容",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "文件路径"
                        }
                    },
                    "required": ["path"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "文件内容"
                        },
                        "size": {
                            "type": "integer",
                            "description": "文件大小（字节）"
                        }
                    }
                },
                "safety_level": "safe",
                "timeout": 10
            },
            {
                "name": "write_file",
                "description": "向指定路径写入文件内容",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "文件路径"
                        },
                        "content": {
                            "type": "string",
                            "description": "文件内容"
                        }
                    },
                    "required": ["path", "content"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "操作状态"
                        },
                        "size": {
                            "type": "integer",
                            "description": "文件大小（字节）"
                        }
                    }
                },
                "safety_level": "medium",
                "timeout": 10
            }
        ]
        
        for tool in builtin_tools:
            self.tools[tool["name"]] = tool
    
    def _load_custom_tools(self):
        """加载自定义工具"""
        tools_dir = os.path.join(os.path.dirname(__file__), "definitions")
        if os.path.exists(tools_dir):
            for file in os.listdir(tools_dir):
                if file.endswith(".json"):
                    try:
                        tool_path = os.path.join(tools_dir, file)
                        with open(tool_path, "r", encoding="utf-8") as f:
                            tool = json.load(f)
                            self.tools[tool["name"]] = tool
                    except Exception as e:
                        print(f"Failed to load custom tool {file}: {e}")
    
    def get_tool(self, tool_name: str) -> Optional[Dict]:
        """获取工具定义"""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """列出所有工具"""
        return list(self.tools.keys())
    
    def register_tool(self, tool: Dict):
        """注册工具"""
        self.tools[tool["name"]] = tool
