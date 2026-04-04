"""
意图识别引擎 - 分类链实现
参考LangChain chains/classification/ 和 chains/router/ 设计模式

本模块实现了基于LangChain设计思想的意图识别分类链，包括：
1. Chain基类模式 - 所有识别器的抽象基类
2. LLMChain模式 - Few-shot学习分类器
3. RouterChain模式 - 意图路由链
4. MultiRouteChain模式 - 多策略融合链

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-02
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, NamedTuple, Mapping
from enum import Enum
from pydantic import BaseModel, Field
import asyncio


# ==================== 数据模型定义 ====================

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


class Route(NamedTuple):
    """路由结果 - 参考LangChain Route"""
    destination: Optional[str]
    next_inputs: Dict[str, Any]


# ==================== Chain基类模式 ====================

class IntentChain(ABC):
    """
    意图识别链抽象基类
    
    参考LangChain的Chain基类设计，提供统一的识别接口
    所有具体的识别器（关键词、语义、Few-shot）都继承此类
    
    核心方法:
        - recognize: 同步识别方法
        - arecognize: 异步识别方法
        - _recognize: 子类实现的实际识别逻辑
    """
    
    def __init__(self, name: str, priority: int = 1):
        self.name = name
        self.priority = priority
        self.verbose: bool = False
        self.metadata: Dict[str, Any] = {}
    
    @property
    @abstractmethod
    def input_keys(self) -> List[str]:
        """输入键列表"""
        return ["query"]
    
    @property
    @abstractmethod
    def output_keys(self) -> List[str]:
        """输出键列表"""
        return ["intent", "confidence"]
    
    @abstractmethod
    def _recognize(self, query: str, context: Optional[Dict] = None) -> Optional[MatchResult]:
        """
        实际识别逻辑 - 子类必须实现
        
        Args:
            query: 用户输入文本
            context: 上下文信息
            
        Returns:
            MatchResult或None
        """
        pass
    
    async def _arecognize(self, query: str, context: Optional[Dict] = None) -> Optional[MatchResult]:
        """
        异步识别逻辑 - 默认使用同步方法
        子类可以覆盖以提供真正的异步实现
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self._recognize, query, context
        )
    
    def recognize(self, query: str, context: Optional[Dict] = None) -> Optional[MatchResult]:
        """
        同步识别入口
        
        Args:
            query: 用户输入文本
            context: 上下文信息
            
        Returns:
            MatchResult或None
        """
        if self.verbose:
            print(f"[{self.name}] Recognizing: {query}")
        
        result = self._recognize(query, context)
        
        if self.verbose and result:
            print(f"[{self.name}] Result: {result.intent} ({result.confidence:.2f})")
        
        return result
    
    async def arecognize(self, query: str, context: Optional[Dict] = None) -> Optional[MatchResult]:
        """
        异步识别入口
        
        Args:
            query: 用户输入文本
            context: 上下文信息
            
        Returns:
            MatchResult或None
        """
        if self.verbose:
            print(f"[{self.name}] Async recognizing: {query}")
        
        result = await self._arecognize(query, context)
        
        if self.verbose and result:
            print(f"[{self.name}] Result: {result.intent} ({result.confidence:.2f})")
        
        return result


# ==================== RouterChain模式 ====================

class IntentRouterChain(IntentChain):
    """
    意图路由链
    
    参考LangChain的RouterChain设计，用于将输入路由到特定的意图
    输出目标意图名称和下一步输入
    
    使用场景:
        - 多意图场景下的初步路由
        - 意图分类的初步筛选
    """
    
    def __init__(self, name: str = "intent_router"):
        super().__init__(name, priority=1)
        self.intent_definitions: Dict[str, IntentDefinition] = {}
    
    @property
    def input_keys(self) -> List[str]:
        return ["query"]
    
    @property
    def output_keys(self) -> List[str]:
        return ["destination", "next_inputs"]
    
    def add_intent(self, intent_def: IntentDefinition) -> None:
        """添加意图定义"""
        self.intent_definitions[intent_def.name] = intent_def
    
    def route(self, query: str, context: Optional[Dict] = None) -> Route:
        """
        路由输入到目标意图
        
        Args:
            query: 用户输入
            context: 上下文
            
        Returns:
            Route对象，包含destination和next_inputs
        """
        result = self._recognize(query, context)
        if result:
            return Route(
                destination=result.intent,
                next_inputs={"query": query, "context": context}
            )
        return Route(destination=None, next_inputs={"query": query})
    
    async def aroute(self, query: str, context: Optional[Dict] = None) -> Route:
        """异步路由"""
        result = await self._arecognize(query, context)
        if result:
            return Route(
                destination=result.intent,
                next_inputs={"query": query, "context": context}
            )
        return Route(destination=None, next_inputs={"query": query})
    
    def _recognize(self, query: str, context: Optional[Dict] = None) -> Optional[MatchResult]:
        """基础路由实现 - 子类应覆盖"""
        raise NotImplementedError("Subclasses must implement _recognize")


# ==================== MultiRouteChain模式 ====================

class MultiIntentChain(IntentChain):
    """
    多意图融合链
    
    参考LangChain的MultiRouteChain设计，实现多策略融合
    支持多个识别链的级联调用和结果融合
    
    核心特性:
        - 多策略级联（关键词 -> 语义 -> Few-shot）
        - 结果融合与冲突解决
        - 提前终止机制
    """
    
    def __init__(
        self,
        name: str = "multi_intent",
        chains: Optional[List[IntentChain]] = None,
        default_chain: Optional[IntentChain] = None,
        enable_early_termination: bool = True
    ):
        super().__init__(name, priority=1)
        self.chains: List[IntentChain] = chains or []
        self.default_chain: Optional[IntentChain] = default_chain
        self.enable_early_termination: bool = enable_early_termination
        self.confidence_threshold: float = 0.8
    
    @property
    def input_keys(self) -> List[str]:
        return ["query"]
    
    @property
    def output_keys(self) -> List[str]:
        return ["intent", "confidence", "strategy"]
    
    def add_chain(self, chain: IntentChain) -> None:
        """添加识别链"""
        self.chains.append(chain)
        # 按优先级排序
        self.chains.sort(key=lambda x: x.priority)
    
    def _recognize(self, query: str, context: Optional[Dict] = None) -> Optional[MatchResult]:
        """
        多链级联识别
        
        执行流程:
        1. 按优先级遍历所有识别链
        2. 每个链尝试识别
        3. 高置信度结果提前返回
        4. 低置信度继续下一链
        5. 融合所有结果
        """
        results: List[MatchResult] = []
        
        for chain in self.chains:
            result = chain.recognize(query, context)
            
            if result:
                results.append(result)
                
                # 提前终止条件
                if self.enable_early_termination and result.confidence >= self.confidence_threshold:
                    if self.verbose:
                        print(f"[MultiIntent] Early termination with confidence {result.confidence:.2f}")
                    return result
        
        # 融合结果
        if results:
            return self._fuse_results(results)
        
        # 使用默认链
        if self.default_chain:
            return self.default_chain.recognize(query, context)
        
        return None
    
    async def _arecognize(self, query: str, context: Optional[Dict] = None) -> Optional[MatchResult]:
        """异步多链级联识别"""
        results: List[MatchResult] = []
        
        for chain in self.chains:
            result = await chain.arecognize(query, context)
            
            if result:
                results.append(result)
                
                if self.enable_early_termination and result.confidence >= self.confidence_threshold:
                    return result
        
        if results:
            return self._fuse_results(results)
        
        if self.default_chain:
            return await self.default_chain.arecognize(query, context)
        
        return None
    
    def _fuse_results(self, results: List[MatchResult]) -> MatchResult:
        """
        融合多个识别结果
        
        融合策略:
        1. 按置信度加权
        2. 考虑策略优先级
        3. 返回最佳结果
        """
        if not results:
            return None
        
        # 按置信度排序，取最高
        best = max(results, key=lambda x: x.confidence)
        
        # 如果有多个高置信度结果，标记为融合策略
        high_conf_results = [r for r in results if r.confidence >= 0.7]
        if len(high_conf_results) > 1:
            best.strategy = IntentStrategy.FUSION
            best.metadata["fused_results"] = len(high_conf_results)
        
        return best


# ==================== LLMChain模式 - Few-shot分类器 ====================

class LLMIntentChain(IntentChain):
    """
    LLM-based意图识别链
    
    参考LangChain的LLMChain设计，实现基于Few-shot学习的意图分类
    
    核心特性:
        - Prompt模板管理
        - Few-shot示例选择
        - 输出解析
        - 置信度计算
    """
    
    def __init__(
        self,
        name: str = "llm_intent",
        llm_client: Optional[Any] = None,
        prompt_template: Optional[str] = None
    ):
        super().__init__(name, priority=3)
        self.llm_client = llm_client
        self.prompt_template = prompt_template or self._default_prompt()
        self.examples: Dict[str, List[str]] = {}
        self.intent_descriptions: Dict[str, str] = {}
    
    @property
    def input_keys(self) -> List[str]:
        return ["query"]
    
    @property
    def output_keys(self) -> List[str]:
        return ["intent", "confidence"]
    
    def _default_prompt(self) -> str:
        """默认分类Prompt模板"""
        return """你是一个意图识别专家。请将用户输入分类到以下意图之一：

{intent_descriptions}

参考示例：
{examples}

用户输入: {query}

请输出JSON格式：
{{
    "intent": "意图名称",
    "confidence": 0.95,
    "reasoning": "分类理由"
}}
"""
    
    def add_intent(self, name: str, description: str, examples: List[str]) -> None:
        """添加意图定义和示例"""
        self.intent_descriptions[name] = description
        self.examples[name] = examples
    
    def _build_prompt(self, query: str) -> str:
        """构建分类Prompt"""
        # 构建意图描述
        desc_parts = []
        for intent, desc in self.intent_descriptions.items():
            desc_parts.append(f"- {intent}: {desc}")
        intent_descriptions = "\n".join(desc_parts)
        
        # 构建示例
        example_parts = []
        for intent, exs in self.examples.items():
            for ex in exs[:2]:  # 每个意图取2个示例
                example_parts.append(f'输入: "{ex}" -> 意图: {intent}')
        examples_str = "\n".join(example_parts)
        
        return self.prompt_template.format(
            intent_descriptions=intent_descriptions,
            examples=examples_str,
            query=query
        )
    
    def _recognize(self, query: str, context: Optional[Dict] = None) -> Optional[MatchResult]:
        """
        LLM分类识别
        
        注意：这是简化实现，实际应调用LLM客户端
        """
        if not self.llm_client:
            # 模拟实现：基于示例匹配
            return self._mock_classify(query)
        
        # 实际实现应调用LLM
        # prompt = self._build_prompt(query)
        # response = self.llm_client.generate(prompt)
        # parsed = self._parse_output(response)
        # return MatchResult(...)
        
        return self._mock_classify(query)
    
    def _mock_classify(self, query: str) -> Optional[MatchResult]:
        """模拟分类 - 基于示例匹配"""
        best_intent = None
        best_score = 0
        
        for intent, examples in self.examples.items():
            score = 0
            for example in examples:
                # 简单词重叠计算
                query_words = set(query.lower().split())
                example_words = set(example.lower().split())
                overlap = len(query_words & example_words)
                score += overlap
            
            if score > best_score:
                best_score = score
                best_intent = intent
        
        if best_intent and best_score > 0:
            confidence = min(0.5 + best_score * 0.1, 0.9)
            return MatchResult(
                intent=best_intent,
                confidence=confidence,
                matched_text=query,
                strategy=IntentStrategy.FEW_SHOT,
                metadata={"mock": True, "score": best_score}
            )
        
        return None
    
    def _parse_output(self, output: str) -> Dict[str, Any]:
        """解析LLM输出"""
        import json
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return {"intent": "unknown", "confidence": 0.0}


# ==================== 使用示例 ====================

def example_usage():
    """使用示例"""
    
    # 1. 创建多意图融合链
    multi_chain = MultiIntentChain(name="intent_engine")
    
    # 2. 创建并添加关键词匹配链（简化示例）
    class KeywordChain(IntentChain):
        def __init__(self):
            super().__init__("keyword_matcher", priority=1)
            self.keywords = {
                "code": ["写代码", "编程", "实现", "开发"],
                "search": ["搜索", "查找", "查询"],
                "chat": ["聊天", "对话", "闲聊"]
            }
        
        def _recognize(self, query: str, context: Optional[Dict] = None) -> Optional[MatchResult]:
            for intent, words in self.keywords.items():
                for word in words:
                    if word in query:
                        return MatchResult(
                            intent=intent,
                            confidence=0.9,
                            matched_text=word,
                            strategy=IntentStrategy.KEYWORD
                        )
            return None
    
    multi_chain.add_chain(KeywordChain())
    
    # 3. 创建并添加LLM Few-shot链
    llm_chain = LLMIntentChain(name="few_shot_classifier")
    llm_chain.add_intent(
        "code",
        "用户需要编写或修改代码",
        ["帮我写一个Python函数", "实现一个排序算法"]
    )
    llm_chain.add_intent(
        "search",
        "用户需要搜索信息",
        ["搜索最新的AI论文", "查找Python文档"]
    )
    multi_chain.add_chain(llm_chain)
    
    # 4. 执行识别
    result = multi_chain.recognize("帮我写一段Python代码")
    if result:
        print(f"识别结果: {result.intent}, 置信度: {result.confidence:.2f}, 策略: {result.strategy}")


if __name__ == "__main__":
    example_usage()
