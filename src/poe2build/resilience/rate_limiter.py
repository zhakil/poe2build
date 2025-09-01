"""速率限制器实现 - 令牌桶算法"""

import time
import threading
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """速率限制配置"""
    requests_per_second: float
    burst_capacity: Optional[int] = None
    
    def __post_init__(self):
        if self.burst_capacity is None:
            self.burst_capacity = max(1, int(self.requests_per_second * 2))

class TokenBucket:
    """令牌桶实现"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity          # 桶容量
        self.refill_rate = refill_rate   # 每秒补充令牌数
        self.tokens = float(capacity)    # 当前令牌数
        self.last_refill = time.time()   # 上次补充时间
        self._lock = threading.RLock()
        
    def consume(self, tokens: int = 1) -> bool:
        """消费令牌"""
        with self._lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
            
    def _refill(self):
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now
        
    def get_available_tokens(self) -> float:
        """获取可用令牌数"""
        with self._lock:
            self._refill()
            return self.tokens

class RateLimiter:
    """速率限制器 - 管理多个服务的速率限制"""
    
    def __init__(self):
        self.buckets: Dict[str, TokenBucket] = {}
        self._lock = threading.RLock()
        
    def add_limit(self, service: str, requests_per_second: float, 
                  burst_capacity: int = None):
        """为服务添加速率限制"""
        if burst_capacity is None:
            burst_capacity = max(1, int(requests_per_second * 2))
            
        with self._lock:
            self.buckets[service] = TokenBucket(
                capacity=burst_capacity,
                refill_rate=requests_per_second
            )
            
        logger.info(f"Added rate limit for {service}: {requests_per_second} req/s, burst: {burst_capacity}")
            
    def allow_request(self, service: str, tokens: int = 1) -> bool:
        """检查是否允许请求"""
        bucket = self.buckets.get(service)
        if not bucket:
            return True  # 未设置限制，允许请求
            
        allowed = bucket.consume(tokens)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for service: {service}")
            
        return allowed
        
    def wait_for_token(self, service: str, timeout: float = 10.0) -> bool:
        """等待令牌可用"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.allow_request(service):
                return True
            time.sleep(0.1)  # 短暂等待
            
        logger.error(f"Timeout waiting for token for service: {service}")
        return False
        
    def get_limit_info(self, service: str) -> Dict:
        """获取限制信息"""
        bucket = self.buckets.get(service)
        if not bucket:
            return {"service": service, "limited": False}
            
        return {
            "service": service,
            "limited": True,
            "capacity": bucket.capacity,
            "refill_rate": bucket.refill_rate,
            "available_tokens": bucket.get_available_tokens()
        }
        
    def remove_limit(self, service: str):
        """移除服务限制"""
        with self._lock:
            if service in self.buckets:
                del self.buckets[service]
                logger.info(f"Removed rate limit for service: {service}")

class SlidingWindowRateLimiter:
    """滑动窗口速率限制器"""
    
    def __init__(self, window_size: int = 60, max_requests: int = 100):
        self.window_size = window_size  # 窗口大小(秒)
        self.max_requests = max_requests
        self.requests: Dict[str, list] = {}
        self._lock = threading.RLock()
        
    def allow_request(self, service: str) -> bool:
        """检查是否允许请求"""
        current_time = time.time()
        
        with self._lock:
            if service not in self.requests:
                self.requests[service] = []
                
            # 清理过期请求
            self.requests[service] = [
                req_time for req_time in self.requests[service]
                if current_time - req_time <= self.window_size
            ]
            
            # 检查是否超过限制
            if len(self.requests[service]) >= self.max_requests:
                logger.warning(f"Sliding window rate limit exceeded for {service}")
                return False
                
            # 添加当前请求
            self.requests[service].append(current_time)
            return True
            
    def get_request_count(self, service: str) -> int:
        """获取当前窗口内的请求数"""
        current_time = time.time()
        
        with self._lock:
            if service not in self.requests:
                return 0
                
            # 清理过期请求并返回数量
            valid_requests = [
                req_time for req_time in self.requests[service]
                if current_time - req_time <= self.window_size
            ]
            self.requests[service] = valid_requests
            return len(valid_requests)

# PoE2专用速率限制器配置
class PoE2RateLimiters:
    """PoE2数据源专用速率限制器"""
    
    @staticmethod
    def create_poe2_scout_limiter() -> RateLimiter:
        """创建PoE2 Scout专用限制器"""
        limiter = RateLimiter()
        limiter.add_limit("poe2scout", requests_per_second=0.5, burst_capacity=2)
        return limiter
        
    @staticmethod
    def create_poe2db_limiter() -> RateLimiter:
        """创建PoE2DB专用限制器"""
        limiter = RateLimiter()
        limiter.add_limit("poe2db", requests_per_second=1.0, burst_capacity=3)
        return limiter
        
    @staticmethod
    def create_poe_ninja_limiter() -> RateLimiter:
        """创建poe.ninja专用限制器"""
        limiter = RateLimiter()
        limiter.add_limit("poe_ninja", requests_per_second=0.2, burst_capacity=1)
        return limiter
        
    @staticmethod
    def create_combined_limiter() -> RateLimiter:
        """创建组合限制器，包含所有PoE2数据源"""
        limiter = RateLimiter()
        
        # PoE2 Scout - 每2秒1个请求
        limiter.add_limit("poe2scout", requests_per_second=0.5, burst_capacity=2)
        
        # PoE2DB - 每秒1个请求
        limiter.add_limit("poe2db", requests_per_second=1.0, burst_capacity=3)
        
        # poe.ninja - 每5秒1个请求
        limiter.add_limit("poe_ninja", requests_per_second=0.2, burst_capacity=1)
        
        logger.info("Created combined PoE2 rate limiter with all data sources")
        return limiter

# 装饰器支持
class RateLimitDecorator:
    """速率限制装饰器"""
    
    def __init__(self, rate_limiter: RateLimiter, service: str):
        self.rate_limiter = rate_limiter
        self.service = service
        
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            if not self.rate_limiter.allow_request(self.service):
                raise RuntimeError(f"Rate limit exceeded for service: {self.service}")
            return func(*args, **kwargs)
        return wrapper

def rate_limit(service: str, requests_per_second: float, burst_capacity: int = None):
    """速率限制装饰器"""
    limiter = RateLimiter()
    limiter.add_limit(service, requests_per_second, burst_capacity)
    return RateLimitDecorator(limiter, service)

# 便利函数
def create_rate_limiter(service: str, requests_per_second: float, 
                       burst_capacity: int = None) -> RateLimiter:
    """创建单一服务的速率限制器"""
    limiter = RateLimiter()
    limiter.add_limit(service, requests_per_second, burst_capacity)
    return limiter