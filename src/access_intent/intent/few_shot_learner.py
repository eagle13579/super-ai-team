from typing import Dict, Optional, List


class FewShotLearner:
    """Few-shot学习器"""
    
    def __init__(self):
        # 示例样本
        self.examples = {
            "search": [
                "帮我搜索一下Python的列表推导式",
                "查找最新的人工智能论文",
                "查询北京的天气"
            ],
            "code": [
                "写一个Python函数来计算斐波那契数列",
                "帮我修改这个JavaScript代码",
                "实现一个简单的神经网络"
            ],
            "chat": [
                "你好，今天过得怎么样？",
                "聊聊最近的电影",
                "讲个笑话吧"
            ],
            "task": [
                "帮我制定一周的学习计划",
                "安排明天的会议",
                "创建一个项目进度表"
            ],
            "question": [
                "为什么天空是蓝色的？",
                "如何提高学习效率？",
                "什么是机器学习？"
            ]
        }
    
    async def classify(self, user_input: str, context: Optional[Dict] = None) -> Dict:
        """基于Few-shot学习进行意图分类"""
        # 这里简化实现，实际应该使用LLM进行分类
        # 这里使用简单的规则匹配作为示例
        
        # 计算每个意图的匹配分数
        scores = {}
        for intent, examples in self.examples.items():
            score = 0
            for example in examples:
                # 简单的词重叠计算
                input_words = set(user_input.lower().split())
                example_words = set(example.lower().split())
                overlap = len(input_words.intersection(example_words))
                score += overlap
            scores[intent] = score
        
        # 找到得分最高的意图
        max_intent = max(scores, key=scores.get)
        max_score = scores[max_intent]
        
        # 计算置信度
        total_score = sum(scores.values())
        confidence = max_score / total_score if total_score > 0 else 0.5
        
        return {
            "intent_type": max_intent,
            "confidence": confidence,
            "scores": scores
        }
