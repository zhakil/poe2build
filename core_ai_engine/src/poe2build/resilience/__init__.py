"""PoE2 Build Generator - Resilience System"""

from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerConfig,
    create_circuit_breaker,
    circuit_breaker
)

from .rate_limiter import (
    RateLimiter,
    PoE2RateLimiters,
    create_rate_limiter
)

from .retry_handler import (
    RetryHandler,
    RetryConfig,
    retry_with_backoff
)

from .cache_manager import (
    CacheManager,
    CacheConfig
)

from .fallback_provider import (
    FallbackProvider,
    PoE2FallbackProvider
)

class ResilientService:
    """弹性服务包装器 - 集成所有弹性模式"""
    
    def __init__(self, 
                 service_name: str,
                 circuit_breaker_config: CircuitBreakerConfig = None,
                 retry_config: RetryConfig = None,
                 cache_config: CacheConfig = None,
                 rate_limit_rps: float = None):
                 
        self.service_name = service_name
        
        # 初始化各种弹性组件
        if circuit_breaker_config:
            self.circuit_breaker = CircuitBreaker(circuit_breaker_config)
        else:
            self.circuit_breaker = None
            
        if retry_config:
            self.retry_handler = RetryHandler(retry_config)
        else:
            self.retry_handler = None
            
        if cache_config:
            self.cache_manager = CacheManager(cache_config)
        else:
            self.cache_manager = None
            
        if rate_limit_rps:
            self.rate_limiter = RateLimiter()
            self.rate_limiter.add_limit(service_name, rate_limit_rps)
        else:
            self.rate_limiter = None
            
    def call(self, func, *args, cache_key: str = None, **kwargs):
        """执行弹性调用"""
        
        # 1. 检查缓存
        if cache_key and self.cache_manager:
            cached_result = self.cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
                
        # 2. 检查速率限制
        if self.rate_limiter:
            if not self.rate_limiter.wait_for_token(self.service_name, timeout=5.0):
                raise RuntimeError(f"Rate limit exceeded for {self.service_name}")
                
        # 3. 定义执行函数
        def execute():
            if self.circuit_breaker:
                return self.circuit_breaker.call(func, *args, **kwargs)
            else:
                return func(*args, **kwargs)
                
        # 4. 应用重试
        if self.retry_handler:
            result = self.retry_handler.execute(execute)
        else:
            result = execute()
            
        # 5. 缓存结果
        if cache_key and self.cache_manager:
            self.cache_manager.put(cache_key, result)
            
        return result

# 预配置的弹性服务实例
def create_poe2_scout_service() -> ResilientService:
    """创建PoE2 Scout服务的弹性包装器"""
    return ResilientService(
        service_name="poe2_scout",
        circuit_breaker_config=CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=60.0
        ),
        retry_config=RetryConfig(
            max_attempts=3,
            base_delay=2.0,
            backoff_factor=2.0
        ),
        cache_config=CacheConfig(
            memory_ttl=300,    # 5分钟内存缓存
            disk_ttl=1800      # 30分钟磁盘缓存
        ),
        rate_limit_rps=0.5     # 每2秒1个请求
    )

def create_poe2db_service() -> ResilientService:
    """创建PoE2DB服务的弹性包装器"""  
    return ResilientService(
        service_name="poe2db",
        circuit_breaker_config=CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=30.0
        ),
        retry_config=RetryConfig(
            max_attempts=2,
            base_delay=1.0,
            backoff_factor=1.5
        ),
        cache_config=CacheConfig(
            memory_ttl=600,    # 10分钟内存缓存
            disk_ttl=3600      # 1小时磁盘缓存
        ),
        rate_limit_rps=1.0     # 每秒1个请求
    )

def create_poe_ninja_service() -> ResilientService:
    """创建poe.ninja服务的弹性包装器"""
    return ResilientService(
        service_name="poe_ninja", 
        circuit_breaker_config=CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=120.0
        ),
        retry_config=RetryConfig(
            max_attempts=3,
            base_delay=3.0,
            backoff_factor=3.0
        ),
        cache_config=CacheConfig(
            memory_ttl=900,    # 15分钟内存缓存
            disk_ttl=7200      # 2小时磁盘缓存
        ),
        rate_limit_rps=0.2     # 每5秒1个请求
    )

__all__ = [
    'ResilientService',
    'CircuitBreaker', 
    'CircuitBreakerState',
    'CircuitBreakerConfig',
    'RateLimiter',
    'RetryHandler',
    'RetryConfig', 
    'CacheManager',
    'CacheConfig',
    'FallbackProvider',
    'PoE2FallbackProvider',
    'create_poe2_scout_service',
    'create_poe2db_service',
    'create_poe_ninja_service'
]