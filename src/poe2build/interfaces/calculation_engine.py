# -*- coding: utf-8 -*-
"""
计算引擎接口定义

本模块定义了PoE2构筑计算引擎的抽象接口，支持DPS计算、防御计算、构筑验证等功能。
设计支持多种计算引擎实现，包括本地PoB2、Web PoB2和Mock计算器。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from ..models import PoE2Build, PoE2BuildStats, PoE2Character, PoE2Skill, PoE2Item


class EngineStatus(Enum):
    """计算引擎状态"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class EngineType(Enum):
    """计算引擎类型"""
    POB2_LOCAL = "pob2_local"
    POB2_WEB = "pob2_web"
    CUSTOM = "custom"
    MOCK = "mock"


@dataclass
class EngineCapabilities:
    """引擎能力描述"""
    can_calculate_dps: bool = True
    can_calculate_defense: bool = True
    can_validate_builds: bool = True
    can_optimize_builds: bool = False
    can_simulate_combat: bool = False
    supports_all_skills: bool = True
    supports_all_items: bool = True
    max_build_complexity: int = 10  # 1-10评分
    accuracy_level: float = 0.95  # 0-1评分
    
    
@dataclass
class CalculationRequest:
    """计算请求"""
    build_data: Dict[str, Any]
    calculation_type: str = "full"  # "full", "dps", "defense", "validation"
    options: Dict[str, Any] = field(default_factory=dict)
    character_level: int = 90
    enemy_level: Optional[int] = None
    include_buffs: bool = True
    include_flasks: bool = True
    detailed_output: bool = False


@dataclass
class DPSCalculation:
    """DPS计算结果"""
    total_dps: float
    skill_dps: Dict[str, float] = field(default_factory=dict)
    average_hit: float = 0.0
    crit_chance: float = 0.0
    crit_multiplier: float = 0.0
    attack_speed: float = 0.0
    cast_speed: float = 0.0
    accuracy: float = 0.0
    penetration: Dict[str, float] = field(default_factory=dict)
    damage_breakdown: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DefenseCalculation:
    """防御计算结果"""
    life: int = 0
    energy_shield: int = 0
    effective_hp: int = 0
    life_regen: float = 0.0
    es_regen: float = 0.0
    resistances: Dict[str, float] = field(default_factory=dict)
    armor: int = 0
    evasion: int = 0
    dodge_chance: float = 0.0
    block_chance: float = 0.0
    damage_reduction: Dict[str, float] = field(default_factory=dict)


@dataclass
class BuildValidationResult:
    """构筑验证结果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    compatibility_score: float = 1.0  # 0-1评分
    missing_requirements: List[str] = field(default_factory=list)


@dataclass
class CalculationResult:
    """计算结果"""
    success: bool
    dps_calculation: Optional[DPSCalculation] = None
    defense_calculation: Optional[DefenseCalculation] = None
    validation_result: Optional[BuildValidationResult] = None
    raw_data: Optional[Dict[str, Any]] = None
    calculation_time_ms: int = 0
    engine_used: str = ""
    engine_version: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None


class ICalculationEngine(ABC):
    """计算引擎基础接口
    
    定义所有计算引擎都应该实现的核心方法，包括DPS计算、防御计算、构筑验证等。
    """
    
    @property
    @abstractmethod
    def engine_type(self) -> EngineType:
        """获取引擎类型
        
        Returns:
            EngineType: 引擎类型标识
        """
        pass
    
    @property
    @abstractmethod
    def engine_version(self) -> str:
        """获取引擎版本
        
        Returns:
            str: 引擎版本信息
        """
        pass
    
    @abstractmethod
    def get_status(self) -> EngineStatus:
        """获取引擎状态
        
        Returns:
            EngineStatus: 当前引擎状态
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> EngineCapabilities:
        """获取引擎能力
        
        Returns:
            EngineCapabilities: 引擎支持的功能和限制
        """
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """执行健康检查
        
        Returns:
            Dict[str, Any]: 健康检查结果
        """
        pass
    
    def is_available(self) -> bool:
        """检查引擎是否可用
        
        Returns:
            bool: 引擎是否可用
        """
        return self.get_status() in [EngineStatus.AVAILABLE, EngineStatus.DEGRADED]


class IDPSCalculator(ABC):
    """DPS计算器接口
    
    专门用于伤害和DPS计算的接口。
    """
    
    @abstractmethod
    def calculate_dps(self, request: CalculationRequest) -> CalculationResult:
        """计算DPS
        
        Args:
            request (CalculationRequest): 计算请求
            
        Returns:
            CalculationResult: 包含DPS计算结果
        """
        pass
    
    @abstractmethod
    def calculate_skill_dps(self, skill_data: Dict[str, Any], character_stats: Dict[str, Any]) -> float:
        """计算单个技能DPS
        
        Args:
            skill_data (Dict[str, Any]): 技能数据
            character_stats (Dict[str, Any]): 角色属性
            
        Returns:
            float: 技能DPS值
        """
        pass
    
    @abstractmethod
    def calculate_damage_per_hit(self, skill_data: Dict[str, Any], character_stats: Dict[str, Any]) -> Tuple[float, float]:
        """计算每次命中伤害
        
        Args:
            skill_data (Dict[str, Any]): 技能数据
            character_stats (Dict[str, Any]): 角色属性
            
        Returns:
            Tuple[float, float]: (最小伤害, 最大伤害)
        """
        pass


class IDefenseCalculator(ABC):
    """防御计算器接口
    
    专门用于防御和生存能力计算的接口。
    """
    
    @abstractmethod
    def calculate_defenses(self, request: CalculationRequest) -> CalculationResult:
        """计算防御属性
        
        Args:
            request (CalculationRequest): 计算请求
            
        Returns:
            CalculationResult: 包含防御计算结果
        """
        pass
    
    @abstractmethod
    def calculate_effective_hp(self, life: int, energy_shield: int, resistances: Dict[str, float]) -> int:
        """计算有效生命值
        
        Args:
            life (int): 生命值
            energy_shield (int): 能量护盾
            resistances (Dict[str, float]): 抗性数据
            
        Returns:
            int: 有效生命值
        """
        pass
    
    @abstractmethod
    def calculate_damage_reduction(self, armor: int, enemy_damage: int) -> float:
        """计算伤害减免
        
        Args:
            armor (int): 护甲值
            enemy_damage (int): 敌人伤害
            
        Returns:
            float: 伤害减免百分比 (0-1)
        """
        pass


class IBuildValidator(ABC):
    """构筑验证器接口
    
    专门用于构筑有效性验证的接口。
    """
    
    @abstractmethod
    def validate_build(self, build_data: Dict[str, Any]) -> BuildValidationResult:
        """验证构筑
        
        Args:
            build_data (Dict[str, Any]): 构筑数据
            
        Returns:
            BuildValidationResult: 验证结果
        """
        pass
    
    @abstractmethod
    def validate_skill_setup(self, skills: List[Dict[str, Any]]) -> List[str]:
        """验证技能配置
        
        Args:
            skills (List[Dict[str, Any]]): 技能配置列表
            
        Returns:
            List[str]: 验证错误信息
        """
        pass
    
    @abstractmethod
    def validate_item_requirements(self, items: List[Dict[str, Any]], character_stats: Dict[str, Any]) -> List[str]:
        """验证物品需求
        
        Args:
            items (List[Dict[str, Any]]): 物品列表
            character_stats (Dict[str, Any]): 角色属性
            
        Returns:
            List[str]: 验证错误信息
        """
        pass
    
    @abstractmethod
    def check_build_consistency(self, build_data: Dict[str, Any]) -> List[str]:
        """检查构筑一致性
        
        Args:
            build_data (Dict[str, Any]): 构筑数据
            
Returns:
            List[str]: 一致性检查结果
        """
        pass


class IPoB2Engine(ICalculationEngine, IDPSCalculator, IDefenseCalculator, IBuildValidator):
    """Path of Building 2 (PoB2) 集成引擎接口
    
    专门用于PoB2集成的综合引擎接口，继承所有计算功能。
    """
    
    @abstractmethod
    def import_build(self, import_code: str) -> Dict[str, Any]:
        """从PoB2导入码导入构筑
        
        Args:
            import_code (str): PoB2导入码
            
        Returns:
            Dict[str, Any]: 导入的构筑数据
        """
        pass
    
    @abstractmethod
    def export_build(self, build_data: Dict[str, Any]) -> str:
        """将构筑导出为PoB2导入码
        
        Args:
            build_data (Dict[str, Any]): 构筑数据
            
        Returns:
            str: PoB2导入码
        """
        pass
    
    @abstractmethod
    def calculate_full_build(self, build_data: Dict[str, Any]) -> CalculationResult:
        """进行完整构筑计算
        
        Args:
            build_data (Dict[str, Any]): 构筑数据
            
        Returns:
            CalculationResult: 完整计算结果
        """
        pass
    
    @abstractmethod
    def optimize_build(self, build_data: Dict[str, Any], optimization_goals: Dict[str, Any]) -> Dict[str, Any]:
        """优化构筑
        
        Args:
            build_data (Dict[str, Any]): 原始构筑数据
            optimization_goals (Dict[str, Any]): 优化目标
            
        Returns:
            Dict[str, Any]: 优化后的构筑数据
        """
        pass
    
    @abstractmethod
    def simulate_combat(self, build_data: Dict[str, Any], enemy_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟战斗
        
        Args:
            build_data (Dict[str, Any]): 构筑数据
            enemy_data (Dict[str, Any]): 敌人数据
            
        Returns:
            Dict[str, Any]: 战斗模拟结果
        """
        pass
    
    @abstractmethod
    def get_pob2_installation_path(self) -> Optional[str]:
        """获取PoB2安装路径
        
        Returns:
            Optional[str]: PoB2安装路径，如果未安装则返回None
        """
        pass
    
    @abstractmethod
    def detect_pob2_version(self) -> Optional[str]:
        """检测PoB2版本
        
        Returns:
            Optional[str]: PoB2版本信息，如果未检测到则返回None
        """
        pass


class ICalculationEngineFactory(ABC):
    """计算引擎工厂接口
    
    用于创建和管理不同类型的计算引擎实例。
    """
    
    @abstractmethod
    def create_engine(self, engine_type: EngineType, config: Optional[Dict[str, Any]] = None) -> ICalculationEngine:
        """创建计算引擎
        
        Args:
            engine_type (EngineType): 引擎类型
            config (Optional[Dict[str, Any]]): 引擎配置
            
        Returns:
            ICalculationEngine: 计算引擎实例
        """
        pass
    
    @abstractmethod
    def get_available_engines(self) -> List[EngineType]:
        """获取可用的引擎类型
        
        Returns:
            List[EngineType]: 可用引擎类型列表
        """
        pass
    
    @abstractmethod
    def get_best_available_engine(self) -> Optional[ICalculationEngine]:
        """获取最佳可用引擎
        
        Returns:
            Optional[ICalculationEngine]: 最佳引擎实例，如果没有可用引擎则返回None
        """
        pass
    
    @abstractmethod
    def register_engine(self, engine_type: EngineType, engine_class: type) -> None:
        """注册引擎类型
        
        Args:
            engine_type (EngineType): 引擎类型
            engine_class (type): 引擎实现类
        """
        pass