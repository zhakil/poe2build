"""
单元测试 - 数据源组件

测试所有外部数据源的功能，包括：
- PoE2ScoutAPI (市场价格数据)
- NinjaScraper (元数据分析)
- PoE2DBScraper (物品数据)
- 数据验证和缓存逻辑
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from src.poe2build.data_sources.poe2_scout import PoE2ScoutAPI, MarketData
from src.poe2build.data_sources.ninja_scraper import NinjaScraper, MetaBuild
from src.poe2build.data_sources.poe2db_scraper import PoE2DBScraper, ItemData
from src.poe2build.resilience.cache_manager import CacheManager


@pytest.mark.unit
class TestPoE2ScoutAPI:
    """测试PoE2Scout API功能"""
    
    def setup_method(self):
        """测试设置"""
        self.scout_api = PoE2ScoutAPI()
        
    def test_scout_api_initialization(self):
        """测试API初始化"""
        assert self.scout_api.base_url == "https://poe2scout.com/api"
        assert self.scout_api.rate_limit_delay > 0
        assert hasattr(self.scout_api, '_session')
        
    @patch('requests.get')
    def test_get_item_price_success(self, mock_get):
        """测试成功获取物品价格"""
        # Mock API响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'item_name': 'Staff of Power',
            'median_price': 15.5,
            'currency': 'divine',
            'listings_count': 45,
            'confidence': 0.92,
            'last_updated': '2024-01-15T10:30:00Z'
        }
        mock_get.return_value = mock_response
        
        # 执行查询
        result = self.scout_api.get_item_price('Staff of Power', league='Standard')
        
        # 验证结果
        assert result is not None
        assert result.item_name == 'Staff of Power'
        assert result.median_price == 15.5
        assert result.currency == 'divine'
        assert result.confidence == 0.92
        assert result.listings_count == 45
        
        # 验证API调用
        mock_get.assert_called_once()
        call_url = mock_get.call_args[0][0]
        assert 'poe2scout.com/api' in call_url
        assert 'Staff%20of%20Power' in call_url
        
    @patch('requests.get')
    def test_get_item_price_not_found(self, mock_get):
        """测试物品未找到情况"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            'error': 'Item not found',
            'message': 'No listings found for this item'
        }
        mock_get.return_value = mock_response
        
        result = self.scout_api.get_item_price('Nonexistent Item', league='Standard')
        
        assert result is None
        
    @patch('requests.get')
    def test_api_rate_limiting(self, mock_get):
        """测试API限流处理"""
        # 模拟429 Too Many Requests
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '60'}
        mock_get.return_value = mock_response
        
        with patch('time.sleep') as mock_sleep:
            result = self.scout_api.get_item_price('Test Item', league='Standard')
            
            # 验证限流处理
            assert result is None
            mock_sleep.assert_called()  # 应该等待
            
    def test_market_data_model(self):
        """测试市场数据模型"""
        market_data = MarketData(
            item_name='Lightning Amulet',
            median_price=3.2,
            currency='divine',
            listings_count=28,
            confidence=0.87,
            min_price=2.8,
            max_price=4.1,
            last_updated=datetime.utcnow()
        )
        
        assert market_data.item_name == 'Lightning Amulet'
        assert market_data.median_price == 3.2
        assert market_data.is_reliable  # confidence > 0.8
        assert market_data.has_good_sample_size  # listings_count > 20
        
    def test_price_validation(self):
        """测试价格数据验证"""
        # 无效的负数价格
        with pytest.raises(ValueError):
            MarketData(
                item_name='Test Item',
                median_price=-1.0,
                currency='divine'
            )
            
        # 无效的置信度
        with pytest.raises(ValueError):
            MarketData(
                item_name='Test Item',
                median_price=5.0,
                currency='divine',
                confidence=1.5  # > 1.0
            )


@pytest.mark.unit
class TestNinjaScraper:
    """测试Ninja爬虫功能"""
    
    def setup_method(self):
        """测试设置"""
        self.ninja_scraper = NinjaScraper()
        
    def test_ninja_scraper_initialization(self):
        """测试爬虫初始化"""
        assert self.ninja_scraper.base_url == "https://poe.ninja/poe2/builds"
        assert hasattr(self.ninja_scraper, '_session')
        assert self.ninja_scraper._request_delay > 0
        
    @patch('requests.get')
    def test_scrape_builds_success(self, mock_get):
        """测试成功爬取构筑数据"""
        # Mock HTML响应
        mock_html = '''
        <div class="build-entry">
            <div class="build-name">Lightning Sorceress</div>
            <div class="class">Sorceress</div>
            <div class="ascendancy">Stormweaver</div>
            <div class="dps">1,250,000</div>
            <div class="level">92</div>
            <div class="popularity">15.2%</div>
        </div>
        <div class="build-entry">
            <div class="build-name">Ice Shot Ranger</div>
            <div class="class">Ranger</div>
            <div class="ascendancy">Deadeye</div>
            <div class="dps">850,000</div>
            <div class="level">88</div>
            <div class="popularity">12.8%</div>
        </div>
        '''
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_get.return_value = mock_response
        
        # 执行爬取
        builds = self.ninja_scraper.get_meta_builds(limit=10)
        
        # 验证结果
        assert len(builds) == 2
        
        lightning_build = builds[0]
        assert lightning_build.name == 'Lightning Sorceress'
        assert lightning_build.character_class == 'Sorceress'
        assert lightning_build.ascendancy == 'Stormweaver'
        assert lightning_build.estimated_dps == 1250000
        assert lightning_build.level == 92
        assert lightning_build.popularity_percent == 15.2
        
    @patch('requests.get')
    def test_scrape_builds_with_filters(self, mock_get):
        """测试带过滤器的构筑爬取"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html>Mock HTML</html>"
        mock_get.return_value = mock_response
        
        # 使用过滤器
        builds = self.ninja_scraper.get_meta_builds(
            character_class='Sorceress',
            min_dps=500000,
            min_level=85,
            limit=5
        )
        
        # 验证API调用参数
        mock_get.assert_called_once()
        call_url = mock_get.call_args[0][0]
        assert 'class=Sorceress' in call_url or 'Sorceress' in call_url
        
    def test_meta_build_model(self):
        """测试元数据构筑模型"""
        meta_build = MetaBuild(
            name='Test Meta Build',
            character_class='Witch',
            ascendancy='Infernalist',
            main_skill='Fireball',
            estimated_dps=750000,
            level=90,
            popularity_percent=8.5,
            popularity_rank=5,
            league='Standard',
            sample_size=150
        )
        
        assert meta_build.name == 'Test Meta Build'
        assert meta_build.is_popular  # popularity > 5%
        assert meta_build.is_endgame  # level >= 85
        assert meta_build.has_reliable_data  # sample_size >= 100
        
    @patch('time.sleep')
    def test_rate_limiting_between_requests(self, mock_sleep):
        """测试请求间限流"""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "<html></html>"
            mock_get.return_value = mock_response
            
            # 执行多次请求
            self.ninja_scraper.get_meta_builds(limit=5)
            self.ninja_scraper.get_meta_builds(limit=5)
            
            # 验证限流延迟
            assert mock_sleep.call_count >= 1


@pytest.mark.unit
class TestPoE2DBScraper:
    """测试PoE2DB爬虫功能"""
    
    def setup_method(self):
        """测试设置"""
        self.poe2db_scraper = PoE2DBScraper()
        
    @patch('requests.get')
    def test_get_item_data_success(self, mock_get):
        """测试成功获取物品数据"""
        mock_html = '''
        <div class="item-data">
            <h1 class="item-name">Staff of Power</h1>
            <div class="item-type">Two-Handed Mace</div>
            <div class="level-requirement">Level: 68</div>
            <div class="stat">Adds 120-180 Lightning Damage</div>
            <div class="stat">25% increased Cast Speed</div>
            <div class="stat">+80 to Intelligence</div>
        </div>
        '''
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_get.return_value = mock_response
        
        # 执行查询
        item_data = self.poe2db_scraper.get_item_data('Staff of Power')
        
        # 验证结果
        assert item_data is not None
        assert item_data.name == 'Staff of Power'
        assert item_data.item_type == 'Two-Handed Mace'
        assert item_data.level_requirement == 68
        assert len(item_data.stats) >= 3
        assert 'Lightning Damage' in item_data.stats[0]
        
    def test_item_data_model(self):
        """测试物品数据模型"""
        item_data = ItemData(
            name='Test Unique Item',
            item_type='Ring',
            level_requirement=45,
            stats=[
                '+50 to Life',
                '20% increased Attack Speed',
                'Adds 15-25 Fire Damage to Attacks'
            ],
            flavor_text='A ring of great power...',
            is_unique=True,
            drop_areas=['Act 4', 'Maps']
        )
        
        assert item_data.name == 'Test Unique Item'
        assert item_data.is_unique
        assert item_data.is_endgame_item  # level >= 40
        assert len(item_data.stats) == 3
        assert 'Life' in item_data.stats[0]
        
    @patch('requests.get')
    def test_search_items_by_type(self, mock_get):
        """测试按类型搜索物品"""
        mock_html = '''
        <div class="item-list">
            <div class="item-entry">
                <a href="/item/staff-1">Lightning Staff</a>
                <span class="item-type">Staff</span>
            </div>
            <div class="item-entry">
                <a href="/item/staff-2">Ice Staff</a>
                <span class="item-type">Staff</span>
            </div>
        </div>
        '''
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_get.return_value = mock_response
        
        # 执行搜索
        items = self.poe2db_scraper.search_items_by_type('Staff', limit=10)
        
        # 验证结果
        assert len(items) == 2
        assert items[0]['name'] == 'Lightning Staff'
        assert items[1]['name'] == 'Ice Staff'
        
        # 验证URL参数
        call_url = mock_get.call_args[0][0]
        assert 'Staff' in call_url


@pytest.mark.unit
class TestDataSourceIntegration:
    """测试数据源集成"""
    
    def test_market_data_aggregation(self):
        """测试市场数据聚合"""
        # 模拟多个数据源的价格数据
        scout_price = MarketData(
            item_name='Staff of Power',
            median_price=15.5,
            currency='divine',
            listings_count=45,
            confidence=0.92,
            source='poe2scout'
        )
        
        # 模拟另一个数据源（例如官方API）
        official_price = MarketData(
            item_name='Staff of Power',
            median_price=16.0,
            currency='divine',
            listings_count=80,
            confidence=0.95,
            source='official'
        )
        
        # 简单的价格聚合逻辑
        prices = [scout_price, official_price]
        weights = [data.confidence * data.listings_count for data in prices]
        weighted_price = sum(p.median_price * w for p, w in zip(prices, weights)) / sum(weights)
        
        assert 15.5 < weighted_price < 16.0  # 应该在两个价格之间
        
    async def test_concurrent_data_fetching(self):
        """测试并发数据获取"""
        import asyncio
        
        # 创建异步Mock
        scout_api = AsyncMock(spec=PoE2ScoutAPI)
        ninja_scraper = AsyncMock(spec=NinjaScraper)
        
        # 设置Mock返回值
        scout_api.get_item_price.return_value = MarketData(
            item_name='Test Item',
            median_price=10.0,
            currency='divine'
        )
        
        ninja_scraper.get_meta_builds.return_value = [
            MetaBuild(
                name='Test Build',
                character_class='Sorceress',
                estimated_dps=500000,
                level=85
            )
        ]
        
        # 并发执行
        results = await asyncio.gather(
            scout_api.get_item_price('Test Item'),
            ninja_scraper.get_meta_builds(limit=5)
        )
        
        market_data, meta_builds = results
        
        # 验证结果
        assert market_data.item_name == 'Test Item'
        assert len(meta_builds) == 1
        assert meta_builds[0].name == 'Test Build'
        
    def test_data_validation_pipeline(self):
        """测试数据验证流水线"""
        # 模拟原始数据
        raw_market_data = {
            'item_name': '  Staff of Power  ',  # 包含空格
            'median_price': '15.5',  # 字符串格式
            'currency': 'DIVINE',  # 大写
            'listings_count': '45',
            'confidence': '0.92'
        }
        
        # 数据清洗和验证
        cleaned_data = {
            'item_name': raw_market_data['item_name'].strip(),
            'median_price': float(raw_market_data['median_price']),
            'currency': raw_market_data['currency'].lower(),
            'listings_count': int(raw_market_data['listings_count']),
            'confidence': float(raw_market_data['confidence'])
        }
        
        # 创建数据模型
        market_data = MarketData(**cleaned_data)
        
        assert market_data.item_name == 'Staff of Power'
        assert market_data.median_price == 15.5
        assert market_data.currency == 'divine'
        assert market_data.is_reliable


@pytest.mark.unit
class TestCacheManager:
    """测试缓存管理器"""
    
    def setup_method(self):
        """测试设置"""
        self.cache_manager = CacheManager(max_size=100, default_ttl=600)
        
    def test_cache_set_and_get(self):
        """测试缓存设置和获取"""
        # 设置缓存
        test_data = {'price': 15.5, 'currency': 'divine'}
        self.cache_manager.set('test_item_price', test_data, ttl=300)
        
        # 获取缓存
        cached_data = self.cache_manager.get('test_item_price')
        
        assert cached_data == test_data
        
    def test_cache_expiration(self):
        """测试缓存过期"""
        # 设置短过期时间的缓存
        self.cache_manager.set('short_lived', 'test_value', ttl=0.1)
        
        # 立即获取应该成功
        assert self.cache_manager.get('short_lived') == 'test_value'
        
        # 等待过期
        import time
        time.sleep(0.2)
        
        # 过期后应该返回None
        assert self.cache_manager.get('short_lived') is None
        
    def test_cache_size_limit(self):
        """测试缓存大小限制"""
        small_cache = CacheManager(max_size=3, default_ttl=3600)
        
        # 添加超过限制的条目
        for i in range(5):
            small_cache.set(f'item_{i}', f'value_{i}')
        
        # 验证缓存大小不超过限制
        assert len(small_cache._cache) <= 3
        
        # 最早的条目应该被移除
        assert small_cache.get('item_0') is None
        assert small_cache.get('item_4') == 'value_4'  # 最新的应该存在
        
    def test_cache_clear(self):
        """测试清空缓存"""
        # 添加一些数据
        for i in range(3):
            self.cache_manager.set(f'item_{i}', f'value_{i}')
        
        # 验证数据存在
        assert len(self.cache_manager._cache) == 3
        
        # 清空缓存
        self.cache_manager.clear()
        
        # 验证缓存为空
        assert len(self.cache_manager._cache) == 0
        assert self.cache_manager.get('item_0') is None
        
    def test_cache_statistics(self):
        """测试缓存统计信息"""
        # 添加一些数据
        self.cache_manager.set('item1', 'value1')
        self.cache_manager.set('item2', 'value2')
        
        # 缓存命中
        self.cache_manager.get('item1')
        self.cache_manager.get('item1')  # 再次命中
        
        # 缓存未命中
        self.cache_manager.get('nonexistent')
        
        stats = self.cache_manager.get_statistics()
        
        assert stats['total_items'] == 2
        assert stats['cache_hits'] == 2
        assert stats['cache_misses'] == 1
        assert stats['hit_rate'] == 2/3  # 2 hits out of 3 total requests
