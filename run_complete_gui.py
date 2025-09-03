#!/usr/bin/env python3
"""
PoE2 完整功能GUI启动脚本
启动具有完整功能的PoE2智能构筑生成器

功能特点:
✅ 四大数据源集成监控
✅ RAG AI训练系统
✅ PoB2高度集成推荐
✅ F12开发者控制台
✅ 实时DPS/EHP计算
✅ 构筑导入导出功能
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """检查必要的依赖"""
    missing_deps = []
    
    try:
        import PyQt6
        print("PyQt6 installed")
    except ImportError:
        missing_deps.append("PyQt6")
        
    try:
        import asyncio
        print("asyncio support OK")
    except ImportError:
        missing_deps.append("asyncio")
    
    if missing_deps:
        print(f"Missing dependencies: {', '.join(missing_deps)}")
        print("Please run: pip install PyQt6")
        return False
    
    return True

def main():
    """启动完整GUI"""
    try:
        # 设置控制台编码为UTF-8
        import sys
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass
    
    print("PoE2 Smart Build Generator Starting...")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        print("Dependency check failed")
        return 1
    
    # 检查后端可用性
    try:
        from core_ai_engine.src.poe2build.data_sources import get_all_four_sources
        print("Backend available - Full functionality mode")
        backend_status = "Full Mode"
    except ImportError:
        print("Backend unavailable - Demo mode")
        backend_status = "Demo Mode"
    
    print(f"Running mode: {backend_status}")
    print("Data sources: PoE2Scout, PoE Ninja, PoB2, PoE2DB")
    print("RAG AI system: Smart build recommendations")
    print("PoB2 integration: Accurate DPS/EHP calculation")
    print("F12 console: Developer debugging tools")
    print("=" * 50)
    
    # 启动GUI
    try:
        from gui_apps.poe2_complete_gui import main as gui_main
        return gui_main()
    except Exception as e:
        print(f"❌ GUI启动失败: {e}")
        print("请检查PyQt6是否正确安装")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code if exit_code else 0)