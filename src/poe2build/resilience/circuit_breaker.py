"""断路器模式实现 - 防止级联故障"""

import time
import threading
import logging
from enum import Enum
from typing import Callable, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class CircuitBreakerState(Enum):
    """断路器状态"""
    CLOSED = "closed"      # 正常状态，允许请求通过
    OPEN = "open"          # 断开状态，拒绝所有请求
    HALF_OPEN = "half_open"  # 半开状态，允许部分请求测试服务

@dataclass
class CircuitBreakerConfig:
    """断路器配置"""
    failure_threshold: int = 5           # 失败阈值
    recovery_timeout: float = 60.0       # 恢复超时时间(秒)
    expected_exception: type = Exception # 预期的异常类型
    fallback_function: Optional[Callable] = None

class CircuitBreaker:
    """断路器实现 - 防止级联故障"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        self._lock = threading.RLock()
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """执行被保护的函数调用"""
        with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info("Circuit breaker moved to HALF_OPEN state")
                else:
                    return self._call_fallback(func, *args, **kwargs)
                    
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
                
            except self.config.expected_exception as e:
                self._on_failure()
                if self.config.fallback_function:
                    return self.config.fallback_function(*args, **kwargs)
                raise e
                
    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置断路器"""
        return (self.last_failure_time and 
                time.time() - self.last_failure_time >= self.config.recovery_timeout)
                
    def _on_success(self):
        """成功调用处理"""
        if self.failure_count > 0 or self.state != CircuitBreakerState.CLOSED:
            logger.info("Circuit breaker reset - service recovered")
            
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
        
    def _on_failure(self):
        """失败调用处理"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        logger.warning(f"Circuit breaker failure count: {self.failure_count}")
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.error(f"Circuit breaker opened - threshold {self.config.failure_threshold} reached")
            
    def _call_fallback(self, func: Callable, *args, **kwargs) -> Any:
        """调用降级函数"""
        if self.config.fallback_function:
            logger.info("Using fallback function due to open circuit breaker")
            return self.config.fallback_function(*args, **kwargs)
        raise RuntimeError(f"Circuit breaker is OPEN for {func.__name__}")
        
    def get_state(self) -> CircuitBreakerState:
        """获取当前状态"""
        return self.state
        
    def get_failure_count(self) -> int:
        """获取失败次数"""
        return self.failure_count
        
    def reset(self):
        """手动重置断路器"""
        with self._lock:
            self.failure_count = 0
            self.last_failure_time = None
            self.state = CircuitBreakerState.CLOSED
            logger.info("Circuit breaker manually reset")

class CircuitBreakerDecorator:
    """断路器装饰器"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.circuit_breaker = CircuitBreaker(config)
        
    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            return self.circuit_breaker.call(func, *args, **kwargs)
        return wrapper

# 便利函数
def create_circuit_breaker(failure_threshold: int = 5, 
                          recovery_timeout: float = 60.0,
                          fallback_function: Optional[Callable] = None) -> CircuitBreaker:
    """创建断路器实例"""
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        fallback_function=fallback_function
    )
    return CircuitBreaker(config)

def circuit_breaker(failure_threshold: int = 5,
                   recovery_timeout: float = 60.0,
                   fallback_function: Optional[Callable] = None):
    """断路器装饰器"""
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        fallback_function=fallback_function
    )
    return CircuitBreakerDecorator(config)