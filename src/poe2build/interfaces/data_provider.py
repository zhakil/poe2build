# -*- coding: utf-8 -*-
"""
数据源提供者接口定义

本模块定义了PoE2数据源的抽象接口，支持多种数据类型的获取和管理。
设计遵循接口分离原则，为不同类型的数据源提供专用接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from ..models import PoE2Item, PoE2Build, PoE2Character, PoE2CurrencyType, PoE2LeagueType


class DataProviderStatus(Enum):
    """数据源提供者状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    MAINTENANCE = "maintenance"


@dataclass
class DataResponse:
    """数据响应基类"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    timestamp: datetime = None
    source: Optional[str] = None
    cache_hit: bool = False
    response_time_ms: int = 0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class MarketDataRequest:
    """市场数据请求"""
    item_name: Optional[str] = None
    item_type: Optional[str] = None
    league: PoE2LeagueType = PoE2LeagueType.STANDARD
    currency: PoE2CurrencyType = PoE2CurrencyType.DIVINE_ORB
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    limit: int = 100


@dataclass
class BuildDataRequest:
    """构筑数据请求"""
    character_class: Optional[str] = None
    ascendancy: Optional[str] = None
    skill_name: Optional[str] = None
    league: PoE2LeagueType = PoE2LeagueType.STANDARD
    min_level: int = 1
    max_level: int = 100
    limit: int = 50


@dataclass 
class GameDataRequest:
    """游戏数据请求"""
    data_type: str  # "skills", "items", "passives", "classes"
    name: Optional[str] = None
    category: Optional[str] = None
    level_range: Optional[tuple] = None


class IDataProvider(ABC):
    """数据源提供者基础接口
    
    定义所有数据源都应该实现的基础方法，包括健康检查、缓存管理等。
    """
    
    @abstractmethod
    def get_status(self) -> DataProviderStatus:
        """获取数据源状态
        
        Returns:
            DataProviderStatus: 当前数据源状态
        """
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """执行健康检查
        
        Returns:
            Dict[str, Any]: 健康检查结果，包含详细状态信息
        """
        pass
    
    @abstractmethod
    def clear_cache(self) -> bool:
        """清空缓存
        
        Returns:
            bool: 缓存清理是否成功
        """
        pass
    
    @abstractmethod
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 缓存命中率、大小等统计信息
        """
        pass
    
    def is_available(self) -> bool:
        """检查数据源是否可用
        
        Returns:
            bool: 数据源是否可用
        """
        return self.get_status() in [DataProviderStatus.HEALTHY, DataProviderStatus.DEGRADED]


class IMarketDataProvider(IDataProvider):
    """市场数据提供者接口
    
    专门用于获取PoE2市场和交易数据，包括物品价格、市场趋势等。
    """
    
    @abstractmethod
    def fetch_market_data(self, request: MarketDataRequest) -> DataResponse:
        """获取市场数据
        
        Args:
            request (MarketDataRequest): 市场数据请求
            
        Returns:
            DataResponse: 包含市场数据的响应
        """
        pass
    
    @abstractmethod
    def fetch_item_prices(self, item_name: str, league: PoE2LeagueType = PoE2LeagueType.STANDARD) -> DataResponse:
        """获取物品价格信息
        
        Args:
            item_name (str): 物品名称
            league (PoE2LeagueType): 联盟类型
            
        Returns:
            DataResponse: 包含价格信息的响应
        """
        pass
    
    @abstractmethod
    def fetch_currency_rates(self, league: PoE2LeagueType = PoE2LeagueType.STANDARD) -> DataResponse:
        """获取货币汇率
        
        Args:
            league (PoE2LeagueType): 联盟类型
            
        Returns:
            DataResponse: 包含货币汇率的响应
        """
        pass
    
    @abstractmethod
    def fetch_market_trends(self, item_name: str, days: int = 7) -> DataResponse:
        """获取市场趋势数据
        
        Args:
            item_name (str): 物品名称
            days (int): 获取多少天的趋势数据
            
        Returns:
            DataResponse: 包含趋势数据的响应
        """
        pass
    
    @abstractmethod
    def search_items(self, query: Dict[str, Any], league: PoE2LeagueType = PoE2LeagueType.STANDARD) -> DataResponse:
        """搜索物品
        
        Args:
            query (Dict[str, Any]): 搜索条件
            league (PoE2LeagueType): 联盟类型
            
        Returns:
            DataResponse: 包含搜索结果的响应
        """
        pass


class IBuildDataProvider(IDataProvider):
    """构筑数据提供者接口
    
    专门用于获取PoE2构筑相关数据，包括流行构筑、构筑统计等。
    """
    
    @abstractmethod
    def fetch_build_data(self, request: BuildDataRequest) -> DataResponse:
        """获取构筑数据
        
        Args:
            request (BuildDataRequest): 构筑数据请求
            
        Returns:
            DataResponse: 包含构筑数据的响应
        """
        pass
    
    @abstractmethod
    def fetch_popular_builds(self, character_class: Optional[str] = None, league: PoE2LeagueType = PoE2LeagueType.STANDARD, limit: int = 50) -> DataResponse:
        """获取流行构筑
        
        Args:
            character_class (Optional[str]): 角色职业过滤
            league (PoE2LeagueType): 联盟类型
            limit (int): 返回结果数量限制
            
        Returns:
            DataResponse: 包含流行构筑的响应
        """
        pass
    
    @abstractmethod
    def fetch_build_details(self, build_id: str) -> DataResponse:
        """获取构筑详细信息
        
        Args:
            build_id (str): 构筑ID
            
        Returns:
            DataResponse: 包含构筑详情的响应
        """
        pass
    
    @abstractmethod
    def fetch_build_statistics(self, character_class: Optional[str] = None, league: PoE2LeagueType = PoE2LeagueType.STANDARD) -> DataResponse:
        """获取构筑统计信息
        
        Args:
            character_class (Optional[str]): 角色职业过滤
            league (PoE2LeagueType): 联盟类型
            
        Returns:
            DataResponse: 包含构筑统计的响应
        """
        pass
    
    @abstractmethod
    def search_builds(self, query: Dict[str, Any]) -> DataResponse:
        """搜索构筑
        
        Args:
            query (Dict[str, Any]): 搜索条件
            
        Returns:
            DataResponse: 包含搜索结果的响应
        """
        pass


class IGameDataProvider(IDataProvider):
    """游戏数据提供者接口
    
    专门用于获取PoE2游戏静态数据，包括技能、物品、天赋树等基础数据。
    """
    
    @abstractmethod
    def fetch_game_data(self, request: GameDataRequest) -> DataResponse:
        """获取游戏数据
        
        Args:
            request (GameDataRequest): 游戏数据请求
            
        Returns:
            DataResponse: 包含游戏数据的响应
        """
        pass
    
    @abstractmethod
    def fetch_skill_data(self, skill_name: Optional[str] = None) -> DataResponse:
        """获取技能数据
        
        Args:
            skill_name (Optional[str]): 技能名称，为None时获取所有技能
            
        Returns:
            DataResponse: 包含技能数据的响应
        """
        pass
    
    @abstractmethod
    def fetch_item_data(self, item_name: Optional[str] = None, category: Optional[str] = None) -> DataResponse:
        """获取物品数据
        
        Args:
            item_name (Optional[str]): 物品名称，为None时获取所有物品
            category (Optional[str]): 物品类别过滤
            
        Returns:
            DataResponse: 包含物品数据的响应
        """
        pass
    
    @abstractmethod
    def fetch_passive_tree_data(self, character_class: Optional[str] = None) -> DataResponse:
        """获取天赋树数据
        
        Args:
            character_class (Optional[str]): 角色职业过滤
            
        Returns:
            DataResponse: 包含天赋树数据的响应
        """
        pass
    
    @abstractmethod
    def fetch_character_data(self) -> DataResponse:
        """获取角色数据
        
        Returns:
            DataResponse: 包含角色数据的响应
        """
        pass
    
    @abstractmethod
    def fetch_atlas_data(self) -> DataResponse:
        """获取地图册数据
        
        Returns:
            DataResponse: 包含地图册数据的响应
        """
        pass


class IPoB2DataProvider(IDataProvider):
    """PoB2数据提供者接口
    
    专门用于Path of Building Community (PoB2)集成，提供构筑导入导出和计算功能。
    """
    
    @abstractmethod
    def import_build_from_code(self, import_code: str) -> DataResponse:
        """从导入码导入构筑
        
        Args:
            import_code (str): PoB2导入码
            
        Returns:
            DataResponse: 包含导入的构筑数据
        """
        pass
    
    @abstractmethod
    def export_build_to_code(self, build_data: Dict[str, Any]) -> DataResponse:
        """将构筑导出为导入码
        
        Args:
            build_data (Dict[str, Any]): 构筑数据
            
        Returns:
            DataResponse: 包含导出的导入码
        """
        pass
    
    @abstractmethod
    def validate_build(self, build_data: Dict[str, Any]) -> DataResponse:
        """验证构筑有效性
        
        Args:
            build_data (Dict[str, Any]): 构筑数据
            
        Returns:
            DataResponse: 包含验证结果
        """
        pass
    
    @abstractmethod
    def calculate_build_stats(self, build_data: Dict[str, Any]) -> DataResponse:
        """计算构筑统计数据
        
        Args:
            build_data (Dict[str, Any]): 构筑数据
            
        Returns:
            DataResponse: 包含计算的统计数据
        """
        pass