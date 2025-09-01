"""
高级测试配置 - 测试环境配置和管理

提供高级的测试环境配置，包括：
- 不同测试环境的配置
- 数据库连接配置  
- 网络测试设置
- 性能测试参数
"""

import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum


class TestEnvironment(Enum):
    """测试环境类型"""
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    E2E = "e2e"
    CI = "ci"
    LOCAL = "local"


class TestMode(Enum):
    """测试模式"""
    FAST = "fast"  # 快速测试，跳过慢速测试
    FULL = "full"  # 完整测试
    SMOKE = "smoke"  # 烟雾测试，仅基本功能
    STRESS = "stress"  # 压力测试


@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str = "localhost"
    port: int = 5432
    database: str = "poe2build_test"
    username: str = "test_user"
    password: str = "test_pass"
    max_connections: int = 10
    timeout_seconds: int = 30
    use_in_memory: bool = True  # 测试使用内存数据库


@dataclass
class NetworkConfig:
    """网络测试配置"""
    mock_external_apis: bool = True
    api_timeout_seconds: int = 10
    retry_attempts: int = 3
    rate_limit_enabled: bool = True
    mock_delays: Dict[str, float] = field(default_factory=lambda: {
        'poe2scout_api': 0.1,
        'ninja_scraper': 0.2,
        'pob2_local': 0.5,
        'pob2_web': 2.0
    })


@dataclass 
class PerformanceConfig:
    """性能测试配置"""
    max_response_time_ms: int = 2000
    max_memory_usage_mb: int = 1024
    min_throughput_rps: float = 5.0
    concurrent_users: int = 20
    test_duration_seconds: int = 60
    warmup_requests: int = 10
    
    # 基准指标
    baseline_metrics: Dict[str, float] = field(default_factory=lambda: {
        'avg_response_time_ms': 800,
        'p95_response_time_ms': 1500,
        'p99_response_time_ms': 2000,
        'memory_usage_mb': 512,
        'throughput_rps': 10.0,
        'cache_hit_rate': 0.85
    })


@dataclass
class CacheConfig:
    """缓存测试配置"""
    enabled: bool = True
    backend: str = "memory"  # memory, redis, memcached
    max_size: int = 1000
    ttl_seconds: int = 600
    redis_url: str = "redis://localhost:6379/1"
    clear_before_tests: bool = True


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    console_output: bool = True
    capture_warnings: bool = True
    test_logs_dir: str = "logs/tests"


class TestConfig:
    """测试配置管理器"""
    
    def __init__(self, 
                 environment: TestEnvironment = TestEnvironment.LOCAL,
                 mode: TestMode = TestMode.FAST):
        self.environment = environment
        self.mode = mode
        self._config_cache = {}
        
        # 加载配置
        self._load_base_config()
        self._load_environment_config()
        self._apply_mode_overrides()
        
    def _load_base_config(self):
        """加载基础配置"""
        self.database = DatabaseConfig()
        self.network = NetworkConfig()
        self.performance = PerformanceConfig()
        self.cache = CacheConfig()
        self.logging = LoggingConfig()
        
        # 基础目录配置
        self.project_root = Path(__file__).parent.parent
        self.tests_root = self.project_root / "tests"
        self.fixtures_dir = self.tests_root / "fixtures"
        self.reports_dir = self.project_root / "test_reports"
        self.temp_dir = self.project_root / "temp" / "tests"
        
        # 创建必要目录
        self.reports_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_environment_config(self):
        """根据环境加载配置"""
        env_configs = {
            TestEnvironment.UNIT: self._get_unit_config,
            TestEnvironment.INTEGRATION: self._get_integration_config,
            TestEnvironment.PERFORMANCE: self._get_performance_config,
            TestEnvironment.E2E: self._get_e2e_config,
            TestEnvironment.CI: self._get_ci_config,
            TestEnvironment.LOCAL: self._get_local_config
        }
        
        config_func = env_configs.get(self.environment, self._get_local_config)
        config_func()
        
    def _get_unit_config(self):
        """单元测试配置"""
        self.network.mock_external_apis = True
        self.network.api_timeout_seconds = 5
        self.cache.enabled = False  # 单元测试不需要缓存
        self.database.use_in_memory = True
        self.performance.max_response_time_ms = 100
        
    def _get_integration_config(self):
        """集成测试配置"""
        self.network.mock_external_apis = False  # 可能需要真实API
        self.network.api_timeout_seconds = 30
        self.cache.enabled = True
        self.cache.clear_before_tests = True
        self.database.use_in_memory = False
        
    def _get_performance_config(self):
        """性能测试配置"""
        self.network.mock_external_apis = True  # 排除网络延迟影响
        self.performance.concurrent_users = 50
        self.performance.test_duration_seconds = 300  # 5分钟
        self.performance.warmup_requests = 20
        self.cache.enabled = True
        self.cache.max_size = 10000
        
    def _get_e2e_config(self):
        """端到端测试配置"""
        self.network.mock_external_apis = False  # 真实环境
        self.network.api_timeout_seconds = 60
        self.cache.enabled = True
        self.cache.backend = "redis"  # 使用持久化缓存
        self.database.use_in_memory = False
        
    def _get_ci_config(self):
        """CI/CD环境配置"""
        self.network.mock_external_apis = True
        self.network.api_timeout_seconds = 10
        self.cache.enabled = True
        self.cache.backend = "memory"
        self.database.use_in_memory = True
        self.performance.test_duration_seconds = 60  # CI中减少测试时间
        self.logging.level = "WARNING"  # 减少CI日志
        
    def _get_local_config(self):
        """本地开发配置"""
        self.network.mock_external_apis = True
        self.cache.enabled = True
        self.cache.backend = "memory"
        self.database.use_in_memory = True
        self.logging.level = "DEBUG"
        self.logging.console_output = True
        
    def _apply_mode_overrides(self):
        """根据测试模式应用覆盖配置"""
        mode_overrides = {
            TestMode.FAST: self._apply_fast_mode,
            TestMode.FULL: self._apply_full_mode,
            TestMode.SMOKE: self._apply_smoke_mode,
            TestMode.STRESS: self._apply_stress_mode
        }
        
        override_func = mode_overrides.get(self.mode)
        if override_func:
            override_func()
            
    def _apply_fast_mode(self):
        """快速测试模式"""
        self.performance.test_duration_seconds = 30
        self.performance.concurrent_users = 10
        self.performance.warmup_requests = 5
        self.network.api_timeout_seconds = 5
        
    def _apply_full_mode(self):
        """完整测试模式"""
        self.performance.test_duration_seconds = 600  # 10分钟
        self.performance.concurrent_users = 100
        self.performance.warmup_requests = 50
        
    def _apply_smoke_mode(self):
        """烟雾测试模式"""
        self.performance.test_duration_seconds = 10
        self.performance.concurrent_users = 1
        self.performance.warmup_requests = 1
        self.network.api_timeout_seconds = 2
        
    def _apply_stress_mode(self):
        """压力测试模式"""
        self.performance.test_duration_seconds = 1800  # 30分钟
        self.performance.concurrent_users = 200
        self.performance.warmup_requests = 100
        
    def get_pytest_args(self) -> List[str]:
        """获取pytest命令行参数"""
        args = []
        
        # 根据环境添加标记
        if self.environment == TestEnvironment.UNIT:
            args.extend(["-m", "unit"])
        elif self.environment == TestEnvironment.INTEGRATION:
            args.extend(["-m", "integration"])
        elif self.environment == TestEnvironment.PERFORMANCE:
            args.extend(["-m", "performance"])
        elif self.environment == TestEnvironment.E2E:
            args.extend(["-m", "e2e"])
            
        # 根据模式添加参数
        if self.mode == TestMode.FAST:
            args.extend(["-m", "not slow"])  # 跳过慢速测试
        elif self.mode == TestMode.SMOKE:
            args.extend(["-m", "smoke or (unit and not slow)"])
        elif self.mode == TestMode.STRESS:
            args.extend(["-m", "performance or stress"])
            
        # 添加报告路径
        args.extend([
            f"--html={self.reports_dir}/report.html",
            f"--junit-xml={self.reports_dir}/junit.xml",
            f"--cov-report=html:{self.reports_dir}/coverage",
            f"--cov-report=xml:{self.reports_dir}/coverage.xml"
        ])
        
        # 添加并发参数
        if self.mode != TestMode.SMOKE:
            args.extend(["-n", "auto"])  # 并发执行
        
        return args
        
    def get_environment_variables(self) -> Dict[str, str]:
        """获取环境变量"""
        env_vars = {
            'TEST_ENVIRONMENT': self.environment.value,
            'TEST_MODE': self.mode.value,
            'PYTHONPATH': str(self.project_root),
            'TEST_REPORTS_DIR': str(self.reports_dir),
            'TEST_TEMP_DIR': str(self.temp_dir)
        }
        
        # 数据库配置
        if not self.database.use_in_memory:
            env_vars.update({
                'DB_HOST': self.database.host,
                'DB_PORT': str(self.database.port),
                'DB_NAME': self.database.database,
                'DB_USER': self.database.username,
                'DB_PASS': self.database.password
            })
        
        # 缓存配置
        if self.cache.enabled:
            env_vars.update({
                'CACHE_BACKEND': self.cache.backend,
                'CACHE_MAX_SIZE': str(self.cache.max_size),
                'CACHE_TTL': str(self.cache.ttl_seconds)
            })
            
            if self.cache.backend == "redis":
                env_vars['REDIS_URL'] = self.cache.redis_url
        
        # 性能测试配置
        env_vars.update({
            'PERF_MAX_RESPONSE_TIME': str(self.performance.max_response_time_ms),
            'PERF_MAX_MEMORY': str(self.performance.max_memory_usage_mb),
            'PERF_MIN_THROUGHPUT': str(self.performance.min_throughput_rps),
            'PERF_CONCURRENT_USERS': str(self.performance.concurrent_users),
            'PERF_TEST_DURATION': str(self.performance.test_duration_seconds)
        })
        
        return env_vars
    
    def save_config_report(self) -> str:
        """保存配置报告"""
        config_data = {
            'environment': self.environment.value,
            'mode': self.mode.value,
            'timestamp': datetime.utcnow().isoformat(),
            'database': {
                'host': self.database.host,
                'port': self.database.port,
                'use_in_memory': self.database.use_in_memory
            },
            'network': {
                'mock_external_apis': self.network.mock_external_apis,
                'api_timeout_seconds': self.network.api_timeout_seconds,
                'rate_limit_enabled': self.network.rate_limit_enabled
            },
            'cache': {
                'enabled': self.cache.enabled,
                'backend': self.cache.backend,
                'max_size': self.cache.max_size
            },
            'performance': {
                'max_response_time_ms': self.performance.max_response_time_ms,
                'concurrent_users': self.performance.concurrent_users,
                'test_duration_seconds': self.performance.test_duration_seconds
            },
            'paths': {
                'project_root': str(self.project_root),
                'tests_root': str(self.tests_root),
                'reports_dir': str(self.reports_dir),
                'temp_dir': str(self.temp_dir)
            }
        }
        
        report_file = self.reports_dir / "test_config.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        return str(report_file)
    
    def validate_environment(self) -> List[str]:
        """验证测试环境"""
        issues = []
        
        # 检查必要目录
        required_dirs = [self.tests_root, self.fixtures_dir]
        for directory in required_dirs:
            if not directory.exists():
                issues.append(f"Required directory missing: {directory}")
        
        # 检查数据库连接
        if not self.database.use_in_memory:
            try:
                # 这里可以添加实际的数据库连接检查
                pass
            except Exception as e:
                issues.append(f"Database connection failed: {e}")
        
        # 检查缓存连接
        if self.cache.enabled and self.cache.backend == "redis":
            try:
                # 这里可以添加Redis连接检查
                pass
            except Exception as e:
                issues.append(f"Redis connection failed: {e}")
        
        # 检查权限
        test_file = self.temp_dir / "test_permissions.txt"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            issues.append(f"File system permissions issue: {e}")
        
        return issues


# =============================================================================
# 全局配置实例
# =============================================================================

# 从环境变量获取配置
env_name = os.getenv('TEST_ENVIRONMENT', 'local').upper()
mode_name = os.getenv('TEST_MODE', 'fast').upper()

try:
    environment = TestEnvironment(env_name.lower())
except ValueError:
    environment = TestEnvironment.LOCAL

try:
    mode = TestMode(mode_name.lower())
except ValueError:
    mode = TestMode.FAST

# 全局配置实例
test_config = TestConfig(environment=environment, mode=mode)


# =============================================================================
# 便捷函数
# =============================================================================

def get_test_config() -> TestConfig:
    """获取当前测试配置"""
    return test_config


def is_unit_test_mode() -> bool:
    """检查是否为单元测试模式"""
    return test_config.environment == TestEnvironment.UNIT


def is_performance_test_mode() -> bool:
    """检查是否为性能测试模式"""
    return test_config.environment == TestEnvironment.PERFORMANCE


def should_mock_external_apis() -> bool:
    """检查是否应该Mock外部API"""
    return test_config.network.mock_external_apis


def get_performance_limits() -> Dict[str, Any]:
    """获取性能测试限制"""
    return {
        'max_response_time_ms': test_config.performance.max_response_time_ms,
        'max_memory_usage_mb': test_config.performance.max_memory_usage_mb,
        'min_throughput_rps': test_config.performance.min_throughput_rps,
        'baseline_metrics': test_config.performance.baseline_metrics
    }


def create_temp_file(suffix: str = ".tmp") -> Path:
    """创建临时文件"""
    import tempfile
    
    temp_file = test_config.temp_dir / f"test_{tempfile.getrandbits(32):08x}{suffix}"
    temp_file.parent.mkdir(parents=True, exist_ok=True)
    return temp_file


def get_mock_delays() -> Dict[str, float]:
    """获取Mock延迟配置"""
    return test_config.network.mock_delays.copy()


if __name__ == "__main__":
    # 命令行工具示例
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Test Configuration Manager")
    parser.add_argument('--env', choices=['unit', 'integration', 'performance', 'e2e', 'ci', 'local'], 
                       default='local', help='Test environment')
    parser.add_argument('--mode', choices=['fast', 'full', 'smoke', 'stress'],
                       default='fast', help='Test mode')
    parser.add_argument('--validate', action='store_true', help='Validate test environment')
    parser.add_argument('--export-env', action='store_true', help='Export environment variables')
    parser.add_argument('--pytest-args', action='store_true', help='Show pytest arguments')
    
    args = parser.parse_args()
    
    # 创建配置
    config = TestConfig(
        environment=TestEnvironment(args.env),
        mode=TestMode(args.mode)
    )
    
    if args.validate:
        print("Validating test environment...")
        issues = config.validate_environment()
        if issues:
            print("Issues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("Environment validation passed!")
    
    if args.export_env:
        print("Environment variables:")
        for key, value in config.get_environment_variables().items():
            print(f"export {key}={value}")
    
    if args.pytest_args:
        print("Pytest arguments:")
        print(" ".join(config.get_pytest_args()))
    
    # 保存配置报告
    config_file = config.save_config_report()
    print(f"\nConfiguration saved to: {config_file}")
