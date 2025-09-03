"""
RAG-PoB2高度集成推荐系统 - 终极构建推荐引擎

这是将RAG训练、四大数据源集成与PoB2完美融合的核心推荐系统。
提供从数据收集、AI分析、推荐生成到PoB2导入的全流程服务。

核心特性:
✨ RAG增强的智能推荐算法
🎯 四大数据源实时集成 (PoE2Scout + PoE Ninja + PoB2 + PoE2DB)
🔧 自动PoB2路径检测与验证
📊 构建数据到PoB2导入代码的无缝转换
🚀 高性能缓存与并行处理
🛡️ 完整的错误处理与降级策略
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json

# 核心模块导入
import sys
sys.path.insert(0, str(Path(__file__).parent / "core_ai_engine/src"))

from poe2build.rag.recommendation import (
    PoE2RecommendationEngine, AlgorithmType, RecommendationScore, 
    UserProfile, OptimizationGoal
)
from poe2build.rag.ai_engine import RecommendationContext, AIRecommendation
from poe2build.rag.knowledge_base import PoE2KnowledgeBase
from poe2build.rag.similarity_engine import PoE2SimilarityEngine, SearchResult
from poe2build.rag.four_sources_integration import FourSourcesIntegrator
from poe2build.pob2.rag_pob2_adapter import RAGPoB2Adapter, PoB2ValidationResult
from poe2build.pob2.local_client import PoB2LocalClient
from poe2build.pob2.path_detector import PoB2PathDetector
from poe2build.models.characters import PoE2CharacterClass, PoE2Ascendancy
from poe2build.models.build import PoE2BuildGoal

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class IntegratedRecommendationRequest:
    """集成推荐请求"""
    # 基础用户偏好
    character_class: str
    ascendancy: Optional[str] = None
    build_goal: str = "endgame_content"
    budget_range: Tuple[float, float] = (0, 50)
    skill_level: str = "intermediate"  # beginner, intermediate, advanced
    
    # 构建偏好
    preferred_skills: List[str] = field(default_factory=list)
    playstyle: str = "balanced"  # aggressive, defensive, balanced
    content_focus: str = "mapping"  # mapping, bossing, delving, pvp
    
    # RAG配置
    use_rag_enhancement: bool = True
    rag_confidence_threshold: float = 0.7
    algorithm_type: AlgorithmType = AlgorithmType.HYBRID
    
    # PoB2配置
    generate_pob2_code: bool = True
    validate_with_pob2: bool = True
    pob2_auto_detect: bool = True
    
    # 输出配置
    max_recommendations: int = 10
    include_alternatives: bool = True
    detailed_analysis: bool = True

@dataclass
class IntegratedRecommendationResult:
    """集成推荐结果"""
    # 推荐构建
    primary_recommendations: List[Tuple[SearchResult, RecommendationScore, PoB2ValidationResult]]
    alternative_recommendations: List[Tuple[SearchResult, RecommendationScore, PoB2ValidationResult]] = field(default_factory=list)
    
    # 系统状态
    processing_time_ms: float = 0.0
    data_sources_status: Dict[str, str] = field(default_factory=dict)
    pob2_status: Dict[str, Any] = field(default_factory=dict)
    
    # RAG分析
    rag_confidence: float = 0.0
    knowledge_base_size: int = 0
    similarity_matches: int = 0
    
    # 统计数据
    total_candidates: int = 0
    successful_conversions: int = 0
    average_compatibility: float = 0.0
    
    # 元数据
    request_id: str = ""
    generation_timestamp: float = field(default_factory=time.time)
    
class RAGPoB2IntegratedRecommender:
    """RAG-PoB2高度集成推荐系统
    
    这是整个系统的核心协调器，整合了所有子系统：
    - 四大数据源实时集成
    - RAG增强的智能推荐
    - PoB2自动检测与验证
    - 构建代码生成与转换
    """
    
    def __init__(self):
        """初始化集成推荐系统"""
        self.logger = logger
        self.initialized = False
        
        # 核心组件
        self.four_sources = None
        self.knowledge_base = None
        self.similarity_engine = None
        self.recommendation_engine = None
        self.pob2_client = None
        self.pob2_adapter = None
        
        # 系统状态
        self.system_status = {}
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'average_response_time': 0.0,
            'cache_hit_rate': 0.0
        }
        
        # 缓存
        self.recommendation_cache = {}
        self.pob2_validation_cache = {}
        
        logger.info("RAG-PoB2集成推荐系统创建完成")
    
    async def initialize(self) -> bool:
        """异步初始化所有系统组件"""
        logger.info("初始化RAG-PoB2集成推荐系统...")
        
        try:
            # 1. 初始化四大数据源集成器
            logger.info("🔄 初始化四大数据源集成器...")
            self.four_sources = FourSourcesIntegrator()
            await self.four_sources.initialize()
            
            # 2. 初始化知识库
            logger.info("🧠 初始化RAG知识库...")
            self.knowledge_base = PoE2KnowledgeBase()
            await self.knowledge_base.initialize()
            
            # 3. 初始化相似度引擎
            logger.info("🔍 初始化相似度搜索引擎...")
            self.similarity_engine = PoE2SimilarityEngine(self.knowledge_base)
            
            # 4. 初始化推荐引擎
            logger.info("🎯 初始化智能推荐引擎...")
            self.recommendation_engine = PoE2RecommendationEngine(self.knowledge_base)
            
            # 5. 初始化PoB2组件
            logger.info("🔧 初始化PoB2集成组件...")
            await self._initialize_pob2_components()
            
            # 6. 系统健康检查
            logger.info("🏥 执行系统健康检查...")
            health_status = await self._perform_health_check()
            
            if health_status['overall_healthy']:
                self.initialized = True
                logger.info("✅ RAG-PoB2集成推荐系统初始化成功!")
                return True
            else:
                logger.warning("⚠️ 系统初始化完成但存在健康问题")
                logger.warning(f"健康状态: {health_status}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 系统初始化失败: {e}")
            return False
    
    async def _initialize_pob2_components(self):
        """初始化PoB2相关组件"""
        # 检测PoB2安装路径
        pob2_path = PoB2PathDetector.detect()
        
        if pob2_path:
            logger.info(f"✅ 检测到PoB2安装路径: {pob2_path}")
            self.pob2_client = PoB2LocalClient(installation_path=Path(pob2_path))
            
            # 验证PoB2可用性
            if await self.pob2_client.is_available_async():
                logger.info("✅ PoB2本地客户端可用")
                self.system_status['pob2_local'] = 'available'
            else:
                logger.warning("⚠️ PoB2本地客户端不可用，将使用Web回退")
                self.system_status['pob2_local'] = 'unavailable'
        else:
            logger.warning("⚠️ 未检测到PoB2安装，将使用Web模式")
            self.pob2_client = PoB2LocalClient()  # Web回退模式
            self.system_status['pob2_local'] = 'not_found'
        
        # 创建RAG-PoB2适配器
        self.pob2_adapter = RAGPoB2Adapter(self.pob2_client)
        logger.info("✅ RAG-PoB2适配器创建完成")
    
    async def _perform_health_check(self) -> Dict[str, Any]:
        """执行系统健康检查"""
        health_status = {
            'four_sources': False,
            'knowledge_base': False,
            'similarity_engine': False,
            'recommendation_engine': False,
            'pob2_components': False,
            'overall_healthy': False
        }
        
        try:
            # 检查四大数据源
            if self.four_sources:
                sources_status = await self.four_sources.health_check()
                health_status['four_sources'] = sources_status.get('overall_health', 'unhealthy') != 'unhealthy'
            
            # 检查知识库
            if self.knowledge_base:
                kb_stats = self.knowledge_base.get_statistics()
                health_status['knowledge_base'] = kb_stats.get('total_builds', 0) > 0
            
            # 检查其他组件
            health_status['similarity_engine'] = self.similarity_engine is not None
            health_status['recommendation_engine'] = self.recommendation_engine is not None
            health_status['pob2_components'] = self.pob2_adapter is not None
            
            # 计算总体健康状态
            healthy_components = sum(health_status[key] for key in health_status if key != 'overall_healthy')
            health_status['overall_healthy'] = healthy_components >= 3  # 至少3个组件健康
            
            self.system_status.update(health_status)
            return health_status
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return health_status
    
    async def generate_integrated_recommendations(self, 
                                                request: IntegratedRecommendationRequest) -> IntegratedRecommendationResult:
        """生成集成推荐结果
        
        这是系统的核心方法，整合所有功能提供完整的推荐服务。
        """
        if not self.initialized:
            raise RuntimeError("系统尚未初始化，请先调用initialize()")
        
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000)}"
        
        logger.info(f"🚀 开始生成集成推荐 [ID: {request_id}]")
        logger.info(f"请求参数: {request.character_class} {request.build_goal}, 预算: {request.budget_range}")
        
        try:
            # 更新性能指标
            self.performance_metrics['total_requests'] += 1
            
            # 1. 创建推荐上下文
            context = self._create_recommendation_context(request)
            
            # 2. 执行RAG相似度搜索
            logger.info("🔍 执行RAG增强的相似度搜索...")
            search_results = await self._perform_rag_search(context, request)
            
            # 3. 应用智能推荐算法
            logger.info("🎯 应用智能推荐算法...")
            scored_recommendations = await self._apply_recommendation_algorithms(
                search_results, context, request
            )
            
            # 4. 转换为PoB2格式并验证
            logger.info("🔧 转换为PoB2格式并验证...")
            pob2_results = await self._convert_and_validate_pob2(
                scored_recommendations, request
            )
            
            # 5. 构建最终结果
            result = self._build_integrated_result(
                pob2_results, search_results, request_id, start_time
            )
            
            # 6. 更新缓存和指标
            await self._update_caches_and_metrics(result, request)
            
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"✅ 集成推荐生成完成 [ID: {request_id}] - {processing_time:.2f}ms")
            logger.info(f"主推荐: {len(result.primary_recommendations)}, 备选: {len(result.alternative_recommendations)}")
            
            self.performance_metrics['successful_requests'] += 1
            return result
            
        except Exception as e:
            logger.error(f"❌ 集成推荐生成失败 [ID: {request_id}]: {e}")
            # 返回错误结果
            return IntegratedRecommendationResult(
                primary_recommendations=[],
                alternative_recommendations=[],
                request_id=request_id,
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    def _create_recommendation_context(self, request: IntegratedRecommendationRequest) -> RecommendationContext:
        """创建推荐上下文"""
        return RecommendationContext(
            user_preferences={
                'character_class': request.character_class,
                'ascendancy': request.ascendancy,
                'build_goal': request.build_goal,
                'preferred_skills': request.preferred_skills,
                'budget_min': request.budget_range[0],
                'budget_max': request.budget_range[1]
            },
            skill_level=request.skill_level,
            content_focus=request.content_focus,
            budget_constraints=request.budget_range,
            playstyle_preference=request.playstyle,
            algorithm_preference=request.algorithm_type.value
        )
    
    async def _perform_rag_search(self, 
                                context: RecommendationContext, 
                                request: IntegratedRecommendationRequest) -> List[SearchResult]:
        """执行RAG增强的相似度搜索"""
        
        # 构建查询
        query = {
            'character_class': request.character_class,
            'build_goal': request.build_goal,
            'budget_range': request.budget_range,
            'preferred_skills': request.preferred_skills
        }
        
        # 执行相似度搜索
        search_results = await self.similarity_engine.search_similar_builds_async(
            query=query,
            top_k=request.max_recommendations * 3,  # 获取更多候选以便筛选
            confidence_threshold=request.rag_confidence_threshold
        )
        
        logger.info(f"RAG搜索找到 {len(search_results)} 个候选构建")
        return search_results
    
    async def _apply_recommendation_algorithms(self, 
                                             search_results: List[SearchResult],
                                             context: RecommendationContext,
                                             request: IntegratedRecommendationRequest) -> List[Tuple[SearchResult, RecommendationScore]]:
        """应用智能推荐算法"""
        
        # 使用指定的推荐算法
        recommendations = self.recommendation_engine.recommend_builds(
            user_context=context,
            candidates=search_results,
            algorithm=request.algorithm_type,
            max_recommendations=request.max_recommendations
        )
        
        logger.info(f"推荐算法产生 {len(recommendations)} 个评分结果")
        return recommendations
    
    async def _convert_and_validate_pob2(self, 
                                       scored_recommendations: List[Tuple[SearchResult, RecommendationScore]],
                                       request: IntegratedRecommendationRequest) -> List[Tuple[SearchResult, RecommendationScore, PoB2ValidationResult]]:
        """转换为PoB2格式并验证"""
        pob2_results = []
        
        for search_result, rec_score in scored_recommendations:
            try:
                # 转换为PoB2格式
                validation_result = self.pob2_adapter.convert_rag_recommendation_to_pob2(
                    search_result
                )
                
                # 只保留有效的转换结果
                if validation_result.is_valid or not request.validate_with_pob2:
                    pob2_results.append((search_result, rec_score, validation_result))
                else:
                    logger.warning(f"构建 {search_result.build_hash} PoB2验证失败")
                    
            except Exception as e:
                logger.error(f"PoB2转换失败 {search_result.build_hash}: {e}")
                continue
        
        logger.info(f"PoB2转换完成: {len(pob2_results)}/{len(scored_recommendations)} 成功")
        return pob2_results
    
    def _build_integrated_result(self, 
                               pob2_results: List[Tuple[SearchResult, RecommendationScore, PoB2ValidationResult]],
                               search_results: List[SearchResult],
                               request_id: str,
                               start_time: float) -> IntegratedRecommendationResult:
        """构建最终的集成结果"""
        
        processing_time = (time.time() - start_time) * 1000
        
        # 分离主推荐和备选推荐
        primary_count = min(5, len(pob2_results))
        primary_recommendations = pob2_results[:primary_count]
        alternative_recommendations = pob2_results[primary_count:]
        
        # 计算统计信息
        successful_conversions = len([r for _, _, validation in pob2_results if validation.is_valid])
        avg_compatibility = 0.0
        if pob2_results:
            avg_compatibility = sum(validation.compatibility_score for _, _, validation in pob2_results) / len(pob2_results)
        
        # RAG分析
        rag_confidence = 0.0
        if pob2_results:
            rag_confidence = sum(rec_score.total_score for _, rec_score, _ in pob2_results) / len(pob2_results)
        
        return IntegratedRecommendationResult(
            primary_recommendations=primary_recommendations,
            alternative_recommendations=alternative_recommendations,
            processing_time_ms=processing_time,
            data_sources_status=self.system_status,
            pob2_status={
                'client_available': self.pob2_client.is_available() if self.pob2_client else False,
                'installation_path': str(self.pob2_client.installation_path) if self.pob2_client else None
            },
            rag_confidence=rag_confidence,
            knowledge_base_size=self.knowledge_base.get_statistics().get('total_builds', 0),
            similarity_matches=len(search_results),
            total_candidates=len(search_results),
            successful_conversions=successful_conversions,
            average_compatibility=avg_compatibility,
            request_id=request_id
        )
    
    async def _update_caches_and_metrics(self, 
                                       result: IntegratedRecommendationResult,
                                       request: IntegratedRecommendationRequest):
        """更新缓存和性能指标"""
        # 缓存推荐结果
        cache_key = f"{request.character_class}_{request.build_goal}_{request.budget_range}"
        self.recommendation_cache[cache_key] = result
        
        # 更新平均响应时间
        total_requests = self.performance_metrics['total_requests']
        current_avg = self.performance_metrics['average_response_time']
        new_avg = (current_avg * (total_requests - 1) + result.processing_time_ms) / total_requests
        self.performance_metrics['average_response_time'] = new_avg
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态信息"""
        return {
            'initialized': self.initialized,
            'system_components': self.system_status,
            'performance_metrics': self.performance_metrics,
            'pob2_available': self.pob2_client.is_available() if self.pob2_client else False,
            'cache_size': len(self.recommendation_cache)
        }
    
    def display_recommendation_summary(self, result: IntegratedRecommendationResult):
        """显示推荐结果摘要"""
        print(f"\n" + "="*80)
        print(f"🎯 RAG-PoB2集成推荐结果 [ID: {result.request_id}]")
        print(f"="*80)
        
        print(f"⏱️  处理时间: {result.processing_time_ms:.2f}ms")
        print(f"🧠 RAG置信度: {result.rag_confidence:.3f}")
        print(f"📊 知识库规模: {result.knowledge_base_size:,} 构建")
        print(f"🔍 相似匹配: {result.similarity_matches} 个")
        print(f"✅ 成功转换: {result.successful_conversions}/{result.total_candidates}")
        print(f"⚖️  平均兼容性: {result.average_compatibility:.3f}")
        
        print(f"\n🏆 主推荐构建 ({len(result.primary_recommendations)}):")
        for i, (search_result, rec_score, pob2_validation) in enumerate(result.primary_recommendations, 1):
            metadata = search_result.metadata
            status_icon = "✅" if pob2_validation.is_valid else "⚠️"
            
            print(f"  {i}. {status_icon} {metadata.get('character_class', 'Unknown')} - {metadata.get('main_skill', 'Unknown')}")
            print(f"     推荐分数: {rec_score.total_score:.3f} | PoB2兼容: {pob2_validation.compatibility_score:.3f}")
            print(f"     预估DPS: {metadata.get('total_dps', 0):,} | 预算: {metadata.get('total_cost', 0)} divine")
            
            if pob2_validation.import_code:
                print(f"     PoB2代码: {pob2_validation.import_code[:50]}...")
        
        if result.alternative_recommendations:
            print(f"\n🔄 备选推荐 ({len(result.alternative_recommendations)}):")
            for i, (search_result, rec_score, pob2_validation) in enumerate(result.alternative_recommendations[:3], 1):
                metadata = search_result.metadata
                status_icon = "✅" if pob2_validation.is_valid else "⚠️"
                print(f"  {i}. {status_icon} {metadata.get('character_class', 'Unknown')} - {metadata.get('main_skill', 'Unknown')} (分数: {rec_score.total_score:.3f})")
        
        print(f"="*80)

# 便捷接口函数
async def create_integrated_recommender() -> RAGPoB2IntegratedRecommender:
    """创建并初始化集成推荐系统"""
    recommender = RAGPoB2IntegratedRecommender()
    success = await recommender.initialize()
    
    if not success:
        logger.warning("系统初始化存在问题，但仍可使用部分功能")
    
    return recommender

async def quick_recommendation(character_class: str, 
                             build_goal: str = "endgame_content",
                             budget_max: float = 20.0) -> IntegratedRecommendationResult:
    """快速推荐接口"""
    recommender = await create_integrated_recommender()
    
    request = IntegratedRecommendationRequest(
        character_class=character_class,
        build_goal=build_goal,
        budget_range=(0, budget_max),
        max_recommendations=5
    )
    
    return await recommender.generate_integrated_recommendations(request)

# 演示和测试函数
async def demo_integrated_system():
    """演示集成推荐系统"""
    print("🚀 RAG-PoB2集成推荐系统演示")
    print("="*60)
    
    # 创建推荐系统
    print("📡 初始化集成推荐系统...")
    recommender = await create_integrated_recommender()
    
    # 显示系统状态
    status = recommender.get_system_status()
    print(f"系统状态: 初始化={status['initialized']}, PoB2可用={status['pob2_available']}")
    
    # 创建示例推荐请求
    request = IntegratedRecommendationRequest(
        character_class="Ranger",
        build_goal="clear_speed", 
        budget_range=(0, 15),
        skill_level="intermediate",
        preferred_skills=["Lightning Arrow", "Explosive Shot"],
        max_recommendations=8,
        generate_pob2_code=True,
        validate_with_pob2=True
    )
    
    print(f"\n🎯 生成推荐: {request.character_class} {request.build_goal} (预算: {request.budget_range[1]} divine)")
    
    # 生成推荐
    result = await recommender.generate_integrated_recommendations(request)
    
    # 显示结果
    recommender.display_recommendation_summary(result)
    
    return recommender, result

if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_integrated_system())