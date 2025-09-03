# -*- coding: utf-8 -*-
"""
AI推荐器接口定义

本模块定义了PoE2 AI推荐系统的抽象接口，支持构筑推荐、智能分析、RAG增强等功能。
设计支持多种AI模型和推荐策略的集成。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from ..models import PoE2Build, PoE2Character, PoE2CharacterClass, PoE2BuildGoal


class AIModelStatus(Enum):
    """AI模型状态"""
    READY = "ready"
    LOADING = "loading"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    UPDATING = "updating"


class RecommendationType(Enum):
    """推荐类型"""
    BUILD_CREATION = "build_creation"
    BUILD_OPTIMIZATION = "build_optimization"
    ITEM_RECOMMENDATION = "item_recommendation"
    SKILL_SUGGESTION = "skill_suggestion"
    PASSIVE_OPTIMIZATION = "passive_optimization"
    BUDGET_PLANNING = "budget_planning"


class ConfidenceLevel(Enum):
    """置信度级别"""
    VERY_HIGH = "very_high"  # 95%+
    HIGH = "high"            # 85-95%
    MEDIUM = "medium"        # 70-85%
    LOW = "low"              # 50-70%
    VERY_LOW = "very_low"    # <50%


@dataclass
class RecommendationScore:
    """推荐评分"""
    overall_score: float  # 0-1整体评分
    dps_score: float = 0.0
    defense_score: float = 0.0
    cost_efficiency_score: float = 0.0
    league_start_viability: float = 0.0
    endgame_potential: float = 0.0
    ease_of_play: float = 0.0
    uniqueness_score: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    scoring_breakdown: Dict[str, float] = field(default_factory=dict)


@dataclass
class BuildSuggestion:
    """构筑建议"""
    build_name: str
    description: str
    character_class: str
    ascendancy: Optional[str] = None
    main_skills: List[str] = field(default_factory=list)
    key_items: List[str] = field(default_factory=list)
    estimated_cost: Dict[str, float] = field(default_factory=dict)
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    difficulty_rating: int = 1  # 1-5
    build_data: Optional[Dict[str, Any]] = None
    pob_import_code: Optional[str] = None
    score: Optional[RecommendationScore] = None


@dataclass
class RecommendationContext:
    """推荐上下文"""
    user_preferences: Dict[str, Any]
    current_league: str = "standard"
    budget_constraint: Optional[Dict[str, float]] = None
    experience_level: str = "intermediate"  # "beginner", "intermediate", "advanced"
    playtime_available: str = "medium"  # "low", "medium", "high"
    preferred_playstyle: List[str] = field(default_factory=list)
    avoid_mechanics: List[str] = field(default_factory=list)
    meta_preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecommendationRequest:
    """推荐请求"""
    recommendation_type: RecommendationType
    context: RecommendationContext
    character_class: Optional[str] = None
    build_goal: Optional[str] = None
    current_build: Optional[Dict[str, Any]] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    optimization_targets: List[str] = field(default_factory=list)
    max_results: int = 10
    include_explanations: bool = True
    include_alternatives: bool = True


@dataclass
class RecommendationResult:
    """推荐结果"""
    success: bool
    suggestions: List[BuildSuggestion] = field(default_factory=list)
    explanations: Dict[str, str] = field(default_factory=dict)
    alternatives: List[BuildSuggestion] = field(default_factory=list)
    meta_analysis: Dict[str, Any] = field(default_factory=dict)
    rag_confidence: float = 0.0
    processing_time_ms: int = 0
    model_version: str = ""
    data_sources_used: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None


class IAIRecommender(ABC):
    """AI推荐器基础接口
    
    定义所有AI推荐器都应该实现的核心方法。
    """
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """获取模型名称
        
        Returns:
            str: AI模型名称
        """
        pass
    
    @property
    @abstractmethod
    def model_version(self) -> str:
        """获取模型版本
        
        Returns:
            str: AI模型版本
        """
        pass
    
    @abstractmethod
    def get_status(self) -> AIModelStatus:
        """获取AI模型状态
        
        Returns:
            AIModelStatus: 当前模型状态
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """获取AI能力描述
        
        Returns:
            Dict[str, Any]: 模型能力和限制信息
        """
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """执行健康检查
        
        Returns:
            Dict[str, Any]: 健康检查结果
        """
        pass
    
    def is_available(self) -> bool:
        """检查AI是否可用
        
        Returns:
            bool: AI是否可用
        """
        return self.get_status() == AIModelStatus.READY


class IBuildRecommender(ABC):
    """构筑推荐器接口
    
    专门用于构筑推荐和创建的AI接口。
    """
    
    @abstractmethod
    def generate_recommendations(self, request: RecommendationRequest) -> RecommendationResult:
        """生成构筑推荐
        
        Args:
            request (RecommendationRequest): 推荐请求
            
        Returns:
            RecommendationResult: 推荐结果
        """
        pass
    
    @abstractmethod
    def create_build(self, preferences: Dict[str, Any], constraints: Dict[str, Any]) -> BuildSuggestion:
        """创建新构筑
        
        Args:
            preferences (Dict[str, Any]): 用户偏好
            constraints (Dict[str, Any]): 构筑约束
            
        Returns:
            BuildSuggestion: 生成的构筑建议
        """
        pass
    
    @abstractmethod
    def optimize_build(self, build_data: Dict[str, Any], optimization_goals: List[str]) -> List[BuildSuggestion]:
        """优化现有构筑
        
        Args:
            build_data (Dict[str, Any]): 现有构筑数据
            optimization_goals (List[str]): 优化目标
            
        Returns:
            List[BuildSuggestion]: 优化建议列表
        """
        pass
    
    @abstractmethod
    def analyze_build(self, build_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析构筑
        
        Args:
            build_data (Dict[str, Any]): 构筑数据
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        pass
    
    @abstractmethod
    def compare_builds(self, build1: Dict[str, Any], build2: Dict[str, Any]) -> Dict[str, Any]:
        """比较构筑
        
        Args:
            build1 (Dict[str, Any]): 构筑1数据
            build2 (Dict[str, Any]): 构筑2数据
            
        Returns:
            Dict[str, Any]: 比较结果
        """
        pass


class IItemRecommender(ABC):
    """物品推荐器接口
    
    专门用于物品推荐和装备优化的AI接口。
    """
    
    @abstractmethod
    def recommend_items(self, build_data: Dict[str, Any], budget: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """推荐物品
        
        Args:
            build_data (Dict[str, Any]): 构筑数据
            budget (Optional[Dict[str, float]]): 预算限制
            
        Returns:
            List[Dict[str, Any]]: 推荐物品列表
        """
        pass
    
    @abstractmethod
    def optimize_gear(self, current_gear: Dict[str, Any], goals: List[str]) -> Dict[str, Any]:
        """优化装备
        
        Args:
            current_gear (Dict[str, Any]): 当前装备
            goals (List[str]): 优化目标
            
        Returns:
            Dict[str, Any]: 优化后的装备配置
        """
        pass
    
    @abstractmethod
    def find_upgrade_path(self, current_gear: Dict[str, Any], budget_progression: List[float]) -> List[Dict[str, Any]]:
        """寻找升级路径
        
        Args:
            current_gear (Dict[str, Any]): 当前装备
            budget_progression (List[float]): 预算阶段列表
            
        Returns:
            List[Dict[str, Any]]: 升级路径建议
        """
        pass


class ISkillRecommender(ABC):
    """技能推荐器接口
    
    专门用于技能组合和支持宝石推荐的AI接口。
    """
    
    @abstractmethod
    def recommend_skills(self, character_class: str, build_goal: str) -> List[Dict[str, Any]]:
        """推荐技能
        
        Args:
            character_class (str): 角色职业
            build_goal (str): 构筑目标
            
        Returns:
            List[Dict[str, Any]]: 推荐技能列表
        """
        pass
    
    @abstractmethod
    def optimize_skill_setups(self, current_skills: List[Dict[str, Any]], available_sockets: Dict[str, int]) -> Dict[str, Any]:
        """优化技能配置
        
        Args:
            current_skills (List[Dict[str, Any]]): 当前技能
            available_sockets (Dict[str, int]): 可用孔位
            
Returns:
            Dict[str, Any]: 优化后的技能配置
        """
        pass
    
    @abstractmethod
    def suggest_support_gems(self, main_skill: Dict[str, Any], available_links: int) -> List[Dict[str, Any]]:
        """建议支持宝石
        
        Args:
            main_skill (Dict[str, Any]): 主技能
            available_links (int): 可用连接数
            
        Returns:
            List[Dict[str, Any]]: 支持宝石建议
        """
        pass


class IRAGEnhancedRecommender(ABC):
    """RAG增强推荐器接口
    
    使用检索增强生成(RAG)技术的高级推荐器接口。
    """
    
    @abstractmethod
    def update_knowledge_base(self, new_data: List[Dict[str, Any]]) -> bool:
        """更新知识库
        
        Args:
            new_data (List[Dict[str, Any]]): 新数据
            
        Returns:
            bool: 更新是否成功
        """
        pass
    
    @abstractmethod
    def query_knowledge_base(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """查询知识库
        
        Args:
            query (str): 查询文本
            top_k (int): 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 相关知识库条目
        """
        pass
    
    @abstractmethod
    def generate_rag_enhanced_recommendation(self, request: RecommendationRequest) -> RecommendationResult:
        """生成RAG增强的推荐
        
        Args:
            request (RecommendationRequest): 推荐请求
            
        Returns:
            RecommendationResult: RAG增强的推荐结果
        """
        pass
    
    @abstractmethod
    def explain_recommendation(self, suggestion: BuildSuggestion, context: RecommendationContext) -> Dict[str, Any]:
        """解释推荐原因
        
        Args:
            suggestion (BuildSuggestion): 构筑建议
            context (RecommendationContext): 推荐上下文
            
        Returns:
            Dict[str, Any]: 详细解释信息
        """
        pass
    
    @abstractmethod
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """获取知识库统计
        
        Returns:
            Dict[str, Any]: 知识库统计信息
        """
        pass


class IMetaAnalyzer(ABC):
    """Meta分析器接口
    
    专门用于游戏Meta分析和趋势预测的AI接口。
    """
    
    @abstractmethod
    def analyze_current_meta(self, league: str = "standard") -> Dict[str, Any]:
        """分析当前Meta
        
        Args:
            league (str): 联盟名称
            
        Returns:
            Dict[str, Any]: Meta分析结果
        """
        pass
    
    @abstractmethod
    def predict_meta_trends(self, time_horizon_days: int = 30) -> Dict[str, Any]:
        """预测Meta趋势
        
        Args:
            time_horizon_days (int): 预测时间范围(天)
            
        Returns:
            Dict[str, Any]: 趋势预测结果
        """
        pass
    
    @abstractmethod
    def identify_emerging_builds(self, confidence_threshold: float = 0.7) -> List[BuildSuggestion]:
        """识别新兴构筑
        
        Args:
            confidence_threshold (float): 置信度阈值
            
        Returns:
            List[BuildSuggestion]: 新兴构筑列表
        """
        pass
    
    @abstractmethod
    def analyze_build_popularity(self, builds: List[Dict[str, Any]]) -> Dict[str, float]:
        """分析构筑流行度
        
        Args:
            builds (List[Dict[str, Any]]): 构筑列表
            
        Returns:
            Dict[str, float]: 构筑流行度评分
        """
        pass


class IAIRecommenderFactory(ABC):
    """AI推荐器工厂接口
    
    用于创建和管理不同类型的AI推荐器实例。
    """
    
    @abstractmethod
    def create_build_recommender(self, config: Optional[Dict[str, Any]] = None) -> IBuildRecommender:
        """创建构筑推荐器
        
        Args:
            config (Optional[Dict[str, Any]]): 配置参数
            
        Returns:
            IBuildRecommender: 构筑推荐器实例
        """
        pass
    
    @abstractmethod
    def create_item_recommender(self, config: Optional[Dict[str, Any]] = None) -> IItemRecommender:
        """创建物品推荐器
        
        Args:
            config (Optional[Dict[str, Any]]): 配置参数
            
        Returns:
            IItemRecommender: 物品推荐器实例
        """
        pass
    
    @abstractmethod
    def create_skill_recommender(self, config: Optional[Dict[str, Any]] = None) -> ISkillRecommender:
        """创建技能推荐器
        
        Args:
            config (Optional[Dict[str, Any]]): 配置参数
            
        Returns:
            ISkillRecommender: 技能推荐器实例
        """
        pass
    
    @abstractmethod
    def create_rag_recommender(self, knowledge_base_path: str, config: Optional[Dict[str, Any]] = None) -> IRAGEnhancedRecommender:
        """创建RAG增强推荐器
        
        Args:
            knowledge_base_path (str): 知识库路径
            config (Optional[Dict[str, Any]]): 配置参数
            
        Returns:
            IRAGEnhancedRecommender: RAG增强推荐器实例
        """
        pass
    
    @abstractmethod
    def create_meta_analyzer(self, config: Optional[Dict[str, Any]] = None) -> IMetaAnalyzer:
        """创建Meta分析器
        
        Args:
            config (Optional[Dict[str, Any]]): 配置参数
            
        Returns:
            IMetaAnalyzer: Meta分析器实例
        """
        pass