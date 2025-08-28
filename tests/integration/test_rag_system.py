"""Phase 4 RAG智能训练系统集成测试"""

import pytest
import asyncio
import tempfile
from pathlib import Path

from src.poe2build.rag import (
    BuildDataCollector, BuildVectorizer, RetrievalEngine, RAGEnhancedAI,
    UserPreferences, SearchQuery, RecommendationStrategy, RetrievalMode
)
from src.poe2build.models.characters import PoE2CharacterClass
from src.poe2build.data_sources.factory import get_factory


class TestRAGSystem:
    """RAG系统集成测试"""
    
    @pytest.mark.asyncio
    async def test_data_collector_initialization(self):
        """测试数据收集器初始化"""
        collector = BuildDataCollector()
        
        # 测试初始化
        init_result = await collector.initialize()
        assert init_result is True
        
        # 测试健康检查
        health = await collector.health_check()
        assert 'status' in health
        assert health['status'] in ['healthy', 'degraded']
        
        # 测试统计信息
        stats = collector.get_stats()
        assert 'total_builds_collected' in stats
        
        await collector.cleanup()
    
    @pytest.mark.asyncio
    async def test_vectorizer_initialization(self):
        """测试向量化器初始化"""
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir)
            vectorizer = BuildVectorizer(index_path)
            
            # 测试初始化
            init_result = await vectorizer.initialize()
            assert init_result is True
            
            # 测试统计信息
            stats = await vectorizer.get_stats()
            assert 'model_name' in stats
            assert 'index_path' in stats
            
            await vectorizer.cleanup()
    
    @pytest.mark.asyncio
    async def test_retrieval_engine_initialization(self):
        """测试检索引擎初始化"""
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir)
            engine = RetrievalEngine(index_path)
            
            # 测试初始化
            init_result = await engine.initialize()
            assert init_result is True
            
            # 测试健康检查
            health = await engine.health_check()
            assert 'status' in health
            assert health['status'] in ['healthy', 'degraded']
            
            # 测试统计信息
            stats = await engine.get_stats()
            assert 'engine_type' in stats
            
            await engine.cleanup()
    
    @pytest.mark.asyncio 
    async def test_search_functionality(self):
        """测试搜索功能"""
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir)
            engine = RetrievalEngine(index_path)
            await engine.initialize()
            
            # 创建搜索查询
            query = SearchQuery(
                text="fire witch build",
                character_class=PoE2CharacterClass.WITCH,
                main_skill="Fireball",
                budget_max=50.0,
                mode=RetrievalMode.SEMANTIC,
                top_k=5
            )
            
            # 执行搜索
            results, stats = await engine.search(query)
            
            # 验证结果
            assert isinstance(results, list)
            assert isinstance(stats.query_time_ms, float)
            assert stats.query_time_ms >= 0
            assert len(results) <= query.top_k
            
            # 验证结果结构
            for result in results:
                assert hasattr(result, 'build_id')
                assert hasattr(result, 'similarity_score')
                assert hasattr(result, 'final_score')
                assert 0.0 <= result.similarity_score <= 1.0
                assert result.final_score >= 0.0
            
            await engine.cleanup()
    
    @pytest.mark.asyncio
    async def test_rag_ai_initialization(self):
        """测试RAG AI引擎初始化"""
        ai_engine = RAGEnhancedAI()
        
        # 测试初始化
        init_result = await ai_engine.initialize()
        assert init_result is True
        
        # 测试健康检查
        health = await ai_engine.health_check()
        assert 'status' in health
        assert health['status'] in ['healthy', 'degraded']
        
        # 测试统计信息
        stats = await ai_engine.get_stats()
        assert 'engine_type' in stats
        
        await ai_engine.cleanup()
    
    @pytest.mark.asyncio
    async def test_recommendation_generation(self):
        """测试推荐生成"""
        ai_engine = RAGEnhancedAI()
        await ai_engine.initialize()
        
        # 创建用户偏好
        preferences = UserPreferences(
            character_class=PoE2CharacterClass.WITCH,
            preferred_ascendancy="Infernalist",
            playstyle=["aggressive", "ranged"],
            skill_preferences=["Fireball"],
            budget_range=(10.0, 50.0),
            experience_level="intermediate",
            content_focus=["mapping", "bossing"]
        )
        
        # 获取推荐
        recommendations = await ai_engine.get_recommendations(
            preferences, 
            RecommendationStrategy.HYBRID,
            limit=3
        )
        
        # 验证推荐结果
        assert isinstance(recommendations, list)
        assert len(recommendations) <= 3
        
        for rec in recommendations:
            assert hasattr(rec, 'build_id')
            assert hasattr(rec, 'recommendation_score')
            assert hasattr(rec, 'confidence_score')
            assert hasattr(rec, 'reasoning')
            assert hasattr(rec, 'pros')
            assert hasattr(rec, 'cons')
            assert 0.0 <= rec.recommendation_score <= 1.0
            assert 0.0 <= rec.confidence_score <= 1.0
            assert rec.difficulty_rating in ['easy', 'medium', 'hard']
        
        await ai_engine.cleanup()
    
    @pytest.mark.asyncio
    async def test_build_analysis(self):
        """测试构筑分析"""
        ai_engine = RAGEnhancedAI()
        await ai_engine.initialize()
        
        # 创建测试构筑数据
        test_build = {
            'build_id': 'test_witch_fire',
            'name': 'Test Fire Witch',
            'character_class': 'Witch',
            'ascendancy': 'Infernalist',
            'main_skill': 'Fireball',
            'support_gems': ['Fire Penetration', 'Elemental Focus'],
            'level': 85,
            'estimated_cost': 25.0,
            'estimated_dps': 800000,
            'estimated_life': 6500,
            'tags': ['fire', 'ranged', 'beginner-friendly']
        }
        
        # 执行分析
        analysis = await ai_engine.analyze_build(test_build, "standard")
        
        # 验证分析结果
        assert hasattr(analysis, 'build_id')
        assert analysis.build_id == 'test_witch_fire'
        assert hasattr(analysis, 'strengths')
        assert hasattr(analysis, 'weaknesses')
        assert hasattr(analysis, 'optimization_suggestions')
        assert isinstance(analysis.strengths, list)
        assert isinstance(analysis.weaknesses, list)
        assert isinstance(analysis.optimization_suggestions, list)
        assert 0.0 <= analysis.synergy_score <= 1.0
        assert 0.0 <= analysis.flexibility_score <= 1.0
        assert analysis.endgame_potential in ['low', 'medium', 'high', 'exceptional']
        
        await ai_engine.cleanup()
    
    @pytest.mark.asyncio
    async def test_build_optimization(self):
        """测试构筑优化"""
        ai_engine = RAGEnhancedAI()
        await ai_engine.initialize()
        
        # 创建测试构筑
        test_build = {
            'build_id': 'test_optimization',
            'name': 'Test Build',
            'estimated_dps': 400000,
            'estimated_life': 5000,
            'estimated_cost': 35.0
        }
        
        # 执行优化
        optimization_goals = ['damage', 'defense', 'cost']
        optimized_build = await ai_engine.optimize_build(test_build, optimization_goals)
        
        # 验证优化结果
        assert 'optimizations_applied' in optimized_build
        assert 'optimization_timestamp' in optimized_build
        assert isinstance(optimized_build['optimizations_applied'], list)
        
        await ai_engine.cleanup()
    
    @pytest.mark.asyncio
    async def test_end_to_end_rag_workflow(self):
        """测试端到端RAG工作流程"""
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir)
            
            # 初始化所有组件
            collector = BuildDataCollector()
            vectorizer = BuildVectorizer(index_path)
            retrieval_engine = RetrievalEngine(index_path, vectorizer)
            ai_engine = RAGEnhancedAI(
                data_collector=collector,
                vectorizer=vectorizer,
                retrieval_engine=retrieval_engine
            )
            
            # 初始化流程
            await collector.initialize()
            await vectorizer.initialize()
            await retrieval_engine.initialize()
            await ai_engine.initialize()
            
            try:
                # 1. 数据收集（使用mock数据）
                collection_stats = collector.get_stats()
                assert 'total_builds_collected' in collection_stats
                
                # 2. 向量化（mock实现）
                vectorization_stats = await vectorizer.get_stats()
                assert 'model_name' in vectorization_stats
                
                # 3. 创建用户偏好
                preferences = UserPreferences(
                    character_class=PoE2CharacterClass.RANGER,
                    playstyle=["ranged", "clear-speed"],
                    budget_range=(5.0, 30.0),
                    experience_level="beginner"
                )
                
                # 4. 获取推荐
                recommendations = await ai_engine.get_recommendations(
                    preferences,
                    RecommendationStrategy.POPULAR,
                    limit=2
                )
                
                # 5. 验证端到端结果
                assert isinstance(recommendations, list)
                assert len(recommendations) <= 2
                
                if recommendations:
                    # 分析第一个推荐
                    first_rec = recommendations[0]
                    analysis = await ai_engine.analyze_build(
                        first_rec.build_data, 
                        "standard"
                    )
                    assert analysis.build_id == first_rec.build_id
                
            finally:
                # 清理资源
                await collector.cleanup()
                await vectorizer.cleanup()
                await retrieval_engine.cleanup()
                await ai_engine.cleanup()
    
    @pytest.mark.asyncio
    async def test_meta_analysis(self):
        """测试元数据分析"""
        ai_engine = RAGEnhancedAI()
        await ai_engine.initialize()
        
        # 获取总体元数据分析
        meta_analysis = await ai_engine.get_meta_analysis()
        
        # 验证结果结构
        assert 'timestamp' in meta_analysis
        assert 'popular_builds' in meta_analysis
        assert 'trending_skills' in meta_analysis
        
        # 获取特定职业的元数据分析
        witch_meta = await ai_engine.get_meta_analysis(PoE2CharacterClass.WITCH)
        assert witch_meta['character_class'] == 'Witch'
        
        await ai_engine.cleanup()
    
    @pytest.mark.asyncio
    async def test_factory_integration(self):
        """测试工厂集成"""
        factory = get_factory()
        
        # 测试创建build provider（用于RAG数据收集）
        build_provider = factory.create_build_provider('ninja_poe2')
        assert build_provider is not None
        
        # 测试健康检查
        health_status = await factory.health_check_all_providers()
        assert 'build_providers' in health_status
        
        # 清理
        await factory.close_all_providers()
    
    @pytest.mark.asyncio
    async def test_error_handling_and_fallbacks(self):
        """测试错误处理和fallback机制"""
        # 测试无效路径的处理
        invalid_path = Path("/nonexistent/path")
        engine = RetrievalEngine(invalid_path)
        
        # 应该能够初始化（使用mock实现）
        init_result = await engine.initialize()
        assert init_result is True
        
        # 搜索应该返回mock结果
        query = SearchQuery(text="test query", top_k=3)
        results, stats = await engine.search(query)
        
        assert isinstance(results, list)
        assert len(results) <= 3
        
        await engine.cleanup()
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """测试并发操作"""
        ai_engine = RAGEnhancedAI()
        await ai_engine.initialize()
        
        # 创建多个不同的用户偏好
        preferences_list = [
            UserPreferences(character_class=PoE2CharacterClass.WITCH),
            UserPreferences(character_class=PoE2CharacterClass.RANGER),
            UserPreferences(character_class=PoE2CharacterClass.MONK)
        ]
        
        # 并发执行推荐请求
        tasks = [
            ai_engine.get_recommendations(prefs, RecommendationStrategy.SIMILAR, 2)
            for prefs in preferences_list
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 验证所有请求都成功完成
        for result in results:
            assert not isinstance(result, Exception)
            assert isinstance(result, list)
        
        await ai_engine.cleanup()


if __name__ == "__main__":
    asyncio.run(pytest.main([__file__, "-v"]))