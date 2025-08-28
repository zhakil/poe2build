"""RAG增强AI引擎

结合检索增强生成(RAG)技术与PoB2计算引擎，提供智能化构筑推荐和优化建议。
"""

import logging
import asyncio
import time
import json
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import random

from .data_collector import PoE2NinjaRAGCollector as BuildDataCollector
from .vectorizer import PoE2RAGVectorizer as BuildVectorizer
from .retrieval import RetrievalEngine, SearchQuery, SearchResult, RetrievalMode
from ..models.characters import PoE2CharacterClass
from ..models.build import PoE2Build, PoE2BuildStats
from ..pob2.calculator import PoB2Calculator


class RecommendationStrategy(Enum):
    """推荐策略枚举"""
    SIMILAR = "similar"  # 基于相似构筑
    POPULAR = "popular"  # 基于流行度
    OPTIMIZED = "optimized"  # 基于优化建议
    HYBRID = "hybrid"  # 混合策略
    BUDGET_FRIENDLY = "budget_friendly"  # 预算友好
    META = "meta"  # 当前元数据


@dataclass
class UserPreferences:
    """用户偏好配置"""
    character_class: Optional[PoE2CharacterClass] = None
    preferred_ascendancy: Optional[str] = None
    playstyle: List[str] = None  # ["aggressive", "defensive", "balanced"]
    skill_preferences: List[str] = None  # 偏好的技能
    budget_range: Tuple[float, float] = (0.0, 100.0)  # Divine orbs
    experience_level: str = "intermediate"  # beginner, intermediate, advanced
    content_focus: List[str] = None  # ["leveling", "endgame", "bossing", "mapping"]
    avoid_mechanics: List[str] = None  # 避免的机制
    
    def __post_init__(self):
        if self.playstyle is None:
            self.playstyle = []
        if self.skill_preferences is None:
            self.skill_preferences = []
        if self.content_focus is None:
            self.content_focus = []
        if self.avoid_mechanics is None:
            self.avoid_mechanics = []


@dataclass
class BuildRecommendation:
    """构筑推荐结果"""
    build_id: str
    build_data: Dict[str, Any]
    recommendation_score: float
    confidence_score: float
    reasoning: List[str]  # 推荐理由
    pros: List[str]  # 优点
    cons: List[str]  # 缺点
    difficulty_rating: str  # easy, medium, hard
    estimated_cost: float
    pob2_import_code: Optional[str] = None
    calculated_stats: Optional[Dict[str, Any]] = None
    similar_builds: List[str] = None  # 相似构筑ID列表
    customization_suggestions: List[str] = None  # 定制建议
    
    def __post_init__(self):
        if self.similar_builds is None:
            self.similar_builds = []
        if self.customization_suggestions is None:
            self.customization_suggestions = []


@dataclass
class OptimizationSuggestion:
    """优化建议"""
    category: str  # damage, defense, utility, cost
    priority: str  # high, medium, low
    description: str
    current_value: Optional[float] = None
    suggested_value: Optional[float] = None
    improvement_potential: Optional[float] = None  # 改进潜力百分比
    implementation_difficulty: str = "medium"  # easy, medium, hard
    cost_impact: Optional[float] = None  # 成本影响


@dataclass
class AIAnalysisResult:
    """AI分析结果"""
    analysis_type: str
    build_id: str
    strengths: List[str]
    weaknesses: List[str]
    optimization_suggestions: List[OptimizationSuggestion]
    meta_position: str  # tier ranking in current meta
    synergy_score: float  # 协同效应分数
    flexibility_score: float  # 灵活性分数
    league_start_viable: bool
    endgame_potential: str  # low, medium, high, exceptional
    timestamp: float


class MockAIEngine:
    """Mock AI引擎，当实际组件不可用时使用"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MockAIEngine")
    
    async def get_recommendations(self, preferences: UserPreferences, strategy: RecommendationStrategy = RecommendationStrategy.HYBRID, limit: int = 5) -> List[BuildRecommendation]:
        """生成Mock推荐"""
        mock_recommendations = []
        
        # 基于偏好生成mock数据
        char_class = preferences.character_class or PoE2CharacterClass.WITCH
        
        for i in range(min(limit, 3)):
            recommendation = BuildRecommendation(
                build_id=f"mock_build_{char_class.value.lower()}_{i+1}",
                build_data={
                    "name": f"Mock {char_class.value} Build {i+1}",
                    "character_class": char_class.value,
                    "ascendancy": "Infernalist" if char_class == PoE2CharacterClass.WITCH else "Generic",
                    "main_skill": "Fireball" if char_class == PoE2CharacterClass.WITCH else "Attack",
                    "level": 80 + i*5,
                    "description": f"A mock {char_class.value} build optimized for {strategy.value}"
                },
                recommendation_score=0.8 - i*0.1,
                confidence_score=0.75 - i*0.05,
                reasoning=[
                    f"匹配{char_class.value}职业偏好",
                    f"适合{strategy.value}策略",
                    "流行度较高"
                ],
                pros=[
                    "高伤害输出",
                    "操作简单",
                    "装备要求适中"
                ],
                cons=[
                    "防御略显不足",
                    "单体伤害一般"
                ],
                difficulty_rating="medium",
                estimated_cost=15.0 + i*10.0,
                pob2_import_code="mock_pob2_code_placeholder",
                calculated_stats={
                    "total_dps": 500000 + i*200000,
                    "life": 6000 + i*500,
                    "effective_health_pool": 8000 + i*1000
                },
                customization_suggestions=[
                    "可以考虑增加生命值",
                    "建议提升元素抗性"
                ]
            )
            
            mock_recommendations.append(recommendation)
        
        return mock_recommendations
    
    async def analyze_build(self, build_data: Dict[str, Any], analysis_depth: str = "standard") -> AIAnalysisResult:
        """分析构筑"""
        return AIAnalysisResult(
            analysis_type=analysis_depth,
            build_id=build_data.get("build_id", "mock_build"),
            strengths=[
                "伤害输出优秀",
                "生存能力良好",
                "装备选择灵活"
            ],
            weaknesses=[
                "前期升级稍慢",
                "某些Boss战稍显吃力"
            ],
            optimization_suggestions=[
                OptimizationSuggestion(
                    category="damage",
                    priority="high",
                    description="提升主技能等级和品质",
                    improvement_potential=15.0,
                    implementation_difficulty="easy",
                    cost_impact=5.0
                ),
                OptimizationSuggestion(
                    category="defense",
                    priority="medium", 
                    description="增加生命值和抗性",
                    improvement_potential=20.0,
                    implementation_difficulty="medium",
                    cost_impact=10.0
                )
            ],
            meta_position="Tier 2",
            synergy_score=0.85,
            flexibility_score=0.75,
            league_start_viable=True,
            endgame_potential="high",
            timestamp=time.time()
        )
    
    async def optimize_build(self, build_data: Dict[str, Any], optimization_goals: List[str]) -> Dict[str, Any]:
        """优化构筑"""
        optimized_build = build_data.copy()
        
        # Mock优化
        if "damage" in optimization_goals:
            optimized_build["estimated_dps"] = build_data.get("estimated_dps", 500000) * 1.15
        
        if "defense" in optimization_goals:
            optimized_build["estimated_life"] = build_data.get("estimated_life", 6000) * 1.1
        
        if "cost" in optimization_goals:
            optimized_build["estimated_cost"] = build_data.get("estimated_cost", 20.0) * 0.85
        
        optimized_build["optimization_applied"] = optimization_goals
        optimized_build["optimization_timestamp"] = time.time()
        
        return optimized_build


class RAGEnhancedAI:
    """RAG增强AI引擎"""
    
    def __init__(self, data_collector: Optional[BuildDataCollector] = None, 
                 vectorizer: Optional[BuildVectorizer] = None,
                 retrieval_engine: Optional[RetrievalEngine] = None,
                 pob2_calculator: Optional[PoB2Calculator] = None):
        self.logger = logging.getLogger(f"{__name__}.RAGEnhancedAI")
        
        self.data_collector = data_collector
        self.vectorizer = vectorizer
        self.retrieval_engine = retrieval_engine
        self.pob2_calculator = pob2_calculator
        
        # 检查组件可用性
        self._check_components()
        
        # AI模型配置
        self.model_config = {
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.9
        }
    
    def _check_components(self):
        """检查组件可用性"""
        components_available = all([
            self.data_collector,
            self.vectorizer, 
            self.retrieval_engine,
            self.pob2_calculator
        ])
        
        if not components_available:
            self.logger.warning("部分RAG组件不可用，使用Mock实现")
            self.use_real_impl = False
            self.mock_engine = MockAIEngine()
        else:
            self.use_real_impl = True
    
    async def initialize(self) -> bool:
        """初始化AI引擎"""
        try:
            if self.use_real_impl:
                # 初始化所有组件
                if self.retrieval_engine and not await self.retrieval_engine.initialize():
                    self.logger.warning("检索引擎初始化失败")
                
                if self.pob2_calculator and not await self.pob2_calculator.initialize():
                    self.logger.warning("PoB2计算器初始化失败")
            
            self.logger.info("RAG增强AI引擎初始化成功")
            return True
        
        except Exception as e:
            self.logger.error(f"AI引擎初始化失败: {e}")
            return False
    
    async def get_recommendations(self, preferences: UserPreferences, 
                                strategy: RecommendationStrategy = RecommendationStrategy.HYBRID,
                                limit: int = 5) -> List[BuildRecommendation]:
        """获取智能构筑推荐"""
        if not self.use_real_impl:
            return await self.mock_engine.get_recommendations(preferences, strategy, limit)
        
        try:
            # 1. 构建搜索查询
            search_query = self._build_search_query(preferences, strategy)
            
            # 2. 执行RAG检索
            search_results, retrieval_stats = await self.retrieval_engine.search(search_query)
            
            # 3. 使用AI增强分析和排序
            enhanced_results = await self._enhance_with_ai_analysis(search_results, preferences, strategy)
            
            # 4. 生成PoB2代码和计算统计数据
            final_recommendations = await self._generate_pob2_data(enhanced_results[:limit], preferences)
            
            # 5. 添加定制化建议
            personalized_recommendations = await self._add_personalization(final_recommendations, preferences)
            
            self.logger.info(f"生成了{len(personalized_recommendations)}个推荐，策略: {strategy.value}")
            return personalized_recommendations
        
        except Exception as e:
            self.logger.error(f"推荐生成失败: {e}")
            return []
    
    def _build_search_query(self, preferences: UserPreferences, strategy: RecommendationStrategy) -> SearchQuery:
        """构建搜索查询"""
        # 基础查询文本
        query_parts = []
        
        if preferences.character_class:
            query_parts.append(preferences.character_class.value)
        
        if preferences.preferred_ascendancy:
            query_parts.append(preferences.preferred_ascendancy)
        
        if preferences.skill_preferences:
            query_parts.extend(preferences.skill_preferences)
        
        if preferences.playstyle:
            query_parts.extend(preferences.playstyle)
        
        if preferences.content_focus:
            query_parts.extend(preferences.content_focus)
        
        query_text = " ".join(query_parts) if query_parts else "popular build"
        
        # 配置搜索参数
        search_mode = RetrievalMode.SEMANTIC
        if strategy == RecommendationStrategy.POPULAR:
            search_mode = RetrievalMode.FILTERED
        elif strategy == RecommendationStrategy.HYBRID:
            search_mode = RetrievalMode.HYBRID
        
        return SearchQuery(
            text=query_text,
            character_class=preferences.character_class,
            ascendancy=preferences.preferred_ascendancy,
            main_skill=preferences.skill_preferences[0] if preferences.skill_preferences else None,
            budget_min=preferences.budget_range[0],
            budget_max=preferences.budget_range[1],
            playstyle_tags=preferences.playstyle + preferences.content_focus,
            exclude_tags=preferences.avoid_mechanics,
            mode=search_mode,
            top_k=20,  # 获取更多候选以便AI筛选
            min_similarity=0.4,
            boost_popular=strategy in [RecommendationStrategy.POPULAR, RecommendationStrategy.META],
            boost_recent=strategy == RecommendationStrategy.META
        )
    
    async def _enhance_with_ai_analysis(self, search_results: List[SearchResult], 
                                      preferences: UserPreferences, 
                                      strategy: RecommendationStrategy) -> List[BuildRecommendation]:
        """使用AI增强分析和排序"""
        recommendations = []
        
        for result in search_results:
            # 分析构筑适配度
            suitability_score = self._calculate_suitability(result.build_data, preferences)
            
            # 生成推荐理由
            reasoning = self._generate_reasoning(result, preferences, strategy)
            
            # 分析优缺点
            pros, cons = self._analyze_pros_cons(result.build_data, preferences)
            
            # 评估难度
            difficulty = self._assess_difficulty(result.build_data, preferences.experience_level)
            
            # 计算最终推荐分数
            final_score = self._calculate_recommendation_score(
                result.final_score, suitability_score, strategy
            )
            
            # 计算置信度
            confidence = self._calculate_confidence(result, preferences, strategy)
            
            recommendation = BuildRecommendation(
                build_id=result.build_id,
                build_data=result.build_data,
                recommendation_score=final_score,
                confidence_score=confidence,
                reasoning=reasoning,
                pros=pros,
                cons=cons,
                difficulty_rating=difficulty,
                estimated_cost=result.build_data.get('estimated_cost', 0.0)
            )
            
            recommendations.append(recommendation)
        
        # 按推荐分数排序
        recommendations.sort(key=lambda x: x.recommendation_score, reverse=True)
        return recommendations
    
    def _calculate_suitability(self, build_data: Dict[str, Any], preferences: UserPreferences) -> float:
        """计算构筑适配度"""
        score = 0.5  # 基础分数
        
        # 职业匹配
        if preferences.character_class:
            if build_data.get('character_class') == preferences.character_class.value:
                score += 0.2
        
        # 升华匹配
        if preferences.preferred_ascendancy:
            if build_data.get('ascendancy') == preferences.preferred_ascendancy:
                score += 0.15
        
        # 技能偏好匹配
        if preferences.skill_preferences:
            main_skill = build_data.get('main_skill', '').lower()
            for skill in preferences.skill_preferences:
                if skill.lower() in main_skill:
                    score += 0.1
                    break
        
        # 预算适配
        build_cost = build_data.get('estimated_cost', 0)
        budget_min, budget_max = preferences.budget_range
        if budget_min <= build_cost <= budget_max:
            score += 0.1
        elif build_cost > budget_max:
            # 超预算惩罚
            overage_ratio = (build_cost - budget_max) / budget_max
            score -= min(0.3, overage_ratio * 0.5)
        
        # 内容焦点匹配
        build_tags = set(build_data.get('tags', []))
        content_tags = set(preferences.content_focus)
        if content_tags & build_tags:
            score += 0.1
        
        # 避免机制检查
        avoid_tags = set(preferences.avoid_mechanics)
        if avoid_tags & build_tags:
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _generate_reasoning(self, result: SearchResult, preferences: UserPreferences, 
                          strategy: RecommendationStrategy) -> List[str]:
        """生成推荐理由"""
        reasoning = []
        
        # 基础匹配理由
        reasoning.extend(result.match_reasons)
        
        # 策略相关理由
        if strategy == RecommendationStrategy.POPULAR:
            if result.popularity_score > 0.7:
                reasoning.append("当前热门构筑")
        elif strategy == RecommendationStrategy.META:
            reasoning.append("符合当前版本元数据")
        elif strategy == RecommendationStrategy.BUDGET_FRIENDLY:
            if result.build_data.get('estimated_cost', 0) < preferences.budget_range[1] * 0.8:
                reasoning.append("性价比优秀")
        
        # 经验等级适配
        difficulty = self._assess_difficulty(result.build_data, preferences.experience_level)
        if difficulty == "easy" and preferences.experience_level == "beginner":
            reasoning.append("适合新手操作")
        elif difficulty == "hard" and preferences.experience_level == "advanced":
            reasoning.append("满足高端玩家需求")
        
        return reasoning
    
    def _analyze_pros_cons(self, build_data: Dict[str, Any], preferences: UserPreferences) -> Tuple[List[str], List[str]]:
        """分析构筑优缺点"""
        pros = []
        cons = []
        
        # 基于统计数据分析
        estimated_dps = build_data.get('estimated_dps', 0)
        if estimated_dps > 1000000:
            pros.append("高伤害输出")
        elif estimated_dps < 300000:
            cons.append("伤害输出一般")
        
        estimated_life = build_data.get('estimated_life', 0)
        if estimated_life > 7000:
            pros.append("生存能力强")
        elif estimated_life < 5000:
            cons.append("生命值偏低")
        
        # 基于成本分析
        cost = build_data.get('estimated_cost', 0)
        if cost < 10:
            pros.append("装备要求低")
        elif cost > 50:
            cons.append("装备投入较高")
        
        # 基于标签分析
        tags = set(build_data.get('tags', []))
        
        if 'beginner-friendly' in tags:
            pros.append("新手友好")
        if 'clear-speed' in tags:
            pros.append("刷图效率高")
        if 'boss-killer' in tags:
            pros.append("单体Boss能力强")
        if 'league-start' in tags:
            pros.append("联赛开荒可用")
        
        if 'complex' in tags:
            cons.append("操作复杂")
        if 'gear-dependent' in tags:
            cons.append("装备依赖性强")
        
        return pros, cons
    
    def _assess_difficulty(self, build_data: Dict[str, Any], experience_level: str) -> str:
        """评估构筑难度"""
        difficulty_score = 0
        
        # 基于标签评估
        tags = build_data.get('tags', [])
        
        if 'beginner-friendly' in tags:
            difficulty_score -= 2
        if 'complex' in tags:
            difficulty_score += 2
        if 'advanced' in tags:
            difficulty_score += 1
        if 'micro-management' in tags:
            difficulty_score += 1
        
        # 基于技能复杂度
        support_gems = build_data.get('support_gems', [])
        if len(support_gems) > 5:
            difficulty_score += 1
        
        # 映射到难度等级
        if difficulty_score <= -1:
            return "easy"
        elif difficulty_score >= 2:
            return "hard"
        else:
            return "medium"
    
    def _calculate_recommendation_score(self, base_score: float, suitability_score: float, 
                                      strategy: RecommendationStrategy) -> float:
        """计算最终推荐分数"""
        # 基础权重
        weights = {
            'base': 0.4,
            'suitability': 0.6
        }
        
        # 根据策略调整权重
        if strategy == RecommendationStrategy.SIMILAR:
            weights['base'] = 0.7
            weights['suitability'] = 0.3
        elif strategy == RecommendationStrategy.OPTIMIZED:
            weights['base'] = 0.3
            weights['suitability'] = 0.7
        
        return base_score * weights['base'] + suitability_score * weights['suitability']
    
    def _calculate_confidence(self, result: SearchResult, preferences: UserPreferences, 
                            strategy: RecommendationStrategy) -> float:
        """计算推荐置信度"""
        confidence = 0.5  # 基础置信度
        
        # 基于相似度分数
        confidence += result.similarity_score * 0.3
        
        # 基于流行度
        confidence += result.popularity_score * 0.2
        
        # 基于匹配理由数量
        confidence += min(0.2, len(result.match_reasons) * 0.05)
        
        return max(0.0, min(1.0, confidence))
    
    async def _generate_pob2_data(self, recommendations: List[BuildRecommendation], 
                                preferences: UserPreferences) -> List[BuildRecommendation]:
        """生成PoB2代码和计算统计数据"""
        if not self.pob2_calculator:
            return recommendations
        
        for recommendation in recommendations:
            try:
                # 生成PoB2导入代码
                import_code = await self.pob2_calculator.generate_import_code(recommendation.build_data)
                recommendation.pob2_import_code = import_code
                
                # 计算详细统计数据
                if import_code:
                    stats_result = await self.pob2_calculator.calculate_build_stats(recommendation.build_data)
                    if stats_result.get('success'):
                        recommendation.calculated_stats = stats_result.get('calculated_stats')
                
            except Exception as e:
                self.logger.error(f"PoB2数据生成失败 (build_id: {recommendation.build_id}): {e}")
        
        return recommendations
    
    async def _add_personalization(self, recommendations: List[BuildRecommendation], 
                                 preferences: UserPreferences) -> List[BuildRecommendation]:
        """添加个性化建议"""
        for recommendation in recommendations:
            customization_suggestions = []
            
            # 基于经验等级的建议
            if preferences.experience_level == "beginner":
                customization_suggestions.append("建议先熟悉核心技能机制再进行高级配置")
                if recommendation.difficulty_rating == "hard":
                    customization_suggestions.append("此构筑较为复杂，建议观看相关教学视频")
            
            # 基于预算的建议
            build_cost = recommendation.estimated_cost
            budget_max = preferences.budget_range[1]
            
            if build_cost > budget_max * 0.8:
                customization_suggestions.append("可以考虑使用更经济的装备替代方案")
            elif build_cost < budget_max * 0.5:
                customization_suggestions.append("预算充足，可以考虑升级关键装备")
            
            # 基于内容焦点的建议
            if "bossing" in preferences.content_focus:
                customization_suggestions.append("针对Boss战，建议提升单体伤害和生存能力")
            if "mapping" in preferences.content_focus:
                customization_suggestions.append("用于刷图时，可以优先考虑清怪速度和移动速度")
            
            recommendation.customization_suggestions = customization_suggestions
        
        return recommendations
    
    async def analyze_build(self, build_data: Dict[str, Any], 
                          analysis_depth: str = "standard") -> AIAnalysisResult:
        """深度分析构筑"""
        if not self.use_real_impl:
            return await self.mock_engine.analyze_build(build_data, analysis_depth)
        
        try:
            # 获取相似构筑以进行比较分析
            similar_builds = []
            if self.retrieval_engine:
                build_id = build_data.get('build_id', 'unknown')
                similar_results = await self.retrieval_engine.get_similar_builds(build_id, 5)
                similar_builds = [r.build_data for r in similar_results]
            
            # 分析构筑强点
            strengths = self._analyze_strengths(build_data, similar_builds)
            
            # 分析构筑弱点
            weaknesses = self._analyze_weaknesses(build_data, similar_builds)
            
            # 生成优化建议
            optimization_suggestions = await self._generate_optimization_suggestions(
                build_data, analysis_depth
            )
            
            # 评估元数据位置
            meta_position = self._evaluate_meta_position(build_data, similar_builds)
            
            # 计算协同效应和灵活性分数
            synergy_score = self._calculate_synergy_score(build_data)
            flexibility_score = self._calculate_flexibility_score(build_data)
            
            # 评估联赛开荒和终局潜力
            league_start_viable = self._assess_league_start_viability(build_data)
            endgame_potential = self._assess_endgame_potential(build_data)
            
            return AIAnalysisResult(
                analysis_type=analysis_depth,
                build_id=build_data.get('build_id', 'unknown'),
                strengths=strengths,
                weaknesses=weaknesses,
                optimization_suggestions=optimization_suggestions,
                meta_position=meta_position,
                synergy_score=synergy_score,
                flexibility_score=flexibility_score,
                league_start_viable=league_start_viable,
                endgame_potential=endgame_potential,
                timestamp=time.time()
            )
        
        except Exception as e:
            self.logger.error(f"构筑分析失败: {e}")
            # 返回基础分析
            return AIAnalysisResult(
                analysis_type="error",
                build_id=build_data.get('build_id', 'unknown'),
                strengths=["分析遇到问题"],
                weaknesses=["无法完整分析"],
                optimization_suggestions=[],
                meta_position="未知",
                synergy_score=0.5,
                flexibility_score=0.5,
                league_start_viable=False,
                endgame_potential="unknown",
                timestamp=time.time()
            )
    
    def _analyze_strengths(self, build_data: Dict[str, Any], similar_builds: List[Dict[str, Any]]) -> List[str]:
        """分析构筑强点"""
        strengths = []
        
        # DPS分析
        build_dps = build_data.get('estimated_dps', 0)
        if similar_builds:
            avg_dps = sum(b.get('estimated_dps', 0) for b in similar_builds) / len(similar_builds)
            if build_dps > avg_dps * 1.2:
                strengths.append("伤害输出优于同类构筑")
        elif build_dps > 800000:
            strengths.append("高伤害输出")
        
        # 生命值分析
        build_life = build_data.get('estimated_life', 0)
        if build_life > 7000:
            strengths.append("生存能力强")
        
        # 成本分析
        build_cost = build_data.get('estimated_cost', 0)
        if build_cost < 15:
            strengths.append("装备要求低，性价比高")
        
        # 基于标签的强点
        tags = build_data.get('tags', [])
        tag_strengths = {
            'clear-speed': '刷图效率极高',
            'boss-killer': 'Boss战表现优秀',
            'league-start': '联赛开荒友好',
            'beginner-friendly': '新手友好，易于上手',
            'all-content': '全内容适用性强'
        }
        
        for tag, strength in tag_strengths.items():
            if tag in tags:
                strengths.append(strength)
        
        return strengths
    
    def _analyze_weaknesses(self, build_data: Dict[str, Any], similar_builds: List[Dict[str, Any]]) -> List[str]:
        """分析构筑弱点"""
        weaknesses = []
        
        # DPS不足
        build_dps = build_data.get('estimated_dps', 0)
        if build_dps < 400000:
            weaknesses.append("伤害输出偏低")
        
        # 生命值不足
        build_life = build_data.get('estimated_life', 0)
        if build_life < 5500:
            weaknesses.append("生命值偏低，容易暴毙")
        
        # 成本过高
        build_cost = build_data.get('estimated_cost', 0)
        if build_cost > 40:
            weaknesses.append("装备投入较高")
        
        # 基于标签的弱点
        tags = build_data.get('tags', [])
        tag_weaknesses = {
            'complex': '操作复杂度较高',
            'gear-dependent': '高度依赖装备',
            'single-target-weak': '单体伤害不足',
            'aoe-weak': 'AOE清怪能力一般',
            'mana-hungry': '蓝耗压力大'
        }
        
        for tag, weakness in tag_weaknesses.items():
            if tag in tags:
                weaknesses.append(weakness)
        
        return weaknesses
    
    async def _generate_optimization_suggestions(self, build_data: Dict[str, Any], 
                                               analysis_depth: str) -> List[OptimizationSuggestion]:
        """生成优化建议"""
        suggestions = []
        
        # DPS优化建议
        build_dps = build_data.get('estimated_dps', 0)
        if build_dps < 600000:
            suggestions.append(OptimizationSuggestion(
                category="damage",
                priority="high",
                description="提升主技能等级和品质，考虑更换高DPS武器",
                current_value=build_dps,
                suggested_value=build_dps * 1.3,
                improvement_potential=30.0,
                implementation_difficulty="medium",
                cost_impact=10.0
            ))
        
        # 防御优化建议
        build_life = build_data.get('estimated_life', 0)
        if build_life < 6000:
            suggestions.append(OptimizationSuggestion(
                category="defense",
                priority="high",
                description="增加生命值属性，提升抗性和护甲",
                current_value=build_life,
                suggested_value=build_life + 1000,
                improvement_potential=20.0,
                implementation_difficulty="easy",
                cost_impact=5.0
            ))
        
        # 成本优化建议
        build_cost = build_data.get('estimated_cost', 0)
        if build_cost > 30:
            suggestions.append(OptimizationSuggestion(
                category="cost",
                priority="medium",
                description="寻找性价比更高的装备替代方案",
                current_value=build_cost,
                suggested_value=build_cost * 0.8,
                improvement_potential=20.0,
                implementation_difficulty="medium",
                cost_impact=-6.0
            ))
        
        # 基于深度分析添加更多建议
        if analysis_depth == "comprehensive":
            suggestions.extend(await self._generate_advanced_optimizations(build_data))
        
        return suggestions
    
    async def _generate_advanced_optimizations(self, build_data: Dict[str, Any]) -> List[OptimizationSuggestion]:
        """生成高级优化建议"""
        advanced_suggestions = []
        
        # 技能宝石优化
        support_gems = build_data.get('support_gems', [])
        if len(support_gems) < 4:
            advanced_suggestions.append(OptimizationSuggestion(
                category="utility",
                priority="medium",
                description="考虑添加更多辅助宝石以提升效果",
                improvement_potential=15.0,
                implementation_difficulty="easy",
                cost_impact=3.0
            ))
        
        # 天赋优化
        level = build_data.get('level', 1)
        if level < 85:
            advanced_suggestions.append(OptimizationSuggestion(
                category="utility",
                priority="low",
                description="继续升级以解锁更多天赋点",
                improvement_potential=10.0,
                implementation_difficulty="easy",
                cost_impact=0.0
            ))
        
        return advanced_suggestions
    
    def _evaluate_meta_position(self, build_data: Dict[str, Any], similar_builds: List[Dict[str, Any]]) -> str:
        """评估元数据位置"""
        # 基于流行度评估
        popularity = build_data.get('popularity', 0.0)
        
        if popularity >= 0.8:
            return "Tier S"
        elif popularity >= 0.6:
            return "Tier 1"
        elif popularity >= 0.4:
            return "Tier 2"
        elif popularity >= 0.2:
            return "Tier 3"
        else:
            return "Tier 4"
    
    def _calculate_synergy_score(self, build_data: Dict[str, Any]) -> float:
        """计算协同效应分数"""
        # 基于技能和辅助宝石的协同
        main_skill = build_data.get('main_skill', '').lower()
        support_gems = [g.lower() for g in build_data.get('support_gems', [])]
        
        synergy_score = 0.5  # 基础分数
        
        # 检查已知的协同组合
        synergy_combinations = {
            'fireball': ['fire penetration', 'elemental focus', 'controlled destruction'],
            'lightning arrow': ['chain', 'elemental damage with attacks', 'added lightning'],
            'quarter staff': ['melee physical damage', 'multistrike', 'fortify']
        }
        
        if main_skill in synergy_combinations:
            synergy_gems = synergy_combinations[main_skill]
            matches = sum(1 for gem in support_gems if any(sg in gem for sg in synergy_gems))
            synergy_score += (matches / len(synergy_gems)) * 0.4
        
        return min(1.0, synergy_score)
    
    def _calculate_flexibility_score(self, build_data: Dict[str, Any]) -> float:
        """计算灵活性分数"""
        flexibility_score = 0.5
        
        # 基于标签评估灵活性
        tags = build_data.get('tags', [])
        
        flexibility_tags = ['versatile', 'adaptable', 'all-content']
        rigidity_tags = ['specialized', 'niche', 'one-trick']
        
        for tag in flexibility_tags:
            if tag in tags:
                flexibility_score += 0.2
        
        for tag in rigidity_tags:
            if tag in tags:
                flexibility_score -= 0.2
        
        return max(0.0, min(1.0, flexibility_score))
    
    def _assess_league_start_viability(self, build_data: Dict[str, Any]) -> bool:
        """评估联赛开荒可行性"""
        # 成本门槛
        cost = build_data.get('estimated_cost', 0)
        if cost > 25:
            return False
        
        # 检查联赛开荒标签
        tags = build_data.get('tags', [])
        if 'league-start' in tags:
            return True
        
        if 'gear-dependent' in tags:
            return False
        
        # 基于其他因素评估
        return cost < 15
    
    def _assess_endgame_potential(self, build_data: Dict[str, Any]) -> str:
        """评估终局潜力"""
        dps = build_data.get('estimated_dps', 0)
        life = build_data.get('estimated_life', 0)
        
        # 综合评分
        score = 0
        
        if dps > 1500000:
            score += 3
        elif dps > 1000000:
            score += 2
        elif dps > 600000:
            score += 1
        
        if life > 8000:
            score += 2
        elif life > 6500:
            score += 1
        
        # 基于标签调整
        tags = build_data.get('tags', [])
        if 'endgame' in tags:
            score += 1
        if 'boss-killer' in tags:
            score += 1
        
        if score >= 5:
            return "exceptional"
        elif score >= 3:
            return "high"
        elif score >= 1:
            return "medium"
        else:
            return "low"
    
    async def optimize_build(self, build_data: Dict[str, Any], 
                           optimization_goals: List[str]) -> Dict[str, Any]:
        """优化构筑配置"""
        if not self.use_real_impl:
            return await self.mock_engine.optimize_build(build_data, optimization_goals)
        
        optimized_build = build_data.copy()
        
        try:
            # 生成优化建议
            suggestions = await self._generate_optimization_suggestions(build_data, "comprehensive")
            
            # 应用优化
            applied_optimizations = []
            
            for goal in optimization_goals:
                relevant_suggestions = [s for s in suggestions if s.category == goal or goal in s.description.lower()]
                
                for suggestion in relevant_suggestions:
                    if suggestion.priority in ["high", "medium"]:
                        # 应用优化（这里是简化实现）
                        if suggestion.category == "damage" and suggestion.suggested_value:
                            optimized_build['estimated_dps'] = suggestion.suggested_value
                        elif suggestion.category == "defense" and suggestion.suggested_value:
                            optimized_build['estimated_life'] = suggestion.suggested_value
                        elif suggestion.category == "cost" and suggestion.suggested_value:
                            optimized_build['estimated_cost'] = suggestion.suggested_value
                        
                        applied_optimizations.append({
                            'category': suggestion.category,
                            'description': suggestion.description,
                            'improvement': suggestion.improvement_potential
                        })
            
            optimized_build['optimizations_applied'] = applied_optimizations
            optimized_build['optimization_timestamp'] = time.time()
            
            # 重新计算PoB2统计数据
            if self.pob2_calculator:
                try:
                    new_stats = await self.pob2_calculator.calculate_build_stats(optimized_build)
                    if new_stats.get('success'):
                        optimized_build['calculated_stats'] = new_stats.get('calculated_stats')
                except Exception as e:
                    self.logger.error(f"PoB2重新计算失败: {e}")
            
            return optimized_build
        
        except Exception as e:
            self.logger.error(f"构筑优化失败: {e}")
            return build_data
    
    async def get_meta_analysis(self, character_class: Optional[PoE2CharacterClass] = None) -> Dict[str, Any]:
        """获取元数据分析"""
        try:
            # 收集最新数据
            if self.data_collector:
                await self.data_collector.collect_latest_builds(limit=200)
            
            # 分析流行趋势
            meta_analysis = {
                "timestamp": time.time(),
                "character_class": character_class.value if character_class else "all",
                "popular_builds": [],
                "trending_skills": [],
                "ascendancy_distribution": {},
                "cost_distribution": {},
                "difficulty_distribution": {},
                "content_focus_trends": {}
            }
            
            # 这里会从数据收集器获取实际数据进行分析
            # 为了简化，返回mock数据
            meta_analysis.update({
                "popular_builds": [
                    {"name": "Infernalist Fire Witch", "popularity": 0.85},
                    {"name": "Deadeye Lightning Bow", "popularity": 0.78},
                    {"name": "Invoker Staff Monk", "popularity": 0.72}
                ],
                "trending_skills": [
                    {"skill": "Fireball", "growth": 0.15},
                    {"skill": "Lightning Arrow", "growth": 0.12},
                    {"skill": "Quarter Staff", "growth": 0.08}
                ]
            })
            
            return meta_analysis
        
        except Exception as e:
            self.logger.error(f"元数据分析失败: {e}")
            return {"error": "元数据分析不可用", "timestamp": time.time()}
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取AI引擎统计信息"""
        return {
            "engine_type": "real" if self.use_real_impl else "mock",
            "components_initialized": self.use_real_impl,
            "model_config": self.model_config,
            "last_updated": time.time()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health = {
            "status": "healthy",
            "components": {},
            "timestamp": time.time()
        }
        
        if self.use_real_impl:
            # 检查各组件状态
            if self.retrieval_engine:
                health["components"]["retrieval"] = await self.retrieval_engine.health_check()
            if self.pob2_calculator:
                health["components"]["pob2"] = await self.pob2_calculator.get_health_status()
        else:
            health["status"] = "degraded"
            health["warning"] = "使用Mock实现"
        
        return health
    
    async def cleanup(self):
        """清理资源"""
        if self.retrieval_engine:
            await self.retrieval_engine.cleanup()
        if self.pob2_calculator:
            await self.pob2_calculator.cleanup()
        
        self.logger.info("RAG增强AI引擎资源已清理")


# 便捷函数
async def create_rag_ai_engine(data_collector=None, vectorizer=None, 
                             retrieval_engine=None, pob2_calculator=None) -> RAGEnhancedAI:
    """创建RAG增强AI引擎"""
    engine = RAGEnhancedAI(data_collector, vectorizer, retrieval_engine, pob2_calculator)
    await engine.initialize()
    return engine