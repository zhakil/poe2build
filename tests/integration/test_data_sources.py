"""Phase 2数据源集成测试"""

import pytest
import asyncio
from datetime import datetime

from src.poe2build.data_sources.factory import get_factory, DataSourceConfig
from src.poe2build.data_sources.poe2_scout import PoE2ScoutAPI
from src.poe2build.data_sources.ninja_scraper import NinjaPoE2Scraper
from src.poe2build.models.characters import PoE2CharacterClass


class TestDataSourcesIntegration:
    """数据源集成测试"""
    
    @pytest.mark.asyncio
    async def test_factory_creation(self):
        """测试工厂创建提供者"""
        factory = get_factory()
        
        # 测试创建市场数据提供者
        market_provider = factory.create_market_provider('poe2scout')
        assert market_provider is not None
        assert market_provider.get_provider_name() == 'PoE2Scout'
        
        # 测试创建构筑数据提供者
        build_provider = factory.create_build_provider('ninja_poe2')
        assert build_provider is not None
        assert build_provider.get_provider_name() == 'NinjaPoE2'
    
    @pytest.mark.asyncio
    async def test_mock_providers(self):
        """测试Mock提供者"""
        factory = get_factory()
        
        # 测试Mock市场提供者
        mock_market = factory.create_market_provider('mock_poe2scout')
        market_data = await mock_market.get_item_price("Test Item")
        assert market_data is not None
        assert market_data.source == "MockPoE2Scout"
        
        # 测试Mock构筑提供者
        mock_builds = factory.create_build_provider('mock_ninja_poe2')
        builds = await mock_builds.get_popular_builds(limit=3)
        assert len(builds) == 3
        assert all(build.source_url.startswith("mock://") for build in builds)
    
    @pytest.mark.asyncio
    async def test_provider_health_check(self):
        """测试提供者健康检查"""
        factory = get_factory()
        health_status = await factory.health_check_all_providers()
        
        assert 'market_providers' in health_status
        assert 'build_providers' in health_status
        assert 'poe2scout' in health_status['market_providers']
        assert 'ninja_poe2' in health_status['build_providers']
    
    @pytest.mark.asyncio
    async def test_resilience_mechanisms(self):
        """测试弹性机制"""
        # 测试熔断器和缓存
        market_provider = PoE2ScoutAPI()
        
        # 测试健康状态
        status = await market_provider.get_health_status()
        assert status in ['healthy', 'degraded', 'unhealthy', 'offline']
        
        # 测试速率限制信息
        rate_info = market_provider.get_rate_limit_info()
        assert 'requests_per_minute' in rate_info
        assert 'requests_per_hour' in rate_info
        
        await market_provider.close()
    
    @pytest.mark.asyncio  
    async def test_config_system(self):
        """测试配置系统"""
        config = DataSourceConfig()
        
        # 测试默认配置
        assert config.market_provider == "poe2scout"
        assert config.build_provider == "ninja_poe2"
        assert config.fallback_to_mock == True
        
        # 测试配置转换
        config_dict = config.to_dict()
        config2 = DataSourceConfig.from_dict(config_dict)
        assert config2.market_provider == config.market_provider


if __name__ == "__main__":
    asyncio.run(pytest.main([__file__, "-v"]))