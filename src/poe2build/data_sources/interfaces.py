"""PoE2数据源接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from ..models.build import PoE2Build
from ..models.market import PoE2ItemMarketData
from ..models.characters import PoE2CharacterClass


class DataProviderStatus(Enum):
    """数据提供者状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


class IDataProvider(ABC):
    """基础数据提供者接口"""
    
    @abstractmethod
    async def get_health_status(self) -> DataProviderStatus:
        """获取提供者健康状态"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """测试连接状态"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供者名称"""
        pass
    
    @abstractmethod
    def get_rate_limit_info(self) -> Dict[str, int]:
        """获取速率限制信息"""
        pass


class IMarketProvider(IDataProvider):
    """市场数据提供者接口"""
    
    @abstractmethod
    async def get_item_price(self, item_name: str, league: str = "Standard") -> Optional[PoE2ItemMarketData]:
        """获取物品价格数据"""
        pass
    
    @abstractmethod
    async def search_items(self, query: Dict[str, Any], league: str = "Standard") -> List[PoE2ItemMarketData]:
        """搜索物品数据"""
        pass
    
    @abstractmethod
    async def get_currency_rates(self, league: str = "Standard") -> Dict[str, float]:
        """获取货币汇率"""
        pass
    
    @abstractmethod
    async def get_popular_items(self, category: str, league: str = "Standard") -> List[PoE2ItemMarketData]:
        """获取热门物品数据"""
        pass


class IBuildProvider(IDataProvider):
    """构筑数据提供者接口"""
    
    @abstractmethod
    async def get_popular_builds(self, character_class: Optional[PoE2CharacterClass] = None,
                               league: str = "Standard", limit: int = 20) -> List[PoE2Build]:
        """获取热门构筑数据"""
        pass
    
    @abstractmethod
    async def get_build_by_id(self, build_id: str) -> Optional[PoE2Build]:
        """根据ID获取构筑数据"""
        pass
    
    @abstractmethod
    async def search_builds(self, query: Dict[str, Any], limit: int = 20) -> List[PoE2Build]:
        """搜索构筑数据"""
        pass
    
    @abstractmethod
    async def get_meta_analysis(self, league: str = "Standard") -> Dict[str, Any]:
        """获取Meta分析数据"""
        pass
    
    @abstractmethod
    async def get_build_trends(self, timeframe: str = "7d") -> Dict[str, Any]:
        """获取构筑趋势数据"""
        pass


class IGameDataProvider(IDataProvider):
    """游戏数据提供者接口"""
    
    @abstractmethod
    async def get_skill_data(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """获取技能数据"""
        pass
    
    @abstractmethod
    async def get_item_data(self, item_name: str) -> Optional[Dict[str, Any]]:
        """获取物品数据"""
        pass
    
    @abstractmethod
    async def get_passive_tree_data(self) -> Dict[str, Any]:
        """获取天赋树数据"""
        pass
    
    @abstractmethod
    async def search_game_data(self, query: str, data_type: str) -> List[Dict[str, Any]]:
        """搜索游戏数据"""
        pass


class ICalculationProvider(IDataProvider):
    """计算提供者接口（PoB2相关）"""
    
    @abstractmethod
    async def calculate_build_stats(self, build_data: Dict[str, Any]) -> Dict[str, Any]:
        """计算构筑统计数据"""
        pass
    
    @abstractmethod
    async def validate_build(self, build_data: Dict[str, Any]) -> bool:
        """验证构筑有效性"""
        pass
    
    @abstractmethod
    async def generate_import_code(self, build_data: Dict[str, Any]) -> Optional[str]:
        """生成导入代码"""
        pass
    
    @abstractmethod
    async def parse_import_code(self, import_code: str) -> Optional[Dict[str, Any]]:
        """解析导入代码"""
        pass


class ICacheProvider(ABC):
    """缓存提供者接口"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        pass
    
    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        pass


# 数据提供者工厂接口
class IDataProviderFactory(ABC):
    """数据提供者工厂接口"""
    
    @abstractmethod
    def create_market_provider(self, provider_name: str) -> IMarketProvider:
        """创建市场数据提供者"""
        pass
    
    @abstractmethod
    def create_build_provider(self, provider_name: str) -> IBuildProvider:
        """创建构筑数据提供者"""
        pass
    
    @abstractmethod
    def create_game_data_provider(self, provider_name: str) -> IGameDataProvider:
        """创建游戏数据提供者"""
        pass
    
    @abstractmethod
    def create_calculation_provider(self, provider_name: str) -> ICalculationProvider:
        """创建计算提供者"""
        pass
    
    @abstractmethod
    def get_available_providers(self, provider_type: str) -> List[str]:
        """获取可用的提供者列表"""
        pass


# 错误处理相关
class DataProviderException(Exception):
    """数据提供者基础异常"""
    def __init__(self, message: str, provider_name: str = "", error_code: Optional[str] = None):
        self.message = message
        self.provider_name = provider_name
        self.error_code = error_code
        super().__init__(self.message)


class RateLimitException(DataProviderException):
    """速率限制异常"""
    def __init__(self, message: str, retry_after: Optional[int] = None, provider_name: str = ""):
        self.retry_after = retry_after
        super().__init__(message, provider_name, "RATE_LIMIT")


class ConnectionException(DataProviderException):
    """连接异常"""
    def __init__(self, message: str, provider_name: str = ""):
        super().__init__(message, provider_name, "CONNECTION_ERROR")


class DataNotFoundException(DataProviderException):
    """数据未找到异常"""
    def __init__(self, message: str, query: str = "", provider_name: str = ""):
        self.query = query
        super().__init__(message, provider_name, "DATA_NOT_FOUND")


class ValidationException(DataProviderException):
    """数据验证异常"""
    def __init__(self, message: str, field: str = "", provider_name: str = ""):
        self.field = field
        super().__init__(message, provider_name, "VALIDATION_ERROR")