"""
PoE2 Scout API集成 - 提供市场数据和构筑趋势
官网: https://poe2scout.com
"""

import requests
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode

from .base_data_source import BaseDataSource
from ..resilience import create_poe2_scout_service, PoE2FallbackProvider

logger = logging.getLogger(__name__)

class PoE2ScoutAPI(BaseDataSource):
    """PoE2 Scout API客户端"""
    
    BASE_URL = "https://poe2scout.com/api"
    
    def __init__(self, 
                 use_resilience: bool = True,
                 api_key: Optional[str] = None):
        """
        初始化PoE2 Scout API客户端
        
        Args:
            use_resilience: 是否使用弹性服务
            api_key: API密钥（如果需要）
        """
        # 初始化弹性服务和降级提供者
        resilient_service = create_poe2_scout_service() if use_resilience else None
        fallback_provider = PoE2FallbackProvider()
        
        super().__init__(
            source_name="poe2_scout",
            resilient_service=resilient_service,
            fallback_provider=fallback_provider
        )
        
        self.api_key = api_key
        self.session = requests.Session()
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'PoE2BuildGenerator/1.0 (Educational-Research-Tool)',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'
            
    def get_market_data(self, league: str = "Standard", **kwargs) -> Dict[str, Any]:
        """
        获取市场数据
        
        Args:
            league: 联盟名称
            **kwargs: 其他参数（item_type, category等）
            
        Returns:
            市场数据响应
        """
        cache_key = self._generate_cache_key("market_data", league=league, **kwargs)
        
        def _fetch_market_data():
            params = {"league": league}
            params.update(kwargs)
            
            # 根据参数构建不同的API端点
            if kwargs.get("item_name"):
                endpoint = f"{self.BASE_URL}/items/{kwargs['item_name']}/market"
            elif kwargs.get("category"):
                endpoint = f"{self.BASE_URL}/market/{kwargs['category']}"
            else:
                endpoint = f"{self.BASE_URL}/market/overview"
                
            response = self._make_request(endpoint, params)
            return self._parse_market_response(response)
            
        return self._make_resilient_call("get_market_data", _fetch_market_data, cache_key)
        
    def get_build_data(self, class_name: str = None, **kwargs) -> Dict[str, Any]:
        """
        获取构筑数据和趋势
        
        Args:
            class_name: 职业名称
            **kwargs: 其他参数（ascendancy, skill等）
            
        Returns:
            构筑数据响应
        """
        cache_key = self._generate_cache_key("build_data", class_name=class_name, **kwargs)
        
        def _fetch_build_data():
            params = {}
            if class_name:
                params["class"] = class_name
            params.update(kwargs)
            
            endpoint = f"{self.BASE_URL}/builds/trends"
            response = self._make_request(endpoint, params)
            return self._parse_build_response(response)
            
        return self._make_resilient_call("get_build_data", _fetch_build_data, cache_key)
        
    def get_item_data(self, item_name: str = None, **kwargs) -> Dict[str, Any]:
        """
        获取物品数据和价格信息
        
        Args:
            item_name: 物品名称
            **kwargs: 其他参数（league, variant等）
            
        Returns:
            物品数据响应
        """
        cache_key = self._generate_cache_key("item_data", item_name=item_name, **kwargs)
        
        def _fetch_item_data():
            if not item_name:
                # 获取热门物品列表
                endpoint = f"{self.BASE_URL}/items/popular"
            else:
                endpoint = f"{self.BASE_URL}/items/{item_name}"
                
            params = kwargs
            response = self._make_request(endpoint, params)
            return self._parse_item_response(response)
            
        return self._make_resilient_call("get_item_data", _fetch_item_data, cache_key)
        
    def get_currency_rates(self, league: str = "Standard") -> Dict[str, Any]:
        """
        获取货币汇率
        
        Args:
            league: 联盟名称
            
        Returns:
            货币汇率数据
        """
        cache_key = self._generate_cache_key("currency_rates", league=league)
        
        def _fetch_currency_rates():
            endpoint = f"{self.BASE_URL}/currency/{league}"
            response = self._make_request(endpoint, {})
            return self._parse_currency_response(response)
            
        return self._make_resilient_call("get_currency_rates", _fetch_currency_rates, cache_key)
        
    def search_items(self, 
                    query: str, 
                    league: str = "Standard",
                    limit: int = 20) -> Dict[str, Any]:
        """
        搜索物品
        
        Args:
            query: 搜索查询
            league: 联盟名称
            limit: 结果限制
            
        Returns:
            搜索结果
        """
        cache_key = self._generate_cache_key("search_items", query=query, league=league, limit=limit)
        
        def _fetch_search_results():
            params = {
                "q": query,
                "league": league,
                "limit": limit
            }
            endpoint = f"{self.BASE_URL}/search"
            response = self._make_request(endpoint, params)
            return self._parse_search_response(response)
            
        return self._make_resilient_call("search_items", _fetch_search_results, cache_key)
        
    def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            服务是否可用
        """
        try:
            endpoint = f"{self.BASE_URL}/health"
            response = self._make_request(endpoint, {}, timeout=5)
            return response.get("status") == "ok"
        except Exception as e:
            logger.error(f"Health check failed for {self.source_name}: {e}")
            return False
            
    def _make_request(self, url: str, params: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        """
        发起HTTP请求
        
        Args:
            url: 请求URL
            params: 请求参数
            timeout: 超时时间
            
        Returns:
            响应数据
            
        Raises:
            requests.RequestException: 请求失败时抛出
        """
        try:
            if params:
                url = f"{url}?{urlencode(params)}"
                
            response = self.session.get(url, timeout=timeout)
            
            # 检查响应状态
            if response.status_code == 429:
                raise requests.RequestException(f"Rate limit exceeded for {self.source_name}")
            elif response.status_code >= 500:
                raise requests.RequestException(f"Server error {response.status_code}: {response.text}")
            elif response.status_code >= 400:
                raise requests.RequestException(f"Client error {response.status_code}: {response.text}")
                
            return response.json()
            
        except requests.exceptions.Timeout:
            raise requests.RequestException(f"Request timeout for {self.source_name}")
        except requests.exceptions.ConnectionError:
            raise requests.RequestException(f"Connection error for {self.source_name}")
        except Exception as e:
            raise requests.RequestException(f"Request failed for {self.source_name}: {e}")
            
    def _parse_market_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析市场数据响应"""
        if not self._validate_response(response, ["data"]):
            raise ValueError("Invalid market data response format")
            
        parsed_data = {
            "items": response.get("data", []),
            "total_count": response.get("total", 0),
            "league": response.get("league", "Unknown"),
            "last_updated": response.get("timestamp", self._get_current_timestamp())
        }
        
        return self._standardize_response(parsed_data, "get_market_data", {
            "item_count": len(parsed_data["items"]),
            "data_source": "poe2scout.com"
        })
        
    def _parse_build_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析构筑数据响应"""
        if not self._validate_response(response, ["builds"]):
            raise ValueError("Invalid build data response format")
            
        parsed_data = {
            "builds": response.get("builds", []),
            "trends": response.get("trends", {}),
            "meta_analysis": response.get("meta", {}),
            "total_builds": response.get("total", 0)
        }
        
        return self._standardize_response(parsed_data, "get_build_data", {
            "build_count": len(parsed_data["builds"]),
            "data_source": "poe2scout.com"
        })
        
    def _parse_item_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析物品数据响应"""
        if not self._validate_response(response):
            raise ValueError("Invalid item data response format")
            
        if "items" in response:
            # 物品列表响应
            parsed_data = {
                "items": response["items"],
                "total_count": response.get("total", len(response["items"]))
            }
        else:
            # 单个物品响应
            parsed_data = {
                "item": response,
                "price_history": response.get("price_history", []),
                "market_stats": response.get("stats", {})
            }
            
        return self._standardize_response(parsed_data, "get_item_data", {
            "data_source": "poe2scout.com"
        })
        
    def _parse_currency_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析货币汇率响应"""
        if not self._validate_response(response, ["rates"]):
            raise ValueError("Invalid currency data response format")
            
        parsed_data = {
            "rates": response["rates"],
            "base_currency": response.get("base", "chaos"),
            "league": response.get("league", "Standard"),
            "last_updated": response.get("timestamp", self._get_current_timestamp())
        }
        
        return self._standardize_response(parsed_data, "get_currency_rates", {
            "rate_count": len(parsed_data["rates"]),
            "data_source": "poe2scout.com"
        })
        
    def _parse_search_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析搜索结果响应"""
        if not self._validate_response(response, ["results"]):
            raise ValueError("Invalid search response format")
            
        parsed_data = {
            "results": response["results"],
            "total_count": response.get("total", len(response["results"])),
            "query": response.get("query", ""),
            "suggestions": response.get("suggestions", [])
        }
        
        return self._standardize_response(parsed_data, "search_items", {
            "result_count": len(parsed_data["results"]),
            "data_source": "poe2scout.com"
        })
        
    def get_build_recommendations(self, 
                                user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据用户偏好获取构筑推荐
        
        Args:
            user_preferences: 用户偏好设置
            
        Returns:
            构筑推荐数据
        """
        cache_key = self._generate_cache_key("build_recommendations", **user_preferences)
        
        def _fetch_recommendations():
            # 基于用户偏好构建查询参数
            params = {}
            
            if user_preferences.get("class"):
                params["class"] = user_preferences["class"]
            if user_preferences.get("budget"):
                params["max_cost"] = user_preferences["budget"]
            if user_preferences.get("playstyle"):
                params["style"] = user_preferences["playstyle"]
                
            endpoint = f"{self.BASE_URL}/builds/recommended"
            response = self._make_request(endpoint, params)
            
            # 增强推荐数据
            recommendations = response.get("builds", [])
            for build in recommendations:
                # 添加匹配度分数
                build["match_score"] = self._calculate_match_score(build, user_preferences)
                
            return self._standardize_response({
                "recommendations": sorted(recommendations, key=lambda x: x.get("match_score", 0), reverse=True),
                "user_preferences": user_preferences,
                "total_matches": len(recommendations)
            }, "get_build_recommendations", {
                "recommendation_count": len(recommendations),
                "data_source": "poe2scout.com"
            })
            
        return self._make_resilient_call("get_build_recommendations", _fetch_recommendations, cache_key)
        
    def _calculate_match_score(self, build: Dict[str, Any], preferences: Dict[str, Any]) -> float:
        """计算构筑与用户偏好的匹配分数"""
        score = 0.0
        
        # 职业匹配
        if preferences.get("class") and build.get("class") == preferences["class"]:
            score += 30.0
            
        # 预算匹配
        if preferences.get("budget"):
            build_cost = build.get("estimated_cost", 0)
            user_budget = preferences["budget"]
            if build_cost <= user_budget:
                score += 20.0 * (1 - (build_cost / user_budget if user_budget > 0 else 0))
                
        # 游戏风格匹配
        if preferences.get("playstyle") and build.get("playstyle") == preferences["playstyle"]:
            score += 25.0
            
        # 难度匹配
        if preferences.get("difficulty"):
            if build.get("difficulty") == preferences["difficulty"]:
                score += 15.0
                
        # 受欢迎程度加权
        popularity = build.get("popularity_score", 0)
        score += popularity * 0.1
        
        return min(score, 100.0)  # 限制最大分数为100