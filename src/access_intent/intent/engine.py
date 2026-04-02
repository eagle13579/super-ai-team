from typing import Dict, Optional
from .keyword_matcher import KeywordMatcher
from .semantic_retriever import SemanticRetriever
from .few_shot_learner import FewShotLearner


class IntentEngine:
    """意图识别引擎"""
    
    def __init__(self):
        self.keyword_matcher = KeywordMatcher()
        self.semantic_retriever = SemanticRetriever()
        self.few_shot_learner = FewShotLearner()
    
    async def recognize(self, user_input: str, context: Optional[Dict] = None) -> Dict:
        """识别用户意图"""
        # 1. 关键词精确匹配（最快）
        if intent := self.keyword_matcher.match(user_input):
            return intent
        
        # 2. 语义向量检索（中等）
        if intent := await self.semantic_retriever.search(user_input):
            return intent
        
        # 3. LLM Few-shot识别（最准但最慢）
        return await self.few_shot_learner.classify(user_input, context)
