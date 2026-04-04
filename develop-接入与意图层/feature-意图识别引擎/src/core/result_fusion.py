"""
意图识别引擎 - 结果融合器

智能融合多策略结果，实现冲突解决和置信度校准

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from interfaces.base_strategy import MatchResult, IntentStrategyType


class FusionStrategy(Enum):
    """融合策略"""
    WEIGHTED_AVERAGE = "weighted_average"  # 加权平均
    VOTING = "voting"                      # 投票机制
    MAX_CONFIDENCE = "max_confidence"      # 最大置信度
    PRIORITY = "priority"                  # 优先级策略


@dataclass
class FusionConfig:
    """融合配置"""
    strategy_weights: Dict[IntentStrategyType, float] = None
    confidence_threshold: float = 0.5
    min_votes: int = 1
    enable_conflict_resolution: bool = True
    
    def __post_init__(self):
        if self.strategy_weights is None:
            self.strategy_weights = {
                IntentStrategyType.KEYWORD: 0.3,
                IntentStrategyType.SEMANTIC: 0.5,
                IntentStrategyType.FEW_SHOT: 0.7
            }


class ResultFusion:
    """
    结果融合器
    
    智能融合多策略结果，实现冲突解决和置信度校准
    """
    
    def __init__(self, config: Optional[FusionConfig] = None):
        """
        初始化结果融合器
        
        Args:
            config: 融合配置
        """
        self.config = config or FusionConfig()
    
    def fuse(self, results: List[MatchResult], fusion_strategy: FusionStrategy = FusionStrategy.WEIGHTED_AVERAGE) -> Optional[MatchResult]:
        """
        融合多个策略结果
        
        Args:
            results: 多个策略的匹配结果
            fusion_strategy: 融合策略
            
        Returns:
            融合后的结果或None
        """
        if not results:
            return None
        
        # 如果只有一个结果，直接返回
        if len(results) == 1:
            return results[0]
        
        # 根据融合策略选择方法
        if fusion_strategy == FusionStrategy.WEIGHTED_AVERAGE:
            return self._weighted_average_fusion(results)
        elif fusion_strategy == FusionStrategy.VOTING:
            return self._voting_fusion(results)
        elif fusion_strategy == FusionStrategy.MAX_CONFIDENCE:
            return self._max_confidence_fusion(results)
        elif fusion_strategy == FusionStrategy.PRIORITY:
            return self._priority_fusion(results)
        else:
            return self._weighted_average_fusion(results)
    
    def _weighted_average_fusion(self, results: List[MatchResult]) -> Optional[MatchResult]:
        """
        加权平均融合
        
        Args:
            results: 匹配结果列表
            
        Returns:
            融合后的结果
        """
        # 按意图分组
        intent_groups: Dict[str, List[MatchResult]] = {}
        for result in results:
            if result.intent not in intent_groups:
                intent_groups[result.intent] = []
            intent_groups[result.intent].append(result)
        
        # 计算每个意图的加权置信度
        best_intent = None
        best_confidence = 0.0
        best_result = None
        
        for intent, group in intent_groups.items():
            weighted_confidence = 0.0
            total_weight = 0.0
            
            for result in group:
                weight = self.config.strategy_weights.get(result.strategy, 0.5)
                weighted_confidence += result.confidence * weight
                total_weight += weight
            
            if total_weight > 0:
                final_confidence = weighted_confidence / total_weight
                
                if final_confidence > best_confidence:
                    best_confidence = final_confidence
                    best_intent = intent
                    # 选择该组中置信度最高的结果作为代表
                    best_result = max(group, key=lambda r: r.confidence)
        
        if best_result and best_confidence >= self.config.confidence_threshold:
            # 创建新的融合结果
            return MatchResult(
                intent=best_intent,
                confidence=min(best_confidence, 0.95),
                matched_text=best_result.matched_text,
                strategy=IntentStrategyType.FUSION,
                metadata={
                    "fusion_strategy": "weighted_average",
                    "original_results": [r.dict() for r in results],
                    "intent_distribution": {intent: len(group) for intent, group in intent_groups.items()}
                }
            )
        
        return None
    
    def _voting_fusion(self, results: List[MatchResult]) -> Optional[MatchResult]:
        """
        投票融合
        
        Args:
            results: 匹配结果列表
            
        Returns:
            融合后的结果
        """
        # 统计每个意图的票数
        intent_votes: Dict[str, int] = {}
        intent_results: Dict[str, List[MatchResult]] = {}
        
        for result in results:
            intent_votes[result.intent] = intent_votes.get(result.intent, 0) + 1
            if result.intent not in intent_results:
                intent_results[result.intent] = []
            intent_results[result.intent].append(result)
        
        # 找到票数最多的意图
        if not intent_votes:
            return None
        
        best_intent = max(intent_votes, key=intent_votes.get)
        max_votes = intent_votes[best_intent]
        
        # 检查是否达到最小票数要求
        if max_votes < self.config.min_votes:
            return None
        
        # 选择该意图中置信度最高的结果
        best_result = max(intent_results[best_intent], key=lambda r: r.confidence)
        
        # 计算投票置信度
        vote_confidence = max_votes / len(results)
        final_confidence = (best_result.confidence + vote_confidence) / 2
        
        return MatchResult(
            intent=best_intent,
            confidence=min(final_confidence, 0.95),
            matched_text=best_result.matched_text,
            strategy=IntentStrategyType.FUSION,
            metadata={
                "fusion_strategy": "voting",
                "votes": max_votes,
                "total_results": len(results),
                "vote_confidence": vote_confidence
            }
        )
    
    def _max_confidence_fusion(self, results: List[MatchResult]) -> Optional[MatchResult]:
        """
        最大置信度融合
        
        Args:
            results: 匹配结果列表
            
        Returns:
            融合后的结果
        """
        # 选择置信度最高的结果
        best_result = max(results, key=lambda r: r.confidence)
        
        if best_result.confidence >= self.config.confidence_threshold:
            # 创建新的融合结果
            return MatchResult(
                intent=best_result.intent,
                confidence=best_result.confidence,
                matched_text=best_result.matched_text,
                strategy=IntentStrategyType.FUSION,
                metadata={
                    "fusion_strategy": "max_confidence",
                    "original_strategy": best_result.strategy.value,
                    "all_confidences": [r.confidence for r in results]
                }
            )
        
        return None
    
    def _priority_fusion(self, results: List[MatchResult]) -> Optional[MatchResult]:
        """
        优先级融合
        
        Args:
            results: 匹配结果列表
            
        Returns:
            融合后的结果
        """
        # 定义策略优先级（数值越小优先级越高）
        priority_map = {
            IntentStrategyType.KEYWORD: 1,
            IntentStrategyType.SEMANTIC: 2,
            IntentStrategyType.FEW_SHOT: 3
        }
        
        # 按优先级排序
        sorted_results = sorted(
            results,
            key=lambda r: priority_map.get(r.strategy, 99)
        )
        
        # 选择优先级最高的结果
        best_result = sorted_results[0]
        
        if best_result.confidence >= self.config.confidence_threshold:
            return MatchResult(
                intent=best_result.intent,
                confidence=best_result.confidence,
                matched_text=best_result.matched_text,
                strategy=IntentStrategyType.FUSION,
                metadata={
                    "fusion_strategy": "priority",
                    "original_strategy": best_result.strategy.value,
                    "priority": priority_map.get(best_result.strategy, 99)
                }
            )
        
        return None
    
    def resolve_conflict(self, results: List[MatchResult]) -> Optional[MatchResult]:
        """
        解决冲突
        
        Args:
            results: 匹配结果列表
            
        Returns:
            解决冲突后的结果
        """
        if not self.config.enable_conflict_resolution:
            return self.fuse(results)
        
        # 检查是否有冲突（不同意图）
        intents = set(r.intent for r in results)
        if len(intents) <= 1:
            # 没有冲突，直接融合
            return self.fuse(results)
        
        # 分析冲突
        intent_scores: Dict[str, float] = {}
        for result in results:
            weight = self.config.strategy_weights.get(result.strategy, 0.5)
            score = result.confidence * weight
            
            if result.intent in intent_scores:
                intent_scores[result.intent] += score
            else:
                intent_scores[result.intent] = score
        
        # 选择得分最高的意图
        best_intent = max(intent_scores, key=intent_scores.get)
        best_score = intent_scores[best_intent]
        
        # 找到该意图的所有结果
        best_results = [r for r in results if r.intent == best_intent]
        best_result = max(best_results, key=lambda r: r.confidence)
        
        return MatchResult(
            intent=best_intent,
            confidence=min(best_score, 0.95),
            matched_text=best_result.matched_text,
            strategy=IntentStrategyType.FUSION,
            metadata={
                "fusion_strategy": "conflict_resolution",
                "conflict_detected": True,
                "competing_intents": list(intents),
                "intent_scores": intent_scores
            }
        )
    
    def calibrate_confidence(self, confidence: float, strategy: IntentStrategyType) -> float:
        """
        校准置信度
        
        Args:
            confidence: 原始置信度
            strategy: 策略类型
            
        Returns:
            校准后的置信度
        """
        # 根据策略类型进行校准
        calibration_factors = {
            IntentStrategyType.KEYWORD: 1.0,
            IntentStrategyType.SEMANTIC: 1.05,
            IntentStrategyType.FEW_SHOT: 1.1
        }
        
        factor = calibration_factors.get(strategy, 1.0)
        calibrated = confidence * factor
        
        # 确保在合理范围内
        return min(max(calibrated, 0.0), 1.0)


# 全局结果融合器实例
_fusion_engine = None


def get_fusion_engine(config: Optional[FusionConfig] = None) -> ResultFusion:
    """
    获取全局结果融合器实例
    
    Args:
        config: 融合配置
        
    Returns:
        结果融合器实例
    """
    global _fusion_engine
    if _fusion_engine is None:
        _fusion_engine = ResultFusion(config)
    return _fusion_engine
