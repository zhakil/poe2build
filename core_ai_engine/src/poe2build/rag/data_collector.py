"""
RAG数据收集器 - 从多个数据源采集PoE2构筑数据

主要功能:
1. 从poe.ninja/poe2采集热门构筑数据
2. 从poe2scout.com获取物品价格信息
3. 从poe2db.tw获取游戏数据
4. 异步批量处理，支持并发采集
5. 集成弹性系统，遵循"生态公民"原则

设计理念:
- 尊重API限制，使用适当的速率限制
- 优雅的错误处理和降级策略
- 数据质量评估和过滤
- 支持增量更新和全量更新
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import asdict
from urllib.parse import urljoin, urlparse

import aiohttp
from aiohttp import ClientTimeout, ClientError
import yarl

from .models import (
    PoE2BuildData, 
    RAGDataModel, 
    SuccessMetrics,
    SkillGemSetup,
    ItemInfo,
    OffensiveStats,
    DefensiveStats,
    BuildGoal,
    DataQuality
)

from ..resilience import (
    ResilientService, 
    create_poe_ninja_service,
    create_poe2_scout_service,
    create_poe2db_service,
    CircuitBreakerState
)

from ..data_sources import BaseDataSource

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PoE2RAGDataCollector:
    """
    PoE2 RAG数据收集器
    
    负责从多个数据源异步采集构筑数据，并将其转换为RAG系统可用的标准格式。
    集成了完整的弹性系统和错误处理机制。
    """
    
    def __init__(self, 
                 session_timeout: int = 30,
                 max_concurrent_requests: int = 3,
                 enable_resilience: bool = True):
        """
        初始化数据收集器
        
        Args:
            session_timeout: HTTP会话超时时间(秒)
            max_concurrent_requests: 最大并发请求数
            enable_resilience: 是否启用弹性系统
        """
        self.session_timeout = session_timeout
        self.max_concurrent_requests = max_concurrent_requests
        self.enable_resilience = enable_resilience
        
        # HTTP会话配置
        self.timeout = ClientTimeout(total=session_timeout)
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        
        # 弹性服务
        if enable_resilience:
            self.poe_ninja_service = create_poe_ninja_service()
            self.poe2_scout_service = create_poe2_scout_service()  
            self.poe2db_service = create_poe2db_service()
        else:
            self.poe_ninja_service = None
            self.poe2_scout_service = None
            self.poe2db_service = None
        
        # API端点配置
        self.api_endpoints = {
            'poe_ninja': {
                'base_url': 'https://poe.ninja/api/data',
                'builds': '/poe2buildsoverview',
                'characters': '/poe2characters', 
                'items': '/poe2itemsoverview'
            },
            'poe2_scout': {
                'base_url': 'https://api.poe2scout.com',
                'search': '/search',
                'item': '/item'
            },
            'poe2db': {
                'base_url': 'https://poe2db.tw/api',
                'skills': '/skills',
                'items': '/items'
            }
        }
        
        # 收集统计
        self.collection_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cached_responses': 0,
            'builds_collected': 0,
            'unique_builds': 0,
            'collection_start_time': None,
            'collection_end_time': None
        }
        
        # 数据缓存
        self.collected_builds: List[PoE2BuildData] = []
        self.skill_metadata: Dict[str, Any] = {}
        self.item_prices: Dict[str, float] = {}
        
    async def __aenter__(self):
        """异步上下文管理器进入"""
        await self._initialize_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self._close_session()
        
    async def _initialize_session(self):
        """初始化HTTP会话"""
        if not self.session:
            headers = {
                'User-Agent': 'PoE2-RAG-Collector/1.0 (https://github.com/your-repo; Educational Purpose)',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache'
            }
            
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers=headers,
                connector=aiohttp.TCPConnector(limit=10, limit_per_host=3)
            )
            
        logger.info("[RAG Collector] HTTP会话已初始化")
        
    async def _close_session(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("[RAG Collector] HTTP会话已关闭")
    
    async def collect_comprehensive_build_data(self, 
                                             league: str = "Standard",
                                             limit: int = 1000,
                                             include_prices: bool = True,
                                             quality_filter: DataQuality = DataQuality.LOW) -> RAGDataModel:
        """
        采集全面的构筑数据用于RAG训练
        
        Args:
            league: 联赛名称
            limit: 采集构筑数量限制
            include_prices: 是否包含价格信息
            quality_filter: 数据质量过滤等级
            
        Returns:
            RAGDataModel: 包含所有采集数据的模型
        """
        self.collection_stats['collection_start_time'] = datetime.now()
        
        logger.info(f"[RAG Collector] 开始采集PoE2构筑数据 (联赛: {league}, 限制: {limit})")
        
        try:
            # 确保会话已初始化
            if not self.session:
                await self._initialize_session()
            
            # 并发采集多种数据
            tasks = [
                self._collect_popular_builds(league, limit),
                self._collect_class_distribution(league),
                self._collect_skill_metadata(),
            ]
            
            if include_prices:
                tasks.append(self._collect_item_prices())
            
            # 等待所有采集任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理采集结果
            popular_builds = results[0] if not isinstance(results[0], Exception) else []
            class_distribution = results[1] if not isinstance(results[1], Exception) else {}
            skill_meta = results[2] if not isinstance(results[2], Exception) else {}
            
            if include_prices and len(results) > 3:
                item_trends = results[3] if not isinstance(results[3], Exception) else {}
            else:
                item_trends = {}
            
            # 构建综合数据集
            comprehensive_builds = await self._build_comprehensive_dataset(
                popular_builds, class_distribution, skill_meta, item_trends
            )
            
            # 创建RAG数据模型
            rag_data = RAGDataModel(
                builds=comprehensive_builds,
                collection_metadata={
                    'league': league,
                    'collection_timestamp': datetime.now(),
                    'source_endpoints': list(self.api_endpoints.keys()),
                    'total_sources_attempted': len(tasks),
                    'successful_sources': sum(1 for r in results if not isinstance(r, Exception)),
                    'include_prices': include_prices,
                    'quality_filter': quality_filter.value
                },
                processing_stats=self.collection_stats.copy()
            )
            
            # 应用质量过滤
            if quality_filter != DataQuality.LOW:
                rag_data = rag_data.filter_by_quality(quality_filter)
            
            self.collection_stats['collection_end_time'] = datetime.now()
            self.collection_stats['builds_collected'] = len(comprehensive_builds)
            self.collection_stats['unique_builds'] = len(rag_data.get_unique_builds().builds)
            
            logger.info(f"[RAG Collector] 采集完成，获得 {len(comprehensive_builds)} 个构筑")
            
            return rag_data
            
        except Exception as e:
            logger.error(f"[RAG Collector] 采集过程出错: {e}")
            self.collection_stats['collection_end_time'] = datetime.now()
            raise
    
    async def _collect_popular_builds(self, league: str, limit: int) -> List[Dict[str, Any]]:
        """
        从poe.ninja采集热门构筑数据
        
        Args:
            league: 联赛名称
            limit: 构筑数量限制
            
        Returns:
            构筑数据列表
        """
        logger.info(f"[RAG Collector] 开始采集热门构筑数据 (限制: {limit})")
        
        endpoint = self.api_endpoints['poe_ninja']
        url = urljoin(endpoint['base_url'], endpoint['builds'])
        
        params = {
            'league': league,
            'type': 'builds',  
            'language': 'en'
        }
        
        try:
            async with self.semaphore:  # 控制并发数
                builds_data = await self._make_resilient_request(
                    'poe_ninja', url, params=params
                )
                
                if builds_data and 'lines' in builds_data:
                    builds = builds_data['lines'][:limit]  # 应用限制
                    logger.info(f"[RAG Collector] 成功采集 {len(builds)} 个热门构筑")
                    return builds
                else:
                    logger.warning("[RAG Collector] poe.ninja响应中未找到构筑数据")
                    return []
                    
        except Exception as e:
            logger.error(f"[RAG Collector] 采集热门构筑失败: {e}")
            return []
    
    async def _collect_class_distribution(self, league: str) -> Dict[str, Any]:
        """采集职业分布数据"""
        logger.info("[RAG Collector] 开始采集职业分布数据")
        
        endpoint = self.api_endpoints['poe_ninja']
        url = urljoin(endpoint['base_url'], endpoint['characters'])
        
        params = {
            'league': league,
            'type': 'characters'
        }
        
        try:
            async with self.semaphore:
                char_data = await self._make_resilient_request(
                    'poe_ninja', url, params=params
                )
                
                if char_data:
                    logger.info("[RAG Collector] 职业分布数据采集完成")
                    return char_data
                else:
                    return {}
                    
        except Exception as e:
            logger.error(f"[RAG Collector] 采集职业分布失败: {e}")
            return {}
    
    async def _collect_skill_metadata(self) -> Dict[str, Any]:
        """采集技能元数据和流行度"""
        logger.info("[RAG Collector] 开始采集技能元数据")
        
        # 尝试从poe2db获取技能数据
        endpoint = self.api_endpoints['poe2db']
        url = urljoin(endpoint['base_url'], endpoint['skills'])
        
        try:
            async with self.semaphore:
                skill_data = await self._make_resilient_request(
                    'poe2db', url
                )
                
                if skill_data:
                    logger.info("[RAG Collector] 技能元数据采集完成")
                    return skill_data
                else:
                    # 如果poe2db不可用，返回基础技能数据
                    return self._get_fallback_skill_data()
                    
        except Exception as e:
            logger.error(f"[RAG Collector] 采集技能元数据失败: {e}")
            return self._get_fallback_skill_data()
    
    async def _collect_item_prices(self) -> Dict[str, float]:
        """采集物品价格数据"""
        logger.info("[RAG Collector] 开始采集物品价格数据")
        
        # 常见PoE2构筑物品列表
        important_items = [
            "Midnight Fang", "The Last Resort", "Doryani's Fist",
            "Shavronne's Wrappings", "Pillars of Arun", "Thirst for Knowledge",
            "Sanguimancy", "Shaper of Storms"
        ]
        
        prices = {}
        
        for item_name in important_items:
            try:
                async with self.semaphore:
                    price = await self._get_item_price(item_name)
                    if price > 0:
                        prices[item_name] = price
                        
                    # 添加延迟避免过于频繁的请求
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.warning(f"[RAG Collector] 获取物品价格失败 {item_name}: {e}")
                continue
        
        logger.info(f"[RAG Collector] 物品价格采集完成，获得 {len(prices)} 个价格")
        return prices
    
    async def _get_item_price(self, item_name: str) -> float:
        """获取单个物品价格"""
        endpoint = self.api_endpoints['poe2_scout']
        url = urljoin(endpoint['base_url'], endpoint['search'])
        
        params = {
            'q': item_name,
            'type': 'item'
        }
        
        try:
            price_data = await self._make_resilient_request(
                'poe2_scout', url, params=params
            )
            
            if price_data and 'results' in price_data:
                results = price_data['results']
                if results:
                    # 取第一个结果的价格
                    first_result = results[0]
                    return float(first_result.get('price', 0))
                    
            return 0.0
            
        except Exception as e:
            logger.warning(f"[RAG Collector] 获取 {item_name} 价格失败: {e}")
            return 0.0
    
    async def _build_comprehensive_dataset(self,
                                         builds: List[Dict],
                                         class_dist: Dict,
                                         skill_meta: Dict,
                                         item_trends: Dict) -> List[PoE2BuildData]:
        """
        构建综合构筑数据集
        
        Args:
            builds: 原始构筑数据
            class_dist: 职业分布数据
            skill_meta: 技能元数据  
            item_trends: 物品价格数据
            
        Returns:
            标准化的构筑数据列表
        """
        logger.info(f"[RAG Collector] 开始构建综合数据集，处理 {len(builds)} 个构筑")
        
        comprehensive_builds = []
        
        for i, build in enumerate(builds):
            try:
                # 创建构筑数据对象
                build_data = await self._parse_build_data(
                    build, i, class_dist, skill_meta, item_trends
                )
                
                if build_data and self._validate_build_data(build_data):
                    comprehensive_builds.append(build_data)
                    
                # 每处理100个构筑输出进度
                if (i + 1) % 100 == 0:
                    logger.info(f"[RAG Collector] 已处理 {i + 1}/{len(builds)} 个构筑")
                    
            except Exception as e:
                logger.warning(f"[RAG Collector] 处理构筑 {i} 时出错: {e}")
                continue
        
        logger.info(f"[RAG Collector] 构建完成，有效构筑: {len(comprehensive_builds)}")
        return comprehensive_builds
    
    async def _parse_build_data(self,
                               build: Dict,
                               index: int,
                               class_dist: Dict,
                               skill_meta: Dict,
                               item_trends: Dict) -> Optional[PoE2BuildData]:
        """
        解析单个构筑数据
        
        Args:
            build: 原始构筑数据
            index: 构筑索引
            class_dist: 职业分布
            skill_meta: 技能元数据
            item_trends: 物品价格
            
        Returns:
            解析后的构筑数据
        """
        try:
            # 提取基础信息
            character_name = build.get('name', f'Build_{index}')
            character_class = build.get('class', 'Unknown')
            ascendancy = build.get('ascendancy', '')
            level = int(build.get('level', 85))
            
            # 提取技能信息
            main_skill_setup = self._extract_main_skill_setup(build)
            
            # 提取装备信息
            weapon, other_items = self._extract_equipment_info(build, item_trends)
            
            # 提取属性数据
            offensive_stats = self._extract_offensive_stats(build)
            defensive_stats = self._extract_defensive_stats(build)
            
            # 计算成本和成功指标
            total_cost = self._calculate_total_cost(other_items, item_trends)
            success_metrics = self._calculate_success_metrics(
                build, skill_meta, class_dist
            )
            
            # 确定构筑目标和数据质量
            build_goal = self._determine_build_goal(build, offensive_stats, defensive_stats)
            data_quality = self._assess_data_quality(build)
            
            # 创建构筑数据对象
            build_data = PoE2BuildData(
                character_name=character_name,
                character_class=character_class,
                ascendancy=ascendancy,
                level=level,
                main_skill_setup=main_skill_setup,
                weapon=weapon,
                offensive_stats=offensive_stats,
                defensive_stats=defensive_stats,
                passive_keystones=self._extract_keystones(build),
                total_cost=total_cost,
                popularity_rank=index + 1,
                success_metrics=success_metrics,
                build_goal=build_goal,
                data_source="poe.ninja",
                data_quality=data_quality,
                collection_timestamp=datetime.now()
            )
            
            return build_data
            
        except Exception as e:
            logger.warning(f"[RAG Collector] 解析构筑数据失败: {e}")
            return None
    
    def _extract_main_skill_setup(self, build: Dict) -> SkillGemSetup:
        """提取主技能配置"""
        skills = build.get('skills', [])
        
        if not skills:
            return SkillGemSetup()
        
        # 通常第一个技能组是主技能
        main_skill_group = skills[0]
        
        main_skill = ""
        support_gems = []
        
        if isinstance(main_skill_group, dict):
            # 提取主技能名称
            if 'skill' in main_skill_group:
                skill_info = main_skill_group['skill']
                if isinstance(skill_info, dict):
                    main_skill = skill_info.get('name', '')
                else:
                    main_skill = str(skill_info)
            
            # 提取辅助宝石
            supports = main_skill_group.get('supports', [])
            for support in supports:
                if isinstance(support, dict):
                    support_name = support.get('name', '')
                elif isinstance(support, str):
                    support_name = support
                else:
                    continue
                    
                if support_name and support_name not in support_gems:
                    support_gems.append(support_name)
        
        return SkillGemSetup(
            main_skill=main_skill,
            support_gems=support_gems,
            links=len(support_gems) + 1 if main_skill else 0
        )
    
    def _extract_equipment_info(self, build: Dict, item_prices: Dict) -> Tuple[Optional[ItemInfo], List[ItemInfo]]:
        """提取装备信息"""
        items = build.get('items', [])
        weapon = None
        other_items = []
        
        for item in items:
            if not isinstance(item, dict):
                continue
                
            item_name = item.get('name', '')
            item_type = item.get('type', '')
            
            if not item_name:
                continue
            
            # 获取价格
            price = item_prices.get(item_name, 0.0)
            
            item_info = ItemInfo(
                name=item_name,
                type=item_type,
                price=price,
                currency="divine"
            )
            
            # 判断是否为武器
            if any(weapon_type in item_type.lower() for weapon_type in 
                  ['weapon', 'sword', 'axe', 'mace', 'bow', 'staff', 'wand', 'dagger']):
                if not weapon:  # 只保留第一个武器作为主武器
                    weapon = item_info
            else:
                other_items.append(item_info)
        
        return weapon, other_items
    
    def _extract_offensive_stats(self, build: Dict) -> OffensiveStats:
        """提取攻击属性"""
        return OffensiveStats(
            dps=float(build.get('dps', 0)),
            average_damage=float(build.get('damage', 0)),
            critical_chance=float(build.get('critChance', 5.0)),
            critical_multiplier=float(build.get('critMultiplier', 150.0)),
            accuracy=float(build.get('accuracy', 90.0))
        )
    
    def _extract_defensive_stats(self, build: Dict) -> DefensiveStats:
        """提取防御属性"""
        return DefensiveStats(
            life=int(build.get('life', 0)),
            energy_shield=int(build.get('energyShield', 0)),
            fire_resistance=int(build.get('fireRes', 75)),
            cold_resistance=int(build.get('coldRes', 75)),
            lightning_resistance=int(build.get('lightningRes', 75)),
            chaos_resistance=int(build.get('chaosRes', -30)),
            armour=int(build.get('armour', 0)),
            evasion=int(build.get('evasion', 0))
        )
    
    def _extract_keystones(self, build: Dict) -> List[str]:
        """提取关键天赋"""
        keystones = []
        
        # 尝试从不同的可能字段中提取关键天赋
        keystone_fields = ['keystones', 'passiveKeystones', 'keyPassives']
        
        for field in keystone_fields:
            if field in build and build[field]:
                if isinstance(build[field], list):
                    keystones.extend(build[field])
                elif isinstance(build[field], str):
                    keystones.append(build[field])
        
        # 清理和去重
        return list(set([ks.strip() for ks in keystones if ks and ks.strip()]))
    
    def _calculate_total_cost(self, items: List[ItemInfo], item_prices: Dict) -> float:
        """计算构筑总成本"""
        total_cost = 0.0
        
        for item in items:
            if item.price > 0:
                total_cost += item.price
            elif item.name in item_prices:
                total_cost += item_prices[item.name]
        
        return total_cost
    
    def _calculate_success_metrics(self, 
                                 build: Dict,
                                 skill_meta: Dict,
                                 class_dist: Dict) -> SuccessMetrics:
        """计算构筑成功指标"""
        metrics = SuccessMetrics()
        
        # 等级成就度
        level = build.get('level', 85)
        metrics.level_achievement = min(level / 100.0, 1.0)
        
        # 构筑完整度（基于可用数据的完整性）
        completeness_factors = [
            bool(build.get('dps', 0) > 0),
            bool(build.get('life', 0) > 0),
            bool(build.get('skills', [])),
            bool(build.get('items', [])),
            bool(build.get('class', '')),
        ]
        metrics.build_completeness = sum(completeness_factors) / len(completeness_factors)
        
        # 装备质量评估
        items = build.get('items', [])
        if items:
            # 基于物品数量和类型多样性评估
            unique_types = set()
            for item in items:
                if isinstance(item, dict) and item.get('type'):
                    unique_types.add(item['type'])
            
            metrics.gear_quality_score = min(len(unique_types) / 10.0, 1.0)
        
        # 基础流行度分数（基于在列表中的位置）
        metrics.popularity_score = 1.0  # 所有从poe.ninja获取的构筑都有一定的流行度
        
        return metrics
    
    def _determine_build_goal(self, 
                            build: Dict,
                            offensive_stats: OffensiveStats,
                            defensive_stats: DefensiveStats) -> BuildGoal:
        """确定构筑目标"""
        dps = offensive_stats.dps
        ehp = defensive_stats.effective_health_pool()
        
        # 基于DPS和EHP比例判断构筑目标
        if dps > 3000000:  # 高DPS
            if ehp < 6000:  # 低防御
                return BuildGoal.CLEAR_SPEED
            else:
                return BuildGoal.BALANCED
        elif dps > 1000000:  # 中等DPS
            if ehp > 8000:  # 高防御
                return BuildGoal.BOSS_KILLING
            else:
                return BuildGoal.BALANCED
        else:  # 低DPS或无数据
            return BuildGoal.BALANCED
    
    def _assess_data_quality(self, build: Dict) -> DataQuality:
        """评估数据质量"""
        # 检查关键数据字段
        required_fields = ['class', 'level', 'skills', 'dps', 'life']
        missing_fields = 0
        
        for field in required_fields:
            if not build.get(field):
                missing_fields += 1
        
        if missing_fields == 0:
            return DataQuality.HIGH
        elif missing_fields <= 1:
            return DataQuality.MEDIUM
        elif missing_fields <= 2:
            return DataQuality.LOW
        else:
            return DataQuality.INVALID
    
    def _validate_build_data(self, build_data: PoE2BuildData) -> bool:
        """验证构筑数据有效性"""
        # 基础验证
        if not build_data.character_class:
            return False
        
        if build_data.level < 1 or build_data.level > 100:
            return False
        
        # 跳过数据质量为无效的构筑
        if build_data.data_quality == DataQuality.INVALID:
            return False
        
        return True
    
    def _get_fallback_skill_data(self) -> Dict[str, Any]:
        """获取降级技能数据"""
        return {
            'skills': [
                {'name': 'Lightning Arrow', 'type': 'projectile', 'usage_rate': 0.15},
                {'name': 'Explosive Shot', 'type': 'projectile', 'usage_rate': 0.12},
                {'name': 'Glacial Cascade', 'type': 'spell', 'usage_rate': 0.10},
                {'name': 'Bone Spear', 'type': 'minion', 'usage_rate': 0.08},
                {'name': 'Raise Skeleton', 'type': 'minion', 'usage_rate': 0.07}
            ]
        }
    
    async def _make_resilient_request(self,
                                    service_name: str,
                                    url: str,
                                    method: str = 'GET',
                                    **kwargs) -> Optional[Dict[str, Any]]:
        """
        执行弹性HTTP请求
        
        Args:
            service_name: 服务名称 ('poe_ninja', 'poe2_scout', 'poe2db')
            url: 请求URL
            method: HTTP方法
            **kwargs: 额外参数
            
        Returns:
            响应数据或None
        """
        self.collection_stats['total_requests'] += 1
        
        try:
            # 选择弹性服务
            resilient_service = None
            if self.enable_resilience:
                if service_name == 'poe_ninja':
                    resilient_service = self.poe_ninja_service
                elif service_name == 'poe2_scout':
                    resilient_service = self.poe2_scout_service
                elif service_name == 'poe2db':
                    resilient_service = self.poe2db_service
            
            # 定义实际请求函数
            async def make_request():
                async with self.session.request(method, url, **kwargs) as response:
                    response.raise_for_status()
                    return await response.json()
            
            # 使用弹性服务或直接调用
            if resilient_service:
                # 生成缓存键
                cache_key = f"{service_name}_{hash(url + str(sorted(kwargs.items())))}"
                result = resilient_service.call(make_request, cache_key=cache_key)
            else:
                result = await make_request()
            
            self.collection_stats['successful_requests'] += 1
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"[RAG Collector] 请求超时: {url}")
            self.collection_stats['failed_requests'] += 1
            return None
        except ClientError as e:
            logger.warning(f"[RAG Collector] 客户端错误: {url} - {e}")
            self.collection_stats['failed_requests'] += 1
            return None
        except Exception as e:
            logger.error(f"[RAG Collector] 请求异常: {url} - {e}")
            self.collection_stats['failed_requests'] += 1
            return None
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """获取采集统计信息"""
        stats = self.collection_stats.copy()
        
        if stats['collection_start_time'] and stats['collection_end_time']:
            duration = stats['collection_end_time'] - stats['collection_start_time']
            stats['collection_duration_seconds'] = duration.total_seconds()
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health = {
            'collector_status': 'healthy',
            'session_initialized': self.session is not None,
            'services': {}
        }
        
        if self.enable_resilience:
            # 检查各个服务的健康状态
            services = {
                'poe_ninja': self.poe_ninja_service,
                'poe2_scout': self.poe2_scout_service,
                'poe2db': self.poe2db_service
            }
            
            for service_name, service in services.items():
                if service and service.circuit_breaker:
                    health['services'][service_name] = {
                        'circuit_breaker_state': service.circuit_breaker.state.value,
                        'available': service.circuit_breaker.state != CircuitBreakerState.OPEN
                    }
                else:
                    health['services'][service_name] = {
                        'circuit_breaker_state': 'none',
                        'available': True
                    }
        
        return health

# 使用示例和测试函数
async def test_rag_data_collection():
    """测试RAG数据收集功能"""
    async with PoE2RAGDataCollector(max_concurrent_requests=2) as collector:
        
        # 健康检查
        health = await collector.health_check()
        print("=== 健康检查 ===")
        print(json.dumps(health, indent=2, ensure_ascii=False))
        
        # 采集数据
        print("\n=== 开始数据采集 ===")
        rag_data = await collector.collect_comprehensive_build_data(
            league="Standard",
            limit=50,  # 测试时使用较小的数量
            include_prices=False,  # 跳过价格采集以加快速度
            quality_filter=DataQuality.LOW
        )
        
        # 显示结果统计
        print("\n=== 采集结果 ===")
        stats = rag_data.get_stats()
        print(f"总构筑数: {stats['total_builds']}")
        print(f"职业分布: {stats['classes']}")
        print(f"主技能分布: {dict(list(stats['main_skills'].items())[:5])}")  # 显示前5个
        
        # 显示采集统计
        print("\n=== 采集统计 ===")
        collection_stats = collector.get_collection_stats()
        print(json.dumps(collection_stats, default=str, indent=2, ensure_ascii=False))
        
        return rag_data

class PoE2NinjaRAGCollector:
    """
    专门针对poe.ninja/poe2的RAG数据收集器
    
    基于prompt要求实现的专门类，提供更简单直接的API
    """
    
    def __init__(self, 
                 rate_limit_delay: float = 1.0,
                 max_retries: int = 3,
                 timeout: int = 30):
        """
        初始化PoE2Ninja RAG收集器
        
        Args:
            rate_limit_delay: API调用间延迟(秒)
            max_retries: 最大重试次数
            timeout: 请求超时时间(秒)
        """
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = None
        
        # poe.ninja API端点
        self.base_url = "https://poe.ninja/api/data"
        self.poe2_endpoints = {
            'builds': '/poe2/builds',
            'characters': '/poe2/characters',
            'items': '/poe2/items'
        }
        
        logger.info("PoE2NinjaRAGCollector initialized with 'ecosystem citizen' approach")
    
    async def collect_comprehensive_build_data(self, 
                                            league: str = "Standard",
                                            limit: int = 1000) -> Dict[str, Any]:
        """
        采集全面的构筑数据
        
        Args:
            league: 联赛名称
            limit: 采集数量限制
            
        Returns:
            包含构筑数据的字典
        """
        logger.info(f"Starting comprehensive build data collection for league: {league}")
        
        try:
            async with aiohttp.ClientSession(
                timeout=ClientTimeout(total=self.timeout)
            ) as session:
                self.session = session
                
                # 采集各种数据
                popular_builds = await self._fetch_popular_builds(league, limit)
                class_distribution = await self._fetch_class_distribution(league)
                skill_meta = await self._fetch_skill_meta()
                
                # 构建综合数据集
                dataset = await self._build_comprehensive_dataset(
                    popular_builds, class_distribution, skill_meta
                )
                
                return dataset
                
        except Exception as e:
            logger.error(f"Error in comprehensive data collection: {e}")
            raise
    
    async def _fetch_popular_builds(self, league: str, limit: int) -> List[Dict[str, Any]]:
        """
        获取热门构筑数据
        
        Args:
            league: 联赛名称
            limit: 获取数量
            
        Returns:
            构筑数据列表
        """
        logger.info(f"Fetching popular builds for {league}, limit: {limit}")
        
        url = f"{self.base_url}{self.poe2_endpoints['builds']}"
        params = {
            'league': league,
            'limit': limit,
            'sort': 'popularity'
        }
        
        builds_data = await self._make_request(url, params=params)
        
        if builds_data and 'builds' in builds_data:
            builds = builds_data['builds'][:limit]
            logger.info(f"Fetched {len(builds)} popular builds")
            return builds
        
        logger.warning("No builds data received")
        return []
    
    async def _fetch_class_distribution(self, league: str) -> Dict[str, Any]:
        """
        获取职业分布数据
        
        Args:
            league: 联赛名称
            
        Returns:
            职业分布数据
        """
        logger.info(f"Fetching class distribution for {league}")
        
        url = f"{self.base_url}{self.poe2_endpoints['characters']}"
        params = {
            'league': league,
            'type': 'class_distribution'
        }
        
        class_data = await self._make_request(url, params=params)
        
        if class_data:
            logger.info("Class distribution data fetched successfully")
            return class_data
        
        logger.warning("No class distribution data received")
        return {}
    
    async def _fetch_skill_meta(self) -> Dict[str, Any]:
        """
        获取技能流行度数据
        
        Returns:
            技能元数据
        """
        logger.info("Fetching skill meta data")
        
        url = f"{self.base_url}/skills/meta"
        
        skill_meta = await self._make_request(url)
        
        if skill_meta:
            logger.info("Skill meta data fetched successfully")
            return skill_meta
        
        logger.warning("No skill meta data received")
        return {}
    
    async def _build_comprehensive_dataset(self,
                                         popular_builds: List[Dict[str, Any]],
                                         class_distribution: Dict[str, Any],
                                         skill_meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建综合数据集
        
        Args:
            popular_builds: 热门构筑数据
            class_distribution: 职业分布数据  
            skill_meta: 技能元数据
            
        Returns:
            综合数据集
        """
        logger.info("Building comprehensive dataset")
        
        dataset = {
            'timestamp': datetime.now().isoformat(),
            'builds_count': len(popular_builds),
            'builds': [],
            'class_distribution': class_distribution,
            'skill_meta': skill_meta,
            'stats': {
                'total_builds': len(popular_builds),
                'classes': {},
                'main_skills': {},
                'ascendancies': {}
            }
        }
        
        # 处理每个构筑
        for build in popular_builds:
            processed_build = await self._process_build(build, skill_meta)
            if processed_build:
                dataset['builds'].append(processed_build)
                
                # 更新统计信息
                character_class = processed_build.get('character_class')
                if character_class:
                    dataset['stats']['classes'][character_class] = \
                        dataset['stats']['classes'].get(character_class, 0) + 1
                
                main_skill = self._extract_main_skill(processed_build)
                if main_skill:
                    dataset['stats']['main_skills'][main_skill] = \
                        dataset['stats']['main_skills'].get(main_skill, 0) + 1
                
                ascendancy = processed_build.get('ascendancy')
                if ascendancy:
                    dataset['stats']['ascendancies'][ascendancy] = \
                        dataset['stats']['ascendancies'].get(ascendancy, 0) + 1
        
        logger.info(f"Built comprehensive dataset with {len(dataset['builds'])} processed builds")
        return dataset
    
    async def _process_build(self, 
                           build: Dict[str, Any],
                           skill_meta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理单个构筑数据
        
        Args:
            build: 原始构筑数据
            skill_meta: 技能元数据
            
        Returns:
            处理后的构筑数据
        """
        try:
            processed = {
                'character_name': build.get('name', ''),
                'character_class': build.get('class', ''),
                'ascendancy': build.get('ascendancy', ''),
                'level': build.get('level', 0),
                'main_skill': self._extract_main_skill(build),
                'support_gems': self._extract_support_gems(build),
                'weapon_type': self._extract_weapon_type(build),
                'key_items': self._extract_key_items(build),
                'dps': build.get('dps', 0),
                'life': build.get('life', 0),
                'energy_shield': build.get('energy_shield', 0),
                'total_cost': self._calculate_total_cost(build),
                'popularity_rank': build.get('rank', 999),
                'success_metrics': self._calculate_success_metrics(build),
                'timestamp': datetime.now().isoformat()
            }
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing build: {e}")
            return None
    
    def _extract_main_skill(self, build: Dict[str, Any]) -> str:
        """提取主要技能"""
        skills = build.get('skills', [])
        if skills and isinstance(skills, list):
            main_skill = skills[0].get('name', '') if len(skills) > 0 else ''
            return main_skill
        return build.get('mainSkill', '')
    
    def _extract_support_gems(self, build: Dict[str, Any]) -> List[str]:
        """提取辅助宝石"""
        skills = build.get('skills', [])
        supports = []
        
        if skills and isinstance(skills, list):
            for skill in skills:
                skill_supports = skill.get('supports', [])
                if isinstance(skill_supports, list):
                    supports.extend([s.get('name', '') for s in skill_supports])
        
        return list(set(supports))  # 去重
    
    def _extract_weapon_type(self, build: Dict[str, Any]) -> str:
        """提取武器类型"""
        items = build.get('items', {})
        weapon = items.get('weapon', {})
        return weapon.get('baseType', '') or weapon.get('typeLine', '')
    
    def _extract_key_items(self, build: Dict[str, Any]) -> List[str]:
        """提取关键物品"""
        items = build.get('items', {})
        key_items = []
        
        # 检查主要装备槽位
        important_slots = ['weapon', 'helmet', 'bodyArmour', 'gloves', 'boots', 'amulet', 'ring', 'ring2']
        
        for slot in important_slots:
            item = items.get(slot, {})
            if item and item.get('name'):
                key_items.append(item['name'])
        
        return key_items
    
    def _calculate_total_cost(self, build: Dict[str, Any]) -> float:
        """计算构筑总成本"""
        # 简化的成本计算
        items = build.get('items', {})
        total_cost = 0.0
        
        for item in items.values():
            if isinstance(item, dict):
                # 使用物品价值或默认估算
                cost = item.get('chaosValue', 0) or item.get('divineValue', 0) * 150
                total_cost += cost
        
        return total_cost
    
    def _calculate_success_metrics(self, build: Dict[str, Any]) -> Dict[str, float]:
        """计算成功指标"""
        return {
            'popularity_score': max(0, 100 - build.get('rank', 100)) / 100,
            'power_score': min(1.0, (build.get('dps', 0) / 1000000)),  # DPS/100万
            'survivability_score': min(1.0, ((build.get('life', 0) + build.get('energy_shield', 0)) / 10000)),  # 总血量/1万
            'level_score': min(1.0, build.get('level', 0) / 100)
        }
    
    async def _make_request(self, 
                          url: str, 
                          params: Optional[Dict] = None,
                          retries: int = 0) -> Optional[Dict[str, Any]]:
        """
        发送HTTP请求（遵循生态公民原则）
        
        Args:
            url: 请求URL
            params: 请求参数
            retries: 当前重试次数
            
        Returns:
            响应数据或None
        """
        try:
            # 遵循速率限制
            await asyncio.sleep(self.rate_limit_delay)
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                elif response.status == 429:  # Too Many Requests
                    if retries < self.max_retries:
                        wait_time = (2 ** retries) * self.rate_limit_delay
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry {retries + 1}")
                        await asyncio.sleep(wait_time)
                        return await self._make_request(url, params, retries + 1)
                    else:
                        logger.error("Max retries reached for rate limiting")
                        return None
                else:
                    logger.error(f"HTTP {response.status}: {await response.text()}")
                    return None
                    
        except Exception as e:
            if retries < self.max_retries:
                logger.warning(f"Request failed, retrying: {e}")
                await asyncio.sleep(self.rate_limit_delay * (retries + 1))
                return await self._make_request(url, params, retries + 1)
            else:
                logger.error(f"Request failed after {retries} retries: {e}")
                return None


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_rag_data_collection())