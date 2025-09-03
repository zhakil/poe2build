"""
PoE2DB API客户端 - 完整游戏数据库
https://poe2db.tw/cn/

提供装备属性、技能详情、升华信息等完整游戏数据
支持中文本地化数据优先
"""

import requests
import time
import json
import re
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, quote


@dataclass
class ItemDetail:
    """物品详细信息"""
    name: str
    name_cn: str
    item_class: str
    base_type: str
    level_requirement: int
    attribute_requirements: Dict[str, int]  # str, dex, int
    implicit_mods: List[str]
    explicit_mods: List[str]
    flavour_text: Optional[str]
    rarity: str  # normal, magic, rare, unique
    tags: List[str]
    weapon_stats: Optional[Dict[str, Any]]  # 武器专用
    armour_stats: Optional[Dict[str, Any]]  # 防具专用
    gem_stats: Optional[Dict[str, Any]]     # 宝石专用
    image_url: Optional[str]
    wiki_url: str


@dataclass 
class SkillDetail:
    """技能详细信息"""
    name: str
    name_cn: str
    skill_type: str  # active, support, aura
    gem_color: str   # red, green, blue, white
    level_requirement: int
    attribute_requirements: Dict[str, int]
    mana_cost: Optional[Union[int, str]]  # 可能是百分比
    cast_time: Optional[float]
    cooldown: Optional[float]
    damage_effectiveness: Optional[float]
    description: str
    stat_descriptions: List[str]
    quality_stats: List[str]
    level_progression: List[Dict[str, Any]]  # 等级提升数据
    tags: List[str]
    related_items: List[str]  # 相关装备
    wiki_url: str


@dataclass
class AscendancyInfo:
    """升华职业信息"""
    name: str
    name_cn: str
    base_class: str
    base_class_cn: str
    description: str
    passive_skills: List[Dict[str, Any]]  # 升华技能
    starting_point: Dict[str, int]  # 起始位置
    image_url: Optional[str]
    wiki_url: str


@dataclass
class PassiveSkillNode:
    """天赋技能节点"""
    node_id: int
    name: str
    name_cn: str
    description: List[str]
    is_keystone: bool
    is_notable: bool
    position: Dict[str, float]
    connected_nodes: List[int]
    ascendancy_class: Optional[str]


class PoE2DBClient:
    """PoE2DB API客户端"""
    
    BASE_URL = "https://poe2db.tw"
    CN_BASE_URL = "https://poe2db.tw/cn"
    
    def __init__(self, prefer_chinese: bool = True, cache_duration: int = 3600):
        """
        初始化客户端
        
        Args:
            prefer_chinese: 优先使用中文数据
            cache_duration: 缓存持续时间（秒）
        """
        self.prefer_chinese = prefer_chinese
        self.base_url = self.CN_BASE_URL if prefer_chinese else self.BASE_URL
        self.cache_duration = cache_duration
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        # 缓存
        self._item_cache: Dict[str, tuple] = {}     # (data, timestamp)
        self._skill_cache: Dict[str, tuple] = {}
        self._ascendancy_cache: Dict[str, tuple] = {}
        self._search_cache: Dict[str, tuple] = {}
        
        # 速率限制
        self.last_request_time = 0
        self.min_request_interval = 2.0  # 2秒间隔，尊重服务器
    
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
            print(f"PoE2DB请求失败: {e}")
            return None
    
    def search_items(self, query: str, item_type: str = "all") -> List[Dict[str, str]]:
        """
        搜索物品
        
        Args:
            query: 搜索关键词
            item_type: 物品类型过滤 (all, weapon, armour, jewellery, gem, etc.)
            
        Returns:
            搜索结果列表 [{name, url, type, description}]
        """
        cache_key = f"search_{query}_{item_type}"
        
        # 检查缓存
        if cache_key in self._search_cache:
            data, timestamp = self._search_cache[cache_key]
            if self._is_cache_valid(timestamp):
                return data
        
        # 构建搜索URL
        search_url = f"{self.base_url}/search"
        params = {
            'q': query,
            'type': item_type if item_type != "all" else ""
        }
        
        # 构建完整URL
        if params['type']:
            search_url += f"?q={quote(query)}&type={params['type']}"
        else:
            search_url += f"?q={quote(query)}"
        
        soup = self._make_request(search_url)
        if not soup:
            return []
        
        results = []
        
        # 解析搜索结果
        search_results = soup.find_all(['div', 'tr'], class_=lambda x: x and 'search-result' in x.lower())
        
        for result in search_results:
            try:
                # 提取物品名称和链接
                link_elem = result.find('a')
                if not link_elem:
                    continue
                    
                name = link_elem.get_text(strip=True)
                relative_url = link_elem.get('href', '')
                full_url = urljoin(self.base_url, relative_url)
                
                # 提取物品类型
                type_elem = result.find(['span', 'div'], class_=lambda x: x and 'type' in x.lower())
                item_type_found = type_elem.get_text(strip=True) if type_elem else 'Unknown'
                
                # 提取描述
                desc_elem = result.find(['div', 'span'], class_=lambda x: x and 'description' in x.lower())
                description = desc_elem.get_text(strip=True) if desc_elem else ''
                
                results.append({
                    'name': name,
                    'url': full_url,
                    'type': item_type_found,
                    'description': description
                })
                
            except Exception as e:
                print(f"解析搜索结果失败: {e}")
                continue
        
        # 缓存结果
        self._search_cache[cache_key] = (results, datetime.now())
        
        return results
    
    def get_item_detail(self, item_name: str) -> Optional[ItemDetail]:
        """
        获取物品详细信息
        
        Args:
            item_name: 物品名称
            
        Returns:
            物品详细信息
        """
        cache_key = f"item_{item_name}"
        
        # 检查缓存
        if cache_key in self._item_cache:
            data, timestamp = self._item_cache[cache_key]
            if self._is_cache_valid(timestamp):
                return data
        
        # 搜索物品页面
        search_results = self.search_items(item_name)
        if not search_results:
            return None
        
        # 使用第一个结果
        item_url = search_results[0]['url']
        soup = self._make_request(item_url)
        if not soup:
            return None
        
        try:
            # 解析物品详细信息
            item_detail = self._parse_item_detail(soup, item_url)
            
            # 缓存结果
            self._item_cache[cache_key] = (item_detail, datetime.now())
            
            return item_detail
            
        except Exception as e:
            print(f"解析物品详情失败: {e}")
            return None
    
    def _parse_item_detail(self, soup: BeautifulSoup, url: str) -> ItemDetail:
        """解析物品详情页面"""
        
        # 提取基本信息
        name = self._extract_text(soup, ['h1', 'title', '.item-name'])
        name_cn = self._extract_text(soup, ['.item-name-cn', '.chinese-name']) or name
        
        # 物品类别和基底
        item_class = self._extract_text(soup, ['.item-class', '.base-type'])
        base_type = self._extract_text(soup, ['.base-type', '.item-base'])
        
        # 需求
        level_req = self._extract_number(soup, ['.level-requirement', '.req-level']) or 1
        
        # 属性需求
        attr_reqs = {}
        str_req = self._extract_number(soup, ['.str-requirement', '.req-str'])
        if str_req:
            attr_reqs['str'] = str_req
        dex_req = self._extract_number(soup, ['.dex-requirement', '.req-dex'])
        if dex_req:
            attr_reqs['dex'] = dex_req
        int_req = self._extract_number(soup, ['.int-requirement', '.req-int'])
        if int_req:
            attr_reqs['int'] = int_req
        
        # 词缀
        implicit_mods = self._extract_mods(soup, 'implicit')
        explicit_mods = self._extract_mods(soup, 'explicit')
        
        # 描述文本
        flavour_text = self._extract_text(soup, ['.flavour-text', '.description'])
        
        # 稀有度
        rarity = self._extract_text(soup, ['.rarity', '.item-rarity']) or 'normal'
        
        # 标签
        tags = self._extract_tags(soup)
        
        # 专用属性
        weapon_stats = self._extract_weapon_stats(soup) if 'weapon' in item_class.lower() else None
        armour_stats = self._extract_armour_stats(soup) if any(x in item_class.lower() for x in ['armour', 'helmet', 'glove', 'boot']) else None
        gem_stats = self._extract_gem_stats(soup) if 'gem' in item_class.lower() else None
        
        # 图片
        image_url = self._extract_image_url(soup)
        
        return ItemDetail(
            name=name,
            name_cn=name_cn,
            item_class=item_class or 'Unknown',
            base_type=base_type or name,
            level_requirement=level_req,
            attribute_requirements=attr_reqs,
            implicit_mods=implicit_mods,
            explicit_mods=explicit_mods,
            flavour_text=flavour_text,
            rarity=rarity,
            tags=tags,
            weapon_stats=weapon_stats,
            armour_stats=armour_stats,
            gem_stats=gem_stats,
            image_url=image_url,
            wiki_url=url
        )
    
    def _extract_text(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """提取文本内容"""
        for selector in selectors:
            if selector.startswith('.'):
                # CSS类选择器
                elem = soup.find(class_=selector[1:])
            else:
                # 标签选择器
                elem = soup.find(selector)
            
            if elem:
                return elem.get_text(strip=True)
        return None
    
    def _extract_number(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[int]:
        """提取数字"""
        text = self._extract_text(soup, selectors)
        if text:
            # 提取数字
            numbers = re.findall(r'\d+', text)
            if numbers:
                return int(numbers[0])
        return None
    
    def _extract_mods(self, soup: BeautifulSoup, mod_type: str) -> List[str]:
        """提取词缀"""
        mods = []
        
        # 查找词缀区域
        mod_selectors = [
            f'.{mod_type}-mods',
            f'.{mod_type}-mod',
            f'[class*="{mod_type}"]'
        ]
        
        for selector in mod_selectors:
            mod_elements = soup.select(selector)
            for elem in mod_elements:
                mod_text = elem.get_text(strip=True)
                if mod_text and mod_text not in mods:
                    mods.append(mod_text)
        
        return mods
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """提取标签"""
        tags = []
        
        tag_elements = soup.find_all(['span', 'div'], class_=lambda x: x and 'tag' in x.lower())
        for elem in tag_elements:
            tag_text = elem.get_text(strip=True)
            if tag_text:
                tags.append(tag_text)
        
        return tags
    
    def _extract_weapon_stats(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """提取武器属性"""
        stats = {}
        
        # 伤害
        damage_elem = soup.find(text=re.compile(r'damage', re.I))
        if damage_elem:
            damage_text = damage_elem.parent.get_text(strip=True) if damage_elem.parent else ''
            damage_match = re.search(r'(\d+)-(\d+)', damage_text)
            if damage_match:
                stats['damage_min'] = int(damage_match.group(1))
                stats['damage_max'] = int(damage_match.group(2))
        
        # 攻击速度
        aps_elem = soup.find(text=re.compile(r'attack.*speed', re.I))
        if aps_elem:
            aps_text = aps_elem.parent.get_text(strip=True) if aps_elem.parent else ''
            aps_match = re.search(r'([\d.]+)', aps_text)
            if aps_match:
                stats['attacks_per_second'] = float(aps_match.group(1))
        
        # 暴击率
        crit_elem = soup.find(text=re.compile(r'critical.*chance', re.I))
        if crit_elem:
            crit_text = crit_elem.parent.get_text(strip=True) if crit_elem.parent else ''
            crit_match = re.search(r'([\d.]+)%', crit_text)
            if crit_match:
                stats['critical_strike_chance'] = float(crit_match.group(1))
        
        return stats if stats else None
    
    def _extract_armour_stats(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """提取防具属性"""
        stats = {}
        
        # 护甲值
        armour_elem = soup.find(text=re.compile(r'armour', re.I))
        if armour_elem:
            armour_text = armour_elem.parent.get_text(strip=True) if armour_elem.parent else ''
            armour_match = re.search(r'(\d+)', armour_text)
            if armour_match:
                stats['armour'] = int(armour_match.group(1))
        
        # 护盾值
        shield_elem = soup.find(text=re.compile(r'energy.*shield', re.I))
        if shield_elem:
            shield_text = shield_elem.parent.get_text(strip=True) if shield_elem.parent else ''
            shield_match = re.search(r'(\d+)', shield_text)
            if shield_match:
                stats['energy_shield'] = int(shield_match.group(1))
        
        return stats if stats else None
    
    def _extract_gem_stats(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """提取宝石属性"""
        stats = {}
        
        # 魔力消耗
        mana_elem = soup.find(text=re.compile(r'mana.*cost', re.I))
        if mana_elem:
            mana_text = mana_elem.parent.get_text(strip=True) if mana_elem.parent else ''
            mana_match = re.search(r'(\d+)', mana_text)
            if mana_match:
                stats['mana_cost'] = int(mana_match.group(1))
        
        # 施法时间
        cast_elem = soup.find(text=re.compile(r'cast.*time', re.I))
        if cast_elem:
            cast_text = cast_elem.parent.get_text(strip=True) if cast_elem.parent else ''
            cast_match = re.search(r'([\d.]+)', cast_text)
            if cast_match:
                stats['cast_time'] = float(cast_match.group(1))
        
        return stats if stats else None
    
    def _extract_image_url(self, soup: BeautifulSoup) -> Optional[str]:
        """提取物品图片URL"""
        img_elem = soup.find('img', class_=lambda x: x and 'item' in x.lower())
        if img_elem:
            src = img_elem.get('src')
            if src:
                return urljoin(self.base_url, src)
        return None
    
    def get_skill_detail(self, skill_name: str) -> Optional[SkillDetail]:
        """
        获取技能详细信息
        
        Args:
            skill_name: 技能名称
            
        Returns:
            技能详细信息
        """
        cache_key = f"skill_{skill_name}"
        
        # 检查缓存
        if cache_key in self._skill_cache:
            data, timestamp = self._skill_cache[cache_key]
            if self._is_cache_valid(timestamp):
                return data
        
        # 搜索技能页面
        search_results = self.search_items(skill_name, "gem")
        if not search_results:
            return None
        
        # 使用第一个结果
        skill_url = search_results[0]['url']
        soup = self._make_request(skill_url)
        if not soup:
            return None
        
        try:
            # 解析技能详细信息
            skill_detail = self._parse_skill_detail(soup, skill_url)
            
            # 缓存结果
            self._skill_cache[cache_key] = (skill_detail, datetime.now())
            
            return skill_detail
            
        except Exception as e:
            print(f"解析技能详情失败: {e}")
            return None
    
    def _parse_skill_detail(self, soup: BeautifulSoup, url: str) -> SkillDetail:
        """解析技能详情页面"""
        # 这里简化实现，实际需要根据PoE2DB的HTML结构调整
        name = self._extract_text(soup, ['h1', '.skill-name'])
        name_cn = name  # 如果有中文名，需要额外提取
        
        return SkillDetail(
            name=name or 'Unknown',
            name_cn=name_cn or name or 'Unknown',
            skill_type='active',  # 需要根据页面内容判断
            gem_color='red',      # 需要从页面提取
            level_requirement=1,  # 需要提取
            attribute_requirements={},
            mana_cost=None,
            cast_time=None,
            cooldown=None,
            damage_effectiveness=None,
            description='',
            stat_descriptions=[],
            quality_stats=[],
            level_progression=[],
            tags=[],
            related_items=[],
            wiki_url=url
        )
    
    def get_ascendancy_info(self, ascendancy_name: str) -> Optional[AscendancyInfo]:
        """
        获取升华职业信息
        
        Args:
            ascendancy_name: 升华职业名称
            
        Returns:
            升华职业信息
        """
        # 简化实现，实际需要根据PoE2DB结构调整
        return None
    
    def get_all_ascendancies(self) -> List[AscendancyInfo]:
        """获取所有升华职业信息"""
        # 简化实现
        return []
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            soup = self._make_request(self.base_url)
            if soup:
                return {
                    'status': 'healthy',
                    'base_url': self.base_url,
                    'response_time': time.time() - self.last_request_time,
                    'prefer_chinese': self.prefer_chinese,
                    'cache_size': {
                        'items': len(self._item_cache),
                        'skills': len(self._skill_cache),
                        'searches': len(self._search_cache)
                    }
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': 'Failed to connect'
                }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }


# 全局实例
_client = None

def get_poe2db_client() -> PoE2DBClient:
    """获取全局PoE2DB客户端实例"""
    global _client
    if _client is None:
        _client = PoE2DBClient()
    return _client