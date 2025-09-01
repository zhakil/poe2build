# -*- coding: utf-8 -*-
"""
PoE2构筑生成器接口定义包

本包包含系统的抽象接口定义，为各个组件提供清晰的架构边界：
- IDataProvider: 数据源提供者接口
- ICalculationEngine: 计算引擎接口  
- IAIRecommender: AI推荐器接口
- IResilientService: 弹性服务接口

设计原则：
- 接口分离：每个接口职责单一
- 依赖倒置：高层模块依赖抽象而非具体实现
- 开闭原则：对扩展开放，对修改封闭
"""

# 数据源接口
from .data_provider import (
    IDataProvider,
    IMarketDataProvider,
    IBuildDataProvider, 
    IGameDataProvider,
    DataProviderStatus,
    MarketDataRequest,
    BuildDataRequest,
    GameDataRequest,
    DataResponse
)

# 计算引擎接口
from .calculation_engine import (
    ICalculationEngine,
    CalculationRequest,
    CalculationResult,
    BuildValidationResult,
    DPSCalculation,
    DefenseCalculation,
    EngineStatus,
    EngineCapabilities
)

# AI推荐器接口
from .ai_recommender import (
    IAIRecommender,
    RecommendationRequest,
    RecommendationResult,
    BuildSuggestion,
    RecommendationScore,
    AIModelStatus,
    RecommendationContext
)

# 弹性服务接口
from .resilient_service import (
    IResilientService,
    ServiceCall,
    ServiceStatus,
    ServiceHealth,
    CircuitBreakerState,
    RetryPolicy,
    FallbackStrategy
)

__all__ = [
    # 数据源接口
    "IDataProvider",
    "IMarketDataProvider", 
    "IBuildDataProvider",
    "IGameDataProvider",
    "DataProviderStatus",
    "MarketDataRequest",
    "BuildDataRequest",
    "GameDataRequest", 
    "DataResponse",
    
    # 计算引擎接口
    "ICalculationEngine",
    "CalculationRequest",
    "CalculationResult", 
    "BuildValidationResult",
    "DPSCalculation",
    "DefenseCalculation",
    "EngineStatus",
    "EngineCapabilities",
    
    # AI推荐器接口
    "IAIRecommender",
    "RecommendationRequest",
    "RecommendationResult",
    "BuildSuggestion",
    "RecommendationScore",
    "AIModelStatus", 
    "RecommendationContext",
    
    # 弹性服务接口
    "IResilientService",
    "ServiceCall",
    "ServiceStatus",
    "ServiceHealth",
    "CircuitBreakerState",
    "RetryPolicy",
    "FallbackStrategy"
]

__version__ = "2.0.0"