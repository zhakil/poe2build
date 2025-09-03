"""数据验证工具"""

import re
import json
from typing import Any, Dict, List, Optional, Union, Callable
from .poe2_constants import PoE2Validators, PoE2Constants

class ValidationResult:
    """验证结果"""
    
    def __init__(self, is_valid: bool, errors: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        
    def add_error(self, error: str):
        """添加错误信息"""
        self.errors.append(error)
        self.is_valid = False
        
    def merge(self, other: 'ValidationResult'):
        """合并另一个验证结果"""
        if not other.is_valid:
            self.errors.extend(other.errors)
            self.is_valid = False
        
    def __bool__(self):
        return self.is_valid
        
    def __str__(self):
        if self.is_valid:
            return "Validation passed"
        return f"Validation failed: {'; '.join(self.errors)}"

class PoE2DataValidator:
    """PoE2专用数据验证器"""
    
    @staticmethod
    def validate_build_data(build_data: Dict[str, Any]) -> ValidationResult:
        """验证构筑数据完整性"""
        result = ValidationResult(True)
        
        # 必需字段检查
        required_fields = ['class', 'level', 'skills', 'equipment']
        for field in required_fields:
            if field not in build_data:
                result.add_error(f"Missing required field: {field}")
                
        # 角色职业验证
        if 'class' in build_data:
            if not PoE2Validators.validate_character_class(build_data['class']):
                result.add_error(f"Invalid character class: {build_data['class']}")
                
        # 升华职业验证
        if 'ascendancy' in build_data and 'class' in build_data:
            if not PoE2Validators.validate_ascendancy(
                build_data['class'], build_data['ascendancy']):
                result.add_error(
                    f"Invalid ascendancy {build_data['ascendancy']} "
                    f"for class {build_data['class']}"
                )
                
        # 等级验证
        if 'level' in build_data:
            level = build_data['level']
            if not isinstance(level, int) or not (1 <= level <= 100):
                result.add_error(f"Invalid level: {level}. Must be 1-100")
                
        # 抗性验证
        if 'resistances' in build_data:
            resistances = build_data['resistances']
            for res_type, value in resistances.items():
                if not PoE2Validators.validate_resistance(value, res_type):
                    result.add_error(
                        f"Invalid {res_type} resistance: {value}. "
                        f"Max is {PoE2Constants.MAX_RESISTANCE}%"
                    )
                    
        return result
        
    @staticmethod
    def validate_equipment_data(equipment: Dict[str, Any]) -> ValidationResult:
        """验证装备数据"""
        result = ValidationResult(True)
        
        # 检查槽位有效性
        for slot, item in equipment.items():
            if slot not in PoE2Constants.EQUIPMENT_SLOTS:
                result.add_error(f"Invalid equipment slot: {slot}")
                
            # 验证物品数据结构
            if item and isinstance(item, dict):
                if 'name' not in item:
                    result.add_error(f"Item in slot {slot} missing name")
                    
        return result
        
    @staticmethod
    def validate_market_data(market_data: Dict[str, Any]) -> ValidationResult:
        """验证市场数据"""
        result = ValidationResult(True)
        
        required_fields = ['item_name', 'price', 'currency', 'timestamp']
        for field in required_fields:
            if field not in market_data:
                result.add_error(f"Missing market data field: {field}")
                
        # 货币验证
        if 'currency' in market_data:
            currency = market_data['currency']
            if currency not in PoE2Constants.CURRENCY_CHAOS_VALUES:
                result.add_error(f"Invalid currency type: {currency}")
                
        # 价格验证
        if 'price' in market_data:
            price = market_data['price']
            if not isinstance(price, (int, float)) or price < 0:
                result.add_error(f"Invalid price: {price}")
                
        return result
        
    @staticmethod
    def validate_skill_data(skill_data: Dict[str, Any]) -> ValidationResult:
        """验证技能数据"""
        result = ValidationResult(True)
        
        required_fields = ['name', 'type']
        for field in required_fields:
            if field not in skill_data:
                result.add_error(f"Missing skill data field: {field}")
                
        # 技能类型验证
        if 'type' in skill_data:
            skill_type = skill_data['type']
            valid_types = ['active', 'support', 'aura', 'curse']
            if skill_type not in valid_types:
                result.add_error(f"Invalid skill type: {skill_type}")
                
        return result

class SchemaValidator:
    """JSON Schema验证器"""
    
    def __init__(self):
        self.schemas = self._load_schemas()
        
    def _load_schemas(self) -> Dict[str, Dict]:
        """加载验证模式"""
        return {
            'build_request': {
                'type': 'object',
                'required': ['preferences'],
                'properties': {
                    'preferences': {
                        'type': 'object',
                        'required': ['class'],
                        'properties': {
                            'class': {'type': 'string'},
                            'ascendancy': {'type': 'string'},
                            'style': {'type': 'string'},
                            'goal': {'type': 'string'},
                            'budget': {
                                'type': 'object',
                                'properties': {
                                    'amount': {'type': 'number'},
                                    'currency': {'type': 'string'}
                                }
                            }
                        }
                    }
                }
            },
            'build_result': {
                'type': 'object',
                'required': ['build_name', 'class', 'estimated_dps'],
                'properties': {
                    'build_name': {'type': 'string'},
                    'class': {'type': 'string'},
                    'estimated_dps': {'type': 'number'},
                    'cost_analysis': {'type': 'object'}
                }
            }
        }
        
    def validate_against_schema(self, data: Any, schema_name: str) -> ValidationResult:
        """根据模式验证数据"""
        result = ValidationResult(True)
        
        if schema_name not in self.schemas:
            result.add_error(f"Unknown schema: {schema_name}")
            return result
            
        # 基础类型检查
        schema = self.schemas[schema_name]
        if not self._validate_type(data, schema):
            result.add_error("Data does not match schema type")
            
        # 必需字段检查
        if schema.get('required') and isinstance(data, dict):
            for field in schema['required']:
                if field not in data:
                    result.add_error(f"Missing required field: {field}")
                    
        return result
        
    def _validate_type(self, data: Any, schema: Dict) -> bool:
        """验证数据类型"""
        expected_type = schema.get('type')
        
        if expected_type == 'object':
            return isinstance(data, dict)
        elif expected_type == 'array':
            return isinstance(data, list)
        elif expected_type == 'string':
            return isinstance(data, str)
        elif expected_type == 'number':
            return isinstance(data, (int, float))
        elif expected_type == 'boolean':
            return isinstance(data, bool)
        else:
            return True  # 未知类型，跳过验证

# 验证装饰器
def validate_input(validator_func: Callable) -> Callable:
    """输入验证装饰器"""
    
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # 假设第一个参数是要验证的数据
            if args:
                validation_result = validator_func(args[0])
                if not validation_result:
                    raise ValueError(f"Validation failed: {validation_result.errors}")
                    
            return func(*args, **kwargs)
        return wrapper
    return decorator

def validate_multiple(*validator_funcs: Callable) -> Callable:
    """多重验证装饰器"""
    
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            if args:
                combined_result = ValidationResult(True)
                
                for validator in validator_funcs:
                    result = validator(args[0])
                    combined_result.merge(result)
                    
                if not combined_result:
                    raise ValueError(f"Validation failed: {combined_result.errors}")
                    
            return func(*args, **kwargs)
        return wrapper
    return decorator

# 便利验证函数
def quick_validate_build(build_data: Dict[str, Any]) -> bool:
    """快速验证构筑数据"""
    result = PoE2DataValidator.validate_build_data(build_data)
    return result.is_valid

def quick_validate_equipment(equipment: Dict[str, Any]) -> bool:
    """快速验证装备数据"""
    result = PoE2DataValidator.validate_equipment_data(equipment)
    return result.is_valid

def validate_json_string(json_string: str) -> ValidationResult:
    """验证JSON字符串格式"""
    result = ValidationResult(True)
    
    try:
        json.loads(json_string)
    except json.JSONDecodeError as e:
        result.add_error(f"Invalid JSON format: {e}")
        
    return result

def validate_url(url: str) -> ValidationResult:
    """验证URL格式"""
    result = ValidationResult(True)
    
    url_pattern = re.compile(
        r'^https?://'  # http:// 或 https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # 域名
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP地址
        r'(?::\d+)?'  # 可选端口
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
    if not url_pattern.match(url):
        result.add_error(f"Invalid URL format: {url}")
        
    return result

# 使用示例装饰器
@validate_input(PoE2DataValidator.validate_build_data)
def process_build_data(build_data: Dict[str, Any]):
    """处理构筑数据（带输入验证）"""
    # 实际处理逻辑
    return f"Processing build for {build_data.get('class', 'Unknown')}"

@validate_multiple(
    PoE2DataValidator.validate_build_data,
    PoE2DataValidator.validate_equipment_data
)
def process_complete_build(build_data: Dict[str, Any]):
    """处理完整构筑数据（多重验证）"""
    return f"Processing complete build for {build_data.get('class', 'Unknown')}"