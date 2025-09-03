"""
缓存管理器 - 多层缓存系统
"""

import time
import json
import pickle
import threading
from typing import Any, Optional, Dict, Callable
from pathlib import Path
from dataclasses import dataclass

@dataclass
class CacheConfig:
    memory_ttl: int = 300        # 内存缓存TTL(秒)
    disk_ttl: int = 3600         # 磁盘缓存TTL(秒) 
    max_memory_items: int = 1000 # 内存缓存最大条目数
    cache_dir: str = "cache"     # 缓存目录

class CacheManager:
    """多层缓存管理器"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.memory_cache: Dict[str, tuple] = {}  # (value, expire_time)
        self.cache_dir = Path(config.cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self._lock = threading.RLock()
        
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        # 1. 尝试内存缓存
        memory_value = self._get_from_memory(key)
        if memory_value is not None:
            return memory_value
            
        # 2. 尝试磁盘缓存
        disk_value = self._get_from_disk(key)
        if disk_value is not None:
            # 重新放入内存缓存
            self._put_to_memory(key, disk_value, self.config.memory_ttl)
            return disk_value
            
        return None
        
    def put(self, key: str, value: Any, ttl: Optional[int] = None):
        """存储缓存值"""
        memory_ttl = ttl or self.config.memory_ttl
        disk_ttl = ttl or self.config.disk_ttl
        
        # 存储到内存缓存
        self._put_to_memory(key, value, memory_ttl)
        
        # 存储到磁盘缓存  
        self._put_to_disk(key, value, disk_ttl)
        
    def _get_from_memory(self, key: str) -> Optional[Any]:
        """从内存获取"""
        with self._lock:
            if key in self.memory_cache:
                value, expire_time = self.memory_cache[key]
                
                if time.time() < expire_time:
                    return value
                else:
                    # 已过期，删除
                    del self.memory_cache[key]
                    
        return None
        
    def _put_to_memory(self, key: str, value: Any, ttl: int):
        """存储到内存"""
        with self._lock:
            # 检查是否需要清理空间
            if len(self.memory_cache) >= self.config.max_memory_items:
                self._evict_expired_memory()
                
                # 如果还是满的，删除最老的条目
                if len(self.memory_cache) >= self.config.max_memory_items:
                    oldest_key = min(self.memory_cache.keys(), 
                                   key=lambda k: self.memory_cache[k][1])
                    del self.memory_cache[oldest_key]
                    
            expire_time = time.time() + ttl
            self.memory_cache[key] = (value, expire_time)
            
    def _get_from_disk(self, key: str) -> Optional[Any]:
        """从磁盘获取"""
        cache_file = self.cache_dir / f"{key}.cache"
        
        try:
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                    
                value, expire_time = cached_data
                
                if time.time() < expire_time:
                    return value
                else:
                    # 已过期，删除文件
                    cache_file.unlink(missing_ok=True)
                    
        except Exception as e:
            # 缓存文件损坏，删除它
            cache_file.unlink(missing_ok=True)
            
        return None
        
    def _put_to_disk(self, key: str, value: Any, ttl: int):
        """存储到磁盘"""
        cache_file = self.cache_dir / f"{key}.cache"
        
        try:
            expire_time = time.time() + ttl
            cached_data = (value, expire_time)
            
            with open(cache_file, 'wb') as f:
                pickle.dump(cached_data, f)
                
        except Exception as e:
            # 序列化失败，忽略磁盘缓存
            pass
            
    def _evict_expired_memory(self):
        """清理过期的内存缓存"""
        current_time = time.time()
        expired_keys = []
        
        for key, (value, expire_time) in self.memory_cache.items():
            if current_time >= expire_time:
                expired_keys.append(key)
                
        for key in expired_keys:
            del self.memory_cache[key]
            
    def clear(self):
        """清空所有缓存"""
        with self._lock:
            self.memory_cache.clear()
            
        # 清空磁盘缓存
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink(missing_ok=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            memory_count = len(self.memory_cache)
            
        disk_count = len(list(self.cache_dir.glob("*.cache")))
        
        return {
            "memory_items": memory_count,
            "disk_items": disk_count,
            "memory_capacity": self.config.max_memory_items,
            "cache_dir": str(self.cache_dir)
        }