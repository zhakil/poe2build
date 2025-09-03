"""
PoE Ninja构筑数据爬虫 - Meta分析和趋势
https://poe.ninja/poe2/builds

提供流行构筑、技能使用统计、升华趋势等数据
"""

import requests
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from bs4 import BeautifulSoup
import re


@dataclass
class PopularBuild:
    """流行构筑数据"""
    name: str
    character_class: str
    ascendancy: Optional[str]
    main_skill: str
    support_gems: List[str]
    popularity_score: float
    avg_level: int
    sample_size: int
    dps_estimate: Optional[float]
    ehp_estimate: Optional[float]
    key_items: List[str]
    passive_keystone: List[str]
    last_updated: datetime


@dataclass
class SkillUsageStats:
    """技能使用统计"""
    skill_name: str
    usage_percentage: float
    average_level: int
    popular_supports: List[str]
    character_classes: Dict[str, float]  # 职业使用比例
    trend: str  # "rising", "stable", "falling"


@dataclass
class AscendancyTrend:
    """升华趋势数据"""
    ascendancy: str
    character_class: str
    popularity_percentage: float
    average_level: int
    popular_skills: List[str]
    trend: str


class NinjaMetaScraper:
    """PoE Ninja Meta数据爬虫"""
    
    BASE_URL = "https://poe.ninja/poe2"
    
    def __init__(self, cache_duration: int = 1800):  # 30分钟缓存
        """
        初始化爬虫
        
        Args:
            cache_duration: 缓存持续时间（秒）
        """
        self.cache_duration = cache_duration
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        # 缓存
        self._builds_cache: Optional[tuple] = None  # (data, timestamp)
        self._skills_cache: Optional[tuple] = None
        self._ascendancy_cache: Optional[tuple] = None
        
        # 速率限制
        self.last_request_time = 0
        self.min_request_interval = 2.0  # 2秒间隔，更尊重服务器
    
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
    
    def _make_request(self, url: str) -> Optional[BeautifulSoup]:
        """发起网页请求"""
        self._rate_limit()
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"PoE Ninja请求失败: {e}")
            return None
    
    def get_popular_builds(self, league: str = "Standard", limit: int = 100) -> List[PopularBuild]:
        """
        获取流行构筑
        
        Args:
            league: 联盟名称
            limit: 限制数量
            
        Returns:
            流行构筑列表
        """
        # 检查缓存
        if self._builds_cache:
            data, timestamp = self._builds_cache
            if self._is_cache_valid(timestamp):
                return data[:limit]
        
        url = f"{self.BASE_URL}/builds"
        if league != "Standard":
            url += f"?league={league}"
        
        soup = self._make_request(url)
        if not soup:
            return []
        
        builds = []
        
        try:
            # 查找构筑表格或卡片
            build_elements = soup.find_all(['tr', 'div'], class_=lambda x: x and 'build' in x.lower())
            
            for element in build_elements[:limit]:
                build_data = self._parse_build_element(element)
                if build_data:
                    builds.append(build_data)
        
        except Exception as e:
            print(f"解析构筑数据失败: {e}")
        
        # 缓存结果
        self._builds_cache = (builds, datetime.now())
        
        return builds
    
    def _parse_build_element(self, element) -> Optional[PopularBuild]:
        """解析构筑元素"""
        try:
            # 这里需要根据实际的HTML结构来解析
            # 由于poe.ninja的结构可能变化，这里提供一个通用框架
            
            name = self._extract_text(element, ['name', 'title', 'build-name'])
            character_class = self._extract_text(element, ['class', 'character-class'])
            ascendancy = self._extract_text(element, ['ascendancy', 'subclass'])
            main_skill = self._extract_text(element, ['skill', 'main-skill', 'primary-skill'])
            
            # 支持宝石（通常在技能链接中）
            support_gems = self._extract_support_gems(element)
            
            # 流行度分数（可能来自排名或百分比）
            popularity_score = self._extract_number(element, ['popularity', 'score', 'rank'])
            
            # 等级
            avg_level = self._extract_number(element, ['level', 'avg-level'])
            
            # 样本大小
            sample_size = self._extract_number(element, ['sample', 'count', 'players'])
            
            # 关键物品
            key_items = self._extract_key_items(element)
            
            # 关键天赋
            passive_keystone = self._extract_keystones(element)
            
            return PopularBuild(
                name=name or "未知构筑",
                character_class=character_class or "Unknown",
                ascendancy=ascendancy,
                main_skill=main_skill or "Unknown",
                support_gems=support_gems,
                popularity_score=popularity_score or 0.0,
                avg_level=int(avg_level) if avg_level else 85,
                sample_size=int(sample_size) if sample_size else 1,
                dps_estimate=None,  # 需要进一步解析或估算
                ehp_estimate=None,
                key_items=key_items,
                passive_keystone=passive_keystone,
                last_updated=datetime.now()
            )
        
        except Exception as e:
            print(f"解析构筑元素失败: {e}")
            return None
    
    def _extract_text(self, element, possible_classes: List[str]) -> Optional[str]:
        """提取文本内容"""
        for class_name in possible_classes:
            found = element.find(['span', 'div', 'td', 'a'], class_=lambda x: x and class_name in x.lower())
            if found:
                return found.get_text(strip=True)
        return None
    
    def _extract_number(self, element, possible_classes: List[str]) -> Optional[float]:
        """提取数字"""
        text = self._extract_text(element, possible_classes)
        if text:
            # 提取数字
            numbers = re.findall(r'[\d.]+', text)
            if numbers:
                return float(numbers[0])
        return None
    
    def _extract_support_gems(self, element) -> List[str]:
        """提取辅助宝石"""
        support_gems = []
        
        # 查找技能链接区域
        skill_links = element.find_all(['div', 'span'], class_=lambda x: x and ('gem' in x.lower() or 'skill' in x.lower()))
        
        for link in skill_links:
            gem_names = link.find_all(['span', 'a'])
            for gem in gem_names:
                gem_text = gem.get_text(strip=True)
                if gem_text and gem_text not in ['', 'Support']:
                    support_gems.append(gem_text)
        
        return list(set(support_gems))  # 去重
    
    def _extract_key_items(self, element) -> List[str]:
        """提取关键物品"""
        items = []
        
        # 查找装备区域
        item_elements = element.find_all(['div', 'span'], class_=lambda x: x and 'item' in x.lower())
        
        for item_elem in item_elements:
            item_name = item_elem.get_text(strip=True)
            if item_name and len(item_name) > 3:  # 过滤太短的文本
                items.append(item_name)
        
        return items[:10]  # 限制数量
    
    def _extract_keystones(self, element) -> List[str]:
        """提取关键天赋"""
        keystones = []
        
        # 查找天赋区域
        passive_elements = element.find_all(['div', 'span'], class_=lambda x: x and ('keystone' in x.lower() or 'passive' in x.lower()))
        
        for passive_elem in passive_elements:
            keystone_name = passive_elem.get_text(strip=True)
            if keystone_name:
                keystones.append(keystone_name)
        
        return keystones
    
    def get_skill_usage_stats(self, league: str = "Standard") -> List[SkillUsageStats]:
        """
        获取技能使用统计
        
        Args:
            league: 联盟名称
            
        Returns:
            技能使用统计列表
        """
        # 检查缓存
        if self._skills_cache:
            data, timestamp = self._skills_cache
            if self._is_cache_valid(timestamp):
                return data
        
        # 从构筑数据中统计技能使用情况
        builds = self.get_popular_builds(league)
        
        skill_stats = {}
        total_builds = len(builds)
        
        for build in builds:
            skill = build.main_skill
            if skill not in skill_stats:
                skill_stats[skill] = {
                    'count': 0,
                    'total_level': 0,
                    'supports': set(),
                    'classes': {}
                }
            
            stats = skill_stats[skill]
            stats['count'] += 1
            stats['total_level'] += build.avg_level
            stats['supports'].update(build.support_gems)
            
            if build.character_class not in stats['classes']:
                stats['classes'][build.character_class] = 0
            stats['classes'][build.character_class] += 1
        
        # 转换为SkillUsageStats对象
        usage_stats = []
        for skill_name, stats in skill_stats.items():
            if stats['count'] > 0:
                usage_percentage = (stats['count'] / total_builds) * 100
                avg_level = stats['total_level'] / stats['count']
                popular_supports = list(stats['supports'])[:5]  # 前5个支持宝石
                
                # 计算职业使用比例
                class_percentages = {}
                for class_name, count in stats['classes'].items():
                    class_percentages[class_name] = (count / stats['count']) * 100
                
                usage_stat = SkillUsageStats(
                    skill_name=skill_name,
                    usage_percentage=usage_percentage,
                    average_level=int(avg_level),
                    popular_supports=popular_supports,
                    character_classes=class_percentages,
                    trend="stable"  # 需要历史数据来确定趋势
                )
                usage_stats.append(usage_stat)
        
        # 按使用率排序
        usage_stats.sort(key=lambda x: x.usage_percentage, reverse=True)
        
        # 缓存结果
        self._skills_cache = (usage_stats, datetime.now())
        
        return usage_stats
    
    def get_ascendancy_trends(self, league: str = "Standard") -> List[AscendancyTrend]:
        """
        获取升华趋势
        
        Args:
            league: 联盟名称
            
        Returns:
            升华趋势列表
        """
        # 检查缓存
        if self._ascendancy_cache:
            data, timestamp = self._ascendancy_cache
            if self._is_cache_valid(timestamp):
                return data
        
        builds = self.get_popular_builds(league)
        
        ascendancy_stats = {}
        total_builds = len(builds)
        
        for build in builds:
            if not build.ascendancy:
                continue
                
            key = (build.ascendancy, build.character_class)
            if key not in ascendancy_stats:
                ascendancy_stats[key] = {
                    'count': 0,
                    'total_level': 0,
                    'skills': set()
                }
            
            stats = ascendancy_stats[key]
            stats['count'] += 1
            stats['total_level'] += build.avg_level
            stats['skills'].add(build.main_skill)
        
        # 转换为AscendancyTrend对象
        trends = []
        for (ascendancy, character_class), stats in ascendancy_stats.items():
            if stats['count'] > 0:
                popularity = (stats['count'] / total_builds) * 100
                avg_level = stats['total_level'] / stats['count']
                popular_skills = list(stats['skills'])
                
                trend = AscendancyTrend(
                    ascendancy=ascendancy,
                    character_class=character_class,
                    popularity_percentage=popularity,
                    average_level=int(avg_level),
                    popular_skills=popular_skills,
                    trend="stable"
                )
                trends.append(trend)
        
        # 按流行度排序
        trends.sort(key=lambda x: x.popularity_percentage, reverse=True)
        
        # 缓存结果
        self._ascendancy_cache = (trends, datetime.now())
        
        return trends
    
    def get_meta_summary(self, league: str = "Standard") -> Dict[str, Any]:
        """
        获取Meta总结
        
        Args:
            league: 联盟名称
            
        Returns:
            Meta总结信息
        """
        builds = self.get_popular_builds(league, limit=50)
        skills = self.get_skill_usage_stats(league)
        ascendancies = self.get_ascendancy_trends(league)
        
        return {
            'total_builds_analyzed': len(builds),
            'top_skills': [skill.skill_name for skill in skills[:10]],
            'top_ascendancies': [asc.ascendancy for asc in ascendancies[:5]],
            'average_level': sum(build.avg_level for build in builds) / len(builds) if builds else 0,
            'meta_diversity': len(set(build.main_skill for build in builds)),
            'last_updated': datetime.now(),
            'data_freshness': 'Recent' if builds else 'Stale'
        }


# 全局实例
_scraper = None

def get_ninja_scraper() -> NinjaMetaScraper:
    """获取全局Ninja爬虫实例"""
    global _scraper
    if _scraper is None:
        _scraper = NinjaMetaScraper()
    return _scraper