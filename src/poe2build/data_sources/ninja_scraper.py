"""poe.ninja PoE2数据采集器"""

import asyncio
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

import aiohttp
from bs4 import BeautifulSoup

from .interfaces import IBuildProvider, DataProviderStatus
from .base_provider import BaseProvider, RateLimitConfig, CacheConfig
from ..models.build import PoE2Build, PoE2BuildStats, PoE2BuildGoal
from ..models.characters import PoE2CharacterClass, PoE2Ascendancy


class NinjaPoE2Scraper(BaseProvider, IBuildProvider):
    """poe.ninja PoE2构筑数据采集器"""
    
    def __init__(self, base_url: str = "https://poe.ninja"):
        # ninja特定的速率限制配置（更保守）
        rate_config = RateLimitConfig(
            requests_per_minute=10,  # ninja需要更保守的限制
            requests_per_hour=500,
            backoff_factor=3.0
        )
        
        # 构筑数据缓存配置
        cache_config = CacheConfig(
            default_ttl=1800,       # 30分钟默认缓存
            market_data_ttl=600,    # 市场数据10分钟
            build_data_ttl=1800,    # 构筑数据30分钟
            game_data_ttl=3600      # 游戏数据1小时
        )
        
        super().__init__(
            name="NinjaPoE2",
            base_url=base_url,
            rate_config=rate_config,
            cache_config=cache_config,
            session_config={
                'headers': {
                    'User-Agent': 'PoE2BuildGenerator/2.0 (Educational Purpose)',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate'
                }
            }
        )
        
        self._logger = logging.getLogger(f"{__name__}.NinjaPoE2Scraper")
        
        # PoE2页面路径
        self.poe2_paths = {
            'builds': '/poe2/builds',
            'characters': '/poe2/characters',
            'stats': '/poe2/stats',
            'meta': '/poe2/meta'
        }
        
        # 职业名称映射
        self.class_mapping = {
            'witch': PoE2CharacterClass.WITCH,
            'monk': PoE2CharacterClass.MONK,
            'ranger': PoE2CharacterClass.RANGER,
            'mercenary': PoE2CharacterClass.MERCENARY,
            'warrior': PoE2CharacterClass.WARRIOR,
            'sorceress': PoE2CharacterClass.SORCERESS
        }
    
    async def get_popular_builds(self, 
                                character_class: Optional[PoE2CharacterClass] = None,
                                league: str = "Standard",
                                limit: int = 20) -> List[PoE2Build]:
        """获取热门构筑数据"""
        try:
            # 构建缓存键
            cache_params = {
                'class': character_class.value if character_class else None,
                'league': league,
                'limit': limit
            }
            cache_key = self._generate_cache_key('popular_builds', cache_params)
            
            # 获取构筑页面
            builds_url = f"{self.poe2_paths['builds']}?league={league}"
            if character_class:
                builds_url += f"&class={character_class.value.lower()}"
            
            html_content = await self._make_request(
                'GET',
                builds_url,
                cache_key=cache_key,
                cache_ttl=self.cache.config.build_data_ttl
            )
            
            if not html_content:
                return []
            
            # 解析HTML内容
            builds = await self._parse_builds_page(html_content, league, limit)
            
            # 过滤指定职业
            if character_class:
                builds = [b for b in builds if b.character_class == character_class]
            
            return builds[:limit]
            
        except Exception as e:
            self._logger.error(f"获取热门构筑失败: {e}")
            return []
    
    async def get_build_by_id(self, build_id: str) -> Optional[PoE2Build]:
        """根据ID获取构筑数据"""
        try:
            cache_key = self._generate_cache_key('build_detail', {'id': build_id})
            
            # ninja的构筑详情页面
            detail_url = f"/poe2/builds/{build_id}"
            
            html_content = await self._make_request(
                'GET',
                detail_url,
                cache_key=cache_key,
                cache_ttl=self.cache.config.build_data_ttl
            )
            
            if not html_content:
                return None
            
            return await self._parse_build_detail(html_content, build_id)
            
        except Exception as e:
            self._logger.error(f"获取构筑详情失败 ({build_id}): {e}")
            return None
    
    async def search_builds(self, query: Dict[str, Any], limit: int = 20) -> List[PoE2Build]:
        """搜索构筑数据"""
        try:
            # 构建搜索参数
            search_params = self._build_search_params(query)
            search_params['limit'] = limit
            
            cache_key = self._generate_cache_key('search_builds', search_params)
            
            # 构建搜索URL
            search_url = f"{self.poe2_paths['builds']}?" + "&".join(
                f"{k}={v}" for k, v in search_params.items() if v is not None
            )
            
            html_content = await self._make_request(
                'GET',
                search_url,
                cache_key=cache_key,
                cache_ttl=self.cache.config.build_data_ttl
            )
            
            if not html_content:
                return []
            
            return await self._parse_builds_page(html_content, query.get('league', 'Standard'), limit)
            
        except Exception as e:
            self._logger.error(f"搜索构筑失败: {e}")
            return []
    
    async def get_meta_analysis(self, league: str = "Standard") -> Dict[str, Any]:
        """获取Meta分析数据"""
        try:
            cache_key = self._generate_cache_key('meta_analysis', {'league': league})
            
            meta_url = f"{self.poe2_paths['meta']}?league={league}"
            
            html_content = await self._make_request(
                'GET',
                meta_url,
                cache_key=cache_key,
                cache_ttl=3600  # Meta分析1小时缓存
            )
            
            if not html_content:
                return {}
            
            return await self._parse_meta_page(html_content, league)
            
        except Exception as e:
            self._logger.error(f"获取Meta分析失败: {e}")
            return {}
    
    async def get_build_trends(self, timeframe: str = "7d") -> Dict[str, Any]:
        """获取构筑趋势数据"""
        try:
            cache_key = self._generate_cache_key('build_trends', {'timeframe': timeframe})
            
            trends_url = f"{self.poe2_paths['stats']}?timeframe={timeframe}"
            
            html_content = await self._make_request(
                'GET',
                trends_url,
                cache_key=cache_key,
                cache_ttl=3600  # 趋势数据1小时缓存
            )
            
            if not html_content:
                return {}
            
            return await self._parse_trends_page(html_content, timeframe)
            
        except Exception as e:
            self._logger.error(f"获取构筑趋势失败: {e}")
            return {}
    
    async def _parse_builds_page(self, html_content: str, league: str, limit: int) -> List[PoE2Build]:
        """解析构筑页面"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            builds = []
            
            # 查找构筑表格或列表
            build_containers = soup.find_all(['tr', 'div'], class_=re.compile(r'build|character'))
            
            for container in build_containers[:limit]:
                build = await self._parse_build_container(container, league)
                if build:
                    builds.append(build)
            
            return builds
            
        except Exception as e:
            self._logger.error(f"解析构筑页面失败: {e}")
            return []
    
    async def _parse_build_container(self, container, league: str) -> Optional[PoE2Build]:
        """解析单个构筑容器"""
        try:
            # 提取基本信息
            name = self._extract_text(container, ['name', 'build-name', 'title'])
            if not name:
                name = f"Unknown Build {datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 提取职业信息
            class_text = self._extract_text(container, ['class', 'character-class', 'ascendancy'])
            character_class = self._parse_character_class(class_text)
            
            # 提取等级
            level_text = self._extract_text(container, ['level', 'char-level'])
            level = self._parse_level(level_text)
            
            # 提取主技能
            skill_text = self._extract_text(container, ['skill', 'main-skill', 'gem'])
            main_skill = skill_text or "Unknown Skill"
            
            # 提取统计数据
            stats = await self._parse_build_stats(container)
            
            # 创建构筑对象
            build = PoE2Build(
                name=name,
                character_class=character_class,
                level=level,
                stats=stats,
                main_skill_gem=main_skill,
                league=league,
                source_url=f"{self.base_url}/poe2/builds",
                created_by="ninja.poe2",
                last_updated=datetime.now().isoformat()
            )
            
            return build
            
        except Exception as e:
            self._logger.error(f"解析构筑容器失败: {e}")
            return None
    
    async def _parse_build_stats(self, container) -> Optional[PoE2BuildStats]:
        """解析构筑统计数据"""
        try:
            # 提取DPS数据
            dps_text = self._extract_text(container, ['dps', 'damage', 'total-dps'])
            total_dps = self._parse_number(dps_text)
            
            # 提取生命值数据
            life_text = self._extract_text(container, ['life', 'hp', 'health'])
            life = self._parse_number(life_text)
            
            # 提取能量护盾数据
            es_text = self._extract_text(container, ['es', 'energy-shield', 'shield'])
            energy_shield = self._parse_number(es_text)
            
            # 计算有效生命值
            ehp = life + energy_shield * 0.5  # 简化的EHP计算
            
            # 提取抗性数据（如果有）
            fire_res = self._extract_resistance(container, 'fire')
            cold_res = self._extract_resistance(container, 'cold')
            lightning_res = self._extract_resistance(container, 'lightning')
            chaos_res = self._extract_resistance(container, 'chaos')
            
            if total_dps > 0 or ehp > 0:
                return PoE2BuildStats(
                    total_dps=total_dps,
                    effective_health_pool=ehp,
                    life=life,
                    energy_shield=energy_shield,
                    fire_resistance=fire_res,
                    cold_resistance=cold_res,
                    lightning_resistance=lightning_res,
                    chaos_resistance=chaos_res
                )
            
            return None
            
        except Exception as e:
            self._logger.error(f"解析构筑统计失败: {e}")
            return None
    
    async def _parse_build_detail(self, html_content: str, build_id: str) -> Optional[PoE2Build]:
        """解析构筑详情页面"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 详情页面通常有更完整的信息
            # 这里需要根据ninja实际的页面结构来实现
            # 目前返回基础解析
            
            build_container = soup.find(['div', 'section'], class_=re.compile(r'build-detail|character-detail'))
            if not build_container:
                return None
            
            return await self._parse_build_container(build_container, "Standard")
            
        except Exception as e:
            self._logger.error(f"解析构筑详情失败: {e}")
            return None
    
    async def _parse_meta_page(self, html_content: str, league: str) -> Dict[str, Any]:
        """解析Meta分析页面"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            meta_data = {}
            
            # 提取职业分布
            class_distribution = {}
            class_containers = soup.find_all(['div', 'tr'], class_=re.compile(r'class|ascendancy'))
            
            for container in class_containers:
                class_name = self._extract_text(container, ['name', 'class'])
                percentage = self._extract_text(container, ['percent', 'popularity', '%'])
                
                if class_name and percentage:
                    percentage_value = self._parse_percentage(percentage)
                    if percentage_value > 0:
                        class_distribution[class_name] = percentage_value
            
            meta_data['class_distribution'] = class_distribution
            
            # 提取技能分布
            skill_distribution = {}
            skill_containers = soup.find_all(['div', 'tr'], class_=re.compile(r'skill|gem'))
            
            for container in skill_containers:
                skill_name = self._extract_text(container, ['name', 'skill'])
                usage = self._extract_text(container, ['usage', 'popularity', '%'])
                
                if skill_name and usage:
                    usage_value = self._parse_percentage(usage)
                    if usage_value > 0:
                        skill_distribution[skill_name] = usage_value
            
            meta_data['skill_distribution'] = skill_distribution
            meta_data['league'] = league
            meta_data['last_updated'] = datetime.now().isoformat()
            
            return meta_data
            
        except Exception as e:
            self._logger.error(f"解析Meta页面失败: {e}")
            return {}
    
    async def _parse_trends_page(self, html_content: str, timeframe: str) -> Dict[str, Any]:
        """解析趋势页面"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            trends_data = {
                'timeframe': timeframe,
                'rising_builds': [],
                'falling_builds': [],
                'stable_builds': [],
                'last_updated': datetime.now().isoformat()
            }
            
            # 查找趋势指示器
            trend_containers = soup.find_all(['div', 'tr'], class_=re.compile(r'trend|change'))
            
            for container in trend_containers:
                build_name = self._extract_text(container, ['name', 'build'])
                trend_indicator = self._extract_text(container, ['trend', 'change', 'direction'])
                
                if build_name and trend_indicator:
                    trend_data = {
                        'name': build_name,
                        'trend': trend_indicator
                    }
                    
                    if 'up' in trend_indicator.lower() or '+' in trend_indicator:
                        trends_data['rising_builds'].append(trend_data)
                    elif 'down' in trend_indicator.lower() or '-' in trend_indicator:
                        trends_data['falling_builds'].append(trend_data)
                    else:
                        trends_data['stable_builds'].append(trend_data)
            
            return trends_data
            
        except Exception as e:
            self._logger.error(f"解析趋势页面失败: {e}")
            return {}
    
    def _build_search_params(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """构建搜索参数"""
        params = {}
        
        if 'class' in query:
            params['class'] = query['class'].lower() if hasattr(query['class'], 'lower') else str(query['class']).lower()
        
        if 'league' in query:
            params['league'] = query['league']
        
        if 'skill' in query:
            params['skill'] = query['skill']
        
        if 'min_level' in query:
            params['minlevel'] = query['min_level']
        
        if 'max_level' in query:
            params['maxlevel'] = query['max_level']
        
        return params
    
    def _extract_text(self, container, selectors: List[str]) -> Optional[str]:
        """从容器中提取文本"""
        for selector in selectors:
            # 尝试CSS类选择器
            element = container.find(class_=re.compile(selector, re.I))
            if element:
                return element.get_text(strip=True)
            
            # 尝试标签选择器
            element = container.find(attrs={'data-field': selector})
            if element:
                return element.get_text(strip=True)
        
        return None
    
    def _parse_character_class(self, class_text: Optional[str]) -> PoE2CharacterClass:
        """解析职业文本"""
        if not class_text:
            return PoE2CharacterClass.WITCH
        
        class_lower = class_text.lower()
        for name, poe_class in self.class_mapping.items():
            if name in class_lower:
                return poe_class
        
        return PoE2CharacterClass.WITCH
    
    def _parse_level(self, level_text: Optional[str]) -> int:
        """解析等级文本"""
        if not level_text:
            return 1
        
        # 提取数字
        numbers = re.findall(r'\d+', level_text)
        if numbers:
            level = int(numbers[0])
            return max(1, min(100, level))
        
        return 1
    
    def _parse_number(self, text: Optional[str]) -> float:
        """解析数字文本"""
        if not text:
            return 0.0
        
        # 移除非数字字符，保留小数点和k/m标识
        cleaned = re.sub(r'[^\d.km]', '', text.lower())
        
        if not cleaned:
            return 0.0
        
        # 处理k和m后缀
        multiplier = 1
        if cleaned.endswith('k'):
            multiplier = 1000
            cleaned = cleaned[:-1]
        elif cleaned.endswith('m'):
            multiplier = 1000000
            cleaned = cleaned[:-1]
        
        try:
            return float(cleaned) * multiplier
        except ValueError:
            return 0.0
    
    def _parse_percentage(self, text: Optional[str]) -> float:
        """解析百分比文本"""
        if not text:
            return 0.0
        
        numbers = re.findall(r'[\d.]+', text)
        if numbers:
            return float(numbers[0])
        
        return 0.0
    
    def _extract_resistance(self, container, res_type: str) -> int:
        """提取抗性值"""
        res_text = self._extract_text(container, [f'{res_type}-res', f'{res_type}', f'res-{res_type}'])
        if res_text:
            percentage = self._parse_percentage(res_text)
            return int(max(-100, min(80, percentage)))  # PoE2抗性范围
        return 75  # 默认值
    
    async def test_connection(self) -> bool:
        """测试ninja连接"""
        try:
            response = await self._make_request('GET', '/poe2', timeout=10)
            return response is not None and len(response) > 1000
        except Exception:
            return False


# Mock Ninja数据提供者
class MockNinjaPoE2Scraper(IBuildProvider):
    """Mock ninja.poe2数据提供者"""
    
    def __init__(self):
        self.name = "MockNinjaPoE2"
        self._logger = logging.getLogger(f"{__name__}.MockNinjaPoE2Scraper")
    
    async def get_health_status(self) -> DataProviderStatus:
        return DataProviderStatus.HEALTHY
    
    async def test_connection(self) -> bool:
        return True
    
    def get_provider_name(self) -> str:
        return self.name
    
    def get_rate_limit_info(self) -> Dict[str, int]:
        return {'requests_per_minute': 999, 'requests_per_hour': 9999}
    
    async def get_popular_builds(self, character_class: Optional[PoE2CharacterClass] = None,
                               league: str = "Standard", limit: int = 20) -> List[PoE2Build]:
        """返回Mock热门构筑"""
        self._logger.warning(f"使用Mock热门构筑数据: {character_class}")
        
        builds = []
        classes = [character_class] if character_class else list(PoE2CharacterClass)
        
        for i, cls in enumerate(classes[:limit]):
            stats = PoE2BuildStats(
                total_dps=500000 + i * 100000,
                effective_health_pool=8000 + i * 500,
                life=6000 + i * 300,
                energy_shield=2000 + i * 200,
                fire_resistance=75,
                cold_resistance=75,
                lightning_resistance=75,
                chaos_resistance=-30
            )
            
            build = PoE2Build(
                name=f"Mock {cls.value} Build {i+1}",
                character_class=cls,
                level=85 + i,
                stats=stats,
                main_skill_gem=f"Mock Skill {i+1}",
                goal=PoE2BuildGoal.ENDGAME_CONTENT,
                league=league,
                estimated_cost=10.0 + i * 2,
                source_url="mock://ninja.poe2",
                created_by="MockNinja"
            )
            builds.append(build)
        
        return builds
    
    async def get_build_by_id(self, build_id: str) -> Optional[PoE2Build]:
        """返回Mock构筑详情"""
        self._logger.warning(f"使用Mock构筑详情: {build_id}")
        
        stats = PoE2BuildStats(
            total_dps=750000,
            effective_health_pool=8500,
            life=6500,
            energy_shield=2000,
            fire_resistance=76,
            cold_resistance=77,
            lightning_resistance=75,
            chaos_resistance=-25
        )
        
        return PoE2Build(
            name=f"Mock Build {build_id}",
            character_class=PoE2CharacterClass.WITCH,
            level=90,
            stats=stats,
            main_skill_gem="Mock Primary Skill",
            goal=PoE2BuildGoal.BOSS_KILLING,
            league="Standard",
            estimated_cost=15.0,
            source_url=f"mock://ninja.poe2/builds/{build_id}",
            created_by="MockNinja"
        )
    
    async def search_builds(self, query: Dict[str, Any], limit: int = 20) -> List[PoE2Build]:
        """返回Mock搜索结果"""
        self._logger.warning("使用Mock构筑搜索")
        return await self.get_popular_builds(limit=limit)
    
    async def get_meta_analysis(self, league: str = "Standard") -> Dict[str, Any]:
        """返回Mock Meta分析"""
        self._logger.warning("使用Mock Meta分析")
        return {
            'class_distribution': {
                'Witch': 25.5,
                'Monk': 18.2,
                'Ranger': 15.8,
                'Mercenary': 14.1,
                'Warrior': 13.4,
                'Sorceress': 13.0
            },
            'skill_distribution': {
                'Lightning Bolt': 22.1,
                'Fireball': 18.5,
                'Ice Shard': 15.2,
                'Poison Arrow': 12.8,
                'Shield Slam': 10.4
            },
            'league': league,
            'last_updated': datetime.now().isoformat()
        }
    
    async def get_build_trends(self, timeframe: str = "7d") -> Dict[str, Any]:
        """返回Mock趋势数据"""
        self._logger.warning(f"使用Mock趋势数据: {timeframe}")
        return {
            'timeframe': timeframe,
            'rising_builds': [
                {'name': 'Lightning Monk', 'trend': '+15%'},
                {'name': 'Ice Witch', 'trend': '+8%'}
            ],
            'falling_builds': [
                {'name': 'Fire Sorceress', 'trend': '-5%'},
                {'name': 'Poison Ranger', 'trend': '-3%'}
            ],
            'stable_builds': [
                {'name': 'Shield Warrior', 'trend': '0%'}
            ],
            'last_updated': datetime.now().isoformat()
        }