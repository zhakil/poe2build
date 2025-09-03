"""
测试配置管理
管理不同测试环境的配置和设置
"""

import os
import json
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class TestConfig:
    """测试配置数据类"""
    # 测试环境设置
    test_env: str = "local"
    debug_mode: bool = False
    parallel_tests: bool = True
    test_timeout: int = 300  # 秒
    
    # 性能测试配置
    performance_test_enabled: bool = True
    benchmark_iterations: int = 5
    stress_test_duration: int = 60  # 秒
    concurrent_limit: int = 20
    
    # API测试配置
    api_test_enabled: bool = True
    real_api_calls: bool = False  # 是否使用真实API
    rate_limit_delay: float = 0.1  # 秒
    
    # 缓存和数据配置
    test_data_cache: bool = True
    cache_ttl: int = 300  # 秒
    clean_cache_after_tests: bool = True
    
    # 数据库和存储
    temp_data_dir: str = ""
    preserve_test_data: bool = False
    
    # 报告和日志配置
    generate_html_report: bool = True
    generate_json_report: bool = True
    log_level: str = "INFO"
    capture_screenshots: bool = False
    
    # 覆盖率配置
    coverage_enabled: bool = True
    coverage_threshold: float = 90.0  # 百分比
    coverage_exclude_patterns: List[str] = None
    
    # 特定测试组件配置
    mock_components: Dict[str, bool] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.coverage_exclude_patterns is None:
            self.coverage_exclude_patterns = [
                "*/tests/*",
                "*/venv/*",
                "*/__pycache__/*",
                "*/migrations/*"
            ]
        
        if self.mock_components is None:
            self.mock_components = {
                'rag_engine': True,
                'pob2_local': True,
                'market_api': True,
                'ninja_scraper': True,
                'cache_manager': True
            }
        
        # 设置临时数据目录
        if not self.temp_data_dir:
            project_root = Path(__file__).parent.parent
            self.temp_data_dir = str(project_root / "data" / "test_temp")


class TestConfigManager:
    """测试配置管理器"""
    
    def __init__(self, config_file: str = None):
        self.project_root = Path(__file__).parent.parent
        self.config_file = config_file or self.project_root / "tests" / "test_config.json"
        self._config = None
    
    def load_config(self, environment: str = None) -> TestConfig:
        """加载测试配置"""
        base_config = TestConfig()
        
        # 从文件加载配置
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                
                # 根据环境选择配置
                if environment and environment in file_config:
                    env_config = file_config[environment]
                    # 更新配置
                    for key, value in env_config.items():
                        if hasattr(base_config, key):
                            setattr(base_config, key, value)
                elif 'default' in file_config:
                    default_config = file_config['default']
                    for key, value in default_config.items():
                        if hasattr(base_config, key):
                            setattr(base_config, key, value)
            except Exception as e:
                print(f"Warning: Failed to load config file {self.config_file}: {e}")
        
        # 环境变量覆盖
        self._load_env_overrides(base_config)
        
        self._config = base_config
        return base_config
    
    def _load_env_overrides(self, config: TestConfig):
        """从环境变量加载覆盖设置"""
        env_mappings = {
            'TEST_ENV': 'test_env',
            'DEBUG_MODE': 'debug_mode',
            'PERFORMANCE_TEST': 'performance_test_enabled',
            'REAL_API_CALLS': 'real_api_calls',
            'TEST_TIMEOUT': 'test_timeout',
            'COVERAGE_THRESHOLD': 'coverage_threshold',
            'LOG_LEVEL': 'log_level'
        }
        
        for env_var, config_attr in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                # 类型转换
                current_value = getattr(config, config_attr)
                if isinstance(current_value, bool):
                    setattr(config, config_attr, env_value.lower() in ['true', '1', 'yes'])
                elif isinstance(current_value, int):
                    setattr(config, config_attr, int(env_value))
                elif isinstance(current_value, float):
                    setattr(config, config_attr, float(env_value))
                else:
                    setattr(config, config_attr, env_value)
    
    def save_config(self, config: TestConfig, environment: str = 'default'):
        """保存配置到文件"""
        # 读取现有配置
        existing_config = {}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
            except Exception:
                pass
        
        # 更新指定环境的配置
        existing_config[environment] = asdict(config)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        # 保存配置
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(existing_config, f, indent=2, ensure_ascii=False)
    
    def get_pytest_args(self, config: TestConfig = None) -> List[str]:
        """获取pytest命令行参数"""
        if not config:
            config = self._config or self.load_config()
        
        args = []
        
        # 基本参数
        if config.debug_mode:
            args.extend(['-v', '-s'])
        else:
            args.append('-q')
        
        # 并行测试
        if config.parallel_tests:
            args.extend(['-n', 'auto'])
        
        # 超时设置
        args.extend(['--timeout', str(config.test_timeout)])
        
        # 覆盖率
        if config.coverage_enabled:
            args.extend([
                '--cov=src/poe2build',
                f'--cov-fail-under={config.coverage_threshold}',
                '--cov-report=html',
                '--cov-report=term-missing'
            ])
            
            if config.coverage_exclude_patterns:
                for pattern in config.coverage_exclude_patterns:
                    args.extend(['--cov-ignore', pattern])
        
        # 报告生成
        if config.generate_html_report:
            args.extend(['--html=reports/test_report.html', '--self-contained-html'])
        
        if config.generate_json_report:
            args.extend(['--json-report', '--json-report-file=reports/test_report.json'])
        
        # 测试选择
        if not config.performance_test_enabled:
            args.extend(['-m', 'not performance'])
        
        if not config.api_test_enabled:
            args.extend(['-m', 'not api'])
        
        return args
    
    def setup_test_environment(self, config: TestConfig = None):
        """设置测试环境"""
        if not config:
            config = self._config or self.load_config()
        
        # 创建必要的目录
        directories = [
            config.temp_data_dir,
            self.project_root / "reports",
            self.project_root / "logs" / "tests",
            self.project_root / "data" / "test_cache"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        # 设置环境变量
        os.environ['PYTHONPATH'] = str(self.project_root / "src")
        os.environ['TEST_ENV'] = config.test_env
        os.environ['LOG_LEVEL'] = config.log_level
        
        # 清理旧的测试数据（如果配置要求）
        if config.clean_cache_after_tests:
            self._clean_test_cache()
        
        print(f"Test environment setup completed for: {config.test_env}")
        return True
    
    def _clean_test_cache(self):
        """清理测试缓存"""
        cache_dir = self.project_root / "data" / "test_cache"
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir, ignore_errors=True)
            os.makedirs(cache_dir, exist_ok=True)
    
    def teardown_test_environment(self, config: TestConfig = None):
        """清理测试环境"""
        if not config:
            config = self._config or self.load_config()
        
        # 清理临时数据（如果配置要求）
        if not config.preserve_test_data:
            temp_dir = Path(config.temp_data_dir)
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        # 清理缓存
        if config.clean_cache_after_tests:
            self._clean_test_cache()
        
        print("Test environment teardown completed")


def create_test_configs():
    """创建预定义的测试配置"""
    manager = TestConfigManager()
    
    # 本地开发配置
    local_config = TestConfig(
        test_env="local",
        debug_mode=True,
        parallel_tests=False,
        performance_test_enabled=True,
        real_api_calls=False,
        coverage_enabled=True,
        coverage_threshold=85.0,
        generate_html_report=True
    )
    
    # CI/CD配置
    ci_config = TestConfig(
        test_env="ci",
        debug_mode=False,
        parallel_tests=True,
        performance_test_enabled=True,
        real_api_calls=False,
        coverage_enabled=True,
        coverage_threshold=90.0,
        generate_html_report=True,
        generate_json_report=True,
        test_timeout=600,
        concurrent_limit=10
    )
    
    # 性能测试配置
    performance_config = TestConfig(
        test_env="performance",
        debug_mode=False,
        parallel_tests=False,
        performance_test_enabled=True,
        benchmark_iterations=10,
        stress_test_duration=300,
        concurrent_limit=50,
        coverage_enabled=False,
        generate_html_report=True,
        test_timeout=900
    )
    
    # 集成测试配置
    integration_config = TestConfig(
        test_env="integration",
        debug_mode=True,
        parallel_tests=False,
        performance_test_enabled=False,
        real_api_calls=True,  # 使用真实API
        rate_limit_delay=0.5,
        api_test_enabled=True,
        coverage_enabled=False,
        test_timeout=900,
        mock_components={
            'rag_engine': False,  # 使用真实组件
            'pob2_local': False,
            'market_api': False,
            'ninja_scraper': False,
            'cache_manager': True  # 仍使用Mock缓存
        }
    )
    
    # 保存配置
    manager.save_config(local_config, 'local')
    manager.save_config(ci_config, 'ci')
    manager.save_config(performance_config, 'performance')
    manager.save_config(integration_config, 'integration')
    
    return {
        'local': local_config,
        'ci': ci_config,
        'performance': performance_config,
        'integration': integration_config
    }


# 全局配置实例
test_config_manager = TestConfigManager()


def get_test_config(environment: str = None) -> TestConfig:
    """获取测试配置的便利函数"""
    return test_config_manager.load_config(environment)


if __name__ == "__main__":
    # 创建默认配置文件
    configs = create_test_configs()
    print("Test configurations created:")
    for env_name, config in configs.items():
        print(f"  {env_name}: {config.test_env} environment")
    
    print(f"\nConfiguration file: {test_config_manager.config_file}")
    print("Use 'pytest --help' to see available options")
    print("Use 'python -m pytest tests/' to run tests with default configuration")