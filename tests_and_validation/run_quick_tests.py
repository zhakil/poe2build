#!/usr/bin/env python3
"""
快速测试脚本
用于快速验证测试套件的基本功能
"""

import sys
import os
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def check_environment():
    """检查基础环境"""
    print("检查测试环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print(f"[FAIL] Python版本过低: {sys.version_info}，需要3.8+")
        return False
    
    print(f"[OK] Python版本: {sys.version.split()[0]}")
    
    # 检查pytest
    try:
        import pytest
        print(f"[OK] pytest: {pytest.__version__}")
    except ImportError:
        print("[FAIL] pytest未安装，请运行: pip install pytest pytest-asyncio")
        return False
    
    # 检查项目结构
    required_dirs = [
        project_root / "src" / "poe2build",
        project_root / "tests" / "unit", 
        project_root / "tests" / "integration",
        project_root / "tests" / "performance",
        project_root / "tests" / "fixtures"
    ]
    
    for dir_path in required_dirs:
        if dir_path.exists():
            print(f"[OK] 目录存在: {dir_path.name}")
        else:
            print(f"[FAIL] 目录缺失: {dir_path}")
            return False
    
    return True

def run_quick_unit_tests():
    """运行快速单元测试"""
    print("\n[INFO] 运行快速单元测试...")
    
    test_files = [
        "tests/unit/test_models.py::TestPoE2BuildStats::test_valid_build_stats_creation",
        "tests/unit/test_models.py::TestPoE2Build::test_valid_build_creation", 
        "tests/unit/test_build_validation.py::TestBuildStatsValidation::test_resistance_range_validation"
    ]
    
    success = True
    for test_file in test_files:
        print(f"  运行: {test_file}")
        result = subprocess.run([
            sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"
        ], cwd=project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  [OK] 通过")
        else:
            print(f"  [FAIL] 失败")
            print(f"     {result.stdout}")
            print(f"     {result.stderr}")
            success = False
    
    return success

def run_integration_health_check():
    """运行集成测试健康检查"""
    print("\n[INFO] 运行集成测试健康检查...")
    
    try:
        # 导入测试模块以验证导入是否正常
        from tests.fixtures.sample_builds import get_sample_builds
        from tests.fixtures.test_data import TestDataFactory
        
        # 基本功能测试
        builds = get_sample_builds()
        if builds and len(builds) > 0:
            print("[OK] 样例构筑数据加载成功")
        else:
            print("[FAIL] 样例构筑数据加载失败")
            return False
        
        # 测试数据工厂
        test_build = TestDataFactory.create_random_build()
        if test_build and test_build.validate():
            print("[OK] 测试数据工厂正常")
        else:
            print("[FAIL] 测试数据工厂异常")
            return False
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 集成测试健康检查失败: {e}")
        return False

def run_performance_check():
    """运行性能测试基础检查"""
    print("\n[INFO] 运行性能测试基础检查...")
    
    try:
        import psutil
        print("[OK] psutil可用（内存监控）")
        
        import time
        import statistics
        
        # 简单的性能测试
        times = []
        for i in range(5):
            start = time.perf_counter()
            # 模拟一些计算
            _ = sum(range(1000))
            end = time.perf_counter()
            times.append((end - start) * 1000)
        
        avg_time = statistics.mean(times)
        print(f"[OK] 基础性能测试: 平均 {avg_time:.3f}ms")
        
        return True
        
    except ImportError as e:
        print(f"[WARN] 性能测试依赖缺失: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] 性能测试基础检查失败: {e}")
        return False

def run_fixtures_validation():
    """验证测试fixtures"""
    print("\n[INFO] 验证测试fixtures...")
    
    try:
        # 验证API响应fixtures
        from tests.fixtures.mock_responses.api_responses import (
            MOCK_POE2_SCOUT_RESPONSES, MOCK_NINJA_RESPONSES, 
            get_mock_response
        )
        
        # 检查数据完整性
        if MOCK_POE2_SCOUT_RESPONSES and 'item_prices' in MOCK_POE2_SCOUT_RESPONSES:
            print("[OK] Scout API mock数据正常")
        else:
            print("[FAIL] Scout API mock数据异常")
            return False
        
        if MOCK_NINJA_RESPONSES and 'build_rankings' in MOCK_NINJA_RESPONSES:
            print("[OK] Ninja API mock数据正常")  
        else:
            print("[FAIL] Ninja API mock数据异常")
            return False
        
        # 测试mock响应函数
        response = get_mock_response('scout', 'item_prices')
        if response:
            print("[OK] Mock响应函数正常")
        else:
            print("[FAIL] Mock响应函数异常")
            return False
        
        return True
        
    except ImportError as e:
        print(f"[FAIL] Fixtures导入失败: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Fixtures验证失败: {e}")
        return False

def main():
    """主函数"""
    print("PoE2构筑生成器 - 快速测试验证")
    print("=" * 60)
    
    success = True
    
    # 1. 环境检查
    if not check_environment():
        print("\n[FAIL] 环境检查失败")
        return 1
    
    # 2. Fixtures验证
    if not run_fixtures_validation():
        print("\n[FAIL] Fixtures验证失败")
        success = False
    
    # 3. 快速单元测试
    if not run_quick_unit_tests():
        print("\n[FAIL] 单元测试失败")
        success = False
    
    # 4. 集成健康检查
    if not run_integration_health_check():
        print("\n[FAIL] 集成健康检查失败")
        success = False
    
    # 5. 性能检查
    if not run_performance_check():
        print("\n[WARN] 性能检查未通过（非致命）")
    
    # 总结
    print("\n" + "=" * 60)
    if success:
        print("[SUCCESS] 快速测试验证通过！")
        print("\n[INFO] 完整测试命令:")
        print("  python tests/run_tests.py all           # 运行所有测试")
        print("  python tests/run_tests.py unit          # 仅运行单元测试") 
        print("  python tests/run_tests.py integration   # 仅运行集成测试")
        print("  python tests/run_tests.py performance   # 仅运行性能测试")
        print("\n或使用pytest直接运行:")
        print("  pytest tests/unit/                      # 单元测试")
        print("  pytest tests/integration/               # 集成测试")
        print("  pytest tests/performance/               # 性能测试")
        print("  pytest -m 'not performance'             # 排除性能测试")
        return 0
    else:
        print("[FAIL] 快速测试验证失败，请检查问题后重试")
        return 1

if __name__ == "__main__":
    exit(main())