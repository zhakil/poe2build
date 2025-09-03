"""
PoE2Scout API客户端 - 市场价格数据
https://poe2scout.com

提供实时物品价格、货币汇率、市场趋势数据
"""

import requests
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ItemPrice:
    """物品价格数据"""
    name: str
    base_type: str
    variant: Optional[str]
    price_chaos: float
    price_divine: float
    confidence: float
    listing_count: int
    last_updated: datetime


@dataclass
class CurrencyExchange:
    """货币汇率数据"""
    from_currency: str
    to_currency: str
    rate: float
    confidence: float
    volume: int
    last_updated: datetime


class PoE2ScoutClient:
    """PoE2Scout API客户端"""
    
    BASE_URL = "https://poe2scout.com/api"
    
    def __init__(self, cache_duration: int = 300):
        """
        初始化客户端
        
        Args:
            cache_duration: 缓存持续时间（秒）
        """
        self.cache_duration = cache_duration
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PoE2BuildGenerator/1.0 (Educational Purpose)',
            'Accept': 'application/json'
        })
        
        # 缓存
        self._item_cache: Dict[str, tuple] = {}  # (data, timestamp)
        self._currency_cache: Dict[str, tuple] = {}
        
        # 速率限制
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1秒间隔
    
    def _rate_limit(self):
        """实施速率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _is_cache_valid(self, timestamp: datetime) -> bool:
        """检查缓存是否有效"""
        return (datetime.now() - timestamp).seconds < self.cache_duration
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """发起API请求"""
        self._rate_limit()
        
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"PoE2Scout API请求失败: {e}")
            return {}
    
    def get_item_prices(self, item_name: str, league: str = "Rise of the Abyssal") -> List[ItemPrice]:
        """
        获取物品价格
        
        Args:
            item_name: 物品名称
            league: 联盟名称
            
        Returns:
            物品价格列表
        """
        cache_key = f"{item_name}_{league}"
        
        # 检查缓存
        if cache_key in self._item_cache:
            data, timestamp = self._item_cache[cache_key]
            if self._is_cache_valid(timestamp):
                return data
        
        # API请求
        params = {
            'item': item_name,
            'league': league
        }
        
        response = self._make_request('/items/search', params)
        
        prices = []
        for item_data in response.get('results', []):
            price = ItemPrice(
                name=item_data.get('name', ''),
                base_type=item_data.get('baseType', ''),
                variant=item_data.get('variant'),
                price_chaos=float(item_data.get('priceChaos', 0)),
                price_divine=float(item_data.get('priceDivine', 0)),
                confidence=float(item_data.get('confidence', 0)),
                listing_count=int(item_data.get('listingCount', 0)),
                last_updated=datetime.now()
            )
            prices.append(price)
        
        # 缓存结果
        self._item_cache[cache_key] = (prices, datetime.now())
        
        return prices
    
    def get_currency_rates(self, league: str = "Rise of the Abyssal") -> List[CurrencyExchange]:
        """
        获取货币汇率
        
        Args:
            league: 联盟名称
            
        Returns:
            货币汇率列表
        """
        cache_key = f"currency_{league}"
        
        # 检查缓存
        if cache_key in self._currency_cache:
            data, timestamp = self._currency_cache[cache_key]
            if self._is_cache_valid(timestamp):
                return data
        
        # API请求
        params = {'league': league}
        response = self._make_request('/currency', params)
        
        rates = []
        for rate_data in response.get('results', []):
            rate = CurrencyExchange(
                from_currency=rate_data.get('fromCurrency', ''),
                to_currency=rate_data.get('toCurrency', ''),
                rate=float(rate_data.get('rate', 0)),
                confidence=float(rate_data.get('confidence', 0)),
                volume=int(rate_data.get('volume', 0)),
                last_updated=datetime.now()
            )
            rates.append(rate)
        
        # 缓存结果
        self._currency_cache[cache_key] = (rates, datetime.now())
        
        return rates
    
    def get_build_cost_estimate(self, item_list: List[str], league: str = "Standard") -> Dict[str, Any]:
        """
        估算构筑成本
        
        Args:
            item_list: 物品名称列表
            league: 联盟名称
            
        Returns:
            成本估算信息
        """
        total_chaos = 0
        total_divine = 0
        item_costs = []
        
        for item_name in item_list:
            prices = self.get_item_prices(item_name, league)
            if prices:
                # 取第一个价格（通常是最优价格）
                best_price = prices[0]
                total_chaos += best_price.price_chaos
                total_divine += best_price.price_divine
                
                item_costs.append({
                    'item': item_name,
                    'price_chaos': best_price.price_chaos,
                    'price_divine': best_price.price_divine,
                    'confidence': best_price.confidence
                })
        
        return {
            'total_chaos': total_chaos,
            'total_divine': total_divine,
            'item_breakdown': item_costs,
            'currency_used': 'mixed' if total_divine > 0 else 'chaos',
            'confidence_avg': sum(item['confidence'] for item in item_costs) / len(item_costs) if item_costs else 0,
            'last_updated': datetime.now()
        }
    
    def search_similar_items(self, base_type: str, min_price: float = None, max_price: float = None) -> List[ItemPrice]:
        """
        搜索相似物品
        
        Args:
            base_type: 物品基底类型
            min_price: 最低价格
            max_price: 最高价格
            
        Returns:
            相似物品价格列表
        """
        params = {
            'baseType': base_type
        }
        
        if min_price:
            params['minPrice'] = min_price
        if max_price:
            params['maxPrice'] = max_price
        
        response = self._make_request('/items/similar', params)
        
        items = []
        for item_data in response.get('results', []):
            item = ItemPrice(
                name=item_data.get('name', ''),
                base_type=item_data.get('baseType', ''),
                variant=item_data.get('variant'),
                price_chaos=float(item_data.get('priceChaos', 0)),
                price_divine=float(item_data.get('priceDivine', 0)),
                confidence=float(item_data.get('confidence', 0)),
                listing_count=int(item_data.get('listingCount', 0)),
                last_updated=datetime.now()
            )
            items.append(item)
        
        return items


# 全局实例
_client = None

def get_poe2scout_client() -> PoE2ScoutClient:
    """获取全局PoE2Scout客户端实例"""
    global _client
    if _client is None:
        _client = PoE2ScoutClient()
    return _client