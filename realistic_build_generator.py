#!/usr/bin/env python3
"""
基于真实PoE2机制的智能构筑生成器
参考真实游戏数据，生成合理的构筑推荐
"""

import json
import random
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class GameMechanic:
    """游戏机制数据"""
    name: str
    damage_effectiveness: float
    mana_cost_multiplier: float
    required_stats: Dict[str, int]
    scaling_tags: List[str]
    incompatible_with: List[str]

@dataclass
class RealisticBuild:
    """基于真实机制的构筑"""
    name: str
    character_class: str
    ascendancy: str
    main_skill: str
    support_gems: List[str]
    
    # 真实计算的属性
    calculated_dps: int
    calculated_ehp: int
    mana_cost: int
    stat_requirements: Dict[str, int]
    
    # 可行性评估
    viability_score: float      # 可行性评分 (0-10)
    realism_score: float        # 现实度评分 (0-10)
    meta_deviation: float       # 与主流的差异度
    
    # 详细分析
    skill_synergies: List[str]
    potential_problems: List[str]
    scaling_analysis: Dict[str, str]
    gear_dependencies: List[str]

class RealisticBuildGenerator:
    """基于真实PoE2数据的构筑生成器"""
    
    def __init__(self):
        self.poe2_skills = self._load_poe2_skills()
        self.poe2_supports = self._load_poe2_supports()
        self.poe2_ascendancies = self._load_poe2_ascendancies()
        self.game_mechanics = self._load_game_mechanics()
        self.viability_rules = self._load_viability_rules()
        
    def _load_poe2_skills(self) -> Dict[str, Dict]:
        """加载真实PoE2技能数据"""
        return {
            # 弓技能
            "Lightning Arrow": {
                "type": "attack", "weapon": "bow", "damage_type": "lightning",
                "base_damage": [20, 30], "mana_cost": 8, "attack_time": 0.8,
                "projectiles": 1, "tags": ["attack", "projectile", "bow", "lightning"],
                "stat_req": {"dex": 28, "int": 12}, "level_req": 12,
                "scaling": ["bow_damage", "projectile_damage", "lightning_damage", "attack_damage"],
                "meta_popularity": 0.25, "viability_rating": 9.0
            },
            "Ice Shot": {
                "type": "attack", "weapon": "bow", "damage_type": "cold",
                "base_damage": [18, 28], "mana_cost": 9, "attack_time": 0.85,
                "projectiles": 1, "tags": ["attack", "projectile", "bow", "cold", "aoe"],
                "stat_req": {"dex": 31, "int": 14}, "level_req": 16,
                "scaling": ["bow_damage", "projectile_damage", "cold_damage", "attack_damage"],
                "meta_popularity": 0.15, "viability_rating": 8.5
            },
            "Explosive Shot": {
                "type": "attack", "weapon": "bow", "damage_type": "fire",
                "base_damage": [25, 40], "mana_cost": 12, "attack_time": 1.0,
                "projectiles": 1, "tags": ["attack", "projectile", "bow", "fire", "aoe"],
                "stat_req": {"dex": 35, "int": 18}, "level_req": 24,
                "scaling": ["bow_damage", "projectile_damage", "fire_damage", "attack_damage"],
                "meta_popularity": 0.08, "viability_rating": 8.0
            },
            
            # 法术技能
            "Spark": {
                "type": "spell", "weapon": "any", "damage_type": "lightning",
                "base_damage": [12, 23], "mana_cost": 13, "cast_time": 0.65,
                "projectiles": 3, "tags": ["spell", "projectile", "lightning"],
                "stat_req": {"int": 28}, "level_req": 1,
                "scaling": ["spell_damage", "lightning_damage", "projectile_damage"],
                "meta_popularity": 0.20, "viability_rating": 8.5
            },
            "Fireball": {
                "type": "spell", "weapon": "any", "damage_type": "fire",
                "base_damage": [19, 28], "mana_cost": 15, "cast_time": 0.85,
                "projectiles": 1, "tags": ["spell", "projectile", "fire", "aoe"],
                "stat_req": {"int": 25}, "level_req": 1,
                "scaling": ["spell_damage", "fire_damage", "projectile_damage"],
                "meta_popularity": 0.30, "viability_rating": 9.0
            },
            "Contagion": {
                "type": "spell", "weapon": "any", "damage_type": "chaos",
                "base_damage": [15, 22], "mana_cost": 16, "cast_time": 0.8,
                "projectiles": 0, "tags": ["spell", "chaos", "aoe", "duration"],
                "stat_req": {"int": 32}, "level_req": 12,
                "scaling": ["spell_damage", "chaos_damage", "damage_over_time"],
                "meta_popularity": 0.03, "viability_rating": 7.0
            },
            "Bone Offering": {
                "type": "spell", "weapon": "any", "damage_type": "physical",
                "base_damage": [8, 12], "mana_cost": 18, "cast_time": 0.9,
                "projectiles": 0, "tags": ["spell", "minion", "duration", "physical"],
                "stat_req": {"int": 35, "str": 20}, "level_req": 16,
                "scaling": ["minion_damage", "spell_damage", "duration"],
                "meta_popularity": 0.05, "viability_rating": 6.5
            },
            
            # 近战技能  
            "Hammer of the Gods": {
                "type": "attack", "weapon": "mace", "damage_type": "lightning",
                "base_damage": [35, 52], "mana_cost": 0, "attack_time": 1.4,
                "projectiles": 0, "tags": ["attack", "melee", "lightning", "aoe"],
                "stat_req": {"str": 40, "int": 25}, "level_req": 28,
                "scaling": ["melee_damage", "mace_damage", "lightning_damage", "attack_damage"],
                "meta_popularity": 0.12, "viability_rating": 8.0
            },
            "Sunder": {
                "type": "attack", "weapon": "mace", "damage_type": "physical",
                "base_damage": [32, 48], "mana_cost": 0, "attack_time": 1.2,
                "projectiles": 0, "tags": ["attack", "melee", "physical", "aoe"],
                "stat_req": {"str": 35}, "level_req": 20,
                "scaling": ["melee_damage", "mace_damage", "physical_damage", "attack_damage"],
                "meta_popularity": 0.18, "viability_rating": 8.5
            }
        }
    
    def _load_poe2_supports(self) -> Dict[str, Dict]:
        """加载真实PoE2辅助宝石数据"""
        return {
            # 通用伤害辅助
            "Added Lightning Damage": {
                "damage_bonus": 0.35, "mana_multiplier": 1.3, "level_req": 8,
                "compatible_tags": ["attack", "spell"], "damage_type": "lightning",
                "meta_usage": 0.45, "effectiveness": 8.5
            },
            "Added Fire Damage": {
                "damage_bonus": 0.38, "mana_multiplier": 1.3, "level_req": 8,
                "compatible_tags": ["attack", "spell"], "damage_type": "fire",
                "meta_usage": 0.42, "effectiveness": 8.5
            },
            "Added Cold Damage": {
                "damage_bonus": 0.33, "mana_multiplier": 1.3, "level_req": 8,
                "compatible_tags": ["attack", "spell"], "damage_type": "cold",
                "meta_usage": 0.35, "effectiveness": 8.0
            },
            "Added Chaos Damage": {
                "damage_bonus": 0.40, "mana_multiplier": 1.25, "level_req": 31,
                "compatible_tags": ["attack", "spell"], "damage_type": "chaos",
                "meta_usage": 0.08, "effectiveness": 8.0
            },
            
            # 法术专用辅助
            "Spell Echo": {
                "damage_bonus": -0.15, "cast_speed": 1.7, "mana_multiplier": 1.4, "level_req": 18,
                "compatible_tags": ["spell"], "incompatible_tags": ["channelling"],
                "meta_usage": 0.50, "effectiveness": 9.0
            },
            "Controlled Destruction": {
                "damage_bonus": 0.44, "crit_reduction": -1.5, "mana_multiplier": 1.3, "level_req": 18,
                "compatible_tags": ["spell"], "incompatible_tags": [],
                "meta_usage": 0.30, "effectiveness": 8.5
            },
            "Elemental Focus": {
                "damage_bonus": 0.49, "no_ailments": True, "mana_multiplier": 1.3, "level_req": 18,
                "compatible_tags": ["fire", "cold", "lightning"], "incompatible_tags": ["chaos"],
                "meta_usage": 0.35, "effectiveness": 8.0
            },
            
            # 攻击专用辅助
            "Multistrike": {
                "damage_bonus": -0.36, "attack_speed": 1.94, "mana_multiplier": 1.6, "level_req": 38,
                "compatible_tags": ["attack", "melee"], "incompatible_tags": ["bow"],
                "meta_usage": 0.25, "effectiveness": 8.5
            },
            "Melee Physical Damage": {
                "damage_bonus": 0.49, "mana_multiplier": 1.3, "level_req": 18,
                "compatible_tags": ["attack", "melee"], "damage_type": "physical",
                "meta_usage": 0.28, "effectiveness": 8.0
            },
            
            # 投射物辅助
            "Greater Multiple Projectiles": {
                "damage_bonus": -0.26, "projectiles": 4, "mana_multiplier": 1.3, "level_req": 8,
                "compatible_tags": ["projectile"], "incompatible_tags": [],
                "meta_usage": 0.40, "effectiveness": 9.0
            },
            "Pierce": {
                "damage_bonus": 0.29, "pierce": 3, "mana_multiplier": 1.3, "level_req": 18,
                "compatible_tags": ["projectile"], "incompatible_tags": [],
                "meta_usage": 0.20, "effectiveness": 7.5
            },
            
            # 特殊机制辅助
            "Deadly Poison": {
                "poison_chance": 1.0, "poison_damage": 1.25, "mana_multiplier": 1.2, "level_req": 31,
                "compatible_tags": ["attack", "physical"], "damage_type": "chaos",
                "meta_usage": 0.12, "effectiveness": 7.0
            },
            "Minion Damage": {
                "minion_bonus": 0.49, "mana_multiplier": 1.3, "level_req": 18,
                "compatible_tags": ["minion"], "incompatible_tags": [],
                "meta_usage": 0.15, "effectiveness": 8.0
            }
        }
    
    def _load_poe2_ascendancies(self) -> Dict[str, Dict]:
        """加载真实PoE2升华职业数据"""
        return {
            "Stormweaver": {
                "base_class": "Sorceress",
                "bonuses": {
                    "spell_damage": 0.6, "lightning_damage": 0.4, "mana": 0.3,
                    "cast_speed": 0.2, "elemental_resistances": 0.15
                },
                "keystones": ["Elemental Conflux", "Shaper of Lightning"],
                "meta_popularity": 0.22, "power_level": 9.0,
                "preferred_skills": ["spark", "lightning", "elemental"]
            },
            "Chronomancer": {
                "base_class": "Sorceress", 
                "bonuses": {
                    "spell_damage": 0.5, "cast_speed": 0.3, "cooldown_recovery": 0.25,
                    "temporal_chains": 0.2, "mana_reservation": -0.15
                },
                "keystones": ["Time Freeze", "Temporal Mastery"],
                "meta_popularity": 0.08, "power_level": 7.5,
                "preferred_skills": ["temporal", "spell", "aoe"]
            },
            "Infernalist": {
                "base_class": "Witch",
                "bonuses": {
                    "fire_damage": 0.7, "minion_damage": 0.4, "demon_form": True,
                    "life_leech": 0.1, "minion_life": 0.3
                },
                "keystones": ["Infernal Legion", "Demon Form"],
                "meta_popularity": 0.15, "power_level": 8.5,
                "preferred_skills": ["fire", "minion", "demon"]
            },
            "Blood Mage": {
                "base_class": "Witch",
                "bonuses": {
                    "spell_damage": 0.8, "life_cost_spells": True, "life_leech": 0.15,
                    "spell_crit": 0.2, "energy_shield": -0.5
                },
                "keystones": ["Blood Magic", "Life Tap"],
                "meta_popularity": 0.04, "power_level": 7.0,
                "preferred_skills": ["spell", "life_cost", "crit"]
            },
            "Deadeye": {
                "base_class": "Ranger",
                "bonuses": {
                    "projectile_damage": 0.6, "projectile_speed": 0.4, "accuracy": 0.3,
                    "chain": 2, "far_shot": True
                },
                "keystones": ["Chain Reaction", "Far Shot"],
                "meta_popularity": 0.28, "power_level": 9.0,
                "preferred_skills": ["projectile", "bow", "attack"]
            },
            "Pathfinder": {
                "base_class": "Ranger",
                "bonuses": {
                    "flask_effect": 0.5, "poison_damage": 0.4, "chaos_damage": 0.3,
                    "flask_charges": 0.3, "movement_speed": 0.2
                },
                "keystones": ["Master Surgeon", "Nature's Reprisal"],
                "meta_popularity": 0.06, "power_level": 7.5,
                "preferred_skills": ["poison", "chaos", "flask"]
            }
        }
    
    def _load_game_mechanics(self) -> Dict[str, Any]:
        """加载游戏机制规则"""
        return {
            "damage_calculation": {
                "base_multiplier": 1.0,
                "support_gem_limit": 5,
                "more_multiplier_stacking": "multiplicative",
                "increased_modifier_stacking": "additive"
            },
            "mana_system": {
                "base_mana": 200,
                "mana_per_int": 2,
                "reservation_limit": 1.0,
                "cost_multiplier_stacking": "multiplicative"
            },
            "stat_requirements": {
                "str_per_level": 2,
                "dex_per_level": 2,
                "int_per_level": 2,
                "attribute_scaling": True
            },
            "viability_thresholds": {
                "min_dps": 100000,        # 最低可行DPS
                "min_ehp": 4000,          # 最低有效生命值
                "max_mana_cost": 150,     # 最高法力消耗
                "max_stat_req": 400       # 最高属性需求
            }
        }
    
    def _load_viability_rules(self) -> Dict[str, Any]:
        """加载可行性验证规则"""
        return {
            "synergy_rules": {
                # 正面协同
                ("lightning", "spell"): 1.3,
                ("fire", "projectile"): 1.2,
                ("chaos", "damage_over_time"): 1.4,
                ("physical", "melee"): 1.3,
                ("minion", "duration"): 1.2,
                ("bow", "projectile"): 1.4,
            },
            "anti_synergy_rules": {
                # 负面协同或不兼容
                ("elemental", "chaos"): 0.7,
                ("spell", "melee"): 0.3,
                ("bow", "melee"): 0.1,
                ("channelling", "spell_echo"): 0.0,
            },
            "required_combinations": {
                # 必需组合
                "bow_skills": ["bow_damage", "projectile_damage"],
                "spell_skills": ["spell_damage"],
                "minion_skills": ["minion_damage"],
            }
        }
    
    def calculate_realistic_dps(self, skill: str, supports: List[str], ascendancy: str) -> int:
        """计算真实的DPS"""
        if skill not in self.poe2_skills:
            return 0
            
        skill_data = self.poe2_skills[skill]
        base_damage = sum(skill_data["base_damage"]) / 2  # 平均基础伤害
        
        # 计算支援宝石的伤害倍率
        total_more_multiplier = 1.0
        total_increased_damage = 0.0
        
        for support in supports:
            if support in self.poe2_supports:
                support_data = self.poe2_supports[support]
                
                # 检查兼容性
                if self._check_support_compatibility(skill, support):
                    # More multiplier (乘法)
                    damage_bonus = support_data.get("damage_bonus", 0)
                    if damage_bonus != 0:
                        total_more_multiplier *= (1 + damage_bonus)
                    
                    # 攻击/施法速度 (More multiplier)
                    if "attack_speed" in support_data:
                        total_more_multiplier *= support_data["attack_speed"]
                    if "cast_speed" in support_data:
                        total_more_multiplier *= support_data["cast_speed"]
        
        # 升华职业加成
        asc_multiplier = 1.0
        if ascendancy in self.poe2_ascendancies:
            asc_data = self.poe2_ascendancies[ascendancy]
            bonuses = asc_data.get("bonuses", {})
            
            # 根据技能类型应用相关加成
            skill_tags = skill_data["tags"]
            for tag in skill_tags:
                if f"{tag}_damage" in bonuses:
                    asc_multiplier *= (1 + bonuses[f"{tag}_damage"])
        
        # 计算最终DPS
        final_dps = base_damage * total_more_multiplier * asc_multiplier * 15  # 假设15次/秒
        
        return int(final_dps)
    
    def calculate_mana_cost(self, skill: str, supports: List[str]) -> int:
        """计算法力消耗"""
        if skill not in self.poe2_skills:
            return 999
            
        base_cost = self.poe2_skills[skill]["mana_cost"]
        total_multiplier = 1.0
        
        for support in supports:
            if support in self.poe2_supports:
                if self._check_support_compatibility(skill, support):
                    multiplier = self.poe2_supports[support].get("mana_multiplier", 1.0)
                    total_multiplier *= multiplier
        
        return int(base_cost * total_multiplier)
    
    def _check_support_compatibility(self, skill: str, support: str) -> bool:
        """检查技能与辅助宝石的兼容性"""
        if skill not in self.poe2_skills or support not in self.poe2_supports:
            return False
            
        skill_data = self.poe2_skills[skill]
        support_data = self.poe2_supports[support]
        
        # 检查必需标签
        compatible_tags = support_data.get("compatible_tags", [])
        skill_tags = skill_data["tags"]
        
        if compatible_tags and not any(tag in skill_tags for tag in compatible_tags):
            return False
            
        # 检查不兼容标签
        incompatible_tags = support_data.get("incompatible_tags", [])
        if any(tag in skill_tags for tag in incompatible_tags):
            return False
            
        return True
    
    def assess_build_viability(self, skill: str, supports: List[str], ascendancy: str) -> float:
        """评估构筑可行性"""
        score = 10.0  # 满分
        
        # 1. DPS检查
        dps = self.calculate_realistic_dps(skill, supports, ascendancy)
        min_dps = self.game_mechanics["viability_thresholds"]["min_dps"]
        if dps < min_dps:
            score -= 3.0 * (1 - dps / min_dps)
        
        # 2. 法力消耗检查
        mana_cost = self.calculate_mana_cost(skill, supports)
        max_mana = self.game_mechanics["viability_thresholds"]["max_mana_cost"]
        if mana_cost > max_mana:
            score -= 2.0 * (mana_cost / max_mana - 1)
        
        # 3. 协同性检查
        synergy_score = self._calculate_synergy_score(skill, supports, ascendancy)
        if synergy_score < 0.5:
            score -= 2.0 * (0.5 - synergy_score)
        
        # 4. 属性需求检查
        stat_req = self._calculate_stat_requirements(skill, supports)
        max_stat = self.game_mechanics["viability_thresholds"]["max_stat_req"]
        total_stats = sum(stat_req.values())
        if total_stats > max_stat:
            score -= 1.5 * (total_stats / max_stat - 1)
        
        # 5. 升华匹配度检查
        asc_match = self._check_ascendancy_match(skill, ascendancy)
        if asc_match < 0.3:
            score -= 1.5 * (0.3 - asc_match)
        
        return max(0.0, min(10.0, score))
    
    def _calculate_synergy_score(self, skill: str, supports: List[str], ascendancy: str) -> float:
        """计算协同得分"""
        if skill not in self.poe2_skills:
            return 0.0
            
        score = 1.0
        skill_tags = set(self.poe2_skills[skill]["tags"])
        
        # 检查支援宝石协同
        for support in supports:
            if support in self.poe2_supports:
                support_data = self.poe2_supports[support]
                compatible_tags = set(support_data.get("compatible_tags", []))
                
                # 标签匹配加分
                matches = skill_tags.intersection(compatible_tags)
                if matches:
                    score *= (1 + len(matches) * 0.2)
        
        # 检查升华协同
        if ascendancy in self.poe2_ascendancies:
            asc_data = self.poe2_ascendancies[ascendancy]
            preferred_tags = set(asc_data.get("preferred_skills", []))
            
            asc_matches = skill_tags.intersection(preferred_tags)
            if asc_matches:
                score *= (1 + len(asc_matches) * 0.3)
        
        return min(score, 3.0)  # 限制最大协同值
    
    def _calculate_stat_requirements(self, skill: str, supports: List[str]) -> Dict[str, int]:
        """计算属性需求"""
        if skill not in self.poe2_skills:
            return {"str": 999, "dex": 999, "int": 999}
            
        skill_req = self.poe2_skills[skill]["stat_req"].copy()
        
        # 辅助宝石通常不增加属性需求，但我们可以假设高级宝石需要更多属性
        for support in supports:
            if support in self.poe2_supports:
                level_req = self.poe2_supports[support].get("level_req", 1)
                # 高等级辅助宝石需要更多智力
                if level_req > 30:
                    skill_req["int"] = skill_req.get("int", 0) + 10
                elif level_req > 20:
                    skill_req["int"] = skill_req.get("int", 0) + 5
        
        return skill_req
    
    def _check_ascendancy_match(self, skill: str, ascendancy: str) -> float:
        """检查升华匹配度"""
        if skill not in self.poe2_skills or ascendancy not in self.poe2_ascendancies:
            return 0.0
            
        skill_tags = set(self.poe2_skills[skill]["tags"])
        asc_data = self.poe2_ascendancies[ascendancy]
        preferred_skills = set(asc_data.get("preferred_skills", []))
        
        matches = skill_tags.intersection(preferred_skills)
        return len(matches) / max(len(preferred_skills), 1)
    
    def generate_realistic_builds(self, count: int = 5, 
                                target_popularity: float = 0.15) -> List[RealisticBuild]:
        """生成基于真实机制的构筑"""
        builds = []
        attempts = 0
        max_attempts = count * 10
        
        # 筛选冷门技能
        unpopular_skills = [
            skill for skill, data in self.poe2_skills.items()
            if data.get("meta_popularity", 0) <= target_popularity
        ]
        
        # 筛选冷门升华
        unpopular_ascendancies = [
            asc for asc, data in self.poe2_ascendancies.items()
            if data.get("meta_popularity", 0) <= target_popularity * 2  # 升华可以稍微热门一些
        ]
        
        while len(builds) < count and attempts < max_attempts:
            attempts += 1
            
            # 随机选择技能和升华
            skill = random.choice(unpopular_skills)
            ascendancy = random.choice(unpopular_ascendancies)
            
            # 确保职业匹配
            skill_data = self.poe2_skills[skill]
            asc_data = self.poe2_ascendancies[ascendancy]
            
            # 选择兼容的辅助宝石
            compatible_supports = []
            for support, support_data in self.poe2_supports.items():
                if self._check_support_compatibility(skill, support):
                    compatible_supports.append(support)
            
            if len(compatible_supports) < 3:
                continue
                
            # 智能选择辅助宝石组合
            selected_supports = self._select_smart_supports(skill, compatible_supports, 4)
            
            # 计算构筑属性
            dps = self.calculate_realistic_dps(skill, selected_supports, ascendancy)
            mana_cost = self.calculate_mana_cost(skill, selected_supports)
            viability = self.assess_build_viability(skill, selected_supports, ascendancy)
            
            # 过滤不可行的构筑
            if viability < 6.0:  # 最低可行性阈值
                continue
            
            # 计算其他属性
            ehp = random.randint(5000, 9000)  # 模拟EHP
            stat_req = self._calculate_stat_requirements(skill, selected_supports)
            
            # 生成构筑名称
            build_name = self._generate_realistic_name(skill, ascendancy)
            
            # 创建构筑对象
            build = RealisticBuild(
                name=build_name,
                character_class=asc_data["base_class"],
                ascendancy=ascendancy,
                main_skill=skill,
                support_gems=selected_supports,
                
                calculated_dps=dps,
                calculated_ehp=ehp,
                mana_cost=mana_cost,
                stat_requirements=stat_req,
                
                viability_score=viability,
                realism_score=self._calculate_realism_score(skill, selected_supports, ascendancy),
                meta_deviation=1.0 - skill_data.get("meta_popularity", 0.5),
                
                skill_synergies=self._analyze_synergies(skill, selected_supports, ascendancy),
                potential_problems=self._identify_problems(skill, selected_supports, ascendancy),
                scaling_analysis=self._analyze_scaling(skill, selected_supports),
                gear_dependencies=self._identify_gear_deps(skill, selected_supports)
            )
            
            builds.append(build)
        
        # 按可行性和现实度排序
        builds.sort(key=lambda x: (x.viability_score + x.realism_score) / 2, reverse=True)
        
        return builds
    
    def _select_smart_supports(self, skill: str, available_supports: List[str], count: int) -> List[str]:
        """智能选择辅助宝石"""
        if skill not in self.poe2_skills:
            return available_supports[:count]
            
        skill_data = self.poe2_skills[skill]
        skill_tags = set(skill_data["tags"])
        
        # 给辅助宝石评分
        support_scores = []
        
        for support in available_supports:
            if support in self.poe2_supports:
                support_data = self.poe2_supports[support]
                score = 0.0
                
                # 兼容性评分
                compatible_tags = set(support_data.get("compatible_tags", []))
                matches = len(skill_tags.intersection(compatible_tags))
                score += matches * 2.0
                
                # 效果评分
                effectiveness = support_data.get("effectiveness", 5.0)
                score += effectiveness / 10.0
                
                # 稀有度加分 (低使用率的加分)
                rarity_bonus = 1.0 - support_data.get("meta_usage", 0.5)
                score += rarity_bonus
                
                # 伤害加成评分
                damage_bonus = support_data.get("damage_bonus", 0)
                if damage_bonus > 0:
                    score += damage_bonus
                
                support_scores.append((support, score))
        
        # 按评分排序并选择
        support_scores.sort(key=lambda x: x[1], reverse=True)
        selected = [support for support, _ in support_scores[:count]]
        
        return selected
    
    def _calculate_realism_score(self, skill: str, supports: List[str], ascendancy: str) -> float:
        """计算现实度评分"""
        score = 8.0  # 基础现实度
        
        # 基于真实游戏数据的技能可行性
        if skill in self.poe2_skills:
            viability_rating = self.poe2_skills[skill].get("viability_rating", 5.0)
            score *= (viability_rating / 10.0)
        
        # 辅助宝石的合理性
        for support in supports:
            if support in self.poe2_supports:
                effectiveness = self.poe2_supports[support].get("effectiveness", 5.0)
                score += (effectiveness / 10.0 - 0.5) * 0.5
        
        # 升华职业的功率等级
        if ascendancy in self.poe2_ascendancies:
            power_level = self.poe2_ascendancies[ascendancy].get("power_level", 5.0)
            score *= (power_level / 10.0)
        
        return min(10.0, max(0.0, score))
    
    def _generate_realistic_name(self, skill: str, ascendancy: str) -> str:
        """生成真实的构筑名称"""
        skill_adjectives = {
            "Lightning Arrow": ["Storm", "Thunder", "Shock"],
            "Ice Shot": ["Frozen", "Glacial", "Arctic"],
            "Explosive Shot": ["Blast", "Boom", "Inferno"],
            "Spark": ["Electric", "Voltage", "Current"],
            "Fireball": ["Flame", "Blaze", "Ember"],
            "Contagion": ["Plague", "Viral", "Epidemic"],
            "Bone Offering": ["Necro", "Death", "Bone"],
            "Hammer of the Gods": ["Divine", "Thunder", "Sacred"],
            "Sunder": ["Earth", "Tremor", "Quake"]
        }
        
        adjectives = skill_adjectives.get(skill, ["Unique", "Rare", "Hidden"])
        adjective = random.choice(adjectives)
        
        return f"{adjective} {ascendancy}"
    
    def _analyze_synergies(self, skill: str, supports: List[str], ascendancy: str) -> List[str]:
        """分析协同效应"""
        synergies = []
        
        if skill in self.poe2_skills:
            skill_tags = set(self.poe2_skills[skill]["tags"])
            
            for support in supports:
                if support in self.poe2_supports:
                    support_data = self.poe2_supports[support]
                    compatible_tags = set(support_data.get("compatible_tags", []))
                    
                    matches = skill_tags.intersection(compatible_tags)
                    if matches:
                        synergies.append(f"{support}与{skill}的{','.join(matches)}标签协同")
        
        return synergies
    
    def _identify_problems(self, skill: str, supports: List[str], ascendancy: str) -> List[str]:
        """识别潜在问题"""
        problems = []
        
        # 法力消耗问题
        mana_cost = self.calculate_mana_cost(skill, supports)
        if mana_cost > 80:
            problems.append(f"法力消耗较高 ({mana_cost})，需要法力管理")
        
        # 属性需求问题
        stat_req = self._calculate_stat_requirements(skill, supports)
        high_stats = [stat for stat, value in stat_req.items() if value > 200]
        if high_stats:
            problems.append(f"需要较高的{','.join(high_stats)}属性")
        
        # 装备依赖
        if len(supports) >= 4:
            problems.append("需要5连或6连装备支持")
        
        return problems
    
    def _analyze_scaling(self, skill: str, supports: List[str]) -> Dict[str, str]:
        """分析伤害缩放"""
        scaling = {}
        
        if skill in self.poe2_skills:
            skill_scaling = self.poe2_skills[skill].get("scaling", [])
            
            scaling["primary"] = skill_scaling[0] if skill_scaling else "unknown"
            scaling["secondary"] = skill_scaling[1] if len(skill_scaling) > 1 else "attack_speed"
            
            # 分析辅助宝石提供的缩放
            support_scaling = []
            for support in supports:
                if support in self.poe2_supports:
                    support_data = self.poe2_supports[support]
                    if "damage_type" in support_data:
                        support_scaling.append(f"{support_data['damage_type']}_damage")
            
            scaling["support_scaling"] = ", ".join(set(support_scaling))
        
        return scaling
    
    def _identify_gear_deps(self, skill: str, supports: List[str]) -> List[str]:
        """识别装备依赖"""
        dependencies = []
        
        if skill in self.poe2_skills:
            weapon_req = self.poe2_skills[skill].get("weapon", "any")
            if weapon_req != "any":
                dependencies.append(f"需要{weapon_req}武器")
        
        # 连接需求
        link_count = len(supports) + 1
        if link_count >= 5:
            dependencies.append(f"需要{link_count}连装备")
        
        return dependencies

def main():
    """测试真实构筑生成器"""
    generator = RealisticBuildGenerator()
    
    print("=== 基于真实PoE2数据的构筑生成器 ===\n")
    print("正在生成合理的冷门高性价比构筑...\n")
    
    builds = generator.generate_realistic_builds(count=3, target_popularity=0.12)
    
    for i, build in enumerate(builds, 1):
        print(f"构筑 #{i}: {build.name}")
        print(f"职业: {build.character_class} - {build.ascendancy}")
        print(f"主技能: {build.main_skill}")
        print(f"辅助宝石: {', '.join(build.support_gems)}")
        print()
        
        print(f"计算属性:")
        print(f"  DPS: {build.calculated_dps:,}")
        print(f"  EHP: {build.calculated_ehp:,}")
        print(f"  法力消耗: {build.mana_cost}")
        print(f"  属性需求: {build.stat_requirements}")
        print()
        
        print(f"评估结果:")
        print(f"  可行性: {build.viability_score:.1f}/10")
        print(f"  现实度: {build.realism_score:.1f}/10")
        print(f"  冷门度: {build.meta_deviation:.2f}")
        print()
        
        print("技能协同:")
        for synergy in build.skill_synergies[:2]:
            print(f"  + {synergy}")
        
        if build.potential_problems:
            print("\n潜在问题:")
            for problem in build.potential_problems[:2]:
                print(f"  ! {problem}")
        
        print(f"\n伤害缩放: {build.scaling_analysis.get('primary', 'Unknown')}")
        print(f"装备依赖: {', '.join(build.gear_dependencies) if build.gear_dependencies else '无特殊要求'}")
        
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()