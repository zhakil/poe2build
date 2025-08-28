"""基础数据提供者实现 - 包含弹性机制"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

import aiohttp
import hashlib
from datetime import datetime, timedelta

from .interfaces import (
    IDataProvider, DataProviderStatus, DataProviderException,
    RateLimitException, ConnectionException, ICacheProvider
)


class CircuitBreakerState(Enum):
    """熔断器状态枚举"""
    CLOSED = "closed"      # 正常状态
    OPEN = "open"          # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5          # 失败阈值
    recovery_timeout: int = 60          # 恢复超时(秒)
    expected_recovery_time: int = 30    # 预期恢复时间
    monitoring_period: int = 300        # 监控周期(秒)


@dataclass
class RateLimitConfig:
    """速率限制配置"""
    requests_per_minute: int = 30
    requests_per_hour: int = 1000
    backoff_factor: float = 2.0
    max_backoff: int = 300  # 最大退避时间(秒)


@dataclass
class CacheConfig:
    """缓存配置"""
    default_ttl: int = 600      # 默认TTL(秒)
    market_data_ttl: int = 600   # 市场数据TTL
    build_data_ttl: int = 1800   # 构筑数据TTL  
    game_data_ttl: int = 3600    # 游戏数据TTL
    enable_compression: bool = True


class CircuitBreaker:
    """熔断器实现"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.next_attempt_time = None
        self._logger = logging.getLogger(f"{__name__}.CircuitBreaker")
    
    async def call(self, func: Callable, *args, **kwargs):
        """通过熔断器调用函数"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self._logger.info("熔断器进入半开状态")
            else:
                raise ConnectionException(
                    f"熔断器开启状态，下次尝试时间: {self.next_attempt_time}"
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置"""
        return (self.next_attempt_time and 
                datetime.now() >= self.next_attempt_time)
    
    def _on_success(self):
        """成功回调"""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
        self.next_attempt_time = None
        self._logger.info("熔断器重置为闭合状态")
    
    def _on_failure(self):
        """失败回调"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.next_attempt_time = (
                datetime.now() + timedelta(seconds=self.config.recovery_timeout)
            )
            self._logger.warning(
                f"熔断器打开，失败次数: {self.failure_count}, "
                f"恢复时间: {self.next_attempt_time}"
            )


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests_minute = []
        self.requests_hour = []
        self.last_request_time = None
        self._logger = logging.getLogger(f"{__name__}.RateLimiter")
    
    async def acquire(self):
        """获取请求许可"""
        now = time.time()
        
        # 清理过期的请求记录
        self._cleanup_old_requests(now)
        
        # 检查分钟限制
        if len(self.requests_minute) >= self.config.requests_per_minute:
            wait_time = 60 - (now - self.requests_minute[0])
            if wait_time > 0:
                self._logger.warning(f"分钟速率限制，等待 {wait_time:.1f} 秒")
                raise RateLimitException(
                    f"分钟速率限制已达上限，请等待 {wait_time:.1f} 秒",
                    retry_after=int(wait_time) + 1
                )
        
        # 检查小时限制
        if len(self.requests_hour) >= self.config.requests_per_hour:
            wait_time = 3600 - (now - self.requests_hour[0])
            if wait_time > 0:
                self._logger.warning(f"小时速率限制，等待 {wait_time:.1f} 秒")
                raise RateLimitException(
                    f"小时速率限制已达上限，请等待 {wait_time/60:.1f} 分钟",
                    retry_after=int(wait_time/60) + 1
                )
        
        # 指数退避
        if self.last_request_time:
            time_since_last = now - self.last_request_time
            min_interval = 60.0 / self.config.requests_per_minute
            if time_since_last < min_interval:
                wait_time = min_interval - time_since_last
                await asyncio.sleep(wait_time)
        
        # 记录请求
        self.requests_minute.append(now)
        self.requests_hour.append(now)
        self.last_request_time = now
    
    def _cleanup_old_requests(self, now: float):
        """清理过期的请求记录"""
        # 清理分钟记录
        self.requests_minute = [
            req_time for req_time in self.requests_minute 
            if now - req_time < 60
        ]
        
        # 清理小时记录  
        self.requests_hour = [
            req_time for req_time in self.requests_hour
            if now - req_time < 3600
        ]


class SimpleMemoryCache:
    """简单内存缓存实现"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._logger = logging.getLogger(f"{__name__}.SimpleMemoryCache")
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if self._is_expired(entry):
            del self._cache[key]
            return None
        
        self._logger.debug(f"缓存命中: {key}")
        return entry['value']
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            expires_at = time.time() + (ttl or self.config.default_ttl)
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': time.time()
            }
            self._logger.debug(f"缓存设置: {key}, TTL: {ttl or self.config.default_ttl}")
            return True
        except Exception as e:
            self._logger.error(f"缓存设置失败: {key}, 错误: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        if key in self._cache:
            del self._cache[key]
            self._logger.debug(f"缓存删除: {key}")
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if key not in self._cache:
            return False
        return not self._is_expired(self._cache[key])
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        count = 0
        keys_to_delete = []
        
        for key in self._cache.keys():
            if pattern in key:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self._cache[key]
            count += 1
        
        self._logger.info(f"清除缓存模式 '{pattern}': {count} 个条目")
        return count
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """检查缓存条目是否过期"""
        return time.time() > entry['expires_at']
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total = len(self._cache)
        expired = sum(1 for entry in self._cache.values() if self._is_expired(entry))
        
        return {
            'total_entries': total,
            'expired_entries': expired,
            'valid_entries': total - expired,
            'memory_usage': f"~{len(str(self._cache))} bytes"
        }


class BaseProvider(IDataProvider):
    """基础数据提供者实现"""
    
    def __init__(self, 
                 name: str,
                 base_url: str,
                 circuit_config: Optional[CircuitBreakerConfig] = None,
                 rate_config: Optional[RateLimitConfig] = None,
                 cache_config: Optional[CacheConfig] = None,
                 session_config: Optional[Dict[str, Any]] = None):
        
        self.name = name
        self.base_url = base_url.rstrip('/')
        
        # 配置组件
        self.circuit_breaker = CircuitBreaker(circuit_config or CircuitBreakerConfig())
        self.rate_limiter = RateLimiter(rate_config or RateLimitConfig())
        self.cache = SimpleMemoryCache(cache_config or CacheConfig())
        
        # HTTP会话配置
        self.session_config = session_config or {}
        self.session_config.setdefault('timeout', aiohttp.ClientTimeout(total=30))
        self.session_config.setdefault('headers', {})
        self.session_config['headers'].setdefault('User-Agent', 
            'PoE2BuildGenerator/2.0 (github.com/zhakil/poe2build)')
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._logger = logging.getLogger(f"{__name__}.{name}")
        
        # 统计信息
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'last_request_time': None,
            'start_time': datetime.now()
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(**self.session_config)
        return self._session
    
    async def close(self):
        """关闭资源"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def get_health_status(self) -> DataProviderStatus:
        """获取健康状态"""
        try:
            is_connected = await self.test_connection()
            
            if self.circuit_breaker.state == CircuitBreakerState.OPEN:
                return DataProviderStatus.OFFLINE
            elif self.circuit_breaker.state == CircuitBreakerState.HALF_OPEN:
                return DataProviderStatus.DEGRADED
            elif is_connected:
                return DataProviderStatus.HEALTHY
            else:
                return DataProviderStatus.UNHEALTHY
                
        except Exception as e:
            self._logger.error(f"健康检查失败: {e}")
            return DataProviderStatus.OFFLINE
    
    async def test_connection(self) -> bool:
        """测试连接"""
        try:
            session = await self._get_session()
            async with session.head(self.base_url) as response:
                return response.status < 500
        except Exception as e:
            self._logger.error(f"连接测试失败: {e}")
            return False
    
    def get_provider_name(self) -> str:
        """获取提供者名称"""
        return self.name
    
    def get_rate_limit_info(self) -> Dict[str, int]:
        """获取速率限制信息"""
        return {
            'requests_per_minute': self.rate_limiter.config.requests_per_minute,
            'requests_per_hour': self.rate_limiter.config.requests_per_hour,
            'current_minute_requests': len(self.rate_limiter.requests_minute),
            'current_hour_requests': len(self.rate_limiter.requests_hour)
        }
    
    async def _make_request(self, 
                           method: str, 
                           url: str, 
                           cache_key: Optional[str] = None,
                           cache_ttl: Optional[int] = None,
                           **kwargs) -> Any:
        """发起HTTP请求（带缓存和弹性机制）"""
        
        # 检查缓存
        if cache_key:
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                self.stats['cache_hits'] += 1
                return cached_result
            self.stats['cache_misses'] += 1
        
        # 准备请求
        full_url = url if url.startswith('http') else f"{self.base_url}{url}"
        
        # 通过弹性机制执行请求
        result = await self.circuit_breaker.call(self._execute_request, method, full_url, **kwargs)
        
        # 缓存结果
        if cache_key and result is not None:
            await self.cache.set(cache_key, result, cache_ttl)
        
        return result
    
    async def _execute_request(self, method: str, url: str, **kwargs) -> Any:
        """执行HTTP请求"""
        # 速率限制
        await self.rate_limiter.acquire()
        
        # 更新统计
        self.stats['total_requests'] += 1
        self.stats['last_request_time'] = datetime.now()
        
        try:
            session = await self._get_session()
            self._logger.debug(f"请求: {method} {url}")
            
            async with session.request(method, url, **kwargs) as response:
                if response.status == 429:
                    retry_after = response.headers.get('Retry-After', '60')
                    raise RateLimitException(
                        f"API速率限制: {response.status}",
                        retry_after=int(retry_after),
                        provider_name=self.name
                    )
                
                if response.status >= 500:
                    raise ConnectionException(
                        f"服务器错误: {response.status}",
                        provider_name=self.name
                    )
                
                if response.status >= 400:
                    error_text = await response.text()
                    raise DataProviderException(
                        f"客户端错误: {response.status} - {error_text}",
                        provider_name=self.name,
                        error_code=str(response.status)
                    )
                
                # 成功响应
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    result = await response.json()
                else:
                    result = await response.text()
                
                self.stats['successful_requests'] += 1
                return result
                
        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            self.stats['failed_requests'] += 1
            raise ConnectionException(
                f"请求失败: {str(e)}",
                provider_name=self.name
            )
        except Exception as e:
            self.stats['failed_requests'] += 1
            if not isinstance(e, DataProviderException):
                raise DataProviderException(
                    f"未知错误: {str(e)}",
                    provider_name=self.name
                )
            raise
    
    def _generate_cache_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """生成缓存键"""
        # 创建参数的哈希
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        return f"{self.name}:{prefix}:{params_hash}"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        uptime = datetime.now() - self.stats['start_time']
        success_rate = 0
        if self.stats['total_requests'] > 0:
            success_rate = (self.stats['successful_requests'] / self.stats['total_requests']) * 100
        
        cache_hit_rate = 0
        total_cache_ops = self.stats['cache_hits'] + self.stats['cache_misses']
        if total_cache_ops > 0:
            cache_hit_rate = (self.stats['cache_hits'] / total_cache_ops) * 100
        
        return {
            'provider_name': self.name,
            'uptime_seconds': uptime.total_seconds(),
            'health_status': self.circuit_breaker.state.value,
            'total_requests': self.stats['total_requests'],
            'success_rate': f"{success_rate:.1f}%",
            'cache_hit_rate': f"{cache_hit_rate:.1f}%",
            'rate_limit_status': self.get_rate_limit_info(),
            'circuit_breaker_failures': self.circuit_breaker.failure_count,
            'last_request_time': self.stats['last_request_time']
        }