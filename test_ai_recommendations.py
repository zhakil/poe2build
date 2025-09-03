#!/usr/bin/env python3
"""
测试AI构筑推荐系统
"""

from ai_build_recommender import AIBuildRecommender
from dynamic_data_crawlers import PoENinjaCrawler

def test_ai_recommendations():
    """测试AI推荐系统"""
    print("=== AI构筑推荐系统测试 ===\n")
    
    # 初始化AI推荐器
    ai_recommender = AIBuildRecommender()
    
    print("1. 生成独特冷门构筑...")
    unique_builds = ai_recommender.generate_unique_combinations(count=3)
    
    for i, build in enumerate(unique_builds, 1):
        print(f"\n推荐 #{i}: {build.name}")
        print(f"职业: {build.character_class} - {build.ascendancy}")
        print(f"主技能: {build.skill_combination.main_skill}")
        print(f"支援宝石: {build.skill_combination.support_gems[:3]}")
        print(f"创新度评分: {build.innovation_score:.2f}/1.0")
        print(f"协同度评分: {build.skill_combination.synergy_score:.2f}")
        print(f"预测DPS: {build.estimated_performance['dps']:,}")
        print(f"预计成本: {build.cost_prediction['mid_league']:.1f} Divine Orbs")
        print(f"风险等级: {build.risk_assessment:.2f}")
        
        print("\n独特之处:")
        for reason in build.why_unique[:2]:
            print(f"  - {reason}")
            
        print("\n优化建议:")
        for path in build.optimization_paths[:2]:
            print(f"  - {path}")
            
        if build.potential_issues:
            print("\n潜在问题:")
            for issue in build.potential_issues[:2]:
                print(f"  - {issue}")
    
    print("\n" + "="*60)
    
    # 测试与现有系统的集成
    print("\n2. 测试与PoE Ninja爬虫的集成...")
    ninja_crawler = PoENinjaCrawler()
    builds = ninja_crawler.crawl_meta_builds()
    
    print(f"获取到 {len(builds)} 个构筑（包含AI生成的）")
    
    ai_generated = [b for b in builds if hasattr(b, 'playstyle') and 'AI Generated' in str(b.playstyle)]
    print(f"其中AI生成构筑: {len(ai_generated)} 个")
    
    if ai_generated:
        print("\nAI生成构筑示例:")
        sample = ai_generated[0]
        print(f"名称: {sample.name}")
        print(f"主技能: {sample.main_skill}")
        print(f"流行度: {sample.popularity:.1%} (创新构筑)")
        print(f"预测DPS: {sample.estimated_dps:,}")
        if hasattr(sample, 'cost_analysis') and sample.cost_analysis:
            mid_cost = sample.cost_analysis.get('mid_league', 'Unknown')
            print(f"构筑成本: {mid_cost} Divine Orbs")
    
    print("\n=== 测试完成 ===")

def demonstrate_ai_features():
    """演示AI推荐系统的特色功能"""
    print("\n=== AI系统特色功能演示 ===\n")
    
    ai = AIBuildRecommender()
    
    # 1. 技能协同分析
    print("1. 技能协同度分析:")
    test_combinations = [
        ("Spark", ["Added Chaos Damage", "Spell Echo"]),
        ("Lightning Tendrils", ["Controlled Destruction", "Added Lightning Damage"]),
        ("Contagion", ["Void Manipulation", "Swift Affliction"])
    ]
    
    for skill, supports in test_combinations:
        synergy = ai.analyze_skill_synergy(skill, supports)
        print(f"   {skill} + {supports}: {synergy:.2f} 协同度")
    
    # 2. 创新度计算
    print("\n2. 构筑创新度评估:")
    test_builds = [
        ("Spark", ["Added Lightning Damage"], "Stormweaver"),  # 主流
        ("Contagion", ["Void Manipulation"], "Blood Mage"),    # 冷门
        ("Lightning Tendrils", ["Added Chaos Damage"], "Chronomancer")  # 极冷门
    ]
    
    for skill, supports, ascendancy in test_builds:
        innovation = ai.calculate_innovation_score(skill, supports, ascendancy)
        print(f"   {skill} {ascendancy}: {innovation:.2f} 创新度")
    
    print("\n3. AI自动推荐 (实时生成):")
    fresh_builds = ai.generate_unique_combinations(count=2)
    
    for build in fresh_builds:
        print(f"   构筑: {build.name}")
        print(f"   技能组合: {build.skill_combination.main_skill} + {build.skill_combination.support_gems[:2]}")
        print(f"   AI评级: 创新 {build.innovation_score:.2f} | 协同 {build.skill_combination.synergy_score:.2f}")
        print()

if __name__ == "__main__":
    test_ai_recommendations()
    demonstrate_ai_features()