#!/usr/bin/env python3
"""
PoE2现实可用数据系统
基于实际可用的数据源提供智能构筑推荐

可用数据源:
✅ PoE2Scout - 市场价格
✅ PoE Ninja - Meta趋势  
✅ 静态游戏数据 - PoE2基础信息
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# PoE2基础游戏数据 (静态数据库)
POE2_SKILL_GEMS = {
    # 弓箭技能
    "Lightning Arrow": {
        "type": "skill", "weapon": "bow", "damage_type": "lightning",
        "tags": ["bow", "projectile", "lightning"], "mana_cost": 12,
        "description": "发射闪电箭矢，击中时会产生连锁闪电"
    },
    "Explosive Shot": {
        "type": "skill", "weapon": "bow", "damage_type": "fire",  
        "tags": ["bow", "projectile", "fire", "area"], "mana_cost": 15,
        "description": "发射爆炸箭矢，击中后爆炸造成范围伤害"
    },
    "Ice Shot": {
        "type": "skill", "weapon": "bow", "damage_type": "cold",
        "tags": ["bow", "projectile", "cold"], "mana_cost": 10,
        "description": "发射寒冰箭矢，击中时冰冻敌人"
    },
    
    # 近战技能  
    "Hammer of the Gods": {
        "type": "skill", "weapon": "mace", "damage_type": "physical",
        "tags": ["melee", "mace", "physical", "slam"], "mana_cost": 20,
        "description": "强力的锤击，造成巨大物理伤害"
    },
    "Bone Spear": {
        "type": "skill", "weapon": "staff", "damage_type": "physical",
        "tags": ["spell", "projectile", "physical"], "mana_cost": 14,
        "description": "发射骨矛穿透敌人"
    },
    
    # 法术技能
    "Ice Nova": {
        "type": "skill", "weapon": "staff", "damage_type": "cold",
        "tags": ["spell", "cold", "area"], "mana_cost": 18,
        "description": "释放寒冰新星，冰冻周围敌人"
    },
    "Fireball": {
        "type": "skill", "weapon": "staff", "damage_type": "fire",
        "tags": ["spell", "fire", "projectile"], "mana_cost": 16,
        "description": "发射火球造成火焰伤害"
    }
}

POE2_CLASSES = {
    "Ranger": {
        "primary_weapons": ["bow", "crossbow"],
        "primary_attributes": ["dexterity"],
        "playstyle": "ranged_physical",
        "ascendancies": ["Deadeye", "Pathfinder"]
    },
    "Warrior": {
        "primary_weapons": ["mace", "sword", "axe"],
        "primary_attributes": ["strength"],
        "playstyle": "melee_physical", 
        "ascendancies": ["Titan", "Warbringer"]
    },
    "Sorceress": {
        "primary_weapons": ["staff", "wand"],
        "primary_attributes": ["intelligence"],
        "playstyle": "caster_elemental",
        "ascendancies": ["Stormweaver", "Chronomancer"]
    },
    "Monk": {
        "primary_weapons": ["quarterstaff", "flail"],
        "primary_attributes": ["dexterity", "intelligence"],
        "playstyle": "melee_elemental",
        "ascendancies": ["Invoker"]
    },
    "Witch": {
        "primary_weapons": ["staff", "wand"],
        "primary_attributes": ["intelligence"],
        "playstyle": "caster_minions",
        "ascendancies": ["Infernalist", "Blood Mage"]
    },
    "Mercenary": {
        "primary_weapons": ["crossbow", "firearm"],
        "primary_attributes": ["dexterity", "intelligence"], 
        "playstyle": "ranged_tech",
        "ascendancies": ["Witchhunter"]
    }
}

@dataclass
class BuildRecommendation:
    """构筑推荐"""
    name: str
    character_class: str
    ascendancy: str
    main_skill: str
    support_gems: List[str]
    weapon_type: str
    playstyle: str
    estimated_budget: Dict[str, float]  # {"chaos": 100, "divine": 5}
    meta_score: float  # 0-1, Meta流行度
    beginner_friendly: bool
    description: str
    pros: List[str]
    cons: List[str]

class PoE2RealisticDataSystem:
    """基于现实可用数据的PoE2构筑推荐系统"""
    
    def __init__(self):
        self.current_league = "Rise of the Abyssal"
        self.last_updated = datetime.now()
        
        # 模拟市场数据 (实际中从PoE2Scout获取)
        self.market_data = {
            "Midnight Fang": {"chaos": 150, "divine": 0.8, "availability": "common"},
            "The Last Resort": {"chaos": 300, "divine": 1.7, "availability": "rare"},
            "Doryani's Fist": {"chaos": 250, "divine": 1.4, "availability": "uncommon"}
        }
        
        # 模拟Meta数据 (实际中从PoE Ninja获取)
        self.meta_trends = {
            "Lightning Arrow": {"usage": 0.23, "trend": "rising"},
            "Explosive Shot": {"usage": 0.18, "trend": "stable"}, 
            "Ice Nova": {"usage": 0.15, "trend": "falling"},
            "Hammer of the Gods": {"usage": 0.12, "trend": "rising"}
        }
    
    def generate_build_recommendations(self, preferences: Dict) -> List[BuildRecommendation]:
        """生成构筑推荐"""
        
        character_class = preferences.get('class', 'Ranger')
        budget = preferences.get('budget', {'amount': 10, 'currency': 'divine'})
        goal = preferences.get('goal', 'clear_speed')
        
        recommendations = []
        
        if character_class == "Ranger":
            # 弓箭手构筑推荐
            lightning_build = BuildRecommendation(
                name="闪电箭清图流派",
                character_class="Ranger",
                ascendancy="Deadeye", 
                main_skill="Lightning Arrow",
                support_gems=["Chain Support", "Lightning Penetration", "Added Lightning Damage"],
                weapon_type="bow",
                playstyle="ranged_lightning",
                estimated_budget={"chaos": 800, "divine": 4.5},
                meta_score=self.meta_trends["Lightning Arrow"]["usage"],
                beginner_friendly=True,
                description="使用闪电箭进行快速清图，连锁闪电可以清除大量怪物",
                pros=["清图速度快", "装备要求低", "操作简单"],
                cons=["单体伤害一般", "对闪电抗性怪物无力"]
            )
            recommendations.append(lightning_build)
            
            explosive_build = BuildRecommendation(
                name="爆炸射击Boss流派", 
                character_class="Ranger",
                ascendancy="Pathfinder",
                main_skill="Explosive Shot",
                support_gems=["Concentrated Effect", "Fire Penetration", "Burning Support"],
                weapon_type="bow",
                playstyle="ranged_fire",
                estimated_budget={"chaos": 1200, "divine": 6.8},
                meta_score=self.meta_trends["Explosive Shot"]["usage"],
                beginner_friendly=False,
                description="专精单体爆发伤害，适合击杀Boss和精英怪物",
                pros=["单体伤害极高", "范围伤害不错", "Boss战表现优秀"],
                cons=["装备要求高", "操作复杂", "清图效率一般"]
            )
            recommendations.append(explosive_build)
            
        elif character_class == "Sorceress":
            # 法师构筑推荐
            ice_nova_build = BuildRecommendation(
                name="寒冰新星群控流派",
                character_class="Sorceress", 
                ascendancy="Stormweaver",
                main_skill="Ice Nova",
                support_gems=["Spell Echo", "Cold Penetration", "Hypothermia"],
                weapon_type="staff",
                playstyle="caster_cold",
                estimated_budget={"chaos": 600, "divine": 3.2},
                meta_score=self.meta_trends["Ice Nova"]["usage"],
                beginner_friendly=True,
                description="以寒冰新星为核心的群体控制流派，冰冻敌人后造成伤害",
                pros=["群体控制强", "安全性高", "装备便宜"],
                cons=["移动速度慢", "单体伤害低", "需要走位技巧"]
            )
            recommendations.append(ice_nova_build)
        
        # 根据预算过滤推荐
        budget_limit = budget['amount'] if budget['currency'] == 'divine' else budget['amount'] / 180
        filtered_recommendations = [
            build for build in recommendations 
            if build.estimated_budget['divine'] <= budget_limit * 1.2  # 20%容差
        ]
        
        # 按Meta得分排序
        filtered_recommendations.sort(key=lambda x: x.meta_score, reverse=True)
        
        return filtered_recommendations[:3]  # 返回前3个推荐
    
    def get_market_analysis(self, item_name: str) -> Dict:
        """获取市场分析"""
        if item_name in self.market_data:
            return {
                "item": item_name,
                "price": self.market_data[item_name],
                "trend": "stable",  # 实际中从PoE2Scout分析
                "availability": self.market_data[item_name]["availability"]
            }
        return {"error": "Item not found in market data"}
    
    def get_meta_report(self) -> Dict:
        """获取当前Meta报告"""
        return {
            "league": self.current_league,
            "updated": self.last_updated.isoformat(),
            "top_skills": sorted(
                self.meta_trends.items(), 
                key=lambda x: x[1]["usage"], 
                reverse=True
            )[:5],
            "rising_skills": [
                skill for skill, data in self.meta_trends.items() 
                if data["trend"] == "rising"
            ]
        }

def main():
    """演示实际可用的PoE2数据系统"""
    system = PoE2RealisticDataSystem()
    
    # 用户请求示例
    user_request = {
        'class': 'Ranger',
        'budget': {'amount': 8, 'currency': 'divine'},
        'goal': 'clear_speed'
    }
    
    print("=== PoE2现实可用数据系统演示 ===")
    print(f"联盟: {system.current_league}")
    print(f"更新时间: {system.last_updated.strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # 生成构筑推荐
    recommendations = system.generate_build_recommendations(user_request)
    
    print("构筑推荐:")
    for i, build in enumerate(recommendations, 1):
        print(f"\n{i}. {build.name}")
        print(f"   职业: {build.character_class} - {build.ascendancy}")
        print(f"   主技能: {build.main_skill}")
        print(f"   预算: {build.estimated_budget['divine']:.1f} Divine")
        print(f"   Meta得分: {build.meta_score:.2f}")
        print(f"   新手友好: {'是' if build.beginner_friendly else '否'}")
        print(f"   描述: {build.description}")
    
    # Meta报告
    print(f"\n当前Meta报告:")
    meta_report = system.get_meta_report()
    print(f"热门技能:")
    for skill, data in meta_report["top_skills"]:
        print(f"  - {skill}: {data['usage']:.1%} 使用率 ({data['trend']})")
    
    return recommendations

if __name__ == "__main__":
    recommendations = main()