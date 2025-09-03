# 开发者指南

## 📖 概述

本指南面向想要扩展、改进或贡献PoE2智能构筑生成器的开发者。涵盖架构设计、代码规范、测试策略和贡献流程。

## 🏗️ 开发环境设置

### 环境要求

```bash
# Python版本
Python 3.8+

# 核心依赖
requests>=2.31.0
beautifulsoup4>=4.12.0

# 开发依赖 (可选)
pytest>=7.0.0          # 测试框架
black>=23.0.0           # 代码格式化
flake8>=6.0.0           # 代码检查
mypy>=1.0.0             # 类型检查
```

### 开发环境安装

```bash
# 1. 克隆项目
git clone https://github.com/zhakil/poe2build.git
cd poe2build

# 2. 创建开发环境
python -m venv poe2_dev_env
poe2_dev_env\Scripts\activate  # Windows
# source poe2_dev_env/bin/activate  # Linux/Mac

# 3. 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖

# 4. 验证安装
python -c "from poe2_real_data_sources import PoE2RealDataOrchestrator; print('安装成功')"
```

### IDE配置

**Visual Studio Code 推荐配置**:

```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./poe2_dev_env/Scripts/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.testing.pytestEnabled": true
}
```

## 🏛️ 架构深入理解

### 核心设计模式

#### 1. Strategy Pattern (策略模式)
```python
# 不同数据源使用统一接口
class PoE2DataSourceStrategy:
    def get_data(self, query: Dict) -> Dict:
        raise NotImplementedError

class PoE2ScoutStrategy(PoE2DataSourceStrategy):
    def get_data(self, query: Dict) -> Dict:
        # PoE2 Scout特定实现
        pass

class PoE2DBStrategy(PoE2DataSourceStrategy):
    def get_data(self, query: Dict) -> Dict:
        # PoE2DB特定实现
        pass
```

#### 2. Factory Pattern (工厂模式)
```python
class PoE2DataSourceFactory:
    @staticmethod
    def create_data_source(source_type: str) -> PoE2DataSourceStrategy:
        if source_type == "scout":
            return PoE2ScoutStrategy()
        elif source_type == "poe2db":
            return PoE2DBStrategy()
        elif source_type == "ninja":
            return PoE2NinjaStrategy()
        else:
            raise ValueError(f"Unknown source type: {source_type}")
```

#### 3. Observer Pattern (观察者模式)
```python
class PoE2DataSourceObserver:
    def on_data_updated(self, source: str, data: Dict):
        pass

class PoE2BuildRecommendationService(PoE2DataSourceObserver):
    def on_data_updated(self, source: str, data: Dict):
        # 数据更新时重新计算推荐
        self.recalculate_recommendations()
```

### 依赖注入系统

```python
class PoE2DependencyContainer:
    """PoE2依赖注入容器"""
    
    def __init__(self):
        self._services = {}
        self._singletons = {}
    
    def register(self, interface: type, implementation: type, singleton: bool = False):
        """注册服务"""
        self._services[interface] = (implementation, singleton)
    
    def get(self, interface: type):
        """获取服务实例"""
        if interface not in self._services:
            raise ValueError(f"Service {interface} not registered")
        
        implementation, is_singleton = self._services[interface]
        
        if is_singleton:
            if interface not in self._singletons:
                self._singletons[interface] = implementation()
            return self._singletons[interface]
        
        return implementation()

# 使用示例
container = PoE2DependencyContainer()
container.register(PoE2ScoutAPI, PoE2ScoutAPI, singleton=True)
container.register(PoE2DBScraper, PoE2DBScraper, singleton=True)

# 在Orchestrator中使用
class PoE2RealDataOrchestrator:
    def __init__(self, container: PoE2DependencyContainer):
        self.poe2_scout = container.get(PoE2ScoutAPI)
        self.poe2db = container.get(PoE2DBScraper)
```

## 🔧 扩展开发

### 添加新的PoE2数据源

#### 1. 创建数据源类
```python
class NewPoE2DataSource(PoE2RealDataProvider):
    """新的PoE2数据源示例"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://new-poe2-service.com"
        self.api_key = os.getenv('NEW_POE2_API_KEY')
        
    def get_build_data(self, query: Dict) -> Dict:
        """获取构筑数据"""
        cache_key = f"new_source_builds_{hash(str(query))}"
        cached = self._get_from_cache(cache_key, 1800)
        if cached:
            return cached
        
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            response = self.session.get(
                f"{self.base_url}/api/builds",
                headers=headers,
                params=query,
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            processed_data = self._process_build_data(data)
            
            self._set_cache(cache_key, processed_data)
            return processed_data
            
        except Exception as e:
            print(f"[NewPoE2DataSource] Error: {e}")
            return self._get_fallback_data()
    
    def _process_build_data(self, raw_data: Dict) -> Dict:
        """处理原始数据为标准格式"""
        processed_builds = []
        
        for raw_build in raw_data.get('builds', []):
            build = {
                'name': raw_build.get('name', 'Unknown'),
                'class': raw_build.get('character_class', 'Unknown'),
                'ascendancy': raw_build.get('ascendancy_class', 'Unknown'),
                'level': raw_build.get('level', 85),
                'dps': raw_build.get('damage_per_second', 0),
                'source': 'new_poe2_service'
            }
            processed_builds.append(build)
        
        return {
            'status': 'success',
            'builds': processed_builds,
            'timestamp': time.time()
        }
```

#### 2. 集成到系统中
```python
# 扩展Orchestrator
class ExtendedPoE2Orchestrator(PoE2RealDataOrchestrator):
    def __init__(self):
        super().__init__()
        self.new_source = NewPoE2DataSource()
    
    def create_poe2_build_recommendation(self, user_request: Dict) -> Dict:
        # 调用父类方法获取基础推荐
        base_result = super().create_poe2_build_recommendation(user_request)
        
        # 从新数据源获取补充数据
        try:
            new_builds = self.new_source.get_build_data(user_request['preferences'])
            # 合并数据
            base_result['additional_sources'] = new_builds
        except Exception as e:
            print(f"New source failed: {e}")
        
        return base_result
```

### 扩展计算引擎

#### 1. 添加新的计算功能
```python
class ExtendedPoE2Calculator(PoE2RealBuildCalculator):
    """扩展的PoE2计算引擎"""
    
    def calculate_dps_vs_boss(self, build_config: Dict, boss_type: str) -> Dict:
        """计算对特定Boss的DPS"""
        base_calculation = self.calculate_poe2_build(build_config)
        
        # Boss特定修正
        boss_modifiers = self._get_boss_modifiers(boss_type)
        
        # 调整计算
        adjusted_dps = self._apply_boss_modifiers(
            base_calculation['dps'],
            boss_modifiers
        )
        
        return {
            **base_calculation,
            'boss_specific': {
                'boss_type': boss_type,
                'adjusted_dps': adjusted_dps,
                'effectiveness_rating': self._rate_boss_effectiveness(adjusted_dps)
            }
        }
    
    def _get_boss_modifiers(self, boss_type: str) -> Dict:
        """获取Boss修正数据"""
        boss_data = {
            'pinnacle_boss': {
                'damage_reduction': 0.15,  # 15%伤害减免
                'resistance_penetration': -10,  # -10%穿透
                'chaos_immunity': True
            },
            'map_boss': {
                'damage_reduction': 0.05,
                'resistance_penetration': 0,
                'chaos_immunity': False
            }
        }
        
        return boss_data.get(boss_type, {})
    
    def calculate_leveling_progression(self, build_config: Dict) -> Dict:
        """计算升级进度"""
        progression = {}
        
        for level in range(1, 101, 10):  # 每10级一个检查点
            level_config = {**build_config, 'level': level}
            level_stats = self.calculate_poe2_build(level_config)
            
            progression[level] = {
                'dps': level_stats['dps']['total_dps'],
                'ehp': level_stats['survivability']['total_ehp'],
                'resistances': level_stats['defenses']
            }
        
        return {
            'progression': progression,
            'power_spikes': self._identify_power_spikes(progression),
            'weak_points': self._identify_weak_points(progression)
        }
```

#### 2. 新的计算算法
```python
def calculate_poe2_energy_shield_advanced(self, level: int, items: Dict, passives: Dict) -> Dict:
    """高级能量护盾计算 - 包含天赋树"""
    
    # 基础计算
    base_calculation = self._calculate_poe2_energy_shield(level, items)
    
    # 天赋树加成
    passive_bonuses = self._calculate_passive_es_bonuses(passives)
    
    # 升华职业特殊加成
    ascendancy = items.get('ascendancy', '')
    ascendancy_bonuses = self._get_ascendancy_es_bonuses(ascendancy)
    
    # 更复杂的ES交互
    final_es = self._apply_advanced_es_interactions(
        base_calculation['total_energy_shield'],
        passive_bonuses,
        ascendancy_bonuses
    )
    
    return {
        **base_calculation,
        'advanced_calculation': {
            'passive_contribution': passive_bonuses,
            'ascendancy_contribution': ascendancy_bonuses,
            'final_energy_shield': final_es,
            'efficiency_rating': final_es / (level * 50)  # 效率评分
        }
    }
```

### 添加新的推荐算法

```python
class AdvancedPoE2RecommendationEngine:
    """高级PoE2推荐引擎"""
    
    def __init__(self, orchestrator: PoE2RealDataOrchestrator):
        self.orchestrator = orchestrator
        self.ml_model = self._load_ml_model()  # 可选的机器学习模型
    
    def generate_smart_recommendations(self, user_request: Dict, user_history: List[Dict] = None) -> Dict:
        """基于用户历史的智能推荐"""
        
        # 获取基础推荐
        base_recommendations = self.orchestrator.create_poe2_build_recommendation(user_request)
        
        # 分析用户历史偏好
        if user_history:
            user_preferences = self._analyze_user_preferences(user_history)
            
            # 调整推荐权重
            adjusted_recommendations = self._adjust_recommendations_by_preference(
                base_recommendations,
                user_preferences
            )
        else:
            adjusted_recommendations = base_recommendations
        
        # 添加创新推荐
        innovative_builds = self._generate_innovative_builds(user_request)
        
        return {
            **adjusted_recommendations,
            'personalized': True,
            'innovative_builds': innovative_builds,
            'confidence_scores': self._calculate_confidence_scores(adjusted_recommendations)
        }
    
    def _analyze_user_preferences(self, history: List[Dict]) -> Dict:
        """分析用户历史偏好"""
        preferences = {
            'preferred_classes': Counter(),
            'preferred_skills': Counter(),
            'budget_range': [],
            'complexity_preference': []
        }
        
        for build in history:
            preferences['preferred_classes'][build.get('class', 'Unknown')] += 1
            preferences['preferred_skills'][build.get('main_skill', 'Unknown')] += 1
            
            if 'budget' in build:
                preferences['budget_range'].append(build['budget']['amount'])
        
        return {
            'top_class': preferences['preferred_classes'].most_common(1)[0][0] if preferences['preferred_classes'] else None,
            'top_skill': preferences['preferred_skills'].most_common(1)[0][0] if preferences['preferred_skills'] else None,
            'avg_budget': sum(preferences['budget_range']) / len(preferences['budget_range']) if preferences['budget_range'] else 10
        }
```

## 🧪 测试策略

### 单元测试

```python
# tests/test_poe2_data_sources.py
import pytest
from unittest.mock import Mock, patch
from poe2_real_data_sources import PoE2ScoutAPI, PoE2DBScraper

class TestPoE2ScoutAPI:
    def setup_method(self):
        self.scout_api = PoE2ScoutAPI()
    
    @patch('requests.Session.get')
    def test_get_market_data_success(self, mock_get):
        """测试市场数据获取成功"""
        # Mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'data': {'items': [{'name': 'Test Item', 'price': 5}]}
        }
        mock_get.return_value = mock_response
        
        # 执行测试
        result = self.scout_api.get_market_data()
        
        # 验证结果
        assert result['status'] == 'success'
        assert 'data' in result
        assert len(result['data']['items']) > 0
    
    @patch('requests.Session.get')
    def test_get_market_data_failure(self, mock_get):
        """测试市场数据获取失败"""
        # Mock网络错误
        mock_get.side_effect = requests.RequestException("Network error")
        
        # 执行测试
        result = self.scout_api.get_market_data()
        
        # 验证降级行为
        assert result['status'] == 'mock'
        assert 'data' in result
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        # 设置缓存
        test_data = {'test': 'data'}
        self.scout_api._set_cache('test_key', test_data)
        
        # 获取缓存
        cached_data = self.scout_api._get_from_cache('test_key', 3600)
        
        # 验证缓存
        assert cached_data == test_data

class TestPoE2Calculator:
    def setup_method(self):
        mock_poe2db = Mock()
        mock_poe2db.get_skill_data.return_value = {'skills': []}
        mock_poe2db.get_item_data.return_value = {'items': []}
        
        self.calculator = PoE2RealBuildCalculator(mock_poe2db)
    
    def test_poe2_dps_calculation(self):
        """测试PoE2 DPS计算"""
        build_config = {
            'main_skill': 'Lightning Arrow',
            'weapon': 'Lightning Bow',
            'level': 85
        }
        
        result = self.calculator.calculate_poe2_build(build_config)
        
        # 验证结果结构
        assert 'dps' in result
        assert 'total_dps' in result['dps']
        assert result['dps']['total_dps'] > 0
    
    def test_poe2_defense_calculation(self):
        """测试PoE2防御计算"""
        build_config = {
            'level': 85,
            'items': {'armor': {'resistance_bonus': 20}}
        }
        
        result = self.calculator.calculate_poe2_build(build_config)
        
        # 验证PoE2特有的80%抗性上限
        defenses = result['defenses']
        for res_type in ['fire_resistance', 'cold_resistance', 'lightning_resistance']:
            assert defenses[res_type] <= 80  # PoE2最大抗性
    
    def test_energy_shield_calculation(self):
        """测试能量护盾计算"""
        build_config = {
            'level': 85,
            'items': {'armor': {'energy_shield': 300}}
        }
        
        result = self.calculator.calculate_poe2_build(build_config)
        
        # 验证能量护盾计算
        assert 'survivability' in result
        assert 'total_energy_shield' in result['survivability']
        assert result['survivability']['total_energy_shield'] > 0

# 运行测试
if __name__ == "__main__":
    pytest.main(["-v", "tests/"])
```

### 集成测试

```python
# tests/test_integration.py
import pytest
from poe2_real_data_sources import PoE2RealDataOrchestrator

class TestPoE2Integration:
    def setup_method(self):
        self.orchestrator = PoE2RealDataOrchestrator()
    
    @pytest.mark.integration
    def test_full_recommendation_flow(self):
        """测试完整推荐流程"""
        request = {
            'game': 'poe2',
            'mode': 'standard',
            'preferences': {
                'class': 'Ranger',
                'style': 'bow',
                'budget': {'amount': 10, 'currency': 'divine'}
            }
        }
        
        result = self.orchestrator.create_poe2_build_recommendation(request)
        
        # 验证结果完整性
        assert 'recommendations' in result
        assert len(result['recommendations']) > 0
        
        for rec in result['recommendations']:
            assert 'build_name' in rec
            assert 'stats' in rec
            assert 'estimated_cost' in rec
    
    @pytest.mark.integration
    def test_data_source_connectivity(self):
        """测试数据源连接性"""
        # 测试PoE2 Scout
        scout_data = self.orchestrator.poe2_scout.get_market_data()
        assert 'status' in scout_data
        
        # 测试PoE2DB
        poe2db_data = self.orchestrator.poe2db.get_skill_data()
        assert 'skills' in poe2db_data
        
        # 测试poe.ninja
        ninja_data = self.orchestrator.poe2_ninja.get_popular_builds()
        assert isinstance(ninja_data, list)
    
    @pytest.mark.slow
    def test_performance_benchmarks(self):
        """性能基准测试"""
        import time
        
        request = {
            'game': 'poe2',
            'preferences': {'class': 'Ranger', 'style': 'bow'}
        }
        
        start_time = time.time()
        result = self.orchestrator.create_poe2_build_recommendation(request)
        end_time = time.time()
        
        # 验证性能要求
        execution_time = end_time - start_time
        assert execution_time < 30  # 30秒内完成
        assert len(result['recommendations']) > 0
```

### 模拟测试

```python
# tests/test_mocks.py
from unittest.mock import Mock, patch
import pytest
from poe2_real_data_sources import PoE2RealDataOrchestrator

class TestPoE2Mocks:
    @patch('poe2_real_data_sources.PoE2ScoutAPI')
    @patch('poe2_real_data_sources.PoE2DBScraper')
    @patch('poe2_real_data_sources.PoE2NinjaScraper')
    def test_orchestrator_with_mocked_sources(self, mock_ninja, mock_db, mock_scout):
        """测试使用模拟数据源的协调器"""
        
        # 设置模拟返回值
        mock_scout.return_value.get_market_data.return_value = {
            'status': 'success',
            'data': {'popular_items': []}
        }
        
        mock_db.return_value.get_skill_data.return_value = {
            'skills': [{'name': 'Lightning Arrow', 'base_damage': 120}]
        }
        
        mock_ninja.return_value.get_popular_builds.return_value = [
            {'name': 'Test Build', 'class': 'Ranger', 'level': 85}
        ]
        
        # 创建协调器
        orchestrator = PoE2RealDataOrchestrator()
        
        # 执行测试
        request = {'game': 'poe2', 'preferences': {'class': 'Ranger'}}
        result = orchestrator.create_poe2_build_recommendation(request)
        
        # 验证模拟调用
        mock_scout.return_value.get_market_data.assert_called()
        mock_ninja.return_value.get_popular_builds.assert_called()
```

## 📋 代码规范

### Python代码风格

```python
# 好的代码示例
class PoE2DataProcessor:
    """PoE2数据处理器
    
    处理来自各种PoE2数据源的原始数据，
    转换为标准化的内部格式。
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.logger = self._setup_logger()
    
    def process_build_data(self, raw_data: Dict[str, Any]) -> List[PoE2Build]:
        """处理构筑数据
        
        Args:
            raw_data: 来自数据源的原始数据
            
        Returns:
            标准化的PoE2构筑列表
            
        Raises:
            ValidationError: 当数据格式无效时
        """
        if not self._validate_raw_data(raw_data):
            raise ValidationError("Invalid data format")
        
        builds = []
        for raw_build in raw_data.get('builds', []):
            build = self._create_build_from_raw(raw_build)
            if build:
                builds.append(build)
        
        return builds
    
    def _validate_raw_data(self, data: Dict[str, Any]) -> bool:
        """验证原始数据格式"""
        required_fields = ['builds', 'timestamp']
        return all(field in data for field in required_fields)
    
    def _create_build_from_raw(self, raw_build: Dict[str, Any]) -> Optional[PoE2Build]:
        """从原始数据创建构筑对象"""
        try:
            return PoE2Build(
                name=raw_build['name'],
                character_class=raw_build['class'],
                level=int(raw_build['level']),
                skills=raw_build.get('skills', [])
            )
        except (KeyError, ValueError) as e:
            self.logger.warning(f"Failed to create build: {e}")
            return None
```

### 类型注解

```python
from typing import Dict, List, Optional, Union, Protocol
from dataclasses import dataclass
from enum import Enum

# 使用数据类
@dataclass
class PoE2BuildConfig:
    main_skill: str
    weapon: str
    level: int
    items: Dict[str, Dict[str, Union[str, int]]]
    
    def validate(self) -> bool:
        """验证配置有效性"""
        return (
            self.level > 0 and 
            self.level <= 100 and
            len(self.main_skill) > 0
        )

# 使用枚举
class PoE2CharacterClass(Enum):
    RANGER = "Ranger"
    SORCERESS = "Sorceress"
    WARRIOR = "Warrior"
    MONK = "Monk"
    WITCH = "Witch"
    MERCENARY = "Mercenary"

# 使用协议
class PoE2DataSource(Protocol):
    def get_data(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """获取数据的标准接口"""
        ...
    
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        ...
```

### 错误处理

```python
class PoE2Error(Exception):
    """PoE2系统基础异常"""
    pass

class PoE2DataSourceError(PoE2Error):
    """数据源相关错误"""
    pass

class PoE2CalculationError(PoE2Error):
    """计算相关错误"""
    pass

class PoE2ValidationError(PoE2Error):
    """数据验证错误"""
    pass

# 错误处理示例
def safe_api_call(func, *args, **kwargs):
    """安全的API调用包装器"""
    try:
        return func(*args, **kwargs)
    except requests.RequestException as e:
        raise PoE2DataSourceError(f"Network error: {e}") from e
    except ValueError as e:
        raise PoE2ValidationError(f"Data validation error: {e}") from e
    except Exception as e:
        raise PoE2Error(f"Unexpected error: {e}") from e
```

## 🔍 调试和分析工具

### 日志系统

```python
import logging
from typing import Dict, Any

class PoE2Logger:
    """PoE2专用日志系统"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 文件处理器
        file_handler = logging.FileHandler('poe2_debug.log')
        file_handler.setLevel(logging.DEBUG)
        
        # 格式化
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def log_api_call(self, source: str, url: str, status: str, response_time: float):
        """记录API调用"""
        self.logger.info(
            f"API_CALL | Source: {source} | URL: {url} | "
            f"Status: {status} | Time: {response_time:.2f}s"
        )
    
    def log_calculation(self, build_name: str, calc_time: float, result: Dict[str, Any]):
        """记录计算过程"""
        self.logger.debug(
            f"CALCULATION | Build: {build_name} | Time: {calc_time:.3f}s | "
            f"DPS: {result.get('dps', {}).get('total_dps', 0):,}"
        )
```

### 性能分析器

```python
import time
import functools
from typing import Dict, List

class PoE2Profiler:
    """PoE2性能分析器"""
    
    def __init__(self):
        self.call_stats = {}
    
    def profile(self, func):
        """性能分析装饰器"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                status = 'success'
            except Exception as e:
                result = None
                status = f'error: {type(e).__name__}'
                raise
            finally:
                end_time = time.time()
                execution_time = end_time - start_time
                
                # 记录统计信息
                func_name = f"{func.__module__}.{func.__name__}"
                if func_name not in self.call_stats:
                    self.call_stats[func_name] = []
                
                self.call_stats[func_name].append({
                    'execution_time': execution_time,
                    'status': status,
                    'timestamp': time.time()
                })
            
            return result
        return wrapper
    
    def get_performance_report(self) -> Dict[str, Dict[str, float]]:
        """生成性能报告"""
        report = {}
        
        for func_name, calls in self.call_stats.items():
            successful_calls = [c for c in calls if c['status'] == 'success']
            times = [c['execution_time'] for c in successful_calls]
            
            if times:
                report[func_name] = {
                    'call_count': len(calls),
                    'success_rate': len(successful_calls) / len(calls),
                    'avg_time': sum(times) / len(times),
                    'max_time': max(times),
                    'min_time': min(times)
                }
        
        return report

# 使用示例
profiler = PoE2Profiler()

@profiler.profile
def expensive_calculation():
    time.sleep(1)  # 模拟耗时操作
    return "result"
```

## 🚀 部署和发布

### 版本控制

```python
# version.py
__version__ = "2.0.0"
__version_info__ = (2, 0, 0)

# 语义化版本控制
# MAJOR.MINOR.PATCH
# MAJOR: 不兼容的API变更
# MINOR: 向后兼容的功能添加
# PATCH: 向后兼容的错误修复
```

### 打包配置

```python
# setup.py
from setuptools import setup, find_packages
from version import __version__

setup(
    name="poe2-build-generator",
    version=__version__,
    description="智能PoE2构筑生成器",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="PoE2 Build Generator Team",
    author_email="dev@poe2build.com",
    url="https://github.com/zhakil/poe2build",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "poe2build=poe2_real_data_sources:main",
        ],
    },
)
```

## 🤝 贡献流程

### Git工作流

```bash
# 1. Fork并克隆项目
git clone https://github.com/your-username/poe2build.git
cd poe2build

# 2. 创建开发分支
git checkout -b feature/new-poe2-feature

# 3. 进行开发
# 编辑代码...

# 4. 运行测试
python -m pytest tests/
python -m black poe2_real_data_sources.py
python -m flake8 poe2_real_data_sources.py

# 5. 提交更改
git add .
git commit -m "feat: 添加新的PoE2功能

详细描述功能的作用和实现方式。

- 添加了新的数据源集成
- 优化了计算性能
- 增加了单元测试覆盖率

Fixes #123"

# 6. 推送分支
git push origin feature/new-poe2-feature

# 7. 创建Pull Request
# 在GitHub上创建PR
```

### 提交信息规范

```
类型(范围): 简短描述

详细描述（可选）

相关Issue（可选）
```

**提交类型**:
- `feat`: 新功能
- `fix`: 错误修复
- `docs`: 文档更新
- `style`: 代码格式化
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具更新

### Code Review检查清单

**功能性**:
- [ ] 功能按预期工作
- [ ] 处理所有边界情况
- [ ] 包含适当的错误处理
- [ ] 有足够的测试覆盖率

**代码质量**:
- [ ] 代码清晰易读
- [ ] 遵循项目代码规范
- [ ] 有适当的类型注解
- [ ] 包含必要的文档字符串

**性能和安全**:
- [ ] 没有明显的性能问题
- [ ] 没有安全漏洞
- [ ] 正确处理用户输入
- [ ] 适当的资源管理

**集成**:
- [ ] 与现有代码良好集成
- [ ] 不破坏现有功能
- [ ] API变更有适当的版本控制
- [ ] 文档已更新

---

**总结**: 这个开发者指南提供了扩展和贡献PoE2智能构筑生成器的完整框架。遵循这些指导原则，可以确保代码质量、系统稳定性和项目的长期维护性。