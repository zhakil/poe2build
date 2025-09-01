# -*- coding: utf-8 -*-
"""
弹性服务接口定义

本模块定义了系统弹性服务的抽象接口，包括断路器、重试机制、降级策略等。
设计基于微服务架构中的弹性模式，确保系统在外部服务故障时的稳定性。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time


class CircuitBreakerState(Enum):
    """断路器状态"""
    CLOSED = "closed"      # 正常状态，允许请求通过
    OPEN = "open"          # 断开状态，拒绝请求
    HALF_OPEN = "half_open"  # 半开状态，允许少量请求测试服务恢复


class ServiceStatus(Enum):
    """服务状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    RECOVERING = "recovering"
    MAINTENANCE = "maintenance"


class FallbackStrategy(Enum):
    """降级策略"""
    CACHED_DATA = "cached_data"      # 使用缓存数据
    MOCK_DATA = "mock_data"          # 使用模拟数据
    ALTERNATIVE_SERVICE = "alternative_service"  # 使用备用服务
    SIMPLIFIED_RESPONSE = "simplified_response"  # 简化响应
    FAIL_FAST = "fail_fast"          # 快速失败


@dataclass
class RetryPolicy:
    """重试策略"""
    max_attempts: int = 3
    base_delay_ms: int = 1000
    max_delay_ms: int = 30000
    backoff_multiplier: float = 2.0
    jitter: bool = True
    retry_on_exceptions: List[type] = field(default_factory=lambda: [Exception])
    

@dataclass
class ServiceCall:
    """服务调用"""
    service_name: str
    method_name: str
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    timeout_ms: int = 5000
    retry_policy: Optional[RetryPolicy] = None
    fallback_strategy: FallbackStrategy = FallbackStrategy.CACHED_DATA
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceHealth:
    """服务健康状态"""
    service_name: str
    status: ServiceStatus
    response_time_ms: float = 0.0
    success_rate: float = 1.0
    error_rate: float = 0.0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    health_check_timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CallResult:
    """调用结果"""
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    execution_time_ms: int = 0
    attempts_made: int = 1
    fallback_used: bool = False
    fallback_strategy: Optional[FallbackStrategy] = None
    circuit_breaker_state: Optional[CircuitBreakerState] = None
    service_name: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


class IResilientService(ABC):
    """弹性服务基础接口
    
    定义所有弹性服务都应该实现的核心方法，包括断路器、重试、降级等功能。
    """
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """获取服务名称
        
        Returns:
            str: 服务名称
        """
        pass
    
    @abstractmethod
    def call(self, service_call: ServiceCall) -> CallResult:
        """执行弹性服务调用
        
        Args:
            service_call (ServiceCall): 服务调用请求
            
        Returns:
            CallResult: 调用结果
        """
        pass
    
    @abstractmethod
    def get_status(self) -> ServiceStatus:
        """获取服务状态
        
        Returns:
            ServiceStatus: 当前服务状态
        """
        pass
    
    @abstractmethod
    def get_health(self) -> ServiceHealth:
        """获取服务健康信息
        
        Returns:
            ServiceHealth: 详细健康状态
        """
        pass
    
    @abstractmethod
    def reset(self) -> bool:
        """重置服务状态
        
        Returns:
            bool: 重置是否成功
        """
        pass
    
    def is_healthy(self) -> bool:
        """检查服务是否健康
        
        Returns:
            bool: 服务是否健康
        """
        return self.get_status() in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]


class ICircuitBreaker(ABC):
    """断路器接口
    
    实现断路器模式，防止级联故障。
    """
    
    @abstractmethod
    def call(self, func: Callable, *args, **kwargs) -> CallResult:
        """通过断路器执行调用
        
        Args:
            func (Callable): 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            CallResult: 执行结果
        """
        pass
    
    @abstractmethod
    def get_state(self) -> CircuitBreakerState:
        """获取断路器状态
        
        Returns:
            CircuitBreakerState: 当前断路器状态
        """
        pass
    
    @abstractmethod
    def record_success(self) -> None:
        """记录成功调用"""
        pass
    
    @abstractmethod
    def record_failure(self) -> None:
        """记录失败调用"""
        pass
    
    @abstractmethod
    def force_open(self) -> None:
        """强制打开断路器"""
        pass
    
    @abstractmethod
    def force_close(self) -> None:
        """强制关闭断路器"""
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """重置断路器状态"""
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """获取断路器指标
        
        Returns:
            Dict[str, Any]: 断路器指标数据
        """
        pass


class IRateLimiter(ABC):
    """速率限制器接口
    
    控制服务调用频率，实现"生态公民"理念。
    """
    
    @abstractmethod
    def acquire(self, permits: int = 1) -> bool:
        """获取许可证
        
        Args:
            permits (int): 需要的许可证数量
            
        Returns:
            bool: 是否成功获取
        """
        pass
    
    @abstractmethod
    def try_acquire(self, permits: int = 1, timeout_ms: int = 0) -> bool:
        """尝试获取许可证
        
        Args:
            permits (int): 需要的许可证数量
            timeout_ms (int): 超时时间(毫秒)
            
        Returns:
            bool: 是否成功获取
        """
        pass
    
    @abstractmethod
    def get_rate(self) -> float:
        """获取当前速率
        
        Returns:
            float: 每秒允许的请求数
        """
        pass
    
    @abstractmethod
    def set_rate(self, permits_per_second: float) -> None:
        """设置速率限制
        
        Args:
            permits_per_second (float): 每秒允许的请求数
        """
        pass
    
    @abstractmethod
    def get_available_permits(self) -> int:
        """获取可用许可证数量
        
        Returns:
            int: 当前可用许可证数量
        """
        pass


class IRetryHandler(ABC):
    """重试处理器接口
    
    实现智能重试机制，包括指数退避。
    """
    
    @abstractmethod
    def execute_with_retry(self, func: Callable, retry_policy: RetryPolicy, *args, **kwargs) -> CallResult:
        """执行带重试的调用
        
        Args:
            func (Callable): 要执行的函数
            retry_policy (RetryPolicy): 重试策略
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            CallResult: 执行结果
        """
        pass
    
    @abstractmethod
    def should_retry(self, exception: Exception, attempt: int, retry_policy: RetryPolicy) -> bool:
        """判断是否应该重试
        
        Args:
            exception (Exception): 异常信息
            attempt (int): 当前尝试次数
            retry_policy (RetryPolicy): 重试策略
            
        Returns:
            bool: 是否应该重试
        """
        pass
    
    @abstractmethod
    def calculate_delay(self, attempt: int, retry_policy: RetryPolicy) -> int:
        """计算延迟时间
        
        Args:
            attempt (int): 当前尝试次数
            retry_policy (RetryPolicy): 重试策略
            
        Returns:
            int: 延迟时间(毫秒)
        """
        pass


class IFallbackHandler(ABC):
    """降级处理器接口
    
    实现多种降级策略，确保服务可用性。
    """
    
    @abstractmethod
    def execute_fallback(self, strategy: FallbackStrategy, service_call: ServiceCall, original_error: Exception) -> CallResult:
        """执行降级策略
        
        Args:
            strategy (FallbackStrategy): 降级策略
            service_call (ServiceCall): 原始服务调用
            original_error (Exception): 原始错误
            
        Returns:
            CallResult: 降级执行结果
        """
        pass
    
    @abstractmethod
    def get_cached_data(self, key: str) -> Optional[Any]:
        """获取缓存数据
        
        Args:
            key (str): 缓存键
            
        Returns:
            Optional[Any]: 缓存数据，不存在则返回None
        """
        pass
    
    @abstractmethod
    def get_mock_data(self, service_name: str, method_name: str) -> Any:
        """获取模拟数据
        
        Args:
            service_name (str): 服务名称
            method_name (str): 方法名称
            
        Returns:
            Any: 模拟数据
        """
        pass
    
    @abstractmethod
    def register_alternative_service(self, service_name: str, alternative: IResilientService) -> None:
        """注册备用服务
        
        Args:
            service_name (str): 主服务名称
            alternative (IResilientService): 备用服务实例
        """
        pass


class IHealthChecker(ABC):
    """健康检查器接口
    
    监控服务健康状态，提供实时状态信息。
    """
    
    @abstractmethod
    def check_health(self, service_name: str) -> ServiceHealth:
        """检查服务健康状态
        
        Args:
            service_name (str): 服务名称
            
        Returns:
            ServiceHealth: 健康状态
        """
        pass
    
    @abstractmethod
    def start_monitoring(self, service_name: str, check_interval_seconds: int = 30) -> None:
        """开始监控服务
        
        Args:
            service_name (str): 服务名称
            check_interval_seconds (int): 检查间隔(秒)
        """
        pass
    
    @abstractmethod
    def stop_monitoring(self, service_name: str) -> None:
        """停止监控服务
        
        Args:
            service_name (str): 服务名称
        """
        pass
    
    @abstractmethod
    def get_all_health_status(self) -> Dict[str, ServiceHealth]:
        """获取所有服务健康状态
        
        Returns:
            Dict[str, ServiceHealth]: 所有服务的健康状态
        """
        pass
    
    @abstractmethod
    def register_health_check_endpoint(self, service_name: str, endpoint: Callable) -> None:
        """注册健康检查端点
        
        Args:
            service_name (str): 服务名称
            endpoint (Callable): 健康检查函数
        """
        pass


class IResilientServiceFactory(ABC):
    """弹性服务工厂接口
    
    用于创建和配置各种弹性服务组件。
    """
    
    @abstractmethod
    def create_circuit_breaker(self, 
                             failure_threshold: int = 5,
                             recovery_timeout: int = 60,
                             half_open_max_calls: int = 3) -> ICircuitBreaker:
        """创建断路器
        
        Args:
            failure_threshold (int): 失败阈值
            recovery_timeout (int): 恢复超时(秒)
            half_open_max_calls (int): 半开状态最大调用数
            
        Returns:
            ICircuitBreaker: 断路器实例
        """
        pass
    
    @abstractmethod
    def create_rate_limiter(self, permits_per_second: float, burst_capacity: Optional[int] = None) -> IRateLimiter:
        """创建速率限制器
        
        Args:
            permits_per_second (float): 每秒允许请求数
            burst_capacity (Optional[int]): 突发容量
            
        Returns:
            IRateLimiter: 速率限制器实例
        """
        pass
    
    @abstractmethod
    def create_retry_handler(self, default_policy: Optional[RetryPolicy] = None) -> IRetryHandler:
        """创建重试处理器
        
        Args:
            default_policy (Optional[RetryPolicy]): 默认重试策略
            
        Returns:
            IRetryHandler: 重试处理器实例
        """
        pass
    
    @abstractmethod
    def create_fallback_handler(self, cache_config: Optional[Dict[str, Any]] = None) -> IFallbackHandler:
        """创建降级处理器
        
        Args:
            cache_config (Optional[Dict[str, Any]]): 缓存配置
            
        Returns:
            IFallbackHandler: 降级处理器实例
        """
        pass
    
    @abstractmethod
    def create_health_checker(self) -> IHealthChecker:
        """创建健康检查器
        
        Returns:
            IHealthChecker: 健康检查器实例
        """
        pass
    
    @abstractmethod
    def create_resilient_service(self, 
                               service_name: str,
                               circuit_breaker: Optional[ICircuitBreaker] = None,
                               rate_limiter: Optional[IRateLimiter] = None,
                               retry_handler: Optional[IRetryHandler] = None,
                               fallback_handler: Optional[IFallbackHandler] = None,
                               health_checker: Optional[IHealthChecker] = None) -> IResilientService:
        """创建弹性服务
        
        Args:
            service_name (str): 服务名称
            circuit_breaker (Optional[ICircuitBreaker]): 断路器
            rate_limiter (Optional[IRateLimiter]): 速率限制器
            retry_handler (Optional[IRetryHandler]): 重试处理器
            fallback_handler (Optional[IFallbackHandler]): 降级处理器
            health_checker (Optional[IHealthChecker]): 健康检查器
            
        Returns:
            IResilientService: 弹性服务实例
        """
        pass