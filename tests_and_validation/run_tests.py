#!/usr/bin/env python3
"""
测试运行器 - 便捷的测试执行脚本

支持多种测试模式和配置选项，用于本地开发和CI/CD环境
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import json

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.test_config_advanced import TestConfig, TestEnvironment, TestMode


def run_command(cmd: List[str], capture_output: bool = False) -> subprocess.CompletedProcess:
    """运行命令并返回结果"""
    print(f"执行命令: {' '.join(cmd)}")
    
    if capture_output:
        return subprocess.run(cmd, capture_output=True, text=True)
    else:
        return subprocess.run(cmd)


def setup_test_environment(test_config: TestConfig) -> Dict[str, str]:
    """设置测试环境变量"""
    env_vars = test_config.get_environment_variables()
    
    # 更新当前进程的环境变量
    os.environ.update(env_vars)
    
    print("测试环境变量:")
    for key, value in env_vars.items():
        print(f"  {key}={value}")
    
    return env_vars


def install_dependencies(upgrade: bool = False) -> bool:
    """安装测试依赖"""
    print("安装测试依赖...")
    
    pip_cmd = [sys.executable, "-m", "pip"]
    
    if upgrade:
        run_command(pip_cmd + ["install", "--upgrade", "pip"])
    
    # 安装基础依赖
    result = run_command(pip_cmd + ["install", "-r", "requirements.txt"])
    if result.returncode != 0:
        print("❌ 安装基础依赖失败")
        return False
    
    # 安装测试依赖
    test_deps = [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0", 
        "pytest-html>=3.1.0",
        "pytest-xdist>=3.0.0",
        "pytest-mock>=3.10.0",
        "pytest-asyncio>=0.21.0",
        "pytest-timeout>=2.1.0",
        "pytest-benchmark>=4.0.0",
        "coverage[toml]>=7.0.0",
        "psutil>=5.9.0",
        "redis>=4.5.0"
    ]
    
    result = run_command(pip_cmd + ["install"] + test_deps)
    if result.returncode != 0:
        print("❌ 安装测试依赖失败")
        return False
    
    print("✅ 依赖安装完成")
    return True


def run_code_quality_checks() -> bool:
    """运行代码质量检查"""
    print("\n" + "="*60)
    print("代码质量检查")
    print("="*60)
    
    checks_passed = True
    
    # 代码格式化检查
    print("\n🔍 检查代码格式化...")
    result = run_command([
        sys.executable, "-m", "black", 
        "--check", "--diff", "src/", "tests/"
    ], capture_output=True)
    
    if result.returncode != 0:
        print("❌ 代码格式化检查失败:")
        print(result.stdout)
        checks_passed = False
    else:
        print("✅ 代码格式化检查通过")
    
    # 导入排序检查
    print("\n🔍 检查导入排序...")
    result = run_command([
        sys.executable, "-m", "isort",
        "--check-only", "--diff", "src/", "tests/"
    ], capture_output=True)
    
    if result.returncode != 0:
        print("❌ 导入排序检查失败:")
        print(result.stdout)
        checks_passed = False
    else:
        print("✅ 导入排序检查通过")
    
    # Linting检查
    print("\n🔍 代码Linting...")
    result = run_command([
        sys.executable, "-m", "flake8",
        "src/", "tests/",
        "--max-line-length=120",
        "--ignore=E203,W503"
    ], capture_output=True)
    
    if result.returncode != 0:
        print("❌ Linting检查失败:")
        print(result.stdout)
        checks_passed = False
    else:
        print("✅ Linting检查通过")
    
    return checks_passed


def run_tests(test_config: TestConfig, 
             test_types: List[str], 
             verbose: bool = False,
             parallel: bool = True,
             coverage: bool = True) -> bool:
    """运行测试"""
    
    print("\n" + "="*60)
    print(f"运行测试 - 环境: {test_config.environment.value}, 模式: {test_config.mode.value}")
    print("="*60)
    
    # 构建pytest命令
    pytest_cmd = [sys.executable, "-m", "pytest"]
    
    # 添加基本参数
    pytest_cmd.extend(test_config.get_pytest_args())
    
    # 根据测试类型添加标记
    if test_types and "all" not in test_types:
        marker_expr = " or ".join(test_types)
        pytest_cmd.extend(["-m", marker_expr])
    
    # 详细输出
    if verbose:
        pytest_cmd.append("-v")
    else:
        pytest_cmd.append("-q")
    
    # 并行执行
    if parallel and test_config.mode != TestMode.SMOKE:
        pytest_cmd.extend(["-n", "auto"])
    
    # 覆盖率
    if coverage:
        pytest_cmd.extend([
            "--cov=src/poe2build",
            "--cov-report=term-missing",
            "--cov-report=html:test_reports/coverage",
            "--cov-report=xml:test_reports/coverage.xml"
        ])
    
    # 超时设置
    timeout = 300
    if TestMode.STRESS in [test_config.mode] or "performance" in test_types:
        timeout = 1800
    elif TestMode.SMOKE in [test_config.mode]:
        timeout = 60
    
    pytest_cmd.extend(["--timeout", str(timeout)])
    
    # 报告输出
    pytest_cmd.extend([
        "--html=test_reports/test_report.html",
        "--junit-xml=test_reports/junit.xml"
    ])
    
    print(f"执行命令: {' '.join(pytest_cmd)}")
    
    # 执行测试
    result = run_command(pytest_cmd)
    
    success = result.returncode == 0
    
    if success:
        print("\n✅ 测试执行完成")
    else:
        print("\n❌ 测试执行失败")
    
    return success


def generate_test_report(test_config: TestConfig) -> str:
    """生成测试报告"""
    reports_dir = test_config.reports_dir
    
    # 检查测试报告文件
    report_files = {
        "HTML报告": reports_dir / "test_report.html",
        "JUnit报告": reports_dir / "junit.xml", 
        "覆盖率HTML": reports_dir / "coverage" / "index.html",
        "覆盖率XML": reports_dir / "coverage.xml"
    }
    
    print("\n" + "="*60)
    print("测试报告")
    print("="*60)
    
    for report_name, report_path in report_files.items():
        if report_path.exists():
            print(f"✅ {report_name}: {report_path}")
        else:
            print(f"❌ {report_name}: 未生成")
    
    # 保存配置报告
    config_report = test_config.save_config_report()
    print(f"📋 配置报告: {config_report}")
    
    return str(reports_dir)


def validate_environment(test_config: TestConfig) -> bool:
    """验证测试环境"""
    print("\n" + "="*60)
    print("环境验证")
    print("="*60)
    
    issues = test_config.validate_environment()
    
    if issues:
        print("❌ 发现环境问题:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ 环境验证通过")
        return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="PoE2 Build Generator 测试运行器")
    
    # 环境和模式选择
    parser.add_argument(
        "--env", 
        choices=["unit", "integration", "performance", "e2e", "ci", "local"],
        default="local",
        help="测试环境"
    )
    
    parser.add_argument(
        "--mode",
        choices=["fast", "full", "smoke", "stress"],
        default="fast",
        help="测试模式"
    )
    
    # 测试类型选择
    parser.add_argument(
        "--types",
        nargs="*",
        choices=["unit", "integration", "performance", "e2e", "slow", "smoke", "all"],
        default=["unit"],
        help="要运行的测试类型"
    )
    
    # 执行选项
    parser.add_argument("--install-deps", action="store_true", help="安装依赖")
    parser.add_argument("--code-quality", action="store_true", help="运行代码质量检查")
    parser.add_argument("--validate-env", action="store_true", help="验证环境")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--no-parallel", action="store_true", help="禁用并行执行")
    parser.add_argument("--no-coverage", action="store_true", help="禁用覆盖率")
    parser.add_argument("--upgrade", action="store_true", help="升级依赖")
    
    # 报告选项
    parser.add_argument("--report-only", action="store_true", help="仅生成报告")
    parser.add_argument("--clean", action="store_true", help="清理临时文件")
    
    args = parser.parse_args()
    
    # 创建测试配置
    environment = TestEnvironment(args.env)
    mode = TestMode(args.mode)
    test_config = TestConfig(environment=environment, mode=mode)
    
    print(f"PoE2 Build Generator 测试运行器")
    print(f"环境: {environment.value}, 模式: {mode.value}")
    print(f"测试类型: {', '.join(args.types)}")
    
    # 清理临时文件
    if args.clean:
        import shutil
        temp_dirs = [test_config.temp_dir, test_config.reports_dir / "coverage"]
        for temp_dir in temp_dirs:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
                print(f"清理目录: {temp_dir}")
    
    # 设置环境
    setup_test_environment(test_config)
    
    success = True
    
    # 安装依赖
    if args.install_deps:
        success = install_dependencies(upgrade=args.upgrade) and success
    
    # 环境验证
    if args.validate_env or not args.report_only:
        success = validate_environment(test_config) and success
    
    # 代码质量检查
    if args.code_quality and not args.report_only:
        success = run_code_quality_checks() and success
    
    # 运行测试
    if not args.report_only and success:
        success = run_tests(
            test_config=test_config,
            test_types=args.types,
            verbose=args.verbose,
            parallel=not args.no_parallel,
            coverage=not args.no_coverage
        ) and success
    
    # 生成报告
    report_dir = generate_test_report(test_config)
    
    # 输出最终结果
    print("\n" + "="*60)
    if success:
        print("🎉 测试执行成功完成!")
        print(f"📊 查看报告: {report_dir}")
        sys.exit(0)
    else:
        print("💥 测试执行失败!")
        print(f"📊 查看报告: {report_dir}")
        sys.exit(1)


if __name__ == "__main__":
    main()