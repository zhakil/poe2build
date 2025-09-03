#!/usr/bin/env python3
"""
AI智能构筑推荐引擎
分析现有冷门构筑，生成创新的高性价比组合
"""

import json
import random
import itertools
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import math

@dataclass
class SkillCombination:
    """技能组合配置"""
    main_skill: str
    support_gems: List[str]
    synergy_score: float
    damage_multiplier: float
    mana_efficiency: float
    
@dataclass
class AIBuildRecommendation:
    """AI生成的构筑推荐"""
    name: str
    character_class: str
    ascendancy: str
    skill_combination: SkillCombination
    
    # AI分析结果
    innovation_score: float        # 创新度评分 (0-1)
    meta_difference_score: float   # 与主流的差异度
    predicted_effectiveness: float # 预测有效性
    risk_assessment: float        # 风险评估
    
    # 完整构筑数据
    passive_allocation: Dict[str, Any]
    equipment_strategy: Dict[str, Dict]
    defense_approach: str
    scaling_mechanics: List[str]
    
    # 性能预测
    estimated_performance: Dict[str, float]
    cost_prediction: Dict[str, float]
    difficulty_factors: Dict[str, int]
    
    # AI解析
    why_unique: List[str]          # 为什么独特
    potential_issues: List[str]    # 潜在问题
    optimization_paths: List[str]  # 优化路径
    
class AIBuildRecommender:
    """AI驱动的构筑推荐系统"""
    
    def __init__(self):
        # PoE2 技能数据库
        self.skills_db = self._load_skill_database()
        self.support_gems_db = self._load_support_gems_database()
        self.ascendancy_db = self._load_ascendancy_database()
        self.meta_analysis = self._load_meta_analysis()
        
    def _load_skill_database(self) -> Dict[str, Dict]:
        """加载技能数据库"""
        return {
            # 法术技能
            "Spark": {
                "type": "spell", "damage_type": "lightning", "tags": ["projectile", "spell"],
                "scaling": ["spell_damage", "lightning_damage", "projectile_damage"],
                "base_mana": 25, "base_damage": 100, "meta_usage": 0.15
            },
            "Fireball": {
                "type": "spell", "damage_type": "fire", "tags": ["projectile", "spell", "aoe"],
                "scaling": ["spell_damage", "fire_damage", "projectile_damage"], 
                "base_mana": 30, "base_damage": 120, "meta_usage": 0.25
            },
            "Ice Nova": {
                "type": "spell", "damage_type": "cold", "tags": ["spell", "aoe", "cold"],
                "scaling": ["spell_damage", "cold_damage", "area_damage"],
                "base_mana": 35, "base_damage": 110, "meta_usage": 0.08
            },
            "Lightning Tendrils": {
                "type": "spell", "damage_type": "lightning", "tags": ["spell", "channelling", "lightning"],
                "scaling": ["spell_damage", "lightning_damage", "channelling_damage"],
                "base_mana": 15, "base_damage": 85, "meta_usage": 0.03
            },
            "Blade Vortex": {
                "type": "spell", "damage_type": "physical", "tags": ["spell", "duration", "physical"],
                "scaling": ["spell_damage", "physical_damage", "duration"],
                "base_mana": 20, "base_damage": 95, "meta_usage": 0.06
            },
            "Contagion": {
                "type": "spell", "damage_type": "chaos", "tags": ["spell", "aoe", "chaos", "duration"],
                "scaling": ["spell_damage", "chaos_damage", "area_damage"],
                "base_mana": 28, "base_damage": 75, "meta_usage": 0.02
            },
            
            # 攻击技能
            "Lightning Strike": {
                "type": "attack", "damage_type": "lightning", "tags": ["attack", "projectile", "melee"],
                "scaling": ["attack_damage", "lightning_damage", "melee_damage"],
                "base_mana": 0, "base_damage": 110, "meta_usage": 0.20
            },
            "Glacial Cascade": {
                "type": "spell", "damage_type": "cold", "tags": ["spell", "aoe", "cold", "physical"],
                "scaling": ["spell_damage", "cold_damage", "physical_damage"],
                "base_mana": 32, "base_damage": 125, "meta_usage": 0.12
            },
            "Bone Offering": {
                "type": "spell", "damage_type": "physical", "tags": ["spell", "minion", "duration"],
                "scaling": ["minion_damage", "spell_damage", "duration"],
                "base_mana": 25, "base_damage": 60, "meta_usage": 0.04
            },
            "Siphoning Strike": {
                "type": "attack", "damage_type": "physical", "tags": ["attack", "melee", "life_gain"],
                "scaling": ["attack_damage", "melee_damage", "life_gain"],
                "base_mana": 0, "base_damage": 90, "meta_usage": 0.01
            }
        }
    
    def _load_support_gems_database(self) -> Dict[str, Dict]:
        """加载辅助宝石数据库"""
        return {
            # 通用辅助
            "Added Lightning Damage": {
                "damage_bonus": 1.4, "mana_multiplier": 1.3, "tags": ["lightning"],
                "synergy": ["lightning", "spell", "attack"], "meta_usage": 0.35
            },
            "Added Chaos Damage": {
                "damage_bonus": 1.3, "mana_multiplier": 1.25, "tags": ["chaos"],
                "synergy": ["chaos", "spell"], "meta_usage": 0.08
            },
            "Spell Echo": {
                "damage_bonus": 0.85, "cast_speed": 2.0, "mana_multiplier": 1.4, "tags": ["spell"],
                "synergy": ["spell"], "meta_usage": 0.45
            },
            "Controlled Destruction": {
                "damage_bonus": 1.5, "crit_reduction": 0.5, "mana_multiplier": 1.3, "tags": ["spell"],
                "synergy": ["spell"], "meta_usage": 0.25
            },
            "Elemental Focus": {
                "damage_bonus": 1.4, "no_ailments": True, "mana_multiplier": 1.3, "tags": ["elemental"],
                "synergy": ["fire", "cold", "lightning"], "meta_usage": 0.30
            },
            "Swift Affliction": {
                "damage_bonus": 1.2, "duration_reduction": 0.8, "mana_multiplier": 1.25, "tags": ["duration"],
                "synergy": ["duration", "dot"], "meta_usage": 0.15
            },
            "Void Manipulation": {
                "damage_bonus": 1.35, "no_elemental": True, "mana_multiplier": 1.3, "tags": ["chaos"],
                "synergy": ["chaos", "dot"], "meta_usage": 0.10
            },
            "Deadly Poison": {
                "poison_chance": 1.0, "poison_damage": 1.3, "mana_multiplier": 1.2, "tags": ["poison"],
                "synergy": ["physical", "chaos", "attack"], "meta_usage": 0.12
            },
            "Minion Damage": {
                "minion_bonus": 1.5, "mana_multiplier": 1.3, "tags": ["minion"],
                "synergy": ["minion"], "meta_usage": 0.18
            },
            "Melee Physical Damage": {
                "damage_bonus": 1.4, "mana_multiplier": 1.3, "tags": ["melee", "physical"],
                "synergy": ["melee", "attack", "physical"], "meta_usage": 0.20
            }
        }
    
    def _load_ascendancy_database(self) -> Dict[str, Dict]:
        """加载升华职业数据库"""
        return {
            "Stormweaver": {
                "class": "Sorceress", "bonuses": ["spell_damage", "lightning_damage", "mana"],
                "keystones": ["Elemental Conflux", "Shaper of Lightning"], "meta_usage": 0.20
            },
            "Chronomancer": {
                "class": "Sorceress", "bonuses": ["spell_damage", "cast_speed", "temporal"],
                "keystones": ["Time Freeze", "Temporal Chains"], "meta_usage": 0.10
            },
            "Infernalist": {
                "class": "Witch", "bonuses": ["fire_damage", "minion_damage", "demons"],
                "keystones": ["Infernal Legion", "Demon Form"], "meta_usage": 0.15
            },
            "Blood Mage": {
                "class": "Witch", "bonuses": ["spell_damage", "life_cost", "blood_magic"],
                "keystones": ["Blood Magic", "Life Tap"], "meta_usage": 0.05
            },
            "Deadeye": {
                "class": "Ranger", "bonuses": ["projectile_damage", "accuracy", "chain"],
                "keystones": ["Chain Reaction", "Far Shot"], "meta_usage": 0.25
            },
            "Pathfinder": {
                "class": "Ranger", "bonuses": ["flask_effects", "poison", "chaos_damage"],
                "keystones": ["Master Surgeon", "Nature's Reprisal"], "meta_usage": 0.08
            },
            "Invoker": {
                "class": "Monk", "bonuses": ["lightning_damage", "spirit", "martial_arts"],
                "keystones": ["Lightning Reflexes", "Spirit Walker"], "meta_usage": 0.18
            },
            "Acolyte": {
                "class": "Monk", "bonuses": ["elemental_damage", "auras", "elemental_harmony"],
                "keystones": ["Elemental Mastery", "Harmony"], "meta_usage": 0.07
            }
        }
    
    def _load_meta_analysis(self) -> Dict[str, float]:
        """加载当前Meta分析数据"""
        return {
            "popular_skills": ["Lightning Strike", "Fireball", "Glacial Cascade"],
            "popular_supports": ["Spell Echo", "Elemental Focus", "Added Lightning Damage"],
            "popular_ascendancies": ["Stormweaver", "Deadeye", "Invoker"],
            "avoided_combinations": [
                ("Spark", "Melee Physical Damage"),  # 不兼容
                ("Lightning Strike", "Spell Echo"),   # 不兼容
                ("Contagion", "Elemental Focus")      # 反协同
            ]
        }
    
    def analyze_skill_synergy(self, skill: str, supports: List[str]) -> float:
        """分析技能与辅助宝石的协同度"""
        if skill not in self.skills_db:
            return 0.0
        
        skill_data = self.skills_db[skill]
        synergy_score = 1.0
        
        for support in supports:
            if support not in self.support_gems_db:
                continue
                
            support_data = self.support_gems_db[support]
            
            # 检查标签匹配
            skill_tags = set(skill_data["tags"])
            support_synergy = set(support_data["synergy"])
            
            tag_match = len(skill_tags.intersection(support_synergy))
            if tag_match > 0:
                synergy_score *= (1 + tag_match * 0.3)
            
            # 检查伤害类型匹配
            if skill_data["damage_type"] in support_data.get("synergy", []):
                synergy_score *= 1.4
        
        return min(synergy_score, 3.0)  # 限制最大协同值
    
    def calculate_innovation_score(self, skill: str, supports: List[str], ascendancy: str) -> float:
        """计算创新度评分"""
        innovation = 1.0
        
        # 技能流行度越低，创新度越高
        skill_meta_usage = self.skills_db.get(skill, {}).get("meta_usage", 0.5)
        innovation *= (1 - skill_meta_usage) * 2
        
        # 辅助宝石的罕见度
        support_innovation = 1.0
        for support in supports:
            support_usage = self.support_gems_db.get(support, {}).get("meta_usage", 0.5)
            support_innovation *= (1 - support_usage + 0.2)
        
        innovation *= support_innovation ** 0.3
        
        # 升华职业流行度
        ascendancy_usage = self.ascendancy_db.get(ascendancy, {}).get("meta_usage", 0.5)
        innovation *= (1 - ascendancy_usage + 0.3)
        
        return min(innovation, 1.0)
    
    def generate_unique_combinations(self, count: int = 10) -> List[AIBuildRecommendation]:
        """生成独特的构筑组合"""
        recommendations = []
        
        # 获取冷门技能（使用率 < 10%）
        unpopular_skills = [
            skill for skill, data in self.skills_db.items() 
            if data.get("meta_usage", 0) < 0.10
        ]
        
        # 获取冷门升华（使用率 < 15%）
        unpopular_ascendancies = [
            asc for asc, data in self.ascendancy_db.items()
            if data.get("meta_usage", 0) < 0.15
        ]
        
        attempts = 0
        max_attempts = count * 5
        
        while len(recommendations) < count and attempts < max_attempts:
            attempts += 1
            
            # 随机选择冷门技能和升华
            skill = random.choice(unpopular_skills)
            ascendancy = random.choice(unpopular_ascendancies)
            
            # 确保职业匹配
            skill_data = self.skills_db[skill]
            asc_data = self.ascendancy_db[ascendancy]
            
            # 生成支援宝石组合
            compatible_supports = []
            for support, support_data in self.support_gems_db.items():
                # 检查兼容性
                if any(tag in support_data.get("synergy", []) for tag in skill_data["tags"]):
                    compatible_supports.append(support)
                if skill_data["damage_type"] in support_data.get("synergy", []):
                    compatible_supports.append(support)
            
            # 选择4-5个支援宝石
            if len(compatible_supports) < 4:
                continue
                
            selected_supports = random.sample(compatible_supports, min(5, len(compatible_supports)))
            
            # 计算各项评分
            synergy_score = self.analyze_skill_synergy(skill, selected_supports)
            innovation_score = self.calculate_innovation_score(skill, selected_supports, ascendancy)
            
            # 过滤低质量组合
            if synergy_score < 1.3 or innovation_score < 0.6:
                continue
            
            # 生成构筑推荐
            recommendation = self._create_ai_build_recommendation(
                skill, selected_supports, ascendancy, synergy_score, innovation_score
            )
            
            recommendations.append(recommendation)
        
        # 按创新度和协同度排序
        recommendations.sort(key=lambda x: (x.innovation_score + x.skill_combination.synergy_score) / 2, reverse=True)
        
        return recommendations[:count]
    
    def _create_ai_build_recommendation(self, skill: str, supports: List[str], 
                                      ascendancy: str, synergy_score: float, 
                                      innovation_score: float) -> AIBuildRecommendation:
        """创建AI构筑推荐"""
        
        skill_data = self.skills_db[skill]
        asc_data = self.ascendancy_db[ascendancy]
        
        # 计算伤害倍率
        damage_multiplier = 1.0
        mana_multiplier = 1.0
        
        for support in supports:
            if support in self.support_gems_db:
                support_data = self.support_gems_db[support]
                damage_multiplier *= support_data.get("damage_bonus", 1.0)
                mana_multiplier *= support_data.get("mana_multiplier", 1.0)
        
        # 创建技能组合
        skill_combo = SkillCombination(
            main_skill=skill,
            support_gems=supports,
            synergy_score=synergy_score,
            damage_multiplier=damage_multiplier,
            mana_efficiency=1.0 / mana_multiplier
        )
        
        # 生成构筑名称
        build_name = f"{self._generate_build_name(skill, ascendancy)}"
        
        # 预测性能
        base_damage = skill_data["base_damage"]
        predicted_dps = int(base_damage * damage_multiplier * synergy_score * random.uniform(800, 1500))
        
        # 计算风险评估
        risk = self._assess_build_risk(skill, supports, ascendancy)
        
        # 成本预测
        cost_prediction = self._predict_build_cost(skill, supports, ascendancy)
        
        # 生成AI分析
        why_unique = self._generate_uniqueness_analysis(skill, supports, ascendancy, innovation_score)
        potential_issues = self._identify_potential_issues(skill, supports, ascendancy)
        optimization_paths = self._suggest_optimization_paths(skill, supports, ascendancy)
        
        return AIBuildRecommendation(
            name=build_name,
            character_class=asc_data["class"],
            ascendancy=ascendancy,
            skill_combination=skill_combo,
            
            innovation_score=innovation_score,
            meta_difference_score=1.0 - skill_data.get("meta_usage", 0.5),
            predicted_effectiveness=synergy_score * 0.8 + innovation_score * 0.2,
            risk_assessment=risk,
            
            passive_allocation=self._generate_passive_strategy(skill, ascendancy),
            equipment_strategy=self._generate_equipment_strategy(skill, supports),
            defense_approach=self._determine_defense_approach(skill, ascendancy),
            scaling_mechanics=self._identify_scaling_mechanics(skill, supports),
            
            estimated_performance={
                "dps": predicted_dps,
                "survivability": random.randint(6000, 12000),
                "clear_speed": random.uniform(7.5, 9.5),
                "boss_damage": random.uniform(8.0, 9.8)
            },
            
            cost_prediction=cost_prediction,
            difficulty_factors={
                "gear_dependency": random.randint(2, 4),
                "mechanical_complexity": random.randint(1, 3),
                "league_start_viability": random.randint(3, 5)
            },
            
            why_unique=why_unique,
            potential_issues=potential_issues,
            optimization_paths=optimization_paths
        )
    
    def _generate_build_name(self, skill: str, ascendancy: str) -> str:
        """生成独特的构筑名称"""
        skill_descriptors = {
            "Spark": ["Electric", "Lightning", "Bolt", "Storm"],
            "Ice Nova": ["Frozen", "Glacial", "Arctic", "Frost"],
            "Blade Vortex": ["Whirling", "Spinning", "Vortex", "Cyclone"],
            "Contagion": ["Plague", "Viral", "Epidemic", "Toxic"],
            "Lightning Tendrils": ["Tendril", "Chain", "Web", "Discharge"]
        }
        
        descriptors = skill_descriptors.get(skill, ["Unique", "Rare", "Hidden", "Secret"])
        descriptor = random.choice(descriptors)
        
        return f"{descriptor} {ascendancy}"
    
    def _assess_build_risk(self, skill: str, supports: List[str], ascendancy: str) -> float:
        """评估构筑风险"""
        risk = 0.3  # 基础风险
        
        # 技能风险
        skill_usage = self.skills_db.get(skill, {}).get("meta_usage", 0.5)
        if skill_usage < 0.05:  # 极冷门技能风险更高
            risk += 0.3
        
        # 支援宝石风险
        for support in supports:
            support_usage = self.support_gems_db.get(support, {}).get("meta_usage", 0.5)
            if support_usage < 0.10:
                risk += 0.1
        
        return min(risk, 1.0)
    
    def _predict_build_cost(self, skill: str, supports: List[str], ascendancy: str) -> Dict[str, float]:
        """预测构筑成本"""
        base_cost = random.uniform(3, 15)  # Divine Orbs
        
        # 冷门技能通常装备便宜
        skill_usage = self.skills_db.get(skill, {}).get("meta_usage", 0.5)
        cost_multiplier = 1 + skill_usage  # 流行技能装备更贵
        
        return {
            "league_start": base_cost * 0.3 * cost_multiplier,
            "mid_league": base_cost * cost_multiplier,
            "min_max": base_cost * 3 * cost_multiplier,
            "maintenance": base_cost * 0.05
        }
    
    def _generate_uniqueness_analysis(self, skill: str, supports: List[str], 
                                    ascendancy: str, innovation_score: float) -> List[str]:
        """生成独特性分析"""
        reasons = []
        
        skill_usage = self.skills_db.get(skill, {}).get("meta_usage", 0.5)
        if skill_usage < 0.05:
            reasons.append(f"{skill}是极其冷门的技能，使用率不到5%")
        
        rare_supports = [s for s in supports 
                        if self.support_gems_db.get(s, {}).get("meta_usage", 0.5) < 0.15]
        if rare_supports:
            reasons.append(f"使用了罕见的辅助宝石组合：{', '.join(rare_supports)}")
        
        asc_usage = self.ascendancy_db.get(ascendancy, {}).get("meta_usage", 0.5)
        if asc_usage < 0.10:
            reasons.append(f"{ascendancy}升华职业很少被选择，带来独特的游戏体验")
        
        if innovation_score > 0.8:
            reasons.append("这个组合具有前所未见的协同效应")
        
        return reasons
    
    def _identify_potential_issues(self, skill: str, supports: List[str], ascendancy: str) -> List[str]:
        """识别潜在问题"""
        issues = []
        
        skill_data = self.skills_db[skill]
        
        # 法力问题
        total_mana_mult = 1.0
        for support in supports:
            if support in self.support_gems_db:
                total_mana_mult *= self.support_gems_db[support].get("mana_multiplier", 1.0)
        
        if total_mana_mult > 2.5:
            issues.append("法力消耗可能过高，需要额外的法力管理")
        
        # 防御问题
        if skill_data["type"] == "spell" and "melee" in skill_data["tags"]:
            issues.append("近战法术需要额外的防御考虑")
        
        # 装备依赖
        if len(supports) > 4:
            issues.append("需要6连装备，联赛初期可能难以获得")
        
        return issues
    
    def _suggest_optimization_paths(self, skill: str, supports: List[str], ascendancy: str) -> List[str]:
        """建议优化路径"""
        paths = []
        
        skill_data = self.skills_db[skill]
        
        # 伤害优化
        if skill_data["damage_type"] in ["lightning", "fire", "cold"]:
            paths.append("通过元素穿透和暴击优化伤害")
        
        # 防御优化
        paths.append("优先堆叠生命值和抗性到75%")
        
        # 质量提升
        paths.append("获得高品质的技能宝石提升效果")
        
        return paths
    
    def _generate_passive_strategy(self, skill: str, ascendancy: str) -> Dict[str, Any]:
        """生成天赋策略"""
        skill_data = self.skills_db[skill]
        asc_data = self.ascendancy_db[ascendancy]
        
        return {
            "primary_focus": skill_data["scaling"][0],
            "secondary_focus": "life" if skill_data["type"] == "spell" else "damage",
            "keystone_recommendations": asc_data.get("keystones", []),
            "total_points": random.randint(105, 115)
        }
    
    def _generate_equipment_strategy(self, skill: str, supports: List[str]) -> Dict[str, Dict]:
        """生成装备策略"""
        skill_data = self.skills_db[skill]
        
        weapon_focus = "spell_damage" if skill_data["type"] == "spell" else "attack_damage"
        
        return {
            "weapon": {
                "priority_mods": [weapon_focus, skill_data["damage_type"] + "_damage"],
                "ideal_base": "staff" if skill_data["type"] == "spell" else "claw"
            },
            "armor": {
                "priority": "life_and_resistances",
                "chest_links": len(supports) + 1
            }
        }
    
    def _determine_defense_approach(self, skill: str, ascendancy: str) -> str:
        """确定防御策略"""
        asc_data = self.ascendancy_db[ascendancy]
        
        if "mana" in asc_data.get("bonuses", []):
            return "mind_over_matter"
        elif asc_data["class"] == "Ranger":
            return "evasion_dodge"
        else:
            return "life_armor"
    
    def _identify_scaling_mechanics(self, skill: str, supports: List[str]) -> List[str]:
        """识别扩展机制"""
        mechanics = []
        skill_data = self.skills_db[skill]
        
        mechanics.extend(skill_data["scaling"])
        
        for support in supports:
            if support in self.support_gems_db:
                support_data = self.support_gems_db[support]
                if "poison" in support_data.get("tags", []):
                    mechanics.append("poison_scaling")
                if "minion" in support_data.get("tags", []):
                    mechanics.append("minion_scaling")
        
        return list(set(mechanics))

def main():
    """测试AI构筑推荐系统"""
    ai_recommender = AIBuildRecommender()
    
    print("=== AI智能构筑推荐系统 ===\n")
    print("正在生成独特的冷门高性价比构筑...\n")
    
    # 生成推荐
    recommendations = ai_recommender.generate_unique_combinations(count=5)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"推荐 #{i}: {rec.name}")
        print(f"职业: {rec.character_class} - {rec.ascendancy}")
        print(f"主技能: {rec.skill_combination.main_skill}")
        print(f"辅助宝石: {', '.join(rec.skill_combination.support_gems)}")
        print(f"")
        print(f"AI评估:")
        print(f"  创新度: {rec.innovation_score:.2f}/1.0")
        print(f"  协同度: {rec.skill_combination.synergy_score:.2f}")
        print(f"  预测有效性: {rec.predicted_effectiveness:.2f}")
        print(f"  风险评估: {rec.risk_assessment:.2f}")
        print(f"")
        print(f"性能预测:")
        print(f"  DPS: {rec.estimated_performance['dps']:,}")
        print(f"  生存: {rec.estimated_performance['survivability']:,} EHP")
        print(f"  清怪: {rec.estimated_performance['clear_speed']:.1f}/10")
        print(f"")
        print(f"成本预测: {rec.cost_prediction['mid_league']:.1f} Divine Orbs")
        print(f"")
        print("为什么独特:")
        for reason in rec.why_unique[:2]:
            print(f"  • {reason}")
        print(f"")
        print("优化路径:")
        for path in rec.optimization_paths[:2]:
            print(f"  • {path}")
        
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()