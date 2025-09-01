"""
测试数据工厂和辅助函数
用于生成各种测试场景所需的数据
"""

import random
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from src.poe2build.models.build import PoE2Build, PoE2BuildStats, PoE2BuildGoal
from src.poe2build.models.characters import (
    PoE2CharacterClass, PoE2Ascendancy, PoE2Character, PoE2CharacterAttributes,
    ASCENDANCY_MAPPING
)
from src.poe2build.core.ai_orchestrator import UserRequest, SystemComponent, ComponentStatus


@dataclass
class TestScenario:
    """测试场景数据类"""
    name: str
    description: str
    input_data: Dict[str, Any]
    expected_output: Dict[str, Any]
    should_pass: bool = True
    tags: List[str] = None


class TestDataFactory:
    """测试数据工厂类"""
    
    @staticmethod
    def create_random_build_stats(
        dps_range: Tuple[int, int] = (100000, 2000000),
        ehp_range: Tuple[int, int] = (3000, 12000),
        resistance_range: Tuple[int, int] = (-60, 80)
    ) -> PoE2BuildStats:
        """创建随机构筑统计数据"""
        return PoE2BuildStats(
            total_dps=random.randint(*dps_range),
            effective_health_pool=random.randint(*ehp_range),
            fire_resistance=random.randint(*resistance_range),
            cold_resistance=random.randint(*resistance_range),
            lightning_resistance=random.randint(*resistance_range),
            chaos_resistance=random.randint(-100, 80),
            life=random.randint(2000, 8000),
            energy_shield=random.randint(0, 5000),
            mana=random.randint(300, 2000),
            critical_strike_chance=random.uniform(5.0, 95.0),
            critical_strike_multiplier=random.uniform(150.0, 500.0),
            attack_speed=random.uniform(1.0, 6.0) if random.choice([True, False]) else 0.0,
            cast_speed=random.uniform(1.0, 4.0) if random.choice([True, False]) else 0.0,
            movement_speed=random.uniform(100.0, 150.0),
            block_chance=random.uniform(0.0, 75.0),
            dodge_chance=random.uniform(0.0, 75.0),
            physical_dps=random.randint(0, int(dps_range[1] * 0.8)),
            elemental_dps=random.randint(0, int(dps_range[1] * 0.8)),
            chaos_dps=random.randint(0, int(dps_range[1] * 0.3))
        )
    
    @staticmethod
    def create_random_build(
        character_class: Optional[PoE2CharacterClass] = None,
        level_range: Tuple[int, int] = (70, 100),
        cost_range: Tuple[float, float] = (0.5, 50.0)
    ) -> PoE2Build:
        """创建随机构筑"""
        if not character_class:
            character_class = random.choice(list(PoE2CharacterClass))
        
        # 选择合适的升华
        possible_ascendancies = ASCENDANCY_MAPPING.get(character_class, [])
        ascendancy = random.choice(possible_ascendancies) if possible_ascendancies else None
        
        # 随机选择构筑目标
        goal = random.choice(list(PoE2BuildGoal))
        
        # 根据目标调整DPS和EHP范围
        if goal == PoE2BuildGoal.BOSS_KILLING:
            dps_range = (800000, 3000000)
            ehp_range = (6000, 10000)
        elif goal == PoE2BuildGoal.CLEAR_SPEED:
            dps_range = (400000, 1500000)
            ehp_range = (4000, 9000)
        elif goal == PoE2BuildGoal.BUDGET_FRIENDLY:
            dps_range = (150000, 800000)
            ehp_range = (4000, 8000)
            cost_range = (0.1, 10.0)
        else:
            dps_range = (300000, 2000000)
            ehp_range = (5000, 12000)
        
        stats = TestDataFactory.create_random_build_stats(dps_range, ehp_range)
        
        return PoE2Build(
            name=f"Test {character_class.value} Build {random.randint(1, 999)}",
            character_class=character_class,
            level=random.randint(*level_range),
            ascendancy=ascendancy,
            stats=stats,
            estimated_cost=round(random.uniform(*cost_range), 1),
            currency_type="divine",
            goal=goal,
            main_skill_gem=f"Test Skill {random.randint(1, 20)}",
            support_gems=[f"Support Gem {i}" for i in range(random.randint(3, 6))],
            key_items=[f"Key Item {i}" for i in range(random.randint(3, 8))],
            passive_keystones=[f"Keystone {i}" for i in range(random.randint(2, 5))],
            created_by="test_factory",
            league="Standard"
        )
    
    @staticmethod
    def create_build_batch(
        count: int,
        character_class: Optional[PoE2CharacterClass] = None
    ) -> List[PoE2Build]:
        """创建一批随机构筑"""
        return [TestDataFactory.create_random_build(character_class) for _ in range(count)]
    
    @staticmethod
    def create_user_request(
        character_class: Optional[PoE2CharacterClass] = None,
        build_goal: Optional[PoE2BuildGoal] = None,
        max_budget: Optional[float] = None,
        **kwargs
    ) -> UserRequest:
        """创建用户请求"""
        defaults = {
            'character_class': character_class or random.choice(list(PoE2CharacterClass)),
            'build_goal': build_goal or random.choice(list(PoE2BuildGoal)),
            'max_budget': max_budget or random.uniform(5.0, 50.0),
            'currency_type': 'divine',
            'preferred_skills': [f"Skill {i}" for i in range(random.randint(1, 3))],
            'playstyle': random.choice(['aggressive', 'defensive', 'balanced']),
            'min_dps': random.randint(200000, 800000),
            'min_ehp': random.randint(4000, 8000),
            'require_resistance_cap': random.choice([True, False]),
            'include_meta_builds': True,
            'include_budget_builds': True,
            'generate_pob2_code': random.choice([True, False]),
            'validate_with_pob2': random.choice([True, False])
        }
        defaults.update(kwargs)
        return UserRequest(**defaults)
    
    @staticmethod
    def create_character(
        character_class: Optional[PoE2CharacterClass] = None,
        level: Optional[int] = None
    ) -> PoE2Character:
        """创建测试角色"""
        if not character_class:
            character_class = random.choice(list(PoE2CharacterClass))
        
        if not level:
            level = random.randint(1, 100)
        
        # 创建属性
        base_attrs = [100, 100, 100]
        # 根据职业调整主属性
        if character_class in [PoE2CharacterClass.WARRIOR]:
            base_attrs[0] += random.randint(100, 300)  # 力量
        elif character_class in [PoE2CharacterClass.SORCERESS, PoE2CharacterClass.WITCH]:
            base_attrs[2] += random.randint(100, 300)  # 智力
        else:
            base_attrs[1] += random.randint(100, 300)  # 敏捷
        
        attributes = PoE2CharacterAttributes(
            strength=base_attrs[0],
            dexterity=base_attrs[1],
            intelligence=base_attrs[2]
        )
        
        # 选择升华
        possible_ascendancies = ASCENDANCY_MAPPING.get(character_class, [])
        ascendancy = random.choice(possible_ascendancies) if possible_ascendancies and level >= 30 else None
        
        return PoE2Character(
            name=f"Test {character_class.value} {random.randint(1, 999)}",
            character_class=character_class,
            level=level,
            attributes=attributes,
            ascendancy=ascendancy,
            experience=level * 100000,
            passive_skill_points=max(0, level - 1),
            ascendancy_points=random.randint(0, 8) if ascendancy else 0,
            league="Standard",
            hardcore=random.choice([True, False])
        )


class TestCaseGenerator:
    """测试用例生成器"""
    
    @staticmethod
    def generate_build_validation_cases() -> List[TestScenario]:
        """生成构筑验证测试用例"""
        cases = []
        
        # 有效构筑
        valid_build = TestDataFactory.create_random_build()
        cases.append(TestScenario(
            name="valid_build_test",
            description="测试有效构筑的验证",
            input_data={'build': valid_build},
            expected_output={'is_valid': True, 'errors': []},
            should_pass=True,
            tags=['validation', 'positive']
        ))
        
        # 无效等级构筑
        invalid_level_build = TestDataFactory.create_random_build()
        invalid_level_build.level = 150  # 超出有效范围
        cases.append(TestScenario(
            name="invalid_level_test",
            description="测试无效等级构筑的验证",
            input_data={'build': invalid_level_build},
            expected_output={'is_valid': False, 'errors': ['invalid_level']},
            should_pass=False,
            tags=['validation', 'negative']
        ))
        
        # 无效抗性构筑
        invalid_res_build = TestDataFactory.create_random_build()
        invalid_res_build.stats.fire_resistance = 150  # 超出范围
        cases.append(TestScenario(
            name="invalid_resistance_test", 
            description="测试无效抗性构筑的验证",
            input_data={'build': invalid_res_build},
            expected_output={'is_valid': False, 'errors': ['invalid_resistance']},
            should_pass=False,
            tags=['validation', 'negative']
        ))
        
        return cases
    
    @staticmethod
    def generate_filtering_cases() -> List[TestScenario]:
        """生成构筑过滤测试用例"""
        cases = []
        
        # 创建测试构筑集合
        builds = []
        for char_class in list(PoE2CharacterClass)[:3]:  # 只用前3个职业
            builds.extend(TestDataFactory.create_build_batch(3, char_class))
        
        # 按职业过滤
        target_class = PoE2CharacterClass.SORCERESS
        expected_count = len([b for b in builds if b.character_class == target_class])
        cases.append(TestScenario(
            name="filter_by_class_test",
            description="测试按职业过滤构筑",
            input_data={'builds': builds, 'character_class': target_class},
            expected_output={'filtered_count': expected_count},
            should_pass=True,
            tags=['filtering', 'class']
        ))
        
        # 按预算过滤
        max_budget = 20.0
        expected_budget_count = len([b for b in builds 
                                   if b.estimated_cost and b.estimated_cost <= max_budget])
        cases.append(TestScenario(
            name="filter_by_budget_test",
            description="测试按预算过滤构筑",
            input_data={'builds': builds, 'max_budget': max_budget},
            expected_output={'filtered_count': expected_budget_count},
            should_pass=True,
            tags=['filtering', 'budget']
        ))
        
        return cases
    
    @staticmethod
    def generate_performance_test_data() -> Dict[str, Any]:
        """生成性能测试数据"""
        return {
            'small_dataset': {
                'builds': TestDataFactory.create_build_batch(10),
                'expected_max_time_ms': 100
            },
            'medium_dataset': {
                'builds': TestDataFactory.create_build_batch(100),
                'expected_max_time_ms': 500
            },
            'large_dataset': {
                'builds': TestDataFactory.create_build_batch(1000),
                'expected_max_time_ms': 2000
            },
            'concurrent_requests': [
                TestDataFactory.create_user_request() for _ in range(10)
            ],
            'memory_stress_builds': TestDataFactory.create_build_batch(5000)
        }
    
    @staticmethod
    def generate_error_scenarios() -> List[TestScenario]:
        """生成错误场景测试用例"""
        cases = []
        
        # API超时场景
        cases.append(TestScenario(
            name="api_timeout_scenario",
            description="测试API超时错误处理",
            input_data={
                'request': TestDataFactory.create_user_request(),
                'mock_error': 'TimeoutError',
                'expected_fallback': True
            },
            expected_output={
                'has_results': True,
                'is_fallback': True,
                'error_handled': True
            },
            should_pass=True,
            tags=['error_handling', 'timeout']
        ))
        
        # 数据验证错误场景
        cases.append(TestScenario(
            name="data_validation_error",
            description="测试数据验证错误处理",
            input_data={
                'invalid_data': {'character_class': 'INVALID_CLASS'},
                'expected_validation_error': True
            },
            expected_output={
                'validation_passed': False,
                'error_message': 'Invalid character class'
            },
            should_pass=False,
            tags=['error_handling', 'validation']
        ))
        
        # 资源不足场景
        cases.append(TestScenario(
            name="resource_exhaustion_scenario",
            description="测试系统资源不足时的处理",
            input_data={
                'concurrent_requests': 100,
                'memory_limit': '512MB'
            },
            expected_output={
                'graceful_degradation': True,
                'service_available': True
            },
            should_pass=True,
            tags=['error_handling', 'resources']
        ))
        
        return cases


class MockDataProvider:
    """Mock数据提供者"""
    
    @staticmethod
    def get_mock_api_responses() -> Dict[str, Any]:
        """获取Mock API响应"""
        return {
            'market_price_success': {
                'status': 'success',
                'data': {
                    'item_name': 'Test Item',
                    'median_price': 5.5,
                    'currency': 'divine',
                    'confidence': 0.9
                }
            },
            'market_price_not_found': {
                'status': 'error',
                'error': 'item_not_found',
                'message': 'Item not found in market data'
            },
            'ninja_builds_success': {
                'status': 'success',
                'data': [
                    {
                        'name': 'Mock Build 1',
                        'class': 'Sorceress',
                        'dps': 800000,
                        'popularity': 12.5
                    }
                ]
            },
            'pob2_calculation_success': {
                'status': 'success',
                'calculations': {
                    'total_dps': 1200000,
                    'ehp': 8500,
                    'resistances': {'fire': 78, 'cold': 76, 'lightning': 77}
                }
            }
        }
    
    @staticmethod
    def create_mock_component_health() -> Dict[SystemComponent, Dict[str, Any]]:
        """创建Mock组件健康状态"""
        return {
            SystemComponent.RAG_ENGINE: {
                'status': ComponentStatus.HEALTHY,
                'response_time_ms': 85,
                'last_check': time.time(),
                'error_message': None
            },
            SystemComponent.MARKET_API: {
                'status': ComponentStatus.HEALTHY,
                'response_time_ms': 120,
                'last_check': time.time(),
                'error_message': None
            },
            SystemComponent.POB2_LOCAL: {
                'status': ComponentStatus.HEALTHY,
                'response_time_ms': 200,
                'last_check': time.time(),
                'error_message': None
            },
            SystemComponent.NINJA_SCRAPER: {
                'status': ComponentStatus.DEGRADED,
                'response_time_ms': 800,
                'last_check': time.time(),
                'error_message': 'High response time'
            }
        }


# 导出常用的测试数据集合
TEST_DATA_SETS = {
    'sample_builds': TestDataFactory.create_build_batch(20),
    'sample_requests': [TestDataFactory.create_user_request() for _ in range(10)],
    'sample_characters': [TestDataFactory.create_character() for _ in range(15)],
    'validation_cases': TestCaseGenerator.generate_build_validation_cases(),
    'filtering_cases': TestCaseGenerator.generate_filtering_cases(),
    'error_scenarios': TestCaseGenerator.generate_error_scenarios(),
    'performance_data': TestCaseGenerator.generate_performance_test_data(),
    'mock_responses': MockDataProvider.get_mock_api_responses(),
    'mock_health': MockDataProvider.create_mock_component_health()
}


def get_test_data(dataset_name: str) -> Any:
    """获取指定的测试数据集"""
    return TEST_DATA_SETS.get(dataset_name)