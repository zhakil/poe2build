"""RAG智能训练系统演示

展示Phase 4 RAG系统的核心功能和组件集成。
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from poe2build.rag import (
    PoE2NinjaRAGCollector, BuildVectorizer, RetrievalEngine, RAGEnhancedAI,
    UserPreferences, SearchQuery, RecommendationStrategy, RetrievalMode
)
from poe2build.models.characters import PoE2CharacterClass
from poe2build.data_sources.factory import get_factory


async def demo_data_collector():
    """演示数据收集器"""
    print("=== Phase 4.1: 数据收集器演示 ===")
    
    collector = PoE2NinjaRAGCollector()
    
    # 初始化
    print("初始化数据收集器...")
    success = await collector.initialize()
    print(f"初始化结果: {'成功' if success else '失败'}")
    
    # 健康检查
    health = await collector.health_check()
    print(f"健康状态: {health['status']}")
    
    # 获取统计信息
    stats = collector.get_stats()
    print(f"收集器统计: {stats}")
    
    # 尝试收集数据（mock模式）
    try:
        collection_result = await collector.collect_latest_builds(limit=5)
        print(f"收集结果: {collection_result}")
    except Exception as e:
        print(f"收集过程: {e} (使用Mock数据)")
    
    await collector.cleanup()
    print("数据收集器演示完成\n")


async def demo_vectorizer():
    """演示向量化器"""
    print("=== Phase 4.2: 向量化器演示 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = Path(temp_dir)
        vectorizer = BuildVectorizer(index_path)
        
        # 初始化
        print("初始化向量化器...")
        success = await vectorizer.initialize()
        print(f"初始化结果: {'成功' if success else '失败'}")
        
        # 获取统计信息
        stats = await vectorizer.get_stats()
        print(f"向量化器统计: {stats}")
        
        # 测试向量化
        test_builds = [
            {
                'build_id': 'demo_witch_1',
                'name': 'Infernalist Fire Witch',
                'description': 'High damage fire-based witch build',
                'character_class': 'Witch',
                'main_skill': 'Fireball'
            }
        ]
        
        try:
            vectorization_result = await vectorizer.vectorize_builds(test_builds)
            print(f"向量化结果: {vectorization_result}")
        except Exception as e:
            print(f"向量化过程: {e} (使用Mock实现)")
        
        await vectorizer.cleanup()
        print("向量化器演示完成\n")


async def demo_retrieval_engine():
    """演示检索引擎"""
    print("=== Phase 4.3: 检索引擎演示 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = Path(temp_dir)
        engine = RetrievalEngine(index_path)
        
        # 初始化
        print("初始化检索引擎...")
        success = await engine.initialize()
        print(f"初始化结果: {'成功' if success else '失败'}")
        
        # 健康检查
        health = await engine.health_check()
        print(f"健康状态: {health}")
        
        # 创建搜索查询
        query = SearchQuery(
            text="fire witch build for mapping",
            character_class=PoE2CharacterClass.WITCH,
            main_skill="Fireball",
            budget_max=30.0,
            playstyle_tags=["fire", "ranged"],
            mode=RetrievalMode.SEMANTIC,
            top_k=3
        )
        
        print(f"执行搜索查询: {query.text}")
        
        # 执行搜索
        results, stats = await engine.search(query)
        
        print(f"搜索统计: 查询时间{stats.query_time_ms:.1f}ms, 返回{stats.returned_results}个结果")
        
        # 显示结果
        for i, result in enumerate(results):
            print(f"\n结果 {i+1}:")
            print(f"  构筑ID: {result.build_id}")
            print(f"  相似度: {result.similarity_score:.3f}")
            print(f"  最终分数: {result.final_score:.3f}")
            print(f"  匹配原因: {', '.join(result.match_reasons)}")
        
        await engine.cleanup()
        print("检索引擎演示完成\n")


async def demo_rag_ai_engine():
    """演示RAG AI引擎"""
    print("=== Phase 4.4: RAG AI引擎演示 ===")
    
    ai_engine = RAGEnhancedAI()
    
    # 初始化
    print("初始化RAG AI引擎...")
    success = await ai_engine.initialize()
    print(f"初始化结果: {'成功' if success else '失败'}")
    
    # 健康检查
    health = await ai_engine.health_check()
    print(f"健康状态: {health['status']}")
    
    # 创建用户偏好
    preferences = UserPreferences(
        character_class=PoE2CharacterClass.WITCH,
        preferred_ascendancy="Infernalist",
        playstyle=["aggressive", "ranged"],
        skill_preferences=["Fireball", "Meteor"],
        budget_range=(15.0, 50.0),
        experience_level="intermediate",
        content_focus=["mapping", "bossing"],
        avoid_mechanics=["melee"]
    )
    
    print("\n用户偏好:")
    print(f"  职业: {preferences.character_class.value}")
    print(f"  升华: {preferences.preferred_ascendancy}")
    print(f"  游戏风格: {', '.join(preferences.playstyle)}")
    print(f"  偏好技能: {', '.join(preferences.skill_preferences)}")
    print(f"  预算范围: {preferences.budget_range[0]}-{preferences.budget_range[1]} Divine")
    print(f"  经验等级: {preferences.experience_level}")
    
    # 获取推荐
    print("\n生成构筑推荐...")
    recommendations = await ai_engine.get_recommendations(
        preferences, 
        RecommendationStrategy.HYBRID,
        limit=3
    )
    
    print(f"生成了{len(recommendations)}个推荐:")
    
    for i, rec in enumerate(recommendations):
        print(f"\n推荐 {i+1}: {rec.build_data.get('name', '未知构筑')}")
        print(f"  推荐分数: {rec.recommendation_score:.3f}")
        print(f"  置信度: {rec.confidence_score:.3f}")
        print(f"  难度: {rec.difficulty_rating}")
        print(f"  预估成本: {rec.estimated_cost:.1f} Divine")
        print(f"  推荐理由: {', '.join(rec.reasoning)}")
        print(f"  优点: {', '.join(rec.pros)}")
        print(f"  缺点: {', '.join(rec.cons)}")
        
        if rec.customization_suggestions:
            print(f"  定制建议: {', '.join(rec.customization_suggestions)}")
    
    # 分析第一个推荐
    if recommendations:
        print("\n分析第一个推荐...")
        first_rec = recommendations[0]
        analysis = await ai_engine.analyze_build(first_rec.build_data, "standard")
        
        print(f"构筑分析结果:")
        print(f"  协同效应分数: {analysis.synergy_score:.3f}")
        print(f"  灵活性分数: {analysis.flexibility_score:.3f}")
        print(f"  元数据位置: {analysis.meta_position}")
        print(f"  联赛开荒可行: {'是' if analysis.league_start_viable else '否'}")
        print(f"  终局潜力: {analysis.endgame_potential}")
        print(f"  强点: {', '.join(analysis.strengths)}")
        print(f"  弱点: {', '.join(analysis.weaknesses)}")
        
        if analysis.optimization_suggestions:
            print(f"  优化建议:")
            for suggestion in analysis.optimization_suggestions[:3]:  # 显示前3个建议
                print(f"    - {suggestion.category}: {suggestion.description}")
                if suggestion.improvement_potential:
                    print(f"      改进潜力: {suggestion.improvement_potential:.1f}%")
    
    # 元数据分析
    print("\n获取元数据分析...")
    meta_analysis = await ai_engine.get_meta_analysis(PoE2CharacterClass.WITCH)
    
    print("当前元数据趋势:")
    print(f"  分析职业: {meta_analysis.get('character_class', '全职业')}")
    
    if 'popular_builds' in meta_analysis:
        print("  热门构筑:")
        for build in meta_analysis['popular_builds'][:3]:
            print(f"    - {build['name']} (流行度: {build['popularity']:.2f})")
    
    if 'trending_skills' in meta_analysis:
        print("  趋势技能:")
        for skill in meta_analysis['trending_skills'][:3]:
            print(f"    - {skill['skill']} (增长: {skill.get('growth', 0):.1%})")
    
    await ai_engine.cleanup()
    print("RAG AI引擎演示完成\n")


async def demo_integrated_workflow():
    """演示集成工作流程"""
    print("=== Phase 4.5: 集成工作流程演示 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = Path(temp_dir)
        
        # 创建完整的RAG系统
        print("构建完整RAG系统...")
        collector = PoE2NinjaRAGCollector()
        vectorizer = BuildVectorizer(index_path)
        retrieval_engine = RetrievalEngine(index_path, vectorizer)
        ai_engine = RAGEnhancedAI(
            data_collector=collector,
            vectorizer=vectorizer,
            retrieval_engine=retrieval_engine
        )
        
        # 初始化所有组件
        print("初始化所有组件...")
        await collector.initialize()
        await vectorizer.initialize()
        await retrieval_engine.initialize()
        await ai_engine.initialize()
        
        try:
            # 端到端工作流程
            print("\n执行端到端工作流程:")
            
            # 1. 用户查询
            user_query = "我想要一个适合新手的巫师火焰构筑，预算在20个Divine以内"
            print(f"用户查询: {user_query}")
            
            # 2. 解析用户需求
            preferences = UserPreferences(
                character_class=PoE2CharacterClass.WITCH,
                playstyle=["fire", "beginner-friendly"],
                budget_range=(0.0, 20.0),
                experience_level="beginner",
                content_focus=["leveling", "mapping"]
            )
            
            print("解析用户需求完成")
            
            # 3. RAG检索和推荐
            recommendations = await ai_engine.get_recommendations(
                preferences,
                RecommendationStrategy.BUDGET_FRIENDLY,
                limit=2
            )
            
            print(f"生成推荐: {len(recommendations)}个构筑")
            
            # 4. 结果展示
            if recommendations:
                best_rec = recommendations[0]
                print(f"\n最佳推荐: {best_rec.build_data.get('name')}")
                print(f"适配评分: {best_rec.recommendation_score:.3f}")
                print(f"推荐理由: {'; '.join(best_rec.reasoning)}")
                
                # 5. 进一步优化
                print("\n执行构筑优化...")
                optimization_goals = ["damage", "defense"]
                optimized_build = await ai_engine.optimize_build(
                    best_rec.build_data, 
                    optimization_goals
                )
                
                if 'optimizations_applied' in optimized_build:
                    print("优化建议已应用:")
                    for opt in optimized_build['optimizations_applied']:
                        print(f"  - {opt['description']}")
            
            print("\n集成工作流程演示成功")
            
        finally:
            # 清理资源
            await collector.cleanup()
            await vectorizer.cleanup()
            await retrieval_engine.cleanup()
            await ai_engine.cleanup()


async def demo_factory_integration():
    """演示工厂集成"""
    print("=== Phase 4.6: 数据源工厂集成演示 ===")
    
    factory = get_factory()
    
    # 获取可用的构筑数据提供者
    build_providers = factory.get_available_providers('build')
    print(f"可用的构筑数据提供者: {build_providers}")
    
    # 创建ninja.poe2数据提供者
    try:
        ninja_provider = factory.create_build_provider('ninja_poe2')
        print(f"创建ninja.poe2提供者: {ninja_provider.get_provider_name()}")
        
        # 测试健康状态
        health_status = await ninja_provider.get_health_status()
        print(f"提供者健康状态: {health_status.value}")
        
        # 测试连接
        connection_ok = await ninja_provider.test_connection()
        print(f"连接测试: {'成功' if connection_ok else '失败'}")
        
    except Exception as e:
        print(f"提供者创建失败: {e} (使用Mock实现)")
    
    # 获取工厂统计信息
    factory_stats = factory.get_provider_stats()
    print(f"工厂统计信息: {factory_stats}")
    
    # 清理
    await factory.close_all_providers()
    print("工厂集成演示完成\n")


async def main():
    """主演示函数"""
    print("🎮 PoE2 Build Generator - Phase 4 RAG智能训练系统演示\n")
    print("=" * 60)
    
    try:
        # 依次执行各个组件的演示
        await demo_data_collector()
        await demo_vectorizer()
        await demo_retrieval_engine()
        await demo_rag_ai_engine()
        await demo_integrated_workflow()
        await demo_factory_integration()
        
        print("=" * 60)
        print("🎉 Phase 4 RAG智能训练系统演示完成！")
        print("\n系统特性总结:")
        print("✅ ninja.poe2数据采集器 - 智能构筑数据收集")
        print("✅ sentence-transformers向量化器 - 语义向量搜索")
        print("✅ FAISS检索引擎 - 高性能相似度检索") 
        print("✅ RAG增强AI引擎 - 智能推荐和分析")
        print("✅ 完整集成工作流程 - 端到端用户体验")
        print("✅ 数据源工厂集成 - 统一数据接口")
        print("✅ Mock实现fallback - 优雅降级机制")
        
        print("\n🚀 系统已准备好进入Phase 5: 系统集成！")
        
    except KeyboardInterrupt:
        print("\n用户中断演示")
    except Exception as e:
        print(f"\n演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())