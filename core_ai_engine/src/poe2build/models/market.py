"""PoE2市场数据模型"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime


class PoE2CurrencyType(Enum):
    """PoE2货币类型枚举"""
    # 主要货币
    DIVINE_ORB = "divine"
    EXALTED_ORB = "exalted"
    CHAOS_ORB = "chaos"
    # 其他货币
    ANCIENT_ORB = "ancient"
    TRANSMUTATION_ORB = "transmutation"
    AUGMENTATION_ORB = "augmentation"
    ALTERATION_ORB = "alteration"
    REGAL_ORB = "regal"
    ALCHEMY_ORB = "alchemy"
    CHROMATIC_ORB = "chromatic"
    JEWELLER_ORB = "jeweller"
    FUSING_ORB = "fusing"
    # PoE2特有货币
    ARTIFICER_ORB = "artificer"  # PoE2新增
    VAAL_ORB = "vaal"
    # 碎片和其他
    PORTAL_SCROLL = "portal"
    WISDOM_SCROLL = "wisdom"


class PoE2LeagueType(Enum):
    """PoE2联盟类型枚举"""
    STANDARD = "Standard"
    HARDCORE = "Hardcore"
    
    # PoE2早期访问赛季
    EARLY_ACCESS = "Early Access"
    EARLY_ACCESS_HARDCORE = "Early Access Hardcore"
    
    # 赛季联盟 - 更新到最新赛季
    RISE_OF_THE_ABYSSAL = "Rise of the Abyssal"           # 第3赛季 - 深渊崛起（当前最新）
    RISE_OF_THE_ABYSSAL_HARDCORE = "Rise of the Abyssal Hardcore"
    
    # 历史赛季
    NECROPOLISES = "Necropolises"           # 第2赛季 - 死灵城
    NECROPOLISES_HARDCORE = "Necropolises Hardcore"
    
    # SSF模式
    SOLO_SELF_FOUND = "SSF"
    HARDCORE_SSF = "Hardcore SSF"
    
    # 当前活跃联盟别名
    CURRENT_LEAGUE = "Rise of the Abyssal"         # 指向当前最新赛季
    CURRENT_HARDCORE = "Rise of the Abyssal Hardcore"


class PoE2MarketTrend(Enum):
    """PoE2市场趋势枚举"""
    RISING = "rising"           # 上涨
    FALLING = "falling"         # 下跌
    STABLE = "stable"           # 稳定
    VOLATILE = "volatile"       # 波动剧烈
    UNKNOWN = "unknown"         # 未知


@dataclass
class PoE2PriceData:
    """PoE2价格数据模型"""
    value: float
    currency: PoE2CurrencyType
    confidence: float = 1.0     # 价格可靠度 0-1
    sample_size: int = 1        # 样本数量
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        """验证价格数据"""
        if self.value < 0:
            raise ValueError("Price value cannot be negative")
        
        if not 0 <= self.confidence <= 1:
            raise ValueError("Price confidence must be between 0 and 1")
        
        if self.sample_size < 1:
            raise ValueError("Sample size must be at least 1")
        
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_divine(self, currency_rates: Dict[PoE2CurrencyType, float]) -> float:
        """转换为神圣石价格"""
        if self.currency == PoE2CurrencyType.DIVINE_ORB:
            return self.value
        
        rate = currency_rates.get(self.currency)
        if rate is None:
            raise ValueError(f"No exchange rate found for {self.currency.value}")
        
        return self.value * rate
    
    def to_chaos(self, currency_rates: Dict[PoE2CurrencyType, float]) -> float:
        """转换为混沌石价格"""
        if self.currency == PoE2CurrencyType.CHAOS_ORB:
            return self.value
        
        # 先转换为神圣石，再转为混沌石
        divine_value = self.to_divine(currency_rates)
        chaos_per_divine = currency_rates.get(PoE2CurrencyType.CHAOS_ORB, 1.0)
        return divine_value / chaos_per_divine
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'value': self.value,
            'currency': self.currency.value,
            'confidence': self.confidence,
            'sample_size': self.sample_size,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PoE2PriceData':
        """从字典创建价格数据"""
        return cls(
            value=data['value'],
            currency=PoE2CurrencyType(data['currency']),
            confidence=data.get('confidence', 1.0),
            sample_size=data.get('sample_size', 1),
            timestamp=data.get('timestamp')
        )


@dataclass
class PoE2MarketTrendData:
    """PoE2市场趋势数据"""
    trend: PoE2MarketTrend
    change_percent: float       # 变化百分比
    volume: int = 0            # 交易量
    period_days: int = 7       # 统计周期（天）
    
    def __post_init__(self):
        """验证趋势数据"""
        if self.volume < 0:
            raise ValueError("Trading volume cannot be negative")
        
        if self.period_days < 1:
            raise ValueError("Period must be at least 1 day")
    
    def is_significant_change(self, threshold: float = 10.0) -> bool:
        """判断是否为显著变化"""
        return abs(self.change_percent) >= threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'trend': self.trend.value,
            'change_percent': self.change_percent,
            'volume': self.volume,
            'period_days': self.period_days,
            'is_significant': self.is_significant_change()
        }


@dataclass
class PoE2MarketListing:
    """PoE2市场物品挂单数据"""
    item_name: str
    price: PoE2PriceData
    seller: str
    league: PoE2LeagueType
    # 物品详情
    item_level: Optional[int] = None
    quality: Optional[int] = None
    corrupted: bool = False
    # 挂单信息
    listing_time: Optional[str] = None
    account_name: Optional[str] = None
    character_name: Optional[str] = None
    whisper_template: Optional[str] = None
    # 位置信息
    stash_tab: Optional[str] = None
    x_position: Optional[int] = None
    y_position: Optional[int] = None
    
    def __post_init__(self):
        """验证挂单数据"""
        if not self.item_name.strip():
            raise ValueError("Item name cannot be empty")
        
        if not self.seller.strip():
            raise ValueError("Seller name cannot be empty")
        
        if not self.listing_time:
            self.listing_time = datetime.now().isoformat()
        
        if self.item_level is not None and not 1 <= self.item_level <= 100:
            raise ValueError("Item level must be between 1 and 100")
        
        if self.quality is not None and not 0 <= self.quality <= 30:
            raise ValueError("Item quality must be between 0% and 30%")
    
    def generate_whisper(self) -> str:
        """生成交易密语"""
        if self.whisper_template:
            return self.whisper_template
        
        price_text = f"{self.price.value} {self.price.currency.value}"
        return f"Hi, I would like to buy your {self.item_name} for {price_text} in {self.league.value}."
    
    def is_recent_listing(self, hours: int = 24) -> bool:
        """检查是否为近期挂单"""
        if not self.listing_time:
            return False
        
        try:
            listing_dt = datetime.fromisoformat(self.listing_time)
            current_dt = datetime.now()
            time_diff = current_dt - listing_dt
            return time_diff.total_seconds() <= hours * 3600
        except:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'item_name': self.item_name,
            'price': self.price.to_dict(),
            'seller': self.seller,
            'league': self.league.value,
            'item_details': {
                'item_level': self.item_level,
                'quality': self.quality,
                'corrupted': self.corrupted
            },
            'listing_info': {
                'listing_time': self.listing_time,
                'account_name': self.account_name,
                'character_name': self.character_name,
                'whisper_template': self.whisper_template
            },
            'location': {
                'stash_tab': self.stash_tab,
                'x_position': self.x_position,
                'y_position': self.y_position
            }
        }
    
    @classmethod 
    def from_dict(cls, data: Dict[str, Any]) -> 'PoE2MarketListing':
        """从字典创建挂单数据"""
        price = PoE2PriceData.from_dict(data['price'])
        item_details = data.get('item_details', {})
        listing_info = data.get('listing_info', {})
        location = data.get('location', {})
        
        return cls(
            item_name=data['item_name'],
            price=price,
            seller=data['seller'],
            league=PoE2LeagueType(data['league']),
            item_level=item_details.get('item_level'),
            quality=item_details.get('quality'),
            corrupted=item_details.get('corrupted', False),
            listing_time=listing_info.get('listing_time'),
            account_name=listing_info.get('account_name'),
            character_name=listing_info.get('character_name'),
            whisper_template=listing_info.get('whisper_template'),
            stash_tab=location.get('stash_tab'),
            x_position=location.get('x_position'),
            y_position=location.get('y_position')
        )


@dataclass
class PoE2ItemMarketData:
    """PoE2物品市场数据汇总"""
    item_name: str
    league: PoE2LeagueType
    # 价格统计
    average_price: Optional[PoE2PriceData] = None
    median_price: Optional[PoE2PriceData] = None
    min_price: Optional[PoE2PriceData] = None
    max_price: Optional[PoE2PriceData] = None
    # 市场活跃度
    total_listings: int = 0
    active_listings: int = 0    # 24小时内的挂单
    trend: Optional[PoE2MarketTrendData] = None
    # 数据更新信息
    last_updated: Optional[str] = None
    data_source: str = "unknown"
    
    def __post_init__(self):
        """验证市场数据"""
        if not self.item_name.strip():
            raise ValueError("Item name cannot be empty")
        
        if self.total_listings < 0:
            raise ValueError("Total listings cannot be negative")
        
        if self.active_listings < 0:
            raise ValueError("Active listings cannot be negative")
        
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()
    
    def get_price_range(self) -> Optional[Dict[str, float]]:
        """获取价格范围"""
        if not self.min_price or not self.max_price:
            return None
        
        if self.min_price.currency != self.max_price.currency:
            return None  # 货币类型不同，无法比较
        
        return {
            'min': self.min_price.value,
            'max': self.max_price.value,
            'range': self.max_price.value - self.min_price.value,
            'currency': self.min_price.currency.value
        }
    
    def get_liquidity_score(self) -> float:
        """计算流动性评分 (0-1)"""
        if self.total_listings == 0:
            return 0.0
        
        # 基于活跃挂单比例
        active_ratio = self.active_listings / self.total_listings
        
        # 基于总挂单数量
        listing_score = min(1.0, self.total_listings / 100)  # 100个挂单为满分
        
        return (active_ratio * 0.7) + (listing_score * 0.3)
    
    def is_data_fresh(self, max_age_hours: int = 6) -> bool:
        """检查数据是否新鲜"""
        if not self.last_updated:
            return False
        
        try:
            update_dt = datetime.fromisoformat(self.last_updated)
            current_dt = datetime.now()
            time_diff = current_dt - update_dt
            return time_diff.total_seconds() <= max_age_hours * 3600
        except:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'item_name': self.item_name,
            'league': self.league.value,
            'price_statistics': {
                'average_price': self.average_price.to_dict() if self.average_price else None,
                'median_price': self.median_price.to_dict() if self.median_price else None,
                'min_price': self.min_price.to_dict() if self.min_price else None,
                'max_price': self.max_price.to_dict() if self.max_price else None,
                'price_range': self.get_price_range()
            },
            'market_activity': {
                'total_listings': self.total_listings,
                'active_listings': self.active_listings,
                'liquidity_score': self.get_liquidity_score()
            },
            'trend': self.trend.to_dict() if self.trend else None,
            'metadata': {
                'last_updated': self.last_updated,
                'data_source': self.data_source,
                'is_fresh': self.is_data_fresh()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PoE2ItemMarketData':
        """从字典创建市场数据"""
        price_stats = data.get('price_statistics', {})
        market_activity = data.get('market_activity', {})
        metadata = data.get('metadata', {})
        
        # 解析价格数据
        average_price = None
        if price_stats.get('average_price'):
            average_price = PoE2PriceData.from_dict(price_stats['average_price'])
        
        median_price = None
        if price_stats.get('median_price'):
            median_price = PoE2PriceData.from_dict(price_stats['median_price'])
        
        min_price = None
        if price_stats.get('min_price'):
            min_price = PoE2PriceData.from_dict(price_stats['min_price'])
        
        max_price = None
        if price_stats.get('max_price'):
            max_price = PoE2PriceData.from_dict(price_stats['max_price'])
        
        # 解析趋势数据
        trend = None
        if data.get('trend'):
            trend_data = data['trend']
            trend = PoE2MarketTrendData(
                trend=PoE2MarketTrend(trend_data['trend']),
                change_percent=trend_data['change_percent'],
                volume=trend_data.get('volume', 0),
                period_days=trend_data.get('period_days', 7)
            )
        
        return cls(
            item_name=data['item_name'],
            league=PoE2LeagueType(data['league']),
            average_price=average_price,
            median_price=median_price,
            min_price=min_price,
            max_price=max_price,
            total_listings=market_activity.get('total_listings', 0),
            active_listings=market_activity.get('active_listings', 0),
            trend=trend,
            last_updated=metadata.get('last_updated'),
            data_source=metadata.get('data_source', 'unknown')
        )


@dataclass
class PoE2CurrencyExchangeRate:
    """PoE2货币汇率数据"""
    from_currency: PoE2CurrencyType
    to_currency: PoE2CurrencyType
    rate: float                 # 汇率
    volume: int = 0            # 交易量
    confidence: float = 1.0    # 汇率可靠度
    last_updated: Optional[str] = None
    
    def __post_init__(self):
        """验证汇率数据"""
        if self.rate <= 0:
            raise ValueError("Exchange rate must be positive")
        
        if not 0 <= self.confidence <= 1:
            raise ValueError("Exchange rate confidence must be between 0 and 1")
        
        if self.volume < 0:
            raise ValueError("Exchange volume cannot be negative")
        
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()
    
    def get_reverse_rate(self) -> float:
        """获取反向汇率"""
        return 1.0 / self.rate
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'from_currency': self.from_currency.value,
            'to_currency': self.to_currency.value,
            'rate': self.rate,
            'reverse_rate': self.get_reverse_rate(),
            'volume': self.volume,
            'confidence': self.confidence,
            'last_updated': self.last_updated
        }


# 市场数据相关工具函数
def filter_listings_by_price_range(listings: List[PoE2MarketListing],
                                  min_price: float,
                                  max_price: float,
                                  currency: PoE2CurrencyType) -> List[PoE2MarketListing]:
    """按价格范围过滤挂单"""
    filtered = []
    for listing in listings:
        if (listing.price.currency == currency and
            min_price <= listing.price.value <= max_price):
            filtered.append(listing)
    return filtered


def filter_listings_by_league(listings: List[PoE2MarketListing],
                             league: PoE2LeagueType) -> List[PoE2MarketListing]:
    """按联盟过滤挂单"""
    return [listing for listing in listings if listing.league == league]


def sort_listings_by_price(listings: List[PoE2MarketListing],
                          ascending: bool = True) -> List[PoE2MarketListing]:
    """按价格排序挂单（同货币类型）"""
    # 按货币类型分组
    currency_groups = {}
    for listing in listings:
        currency = listing.price.currency
        if currency not in currency_groups:
            currency_groups[currency] = []
        currency_groups[currency].append(listing)
    
    # 对每个货币类型组内排序
    sorted_listings = []
    for currency, group in currency_groups.items():
        sorted_group = sorted(group, key=lambda x: x.price.value, reverse=not ascending)
        sorted_listings.extend(sorted_group)
    
    return sorted_listings


def calculate_market_statistics(listings: List[PoE2MarketListing],
                              currency: PoE2CurrencyType) -> Dict[str, float]:
    """计算市场统计数据"""
    # 筛选指定货币的挂单
    currency_listings = [l for l in listings if l.price.currency == currency]
    
    if not currency_listings:
        return {'count': 0}
    
    prices = [listing.price.value for listing in currency_listings]
    
    return {
        'count': len(prices),
        'min': min(prices),
        'max': max(prices),
        'average': sum(prices) / len(prices),
        'median': sorted(prices)[len(prices) // 2],
        'std_dev': calculate_std_dev(prices)
    }


def calculate_std_dev(values: List[float]) -> float:
    """计算标准差"""
    if len(values) <= 1:
        return 0.0
    
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance ** 0.5


def estimate_item_value(item_name: str,
                       market_data: List[PoE2ItemMarketData],
                       fallback_value: float = 1.0) -> float:
    """估算物品价值"""
    # 查找匹配的市场数据
    for data in market_data:
        if data.item_name.lower() == item_name.lower():
            if data.average_price:
                return data.average_price.value
            elif data.median_price:
                return data.median_price.value
    
    return fallback_value


def find_arbitrage_opportunities(exchange_rates: List[PoE2CurrencyExchangeRate],
                               min_profit_percent: float = 5.0) -> List[Dict[str, Any]]:
    """查找套利机会"""
    opportunities = []
    
    # 创建汇率映射
    rate_map = {}
    for rate_data in exchange_rates:
        key = (rate_data.from_currency, rate_data.to_currency)
        rate_map[key] = rate_data.rate
    
    # 检查三角套利
    currencies = list(set(r.from_currency for r in exchange_rates) | 
                     set(r.to_currency for r in exchange_rates))
    
    for curr_a in currencies:
        for curr_b in currencies:
            for curr_c in currencies:
                if curr_a != curr_b and curr_b != curr_c and curr_a != curr_c:
                    # A -> B -> C -> A
                    rate_ab = rate_map.get((curr_a, curr_b))
                    rate_bc = rate_map.get((curr_b, curr_c))
                    rate_ca = rate_map.get((curr_c, curr_a))
                    
                    if rate_ab and rate_bc and rate_ca:
                        final_amount = rate_ab * rate_bc * rate_ca
                        profit_percent = (final_amount - 1.0) * 100
                        
                        if profit_percent >= min_profit_percent:
                            opportunities.append({
                                'path': [curr_a.value, curr_b.value, curr_c.value, curr_a.value],
                                'rates': [rate_ab, rate_bc, rate_ca],
                                'profit_percent': profit_percent,
                                'final_multiplier': final_amount
                            })
    
    return sorted(opportunities, key=lambda x: x['profit_percent'], reverse=True)