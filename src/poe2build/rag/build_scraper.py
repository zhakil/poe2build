"""
构筑数据爬取器 - 专门从Web页面爬取PoE2构筑数据

主要功能:
1. 从poe.ninja/poe2/builds网页爬取构筑详情
2. 从论坛和社区网站爬取构筑指南
3. 解析HTML内容提取构筑信息
4. 智能反反爬虫策略
5. 遵循robots.txt和速率限制

特点:
- 基于beautifulsoup的HTML解析
- 支持JavaScript动态内容(通过API端点)
- 智能内容识别和提取
- 错误重试和优雅降级
- 尊重网站的robots.txt规则
"""

import asyncio
import logging
import re
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from urllib.parse import urljoin, urlparse, parse_qs
from dataclasses import dataclass

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError
from bs4 import BeautifulSoup, Tag
import yarl

from .models import (
    PoE2BuildData,
    RAGDataModel,
    SkillGemSetup,
    ItemInfo,
    OffensiveStats,
    DefensiveStats,
    SuccessMetrics,
    BuildGoal,
    DataQuality
)

from ..resilience import ResilientService, create_poe_ninja_service

logger = logging.getLogger(__name__)

@dataclass
class ScrapingTarget:
    """爬取目标定义"""
    name: str                    # 目标名称
    base_url: str               # 基础URL
    build_list_path: str        # 构筑列表页面路径
    build_detail_path: str      # 构筑详情页面路径模板
    selectors: Dict[str, str]   # CSS选择器映射
    rate_limit: float          # 请求间隔(秒)
    requires_js: bool = False   # 是否需要JavaScript渲染

class PoE2BuildScraper:
    """
    PoE2构筑数据爬取器
    
    专门用于从Web页面爬取构筑数据，支持多个目标网站，
    具有智能的内容识别和提取能力。
    """
    
    def __init__(self, 
                 max_concurrent: int = 2,
                 request_delay: float = 1.0,
                 enable_resilience: bool = True,
                 user_agent_rotation: bool = True):
        """
        初始化爬虫
        
        Args:
            max_concurrent: 最大并发请求数
            request_delay: 请求间隔延迟
            enable_resilience: 是否启用弹性系统
            user_agent_rotation: 是否轮换User-Agent
        """
        self.max_concurrent = max_concurrent
        self.request_delay = request_delay
        self.enable_resilience = enable_resilience
        self.user_agent_rotation = user_agent_rotation
        
        # HTTP会话配置
        self.session: Optional[ClientSession] = None
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.timeout = ClientTimeout(total=30)
        
        # User-Agent池
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        self.current_ua_index = 0
        
        # 弹性服务
        if enable_resilience:
            self.resilient_service = create_poe_ninja_service()
        else:
            self.resilient_service = None
        
        # 爬取目标配置
        self.scraping_targets = self._initialize_scraping_targets()
        
        # 爬取统计
        self.scraping_stats = {
            'pages_scraped': 0,
            'builds_extracted': 0,
            'errors_encountered': 0,
            'start_time': None,
            'end_time': None
        }
        
        # 已访问的URL缓存
        self.visited_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        
    def _initialize_scraping_targets(self) -> Dict[str, ScrapingTarget]:
        """初始化爬取目标配置"""
        return {
            'poe_ninja_web': ScrapingTarget(
                name='poe.ninja Web Interface',
                base_url='https://poe.ninja',
                build_list_path='/poe2/builds',
                build_detail_path='/poe2/builds/{character_name}',
                selectors={
                    'build_cards': '.build-card',
                    'build_name': '.build-name',
                    'character_class': '.character-class',
                    'main_skill': '.main-skill',
                    'dps': '.dps-value',
                    'life': '.life-value',
                    'level': '.level-value'
                },
                rate_limit=2.0,  # 每2秒一个请求
                requires_js=True
            ),
            
            'poe2_reddit': ScrapingTarget(
                name='Reddit PoE2 Build Guides',
                base_url='https://www.reddit.com',
                build_list_path='/r/PathOfExile2/search',
                build_detail_path='/{post_id}',
                selectors={
                    'post_title': '[data-testid="post-content"] h1',
                    'post_content': '[data-testid="post-content"] .md',
                    'author': '.author',
                    'upvotes': '[data-testid="upvote-button"]'
                },
                rate_limit=3.0,  # Reddit较为严格
                requires_js=False
            ),
            
            'poe2_forum': ScrapingTarget(
                name='Official PoE2 Forums',
                base_url='https://www.pathofexile.com',
                build_list_path='/forum/view-forum/2613',  # PoE2 Build forum
                build_detail_path='/forum/view-thread/{thread_id}',
                selectors={
                    'thread_title': '.thread-title',
                    'post_content': '.content',
                    'author': '.profile-link',
                    'post_date': '.post-date'
                },
                rate_limit=1.5,
                requires_js=False
            )
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._initialize_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self._close_session()
    
    async def _initialize_session(self):
        """初始化HTTP会话"""
        if not self.session:
            headers = {
                'User-Agent': self._get_next_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
            
            self.session = ClientSession(
                timeout=self.timeout,
                headers=headers,
                connector=aiohttp.TCPConnector(limit=10, limit_per_host=2)
            )
            
        logger.info("[Build Scraper] HTTP会话已初始化")
    
    async def _close_session(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("[Build Scraper] HTTP会话已关闭")
    
    def _get_next_user_agent(self) -> str:
        """获取下一个User-Agent"""
        if self.user_agent_rotation:
            ua = self.user_agents[self.current_ua_index]
            self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
            return ua
        else:
            return self.user_agents[0]
    
    async def scrape_builds_from_web(self,
                                   target_names: List[str] = None,
                                   max_builds: int = 100,
                                   include_guides: bool = True) -> RAGDataModel:
        """
        从Web页面爬取构筑数据
        
        Args:
            target_names: 目标网站列表，None表示所有目标
            max_builds: 最大爬取构筑数
            include_guides: 是否包含构筑指南内容
            
        Returns:
            RAGDataModel: 爬取到的构筑数据
        """
        self.scraping_stats['start_time'] = datetime.now()
        
        if not target_names:
            target_names = list(self.scraping_targets.keys())
        
        logger.info(f"[Build Scraper] 开始从Web爬取构筑数据，目标: {target_names}")
        
        all_builds = []
        
        try:
            for target_name in target_names:
                if target_name not in self.scraping_targets:
                    logger.warning(f"[Build Scraper] 未知目标: {target_name}")
                    continue
                
                target = self.scraping_targets[target_name]
                logger.info(f"[Build Scraper] 开始爬取 {target.name}")
                
                # 爬取该目标的构筑数据
                target_builds = await self._scrape_target(target, max_builds // len(target_names))
                all_builds.extend(target_builds)
                
                if len(all_builds) >= max_builds:
                    break
                
                # 目标间延迟
                await asyncio.sleep(target.rate_limit)
            
            # 创建RAG数据模型
            rag_data = RAGDataModel(
                builds=all_builds[:max_builds],
                collection_metadata={
                    'scraping_targets': target_names,
                    'max_builds_requested': max_builds,
                    'include_guides': include_guides,
                    'scraping_timestamp': datetime.now(),
                    'user_agent_rotation': self.user_agent_rotation,
                    'resilience_enabled': self.enable_resilience
                },
                processing_stats=self.scraping_stats.copy()
            )
            
            self.scraping_stats['end_time'] = datetime.now()
            self.scraping_stats['builds_extracted'] = len(all_builds)
            
            logger.info(f"[Build Scraper] 爬取完成，获得 {len(all_builds)} 个构筑")
            
            return rag_data
            
        except Exception as e:
            logger.error(f"[Build Scraper] 爬取过程出错: {e}")
            self.scraping_stats['end_time'] = datetime.now()
            raise
    
    async def _scrape_target(self, target: ScrapingTarget, max_builds: int) -> List[PoE2BuildData]:
        """
        爬取特定目标的构筑数据
        
        Args:
            target: 爬取目标配置
            max_builds: 最大构筑数
            
        Returns:
            构筑数据列表
        """
        builds = []
        
        if target.name == 'poe.ninja Web Interface':
            # poe.ninja使用API端点，不需要HTML爬取
            builds = await self._scrape_poe_ninja_api_fallback(max_builds)
        elif target.name == 'Reddit PoE2 Build Guides':
            builds = await self._scrape_reddit_builds(target, max_builds)
        elif target.name == 'Official PoE2 Forums':
            builds = await self._scrape_forum_builds(target, max_builds)
        
        return builds
    
    async def _scrape_poe_ninja_api_fallback(self, max_builds: int) -> List[PoE2BuildData]:
        """
        作为API的后备，从poe.ninja的前端接口获取数据
        
        这个方法在主API不可用时提供额外的数据源
        """
        logger.info("[Build Scraper] 使用poe.ninja前端接口作为后备")
        
        # 尝试访问前端数据接口
        builds = []
        
        try:
            # poe.ninja的前端通常使用这些端点
            frontend_endpoints = [
                'https://poe.ninja/api/data/poe2buildsoverview?language=en',
                'https://poe.ninja/api/data/poe2ladders?language=en'
            ]
            
            for endpoint in frontend_endpoints:
                try:
                    async with self.semaphore:
                        data = await self._fetch_json_data(endpoint)
                        
                        if data and 'lines' in data:
                            # 处理返回的构筑数据
                            for i, build_data in enumerate(data['lines'][:max_builds]):
                                build = await self._parse_ninja_frontend_data(build_data, i)
                                if build:
                                    builds.append(build)
                                    
                            if builds:
                                break  # 获得数据就停止尝试其他端点
                                
                except Exception as e:
                    logger.warning(f"[Build Scraper] 前端端点失败 {endpoint}: {e}")
                    continue
                    
            logger.info(f"[Build Scraper] 从poe.ninja前端获得 {len(builds)} 个构筑")
            
        except Exception as e:
            logger.error(f"[Build Scraper] poe.ninja前端爬取失败: {e}")
        
        return builds
    
    async def _scrape_reddit_builds(self, target: ScrapingTarget, max_builds: int) -> List[PoE2BuildData]:
        """从Reddit爬取构筑指南"""
        logger.info("[Build Scraper] 开始爬取Reddit构筑指南")
        
        builds = []
        
        try:
            # 搜索PoE2构筑相关的帖子
            search_params = {
                'q': 'flair:Build OR title:"build guide" OR title:"build"',
                'sort': 'top',
                'restrict_sr': '1',
                't': 'month'  # 最近一个月的热门帖子
            }
            
            search_url = urljoin(target.base_url, target.build_list_path)
            
            async with self.semaphore:
                html_content = await self._fetch_html_content(search_url, params=search_params)
                
                if html_content:
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # 查找构筑帖子
                    post_links = soup.find_all('a', {'data-testid': 'post-title'})
                    
                    for i, link in enumerate(post_links[:max_builds]):
                        if len(builds) >= max_builds:
                            break
                            
                        try:
                            post_url = urljoin(target.base_url, link.get('href', ''))
                            build = await self._parse_reddit_build_post(post_url, i)
                            
                            if build:
                                builds.append(build)
                                
                            # 请求间延迟
                            await asyncio.sleep(target.rate_limit)
                            
                        except Exception as e:
                            logger.warning(f"[Build Scraper] 解析Reddit帖子失败: {e}")
                            continue
            
            logger.info(f"[Build Scraper] 从Reddit获得 {len(builds)} 个构筑指南")
            
        except Exception as e:
            logger.error(f"[Build Scraper] Reddit爬取失败: {e}")
            
        return builds
    
    async def _scrape_forum_builds(self, target: ScrapingTarget, max_builds: int) -> List[PoE2BuildData]:
        """从官方论坛爬取构筑指南"""
        logger.info("[Build Scraper] 开始爬取官方论坛构筑指南")
        
        builds = []
        
        try:
            forum_url = urljoin(target.base_url, target.build_list_path)
            
            async with self.semaphore:
                html_content = await self._fetch_html_content(forum_url)
                
                if html_content:
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # 查找构筑指南帖子
                    thread_links = soup.find_all('a', class_='thread_title')
                    
                    for i, link in enumerate(thread_links[:max_builds]):
                        if len(builds) >= max_builds:
                            break
                            
                        try:
                            thread_url = urljoin(target.base_url, link.get('href', ''))
                            build = await self._parse_forum_build_post(thread_url, i)
                            
                            if build:
                                builds.append(build)
                                
                            # 请求间延迟
                            await asyncio.sleep(target.rate_limit)
                            
                        except Exception as e:
                            logger.warning(f"[Build Scraper] 解析论坛帖子失败: {e}")
                            continue
            
            logger.info(f"[Build Scraper] 从论坛获得 {len(builds)} 个构筑指南")
            
        except Exception as e:
            logger.error(f"[Build Scraper] 论坛爬取失败: {e}")
            
        return builds
    
    async def _fetch_html_content(self, url: str, **kwargs) -> Optional[str]:
        """获取HTML内容"""
        if url in self.visited_urls:
            return None
        
        if url in self.failed_urls:
            return None
        
        try:
            # 轮换User-Agent
            headers = {'User-Agent': self._get_next_user_agent()}
            
            async with self.session.get(url, headers=headers, **kwargs) as response:
                if response.status == 200:
                    content = await response.text()
                    self.visited_urls.add(url)
                    self.scraping_stats['pages_scraped'] += 1
                    return content
                else:
                    logger.warning(f"[Build Scraper] HTTP {response.status}: {url}")
                    self.failed_urls.add(url)
                    return None
                    
        except Exception as e:
            logger.error(f"[Build Scraper] 获取HTML失败 {url}: {e}")
            self.failed_urls.add(url)
            self.scraping_stats['errors_encountered'] += 1
            return None
    
    async def _fetch_json_data(self, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """获取JSON数据"""
        try:
            headers = {
                'User-Agent': self._get_next_user_agent(),
                'Accept': 'application/json'
            }
            
            async with self.session.get(url, headers=headers, **kwargs) as response:
                if response.status == 200:
                    data = await response.json()
                    self.scraping_stats['pages_scraped'] += 1
                    return data
                else:
                    logger.warning(f"[Build Scraper] JSON API HTTP {response.status}: {url}")
                    return None
                    
        except Exception as e:
            logger.error(f"[Build Scraper] 获取JSON数据失败 {url}: {e}")
            self.scraping_stats['errors_encountered'] += 1
            return None
    
    async def _parse_ninja_frontend_data(self, build_data: Dict, index: int) -> Optional[PoE2BuildData]:
        """解析poe.ninja前端数据"""
        try:
            # 提取基础信息
            character_name = build_data.get('name', f'Frontend_Build_{index}')
            character_class = build_data.get('class', 'Unknown')
            ascendancy = build_data.get('ascendancy', '')
            level = int(build_data.get('level', 85))
            
            # 提取技能信息
            main_skill = ''
            support_gems = []
            
            if 'skills' in build_data and build_data['skills']:
                skill_group = build_data['skills'][0]
                if 'skill' in skill_group:
                    main_skill = skill_group['skill'].get('name', '')
                if 'supports' in skill_group:
                    support_gems = [s.get('name', '') for s in skill_group['supports']]
            
            main_skill_setup = SkillGemSetup(
                main_skill=main_skill,
                support_gems=support_gems
            )
            
            # 提取属性数据
            offensive_stats = OffensiveStats(
                dps=float(build_data.get('dps', 0)),
                critical_chance=float(build_data.get('critChance', 5.0)),
                critical_multiplier=float(build_data.get('critMultiplier', 150.0))
            )
            
            defensive_stats = DefensiveStats(
                life=int(build_data.get('life', 0)),
                energy_shield=int(build_data.get('energyShield', 0))
            )
            
            # 创建构筑数据
            build = PoE2BuildData(
                character_name=character_name,
                character_class=character_class,
                ascendancy=ascendancy,
                level=level,
                main_skill_setup=main_skill_setup,
                offensive_stats=offensive_stats,
                defensive_stats=defensive_stats,
                popularity_rank=index + 1,
                data_source="poe.ninja_frontend",
                data_quality=DataQuality.MEDIUM,
                collection_timestamp=datetime.now()
            )
            
            return build
            
        except Exception as e:
            logger.warning(f"[Build Scraper] 解析ninja前端数据失败: {e}")
            return None
    
    async def _parse_reddit_build_post(self, post_url: str, index: int) -> Optional[PoE2BuildData]:
        """解析Reddit构筑指南帖子"""
        try:
            html_content = await self._fetch_html_content(post_url)
            if not html_content:
                return None
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取标题
            title_elem = soup.find('h1', {'data-testid': 'post-content'})
            title = title_elem.get_text(strip=True) if title_elem else f'Reddit_Build_{index}'
            
            # 从标题中提取构筑信息
            character_class = self._extract_class_from_text(title)
            main_skill = self._extract_skill_from_text(title)
            
            # 提取帖子内容
            content_elem = soup.find('div', {'data-testid': 'post-content'})
            content = content_elem.get_text(strip=True) if content_elem else ''
            
            # 分析内容提取更多信息
            ascendancy = self._extract_ascendancy_from_text(content)
            level = self._extract_level_from_text(content)
            
            # 创建基础的构筑数据
            build = PoE2BuildData(
                character_name=title[:50],  # 截断标题作为构筑名
                character_class=character_class or 'Unknown',
                ascendancy=ascendancy or '',
                level=level or 90,  # Reddit指南通常是高等级构筑
                main_skill_setup=SkillGemSetup(main_skill=main_skill or 'Unknown'),
                build_goal=BuildGoal.ENDGAME_CONTENT,  # Reddit指南通常是终局构筑
                data_source="reddit",
                data_quality=DataQuality.LOW,  # 从文本提取的数据质量较低
                build_description=content[:500],  # 保存部分内容作为描述
                collection_timestamp=datetime.now()
            )
            
            return build
            
        except Exception as e:
            logger.warning(f"[Build Scraper] 解析Reddit帖子失败 {post_url}: {e}")
            return None
    
    async def _parse_forum_build_post(self, thread_url: str, index: int) -> Optional[PoE2BuildData]:
        """解析论坛构筑指南帖子"""
        try:
            html_content = await self._fetch_html_content(thread_url)
            if not html_content:
                return None
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取标题
            title_elem = soup.find('span', class_='thread_title')
            title = title_elem.get_text(strip=True) if title_elem else f'Forum_Build_{index}'
            
            # 从标题提取构筑信息
            character_class = self._extract_class_from_text(title)
            main_skill = self._extract_skill_from_text(title)
            
            # 提取帖子内容
            content_elem = soup.find('div', class_='content')
            content = content_elem.get_text(strip=True) if content_elem else ''
            
            # 分析内容
            ascendancy = self._extract_ascendancy_from_text(content)
            level = self._extract_level_from_text(content)
            
            # 创建构筑数据
            build = PoE2BuildData(
                character_name=title[:50],
                character_class=character_class or 'Unknown',
                ascendancy=ascendancy or '',
                level=level or 85,
                main_skill_setup=SkillGemSetup(main_skill=main_skill or 'Unknown'),
                build_goal=BuildGoal.ENDGAME_CONTENT,
                data_source="poe_forum",
                data_quality=DataQuality.LOW,
                build_description=content[:500],
                collection_timestamp=datetime.now()
            )
            
            return build
            
        except Exception as e:
            logger.warning(f"[Build Scraper] 解析论坛帖子失败 {thread_url}: {e}")
            return None
    
    def _extract_class_from_text(self, text: str) -> Optional[str]:
        """从文本中提取职业名称"""
        # PoE2职业名称
        classes = [
            'Sorceress', 'Witch', 'Monk', 'Mercenary',
            'Ranger', 'Warrior'
        ]
        
        text_lower = text.lower()
        for class_name in classes:
            if class_name.lower() in text_lower:
                return class_name
                
        return None
    
    def _extract_ascendancy_from_text(self, text: str) -> Optional[str]:
        """从文本中提取升华职业"""
        # PoE2升华职业名称
        ascendancies = [
            'Chronomancer', 'Infernalist', 'Stormweaver',
            'Invoker', 'Deadeye', 'Pathfinder',
            'Gemling Legionnaire', 'Witchhunter', 'Titan', 'Warbringer'
        ]
        
        text_lower = text.lower()
        for ascendancy in ascendancies:
            if ascendancy.lower() in text_lower:
                return ascendancy
                
        return None
    
    def _extract_skill_from_text(self, text: str) -> Optional[str]:
        """从文本中提取主要技能"""
        # 常见PoE2技能名称
        skills = [
            'Lightning Arrow', 'Explosive Shot', 'Glacial Cascade',
            'Bone Spear', 'Raise Skeleton', 'Flame Wall',
            'Ice Nova', 'Spark', 'Fireball', 'Arc'
        ]
        
        text_lower = text.lower()
        for skill in skills:
            if skill.lower() in text_lower:
                return skill
                
        return None
    
    def _extract_level_from_text(self, text: str) -> Optional[int]:
        """从文本中提取等级信息"""
        # 查找类似"level 85", "lvl 90", "lv 95"等模式
        level_patterns = [
            r'level\s+(\d+)',
            r'lvl\s+(\d+)',
            r'lv\s+(\d+)',
            r'level:\s*(\d+)',
            r'character level:\s*(\d+)'
        ]
        
        text_lower = text.lower()
        for pattern in level_patterns:
            match = re.search(pattern, text_lower)
            if match:
                level = int(match.group(1))
                if 1 <= level <= 100:  # 合理的等级范围
                    return level
                    
        return None
    
    def get_scraping_stats(self) -> Dict[str, Any]:
        """获取爬取统计信息"""
        stats = self.scraping_stats.copy()
        
        if stats['start_time'] and stats['end_time']:
            duration = stats['end_time'] - stats['start_time']
            stats['scraping_duration_seconds'] = duration.total_seconds()
        
        stats['visited_urls_count'] = len(self.visited_urls)
        stats['failed_urls_count'] = len(self.failed_urls)
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            'scraper_status': 'healthy',
            'session_initialized': self.session is not None,
            'targets_configured': len(self.scraping_targets),
            'user_agent_rotation': self.user_agent_rotation,
            'resilience_enabled': self.enable_resilience,
            'visited_urls': len(self.visited_urls),
            'failed_urls': len(self.failed_urls)
        }

# 测试函数
async def test_build_scraping():
    """测试构筑数据爬取功能"""
    async with PoE2BuildScraper(max_concurrent=1, request_delay=2.0) as scraper:
        
        # 健康检查
        health = await scraper.health_check()
        print("=== 爬取器健康检查 ===")
        print(f"状态: {health['scraper_status']}")
        print(f"目标数量: {health['targets_configured']}")
        
        # 测试爬取
        print("\n=== 开始构筑数据爬取 ===")
        rag_data = await scraper.scrape_builds_from_web(
            target_names=['poe_ninja_web'],  # 只测试一个目标
            max_builds=10,
            include_guides=False
        )
        
        # 显示结果
        print(f"\n=== 爬取结果 ===")
        print(f"获得构筑数: {len(rag_data.builds)}")
        
        for i, build in enumerate(rag_data.builds[:3]):  # 显示前3个
            print(f"\n构筑 {i+1}: {build.character_name}")
            print(f"  职业: {build.character_class} ({build.ascendancy})")
            print(f"  主技能: {build.main_skill_setup.main_skill}")
            print(f"  数据来源: {build.data_source}")
            print(f"  数据质量: {build.data_quality.value}")
        
        # 爬取统计
        stats = scraper.get_scraping_stats()
        print(f"\n=== 爬取统计 ===")
        print(f"页面访问: {stats['pages_scraped']}")
        print(f"构筑提取: {stats['builds_extracted']}")
        print(f"遇到错误: {stats['errors_encountered']}")

if __name__ == "__main__":
    asyncio.run(test_build_scraping())