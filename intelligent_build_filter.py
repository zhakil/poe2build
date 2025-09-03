#!/usr/bin/env python3
"""
智能构筑过滤与优化系统
基于真实PoE2数据，过滤掉不靠谱的构筑组合
"""

from realistic_build_generator import RealisticBuildGenerator, RealisticBuild
from typing import List, Dict, Any, Tuple
import math

class IntelligentBuildFilter:
    """智能构筑过滤器"""
    
    def __init__(self):
        self.generator = RealisticBuildGenerator()
        self.filter_rules = self._load_filter_rules()
        self.optimization_rules = self._load_optimization_rules()
    
    def _load_filter_rules(self) -> Dict[str, Any]:
        """加载过滤规则"""
        return {
            # 严重问题（直接淘汰）
            "critical_issues": {
                "invalid_weapon_skill": [
                    # (技能, 不兼容的武器类型)
                    ("Lightning Arrow", "mace"),
                    ("Ice Shot", "mace"),
                    ("Explosive Shot", "mace"),
                    ("Hammer of the Gods", "bow"),
                    ("Sunder", "bow")
                ],
                "impossible_combinations": [
                    # (技能类型, 不兼容的辅助)
                    ("attack", "Controlled Destruction"),  # 攻击技能不能用法术辅助
                    ("spell", "Multistrike"),             # 法术不能用攻击辅助
                    ("bow", "Melee Physical Damage"),     # 弓不能用近战辅助
                    ("channelling", "Spell Echo")         # 引导技能不能用回响
                ],
                "attribute_impossible": 500,  # 单属性超过500不合理
                "mana_cost_impossible": 200,  # 法力消耗超过200不合理
                "dps_too_low": 500            # DPS低于500不可用
            },
            
            # 严重警告（大幅减分）
            "major_warnings": {
                "poor_ascendancy_match": 0.2,     # 升华匹配度低于0.2
                "excessive_mana_cost": 120,       # 法力消耗过高
                "low_synergy": 0.8,               # 协同度低于0.8
                "attribute_strain": 350           # 单属性超过350
            },
            
            # 一般问题（轻微减分）
            "minor_issues": {
                "suboptimal_supports": 3,         # 超过3个次优辅助
                "gear_dependency": 5,             # 需要5连以上装备
                "level_requirement": 60           # 等级需求过高
            }
        }
    
    def _load_optimization_rules(self) -> Dict[str, Any]:
        """加载优化规则"""
        return {
            # 智能替换规则
            "smart_replacements": {
                # 如果技能是攻击但用了法术辅助，替换为攻击辅助
                ("attack", "Controlled Destruction"): "Melee Physical Damage",
                ("attack", "Spell Echo"): "Multistrike",
                
                # 如果是法术但用了攻击辅助，替换为法术辅助
                ("spell", "Melee Physical Damage"): "Controlled Destruction",
                ("spell", "Multistrike"): "Spell Echo",
                
                # 优化元素组合
                ("fire", "Added Cold Damage"): "Added Fire Damage",
                ("cold", "Added Fire Damage"): "Added Cold Damage",
                ("lightning", "Added Fire Damage"): "Added Lightning Damage"
            },
            
            # 协同优化建议
            "synergy_improvements": {
                "bow_skills": ["Greater Multiple Projectiles", "Pierce", "Added Lightning Damage"],
                "spell_skills": ["Spell Echo", "Controlled Destruction", "Elemental Focus"],
                "chaos_skills": ["Added Chaos Damage", "Void Manipulation", "Deadly Poison"],
                "melee_skills": ["Melee Physical Damage", "Multistrike", "Added Fire Damage"]
            }
        }
    
    def filter_and_optimize_builds(self, builds: List[RealisticBuild], 
                                 target_count: int = 5) -> List[RealisticBuild]:
        """过滤和优化构筑列表"""
        
        print(f"开始过滤 {len(builds)} 个构筑...")
        
        # 第一步：严格过滤
        viable_builds = []
        for build in builds:
            filter_result = self._comprehensive_filter(build)
            if filter_result["viable"]:
                build.viability_score = filter_result["adjusted_score"]
                viable_builds.append(build)
        
        print(f"严格过滤后剩余 {len(viable_builds)} 个可行构筑")
        
        # 第二步：优化构筑
        optimized_builds = []
        for build in viable_builds:
            optimized_build = self._optimize_build(build)
            if optimized_build:
                optimized_builds.append(optimized_build)
        
        print(f"优化后剩余 {len(optimized_builds)} 个构筑")
        
        # 第三步：最终排序和选择
        final_builds = self._rank_and_select(optimized_builds, target_count)
        
        print(f"最终选择 {len(final_builds)} 个最佳构筑")
        
        return final_builds
    
    def _comprehensive_filter(self, build: RealisticBuild) -> Dict[str, Any]:
        """综合过滤评估"""
        score = build.viability_score
        issues = []
        viable = True
        
        # 检查严重问题
        critical_issues = self._check_critical_issues(build)
        if critical_issues:
            viable = False
            issues.extend(critical_issues)
            return {"viable": False, "issues": issues, "adjusted_score": 0.0}
        
        # 检查严重警告
        major_warnings = self._check_major_warnings(build)
        for warning in major_warnings:
            score -= 2.0  # 每个严重警告扣2分
            issues.append(warning)
        
        # 检查一般问题
        minor_issues = self._check_minor_issues(build)
        for issue in minor_issues:
            score -= 0.5  # 每个一般问题扣0.5分
            issues.append(issue)
        
        # 最低可行性阈值
        if score < 5.0:
            viable = False
        
        return {
            "viable": viable,
            "adjusted_score": max(0.0, score),
            "issues": issues
        }
    
    def _check_critical_issues(self, build: RealisticBuild) -> List[str]:
        """检查严重问题"""
        issues = []
        rules = self.filter_rules["critical_issues"]
        
        # 1. 武器技能不匹配
        skill_data = self.generator.poe2_skills.get(build.main_skill, {})
        required_weapon = skill_data.get("weapon", "any")
        
        for skill, incompatible_weapon in rules["invalid_weapon_skill"]:
            if build.main_skill == skill:
                # 这里简化检查，实际应该检查构筑指定的武器类型
                if required_weapon != "any" and required_weapon != incompatible_weapon:
                    continue  # 实际是正确的
                else:
                    issues.append(f"{skill}与{incompatible_weapon}武器不兼容")
        
        # 2. 不可能的技能-辅助组合
        skill_type = skill_data.get("type", "unknown")
        skill_tags = set(skill_data.get("tags", []))
        
        for incompatible_type, support in rules["impossible_combinations"]:
            if (incompatible_type in skill_tags or skill_type == incompatible_type) and support in build.support_gems:
                issues.append(f"{build.main_skill}({incompatible_type})不能使用{support}")
        
        # 3. 属性需求不可能
        for attr, value in build.stat_requirements.items():
            if value > rules["attribute_impossible"]:
                issues.append(f"{attr}需求过高: {value}")
        
        # 4. 法力消耗不可能
        if build.mana_cost > rules["mana_cost_impossible"]:
            issues.append(f"法力消耗过高: {build.mana_cost}")
        
        # 5. DPS过低
        if build.calculated_dps < rules["dps_too_low"]:
            issues.append(f"DPS过低: {build.calculated_dps}")
        
        return issues
    
    def _check_major_warnings(self, build: RealisticBuild) -> List[str]:
        """检查严重警告"""
        warnings = []
        rules = self.filter_rules["major_warnings"]
        
        # 升华匹配度检查
        match_score = self.generator._check_ascendancy_match(build.main_skill, build.ascendancy)
        if match_score < rules["poor_ascendancy_match"]:
            warnings.append(f"升华{build.ascendancy}与技能{build.main_skill}匹配度很低")
        
        # 法力消耗检查
        if build.mana_cost > rules["excessive_mana_cost"]:
            warnings.append(f"法力消耗偏高: {build.mana_cost}")
        
        # 协同度检查
        synergy = self.generator._calculate_synergy_score(build.main_skill, build.support_gems, build.ascendancy)
        if synergy < rules["low_synergy"]:
            warnings.append(f"技能协同度较低: {synergy:.2f}")
        
        # 属性需求检查
        for attr, value in build.stat_requirements.items():
            if value > rules["attribute_strain"]:
                warnings.append(f"{attr}需求较高: {value}")
        
        return warnings
    
    def _check_minor_issues(self, build: RealisticBuild) -> List[str]:
        """检查一般问题"""
        issues = []
        rules = self.filter_rules["minor_issues"]
        
        # 连接需求
        if len(build.support_gems) + 1 >= rules["gear_dependency"]:
            issues.append(f"需要{len(build.support_gems) + 1}连装备")
        
        return issues
    
    def _optimize_build(self, build: RealisticBuild) -> RealisticBuild:
        """优化单个构筑"""
        optimized_build = build  # 先复制原构筑
        
        # 智能替换不兼容的辅助宝石
        optimized_supports = self._smart_replace_supports(build.main_skill, build.support_gems)
        
        if optimized_supports != build.support_gems:
            # 重新计算优化后的属性
            new_dps = self.generator.calculate_realistic_dps(build.main_skill, optimized_supports, build.ascendancy)
            new_mana = self.generator.calculate_mana_cost(build.main_skill, optimized_supports)
            new_viability = self.generator.assess_build_viability(build.main_skill, optimized_supports, build.ascendancy)
            
            # 创建新的优化构筑
            optimized_build = RealisticBuild(
                name=build.name,
                character_class=build.character_class,
                ascendancy=build.ascendancy,
                main_skill=build.main_skill,
                support_gems=optimized_supports,
                
                calculated_dps=new_dps,
                calculated_ehp=build.calculated_ehp,
                mana_cost=new_mana,
                stat_requirements=build.stat_requirements,
                
                viability_score=new_viability,
                realism_score=build.realism_score,
                meta_deviation=build.meta_deviation,
                
                skill_synergies=build.skill_synergies,
                potential_problems=build.potential_problems,
                scaling_analysis=build.scaling_analysis,
                gear_dependencies=build.gear_dependencies
            )
        
        return optimized_build
    
    def _smart_replace_supports(self, skill: str, supports: List[str]) -> List[str]:
        """智能替换辅助宝石"""
        if skill not in self.generator.poe2_skills:
            return supports
        
        skill_data = self.generator.poe2_skills[skill]
        skill_type = skill_data.get("type", "unknown")
        skill_tags = set(skill_data.get("tags", []))
        damage_type = skill_data.get("damage_type", "physical")
        
        optimized_supports = []
        
        for support in supports:
            # 检查是否需要替换
            replacement = None
            
            # 基于技能类型的替换
            if (skill_type, support) in self.optimization_rules["smart_replacements"]:
                replacement = self.optimization_rules["smart_replacements"][(skill_type, support)]
            
            # 基于伤害类型的替换
            if (damage_type, support) in self.optimization_rules["smart_replacements"]:
                replacement = self.optimization_rules["smart_replacements"][(damage_type, support)]
            
            # 检查兼容性，如果不兼容就寻找替代品
            if not self.generator._check_support_compatibility(skill, support):
                replacement = self._find_compatible_replacement(skill, support)
            
            optimized_supports.append(replacement if replacement else support)
        
        return optimized_supports
    
    def _find_compatible_replacement(self, skill: str, incompatible_support: str) -> str:
        """为不兼容的辅助宝石找到替代品"""
        if skill not in self.generator.poe2_skills:
            return incompatible_support
        
        skill_data = self.generator.poe2_skills[skill]
        skill_tags = set(skill_data.get("tags", []))
        
        # 寻找兼容的替代辅助
        for support, support_data in self.generator.poe2_supports.items():
            if self.generator._check_support_compatibility(skill, support):
                compatible_tags = set(support_data.get("compatible_tags", []))
                
                # 优先选择标签匹配度高的
                if skill_tags.intersection(compatible_tags):
                    return support
        
        # 如果找不到完美替代，返回通用辅助
        universal_supports = ["Added Lightning Damage", "Added Fire Damage", "Added Cold Damage"]
        for support in universal_supports:
            if self.generator._check_support_compatibility(skill, support):
                return support
        
        return incompatible_support  # 找不到替代品就保持原样
    
    def _rank_and_select(self, builds: List[RealisticBuild], target_count: int) -> List[RealisticBuild]:
        """排序并选择最佳构筑"""
        
        # 综合评分函数
        def composite_score(build: RealisticBuild) -> float:
            # 多维度评分
            viability_weight = 0.4      # 可行性权重
            realism_weight = 0.3        # 现实度权重
            uniqueness_weight = 0.2     # 独特性权重
            performance_weight = 0.1    # 性能权重
            
            viability_score = build.viability_score / 10.0
            realism_score = build.realism_score / 10.0
            uniqueness_score = build.meta_deviation
            
            # 性能评分 (DPS和生存能力的平衡)
            dps_score = min(build.calculated_dps / 500000, 1.0)  # DPS上限50万
            ehp_score = min(build.calculated_ehp / 10000, 1.0)   # EHP上限1万
            performance_score = (dps_score + ehp_score) / 2
            
            total_score = (
                viability_score * viability_weight +
                realism_score * realism_weight +
                uniqueness_score * uniqueness_weight +
                performance_score * performance_weight
            )
            
            return total_score
        
        # 按综合评分排序
        builds.sort(key=composite_score, reverse=True)
        
        return builds[:target_count]

def main():
    """测试智能过滤系统"""
    print("=== 智能构筑过滤与优化系统 ===\n")
    
    # 生成原始构筑
    generator = RealisticBuildGenerator()
    raw_builds = generator.generate_realistic_builds(count=10, target_popularity=0.20)
    
    print(f"原始生成了 {len(raw_builds)} 个构筑")
    
    # 应用智能过滤
    filter_system = IntelligentBuildFilter()
    filtered_builds = filter_system.filter_and_optimize_builds(raw_builds, target_count=3)
    
    print(f"\n=== 最终推荐的 {len(filtered_builds)} 个构筑 ===\n")
    
    for i, build in enumerate(filtered_builds, 1):
        print(f"推荐 #{i}: {build.name}")
        print(f"职业: {build.character_class} - {build.ascendancy}")
        print(f"技能: {build.main_skill} + {len(build.support_gems)}个辅助")
        print(f"辅助宝石: {', '.join(build.support_gems[:3])}")
        print()
        
        print(f"计算属性:")
        print(f"  DPS: {build.calculated_dps:,}")
        print(f"  EHP: {build.calculated_ehp:,}")
        print(f"  法力: {build.mana_cost}")
        print()
        
        print(f"质量评估:")
        print(f"  可行性: {build.viability_score:.1f}/10")
        print(f"  现实度: {build.realism_score:.1f}/10")
        print(f"  冷门度: {build.meta_deviation:.2f}")
        print()
        
        if build.skill_synergies:
            print("技能协同:")
            for synergy in build.skill_synergies[:2]:
                print(f"  + {synergy}")
        
        if build.potential_problems:
            print("\n注意事项:")
            for problem in build.potential_problems[:2]:
                print(f"  ! {problem}")
        
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()