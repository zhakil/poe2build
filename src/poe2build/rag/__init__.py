"""RAG (Retrieval-Augmented Generation) intelligent training system

RAG-enhanced AI system based on ninja.poe2 data for intelligent build recommendations and optimization suggestions.
"""

from .data_collector import (
    PoE2NinjaRAGCollector,
    CollectionStats
)

from .vectorizer import (
    PoE2RAGVectorizer as BuildVectorizer,
    VectorizationStats,
    create_vector_index as create_vectorizer
)

from .retrieval import (
    RetrievalEngine,
    SearchQuery,
    SearchResult,
    RetrievalStats,
    RetrievalMode,
    create_retrieval_engine,
    search_builds
)

from .ai_enhanced import (
    RAGEnhancedAI,
    UserPreferences,
    BuildRecommendation,
    OptimizationSuggestion,
    AIAnalysisResult,
    RecommendationStrategy,
    create_rag_ai_engine
)


__all__ = [
    # Data Collection
    'PoE2NinjaRAGCollector',
    'CollectionStats',
    
    # Vectorization
    'BuildVectorizer', 
    'VectorizationStats',
    'create_vectorizer',
    
    # Retrieval
    'RetrievalEngine',
    'SearchQuery',
    'SearchResult', 
    'RetrievalStats',
    'RetrievalMode',
    'create_retrieval_engine',
    'search_builds',
    
    # AI Enhancement
    'RAGEnhancedAI',
    'UserPreferences',
    'BuildRecommendation',
    'OptimizationSuggestion', 
    'AIAnalysisResult',
    'RecommendationStrategy',
    'create_rag_ai_engine'
]