from typing import Dict, Optional, List


class KeywordMatcher:
    """关键词匹配器"""
    
    def __init__(self):
        self.intent_keywords = {
            "search": ["搜索", "查找", "查询", "搜索一下", "查一下"],
            "code": ["代码", "编程", "写代码", "开发", "实现"],
            "chat": ["聊天", "对话", "闲聊", "交流"],
            "task": ["任务", "工作", "计划", "安排"],
            "question": ["问题", "疑问", "怎么", "如何", "为什么"]
        }
    
    def match(self, user_input: str) -> Optional[Dict]:
        """匹配关键词"""
        user_input = user_input.lower()
        
        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword in user_input:
                    return {
                        "intent_type": intent,
                        "confidence": 0.9,
                        "keywords": [keyword]
                    }
        
        return None
