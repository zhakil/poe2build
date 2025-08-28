"""Simple RAG System Demo - Phase 4 Demonstration

A simplified demonstration of the RAG intelligent training system components.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add project path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from poe2build.rag import (
    PoE2NinjaRAGCollector, BuildVectorizer, RetrievalEngine, RAGEnhancedAI,
    UserPreferences, SearchQuery, RecommendationStrategy, RetrievalMode
)
from poe2build.models.characters import PoE2CharacterClass


async def demo_basic_functionality():
    """Demonstrate basic RAG system functionality"""
    print("=== Phase 4 RAG System Basic Demo ===")
    
    # 1. Data Collector Demo
    print("\n1. Testing Data Collector...")
    collector = PoE2NinjaRAGCollector()
    print("Data Collector created successfully")
    
    try:
        health = await collector.health_check()
        print(f"Health status: {health.get('status', 'unknown')}")
    except Exception as e:
        print(f"Health check: {e} (using fallback)")
    
    stats = collector.get_stats()
    print(f"Stats: {stats}")
    
    try:
        await collector.cleanup()
    except Exception as e:
        print(f"Cleanup: {e} (not critical)")
    
    # 2. Vectorizer Demo
    print("\n2. Testing Vectorizer...")
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = Path(temp_dir)
        vectorizer = BuildVectorizer(index_path)
        success = await vectorizer.initialize()
        print(f"Vectorizer initialized: {success}")
        
        stats = await vectorizer.get_stats()
        print(f"Vectorizer stats: {stats}")
        
        await vectorizer.cleanup()
    
    # 3. Retrieval Engine Demo
    print("\n3. Testing Retrieval Engine...")
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = Path(temp_dir)
        engine = RetrievalEngine(index_path)
        success = await engine.initialize()
        print(f"Retrieval Engine initialized: {success}")
        
        # Test search
        query = SearchQuery(
            text="fire witch build",
            character_class=PoE2CharacterClass.WITCH,
            top_k=3
        )
        
        results, stats = await engine.search(query)
        print(f"Search results: {len(results)} builds found")
        print(f"Query time: {stats.query_time_ms:.1f}ms")
        
        for i, result in enumerate(results):
            print(f"  Result {i+1}: {result.build_id} (score: {result.final_score:.3f})")
        
        await engine.cleanup()
    
    # 4. RAG AI Engine Demo
    print("\n4. Testing RAG AI Engine...")
    ai_engine = RAGEnhancedAI()
    success = await ai_engine.initialize()
    print(f"RAG AI Engine initialized: {success}")
    
    # Test recommendations
    preferences = UserPreferences(
        character_class=PoE2CharacterClass.WITCH,
        playstyle=["fire", "ranged"],
        budget_range=(10.0, 50.0),
        experience_level="intermediate"
    )
    
    print(f"User preferences: {preferences.character_class.value}, budget: {preferences.budget_range}")
    
    recommendations = await ai_engine.get_recommendations(
        preferences, 
        RecommendationStrategy.HYBRID,
        limit=2
    )
    
    print(f"Generated {len(recommendations)} recommendations:")
    for i, rec in enumerate(recommendations):
        print(f"  Recommendation {i+1}:")
        print(f"    Name: {rec.build_data.get('name', 'Unknown')}")
        print(f"    Score: {rec.recommendation_score:.3f}")
        print(f"    Confidence: {rec.confidence_score:.3f}")
        print(f"    Difficulty: {rec.difficulty_rating}")
        print(f"    Cost: {rec.estimated_cost:.1f} Divine")
        print(f"    Pros: {', '.join(rec.pros)}")
        print(f"    Cons: {', '.join(rec.cons)}")
    
    # Test build analysis
    if recommendations:
        print("\n5. Testing Build Analysis...")
        first_rec = recommendations[0]
        analysis = await ai_engine.analyze_build(first_rec.build_data, "standard")
        
        print(f"Build Analysis Results:")
        print(f"  Synergy score: {analysis.synergy_score:.3f}")
        print(f"  Flexibility score: {analysis.flexibility_score:.3f}")
        print(f"  Meta position: {analysis.meta_position}")
        print(f"  League start viable: {analysis.league_start_viable}")
        print(f"  Endgame potential: {analysis.endgame_potential}")
        print(f"  Strengths: {', '.join(analysis.strengths)}")
        print(f"  Weaknesses: {', '.join(analysis.weaknesses)}")
        
        if analysis.optimization_suggestions:
            print(f"  Optimization suggestions:")
            for suggestion in analysis.optimization_suggestions[:2]:
                print(f"    - {suggestion.category}: {suggestion.description}")
    
    await ai_engine.cleanup()
    
    print("\n=== Demo completed successfully! ===")
    print("\nPhase 4 RAG System Summary:")
    print("- Data Collection: ninja.poe2 build data harvesting")
    print("- Vectorization: sentence-transformers semantic encoding") 
    print("- Retrieval: FAISS-powered similarity search")
    print("- AI Enhancement: Intelligent recommendations and analysis")
    print("- Mock Fallbacks: Graceful degradation when dependencies unavailable")


async def demo_integrated_workflow():
    """Demonstrate integrated RAG workflow"""
    print("\n=== Integrated Workflow Demo ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = Path(temp_dir)
        
        # Create integrated RAG system
        collector = PoE2NinjaRAGCollector()
        vectorizer = BuildVectorizer(index_path)
        retrieval_engine = RetrievalEngine(index_path, vectorizer)
        ai_engine = RAGEnhancedAI(
            data_collector=collector,
            vectorizer=vectorizer,
            retrieval_engine=retrieval_engine
        )
        
        # Initialize all components
        try:
            await vectorizer.initialize()
            await retrieval_engine.initialize()
            await ai_engine.initialize()
            print("RAG components initialized")
        except Exception as e:
            print(f"Initialization: {e} (using fallback implementations)")
        
        try:
            # Simulate user query
            user_query = "I want a beginner-friendly fire witch build under 20 Divine"
            print(f"User Query: {user_query}")
            
            # Parse to preferences
            preferences = UserPreferences(
                character_class=PoE2CharacterClass.WITCH,
                playstyle=["fire", "beginner-friendly"],
                budget_range=(0.0, 20.0),
                experience_level="beginner"
            )
            
            # Get recommendations
            recommendations = await ai_engine.get_recommendations(
                preferences,
                RecommendationStrategy.BUDGET_FRIENDLY,
                limit=1
            )
            
            if recommendations:
                best_rec = recommendations[0]
                print(f"\nBest Recommendation: {best_rec.build_data.get('name')}")
                print(f"Match Score: {best_rec.recommendation_score:.3f}")
                print(f"Reasoning: {'; '.join(best_rec.reasoning)}")
                
                # Apply optimizations
                optimization_goals = ["damage", "defense"]
                optimized_build = await ai_engine.optimize_build(
                    best_rec.build_data, 
                    optimization_goals
                )
                
                if 'optimizations_applied' in optimized_build:
                    print("\nOptimizations Applied:")
                    for opt in optimized_build['optimizations_applied']:
                        print(f"  - {opt['description']}")
                
                print("\nIntegrated workflow completed successfully!")
            else:
                print("No suitable recommendations found.")
                
        finally:
            # Cleanup
            try:
                await vectorizer.cleanup() 
                await retrieval_engine.cleanup()
                await ai_engine.cleanup()
            except Exception as e:
                print(f"Cleanup: {e} (not critical)")


async def main():
    """Main demo function"""
    print("PoE2 Build Generator - Phase 4 RAG System Demo")
    print("=" * 50)
    
    try:
        await demo_basic_functionality()
        await demo_integrated_workflow()
        
        print("\n" + "=" * 50)
        print("Phase 4 RAG System Demo Completed Successfully!")
        print("\nSystem is ready for Phase 5: System Integration")
        
    except Exception as e:
        print(f"\nDemo encountered an error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())