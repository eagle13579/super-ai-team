"""
意图识别引擎 - 语义检索策略

基于向量相似度的语义匹配策略

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from interfaces.base_strategy import BaseStrategy, MatchResult, IntentStrategyType
from common.template_parser import get_all_intents, get_intent


class SemanticStrategy(BaseStrategy):
    """
    语义检索策略
    
    基于向量相似度的语义匹配策略
    使用 TF-IDF 进行文本向量化，支持多语言
    """
    
    @property
    def strategy_type(self) -> IntentStrategyType:
        """策略类型"""
        return IntentStrategyType.SEMANTIC
    
    @property
    def name(self) -> str:
        """策略名称"""
        return "semantic"
    
    @property
    def priority(self) -> int:
        """策略优先级"""
        return 2
    
    def __init__(self):
        """初始化语义检索策略"""
        super().__init__()
        self.vectorizer = TfidfVectorizer(
            analyzer='char_wb',  # 字符级 n-gram，适合中文
            ngram_range=(2, 4),  # 2-4 个字符的 n-gram
            max_features=5000,   # 最大特征数
            min_df=1,           # 最小文档频率
            max_df=0.95         # 最大文档频率
        )
        self.intent_vectors = None
        self.intent_names = []
        self.intent_examples = []
        self._initialized = False
        self._similarity_threshold = 0.3
    
    def initialize(self, config: Dict[str, Any] = None) -> None:
        """
        初始化策略
        
        Args:
            config: 策略配置
        """
        if config:
            self._similarity_threshold = config.get('similarity_threshold', 0.3)
        
        self._load_intent_data()
        self._train_vectorizer()
        self._initialized = True
    
    def _load_intent_data(self) -> None:
        """加载意图数据"""
        intents = get_all_intents()
        self.intent_names = []
        self.intent_examples = []
        
        for intent in intents:
            intent_name = intent.get("name")
            examples = intent.get("examples", [])
            
            if intent_name and examples:
                self.intent_names.append(intent_name)
                self.intent_examples.append(examples)
    
    def _train_vectorizer(self) -> None:
        """训练向量器"""
        if not self.intent_examples:
            return
        
        # 准备训练数据：每个意图的所有示例
        all_examples = []
        for examples in self.intent_examples:
            # 将同一意图的所有示例合并为一个文档
            combined = ' '.join(examples)
            all_examples.append(combined)
        
        # 训练 TF-IDF 向量器
        self.intent_vectors = self.vectorizer.fit_transform(all_examples)
    
    async def recognize(self, query: str, context: Optional[Dict[str, Any]] = None) -> Optional[MatchResult]:
        """
        异步识别意图
        
        Args:
            query: 用户输入文本
            context: 上下文信息
            
        Returns:
            匹配结果或None
        """
        # 委托给同步方法
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.recognize_sync, query, context)
    
    def recognize_sync(self, query: str, context: Optional[Dict[str, Any]] = None) -> Optional[MatchResult]:
        """
        同步识别意图
        
        Args:
            query: 用户输入文本
            context: 上下文信息
            
        Returns:
            匹配结果或None
        """
        if not self._initialized:
            self.initialize()
        
        if not query or not self.intent_names:
            return None
        
        # 将查询转换为向量
        query_vector = self.vectorizer.transform([query])
        
        # 计算与所有意图的相似度
        similarities = cosine_similarity(query_vector, self.intent_vectors)[0]
        
        # 找到最相似的意图
        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]
        
        # 如果相似度超过阈值
        if best_score >= self._similarity_threshold:
            intent_name = self.intent_names[best_idx]
            
            # 计算置信度（归一化到 0-1）
            confidence = min(best_score * 1.2, 0.95)  # 适当放大，但不超过 0.95
            
            return MatchResult(
                intent=intent_name,
                confidence=confidence,
                matched_text=query,
                strategy=self.strategy_type,
                metadata={
                    "semantic_score": float(best_score),
                    "all_scores": {
                        name: float(score) 
                        for name, score in zip(self.intent_names, similarities)
                    }
                }
            )
        
        return None
    
    def get_similarity_scores(self, query: str) -> List[Tuple[str, float]]:
        """
        获取与所有意图的相似度分数
        
        Args:
            query: 用户输入文本
            
        Returns:
            意图名称和相似度分数的列表
        """
        if not self._initialized:
            self.initialize()
        
        if not query or not self.intent_names:
            return []
        
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.intent_vectors)[0]
        
        return [
            (name, float(score)) 
            for name, score in zip(self.intent_names, similarities)
        ]
    
    def shutdown(self) -> None:
        """关闭策略"""
        self.intent_vectors = None
        self.intent_names = []
        self.intent_examples = []
        self._initialized = False
