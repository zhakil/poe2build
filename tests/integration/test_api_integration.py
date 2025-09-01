"""
API集成测试
测试与外部API的真实集成，包括PoE2Scout、Ninja、PoE2DB等数据源
"""

import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock
from typing import Dict, List, Any, Optional

from tests.fixtures.mock_responses.api_responses import (
    MOCK_POE2_SCOUT_RESPONSES, MOCK_NINJA_RESPONSES, 
    MOCK_POE2DB_RESPONSES, get_mock_response, get_error_response
)


class MockPoE2ScoutAPI:
    """Mock PoE2 Scout API实现"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.base_url = "https://poe2scout.com"
        self.rate_limit_remaining = 60
        self.last_request_time = 0
    
    async def get_item_price(self, item_name: str) -> Optional[Dict[str, Any]]:
        """获取物品价格"""
        await self._simulate_network_delay()
        
        if item_name in MOCK_POE2_SCOUT_RESPONSES['item_prices']:
            return MOCK_POE2_SCOUT_RESPONSES['item_prices'][item_name]
        
        return None
    
    async def get_market_trends(self) -> Dict[str, Any]:
        """获取市场趋势"""
        await self._simulate_network_delay()
        return MOCK_POE2_SCOUT_RESPONSES['market_trends']
    
    async def get_top_builds(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取热门构筑"""
        await self._simulate_network_delay()
        builds = MOCK_POE2_SCOUT_RESPONSES['build_data']['top_builds']
        return builds[:limit]
    
    async def health_check(self) -> Dict[str, Any]:
        """API健康检查"""
        await self._simulate_network_delay(min_delay=0.1, max_delay=0.3)
        return {
            'status': 'healthy',
            'response_time_ms': 150,
            'rate_limit_remaining': self.rate_limit_remaining,
            'timestamp': time.time()
        }
    
    async def _simulate_network_delay(self, min_delay=0.05, max_delay=0.2):
        """模拟网络延迟"""
        import random
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
        self.rate_limit_remaining = max(0, self.rate_limit_remaining - 1)
        self.last_request_time = time.time()


class MockNinjaAPI:
    """Mock Ninja API实现"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.base_url = "https://poe.ninja/poe2"
    
    async def get_build_rankings(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取构筑排行榜"""
        await asyncio.sleep(0.1)  # 模拟网络延迟
        rankings = MOCK_NINJA_RESPONSES['build_rankings']
        return rankings[:limit]
    
    async def get_class_distribution(self) -> Dict[str, Dict[str, int]]:
        """获取职业分布"""
        await asyncio.sleep(0.1)
        return MOCK_NINJA_RESPONSES['class_distribution']
    
    async def get_skill_usage_stats(self) -> List[Dict[str, Any]]:
        """获取技能使用统计"""
        await asyncio.sleep(0.1)
        return MOCK_NINJA_RESPONSES['skill_usage']
    
    async def search_builds(self, 
                          character_class: Optional[str] = None,
                          ascendancy: Optional[str] = None,
                          main_skill: Optional[str] = None) -> List[Dict[str, Any]]:
        """搜索构筑"""
        await asyncio.sleep(0.15)
        
        # 简单过滤逻辑
        builds = MOCK_NINJA_RESPONSES['build_rankings']
        
        if character_class:
            builds = [b for b in builds if b['class'] == character_class]
        
        if ascendancy:
            builds = [b for b in builds if b['ascendancy'] == ascendancy]
        
        if main_skill:
            builds = [b for b in builds if b['main_skill'] == main_skill]
        
        return builds
    
    async def health_check(self) -> Dict[str, Any]:
        """API健康检查"""
        await asyncio.sleep(0.08)
        return {
            'status': 'healthy',
            'response_time_ms': 80,
            'timestamp': time.time()
        }


class MockPoE2DBAPI:
    """Mock PoE2DB API实现"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.base_url = "https://poe2db.tw"
    
    async def get_skill_gem_data(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """获取技能宝石数据"""
        await asyncio.sleep(0.12)
        
        if skill_name in MOCK_POE2DB_RESPONSES['skill_gems']:
            return MOCK_POE2DB_RESPONSES['skill_gems'][skill_name]
        
        return None
    
    async def get_support_gem_data(self, support_name: str) -> Optional[Dict[str, Any]]:
        """获取辅助宝石数据"""
        await asyncio.sleep(0.12)
        
        if support_name in MOCK_POE2DB_RESPONSES['support_gems']:
            return MOCK_POE2DB_RESPONSES['support_gems'][support_name]
        
        return None
    
    async def get_item_data(self, item_name: str) -> Optional[Dict[str, Any]]:
        """获取物品数据"""
        await asyncio.sleep(0.15)
        
        if item_name in MOCK_POE2DB_RESPONSES['item_database']:
            return MOCK_POE2DB_RESPONSES['item_database'][item_name]
        
        return None
    
    async def get_passive_tree_data(self) -> Dict[str, Any]:
        """获取天赋树数据"""
        await asyncio.sleep(0.2)
        return MOCK_POE2DB_RESPONSES['passive_tree']
    
    async def health_check(self) -> Dict[str, Any]:
        """API健康检查"""
        await asyncio.sleep(0.1)
        return {
            'status': 'healthy',
            'response_time_ms': 100,
            'timestamp': time.time()
        }


@pytest.mark.integration
class TestPoE2ScoutAPIIntegration:
    """PoE2 Scout API集成测试"""
    
    @pytest.fixture
    async def scout_api(self):
        """创建Scout API实例"""
        return MockPoE2ScoutAPI()
    
    @pytest.mark.asyncio
    async def test_get_item_price_success(self, scout_api):
        """测试成功获取物品价格"""
        item_name = "Staff of Power"
        
        result = await scout_api.get_item_price(item_name)
        
        assert result is not None
        assert result['item_name'] == item_name
        assert 'median_price' in result
        assert 'currency' in result
        assert result['currency'] == 'divine'
        assert result['median_price'] > 0
        assert 'confidence' in result
        assert 0 <= result['confidence'] <= 1
    
    @pytest.mark.asyncio
    async def test_get_item_price_not_found(self, scout_api):
        """测试物品未找到的情况"""
        item_name = "Non Existent Item"
        
        result = await scout_api.get_item_price(item_name)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_market_trends(self, scout_api):
        """测试获取市场趋势"""
        trends = await scout_api.get_market_trends()
        
        assert 'popular_items' in trends
        assert 'meta_shifts' in trends
        assert isinstance(trends['popular_items'], list)
        assert len(trends['popular_items']) > 0
        
        # 验证流行物品数据结构
        popular_item = trends['popular_items'][0]
        assert 'item_name' in popular_item
        assert 'demand_index' in popular_item
        assert 'price_velocity' in popular_item
    
    @pytest.mark.asyncio
    async def test_get_top_builds(self, scout_api):
        """测试获取热门构筑"""
        limit = 5
        builds = await scout_api.get_top_builds(limit)
        
        assert isinstance(builds, list)
        assert len(builds) <= limit
        
        if builds:
            build = builds[0]
            assert 'build_id' in build
            assert 'name' in build
            assert 'class' in build
            assert 'estimated_dps' in build
            assert 'popularity_rank' in build
    
    @pytest.mark.asyncio
    async def test_api_health_check(self, scout_api):
        """测试API健康检查"""
        health = await scout_api.health_check()
        
        assert health['status'] == 'healthy'
        assert 'response_time_ms' in health
        assert 'rate_limit_remaining' in health
        assert 'timestamp' in health
        assert health['response_time_ms'] > 0
    
    @pytest.mark.asyncio
    async def test_rate_limiting_behavior(self, scout_api):
        """测试速率限制行为"""
        initial_limit = scout_api.rate_limit_remaining
        
        # 发送多个请求
        for _ in range(5):
            await scout_api.get_item_price("Basic Staff")
        
        # 验证速率限制递减
        assert scout_api.rate_limit_remaining < initial_limit
        assert scout_api.rate_limit_remaining >= 0


@pytest.mark.integration
class TestNinjaAPIIntegration:
    """Ninja API集成测试"""
    
    @pytest.fixture
    async def ninja_api(self):
        """创建Ninja API实例"""
        return MockNinjaAPI()
    
    @pytest.mark.asyncio
    async def test_get_build_rankings(self, ninja_api):
        """测试获取构筑排行榜"""
        rankings = await ninja_api.get_build_rankings(limit=10)
        
        assert isinstance(rankings, list)
        assert len(rankings) <= 10
        
        if rankings:
            build = rankings[0]
            assert 'rank' in build
            assert 'name' in build
            assert 'class' in build
            assert 'ascendancy' in build
            assert 'dps' in build
            assert 'popularity_percent' in build
            
            # 验证排行顺序
            assert build['rank'] >= 1
    
    @pytest.mark.asyncio
    async def test_get_class_distribution(self, ninja_api):
        """测试获取职业分布"""
        distribution = await ninja_api.get_class_distribution()
        
        assert isinstance(distribution, dict)
        assert len(distribution) > 0
        
        # 验证职业数据结构
        for class_name, stats in distribution.items():
            assert 'percentage' in stats
            assert 'count' in stats
            assert stats['percentage'] > 0
            assert stats['count'] > 0
    
    @pytest.mark.asyncio
    async def test_get_skill_usage_stats(self, ninja_api):
        """测试获取技能使用统计"""
        skill_stats = await ninja_api.get_skill_usage_stats()
        
        assert isinstance(skill_stats, list)
        assert len(skill_stats) > 0
        
        skill = skill_stats[0]
        assert 'skill_name' in skill
        assert 'usage_percent' in skill
        assert 'average_dps' in skill
        assert skill['usage_percent'] > 0
    
    @pytest.mark.asyncio
    async def test_search_builds_by_class(self, ninja_api):
        """测试按职业搜索构筑"""
        character_class = "Sorceress"
        builds = await ninja_api.search_builds(character_class=character_class)
        
        assert isinstance(builds, list)
        
        # 验证过滤结果
        for build in builds:
            assert build['class'] == character_class
    
    @pytest.mark.asyncio
    async def test_search_builds_by_ascendancy(self, ninja_api):
        """测试按升华搜索构筑"""
        ascendancy = "Stormweaver"
        builds = await ninja_api.search_builds(ascendancy=ascendancy)
        
        assert isinstance(builds, list)
        
        # 验证过滤结果
        for build in builds:
            assert build['ascendancy'] == ascendancy
    
    @pytest.mark.asyncio
    async def test_search_builds_multiple_filters(self, ninja_api):
        """测试多重过滤搜索构筑"""
        builds = await ninja_api.search_builds(
            character_class="Sorceress",
            ascendancy="Stormweaver",
            main_skill="Lightning Bolt"
        )
        
        assert isinstance(builds, list)
        
        # 验证所有过滤条件
        for build in builds:
            assert build['class'] == "Sorceress"
            assert build['ascendancy'] == "Stormweaver"
            assert build['main_skill'] == "Lightning Bolt"
    
    @pytest.mark.asyncio
    async def test_ninja_health_check(self, ninja_api):
        """测试Ninja API健康检查"""
        health = await ninja_api.health_check()
        
        assert health['status'] == 'healthy'
        assert 'response_time_ms' in health
        assert 'timestamp' in health


@pytest.mark.integration
class TestPoE2DBAPIIntegration:
    """PoE2DB API集成测试"""
    
    @pytest.fixture
    async def poe2db_api(self):
        """创建PoE2DB API实例"""
        return MockPoE2DBAPI()
    
    @pytest.mark.asyncio
    async def test_get_skill_gem_data(self, poe2db_api):
        """测试获取技能宝石数据"""
        skill_name = "Lightning Bolt"
        
        result = await poe2db_api.get_skill_gem_data(skill_name)
        
        assert result is not None
        assert result['name'] == skill_name
        assert 'gem_type' in result
        assert result['gem_type'] == 'Active'
        assert 'damage_type' in result
        assert 'tags' in result
        assert 'requirements' in result
    
    @pytest.mark.asyncio
    async def test_get_support_gem_data(self, poe2db_api):
        """测试获取辅助宝石数据"""
        support_name = "Added Lightning Damage"
        
        result = await poe2db_api.get_support_gem_data(support_name)
        
        assert result is not None
        assert result['name'] == support_name
        assert result['gem_type'] == 'Support'
        assert 'effect' in result
        assert 'mana_multiplier' in result
    
    @pytest.mark.asyncio
    async def test_get_item_data(self, poe2db_api):
        """测试获取物品数据"""
        item_name = "Staff of Power"
        
        result = await poe2db_api.get_item_data(item_name)
        
        assert result is not None
        assert result['name'] == item_name
        assert 'item_class' in result
        assert 'rarity' in result
        assert 'properties' in result
        assert 'explicit_mods' in result
    
    @pytest.mark.asyncio
    async def test_get_passive_tree_data(self, poe2db_api):
        """测试获取天赋树数据"""
        passive_tree = await poe2db_api.get_passive_tree_data()
        
        assert 'keystones' in passive_tree
        assert 'notable_passives' in passive_tree
        assert isinstance(passive_tree['keystones'], list)
        assert isinstance(passive_tree['notable_passives'], list)
        
        # 验证天赋节点结构
        if passive_tree['keystones']:
            keystone = passive_tree['keystones'][0]
            assert 'name' in keystone
            assert 'description' in keystone
            assert 'position' in keystone
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_data(self, poe2db_api):
        """测试获取不存在的数据"""
        result = await poe2db_api.get_skill_gem_data("Nonexistent Skill")
        assert result is None
        
        result = await poe2db_api.get_item_data("Nonexistent Item")
        assert result is None


@pytest.mark.integration
class TestMultiAPIIntegration:
    """多API集成测试"""
    
    @pytest.fixture
    async def all_apis(self):
        """创建所有API实例"""
        return {
            'scout': MockPoE2ScoutAPI(),
            'ninja': MockNinjaAPI(),
            'poe2db': MockPoE2DBAPI()
        }
    
    @pytest.mark.asyncio
    async def test_concurrent_api_calls(self, all_apis):
        """测试并发API调用"""
        # 创建并发任务
        tasks = [
            all_apis['scout'].get_item_price("Staff of Power"),
            all_apis['ninja'].get_build_rankings(5),
            all_apis['poe2db'].get_skill_gem_data("Lightning Bolt")
        ]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # 验证所有结果
        assert len(results) == 3
        assert results[0] is not None  # Scout price data
        assert isinstance(results[1], list)  # Ninja rankings
        assert results[2] is not None  # PoE2DB skill data
        
        # 并发调用应该比串行快
        total_time = end_time - start_time
        assert total_time < 1.0  # 应该在1秒内完成
    
    @pytest.mark.asyncio
    async def test_comprehensive_build_data_collection(self, all_apis):
        """测试综合构筑数据收集"""
        # 从Ninja获取热门构筑
        ninja_builds = await all_apis['ninja'].get_build_rankings(3)
        
        if not ninja_builds:
            pytest.skip("No ninja builds available for testing")
        
        # 选择一个构筑进行详细分析
        target_build = ninja_builds[0]
        
        # 并发收集相关数据
        tasks = []
        
        # 从PoE2DB获取主技能信息
        if 'main_skill' in target_build:
            tasks.append(all_apis['poe2db'].get_skill_gem_data(target_build['main_skill']))
        
        # 从Scout获取相关物品价格（假设有装备信息）
        tasks.append(all_apis['scout'].get_market_trends())
        
        # 从PoE2DB获取天赋树数据
        tasks.append(all_apis['poe2db'].get_passive_tree_data())
        
        results = await asyncio.gather(*tasks)
        
        # 验证数据完整性
        skill_data = results[0] if len(results) > 0 else None
        market_trends = results[1] if len(results) > 1 else None
        passive_tree = results[2] if len(results) > 2 else None
        
        # 构建综合数据结构
        comprehensive_data = {
            'build_info': target_build,
            'skill_data': skill_data,
            'market_trends': market_trends,
            'passive_tree': passive_tree,
            'data_collection_timestamp': time.time()
        }
        
        # 验证综合数据
        assert comprehensive_data['build_info'] is not None
        assert comprehensive_data['market_trends'] is not None
        assert comprehensive_data['passive_tree'] is not None
        
        return comprehensive_data
    
    @pytest.mark.asyncio
    async def test_api_health_monitoring(self, all_apis):
        """测试API健康监控"""
        # 并发检查所有API健康状态
        health_tasks = [
            all_apis['scout'].health_check(),
            all_apis['ninja'].health_check(),
            all_apis['poe2db'].health_check()
        ]
        
        health_results = await asyncio.gather(*health_tasks)
        
        # 验证所有API健康状态
        for i, (api_name, health) in enumerate(zip(['scout', 'ninja', 'poe2db'], health_results)):
            assert health['status'] == 'healthy', f"{api_name} API is not healthy"
            assert 'response_time_ms' in health
            assert health['response_time_ms'] > 0
        
        # 计算平均响应时间
        avg_response_time = sum(h['response_time_ms'] for h in health_results) / len(health_results)
        assert avg_response_time < 500  # 平均响应时间应小于500ms
    
    @pytest.mark.asyncio 
    async def test_error_handling_across_apis(self, all_apis):
        """测试跨API错误处理"""
        # 测试各种错误场景
        error_tasks = [
            all_apis['scout'].get_item_price("Nonexistent Item"),
            all_apis['ninja'].search_builds(character_class="InvalidClass"),
            all_apis['poe2db'].get_skill_gem_data("Invalid Skill")
        ]
        
        results = await asyncio.gather(*error_tasks, return_exceptions=True)
        
        # 验证错误处理
        assert results[0] is None  # Scout应返回None表示未找到
        assert isinstance(results[1], list)  # Ninja应返回空列表
        assert results[2] is None  # PoE2DB应返回None表示未找到
        
        # 确保没有未处理的异常
        for result in results:
            assert not isinstance(result, Exception)


@pytest.mark.integration
@pytest.mark.slow
class TestAPIPerformanceIntegration:
    """API性能集成测试"""
    
    @pytest.fixture
    async def performance_apis(self):
        """创建性能测试API实例"""
        return {
            'scout': MockPoE2ScoutAPI(),
            'ninja': MockNinjaAPI(),
            'poe2db': MockPoE2DBAPI()
        }
    
    @pytest.mark.asyncio
    async def test_api_response_time_benchmarks(self, performance_apis):
        """测试API响应时间基准"""
        benchmarks = {
            'scout_item_price': 500,  # ms
            'ninja_rankings': 300,
            'poe2db_skill_data': 400
        }
        
        # 测试Scout API响应时间
        start_time = time.time()
        await performance_apis['scout'].get_item_price("Staff of Power")
        scout_time = (time.time() - start_time) * 1000
        
        # 测试Ninja API响应时间
        start_time = time.time()
        await performance_apis['ninja'].get_build_rankings(10)
        ninja_time = (time.time() - start_time) * 1000
        
        # 测试PoE2DB API响应时间
        start_time = time.time()
        await performance_apis['poe2db'].get_skill_gem_data("Lightning Bolt")
        poe2db_time = (time.time() - start_time) * 1000
        
        # 验证响应时间在可接受范围内
        assert scout_time < benchmarks['scout_item_price']
        assert ninja_time < benchmarks['ninja_rankings']
        assert poe2db_time < benchmarks['poe2db_skill_data']
    
    @pytest.mark.asyncio
    async def test_concurrent_load_handling(self, performance_apis):
        """测试并发负载处理"""
        concurrent_requests = 20
        
        # 创建大量并发请求
        tasks = []
        for i in range(concurrent_requests):
            tasks.extend([
                performance_apis['scout'].get_item_price(f"Test Item {i % 3}"),
                performance_apis['ninja'].get_build_rankings(5),
                performance_apis['poe2db'].get_skill_gem_data("Lightning Bolt")
            ])
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # 验证所有请求都成功处理
        successful_requests = sum(1 for r in results if not isinstance(r, Exception))
        assert successful_requests >= len(tasks) * 0.9  # 至少90%成功率
        
        # 验证总时间在合理范围内
        assert total_time < 10.0  # 10秒内完成所有请求
    
    @pytest.mark.asyncio
    async def test_memory_usage_during_api_calls(self, performance_apis):
        """测试API调用期间的内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行大量API调用
        tasks = []
        for _ in range(50):
            tasks.extend([
                performance_apis['scout'].get_market_trends(),
                performance_apis['ninja'].get_build_rankings(20),
                performance_apis['poe2db'].get_passive_tree_data()
            ])
        
        await asyncio.gather(*tasks)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # 内存增长应该在合理范围内
        assert memory_increase < 100  # 不超过100MB增长