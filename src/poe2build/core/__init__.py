"""
PoE2 Build Generator Core Module

This package contains core system components:
- AI Orchestrator: Integrates RAG, PoB2 and data sources
- Build Generator: Intelligent build generation and optimization
- Recommendation Engine: Smart recommendation and ranking system
"""

from .ai_orchestrator import (
    PoE2AIOrchestrator,
    UserRequest,
    RecommendationResult,
    SystemComponent,
    ComponentStatus,
    ComponentHealth
)

from .build_generator import (
    PoE2BuildGenerator,
    GenerationConstraints,
    BuildTemplate,
    BuildArchetype,
    BuildComplexity
)

from .recommender import (
    PoE2Recommender,
    RecommendationRequest,
    BuildRecommendation,
    RecommendationScore,
    ScoringWeights,
    ScoringCriteria,
    RecommendationType
)

__all__ = [
    # AI Orchestrator
    'PoE2AIOrchestrator',
    'UserRequest', 
    'RecommendationResult',
    'SystemComponent',
    'ComponentStatus',
    'ComponentHealth',
    
    # Build Generator
    'PoE2BuildGenerator',
    'GenerationConstraints',
    'BuildTemplate',
    'BuildArchetype', 
    'BuildComplexity',
    
    # Recommendation Engine
    'PoE2Recommender',
    'RecommendationRequest',
    'BuildRecommendation',
    'RecommendationScore',
    'ScoringWeights',
    'ScoringCriteria',
    'RecommendationType'
]