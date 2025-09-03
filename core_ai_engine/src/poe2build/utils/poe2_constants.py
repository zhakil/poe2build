"""PoE2游戏机制相关常量"""

from typing import Dict, List, Set
from enum import Enum

class PoE2Constants:
    """PoE2核心游戏常量"""
    
    # 抗性相关
    MAX_RESISTANCE = 80          # PoE2最大抗性80%
    BASE_CHAOS_RESISTANCE = -30  # 基础混沌抗性-30%
    
    # 能量护盾相关
    ES_RECHARGE_DELAY = 2.0      # 能量护盾恢复延迟(秒)
    ES_RECHARGE_RATE = 0.33      # 能量护盾恢复速率(每秒33%)
    
    # 生命相关
    BASE_LIFE_PER_LEVEL = 12     # 每级基础生命
    BASE_LIFE_START = 50         # 1级基础生命
    
    # 法力相关  
    BASE_MANA_PER_LEVEL = 6      # 每级基础法力
    BASE_MANA_START = 40         # 1级基础法力
    
    # 属性相关
    LIFE_PER_STRENGTH = 0.5      # 每点力量增加0.5生命
    MANA_PER_INTELLIGENCE = 0.5  # 每点智力增加0.5法力
    ACCURACY_PER_DEXTERITY = 2   # 每点敏捷增加2命中
    
    # 伤害计算
    CRIT_MULTIPLIER_BASE = 1.5   # 基础暴击倍率150%
    
    # 货币汇率(基准值,实际应从API获取)
    CURRENCY_CHAOS_VALUES = {
        'divine': 180,           # 1 Divine = 180 Chaos
        'exalted': 45,          # 1 Exalted = 45 Chaos  
        'ancient': 8,           # 1 Ancient = 8 Chaos
        'regal': 3,             # 1 Regal = 3 Chaos
        'alchemy': 1.5,         # 1 Alchemy = 1.5 Chaos
        'fusing': 0.4,          # 1 Fusing = 0.4 Chaos
        'chromatic': 0.2,       # 1 Chromatic = 0.2 Chaos
        'chaos': 1              # 1 Chaos = 1 Chaos (基准)
    }
    
    # 角色职业
    CHARACTER_CLASSES = {
        'witch': 'Witch',
        'ranger': 'Ranger', 
        'warrior': 'Warrior',
        'monk': 'Monk',
        'sorceress': 'Sorceress',
        'mercenary': 'Mercenary'
    }
    
    # 升华职业映射
    ASCENDANCY_MAPPING = {
        'Witch': ['Infernalist', 'Blood Mage', 'Chronomancer'],
        'Ranger': ['Deadeye', 'Pathfinder', 'Beastmaster'], 
        'Warrior': ['Titan', 'Warbringer'],
        'Monk': ['Invoker', 'Acolyte'],
        'Sorceress': ['Stormweaver', 'Templar'],
        'Mercenary': ['Witchhunter', 'Gemling Legionnaire']
    }
    
    # 装备槽位
    EQUIPMENT_SLOTS = [
        'weapon_main_hand',
        'weapon_off_hand', 
        'helmet',
        'body_armour',
        'gloves',
        'boots',
        'ring_1',
        'ring_2',
        'amulet',
        'belt',
        'jewel_1',
        'jewel_2',
        'jewel_3',
        'jewel_4'
    ]
    
    # 伤害类型
    DAMAGE_TYPES = [
        'physical',
        'fire', 
        'cold',
        'lightning',
        'chaos'
    ]
    
    # 防御类型
    DEFENSE_TYPES = [
        'armour',
        'evasion',
        'energy_shield'
    ]

# PoE2特定的验证规则
class PoE2Validators:
    """PoE2数据验证规则"""
    
    @staticmethod
    def validate_resistance(value: float, res_type: str) -> bool:
        """验证抗性值"""
        if res_type == 'chaos':
            return -100 <= value <= PoE2Constants.MAX_RESISTANCE
        else:
            return -60 <= value <= PoE2Constants.MAX_RESISTANCE
            
    @staticmethod
    def validate_character_class(class_name: str) -> bool:
        """验证角色职业"""
        return class_name.lower() in PoE2Constants.CHARACTER_CLASSES
        
    @staticmethod
    def validate_ascendancy(class_name: str, ascendancy: str) -> bool:
        """验证升华职业"""
        if class_name not in PoE2Constants.ASCENDANCY_MAPPING:
            return False
        return ascendancy in PoE2Constants.ASCENDANCY_MAPPING[class_name]
        
    @staticmethod
    def validate_currency_amount(currency: str, amount: float) -> bool:
        """验证货币数量"""
        return (currency in PoE2Constants.CURRENCY_CHAOS_VALUES and 
                0 <= amount <= 999999)

# PoE2计算辅助函数
class PoE2Calculations:
    """PoE2游戏机制计算"""
    
    @staticmethod
    def calculate_total_life(level: int, strength: int, life_from_gear: int, 
                           life_from_passives: int) -> int:
        """计算总生命值"""
        base_life = PoE2Constants.BASE_LIFE_START + \
                   (level - 1) * PoE2Constants.BASE_LIFE_PER_LEVEL
        strength_life = strength * PoE2Constants.LIFE_PER_STRENGTH
        
        return int(base_life + strength_life + life_from_gear + life_from_passives)
        
    @staticmethod
    def calculate_total_mana(level: int, intelligence: int, mana_from_gear: int,
                           mana_from_passives: int) -> int:
        """计算总法力值"""
        base_mana = PoE2Constants.BASE_MANA_START + \
                   (level - 1) * PoE2Constants.BASE_MANA_PER_LEVEL
        int_mana = intelligence * PoE2Constants.MANA_PER_INTELLIGENCE
        
        return int(base_mana + int_mana + mana_from_gear + mana_from_passives)
        
    @staticmethod
    def calculate_effective_health_pool(life: int, energy_shield: int, 
                                      resistances: Dict[str, float]) -> float:
        """计算有效生命池(考虑抗性)"""
        # 计算平均抗性减伤
        avg_resistance = sum(resistances.values()) / len(resistances)
        damage_taken_multiplier = (100 - avg_resistance) / 100
        
        # 有效生命池 = (生命 + 能量护盾) / 承受伤害倍率
        return (life + energy_shield) / damage_taken_multiplier
        
    @staticmethod
    def convert_currency_to_chaos(amount: float, currency_type: str) -> float:
        """将货币转换为混沌石等值"""
        if currency_type not in PoE2Constants.CURRENCY_CHAOS_VALUES:
            raise ValueError(f"Unknown currency type: {currency_type}")
            
        return amount * PoE2Constants.CURRENCY_CHAOS_VALUES[currency_type]
        
    @staticmethod
    def estimate_build_cost_tier(total_chaos_cost: float) -> str:
        """估算构筑成本等级"""
        if total_chaos_cost <= 50:
            return "league_start"      # 赛季初
        elif total_chaos_cost <= 200:
            return "budget"           # 平民
        elif total_chaos_cost <= 800:
            return "medium"           # 中档
        elif total_chaos_cost <= 2500:
            return "expensive"        # 昂贵
        else:
            return "mirror_tier"      # 镜子级