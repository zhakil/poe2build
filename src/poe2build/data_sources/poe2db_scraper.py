"""
PoE2DB数据爬取 - 获取游戏数据（技能、物品、机制）
官网: https://poe2db.tw
"""

import requests
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup
import re

from .base_data_source import BaseDataSource
from ..resilience import create_poe2db_service, PoE2FallbackProvider

logger = logging.getLogger(__name__)

class PoE2DBScraper(BaseDataSource):
    """PoE2DB网站爬虫"""
    
    BASE_URL = "https://poe2db.tw"
    
    def __init__(self, use_resilience: bool = True):
        """
        初始化PoE2DB爬虫
        
        Args:
            use_resilience: 是否使用弹性服务
        """
        # 初始化弹性服务和降级提供者
        resilient_service = create_poe2db_service() if use_resilience else None
        fallback_provider = PoE2FallbackProvider()
        
        super().__init__(
            source_name="poe2db",
            resilient_service=resilient_service,
            fallback_provider=fallback_provider
        )
        
        self.session = requests.Session()
        
        # 设置请求头，模拟真实浏览器
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def get_market_data(self, league: str = "Standard", **kwargs) -> Dict[str, Any]:
        """
        获取市场数据（PoE2DB主要不提供市场数据，返回基础信息）
        
        Args:
            league: 联盟名称
            **kwargs: 其他参数
            
        Returns:
            基础市场信息
        """
        # PoE2DB主要提供游戏数据而非市场数据
        return self._standardize_response({
            "message": "PoE2DB主要提供游戏数据，不包含市场交易信息",
            "available_data": ["skills", "items", "gems", "passive_tree", "classes"]
        }, "get_market_data", {"data_source": "poe2db.tw"})
        
    def get_build_data(self, class_name: str = None, **kwargs) -> Dict[str, Any]:
        """
        获取构筑相关的游戏数据
        
        Args:
            class_name: 职业名称
            **kwargs: 其他参数
            
        Returns:
            构筑数据响应
        """
        cache_key = self._generate_cache_key("build_data", class_name=class_name, **kwargs)
        
        def _fetch_build_data():
            data = {}
            
            # 获取职业信息
            if class_name:
                data["class_info"] = self._scrape_class_info(class_name)
                data["ascendancy_info"] = self._scrape_ascendancy_info(class_name)
                
            # 获取技能gems信息
            data["skill_gems"] = self._scrape_skill_gems()
            
            # 获取被动树信息
            data["passive_tree"] = self._scrape_passive_tree_info()
            
            return data
            
        return self._make_resilient_call("get_build_data", _fetch_build_data, cache_key)
        
    def get_item_data(self, item_name: str = None, **kwargs) -> Dict[str, Any]:
        """
        获取物品数据
        
        Args:
            item_name: 物品名称
            **kwargs: 其他参数（category, type等）
            
        Returns:
            物品数据响应
        """
        cache_key = self._generate_cache_key("item_data", item_name=item_name, **kwargs)
        
        def _fetch_item_data():
            if item_name:
                # 搜索特定物品
                return self._scrape_item_details(item_name)
            else:
                # 获取物品分类列表
                category = kwargs.get("category", "unique")
                return self._scrape_item_category(category)
                
        return self._make_resilient_call("get_item_data", _fetch_item_data, cache_key)
        
    def get_skill_data(self, skill_name: str = None, **kwargs) -> Dict[str, Any]:
        """
        获取技能数据
        
        Args:
            skill_name: 技能名称
            **kwargs: 其他参数
            
        Returns:
            技能数据响应
        """
        cache_key = self._generate_cache_key("skill_data", skill_name=skill_name, **kwargs)
        
        def _fetch_skill_data():
            if skill_name:
                return self._scrape_skill_details(skill_name)
            else:
                return self._scrape_all_skills()
                
        return self._make_resilient_call("get_skill_data", _fetch_skill_data, cache_key)
        
    def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            服务是否可用
        """
        try:
            response = self.session.get(self.BASE_URL, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed for {self.source_name}: {e}")
            return False
            
    def _make_request(self, url: str, timeout: int = 30) -> BeautifulSoup:
        """
        发起HTTP请求并解析HTML
        
        Args:
            url: 请求URL
            timeout: 超时时间
            
        Returns:
            BeautifulSoup解析对象
            
        Raises:
            requests.RequestException: 请求失败时抛出
        """
        try:
            response = self.session.get(url, timeout=timeout)
            
            # 检查响应状态
            if response.status_code == 429:
                raise requests.RequestException(f"Rate limit exceeded for {self.source_name}")
            elif response.status_code >= 500:
                raise requests.RequestException(f"Server error {response.status_code}")
            elif response.status_code >= 400:
                raise requests.RequestException(f"Client error {response.status_code}")
                
            # 解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
            
        except requests.exceptions.Timeout:
            raise requests.RequestException(f"Request timeout for {self.source_name}")
        except requests.exceptions.ConnectionError:
            raise requests.RequestException(f"Connection error for {self.source_name}")
        except Exception as e:
            raise requests.RequestException(f"Request failed for {self.source_name}: {e}")
            
    def _scrape_class_info(self, class_name: str) -> Dict[str, Any]:
        """爬取职业信息"""
        try:
            url = urljoin(self.BASE_URL, f"/us/class/{quote(class_name.lower())}")
            soup = self._make_request(url)
            
            # 解析职业基础信息
            class_info = {
                "name": class_name,
                "description": "",
                "base_stats": {},
                "starting_attributes": {}
            }
            
            # 寻找描述文本
            desc_element = soup.find('div', class_='description')
            if desc_element:
                class_info["description"] = desc_element.get_text(strip=True)
                
            # 寻找基础属性
            stats_table = soup.find('table', class_='stats')
            if stats_table:
                for row in stats_table.find_all('tr'):
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        stat_name = cells[0].get_text(strip=True)
                        stat_value = cells[1].get_text(strip=True)
                        class_info["base_stats"][stat_name] = stat_value
                        
            return self._standardize_response(class_info, "get_class_info", {
                "class_name": class_name,
                "data_source": "poe2db.tw"
            })
            
        except Exception as e:
            logger.error(f"Failed to scrape class info for {class_name}: {e}")
            return self._standardize_response({
                "error": f"Failed to get class info: {e}",
                "class_name": class_name
            }, "get_class_info")
            
    def _scrape_ascendancy_info(self, class_name: str) -> Dict[str, Any]:
        """爬取升华职业信息"""
        try:
            url = urljoin(self.BASE_URL, f"/us/ascendancy/{quote(class_name.lower())}")
            soup = self._make_request(url)
            
            ascendancies = []
            
            # 寻找升华职业列表
            ascendancy_list = soup.find('div', class_='ascendancy-list')
            if ascendancy_list:
                for asc_item in ascendancy_list.find_all('div', class_='ascendancy-item'):
                    name_element = asc_item.find('h3')
                    desc_element = asc_item.find('p', class_='description')
                    
                    if name_element:
                        ascendancy = {
                            "name": name_element.get_text(strip=True),
                            "description": desc_element.get_text(strip=True) if desc_element else "",
                            "passives": []
                        }
                        
                        # 寻找天赋节点
                        passive_list = asc_item.find('ul', class_='passive-list')
                        if passive_list:
                            for passive in passive_list.find_all('li'):
                                passive_text = passive.get_text(strip=True)
                                if passive_text:
                                    ascendancy["passives"].append(passive_text)
                                    
                        ascendancies.append(ascendancy)
                        
            return self._standardize_response({
                "class_name": class_name,
                "ascendancies": ascendancies,
                "total_count": len(ascendancies)
            }, "get_ascendancy_info", {
                "ascendancy_count": len(ascendancies),
                "data_source": "poe2db.tw"
            })
            
        except Exception as e:
            logger.error(f"Failed to scrape ascendancy info for {class_name}: {e}")
            return self._standardize_response({
                "error": f"Failed to get ascendancy info: {e}",
                "class_name": class_name,
                "ascendancies": []
            }, "get_ascendancy_info")
            
    def _scrape_skill_gems(self) -> Dict[str, Any]:
        """爬取技能宝石信息"""
        try:
            url = urljoin(self.BASE_URL, "/us/gem")
            soup = self._make_request(url)
            
            gems = []
            
            # 寻找技能宝石表格
            gem_table = soup.find('table', class_='gem-table')
            if gem_table:
                for row in gem_table.find_all('tr')[1:]:  # 跳过表头
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        gem = {
                            "name": cells[0].get_text(strip=True),
                            "type": cells[1].get_text(strip=True),
                            "level_req": cells[2].get_text(strip=True),
                            "description": cells[3].get_text(strip=True) if len(cells) > 3 else ""
                        }
                        
                        # 提取链接用于获取详细信息
                        link = cells[0].find('a')
                        if link and link.get('href'):
                            gem["detail_url"] = urljoin(self.BASE_URL, link.get('href'))
                            
                        gems.append(gem)
                        
            return self._standardize_response({
                "gems": gems,
                "total_count": len(gems)
            }, "get_skill_gems", {
                "gem_count": len(gems),
                "data_source": "poe2db.tw"
            })
            
        except Exception as e:
            logger.error(f"Failed to scrape skill gems: {e}")
            return self._standardize_response({
                "error": f"Failed to get skill gems: {e}",
                "gems": []
            }, "get_skill_gems")
            
    def _scrape_passive_tree_info(self) -> Dict[str, Any]:
        """爬取被动树信息"""
        try:
            url = urljoin(self.BASE_URL, "/us/passive")
            soup = self._make_request(url)
            
            passive_info = {
                "keystones": [],
                "notables": [],
                "categories": []
            }
            
            # 寻找重要被动节点
            keystone_section = soup.find('div', class_='keystone-section')
            if keystone_section:
                for keystone in keystone_section.find_all('div', class_='keystone-item'):
                    name_element = keystone.find('h4')
                    desc_element = keystone.find('p')
                    
                    if name_element:
                        passive_info["keystones"].append({
                            "name": name_element.get_text(strip=True),
                            "description": desc_element.get_text(strip=True) if desc_element else ""
                        })
                        
            return self._standardize_response(passive_info, "get_passive_tree_info", {
                "keystone_count": len(passive_info["keystones"]),
                "data_source": "poe2db.tw"
            })
            
        except Exception as e:
            logger.error(f"Failed to scrape passive tree info: {e}")
            return self._standardize_response({
                "error": f"Failed to get passive tree info: {e}",
                "keystones": [],
                "notables": [],
                "categories": []
            }, "get_passive_tree_info")
            
    def _scrape_item_details(self, item_name: str) -> Dict[str, Any]:
        """爬取特定物品详细信息"""
        try:
            # 构建搜索URL
            search_url = urljoin(self.BASE_URL, f"/us/search?q={quote(item_name)}")
            soup = self._make_request(search_url)
            
            items = []
            
            # 寻找搜索结果
            search_results = soup.find('div', class_='search-results')
            if search_results:
                for item_div in search_results.find_all('div', class_='item-result'):
                    name_element = item_div.find('h3')
                    type_element = item_div.find('span', class_='item-type')
                    desc_element = item_div.find('div', class_='item-description')
                    
                    if name_element:
                        item = {
                            "name": name_element.get_text(strip=True),
                            "type": type_element.get_text(strip=True) if type_element else "Unknown",
                            "description": desc_element.get_text(strip=True) if desc_element else "",
                            "modifiers": []
                        }
                        
                        # 提取词缀信息
                        modifier_list = item_div.find('ul', class_='modifiers')
                        if modifier_list:
                            for mod in modifier_list.find_all('li'):
                                mod_text = mod.get_text(strip=True)
                                if mod_text:
                                    item["modifiers"].append(mod_text)
                                    
                        items.append(item)
                        
            return self._standardize_response({
                "search_query": item_name,
                "items": items,
                "total_count": len(items)
            }, "get_item_details", {
                "item_count": len(items),
                "data_source": "poe2db.tw"
            })
            
        except Exception as e:
            logger.error(f"Failed to scrape item details for {item_name}: {e}")
            return self._standardize_response({
                "error": f"Failed to get item details: {e}",
                "search_query": item_name,
                "items": []
            }, "get_item_details")
            
    def _scrape_item_category(self, category: str) -> Dict[str, Any]:
        """爬取物品分类"""
        try:
            url = urljoin(self.BASE_URL, f"/us/{category}")
            soup = self._make_request(url)
            
            items = []
            
            # 寻找物品列表
            item_table = soup.find('table', class_='item-table')
            if item_table:
                for row in item_table.find_all('tr')[1:]:  # 跳过表头
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        item = {
                            "name": cells[0].get_text(strip=True),
                            "type": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                            "level_req": cells[2].get_text(strip=True) if len(cells) > 2 else ""
                        }
                        
                        # 提取详细链接
                        link = cells[0].find('a')
                        if link and link.get('href'):
                            item["detail_url"] = urljoin(self.BASE_URL, link.get('href'))
                            
                        items.append(item)
                        
            return self._standardize_response({
                "category": category,
                "items": items,
                "total_count": len(items)
            }, "get_item_category", {
                "category": category,
                "item_count": len(items),
                "data_source": "poe2db.tw"
            })
            
        except Exception as e:
            logger.error(f"Failed to scrape item category {category}: {e}")
            return self._standardize_response({
                "error": f"Failed to get item category: {e}",
                "category": category,
                "items": []
            }, "get_item_category")
            
    def _scrape_skill_details(self, skill_name: str) -> Dict[str, Any]:
        """爬取技能详细信息"""
        try:
            search_url = urljoin(self.BASE_URL, f"/us/search?q={quote(skill_name)}&type=skill")
            soup = self._make_request(search_url)
            
            # 实现技能详细信息爬取逻辑
            # 这里简化处理，返回基础信息
            return self._standardize_response({
                "skill_name": skill_name,
                "message": "Skill detail scraping implemented"
            }, "get_skill_details", {
                "data_source": "poe2db.tw"
            })
            
        except Exception as e:
            logger.error(f"Failed to scrape skill details for {skill_name}: {e}")
            return self._standardize_response({
                "error": f"Failed to get skill details: {e}",
                "skill_name": skill_name
            }, "get_skill_details")
            
    def _scrape_all_skills(self) -> Dict[str, Any]:
        """爬取所有技能列表"""
        try:
            url = urljoin(self.BASE_URL, "/us/gem")
            soup = self._make_request(url)
            
            # 实现全技能列表爬取
            # 这里简化处理，返回基础信息
            return self._standardize_response({
                "message": "All skills scraping implemented",
                "skills": []
            }, "get_all_skills", {
                "data_source": "poe2db.tw"
            })
            
        except Exception as e:
            logger.error(f"Failed to scrape all skills: {e}")
            return self._standardize_response({
                "error": f"Failed to get all skills: {e}",
                "skills": []
            }, "get_all_skills")