"""
意图识别引擎 - 关键词匹配策略

基于关键词匹配的意图识别策略

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

import asyncio
import re
from typing import Dict, List, Optional, Any

from interfaces.base_strategy import BaseStrategy, MatchResult, IntentStrategyType
from common.template_parser import get_all_intents, get_intent


class KeywordStrategy(BaseStrategy):
    """
    关键词匹配策略
    
    基于关键词的意图识别策略，支持完全匹配和包含匹配
    """
    
    @property
    def strategy_type(self) -> IntentStrategyType:
        """
        策略类型
        
        Returns:
            策略类型枚举值
        """
        return IntentStrategyType.KEYWORD
    
    @property
    def name(self) -> str:
        """
        策略名称
        
        Returns:
            策略名称字符串
        """
        return "keyword"
    
    @property
    def priority(self) -> int:
        """
        策略优先级
        
        Returns:
            优先级数值，越小优先级越高
        """
        return 1
    
    def __init__(self):
        """
        初始化关键词匹配策略
        """
        super().__init__()
        self._intents = []
        self._keyword_map: Dict[str, List[str]] = {}
        self._initialized = False
    
    def initialize(self, config: Dict[str, Any] = None) -> None:
        """
        初始化策略
        
        Args:
            config: 策略配置
        """
        self._load_intents()
        self._build_keyword_map()
        self._initialized = True
    
    def _load_intents(self) -> None:
        """
        加载意图模板
        """
        self._intents = get_all_intents()
    
    def _build_keyword_map(self) -> None:
        """
        构建关键词映射
        """
        self._keyword_map.clear()
        for intent in self._intents:
            intent_name = intent.get("name")
            keywords = intent.get("keywords", [])
            if intent_name and keywords:
                self._keyword_map[intent_name] = keywords
    
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
        
        if not query:
            return None
        
        # 预处理查询文本
        query = query.strip().lower()
        
        # 匹配结果
        best_match = None
        best_score = 0.0
        matched_keywords = []
        
        # 遍历所有意图进行匹配
        for intent_name, keywords in self._keyword_map.items():
            score, matched = self._match_keywords(query, keywords)
            if score > best_score:
                best_score = score
                best_match = intent_name
                matched_keywords = matched
        
        # 如果找到匹配
        if best_match and best_score > 0:
            # 计算置信度
            confidence = self._calculate_confidence(best_score, len(query), len(matched_keywords))
            
            # 提取实体（简单实现）
            entities = self._extract_entities(query, best_match)
            
            # 构建匹配结果
            result = MatchResult(
                intent=best_match,
                confidence=confidence,
                matched_text=query,
                strategy=self.strategy_type,
                metadata={
                    "matched_keywords": matched_keywords,
                    "score": best_score
                }
            )
            
            return result
        
        return None
    
    def _match_keywords(self, query: str, keywords: List[str]) -> tuple[float, List[str]]:
        """
        匹配关键词
        
        Args:
            query: 用户输入文本
            keywords: 关键词列表
            
        Returns:
            (匹配得分, 匹配的关键词列表)
        """
        matched = []
        score = 0.0
        
        for keyword in keywords:
            keyword_lower = keyword.strip().lower()
            query_lower = query.strip().lower()
            
            # 跳过空关键词
            if not keyword_lower:
                continue
            
            # 完全匹配
            if keyword_lower == query_lower:
                score += 3.0 + len(keyword) * 0.1  # 完全匹配得分最高
                matched.append(keyword)
            # 包含匹配（关键词是查询的子串）
            elif keyword_lower in query_lower:
                # 计算匹配长度占比
                match_ratio = len(keyword_lower) / len(query_lower)
                if match_ratio > 0.2:  # 只考虑有一定长度的匹配
                    score += 2.0 * match_ratio + len(keyword) * 0.05
                    matched.append(keyword)
            # 分词匹配 - 对于多词关键词
            elif ' ' in keyword_lower:
                keyword_words = keyword_lower.split()
                # 检查所有词是否都在查询中
                all_words_present = all(word in query_lower for word in keyword_words)
                if all_words_present:
                    score += 1.5 + len(keyword) * 0.03
                    matched.append(keyword)
            # 特殊处理：代码相关关键词
            elif any(code_term in query_lower for code_term in ['代码', '编程', 'python', 'java', 'c++']):
                if any(code_keyword in keyword_lower for code_keyword in ['代码', '生成', '实现', '创建']):
                    score += 1.0 + len(keyword) * 0.02
                    matched.append(keyword)
        
        return score, matched
    
    def _calculate_confidence(self, score: float, query_length: int, matched_count: int) -> float:
        """
        计算置信度
        
        Args:
            score: 匹配得分
            query_length: 查询长度
            matched_count: 匹配的关键词数量
            
        Returns:
            置信度 (0.0-1.0)
        """
        # 基础置信度
        base_confidence = min(score / (score + 1.0), 0.95)
        
        # 考虑查询长度和匹配数量
        if query_length > 0:
            length_factor = min(matched_count / max(1, query_length / 5), 1.0)
            base_confidence = base_confidence * 0.8 + length_factor * 0.2
        
        # 确保置信度在合理范围内
        return max(0.1, min(base_confidence, 1.0))
    
    def _extract_entities(self, query: str, intent_name: str) -> Dict[str, Any]:
        """
        从查询中提取实体
        
        Args:
            query: 用户输入文本
            intent_name: 意图名称
            
        Returns:
            提取的实体
        """
        entities = {}
        
        # 获取意图定义
        intent = get_intent(intent_name)
        if not intent:
            return entities
        
        # 简单的实体提取逻辑
        # 实际项目中可以使用更复杂的实体提取方法
        entity_schema = intent.get("entity_schema", {})
        
        # 示例：提取数字
        numbers = re.findall(r'\d+', query)
        if numbers:
            entities["numbers"] = numbers
        
        # 示例：提取日期
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', query)
        if dates:
            entities["dates"] = dates
        
        return entities
    
    def shutdown(self) -> None:
        """
        关闭策略
        """
        self._intents.clear()
        self._keyword_map.clear()
        self._initialized = False
