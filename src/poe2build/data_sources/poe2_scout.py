"""PoE2Scout市场数据API集成"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from .interfaces import IMarketProvider, DataProviderStatus
from .base_provider import BaseProvider, RateLimitConfig, CacheConfig
from ..models.market import PoE2ItemMarketData as MarketData, PoE2MarketListing as ItemListing, PoE2MarketTrendData as PricePoint


class PoE2ScoutAPI(BaseProvider, IMarketProvider):
    """PoE2Scout市场数据提供者"""
    
    def __init__(self, base_url: str = "https://poe2scout.com"):
        # PoE2Scout特定的速率限制配置
        rate_config = RateLimitConfig(
            requests_per_minute=30,
            requests_per_hour=1000,
            backoff_factor=2.0
        )
        
        # 市场数据缓存配置
        cache_config = CacheConfig(
            default_ttl=600,        # 10分钟默认缓存
            market_data_ttl=600,    # 市场数据10分钟
            build_data_ttl=1800,    # 构筑数据30分钟
            game_data_ttl=3600      # 游戏数据1小时
        )
        
        super().__init__(
            name="PoE2Scout",
            base_url=base_url,
            rate_config=rate_config,
            cache_config=cache_config
        )
        
        self._logger = logging.getLogger(f"{__name__}.PoE2ScoutAPI")
        
        # API端点映射
        self.endpoints = {
            'search': '/api/v1/search',
            'item_details': '/api/v1/item/{item_id}',
            'currency_rates': '/api/v1/currency',
            'popular_items': '/api/v1/popular',
            'market_stats': '/api/v1/stats',
            'leagues': '/api/v1/leagues'
        }
    
    async def get_item_price(self, item_name: str, league: str = "Standard") -> Optional[MarketData]:
        """获取单个物品的价格数据"""
        try:
            search_params = {
                'name': item_name,
                'league': league,
                'limit': 10
            }
            
            cache_key = self._generate_cache_key('item_price', search_params)
            
            response = await self._make_request(
                'GET',
                f"{self.endpoints['search']}",
                params=search_params,
                cache_key=cache_key,
                cache_ttl=self.cache.config.market_data_ttl
            )
            
            if not response or 'items' not in response or not response['items']:
                return None
            
            # 取第一个匹配的物品
            item_data = response['items'][0]
            return self._parse_market_data(item_data, league)
            
        except Exception as e:
            self._logger.error(f"获取物品价格失败 ({item_name}): {e}")
            return None
    
    async def search_items(self, query: Dict[str, Any], league: str = "Standard") -> List[MarketData]:
        """搜索物品数据"""
        try:
            # 构建搜索参数
            search_params = {
                'league': league,
                'limit': query.get('limit', 20),
                **self._build_search_filters(query)
            }
            
            cache_key = self._generate_cache_key('search_items', search_params)
            
            response = await self._make_request(
                'GET',
                self.endpoints['search'],
                params=search_params,
                cache_key=cache_key,
                cache_ttl=self.cache.config.market_data_ttl
            )
            
            if not response or 'items' not in response:
                return []
            
            # 解析所有物品数据
            market_data_list = []
            for item_data in response['items']:
                market_data = self._parse_market_data(item_data, league)
                if market_data:
                    market_data_list.append(market_data)
            
            return market_data_list
            
        except Exception as e:
            self._logger.error(f"搜索物品失败: {e}")
            return []
    
    async def get_currency_rates(self, league: str = "Standard") -> Dict[str, float]:
        """获取货币汇率"""
        try:
            cache_key = self._generate_cache_key('currency_rates', {'league': league})
            
            response = await self._make_request(
                'GET',
                self.endpoints['currency_rates'],
                params={'league': league},
                cache_key=cache_key,
                cache_ttl=300  # 货币汇率5分钟缓存
            )
            
            if not response or 'rates' not in response:
                # 返回默认汇率
                return self._get_default_currency_rates()
            
            return self._parse_currency_rates(response['rates'])
            
        except Exception as e:
            self._logger.error(f"获取货币汇率失败: {e}")
            # 返回默认汇率作为降级策略
            return self._get_default_currency_rates()
    
    async def get_popular_items(self, category: str, league: str = "Standard") -> List[MarketData]:
        """获取热门物品数据"""
        try:
            params = {
                'category': category,
                'league': league,
                'timeframe': '7d'  # 7天内的热门物品
            }
            
            cache_key = self._generate_cache_key('popular_items', params)
            
            response = await self._make_request(
                'GET',
                self.endpoints['popular_items'],
                params=params,
                cache_key=cache_key,
                cache_ttl=self.cache.config.market_data_ttl
            )
            
            if not response or 'items' not in response:
                return []
            
            # 解析热门物品数据
            popular_items = []
            for item_data in response['items']:
                market_data = self._parse_market_data(item_data, league)
                if market_data:
                    popular_items.append(market_data)
            
            return popular_items
            
        except Exception as e:
            self._logger.error(f"获取热门物品失败 ({category}): {e}")
            return []
    
    async def get_market_stats(self, league: str = "Standard") -> Dict[str, Any]:
        """获取市场统计数据"""
        try:
            cache_key = self._generate_cache_key('market_stats', {'league': league})
            
            response = await self._make_request(
                'GET',
                self.endpoints['market_stats'],
                params={'league': league},
                cache_key=cache_key,
                cache_ttl=1800  # 市场统计30分钟缓存
            )
            
            return response or {}
            
        except Exception as e:
            self._logger.error(f"获取市场统计失败: {e}")
            return {}
    
    async def get_available_leagues(self) -> List[str]:
        """获取可用的联盟列表"""
        try:
            cache_key = self._generate_cache_key('leagues', {})
            
            response = await self._make_request(
                'GET',
                self.endpoints['leagues'],
                cache_key=cache_key,
                cache_ttl=3600  # 联盟列表1小时缓存
            )
            
            if response and 'leagues' in response:
                return [league['name'] for league in response['leagues']]
            
            # 默认联盟列表
            return ["Standard", "Hardcore"]
            
        except Exception as e:
            self._logger.error(f"获取联盟列表失败: {e}")
            return ["Standard", "Hardcore"]
    
    def _build_search_filters(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """构建搜索过滤器"""
        filters = {}
        
        # 基础过滤器
        if 'name' in query:
            filters['name'] = query['name']
        
        if 'category' in query:
            filters['category'] = query['category']
        
        if 'rarity' in query:
            filters['rarity'] = query['rarity']
        
        # 价格范围过滤器
        if 'min_price' in query:
            filters['min_price'] = query['min_price']
        
        if 'max_price' in query:
            filters['max_price'] = query['max_price']
        
        if 'currency' in query:
            filters['currency'] = query['currency']
        
        # 属性过滤器
        if 'min_level' in query:
            filters['min_level'] = query['min_level']
        
        if 'max_level' in query:
            filters['max_level'] = query['max_level']
        
        # 链接和插槽过滤器
        if 'min_links' in query:
            filters['min_links'] = query['min_links']
        
        if 'min_sockets' in query:
            filters['min_sockets'] = query['min_sockets']
        
        return filters
    
    def _parse_market_data(self, item_data: Dict[str, Any], league: str) -> Optional[MarketData]:
        """解析市场数据"""
        try:
            # 提取基本信息
            item_id = item_data.get('id', '')
            name = item_data.get('name', '')
            category = item_data.get('category', 'Unknown')
            
            if not name:
                return None
            
            # 解析价格信息
            price_data = item_data.get('price', {})
            current_price = PricePoint(
                value=price_data.get('amount', 0.0),
                currency=price_data.get('currency', 'chaos'),
                timestamp=datetime.now()
            )
            
            # 解析历史价格（如果有）
            price_history = []
            if 'price_history' in item_data:
                for hist_price in item_data['price_history']:
                    price_point = PricePoint(
                        value=hist_price.get('amount', 0.0),
                        currency=hist_price.get('currency', 'chaos'),
                        timestamp=datetime.fromisoformat(hist_price.get('timestamp', datetime.now().isoformat()))
                    )
                    price_history.append(price_point)
            
            # 解析物品清单
            listings = []
            if 'listings' in item_data:
                for listing_data in item_data['listings'][:5]:  # 只取前5个
                    listing = ItemListing(
                        seller=listing_data.get('seller', 'Unknown'),
                        price=PricePoint(
                            value=listing_data.get('price', {}).get('amount', 0.0),
                            currency=listing_data.get('price', {}).get('currency', 'chaos'),
                            timestamp=datetime.now()
                        ),
                        stock=listing_data.get('stock', 1),
                        whisper_template=listing_data.get('whisper', ''),
                        account_name=listing_data.get('account', ''),
                        last_seen=datetime.now()
                    )
                    listings.append(listing)
            
            # 计算统计信息
            average_price = self._calculate_average_price(price_history + [current_price])
            min_price = min((p.value for p in price_history + [current_price] if p.value > 0), default=0)
            max_price = max((p.value for p in price_history + [current_price]), default=0)
            
            return MarketData(
                item_id=item_id,
                item_name=name,
                category=category,
                league=league,
                current_price=current_price,
                average_price=average_price,
                min_price=min_price,
                max_price=max_price,
                price_history=price_history,
                listings=listings,
                last_updated=datetime.now(),
                source="PoE2Scout",
                confidence_score=0.8  # PoE2Scout数据质量较高
            )
            
        except Exception as e:
            self._logger.error(f"解析市场数据失败: {e}")
            return None
    
    def _parse_currency_rates(self, rates_data: Dict[str, Any]) -> Dict[str, float]:
        """解析货币汇率数据"""
        try:
            parsed_rates = {}
            
            for currency, rate_info in rates_data.items():
                if isinstance(rate_info, (int, float)):
                    parsed_rates[currency] = float(rate_info)
                elif isinstance(rate_info, dict) and 'rate' in rate_info:
                    parsed_rates[currency] = float(rate_info['rate'])
            
            return parsed_rates
            
        except Exception as e:
            self._logger.error(f"解析货币汇率失败: {e}")
            return self._get_default_currency_rates()
    
    def _get_default_currency_rates(self) -> Dict[str, float]:
        """获取默认货币汇率（降级策略）"""
        return {
            'chaos': 1.0,
            'divine': 180.0,
            'exalted': 25.0,
            'ancient': 5.0,
            'chrome': 0.1,
            'fusing': 0.5,
            'jeweller': 0.2,
            'alchemy': 0.3,
            'alteration': 0.05
        }
    
    def _calculate_average_price(self, price_points: List[PricePoint]) -> float:
        """计算平均价格"""
        if not price_points:
            return 0.0
        
        valid_prices = [p.value for p in price_points if p.value > 0]
        if not valid_prices:
            return 0.0
        
        return sum(valid_prices) / len(valid_prices)
    
    async def test_connection(self) -> bool:
        """测试PoE2Scout连接"""
        try:
            response = await self._make_request('GET', '/api/v1/health', timeout=10)
            return response is not None
        except Exception:
            # 尝试获取联盟列表作为备用测试
            try:
                leagues = await self.get_available_leagues()
                return len(leagues) > 0
            except Exception:
                return False


# Mock数据提供者（作为最后的降级保障）
class MockPoE2ScoutAPI(IMarketProvider):
    """PoE2Scout Mock数据提供者"""
    
    def __init__(self):
        self.name = "MockPoE2Scout"
        self._logger = logging.getLogger(f"{__name__}.MockPoE2ScoutAPI")
    
    async def get_health_status(self) -> DataProviderStatus:
        return DataProviderStatus.HEALTHY
    
    async def test_connection(self) -> bool:
        return True
    
    def get_provider_name(self) -> str:
        return self.name
    
    def get_rate_limit_info(self) -> Dict[str, int]:
        return {'requests_per_minute': 999, 'requests_per_hour': 9999}
    
    async def get_item_price(self, item_name: str, league: str = "Standard") -> Optional[MarketData]:
        """返回Mock价格数据"""
        self._logger.warning(f"使用Mock数据: {item_name}")
        
        # 生成基于物品名称的Mock价格
        import hashlib
        hash_val = int(hashlib.md5(item_name.encode()).hexdigest()[:8], 16)
        base_price = (hash_val % 100) + 1  # 1-100 chaos
        
        current_price = PricePoint(
            value=float(base_price),
            currency='chaos',
            timestamp=datetime.now()
        )
        
        return MarketData(
            item_id=f"mock_{item_name.lower().replace(' ', '_')}",
            item_name=item_name,
            category="Mock",
            league=league,
            current_price=current_price,
            average_price=base_price,
            min_price=base_price * 0.8,
            max_price=base_price * 1.2,
            price_history=[current_price],
            listings=[],
            last_updated=datetime.now(),
            source="MockPoE2Scout",
            confidence_score=0.1  # Mock数据置信度低
        )
    
    async def search_items(self, query: Dict[str, Any], league: str = "Standard") -> List[MarketData]:
        """返回Mock搜索结果"""
        self._logger.warning("使用Mock搜索数据")
        
        # 返回几个Mock物品
        mock_items = ["Unique Sword", "Rare Bow", "Magic Shield"]
        results = []
        
        for item_name in mock_items:
            market_data = await self.get_item_price(item_name, league)
            if market_data:
                results.append(market_data)
        
        return results
    
    async def get_currency_rates(self, league: str = "Standard") -> Dict[str, float]:
        """返回Mock货币汇率"""
        self._logger.warning("使用Mock货币汇率")
        return {
            'chaos': 1.0,
            'divine': 180.0,
            'exalted': 25.0,
            'ancient': 5.0
        }
    
    async def get_popular_items(self, category: str, league: str = "Standard") -> List[MarketData]:
        """返回Mock热门物品"""
        self._logger.warning(f"使用Mock热门物品数据: {category}")
        return await self.search_items({'category': category}, league)