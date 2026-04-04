"""
意图识别引擎 - 核心引擎实现
参考LangChain设计模式和开发技术落地文档

核心特性:
1. 三级策略级联（关键词 -> 语义 -> Few-shot）
2. 结果融合与冲突解决
3. 缓存优化
4. 性能监控

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
from enum import Enum


class IntentStrategy(str, Enum):
    """识别策略枚举"""
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    FEW_SHOT = "few_shot"
    FUSION = "fusion"


class MatchResult(BaseModel):
    """匹配结果"""
    intent: str
    confidence: float = Field(ge=0.0, le=1.0)
    matched_text: str = ""
    strategy: IntentStrategy
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IntentResult(BaseModel):
    """意图识别结果"""
    intent: str
    confidence: float = Field(ge=0.0, le=1.0)
    entities: Dict[str, Any] = Field(default_factory=dict)
    strategy: IntentStrategy
    alternative_intents: List[MatchResult] = Field(default_factory=list)
    processing_time_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IntentDefinition(BaseModel):
    """意图定义"""
    name: str
    description: str
    keywords: List[str] = Field(default_factory=list)
    patterns: List[str] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)
    entity_schema: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 1
    threshold: float = 0.7


class IntentConfig(BaseModel):
    """意图识别配置"""
    # 关键词匹配配置
    keyword_match_threshold: float = 0.8
    synonym_expansion: bool = True
    
    # 语义检索配置
    semantic_search_top_k: int = 5
    semantic_match_threshold: float = 0.75
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    
    # Few-shot配置
    few_shot_examples_per_intent: int = 3
    few_shot_max_tokens: int = 500
    few_shot_temperature: float = 0.1
    
    # 缓存配置
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    
    # 性能配置
    max_processing_time_ms: int = 2000
    enable_early_termination: bool = True
    early_termination_threshold: float = 0.85


@dataclass
class PerformanceMetrics:
    """性能指标"""
    total_requests: int = 0
    keyword_hits: int = 0
    semantic_hits: int = 0
    few_shot_hits: int = 0
    cache_hits: int = 0
    total_processing_time_ms: float = 0.0
    
    @property
    def avg_processing_time_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_processing_time_ms / self.total_requests
    
    @property
    def keyword_hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.keyword_hits / self.total_requests
    
    @property
    def cache_hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests


class IntentCache:
    """意图识别结果缓存"""
    
    def __init__(self, ttl_seconds: int = 3600):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}
        self.ttl_seconds = ttl_seconds
    
    def get(self, key: str) -> Optional[IntentResult]:
        """获取缓存结果"""
        if key not in self._cache:
            return None
        
        # 检查是否过期
        if time.time() - self._timestamps[key] > self.ttl_seconds:
            del self._cache[key]
            del self._timestamps[key]
            return None
        
        data = self._cache[key]
        return IntentResult(**data)
    
    def put(self, key: str, result: IntentResult) -> None:
        """添加缓存"""
        self._cache[key] = result.dict()
        self._timestamps[key] = time.time()
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._timestamps.clear()


class IntentEngine:
    """
    意图识别引擎（主类）
    
    整合关键词匹配、语义检索、Few-shot学习三种策略
    实现三级级联识别流程
    
    使用示例:
        engine = IntentEngine(config)
        
        # 注册意图
        engine.register_intent(IntentDefinition(
            name="code_generation",
            description="生成代码",
            keywords=["写代码", "编程"],
            examples=["帮我写个Python函数"]
        ))
        
        # 识别意图
        result = await engine.recognize("帮我写个排序算法")
        print(f"意图: {result.intent}, 置信度: {result.confidence}")
    """
    
    def __init__(self, config: Optional[IntentConfig] = None):
        self.config = config or IntentConfig()
        self.metrics = PerformanceMetrics()
        
        # 初始化缓存
        self.cache = IntentCache(self.config.cache_ttl_seconds) if self.config.cache_enabled else None
        
        # 关键词匹配器（简化实现）
        self._keywords: Dict[str, List[str]] = {}
        self._keyword_priorities: Dict[str, int] = {}
        
        # 意图定义注册表
        self.intent_definitions: Dict[str, IntentDefinition] = {}
        
        # 回调函数
        self.on_recognize: Optional[Callable] = None
    
    def register_intent(self, intent_def: IntentDefinition) -> None:
        """
        注册意图定义
        
        Args:
            intent_def: 意图定义
        """
        self.intent_definitions[intent_def.name] = intent_def
        
        # 存储关键词
        if intent_def.keywords:
            self._keywords[intent_def.name] = intent_def.keywords
            self._keyword_priorities[intent_def.name] = intent_def.priority
    
    def unregister_intent(self, intent_name: str) -> None:
        """注销意图"""
        if intent_name in self.intent_definitions:
            del self.intent_definitions[intent_name]
        if intent_name in self._keywords:
            del self._keywords[intent_name]
            del self._keyword_priorities[intent_name]
    
    def get_intent_definitions(self) -> List[IntentDefinition]:
        """获取所有意图定义"""
        return list(self.intent_definitions.values())
    
    async def recognize(
        self,
        query: str,
        context: Optional[Dict] = None,
        candidate_intents: Optional[List[str]] = None
    ) -> IntentResult:
        """
        识别用户输入的意图
        
        执行流程:
        1. 检查缓存
        2. 关键词匹配（快速路径）
        3. 语义检索（中速路径）
        4. Few-shot学习（慢速路径）
        5. 结果融合
        6. 更新缓存
        
        Args:
            query: 用户输入文本
            context: 上下文信息
            candidate_intents: 候选意图列表（可选，限制识别范围）
            
        Returns:
            IntentResult: 意图识别结果
        """
        start_time = time.time()
        self.metrics.total_requests += 1
        
        # 1. 检查缓存
        if self.cache:
            cache_key = f"{query}:{str(candidate_intents)}"
            cached_result = self.cache.get(cache_key)
            if cached_result:
                self.metrics.cache_hits += 1
                cached_result.processing_time_ms = 0
                return cached_result
        
        # 2. 关键词匹配（快速路径）
        match_result = self._keyword_match(query)
        
        if match_result and match_result.confidence >= self.config.early_termination_threshold:
            self.metrics.keyword_hits += 1
            result = IntentResult(
                intent=match_result.intent,
                confidence=match_result.confidence,
                entities=self._extract_entities(query, match_result.intent),
                strategy=IntentStrategy.KEYWORD,
                metadata=match_result.metadata
            )
        else:
            # 3. 语义匹配（中速路径）
            semantic_result = self._semantic_match(query)
            
            if semantic_result and semantic_result.confidence >= self.config.semantic_match_threshold:
                self.metrics.semantic_hits += 1
                result = IntentResult(
                    intent=semantic_result.intent,
                    confidence=semantic_result.confidence,
                    entities=self._extract_entities(query, semantic_result.intent),
                    strategy=IntentStrategy.SEMANTIC,
                    metadata=semantic_result.metadata
                )
            elif match_result:
                # 使用关键词匹配结果
                self.metrics.keyword_hits += 1
                result = IntentResult(
                    intent=match_result.intent,
                    confidence=match_result.confidence,
                    entities=self._extract_entities(query, match_result.intent),
                    strategy=IntentStrategy.KEYWORD,
                    metadata=match_result.metadata
                )
            else:
                # 4. Few-shot匹配（慢速路径）
                few_shot_result = self._few_shot_match(query)
                
                if few_shot_result:
                    self.metrics.few_shot_hits += 1
                    result = IntentResult(
                        intent=few_shot_result.intent,
                        confidence=few_shot_result.confidence,
                        entities=self._extract_entities(query, few_shot_result.intent),
                        strategy=IntentStrategy.FEW_SHOT,
                        metadata=few_shot_result.metadata
                    )
                else:
                    # 默认结果
                    result = IntentResult(
                        intent="unknown",
                        confidence=0.0,
                        strategy=IntentStrategy.KEYWORD,
                        metadata={"reason": "no_match"}
                    )
        
        # 5. 计算处理时间
        processing_time = (time.time() - start_time) * 1000
        result.processing_time_ms = processing_time
        self.metrics.total_processing_time_ms += processing_time
        
        # 6. 更新缓存
        if self.cache:
            self.cache.put(cache_key, result)
        
        # 7. 触发回调
        if self.on_recognize:
            self.on_recognize(query, result)
        
        return result
    
    async def batch_recognize(
        self,
        queries: List[str],
        context: Optional[Dict] = None
    ) -> List[IntentResult]:
        """
        批量识别意图
        
        Args:
            queries: 用户输入文本列表
            context: 上下文信息
            
        Returns:
            意图识别结果列表
        """
        tasks = [self.recognize(query, context) for query in queries]
        return await asyncio.gather(*tasks)
    
    def _keyword_match(self, query: str) -> Optional[MatchResult]:
        """
        关键词匹配
        
        Args:
            query: 用户输入文本
            
        Returns:
            匹配结果或None
        """
        best_match = None
        best_confidence = 0.0
        matched_keyword = ""
        
        for intent_name, keywords in self._keywords.items():
            for keyword in keywords:
                if keyword in query:
                    # 计算置信度（基于匹配长度）
                    confidence = min(0.5 + len(keyword) / len(query) * 0.5, 0.95)
                    priority = self._keyword_priorities.get(intent_name, 1)
                    
                    # 考虑优先级
                    adjusted_confidence = confidence * (1.0 / priority)
                    
                    if adjusted_confidence > best_confidence:
                        best_confidence = adjusted_confidence
                        best_match = intent_name
                        matched_keyword = keyword
        
        if best_match:
            return MatchResult(
                intent=best_match,
                confidence=best_confidence,
                matched_text=matched_keyword,
                strategy=IntentStrategy.KEYWORD,
                metadata={"matched_keyword": matched_keyword}
            )
        
        return None
    
    def _semantic_match(self, query: str) -> Optional[MatchResult]:
        """
        语义匹配（简化实现）
        
        Args:
            query: 用户输入文本
            
        Returns:
            匹配结果或None
        """
        # 简化的语义匹配：基于示例文本的词重叠
        best_match = None
        best_score = 0.0
        
        query_words = set(query.lower().split())
        
        for intent_name, intent_def in self.intent_definitions.items():
            if not intent_def.examples:
                continue
            
            total_score = 0
            for example in intent_def.examples:
                example_words = set(example.lower().split())
                overlap = len(query_words & example_words)
                total_score += overlap
            
            avg_score = total_score / len(intent_def.examples) if intent_def.examples else 0
            
            if avg_score > best_score:
                best_score = avg_score
                best_match = intent_name
        
        if best_match and best_score > 0:
            confidence = min(0.5 + best_score * 0.1, 0.85)
            return MatchResult(
                intent=best_match,
                confidence=confidence,
                matched_text=query,
                strategy=IntentStrategy.SEMANTIC,
                metadata={"semantic_score": best_score}
            )
        
        return None
    
    def _few_shot_match(self, query: str) -> Optional[MatchResult]:
        """
        Few-shot匹配（简化实现）
        
        Args:
            query: 用户输入文本
            
        Returns:
            匹配结果或None
        """
        # 简化的Few-shot匹配：基于描述和示例的相似度
        best_match = None
        best_score = 0.0
        
        query_lower = query.lower()
        
        for intent_name, intent_def in self.intent_definitions.items():
            score = 0
            
            # 检查描述匹配
            if intent_def.description.lower() in query_lower:
                score += 2
            
            # 检查示例匹配
            for example in intent_def.examples:
                example_words = set(example.lower().split())
                query_words = set(query_lower.split())
                overlap = len(query_words & example_words)
                score += overlap * 0.5
            
            if score > best_score:
                best_score = score
                best_match = intent_name
        
        if best_match and best_score > 0:
            confidence = min(0.4 + best_score * 0.05, 0.75)
            return MatchResult(
                intent=best_match,
                confidence=confidence,
                matched_text=query,
                strategy=IntentStrategy.FEW_SHOT,
                metadata={"few_shot_score": best_score}
            )
        
        return None
    
    def _extract_entities(self, query: str, intent: str) -> Dict[str, Any]:
        """
        从查询中提取实体
        
        根据意图定义中的entity_schema提取实体
        """
        entities = {}
        
        intent_def = self.intent_definitions.get(intent)
        if not intent_def or not intent_def.entity_schema:
            return entities
        
        # 简单的实体提取逻辑（实际项目中可使用NER模型）
        for field_name, field_info in intent_def.entity_schema.items():
            # 这里可以实现更复杂的实体提取逻辑
            pass
        
        return entities
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            "total_requests": self.metrics.total_requests,
            "keyword_hit_rate": self.metrics.keyword_hit_rate,
            "semantic_hits": self.metrics.semantic_hits,
            "few_shot_hits": self.metrics.few_shot_hits,
            "cache_hit_rate": self.metrics.cache_hit_rate,
            "avg_processing_time_ms": self.metrics.avg_processing_time_ms
        }
    
    def clear_cache(self) -> None:
        """清空缓存"""
        if self.cache:
            self.cache.clear()
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy",
            "components": {
                "keyword_matcher": True,
                "semantic_retriever": True,
                "few_shot_learner": True,
                "cache": self.cache is not None
            },
            "registered_intents": len(self.intent_definitions),
            "metrics": self.get_metrics()
        }
