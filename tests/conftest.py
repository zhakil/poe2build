"""
pytest配置文件 - 全局fixtures和测试配置

提供所有测试模块通用的fixtures和配置
"""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, MagicMock

# 导入项目模型
from src.poe2build.models.build import PoE2Build, PoE2BuildStats, PoE2BuildGoal
from src.poe2build.models.characters import (
    PoE2CharacterClass, PoE2Ascendancy, PoE2Character, 
    PoE2CharacterAttributes
)
from src.poe2build.models.items import PoE2Item
from src.poe2build.core.ai_orchestrator import (
    PoE2AIOrchestrator, UserRequest, SystemComponent, ComponentStatus
)


# ===== 异步测试支持 =====
@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ===== 临时目录和文件系统 =====
@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_cache_dir(temp_dir):
    """创建Mock缓存目录"""
    cache_dir = temp_dir / "cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


@pytest.fixture
def mock_rag_dir(temp_dir):
    """创建Mock RAG目录"""
    rag_dir = temp_dir / "rag"
    rag_dir.mkdir(exist_ok=True)
    return rag_dir


# ===== 基础数据模型Fixtures =====
@pytest.fixture
def sample_character_attributes():
    """样例角色属性"""
    return PoE2CharacterAttributes(
        strength=150,
        dexterity=200,
        intelligence=300
    )


@pytest.fixture
def sample_build_stats():
    """样例构筑统计数据"""
    return PoE2BuildStats(
        total_dps=750000,
        effective_health_pool=8500,
        fire_resistance=78,
        cold_resistance=76,
        lightning_resistance=77,
        chaos_resistance=-25,
        life=5500,
        energy_shield=3000,
        critical_strike_chance=45.0,
        critical_strike_multiplier=320.0,
        attack_speed=2.5,
        cast_speed=3.2,
        movement_speed=115.0
    )


@pytest.fixture
def sample_character(sample_character_attributes):
    """样例PoE2角色"""
    return PoE2Character(
        name="Test Sorceress",
        character_class=PoE2CharacterClass.SORCERESS,
        level=92,
        attributes=sample_character_attributes,
        ascendancy=PoE2Ascendancy.STORMWEAVER,
        experience=1250000000,
        passive_skill_points=85,
        ascendancy_points=8,
        league="Standard",
        hardcore=False
    )


@pytest.fixture
def sample_build(sample_build_stats):
    """样例PoE2构筑"""
    return PoE2Build(
        name="Lightning Sorceress",
        character_class=PoE2CharacterClass.SORCERESS,
        level=92,
        ascendancy=PoE2Ascendancy.STORMWEAVER,
        stats=sample_build_stats,
        estimated_cost=15.5,
        currency_type="divine",
        goal=PoE2BuildGoal.ENDGAME_CONTENT,
        main_skill_gem="Lightning Bolt",
        support_gems=["Added Lightning Damage", "Lightning Penetration", "Elemental Focus"],
        key_items=["Staff of Power", "Lightning Amulet", "Spell Echo Ring"],
        passive_keystones=["Elemental Overload", "Lightning Mastery"],
        notes="High DPS lightning build for endgame content",
        created_by="test_user",
        league="Standard"
    )


@pytest.fixture
def sample_builds_list(sample_build, sample_build_stats):
    """样例构筑列表"""
    builds = []
    
    # 构筑1: Lightning Sorceress
    builds.append(sample_build)
    
    # 构筑2: Ice Ranger
    ice_stats = PoE2BuildStats(
        total_dps=620000,
        effective_health_pool=9200,
        fire_resistance=75,
        cold_resistance=80,
        lightning_resistance=75,
        chaos_resistance=-30,
        life=6200,
        energy_shield=3000,
        movement_speed=135.0
    )
    
    ice_build = PoE2Build(
        name="Ice Shot Ranger",
        character_class=PoE2CharacterClass.RANGER,
        level=88,
        ascendancy=PoE2Ascendancy.DEADEYE,
        stats=ice_stats,
        estimated_cost=8.5,
        goal=PoE2BuildGoal.CLEAR_SPEED,
        main_skill_gem="Ice Shot",
        support_gems=["Added Cold Damage", "Elemental Damage with Attacks", "Pierce"],
        key_items=["Bow of Frost", "Cold Quiver"],
        league="Standard"
    )
    builds.append(ice_build)
    
    # 构筑3: Budget Monk
    budget_stats = PoE2BuildStats(
        total_dps=350000,
        effective_health_pool=6500,
        fire_resistance=75,
        cold_resistance=75,
        lightning_resistance=75,
        chaos_resistance=-30,
        life=4500,
        energy_shield=2000
    )
    
    budget_build = PoE2Build(
        name="Budget Monk Invoker",
        character_class=PoE2CharacterClass.MONK,
        level=85,
        ascendancy=PoE2Ascendancy.INVOKER,
        stats=budget_stats,
        estimated_cost=2.0,
        goal=PoE2BuildGoal.BUDGET_FRIENDLY,
        main_skill_gem="Spirit Wave",
        support_gems=["Melee Physical Damage", "Increased Area of Effect"],
        key_items=["Basic Staff"],
        league="Standard"
    )
    builds.append(budget_build)
    
    return builds


# ===== 用户请求Fixtures =====
@pytest.fixture
def sample_user_request():
    """样例用户请求"""
    return UserRequest(
        character_class=PoE2CharacterClass.SORCERESS,
        ascendancy=PoE2Ascendancy.STORMWEAVER,
        build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
        max_budget=20.0,
        currency_type="divine",
        preferred_skills=["Lightning Bolt", "Chain Lightning"],
        playstyle="aggressive",
        min_dps=500000,
        min_ehp=7000,
        require_resistance_cap=True,
        include_meta_builds=True,
        generate_pob2_code=True,
        validate_with_pob2=True
    )


@pytest.fixture
def budget_user_request():
    """预算型用户请求"""
    return UserRequest(
        character_class=PoE2CharacterClass.MONK,
        build_goal=PoE2BuildGoal.BUDGET_FRIENDLY,
        max_budget=5.0,
        currency_type="divine",
        playstyle="balanced",
        min_dps=200000,
        min_ehp=5000,
        require_resistance_cap=True,
        include_budget_builds=True,
        generate_pob2_code=False,
        validate_with_pob2=False
    )


# ===== Mock对象Fixtures =====
@pytest.fixture
def mock_rag_engine():
    """Mock RAG引擎"""
    mock = AsyncMock()
    mock.generate_recommendations.return_value = [
        {
            'name': 'RAG Lightning Build',
            'level': 90,
            'estimated_dps': 800000,
            'estimated_ehp': 7500,
            'estimated_cost': 12.0,
            'main_skill': 'Lightning Bolt',
            'support_gems': ['Added Lightning', 'Lightning Penetration'],
            'confidence': 0.85
        },
        {
            'name': 'RAG Ice Build',
            'level': 88,
            'estimated_dps': 650000,
            'estimated_ehp': 8200,
            'estimated_cost': 9.0,
            'main_skill': 'Ice Shot',
            'support_gems': ['Added Cold', 'Pierce'],
            'confidence': 0.78
        }
    ]
    return mock


@pytest.fixture
def mock_market_api():
    """Mock市场API"""
    mock = AsyncMock()
    mock.get_item_price.return_value = {
        'median_price': 3.5,
        'currency': 'divine',
        'confidence': 0.9,
        'sample_size': 150
    }
    return mock


@pytest.fixture
def mock_pob2_local():
    """Mock PoB2本地客户端"""
    mock = AsyncMock()
    mock.is_available.return_value = True
    mock.generate_build_code.return_value = "mock_pob2_import_code_12345"
    mock.calculate_build_stats.return_value = {
        'total_dps': 850000,
        'ehp': 8500,
        'fire_res': 78,
        'cold_res': 76,
        'lightning_res': 77,
        'chaos_res': -25,
        'validation_status': 'valid'
    }
    return mock


@pytest.fixture
def mock_pob2_web():
    """Mock PoB2 Web客户端"""
    mock = AsyncMock()
    mock.generate_build_code.return_value = "mock_web_pob2_code_67890"
    mock.calculate_build_stats.return_value = {
        'total_dps': 750000,
        'ehp': 8000,
        'fire_res': 75,
        'cold_res': 75,
        'lightning_res': 75,
        'chaos_res': -30,
        'validation_status': 'valid'
    }
    return mock


@pytest.fixture
def mock_ninja_scraper():
    """Mock ninja爬虫"""
    mock = AsyncMock()
    mock.get_meta_builds.return_value = [
        {
            'name': 'Meta Lightning Build',
            'class': 'Sorceress',
            'ascendancy': 'Stormweaver',
            'dps': 900000,
            'popularity': 15.5,
            'average_level': 91
        }
    ]
    return mock


@pytest.fixture
def mock_cache_manager():
    """Mock缓存管理器"""
    mock = AsyncMock()
    mock.get.return_value = None  # 默认缓存未命中
    mock.set.return_value = True
    mock.clear.return_value = True
    return mock


# ===== 完整系统Mock =====
@pytest.fixture
def mock_orchestrator_config():
    """Mock协调器配置"""
    return {
        'max_recommendations': 10,
        'timeout_seconds': 30,
        'cache': {
            'ttl_seconds': 600,
            'max_size': 1000
        },
        'rag': {
            'model_name': 'test-model',
            'max_context_length': 4000,
            'similarity_threshold': 0.7
        },
        'pob2': {
            'timeout_seconds': 10,
            'max_retries': 3
        },
        'api_limits': {
            'requests_per_minute': 60,
            'burst_limit': 10
        }
    }


@pytest.fixture
async def initialized_orchestrator(mock_orchestrator_config):
    """已初始化的协调器（使用Mock组件）"""
    orchestrator = PoE2AIOrchestrator(mock_orchestrator_config)
    
    # 手动设置Mock组件（模拟成功初始化）
    orchestrator._rag_engine = AsyncMock()
    orchestrator._market_api = AsyncMock()
    orchestrator._pob2_local = AsyncMock()
    orchestrator._pob2_web = AsyncMock()
    orchestrator._ninja_scraper = AsyncMock()
    orchestrator._cache_manager = AsyncMock()
    
    # 设置组件健康状态
    from src.poe2build.core.ai_orchestrator import ComponentHealth, ComponentStatus
    for component in SystemComponent:
        orchestrator._component_health[component] = ComponentHealth(
            component=component,
            status=ComponentStatus.HEALTHY,
            response_time_ms=50.0,
            last_check=1700000000.0
        )
    
    orchestrator._initialized = True
    return orchestrator


# ===== 测试数据管理 =====
@pytest.fixture
def api_response_samples():
    """API响应样例数据"""
    return {
        'market_prices': {
            'Staff of Power': {'median_price': 15.5, 'currency': 'divine'},
            'Lightning Amulet': {'median_price': 3.2, 'currency': 'divine'},
            'Spell Echo Ring': {'median_price': 1.8, 'currency': 'divine'}
        },
        'ninja_builds': [
            {
                'name': 'Popular Lightning Build',
                'class': 'Sorceress',
                'ascendancy': 'Stormweaver',
                'main_skill': 'Lightning Bolt',
                'dps': 1200000,
                'level': 95,
                'popularity_rank': 1
            },
            {
                'name': 'Budget Ice Shot',
                'class': 'Ranger',
                'ascendancy': 'Deadeye',
                'main_skill': 'Ice Shot',
                'dps': 450000,
                'level': 85,
                'popularity_rank': 8
            }
        ]
    }


@pytest.fixture
def error_scenarios():
    """错误场景数据"""
    return {
        'api_timeout': {
            'error_type': 'TimeoutError',
            'message': 'API request timed out',
            'expected_fallback': True
        },
        'invalid_build_data': {
            'error_type': 'ValidationError',
            'message': 'Invalid build statistics',
            'expected_fallback': False
        },
        'pob2_unavailable': {
            'error_type': 'ConnectionError',
            'message': 'PoB2 client not available',
            'expected_fallback': True
        },
        'rag_model_error': {
            'error_type': 'ModelError',
            'message': 'RAG model inference failed',
            'expected_fallback': True
        }
    }


# ===== 性能测试Fixtures =====
@pytest.fixture
def performance_benchmarks():
    """性能基准数据"""
    return {
        'rag_retrieval_ms': 100,
        'pob2_calculation_ms': 5000,
        'api_response_ms': 2000,
        'memory_usage_mb': 2048,
        'cache_hit_rate_percent': 85
    }


# ===== 测试标记和分类 =====
def pytest_configure(config):
    """pytest配置钩子"""
    # 添加自定义标记
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "integration: 集成测试") 
    config.addinivalue_line("markers", "performance: 性能测试")
    config.addinivalue_line("markers", "e2e: 端到端测试")
    config.addinivalue_line("markers", "slow: 慢速测试")
    config.addinivalue_line("markers", "api: API相关测试")
    config.addinivalue_line("markers", "pob2: PoB2集成测试")
    config.addinivalue_line("markers", "rag: RAG系统测试")
    config.addinivalue_line("markers", "mock: Mock测试")


def pytest_collection_modifyitems(config, items):
    """测试收集钩子 - 自动添加标记"""
    for item in items:
        # 根据路径自动添加标记
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # 根据测试名称添加功能标记
        if "rag" in item.name.lower():
            item.add_marker(pytest.mark.rag)
        if "pob2" in item.name.lower():
            item.add_marker(pytest.mark.pob2)
        if "api" in item.name.lower():
            item.add_marker(pytest.mark.api)
        if "mock" in item.name.lower():
            item.add_marker(pytest.mark.mock)


# ===== 辅助函数 =====
def assert_valid_build(build: PoE2Build):
    """验证构筑对象的有效性"""
    assert build is not None
    assert build.name.strip()
    assert 1 <= build.level <= 100
    assert build.character_class is not None
    
    if build.stats:
        assert build.stats.total_dps >= 0
        assert build.stats.effective_health_pool >= 0
        assert -100 <= build.stats.fire_resistance <= 80
        assert -100 <= build.stats.cold_resistance <= 80
        assert -100 <= build.stats.lightning_resistance <= 80


def assert_valid_user_request(request: UserRequest):
    """验证用户请求的有效性"""
    assert request is not None
    
    if request.max_budget:
        assert request.max_budget > 0
    
    if request.min_dps:
        assert request.min_dps > 0
        
    if request.min_ehp:
        assert request.min_ehp > 0


def create_test_build(**kwargs):
    """创建测试用构筑对象"""
    defaults = {
        'name': 'Test Build',
        'character_class': PoE2CharacterClass.WITCH,
        'level': 85,
        'stats': PoE2BuildStats(
            total_dps=500000,
            effective_health_pool=6000,
            fire_resistance=75,
            cold_resistance=75,
            lightning_resistance=75,
            chaos_resistance=-30
        ),
        'estimated_cost': 10.0,
        'goal': PoE2BuildGoal.ENDGAME_CONTENT
    }
    defaults.update(kwargs)
    return PoE2Build(**defaults)