#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试自然语言构建生成功能
"""

import sys
import os
import json
import asyncio

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from poe2build.core.ai_orchestrator import PoE2AIOrchestrator, UserRequest
from poe2build.models.characters import PoE2CharacterClass, PoE2Ascendancy
from poe2build.models.build import PoE2BuildGoal

async def test_natural_language_generation():
    """测试自然语言构建生成"""
    print("="*60)
    print("PoE2 Build Generator - 自然语言构建生成测试")
    print("="*60)
    print()
    
    # 初始化AI编排器
    print("正在初始化AI编排器...")
    orchestrator = PoE2AIOrchestrator()
    await orchestrator.initialize()
    print("[OK] AI编排器初始化完成")
    print()
    
    # 测试用例
    test_cases = [
        {
            "name": "弓箭手新手构筑",
            "request": UserRequest(
                character_class=PoE2CharacterClass.RANGER,
                build_goal=PoE2BuildGoal.LEAGUE_START,
                max_budget=5.0,
                currency_type="divine",
                preferred_skills=["Explosive Shot", "Lightning Arrow"],
                playstyle="balanced"
            )
        },
        {
            "name": "法师终游构筑",
            "request": UserRequest(
                character_class=PoE2CharacterClass.SORCERESS,
                ascendancy=PoE2Ascendancy.STORMWEAVER,
                build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
                max_budget=50.0,
                currency_type="divine",
                preferred_skills=["Fireball", "Meteor"],
                playstyle="aggressive",
                min_dps=500000.0
            )
        },
        {
            "name": "格斗家刷图构筑",
            "request": UserRequest(
                character_class=PoE2CharacterClass.MONK,
                build_goal=PoE2BuildGoal.CLEAR_SPEED,
                max_budget=20.0,
                currency_type="divine",
                preferred_skills=["Martial Arts", "Spirit Wave"],
                playstyle="balanced"
            )
        }
    ]
    
    # 执行测试用例
    for i, test_case in enumerate(test_cases, 1):
        print(f"测试用例 {i}: {test_case['name']}")
        print("-" * 40)
        
        try:
            # 调用构建生成功能
            result = await orchestrator.generate_build_recommendations(test_case["request"])
            
            # 显示结果
            print(f"[OK] 生成成功")
            print(f"推荐数量: {len(result.builds)}")
            
            # 显示前2个推荐
            recommendations = result.builds
            for j, rec in enumerate(recommendations[:2]):
                print(f"  推荐 {j+1}: {rec.name}")
                print(f"    类型: {rec.character_class.value} - {rec.ascendancy.value if rec.ascendancy else 'N/A'}")
                print(f"    技能: {rec.main_skill_gem or 'N/A'}")
                print(f"    预估伤害: {rec.stats.total_dps if rec.stats else 0:,}")
                print(f"    预估成本: {rec.estimated_cost or 0} {rec.currency_type}")
                
                # 显示PoB2集成状态
                if rec.pob2_code:
                    print(f"    PoB2集成: [OK] 可用")
                    print(f"    导入代码: 有 (PoB2版本: {rec.pob2_version or 'Unknown'})")
                else:
                    print(f"    PoB2集成: [WARN] 不可用")
                
                print()
            
            # 显示系统信息
            print(f"响应时间: {result.generation_time_ms}ms")
            print(f"RAG置信度: {result.rag_confidence:.3f}")
            print(f"PoB2验证: {'通过' if result.pob2_validated else '未验证'}")
            print(f"使用组件: {[comp.value for comp in result.used_components]}")
            print()
            
        except Exception as e:
            print(f"[ERROR] 测试失败: {e}")
            import traceback
            traceback.print_exc()
            print()
        
        print("="*60)
        print()
    
    # 健康检查
    print("执行系统健康检查...")
    try:
        health_status = await orchestrator.health_check()
        print("[OK] 系统健康检查完成")
        
        for service, status in health_status.items():
            icon = "[OK]" if status.get("status") == "healthy" else "[WARN]"
            print(f"  {icon} {service}: {status.get('status', 'unknown')}")
            
    except Exception as e:
        print(f"[ERROR] 健康检查失败: {e}")
    
    print()
    print("="*60)
    print("自然语言构建生成测试完成！")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_natural_language_generation())