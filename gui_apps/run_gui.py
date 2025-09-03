#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PoE2 Build Generator GUI启动脚本

启动PyQt6 GUI应用程序的主入口点。
"""

import sys
import os

# 设置控制台输出编码
if sys.platform.startswith('win'):
    try:
        import locale
        locale.setlocale(locale.LC_ALL, '')  # 使用系统默认locale
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    except locale.Error:
        # fallback to environment variable only
        os.environ['PYTHONIOENCODING'] = 'utf-8'

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

# 添加D盘Python包路径
d_packages_path = "D:\\python_packages"
if os.path.exists(d_packages_path) and d_packages_path not in sys.path:
    sys.path.insert(0, d_packages_path)
    print(f"[INFO] 使用D盘Python包: {d_packages_path}")

def check_dependencies():
    """检查必需的依赖项"""
    missing_deps = []
    available_deps = []
    
    try:
        from PyQt6 import QtCore
        print(f"[OK] PyQt6 版本: {QtCore.qVersion()}")
        available_deps.append("PyQt6")
    except ImportError:
        missing_deps.append("PyQt6")
        print("[WARNING] PyQt6 未安装 - GUI无法显示")
    
    try:
        import requests
        print(f"[OK] requests 可用")
        available_deps.append("requests")
    except ImportError:
        missing_deps.append("requests")
        print("[WARNING] requests 未安装 - 网络功能受限")
    
    try:
        import bs4
        print(f"[OK] beautifulsoup4 可用")
        available_deps.append("beautifulsoup4")
    except ImportError:
        missing_deps.append("beautifulsoup4")
        print("[WARNING] beautifulsoup4 未安装 - 数据解析功能受限")
    
    if missing_deps:
        print(f"\\n[WARNING] 缺少以下依赖项: {', '.join(missing_deps)}")
        print("\\n建议安装命令:")
        print(f"pip install {' '.join(missing_deps)}")
        
        if "PyQt6" in missing_deps:
            print("\\n[ERROR] PyQt6是必需的，GUI无法启动")
            return False
        else:
            print("\\n[INFO] 将在降级模式下运行")
    
    print(f"\\n[OK] 可用依赖项: {', '.join(available_deps) if available_deps else '无'}")
    return True

def main():
    """主函数"""
    print("=" * 50)
    print("PoE2 Build Generator GUI 启动中...")
    print("=" * 50)
    
    # 检查依赖项
    if not check_dependencies():
        sys.exit(1)
    
    # 检查PyQt6是否支持当前系统
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QCoreApplication
        
        # 测试创建应用程序
        test_app = QCoreApplication([])
        print("[OK] PyQt6 系统兼容性检查通过")
        
    except Exception as e:
        print(f"[ERROR] PyQt6 兼容性检查失败: {e}")
        print("\\n可能的解决方案:")
        print("1. 更新PyQt6: pip install --upgrade PyQt6")
        print("2. 检查系统是否支持GUI显示")
        sys.exit(1)
    
    # 导入并启动GUI应用程序
    try:
        print("\\n启动GUI应用程序...")
        from poe2build.gui.app import main as gui_main
        
        return gui_main()
        
    except ImportError as e:
        print(f"[ERROR] 导入GUI模块失败: {e}")
        print("\\n请确保项目结构完整且所有文件都存在")
        sys.exit(1)
        
    except Exception as e:
        print(f"[ERROR] 应用程序启动失败: {e}")
        print("\\n请检查系统日志获取详细错误信息")
        sys.exit(1)

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\\n用户中断程序")
        sys.exit(0)
    except Exception as e:
        print(f"\\n未处理的异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)