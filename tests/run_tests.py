"""
测试运行脚本
提供便捷的测试执行和报告生成功能
"""

import sys
import os
import argparse
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_config import TestConfigManager, get_test_config


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.config_manager = TestConfigManager()
        self.project_root = Path(__file__).parent.parent
    
    def run_all_tests(self, environment: str = "local") -> bool:
        """运行所有测试"""
        print("="*80)
        print("PoE2 智能构筑生成器 - 测试套件")
        print("="*80)
        
        config = get_test_config(environment)
        self.config_manager.setup_test_environment(config)
        
        start_time = time.time()
        success = True
        
        try:
            # 运行单元测试
            print("\n📋 运行单元测试...")
            if not self._run_test_category("unit", config):
                success = False
            
            # 运行集成测试
            print("\n🔗 运行集成测试...")
            if not self._run_test_category("integration", config):
                success = False
            
            # 运行性能测试（如果启用）
            if config.performance_test_enabled:
                print("\n⚡ 运行性能测试...")
                if not self._run_test_category("performance", config):
                    success = False
            
            # 生成综合报告
            self._generate_summary_report(start_time, success)
            
        finally:
            self.config_manager.teardown_test_environment(config)
        
        return success
    
    def run_unit_tests(self, environment: str = "local") -> bool:
        """运行单元测试"""
        config = get_test_config(environment)
        self.config_manager.setup_test_environment(config)
        
        try:
            return self._run_test_category("unit", config)
        finally:
            self.config_manager.teardown_test_environment(config)
    
    def run_integration_tests(self, environment: str = "local") -> bool:
        """运行集成测试"""
        config = get_test_config(environment)
        self.config_manager.setup_test_environment(config)
        
        try:
            return self._run_test_category("integration", config)
        finally:
            self.config_manager.teardown_test_environment(config)
    
    def run_performance_tests(self, environment: str = "performance") -> bool:
        """运行性能测试"""
        config = get_test_config(environment)
        self.config_manager.setup_test_environment(config)
        
        try:
            return self._run_test_category("performance", config)
        finally:
            self.config_manager.teardown_test_environment(config)
    
    def run_specific_test(self, test_path: str, environment: str = "local") -> bool:
        """运行特定测试"""
        config = get_test_config(environment)
        self.config_manager.setup_test_environment(config)
        
        try:
            args = self.config_manager.get_pytest_args(config)
            args.append(test_path)
            
            return self._execute_pytest(args)
        finally:
            self.config_manager.teardown_test_environment(config)
    
    def _run_test_category(self, category: str, config) -> bool:
        """运行特定类别的测试"""
        test_dir = self.project_root / "tests" / category
        
        if not test_dir.exists():
            print(f"⚠️  测试目录不存在: {test_dir}")
            return True  # 不存在不算失败
        
        args = self.config_manager.get_pytest_args(config)
        args.append(str(test_dir))
        
        # 添加类别特定的标记
        if category == "unit":
            args.extend(['-m', 'unit or not (integration or performance or e2e)'])
        elif category == "integration":
            args.extend(['-m', 'integration'])
        elif category == "performance":
            args.extend(['-m', 'performance'])
        
        print(f"执行命令: pytest {' '.join(args)}")
        return self._execute_pytest(args)
    
    def _execute_pytest(self, args: List[str]) -> bool:
        """执行pytest命令"""
        try:
            # 构建完整命令
            cmd = [sys.executable, '-m', 'pytest'] + args
            
            # 执行命令
            result = subprocess.run(cmd, 
                                  cwd=self.project_root,
                                  capture_output=False,
                                  text=True)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ 测试执行失败: {e}")
            return False
    
    def _generate_summary_report(self, start_time: float, success: bool):
        """生成测试摘要报告"""
        duration = time.time() - start_time
        
        print("\n" + "="*80)
        print("测试执行摘要")
        print("="*80)
        print(f"总耗时: {duration:.2f} 秒")
        print(f"整体结果: {'✅ 成功' if success else '❌ 失败'}")
        
        # 检查报告文件
        reports_dir = self.project_root / "reports"
        if reports_dir.exists():
            print(f"\n📊 报告文件:")
            for report_file in reports_dir.glob("*"):
                print(f"  - {report_file.name}")
        
        print("="*80)
    
    def check_environment(self) -> Dict[str, Any]:
        """检查测试环境"""
        print("检查测试环境...")
        
        checks = {
            'python_version': sys.version,
            'project_root': str(self.project_root),
            'pytest_available': False,
            'required_packages': {},
            'test_directories': {},
            'config_files': {}
        }
        
        # 检查pytest
        try:
            import pytest
            checks['pytest_available'] = True
            checks['pytest_version'] = pytest.__version__
        except ImportError:
            print("❌ pytest 未安装")
        
        # 检查必需包
        required_packages = [
            'pytest', 'pytest-asyncio', 'pytest-cov', 
            'pytest-html', 'pytest-json-report', 'psutil'
        ]
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                checks['required_packages'][package] = True
            except ImportError:
                checks['required_packages'][package] = False
                print(f"⚠️  {package} 未安装")
        
        # 检查测试目录
        test_dirs = ['unit', 'integration', 'performance', 'e2e', 'fixtures']
        for test_dir in test_dirs:
            dir_path = self.project_root / "tests" / test_dir
            checks['test_directories'][test_dir] = dir_path.exists()
            if not dir_path.exists():
                print(f"⚠️  测试目录不存在: {dir_path}")
        
        # 检查配置文件
        config_files = ['pytest.ini', 'pyproject.toml', 'requirements.txt']
        for config_file in config_files:
            file_path = self.project_root / config_file
            checks['config_files'][config_file] = file_path.exists()
        
        # 输出检查结果
        print("\n环境检查结果:")
        print(f"  Python: {sys.version.split()[0]}")
        print(f"  工作目录: {self.project_root}")
        
        if checks['pytest_available']:
            print(f"  ✅ pytest: {checks.get('pytest_version', 'unknown')}")
        else:
            print("  ❌ pytest: 未安装")
        
        missing_packages = [pkg for pkg, installed in checks['required_packages'].items() if not installed]
        if missing_packages:
            print(f"  ⚠️  缺失包: {', '.join(missing_packages)}")
        else:
            print("  ✅ 所有依赖包已安装")
        
        missing_dirs = [d for d, exists in checks['test_directories'].items() if not exists]
        if missing_dirs:
            print(f"  ⚠️  缺失目录: {', '.join(missing_dirs)}")
        else:
            print("  ✅ 所有测试目录存在")
        
        return checks
    
    def install_dependencies(self):
        """安装测试依赖"""
        print("安装测试依赖...")
        
        requirements = [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.20.0',
            'pytest-cov>=4.0.0',
            'pytest-html>=3.1.0',
            'pytest-json-report>=1.5.0',
            'pytest-xdist>=3.0.0',  # 并行测试
            'pytest-timeout>=2.1.0',
            'psutil>=5.9.0',
            'coverage>=7.0.0'
        ]
        
        for requirement in requirements:
            try:
                print(f"安装 {requirement}...")
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', requirement
                ], check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                print(f"❌ 安装 {requirement} 失败: {e}")
                return False
        
        print("✅ 所有依赖安装完成")
        return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='PoE2构筑生成器测试运行器')
    
    parser.add_argument('command', choices=[
        'all', 'unit', 'integration', 'performance', 
        'check', 'install-deps', 'specific'
    ], help='要执行的命令')
    
    parser.add_argument('--env', '-e', default='local',
                       choices=['local', 'ci', 'performance', 'integration'],
                       help='测试环境')
    
    parser.add_argument('--path', '-p', help='特定测试路径（用于specific命令）')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.command == 'check':
        runner.check_environment()
        return
    
    if args.command == 'install-deps':
        success = runner.install_dependencies()
        sys.exit(0 if success else 1)
    
    if args.command == 'all':
        success = runner.run_all_tests(args.env)
    elif args.command == 'unit':
        success = runner.run_unit_tests(args.env)
    elif args.command == 'integration':
        success = runner.run_integration_tests(args.env)
    elif args.command == 'performance':
        success = runner.run_performance_tests(args.env)
    elif args.command == 'specific':
        if not args.path:
            print("❌ 使用 specific 命令时必须指定 --path")
            sys.exit(1)
        success = runner.run_specific_test(args.path, args.env)
    else:
        print(f"❌ 未知命令: {args.command}")
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()