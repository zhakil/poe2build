"""数据提供者工厂实现"""

import logging
from typing import Dict, List, Optional, Any, Type
from enum import Enum

from .interfaces import (
    IDataProviderFactory, IMarketProvider, IBuildProvider, 
    IGameDataProvider, ICalculationProvider, DataProviderException
)
from .poe2_scout import PoE2ScoutAPI, MockPoE2ScoutAPI
from .ninja_scraper import NinjaPoE2Scraper, MockNinjaPoE2Scraper


class ProviderType(Enum):
    """数据提供者类型枚举"""
    MARKET = "market"
    BUILD = "build"
    GAME_DATA = "game_data"
    CALCULATION = "calculation"


class DataProviderFactory(IDataProviderFactory):
    """数据提供者工厂实现"""
    
    def __init__(self):
        self._logger = logging.getLogger(f"{__name__}.DataProviderFactory")
        
        # 注册提供者
        self._market_providers: Dict[str, Type[IMarketProvider]] = {
            'poe2scout': PoE2ScoutAPI,
            'mock_poe2scout': MockPoE2ScoutAPI
        }
        
        self._build_providers: Dict[str, Type[IBuildProvider]] = {
            'ninja_poe2': NinjaPoE2Scraper,
            'mock_ninja_poe2': MockNinjaPoE2Scraper
        }
        
        self._game_data_providers: Dict[str, Type[IGameDataProvider]] = {
            # 将在后续阶段添加 PoE2DB等
        }
        
        # 导入PoB2计算提供者
        from ..pob2.calculator import PoB2Calculator
        
        self._calculation_providers: Dict[str, Type[ICalculationProvider]] = {
            'pob2_calculator': PoB2Calculator
        }
        
        # 缓存已创建的提供者实例
        self._provider_cache: Dict[str, Any] = {}
    
    def create_market_provider(self, provider_name: str) -> IMarketProvider:
        """创建市场数据提供者"""
        if provider_name not in self._market_providers:
            available = ", ".join(self._market_providers.keys())
            raise DataProviderException(
                f"未知的市场数据提供者: {provider_name}. 可用提供者: {available}"
            )
        
        cache_key = f"market_{provider_name}"
        if cache_key not in self._provider_cache:
            provider_class = self._market_providers[provider_name]
            try:
                self._provider_cache[cache_key] = provider_class()
                self._logger.info(f"创建市场数据提供者: {provider_name}")
            except Exception as e:
                self._logger.error(f"创建市场数据提供者失败 ({provider_name}): {e}")
                # 降级到Mock提供者
                if provider_name != 'mock_poe2scout':
                    self._logger.warning(f"降级到Mock市场数据提供者")
                    self._provider_cache[cache_key] = MockPoE2ScoutAPI()
                else:
                    raise
        
        return self._provider_cache[cache_key]
    
    def create_build_provider(self, provider_name: str) -> IBuildProvider:
        """创建构筑数据提供者"""
        if provider_name not in self._build_providers:
            available = ", ".join(self._build_providers.keys())
            raise DataProviderException(
                f"未知的构筑数据提供者: {provider_name}. 可用提供者: {available}"
            )
        
        cache_key = f"build_{provider_name}"
        if cache_key not in self._provider_cache:
            provider_class = self._build_providers[provider_name]
            try:
                self._provider_cache[cache_key] = provider_class()
                self._logger.info(f"创建构筑数据提供者: {provider_name}")
            except Exception as e:
                self._logger.error(f"创建构筑数据提供者失败 ({provider_name}): {e}")
                # 降级到Mock提供者
                if provider_name != 'mock_ninja_poe2':
                    self._logger.warning(f"降级到Mock构筑数据提供者")
                    self._provider_cache[cache_key] = MockNinjaPoE2Scraper()
                else:
                    raise
        
        return self._provider_cache[cache_key]
    
    def create_game_data_provider(self, provider_name: str) -> IGameDataProvider:
        """创建游戏数据提供者"""
        if provider_name not in self._game_data_providers:
            available = ", ".join(self._game_data_providers.keys()) or "无可用提供者"
            raise DataProviderException(
                f"未知的游戏数据提供者: {provider_name}. 可用提供者: {available}"
            )
        
        cache_key = f"game_data_{provider_name}"
        if cache_key not in self._provider_cache:
            provider_class = self._game_data_providers[provider_name]
            self._provider_cache[cache_key] = provider_class()
            self._logger.info(f"创建游戏数据提供者: {provider_name}")
        
        return self._provider_cache[cache_key]
    
    def create_calculation_provider(self, provider_name: str) -> ICalculationProvider:
        """创建计算提供者"""
        if provider_name not in self._calculation_providers:
            available = ", ".join(self._calculation_providers.keys()) or "无可用提供者"
            raise DataProviderException(
                f"未知的计算提供者: {provider_name}. 可用提供者: {available}"
            )
        
        cache_key = f"calculation_{provider_name}"
        if cache_key not in self._provider_cache:
            provider_class = self._calculation_providers[provider_name]
            self._provider_cache[cache_key] = provider_class()
            self._logger.info(f"创建计算提供者: {provider_name}")
        
        return self._provider_cache[cache_key]
    
    def get_available_providers(self, provider_type: str) -> List[str]:
        """获取可用的提供者列表"""
        try:
            provider_type_enum = ProviderType(provider_type)
        except ValueError:
            return []
        
        if provider_type_enum == ProviderType.MARKET:
            return list(self._market_providers.keys())
        elif provider_type_enum == ProviderType.BUILD:
            return list(self._build_providers.keys())
        elif provider_type_enum == ProviderType.GAME_DATA:
            return list(self._game_data_providers.keys())
        elif provider_type_enum == ProviderType.CALCULATION:
            return list(self._calculation_providers.keys())
        else:
            return []
    
    def register_market_provider(self, name: str, provider_class: Type[IMarketProvider]):
        """注册市场数据提供者"""
        self._market_providers[name] = provider_class
        self._logger.info(f"注册市场数据提供者: {name}")
    
    def register_build_provider(self, name: str, provider_class: Type[IBuildProvider]):
        """注册构筑数据提供者"""
        self._build_providers[name] = provider_class
        self._logger.info(f"注册构筑数据提供者: {name}")
    
    def register_game_data_provider(self, name: str, provider_class: Type[IGameDataProvider]):
        """注册游戏数据提供者"""
        self._game_data_providers[name] = provider_class
        self._logger.info(f"注册游戏数据提供者: {name}")
    
    def register_calculation_provider(self, name: str, provider_class: Type[ICalculationProvider]):
        """注册计算提供者"""
        self._calculation_providers[name] = provider_class
        self._logger.info(f"注册计算提供者: {name}")
    
    async def health_check_all_providers(self) -> Dict[str, Dict[str, Any]]:
        """检查所有提供者的健康状态"""
        health_status = {}
        
        # 检查市场数据提供者
        market_status = {}
        for name in self._market_providers.keys():
            try:
                provider = self.create_market_provider(name)
                status = await provider.get_health_status()
                connection = await provider.test_connection()
                market_status[name] = {
                    'status': status.value,
                    'connection': connection,
                    'rate_limit': provider.get_rate_limit_info()
                }
            except Exception as e:
                market_status[name] = {
                    'status': 'error',
                    'connection': False,
                    'error': str(e)
                }
        
        health_status['market_providers'] = market_status
        
        # 检查构筑数据提供者
        build_status = {}
        for name in self._build_providers.keys():
            try:
                provider = self.create_build_provider(name)
                status = await provider.get_health_status()
                connection = await provider.test_connection()
                build_status[name] = {
                    'status': status.value,
                    'connection': connection,
                    'rate_limit': provider.get_rate_limit_info()
                }
            except Exception as e:
                build_status[name] = {
                    'status': 'error',
                    'connection': False,
                    'error': str(e)
                }
        
        health_status['build_providers'] = build_status
        
        return health_status
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """获取提供者统计信息"""
        stats = {
            'total_providers': len(self._provider_cache),
            'market_providers': len(self._market_providers),
            'build_providers': len(self._build_providers),
            'game_data_providers': len(self._game_data_providers),
            'calculation_providers': len(self._calculation_providers),
            'cached_instances': {}
        }
        
        # 获取缓存实例的统计信息
        for cache_key, provider in self._provider_cache.items():
            if hasattr(provider, 'get_stats'):
                try:
                    stats['cached_instances'][cache_key] = provider.get_stats()
                except Exception as e:
                    stats['cached_instances'][cache_key] = {'error': str(e)}
        
        return stats
    
    async def close_all_providers(self):
        """关闭所有提供者资源"""
        for provider in self._provider_cache.values():
            if hasattr(provider, 'close'):
                try:
                    await provider.close()
                except Exception as e:
                    self._logger.error(f"关闭提供者失败: {e}")
        
        self._provider_cache.clear()
        self._logger.info("所有数据提供者已关闭")


# 全局工厂实例
_factory_instance: Optional[DataProviderFactory] = None


def get_factory() -> DataProviderFactory:
    """获取全局工厂实例"""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = DataProviderFactory()
    return _factory_instance


def reset_factory():
    """重置全局工厂实例（主要用于测试）"""
    global _factory_instance
    if _factory_instance:
        # 注意：这里不能使用await，因为这是同步函数
        # 在实际使用中，应该在异步上下文中调用close_all_providers
        pass
    _factory_instance = None


# 便捷函数
async def create_market_provider(name: str = "poe2scout") -> IMarketProvider:
    """创建市场数据提供者的便捷函数"""
    return get_factory().create_market_provider(name)


async def create_build_provider(name: str = "ninja_poe2") -> IBuildProvider:
    """创建构筑数据提供者的便捷函数"""
    return get_factory().create_build_provider(name)


async def health_check_providers() -> Dict[str, Dict[str, Any]]:
    """检查所有提供者健康状态的便捷函数"""
    return await get_factory().health_check_all_providers()


# 配置类
class DataSourceConfig:
    """数据源配置类"""
    
    def __init__(self):
        self.market_provider = "poe2scout"
        self.build_provider = "ninja_poe2"
        self.fallback_to_mock = True
        self.enable_caching = True
        self.cache_ttl = {
            'market_data': 600,    # 10分钟
            'build_data': 1800,    # 30分钟
            'game_data': 3600      # 1小时
        }
        self.rate_limits = {
            'poe2scout': {'rpm': 30, 'rph': 1000},
            'ninja_poe2': {'rpm': 10, 'rph': 500}
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'market_provider': self.market_provider,
            'build_provider': self.build_provider,
            'fallback_to_mock': self.fallback_to_mock,
            'enable_caching': self.enable_caching,
            'cache_ttl': self.cache_ttl,
            'rate_limits': self.rate_limits
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataSourceConfig':
        """从字典创建配置"""
        config = cls()
        config.market_provider = data.get('market_provider', config.market_provider)
        config.build_provider = data.get('build_provider', config.build_provider)
        config.fallback_to_mock = data.get('fallback_to_mock', config.fallback_to_mock)
        config.enable_caching = data.get('enable_caching', config.enable_caching)
        
        if 'cache_ttl' in data:
            config.cache_ttl.update(data['cache_ttl'])
        
        if 'rate_limits' in data:
            config.rate_limits.update(data['rate_limits'])
        
        return config