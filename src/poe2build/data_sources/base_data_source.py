"""
数据源基类 - 定义统一接口和通用功能
"""

import logging
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum

from ..resilience import (
    ResilientService, 
    PoE2FallbackProvider,
    CacheManager,
    CacheConfig
)

logger = logging.getLogger(__name__)

class DataSourceStatus(Enum):
    """数据源状态枚举"""
    ACTIVE = "active"           # 正常工作
    DEGRADED = "degraded"       # 降级模式
    UNAVAILABLE = "unavailable" # 不可用
    MAINTENANCE = "maintenance" # 维护中

class BaseDataSource(ABC):
    """数据源抽象基类"""
    
    def __init__(self, 
                 source_name: str,
                 resilient_service: Optional[ResilientService] = None,
                 fallback_provider: Optional[PoE2FallbackProvider] = None):
        """
        初始化数据源基类
        
        Args:
            source_name: 数据源名称
            resilient_service: 弹性服务包装器
            fallback_provider: 降级服务提供者
        """
        self.source_name = source_name
        self.resilient_service = resilient_service
        self.fallback_provider = fallback_provider
        self.status = DataSourceStatus.ACTIVE
        self.last_error = None
        
        # 初始化独立缓存管理器（如果没有弹性服务）
        if not resilient_service:
            cache_config = CacheConfig(
                memory_ttl=300,
                disk_ttl=1800,
                cache_dir=f"cache/{source_name}"
            )
            self.cache_manager = CacheManager(cache_config)
        else:
            self.cache_manager = resilient_service.cache_manager
        
    @abstractmethod
    def get_market_data(self, league: str = "Standard", **kwargs) -> Dict[str, Any]:
        """获取市场数据"""
        pass
        
    @abstractmethod
    def get_build_data(self, class_name: str = None, **kwargs) -> Dict[str, Any]:
        """获取构筑数据"""
        pass
        
    @abstractmethod
    def get_item_data(self, item_name: str = None, **kwargs) -> Dict[str, Any]:
        """获取物品数据"""
        pass
        
    @abstractmethod
    def health_check(self) -> bool:
        """健康检查"""
        pass
        
    def _make_resilient_call(self, 
                           func_name: str, 
                           func, 
                           cache_key: str = None,
                           *args, **kwargs) -> Dict[str, Any]:
        """
        执行弹性调用
        
        Args:
            func_name: 函数名（用于降级）
            func: 要执行的函数
            cache_key: 缓存键
            *args, **kwargs: 函数参数
            
        Returns:
            调用结果
        """
        try:
            if self.resilient_service:
                # 使用弹性服务执行调用
                result = self.resilient_service.call(
                    func, *args, cache_key=cache_key, **kwargs
                )
            else:
                # 检查缓存
                if cache_key and self.cache_manager:
                    cached_result = self.cache_manager.get(cache_key)
                    if cached_result is not None:
                        return cached_result
                
                # 直接调用
                result = func(*args, **kwargs)
                
                # 缓存结果
                if cache_key and self.cache_manager:
                    self.cache_manager.put(cache_key, result)
                    
            self.status = DataSourceStatus.ACTIVE
            self.last_error = None
            return result
            
        except Exception as e:
            logger.error(f"Error in {self.source_name}.{func_name}: {e}")
            self.last_error = str(e)
            self.status = DataSourceStatus.DEGRADED
            
            # 尝试使用降级服务
            if self.fallback_provider:
                try:
                    fallback_result = self.fallback_provider.provide_fallback(
                        self.source_name, func_name, *args, **kwargs
                    )
                    fallback_result["source_status"] = "fallback"
                    return fallback_result
                except Exception as fallback_error:
                    logger.error(f"Fallback failed for {self.source_name}.{func_name}: {fallback_error}")
            
            # 如果没有降级服务或降级失败，标记为不可用
            self.status = DataSourceStatus.UNAVAILABLE
            raise e
            
    def _generate_cache_key(self, operation: str, **params) -> str:
        """
        生成缓存键
        
        Args:
            operation: 操作名称
            **params: 参数
            
        Returns:
            缓存键字符串
        """
        # 创建参数的确定性字符串表示
        param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()) if v is not None)
        
        # 生成MD5哈希以避免键过长
        key_material = f"{self.source_name}:{operation}:{param_str}"
        cache_key = hashlib.md5(key_material.encode()).hexdigest()
        
        return cache_key
        
    def get_status_info(self) -> Dict[str, Any]:
        """
        获取数据源状态信息
        
        Returns:
            状态信息字典
        """
        info = {
            "name": self.source_name,
            "status": self.status.value,
            "last_error": self.last_error
        }
        
        # 添加缓存统计信息
        if self.cache_manager:
            info["cache_stats"] = self.cache_manager.get_stats()
            
        # 添加弹性服务信息
        if self.resilient_service:
            info["resilience"] = {
                "circuit_breaker_state": (
                    self.resilient_service.circuit_breaker.state.value 
                    if self.resilient_service.circuit_breaker else None
                ),
                "rate_limiter_active": self.resilient_service.rate_limiter is not None,
                "retry_handler_active": self.resilient_service.retry_handler is not None,
                "cache_manager_active": self.resilient_service.cache_manager is not None
            }
            
        return info
        
    def clear_cache(self):
        """清空缓存"""
        if self.cache_manager:
            self.cache_manager.clear()
            logger.info(f"Cache cleared for {self.source_name}")
        
    def _validate_response(self, response: Dict[str, Any], required_fields: List[str] = None) -> bool:
        """
        验证响应数据
        
        Args:
            response: 响应数据
            required_fields: 必需字段列表
            
        Returns:
            验证是否通过
        """
        if not isinstance(response, dict):
            return False
            
        if required_fields:
            for field in required_fields:
                if field not in response:
                    logger.warning(f"Missing required field '{field}' in {self.source_name} response")
                    return False
                    
        return True
        
    def _standardize_response(self, 
                            data: Any, 
                            operation: str,
                            metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        标准化响应格式
        
        Args:
            data: 响应数据
            operation: 操作类型
            metadata: 额外元数据
            
        Returns:
            标准化的响应
        """
        response = {
            "source": self.source_name,
            "operation": operation,
            "status": "success",
            "data": data,
            "timestamp": self._get_current_timestamp(),
            "metadata": metadata or {}
        }
        
        # 添加状态信息
        response["metadata"]["source_status"] = self.status.value
        
        return response
        
    def _get_current_timestamp(self) -> int:
        """获取当前时间戳"""
        import time
        return int(time.time())
        
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.source_name}', status='{self.status.value}')"