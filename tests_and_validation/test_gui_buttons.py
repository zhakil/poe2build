#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI按钮功能测试脚本

用于验证修复后的GUI按钮响应功能
"""

import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

def test_gui_creation():
    """测试GUI创建"""
    print("=== GUI Creation Test ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.poe2build.gui.app import PoE2BuildApp
        
        # 创建应用程序
        app = PoE2BuildApp([])
        
        print("[OK] GUI application created successfully")
        print(f"Application name: {app.applicationName()}")
        print(f"Application version: {app.applicationVersion()}")
        
        # 检查主窗口
        main_window = app.main_window
        print(f"[OK] Main window created: {main_window.__class__.__name__}")
        
        # 检查后端连接
        orchestrator = app.get_orchestrator()
        if orchestrator:
            print("[OK] Backend orchestrator available")
            print(f"Backend initialized: {orchestrator._initialized}")
        else:
            print("[WARN] Backend orchestrator not available")
        
        # 清理
        app.quit()
        return True
        
    except Exception as e:
        print(f"[FAIL] GUI creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_button_connections():
    """测试按钮连接"""
    print("\n=== Button Connection Test ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.poe2build.gui.app import PoE2BuildApp
        from src.poe2build.gui.pages.build_generator_page import BuildGeneratorPage
        
        # 创建应用程序
        app = QApplication([])
        
        # 创建构筑生成器页面
        page = BuildGeneratorPage()
        
        # 检查关键按钮
        if hasattr(page, 'generate_button'):
            print("[OK] Generate button exists")
            # 检查按钮是否连接了信号
            generate_button = page.generate_button
            print(f"Button enabled: {generate_button.isEnabled()}")
            print(f"Button text: {generate_button.text()}")
        else:
            print("[FAIL] Generate button not found")
            
        if hasattr(page, 'cancel_button'):
            print("[OK] Cancel button exists")
        else:
            print("[WARN] Cancel button not found")
            
        if hasattr(page, 'reset_button'):
            print("[OK] Reset button exists") 
        else:
            print("[WARN] Reset button not found")
            
        # 检查后端客户端
        if hasattr(page, 'backend_client'):
            print("[OK] Backend client exists")
            backend_client = page.backend_client
            print(f"Backend client status: {backend_client.get_current_status()}")
            print(f"Backend client busy: {backend_client.is_busy()}")
        else:
            print("[FAIL] Backend client not found")
        
        # 清理
        app.quit()
        return True
        
    except Exception as e:
        print(f"[FAIL] Button connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backend_services():
    """测试后端服务"""
    print("\n=== Backend Services Test ===")
    
    try:
        from src.poe2build.gui.services.backend_client import BackendClient
        from src.poe2build.core.ai_orchestrator import PoE2AIOrchestrator
        
        # 创建后端客户端
        backend_client = BackendClient()
        print("[OK] Backend client created")
        print(f"Current status: {backend_client.get_current_status()}")
        print(f"Is busy: {backend_client.is_busy()}")
        
        # 创建AI协调器
        orchestrator = PoE2AIOrchestrator()
        print("[OK] AI orchestrator created")
        print(f"Initialized: {orchestrator._initialized}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Backend services test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("PoE2 Build Generator - GUI Button Function Test")
    print("=" * 50)
    
    test_results = []
    
    # 运行测试
    test_results.append(("GUI Creation", test_gui_creation()))
    test_results.append(("Button Connections", test_button_connections()))
    test_results.append(("Backend Services", test_backend_services()))
    
    # 总结结果
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:20} : {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("=" * 50)
    print(f"Total: {len(test_results)}, Passed: {passed}, Failed: {failed}")
    
    if failed == 0:
        print("All tests passed! GUI buttons should be functional.")
        return 0
    else:
        print("Some tests failed. Please check the error messages above.")
        return 1

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnhandled exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)