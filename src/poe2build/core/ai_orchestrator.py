"""
PoE2 AI协调器 - 整合RAG、PoB2和数据源的核心组件

这个模块是系统的核心协调器，负责：
1. 整合RAG增强的推荐系统
2. 集成PoB2本地计算
3. 协调各种数据源
4. 管理推荐生成流程
5. 提供系统健康检查和状态报告
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple, Callable

from ..models.build import PoE2Build, PoE2BuildGoal, PoE2BuildStats
from ..models.characters import PoE2CharacterClass, PoE2Ascendancy


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SystemComponent(Enum):
    """系统组件枚举"""
    RAG_ENGINE = "rag_engine"
    POB2_LOCAL = "pob2_local"
    POB2_WEB = "pob2_web"
    MARKET_API = "market_api"
    NINJA_SCRAPER = "ninja_scraper"
    DATA_CACHE = "data_cache"


class ComponentStatus(Enum):
    """组件状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass
class ComponentHealth:
    """组件健康状态"""
    component: SystemComponent
    status: ComponentStatus
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    last_check: Optional[float] = None


@dataclass
class UserRequest:
    """用户推荐请求"""
    # 基础需求
    character_class: Optional[PoE2CharacterClass] = None
    ascendancy: Optional[PoE2Ascendancy] = None
    build_goal: Optional[PoE2BuildGoal] = None
    
    # 预算约束
    max_budget: Optional[float] = None
    currency_type: str = "divine"
    
    # 玩法偏好
    preferred_skills: Optional[List[str]] = None
    playstyle: Optional[str] = None  # "aggressive", "defensive", "balanced"
    
    # 技术要求
    min_dps: Optional[float] = None
    min_ehp: Optional[float] = None
    require_resistance_cap: bool = True
    
    # 源偏好
    include_meta_builds: bool = True
    include_budget_builds: bool = True
    max_build_complexity: str = "medium"  # "low", "medium", "high"
    
    # PoB2集成
    generate_pob2_code: bool = True
    validate_with_pob2: bool = True


@dataclass
class RecommendationResult:
    """推荐结果"""
    builds: List[PoE2Build]
    metadata: Dict[str, Any]
    rag_confidence: float
    pob2_validated: bool
    generation_time_ms: float
    used_components: List[SystemComponent]


class PoE2AIOrchestrator:
    """
    PoE2 AI协调器主类
    
    负责整合所有子系统并提供统一的推荐接口
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化AI协调器
        
        Args:
            config: 配置字典，包含各组件的配置信息
        """
        self.config = config or {}
        self._component_health: Dict[SystemComponent, ComponentHealth] = {}
        self._initialized = False
        
        # 组件实例（延迟初始化）
        self._rag_engine = None
        self._pob2_local = None
        self._pob2_web = None
        self._market_api = None
        self._ninja_scraper = None
        self._cache_manager = None
        
        # 性能统计
        self._request_count = 0
        self._total_response_time = 0.0
        self._error_count = 0
        
        logger.info("PoE2AIOrchestrator 已创建，等待初始化...")
    
    async def initialize(self) -> bool:
        """
        异步初始化所有组件
        
        Returns:
            初始化是否成功
        """
        if self._initialized:
            return True
            
        logger.info("开始初始化 PoE2AIOrchestrator...")
        start_time = time.time()
        
        # 初始化各个组件
        success_count = 0
        total_components = len(SystemComponent)
        
        try:
            # 1. 初始化缓存管理器
            success_count += await self._init_cache_manager()
            
            # 2. 初始化数据源
            success_count += await self._init_market_api()
            success_count += await self._init_ninja_scraper()
            
            # 3. 初始化PoB2集成
            success_count += await self._init_pob2_local()
            success_count += await self._init_pob2_web()
            
            # 4. 初始化RAG引擎
            success_count += await self._init_rag_engine()
            
            # 检查初始化成功率
            success_rate = success_count / total_components
            self._initialized = success_rate >= 0.5  # 至少50%组件正常
            
            init_time = (time.time() - start_time) * 1000
            logger.info(f"PoE2AIOrchestrator 初始化完成: {success_count}/{total_components} 组件正常 ({init_time:.2f}ms)")
            
            return self._initialized
            
        except Exception as e:
            logger.error(f"PoE2AIOrchestrator 初始化失败: {e}")
            return False
    
    async def _init_cache_manager(self) -> int:
        """初始化缓存管理器"""
        try:
            # 这里应该导入实际的缓存管理器
            # from ..utils.cache import CacheManager
            # self._cache_manager = CacheManager(self.config.get('cache', {}))
            
            # 临时Mock实现
            self._cache_manager = MockCacheManager()
            
            self._component_health[SystemComponent.DATA_CACHE] = ComponentHealth(
                component=SystemComponent.DATA_CACHE,
                status=ComponentStatus.HEALTHY,
                response_time_ms=1.0,
                last_check=time.time()
            )
            logger.info("✓ 缓存管理器初始化成功")
            return 1
        except Exception as e:
            self._component_health[SystemComponent.DATA_CACHE] = ComponentHealth(
                component=SystemComponent.DATA_CACHE,
                status=ComponentStatus.ERROR,
                error_message=str(e),
                last_check=time.time()
            )
            logger.warning(f"✗ 缓存管理器初始化失败: {e}")
            return 0
    
    async def _init_market_api(self) -> int:
        """初始化市场API"""
        try:
            # 这里应该导入实际的市场API
            # from ..data_sources.poe2_scout import PoE2ScoutAPI
            # self._market_api = PoE2ScoutAPI(self.config.get('market_api', {}))
            
            # 临时Mock实现
            self._market_api = MockMarketAPI()
            
            self._component_health[SystemComponent.MARKET_API] = ComponentHealth(
                component=SystemComponent.MARKET_API,
                status=ComponentStatus.HEALTHY,
                response_time_ms=50.0,
                last_check=time.time()
            )
            logger.info("✓ 市场API初始化成功")
            return 1
        except Exception as e:
            self._component_health[SystemComponent.MARKET_API] = ComponentHealth(
                component=SystemComponent.MARKET_API,
                status=ComponentStatus.ERROR,
                error_message=str(e),
                last_check=time.time()
            )
            logger.warning(f"✗ 市场API初始化失败: {e}")
            return 0
    
    async def _init_ninja_scraper(self) -> int:
        """初始化ninja爬虫"""
        try:
            # 这里应该导入实际的ninja爬虫
            # from ..data_sources.ninja_scraper import NinjaScraper
            # self._ninja_scraper = NinjaScraper(self.config.get('ninja', {}))
            
            # 临时Mock实现
            self._ninja_scraper = MockNinjaScraper()
            
            self._component_health[SystemComponent.NINJA_SCRAPER] = ComponentHealth(
                component=SystemComponent.NINJA_SCRAPER,
                status=ComponentStatus.HEALTHY,
                response_time_ms=100.0,
                last_check=time.time()
            )
            logger.info("✓ Ninja爬虫初始化成功")
            return 1
        except Exception as e:
            self._component_health[SystemComponent.NINJA_SCRAPER] = ComponentHealth(
                component=SystemComponent.NINJA_SCRAPER,
                status=ComponentStatus.ERROR,
                error_message=str(e),
                last_check=time.time()
            )
            logger.warning(f"✗ Ninja爬虫初始化失败: {e}")
            return 0
    
    async def _init_pob2_local(self) -> int:
        """初始化PoB2本地客户端"""
        try:
            # 这里应该导入实际的PoB2客户端
            # from ..pob2.local_client import PoB2LocalClient
            # self._pob2_local = PoB2LocalClient(self.config.get('pob2_local', {}))
            
            # 临时Mock实现
            self._pob2_local = MockPoB2Local()
            
            is_available = await self._pob2_local.is_available()
            status = ComponentStatus.HEALTHY if is_available else ComponentStatus.UNAVAILABLE
            
            self._component_health[SystemComponent.POB2_LOCAL] = ComponentHealth(
                component=SystemComponent.POB2_LOCAL,
                status=status,
                response_time_ms=200.0,
                last_check=time.time()
            )
            
            if is_available:
                logger.info("✓ PoB2本地客户端初始化成功")
                return 1
            else:
                logger.info("- PoB2本地客户端不可用，将使用Web版本")
                return 0
        except Exception as e:
            self._component_health[SystemComponent.POB2_LOCAL] = ComponentHealth(
                component=SystemComponent.POB2_LOCAL,
                status=ComponentStatus.ERROR,
                error_message=str(e),
                last_check=time.time()
            )
            logger.warning(f"✗ PoB2本地客户端初始化失败: {e}")
            return 0
    
    async def _init_pob2_web(self) -> int:
        """初始化PoB2 Web版本"""
        try:
            # 这里应该导入实际的PoB2 Web客户端
            # from ..pob2.web_client import PoB2WebClient
            # self._pob2_web = PoB2WebClient(self.config.get('pob2_web', {}))
            
            # 临时Mock实现
            self._pob2_web = MockPoB2Web()
            
            self._component_health[SystemComponent.POB2_WEB] = ComponentHealth(
                component=SystemComponent.POB2_WEB,
                status=ComponentStatus.HEALTHY,
                response_time_ms=300.0,
                last_check=time.time()
            )
            logger.info("✓ PoB2 Web版本初始化成功")
            return 1
        except Exception as e:
            self._component_health[SystemComponent.POB2_WEB] = ComponentHealth(
                component=SystemComponent.POB2_WEB,
                status=ComponentStatus.ERROR,
                error_message=str(e),
                last_check=time.time()
            )
            logger.warning(f"✗ PoB2 Web版本初始化失败: {e}")
            return 0
    
    async def _init_rag_engine(self) -> int:
        """初始化RAG引擎"""
        try:
            # 这里应该导入实际的RAG引擎
            # from ..rag.ai_enhanced import RAGEnhancedEngine
            # self._rag_engine = RAGEnhancedEngine(self.config.get('rag', {}))
            
            # 临时Mock实现
            self._rag_engine = MockRAGEngine()
            
            self._component_health[SystemComponent.RAG_ENGINE] = ComponentHealth(
                component=SystemComponent.RAG_ENGINE,
                status=ComponentStatus.HEALTHY,
                response_time_ms=150.0,
                last_check=time.time()
            )
            logger.info("✓ RAG引擎初始化成功")
            return 1
        except Exception as e:
            self._component_health[SystemComponent.RAG_ENGINE] = ComponentHealth(
                component=SystemComponent.RAG_ENGINE,
                status=ComponentStatus.ERROR,
                error_message=str(e),
                last_check=time.time()
            )
            logger.warning(f"✗ RAG引擎初始化失败: {e}")
            return 0
    
    async def generate_build_recommendations(self, request: UserRequest) -> RecommendationResult:
        """
        生成构筑推荐
        
        Args:
            request: 用户请求
            
        Returns:
            推荐结果
        """
        if not self._initialized:
            raise RuntimeError("Orchestrator not initialized. Call initialize() first.")
        
        start_time = time.time()
        self._request_count += 1
        used_components = []
        
        try:
            logger.info(f"开始生成构筑推荐: {request.character_class}, 目标: {request.build_goal}")
            
            # 第1阶段: RAG增强的初始推荐生成
            rag_recommendations = []
            rag_confidence = 0.0
            
            if self._is_component_healthy(SystemComponent.RAG_ENGINE):
                used_components.append(SystemComponent.RAG_ENGINE)
                rag_recommendations, rag_confidence = await self._generate_rag_recommendations(request)
                logger.info(f"RAG推荐生成: {len(rag_recommendations)} 个构筑, 置信度: {rag_confidence:.3f}")
            
            # 第2阶段: 市场数据整合
            market_enhanced_builds = rag_recommendations
            if self._is_component_healthy(SystemComponent.MARKET_API):
                used_components.append(SystemComponent.MARKET_API)
                market_enhanced_builds = await self._enhance_with_market_data(
                    rag_recommendations, request
                )
                logger.info(f"市场数据整合完成: {len(market_enhanced_builds)} 个构筑")
            
            # 第3阶段: PoB2计算验证
            validated_builds = market_enhanced_builds
            pob2_validated = False
            
            if request.validate_with_pob2:
                pob2_client = self._get_available_pob2_client()
                if pob2_client:
                    used_components.append(
                        SystemComponent.POB2_LOCAL if pob2_client == self._pob2_local
                        else SystemComponent.POB2_WEB
                    )
                    validated_builds = await self._validate_with_pob2(
                        market_enhanced_builds, pob2_client, request
                    )
                    pob2_validated = True
                    logger.info(f"PoB2验证完成: {len(validated_builds)} 个构筑通过验证")
            
            # 第4阶段: 最终排序和筛选
            final_builds = await self._finalize_recommendations(validated_builds, request)
            
            # 生成元数据
            generation_time = (time.time() - start_time) * 1000
            self._total_response_time += generation_time
            
            metadata = {
                'request_id': f"req_{int(time.time())}_{self._request_count}",
                'generation_timestamp': time.time(),
                'stages_completed': [
                    'rag_generation',
                    'market_integration',
                    'pob2_validation' if pob2_validated else 'pob2_skipped',
                    'final_ranking'
                ],
                'component_health': {
                    comp.value: self._component_health[comp].status.value
                    for comp in used_components
                },
                'performance_metrics': {
                    'generation_time_ms': generation_time,
                    'builds_generated': len(final_builds),
                    'success_rate': 1.0 if final_builds else 0.0
                }
            }
            
            result = RecommendationResult(
                builds=final_builds,
                metadata=metadata,
                rag_confidence=rag_confidence,
                pob2_validated=pob2_validated,
                generation_time_ms=generation_time,
                used_components=used_components
            )
            
            logger.info(f"构筑推荐生成完成: {len(final_builds)} 个推荐, 耗时 {generation_time:.2f}ms")
            return result
            
        except Exception as e:
            self._error_count += 1
            logger.error(f"构筑推荐生成失败: {e}")
            
            # 返回降级结果
            fallback_builds = await self._generate_fallback_recommendations(request)
            generation_time = (time.time() - start_time) * 1000
            
            return RecommendationResult(
                builds=fallback_builds,
                metadata={
                    'error': str(e),
                    'fallback_mode': True,
                    'generation_time_ms': generation_time
                },
                rag_confidence=0.0,
                pob2_validated=False,
                generation_time_ms=generation_time,
                used_components=used_components
            )
    
    async def _generate_rag_recommendations(self, request: UserRequest) -> Tuple[List[PoE2Build], float]:
        """使用RAG引擎生成推荐"""
        try:
            # 构建RAG查询
            rag_query = {
                'character_class': request.character_class.value if request.character_class else None,
                'ascendancy': request.ascendancy.value if request.ascendancy else None,
                'build_goal': request.build_goal.value if request.build_goal else None,
                'max_budget': request.max_budget,
                'preferred_skills': request.preferred_skills,
                'playstyle': request.playstyle
            }
            
            # 调用RAG引擎
            recommendations = await self._rag_engine.generate_recommendations(rag_query)
            
            builds = []
            total_confidence = 0.0
            
            for rec in recommendations:
                build = PoE2Build(
                    name=rec.get('name', 'RAG Generated Build'),
                    character_class=request.character_class or PoE2CharacterClass.WITCH,
                    level=rec.get('level', 90),
                    ascendancy=request.ascendancy,
                    stats=PoE2BuildStats(
                        total_dps=rec.get('estimated_dps', 500000),
                        effective_health_pool=rec.get('estimated_ehp', 6000),
                        fire_resistance=75,
                        cold_resistance=75,
                        lightning_resistance=75,
                        chaos_resistance=-30
                    ),
                    estimated_cost=rec.get('estimated_cost', 10.0),
                    goal=request.build_goal,
                    main_skill_gem=rec.get('main_skill'),
                    support_gems=rec.get('support_gems', []),
                    notes=f"RAG confidence: {rec.get('confidence', 0.5):.3f}"
                )
                builds.append(build)
                total_confidence += rec.get('confidence', 0.5)
            
            avg_confidence = total_confidence / len(recommendations) if recommendations else 0.0
            return builds, avg_confidence
            
        except Exception as e:
            logger.error(f"RAG推荐生成失败: {e}")
            return [], 0.0
    
    async def _enhance_with_market_data(self, builds: List[PoE2Build], request: UserRequest) -> List[PoE2Build]:
        """使用市场数据增强构筑信息"""
        try:
            enhanced_builds = []
            
            for build in builds:
                # 获取关键物品价格
                if build.key_items:
                    total_cost = 0.0
                    for item_name in build.key_items:
                        item_price = await self._market_api.get_item_price(item_name)
                        if item_price:
                            total_cost += item_price.get('median_price', 0)
                    
                    if total_cost > 0:
                        build.estimated_cost = total_cost
                
                # 检查预算约束
                if request.max_budget and build.estimated_cost:
                    if build.estimated_cost <= request.max_budget:
                        enhanced_builds.append(build)
                else:
                    enhanced_builds.append(build)
            
            return enhanced_builds
            
        except Exception as e:
            logger.error(f"市场数据增强失败: {e}")
            return builds
    
    async def _validate_with_pob2(self, builds: List[PoE2Build], pob2_client, request: UserRequest) -> List[PoE2Build]:
        """使用PoB2验证构筑"""
        try:
            validated_builds = []
            
            for build in builds:
                if request.generate_pob2_code:
                    # 生成PoB2导入代码
                    pob2_code = await pob2_client.generate_build_code(build)
                    if pob2_code:
                        build.pob2_code = pob2_code
                
                # 计算统计数据
                calculated_stats = await pob2_client.calculate_build_stats(build)
                if calculated_stats:
                    build.stats = PoE2BuildStats(
                        total_dps=calculated_stats.get('total_dps', build.stats.total_dps if build.stats else 0),
                        effective_health_pool=calculated_stats.get('ehp', build.stats.effective_health_pool if build.stats else 0),
                        fire_resistance=calculated_stats.get('fire_res', 75),
                        cold_resistance=calculated_stats.get('cold_res', 75),
                        lightning_resistance=calculated_stats.get('lightning_res', 75),
                        chaos_resistance=calculated_stats.get('chaos_res', -30)
                    )
                
                # 验证构筑是否满足用户要求
                if self._validate_build_requirements(build, request):
                    validated_builds.append(build)
            
            return validated_builds
            
        except Exception as e:
            logger.error(f"PoB2验证失败: {e}")
            return builds
    
    def _validate_build_requirements(self, build: PoE2Build, request: UserRequest) -> bool:
        """验证构筑是否满足用户要求"""
        if not build.stats:
            return False
        
        # 检查最低DPS要求
        if request.min_dps and build.stats.total_dps < request.min_dps:
            return False
        
        # 检查最低EHP要求
        if request.min_ehp and build.stats.effective_health_pool < request.min_ehp:
            return False
        
        # 检查抗性要求
        if request.require_resistance_cap and not build.stats.is_resistance_capped():
            return False
        
        return True
    
    async def _finalize_recommendations(self, builds: List[PoE2Build], request: UserRequest) -> List[PoE2Build]:
        """最终排序和筛选推荐"""
        try:
            if not builds:
                return []
            
            # 根据目标排序
            if request.build_goal == PoE2BuildGoal.BOSS_KILLING:
                builds.sort(key=lambda b: b.stats.total_dps if b.stats else 0, reverse=True)
            elif request.build_goal == PoE2BuildGoal.CLEAR_SPEED:
                builds.sort(key=lambda b: (b.stats.movement_speed if b.stats else 0, 
                                         b.stats.total_dps if b.stats else 0), reverse=True)
            elif request.build_goal == PoE2BuildGoal.BUDGET_FRIENDLY:
                builds.sort(key=lambda b: b.estimated_cost if b.estimated_cost else float('inf'))
            else:
                # 默认按综合评分排序
                builds.sort(key=lambda b: self._calculate_build_score(b, request), reverse=True)
            
            # 限制返回数量
            max_results = self.config.get('max_recommendations', 10)
            return builds[:max_results]
            
        except Exception as e:
            logger.error(f"最终排序失败: {e}")
            return builds[:10]  # 至少返回前10个
    
    def _calculate_build_score(self, build: PoE2Build, request: UserRequest) -> float:
        """计算构筑综合评分"""
        score = 0.0
        
        if not build.stats:
            return score
        
        # DPS权重
        dps_score = min(build.stats.total_dps / 1000000, 1.0)  # 标准化到0-1
        score += dps_score * 0.4
        
        # 生存性权重
        ehp_score = min(build.stats.effective_health_pool / 10000, 1.0)
        score += ehp_score * 0.3
        
        # 抗性权重
        res_score = 1.0 if build.stats.is_resistance_capped() else 0.5
        score += res_score * 0.2
        
        # 成本权重（成本越低分数越高）
        if build.estimated_cost and request.max_budget:
            cost_score = max(0, (request.max_budget - build.estimated_cost) / request.max_budget)
            score += cost_score * 0.1
        
        return score
    
    async def _generate_fallback_recommendations(self, request: UserRequest) -> List[PoE2Build]:
        """生成降级推荐（当主系统失败时）"""
        try:
            logger.info("生成降级推荐...")
            
            # 基础模板构筑
            fallback_build = PoE2Build(
                name=f"Fallback {request.character_class.value if request.character_class else 'Generic'} Build",
                character_class=request.character_class or PoE2CharacterClass.WITCH,
                level=85,
                ascendancy=request.ascendancy,
                stats=PoE2BuildStats(
                    total_dps=300000,
                    effective_health_pool=5000,
                    fire_resistance=75,
                    cold_resistance=75,
                    lightning_resistance=75,
                    chaos_resistance=-30
                ),
                estimated_cost=5.0,
                goal=request.build_goal or PoE2BuildGoal.ENDGAME_CONTENT,
                main_skill_gem="Fallback Skill",
                notes="This is a fallback recommendation generated when the main system is unavailable."
            )
            
            return [fallback_build]
            
        except Exception as e:
            logger.error(f"降级推荐生成失败: {e}")
            return []
    
    def _get_available_pob2_client(self):
        """获取可用的PoB2客户端"""
        if self._is_component_healthy(SystemComponent.POB2_LOCAL):
            return self._pob2_local
        elif self._is_component_healthy(SystemComponent.POB2_WEB):
            return self._pob2_web
        return None
    
    def _is_component_healthy(self, component: SystemComponent) -> bool:
        """检查组件是否健康"""
        health = self._component_health.get(component)
        return health and health.status == ComponentStatus.HEALTHY
    
    async def health_check(self) -> Dict[str, Any]:
        """执行系统健康检查"""
        logger.info("执行系统健康检查...")
        
        health_report = {
            'timestamp': time.time(),
            'overall_status': 'healthy',
            'components': {},
            'performance': {
                'total_requests': self._request_count,
                'error_count': self._error_count,
                'average_response_time_ms': (
                    self._total_response_time / self._request_count 
                    if self._request_count > 0 else 0
                ),
                'error_rate': self._error_count / max(self._request_count, 1)
            }
        }
        
        # 检查各组件状态
        unhealthy_count = 0
        for component, health in self._component_health.items():
            component_info = {
                'status': health.status.value,
                'response_time_ms': health.response_time_ms,
                'last_check': health.last_check,
                'error_message': health.error_message
            }
            
            health_report['components'][component.value] = component_info
            
            if health.status != ComponentStatus.HEALTHY:
                unhealthy_count += 1
        
        # 确定整体状态
        total_components = len(self._component_health)
        if unhealthy_count == 0:
            health_report['overall_status'] = 'healthy'
        elif unhealthy_count < total_components / 2:
            health_report['overall_status'] = 'degraded'
        else:
            health_report['overall_status'] = 'unhealthy'
        
        logger.info(f"健康检查完成: {health_report['overall_status']}, {total_components - unhealthy_count}/{total_components} 组件正常")
        
        return health_report
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        return {
            'initialized': self._initialized,
            'request_count': self._request_count,
            'error_count': self._error_count,
            'success_rate': (self._request_count - self._error_count) / max(self._request_count, 1),
            'average_response_time_ms': (
                self._total_response_time / self._request_count 
                if self._request_count > 0 else 0
            ),
            'component_count': len(self._component_health),
            'healthy_components': sum(
                1 for h in self._component_health.values() 
                if h.status == ComponentStatus.HEALTHY
            )
        }


# Mock组件实现（用于测试）
class MockCacheManager:
    async def get(self, key: str):
        return None
    
    async def set(self, key: str, value: Any):
        pass


class MockMarketAPI:
    async def get_item_price(self, item_name: str):
        return {'median_price': 2.5, 'currency': 'divine'}


class MockNinjaScraper:
    async def get_meta_builds(self, character_class: str):
        return []


class MockPoB2Local:
    async def is_available(self):
        return True
    
    async def generate_build_code(self, build: PoE2Build):
        return f"mock_pob2_code_{build.name.replace(' ', '_')}"
    
    async def calculate_build_stats(self, build: PoE2Build):
        return {
            'total_dps': 750000,
            'ehp': 8500,
            'fire_res': 78,
            'cold_res': 76,
            'lightning_res': 77,
            'chaos_res': -25
        }


class MockPoB2Web:
    async def generate_build_code(self, build: PoE2Build):
        return f"mock_web_pob2_code_{build.name.replace(' ', '_')}"
    
    async def calculate_build_stats(self, build: PoE2Build):
        return {
            'total_dps': 650000,
            'ehp': 7800,
            'fire_res': 75,
            'cold_res': 75,
            'lightning_res': 75,
            'chaos_res': -30
        }


class MockRAGEngine:
    async def generate_recommendations(self, query: Dict[str, Any]):
        character_class = query.get('character_class', 'Witch')
        build_goal = query.get('build_goal', 'endgame_content')
        
        return [
            {
                'name': f"RAG {character_class} Build 1",
                'level': 92,
                'estimated_dps': 850000,
                'estimated_ehp': 7500,
                'estimated_cost': 12.0,
                'main_skill': f"{character_class} Main Skill",
                'support_gems': ['Support 1', 'Support 2', 'Support 3'],
                'confidence': 0.85
            },
            {
                'name': f"RAG {character_class} Build 2",
                'level': 88,
                'estimated_dps': 620000,
                'estimated_ehp': 9200,
                'estimated_cost': 8.5,
                'main_skill': f"{character_class} Alternative Skill",
                'support_gems': ['Support A', 'Support B', 'Support C'],
                'confidence': 0.78
            }
        ]