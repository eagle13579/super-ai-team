from typing import Dict, Optional


class TaskRouter:
    """任务路由器"""
    
    def __init__(self):
        # 意图到角色的映射
        self.intent_role_map = {
            "search": "search_agent",
            "code": "engineer",
            "chat": "chat_agent",
            "task": "planner",
            "question": "knowledge_agent"
        }
    
    def route(self, intent: Dict, context: Optional[Dict] = None) -> Dict:
        """根据意图和上下文路由任务"""
        intent_type = intent.get("intent_type", "chat")
        confidence = intent.get("confidence", 0.0)
        
        # 根据意图类型选择角色
        role = self.intent_role_map.get(intent_type, "chat_agent")
        
        # 构建路由结果
        routing_result = {
            "intent_type": intent_type,
            "confidence": confidence,
            "assigned_role": role,
            "route_time": "2026-04-01T12:00:00Z"  # 实际应该使用当前时间
        }
        
        # 如果上下文中有特殊信息，可以根据上下文调整路由
        if context:
            user_preferences = context.get("user_preferences", {})
            preferred_role = user_preferences.get("preferred_role")
            if preferred_role:
                routing_result["assigned_role"] = preferred_role
                routing_result["reason"] = "User preference"
        
        return routing_result
