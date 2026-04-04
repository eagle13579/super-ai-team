"""
意图识别引擎 - 监控系统

提供全面的性能监控和可观测性

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"      # 计数器
    GAUGE = "gauge"          # 仪表盘
    HISTOGRAM = "histogram"  # 直方图
    TIMER = "timer"          # 计时器


@dataclass
class Metric:
    """指标定义"""
    name: str
    value: float
    metric_type: MetricType
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "labels": self.labels,
            "timestamp": self.timestamp
        }


@dataclass
class RequestLog:
    """请求日志"""
    query: str
    intent: str
    confidence: float
    latency_ms: float
    strategy: str
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MonitoringSystem:
    """
    监控系统
    
    提供全面的性能监控和可观测性
    """
    
    def __init__(self, enable_logging: bool = True):
        """
        初始化监控系统
        
        Args:
            enable_logging: 是否启用日志
        """
        self.metrics: Dict[str, List[Metric]] = {}
        self.request_logs: List[RequestLog] = []
        self.max_logs = 10000  # 最大日志数
        self.enable_logging = enable_logging
        
        # 回调函数
        self.on_metric_recorded: Optional[Callable] = None
        self.on_request_logged: Optional[Callable] = None
        
        # 性能统计
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_latency_ms": 0.0,
            "strategy_distribution": {},
            "intent_distribution": {}
        }
        
        # 设置日志
        if enable_logging:
            self._setup_logging()
    
    def _setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('intent_engine.log')
            ]
        )
        self.logger = logging.getLogger('IntentEngine')
    
    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        记录指标
        
        Args:
            name: 指标名称
            value: 指标值
            metric_type: 指标类型
            labels: 标签
        """
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            labels=labels or {}
        )
        
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append(metric)
        
        # 触发回调
        if self.on_metric_recorded:
            self.on_metric_recorded(metric)
        
        # 记录日志
        if self.enable_logging:
            self.logger.info(f"Metric recorded: {name}={value} ({metric_type.value})")
    
    def record_request(
        self,
        query: str,
        intent: str,
        confidence: float,
        latency_ms: float,
        strategy: str,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        记录请求
        
        Args:
            query: 查询文本
            intent: 识别意图
            confidence: 置信度
            latency_ms: 延迟（毫秒）
            strategy: 使用的策略
            success: 是否成功
            metadata: 元数据
        """
        request_log = RequestLog(
            query=query,
            intent=intent,
            confidence=confidence,
            latency_ms=latency_ms,
            strategy=strategy,
            success=success,
            metadata=metadata or {}
        )
        
        # 添加到日志列表
        self.request_logs.append(request_log)
        
        # 限制日志数量
        if len(self.request_logs) > self.max_logs:
            self.request_logs = self.request_logs[-self.max_logs:]
        
        # 更新统计
        self._update_stats(request_log)
        
        # 触发回调
        if self.on_request_logged:
            self.on_request_logged(request_log)
        
        # 记录日志
        if self.enable_logging:
            status = "SUCCESS" if success else "FAILED"
            self.logger.info(
                f"Request {status}: query='{query}', intent={intent}, "
                f"confidence={confidence:.2f}, latency={latency_ms:.2f}ms, strategy={strategy}"
            )
    
    def _update_stats(self, request_log: RequestLog) -> None:
        """更新统计信息"""
        self.stats["total_requests"] += 1
        
        if request_log.success:
            self.stats["successful_requests"] += 1
        else:
            self.stats["failed_requests"] += 1
        
        self.stats["total_latency_ms"] += request_log.latency_ms
        
        # 策略分布
        strategy = request_log.strategy
        if strategy not in self.stats["strategy_distribution"]:
            self.stats["strategy_distribution"][strategy] = 0
        self.stats["strategy_distribution"][strategy] += 1
        
        # 意图分布
        intent = request_log.intent
        if intent not in self.stats["intent_distribution"]:
            self.stats["intent_distribution"][intent] = 0
        self.stats["intent_distribution"][intent] += 1
    
    def get_metrics(self, name: Optional[str] = None) -> List[Metric]:
        """
        获取指标
        
        Args:
            name: 指标名称（可选）
            
        Returns:
            指标列表
        """
        if name:
            return self.metrics.get(name, [])
        
        # 返回所有指标
        all_metrics = []
        for metrics in self.metrics.values():
            all_metrics.extend(metrics)
        return all_metrics
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息
        """
        stats = self.stats.copy()
        
        # 计算平均延迟
        if stats["total_requests"] > 0:
            stats["avg_latency_ms"] = stats["total_latency_ms"] / stats["total_requests"]
            stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
        else:
            stats["avg_latency_ms"] = 0.0
            stats["success_rate"] = 0.0
        
        return stats
    
    def get_request_logs(
        self,
        limit: int = 100,
        intent: Optional[str] = None,
        strategy: Optional[str] = None
    ) -> List[RequestLog]:
        """
        获取请求日志
        
        Args:
            limit: 返回数量限制
            intent: 意图过滤
            strategy: 策略过滤
            
        Returns:
            请求日志列表
        """
        logs = self.request_logs
        
        # 过滤
        if intent:
            logs = [log for log in logs if log.intent == intent]
        if strategy:
            logs