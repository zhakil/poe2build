"""PoE2智能构筑生成器 - 工具函数模块

提供PoE2游戏机制相关的常量、验证、文本处理等工具功能。
"""

__version__ = "2.0.0"
__author__ = "PoE2 Build Generator Team"

# 主要类和函数导入
from .poe2_constants import (
    PoE2Constants,
    PoE2Validators, 
    PoE2Calculations
)

from .data_validation import (
    ValidationResult,
    PoE2DataValidator,
    SchemaValidator,
    validate_input,
    validate_multiple,
    quick_validate_build,
    quick_validate_equipment,
    validate_json_string,
    validate_url
)

from .text_processing import (
    PoE2TextProcessor,
    TextTemplate,
    PoE2Templates,
    PoE2TextUtils,
    clean_poe2_item_name,
    search_poe2_items,
    format_poe2_currency,
    extract_poe2_numbers
)

# 便利函数
def validate_poe2_build(build_data: dict) -> bool:
    """快速验证PoE2构筑数据
    
    Args:
        build_data: 构筑数据字典
        
    Returns:
        bool: 验证是否通过
    """
    return quick_validate_build(build_data)

def format_currency(amount: float, currency: str = 'chaos') -> str:
    """快速格式化货币显示
    
    Args:
        amount: 货币数量
        currency: 货币类型 (chaos, divine, exalted等)
        
    Returns:
        str: 格式化后的货币字符串
    """
    return format_poe2_currency(amount, currency)

def clean_item_text(item_name: str) -> str:
    """快速清理物品名称
    
    Args:
        item_name: 原始物品名称
        
    Returns:
        str: 清理后的物品名称
    """
    return clean_poe2_item_name(item_name)

def calculate_total_life(level: int, strength: int = 0, 
                        life_from_gear: int = 0, life_from_passives: int = 0) -> int:
    """计算角色总生命值
    
    Args:
        level: 角色等级
        strength: 力量属性
        life_from_gear: 装备提供的生命
        life_from_passives: 天赋提供的生命
        
    Returns:
        int: 总生命值
    """
    return PoE2Calculations.calculate_total_life(
        level, strength, life_from_gear, life_from_passives
    )

def calculate_total_mana(level: int, intelligence: int = 0,
                        mana_from_gear: int = 0, mana_from_passives: int = 0) -> int:
    """计算角色总法力值
    
    Args:
        level: 角色等级
        intelligence: 智力属性
        mana_from_gear: 装备提供的法力
        mana_from_passives: 天赋提供的法力
        
    Returns:
        int: 总法力值
    """
    return PoE2Calculations.calculate_total_mana(
        level, intelligence, mana_from_gear, mana_from_passives
    )

def convert_currency_to_chaos(amount: float, currency_type: str) -> float:
    """将其他货币转换为混沌石等值
    
    Args:
        amount: 货币数量
        currency_type: 货币类型
        
    Returns:
        float: 混沌石等值
    """
    return PoE2Calculations.convert_currency_to_chaos(amount, currency_type)

def estimate_build_cost_tier(total_chaos_cost: float) -> str:
    """估算构筑成本等级
    
    Args:
        total_chaos_cost: 总成本(混沌石)
        
    Returns:
        str: 成本等级 (league_start, budget, medium, expensive, mirror_tier)
    """
    return PoE2Calculations.estimate_build_cost_tier(total_chaos_cost)

def format_large_number(number: float, precision: int = 1) -> str:
    """格式化大数字显示
    
    Args:
        number: 要格式化的数字
        precision: 小数位精度
        
    Returns:
        str: 格式化后的数字字符串 (如: 1.5M, 250K)
    """
    return PoE2TextUtils.format_large_number(number, precision)

def search_similar_items(query: str, item_list: list, threshold: float = 0.6) -> list:
    """搜索相似物品
    
    Args:
        query: 搜索查询
        item_list: 物品列表
        threshold: 相似度阈值
        
    Returns:
        list: 匹配的物品及相似度列表 [(item, similarity), ...]
    """
    return search_poe2_items(query, item_list, threshold)

# 常用常量快速访问
MAX_RESISTANCE = PoE2Constants.MAX_RESISTANCE
CHARACTER_CLASSES = PoE2Constants.CHARACTER_CLASSES
ASCENDANCY_MAPPING = PoE2Constants.ASCENDANCY_MAPPING
CURRENCY_CHAOS_VALUES = PoE2Constants.CURRENCY_CHAOS_VALUES
EQUIPMENT_SLOTS = PoE2Constants.EQUIPMENT_SLOTS
DAMAGE_TYPES = PoE2Constants.DAMAGE_TYPES

# 预定义模板快速访问
BUILD_SUMMARY_TEMPLATE = PoE2Templates.BUILD_SUMMARY
ITEM_DESCRIPTION_TEMPLATE = PoE2Templates.ITEM_DESCRIPTION
ERROR_MESSAGE_TEMPLATE = PoE2Templates.ERROR_MESSAGE

# 模块导出列表
__all__ = [
    # 核心类
    'PoE2Constants',
    'PoE2Validators', 
    'PoE2Calculations',
    'ValidationResult',
    'PoE2DataValidator',
    'SchemaValidator',
    'PoE2TextProcessor',
    'TextTemplate',
    'PoE2Templates',
    'PoE2TextUtils',
    
    # 装饰器
    'validate_input',
    'validate_multiple',
    
    # 便利函数
    'validate_poe2_build',
    'format_currency',
    'clean_item_text',
    'calculate_total_life',
    'calculate_total_mana',
    'convert_currency_to_chaos',
    'estimate_build_cost_tier',
    'format_large_number',
    'search_similar_items',
    
    # 快速验证函数
    'quick_validate_build',
    'quick_validate_equipment',
    'validate_json_string',
    'validate_url',
    
    # 文本处理函数
    'clean_poe2_item_name',
    'search_poe2_items', 
    'format_poe2_currency',
    'extract_poe2_numbers',
    
    # 常量
    'MAX_RESISTANCE',
    'CHARACTER_CLASSES',
    'ASCENDANCY_MAPPING', 
    'CURRENCY_CHAOS_VALUES',
    'EQUIPMENT_SLOTS',
    'DAMAGE_TYPES',
    
    # 模板
    'BUILD_SUMMARY_TEMPLATE',
    'ITEM_DESCRIPTION_TEMPLATE',
    'ERROR_MESSAGE_TEMPLATE',
    
    # 元信息
    '__version__',
    '__author__'
]

# 模块级别文档
def get_module_info():
    """获取模块信息"""
    return {
        'name': 'poe2build.utils',
        'version': __version__,
        'description': 'PoE2智能构筑生成器工具函数模块',
        'features': [
            'PoE2游戏机制常量和计算',
            '数据验证和Schema验证', 
            'PoE2专用文本处理',
            '便利函数和装饰器',
            '预定义模板系统'
        ],
        'key_classes': [
            'PoE2Constants - 游戏常量',
            'PoE2Validators - 数据验证', 
            'PoE2Calculations - 游戏计算',
            'PoE2TextProcessor - 文本处理',
            'ValidationResult - 验证结果'
        ]
    }

# 使用示例
def usage_examples():
    """使用示例"""
    examples = {
        'validate_build': """
# 验证构筑数据
build_data = {
    'class': 'Ranger',
    'level': 85,
    'ascendancy': 'Deadeye'
}
is_valid = validate_poe2_build(build_data)
        """,
        
        'format_currency': """
# 格式化货币
cost_text = format_currency(1500, 'chaos')  # "1.5K c"
divine_text = format_currency(15, 'divine')  # "15 div"
        """,
        
        'clean_item_name': """
# 清理物品名称
clean_name = clean_item_text('Unique Windripper (Quality: +20%)')
# 结果: "Windripper"
        """,
        
        'calculate_stats': """
# 计算角色属性
total_life = calculate_total_life(85, strength=200, life_from_gear=150)
total_mana = calculate_total_mana(85, intelligence=150, mana_from_gear=100)
        """,
        
        'currency_conversion': """
# 货币转换
chaos_value = convert_currency_to_chaos(5, 'divine')  # 900 混沌
cost_tier = estimate_build_cost_tier(900)  # "expensive"
        """
    }
    
    return examples

# 兼容性检查
def check_compatibility():
    """检查模块兼容性"""
    import sys
    
    compatibility_info = {
        'python_version': sys.version,
        'python_version_info': sys.version_info,
        'required_python': '3.9+',
        'compatible': sys.version_info >= (3, 9),
        'features_available': {
            'type_hints': True,
            'dataclasses': True, 
            'enum': True,
            'pathlib': True,
            'typing': True
        }
    }
    
    return compatibility_info