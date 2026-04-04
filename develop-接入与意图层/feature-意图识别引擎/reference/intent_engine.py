"""
意图识别引擎 - 主类实现
参考LangChain设计模式和开发技术落地文档

核心特性:
1. 三级策略级联（关键词 -> 语义 -> Few-shot）
2. 结果融合与冲突解决
3. 缓存优化
4. 性能监控

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-02
"""

import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
from enum import Enum

# 导入参考模块
from classification_chain import (
    IntentChain, MultiIntentChain, LLMIntentChain,
    IntentResult, MatchResult, IntentStrategy, IntentDefinition
)
from keyword_matcher import KeywordMatcher
from semantic_retriever import SemanticRetriever


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
    
    def cleanup_expired(self) -> int:
        """清理过期缓存，返回清理数量"""
        current_time = time.time()
        expired_keys = [
            key for key, ts in self._timestamps.items()
            if current_time - ts > self.ttl_seconds
        ]
        for key in expired_keys:
            del self._cache[key]
            del self._timestamps[key]
        return len(expired_keys)


class KeywordIntentChain(IntentChain):
    """关键词匹配链"""
    
    def __init__(self, config: IntentConfig):
        super().__init__("keyword_matcher", priority=1)
        self.config = config
        self.matcher = KeywordMatcher()
        self._init_default_keywords()
    
    def _init_default_keywords(self):
        """初始化默认关键词"""
        default_keywords = {
            "code_generation": ["写代码", "编程", "实现", "开发", "创建"],
            "code_review": ["review", "检查", "优化", "改进", "审查"],
            "search": ["搜索", "查找", "查询", "检索"],
            "question": ["什么是", "怎么", "为什么", "如何"],
            "chat": ["你好", "谢谢", "再见", "闲聊"]
        }
        
        for intent, keywords in default_keywords.items():
            for keyword in keywords:
                self.matcher.add_keyword(keyword, intent, priority=1)
    
    def add_keyword(self, keyword: str, intent: str, priority: int = 1):
        """添加关键词"""
        self.matcher.add_keyword(keyword, intent, priority)
    
    def _recognize(self, query: str, context: Optional[Dict] = None) -> Optional[MatchResult]:
        result = self.matcher.match(query, expand_synonyms=self.config.synonym_expansion)
        if result:
            return MatchResult(
                intent=result["intent"],
                confidence=result["confidence"],
                matched_text=result.get("matched_keyword", ""),
                strategy=IntentStrategy.KEYWORD,
                metadata=result
            )
        return None


class SemanticIntentChain(IntentChain):
    """语义检索链"""
    
    def __init__(self, config: IntentConfig):
        super().__init__("semantic_retriever", priority=2)
        self.config = config
        self.retriever = SemanticRetriever(
            cache_enabled=config.cache_enabled,
            similarity_threshold=config.semantic_match_threshold
        )
    
    def build_index(self, intent_examples: Dict[str, List[str]]):
        """构建语义索引"""
        self.retriever.build_index(intent_examples)
    
    def _recognize(self, query: str, context: Optional[Dict] = None) -> Optional[MatchResult]:
        result = self.retriever.search(
            query,
            top_k=self.config.semantic_search_top_k
        )
        if result:
            return MatchResult(
                intent=result["intent"],
                confidence=result["confidence"],
                matched_text=result.get("matched_text", ""),
                strategy=IntentStrategy.SEMANTIC,
                metadata=result
            )
        return None


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
        
        # 初始化识别链
        self.keyword_chain = KeywordIntentChain(self.config)
        self.semantic_chain = SemanticIntentChain(self.config)
        self.few_shot_chain = LLMIntentChain(name="few_shot_classifier")
        
        # 初始化多链融合
        self.multi_chain = MultiIntentChain(
            name="intent_fusion",
            enable_early_termination=self.config.enable_early_termination
        )
        self.multi_chain.confidence_threshold = self.config.early_termination_threshold
        
        # 添加识别链（按优先级）
        self.multi_chain.add_chain(self.keyword_chain)
        self.multi_chain.add_chain(self.semantic_chain)
        self.multi_chain.add_chain(self.few_shot_chain)
        
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
        
        # 添加到关键词匹配器
        for keyword in intent_def.keywords:
            self.keyword_chain.add_keyword(keyword, intent_def.name, intent_def.priority)
        
        # 添加到Few-shot学习器
        if intent_def.examples:
            self.few_shot_chain.add_intent(
                intent_def.name,
                intent_def.description,
                intent_def.examples
            )
        
        # 添加到语义检索器
        if intent_def.examples:
            self.semantic_chain.build_index({intent_def.name: intent_def.examples})
    
    def unregister_intent(self, intent_name: str) -> None:
        """注销意图"""
        if intent_name in self.intent_definitions:
            del self.intent_definitions[intent_name]
    
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
        
        # 2. 执行三级识别
        match_result = await self.multi_chain.arecognize(query, context)
        
        # 3. 构建结果
        if match_result:
            result = IntentResult(
                intent=match_result.intent,
                confidence=match_result.confidence,
                entities=self._extract_entities(query, match_result.intent),
                strategy=match_result.strategy,
                metadata=match_result.metadata
            )
            
            # 更新指标
            if match_result.strategy == IntentStrategy.KEYWORD:
                self.metrics.keyword_hits += 1
            elif match_result.strategy == IntentStrategy.SEMANTIC:
                self.metrics.semantic_hits += 1
            elif match_result.strategy == IntentStrategy.FEW_SHOT:
                self.metrics.few_shot_hits += 1
        else:
            # 默认结果
            result = IntentResult(
                intent="unknown",
                confidence=0.0,
                strategy=IntentStrategy.KEYWORD,
                metadata={"reason": "no_match"}
            )
        
        # 4. 计算处理时间
        processing_time = (time.time() - start_time) * 1000
        result.processing_time_ms = processing_time
        self.metrics.total_processing_time_ms += processing_time
        
        # 5. 更新缓存
        if self.cache:
            self.cache.put(cache_key, result)
        
        # 6. 触发回调
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


# ==================== 使用示例 ====================

async def example_usage():
    """使用示例"""
    
    # 创建配置
    config = IntentConfig(
        keyword_match_threshold=0.8,
        semantic_match_threshold=0.75,
        cache_enabled=True
    )
    
    # 初始化引擎
    engine = IntentEngine(config)
    
    # 注册意图
    engine.register_intent(IntentDefinition(
        name="code_generation",
        description="生成代码",
        keywords=["写代码", "编程", "实现", "开发"],
        patterns=[r".*写.*代码.*", r".*生成.*函数.*"],
        examples=[
            "帮我写一个Python函数",
            "生成一个排序算法",
            "实现一个用户登录功能"
        ],
        priority=1,
        threshold=0.7
    ))
    
    engine.register_intent(IntentDefinition(
        name="code_review",
        description="代码审查",
        keywords=["review", "检查", "优化", "改进"],
        patterns=[r".*review.*代码.*", r".*检查.*代码.*"],
        examples=[
            "帮我review这段代码",
            "检查一下这个函数的问题",
            "优化一下这个实现"
        ],
        priority=1,
        threshold=0.75
    ))
    
    engine.register_intent(IntentDefinition(
        name="question_answering",
        description="问答",
        keywords=["什么是", "怎么", "为什么", "如何"],
        patterns=[r"^(什么是|怎么|为什么|如何).*"],
        examples=[
            "什么是Python的装饰器？",
            "怎么实现单例模式？",
            "为什么需要类型提示？"
        ],
        priority=2,
        threshold=0.6
    ))
    
    # 测试识别
    test_queries = [
        "帮我写一个Python快速排序函数",
        "检查一下这段代码",
        "什么是装饰器？",
        "你好"
    ]
    
    print("=== 意图识别测试 ===\n")
    
    for query in test_queries:
        result = await engine.recognize(query)
        print(f"输入: '{query}'")
        print(f"  意图: {result.intent}")
        print(f"  置信度: {result.confidence:.2f}")
        print(f"  策略: {result.strategy}")
        print(f"  耗时: {result.processing_time_ms:.2f}ms")
        print()
    
    # 打印性能指标
    print("=== 性能指标 ===")
    metrics = engine.get_metrics()
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")


if __name__ == "__main__":
    asyncio.run(example_usage())
