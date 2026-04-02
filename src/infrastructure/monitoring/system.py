from prometheus_client import Counter, Gauge, Histogram, Summary
import time
import logging
from typing import Dict, Optional


class MonitoringSystem:
    """监控系统"""
    
    def __init__(self):
        # 初始化指标
        self._init_metrics()
        
        # 配置日志
        self._configure_logging()
    
    def _init_metrics(self):
        """初始化监控指标"""
        # 计数器
        self.request_count = Counter(
            'super_ai_team_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status']
        )
        
        self.error_count = Counter(
            'super_ai_team_errors_total',
            'Total number of errors',
            ['error_type']
        )
        
        self.token_count = Counter(
            'super_ai_team_tokens_total',
            'Total number of tokens used',
            ['model', 'operation']
        )
        
        # 仪表盘
        self.active_requests = Gauge(
            'super_ai_team_active_requests',
            'Number of active requests'
        )
        
        self.memory_usage = Gauge(
            'super_ai_team_memory_usage_bytes',
            'Memory usage in bytes'
        )
        
        self.cpu_usage = Gauge(
            'super_ai_team_cpu_usage_percent',
            'CPU usage in percent'
        )
        
        # 直方图
        self.response_time = Histogram(
            'super_ai_team_response_time_seconds',
            'Response time in seconds',
            buckets=[0.001, 0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        
        # 摘要
        self.execution_time = Summary(
            'super_ai_team_execution_time_seconds',
            'Execution time in seconds'
        )
    
    def _configure_logging(self):
        """配置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('super-ai-team.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('super-ai-team')
    
    def log_request(self, method: str, endpoint: str, status: int, duration: float):
        """记录请求"""
        self.request_count.labels(method=method, endpoint=endpoint, status=status).inc()
        self.response_time.observe(duration)
        self.logger.info(f"Request: {method} {endpoint} {status} {duration:.4f}s")
    
    def log_error(self, error_type: str, message: str):
        """记录错误"""
        self.error_count.labels(error_type=error_type).inc()
        self.logger.error(f"Error ({error_type}): {message}")
    
    def log_token_usage(self, model: str, operation: str, tokens: int):
        """记录token使用情况"""
        self.token_count.labels(model=model, operation=operation).inc(tokens)
        self.logger.info(f"Token usage: {model} {operation} {tokens}")
    
    def update_resource_usage(self, memory: int, cpu: float):
        """更新资源使用情况"""
        self.memory_usage.set(memory)
        self.cpu_usage.set(cpu)
    
    def time_execution(self, func):
        """装饰器：记录执行时间"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            self.execution_time.observe(duration)
            return result
        return wrapper
    
    def get_metrics(self) -> Dict[str, float]:
        """获取指标"""
        # 这里简化实现，实际应该从prometheus客户端获取
        return {
            'requests_total': self.request_count._value.get(),
            'errors_total': self.error_count._value.get(),
            'active_requests': self.active_requests._value.get(),
            'response_time': self.response_time._value.get()
        }
