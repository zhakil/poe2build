#!/usr/bin/env python3
"""
PoE2 Build Generator GUI 安装和设置脚本

自动安装依赖项并验证GUI环境。
"""

import sys
import subprocess
import os
from pathlib import Path

def run_command(command, description):
    """执行命令并显示结果"""
    print(f"\\n⏳ {description}...")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            check=True
        )
        print(f"✅ {description} 完成")
        if result.stdout:
            print(f"输出: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败")
        print(f"错误: {e.stderr.strip()}")
        return False

def check_python_version():
    """检查Python版本"""
    print("🔍 检查Python版本...")
    
    if sys.version_info < (3, 8):
        print(f"❌ Python版本过低: {sys.version}")
        print("❗ 需要Python 3.8或更高版本")
        return False
    
    print(f"✅ Python版本: {sys.version}")
    return True

def install_dependencies():
    """安装GUI依赖项"""
    print("\\n📦 安装GUI依赖项...")
    
    # 核心依赖列表
    core_deps = [
        "PyQt6>=6.4.0",
        "requests>=2.28.0", 
        "beautifulsoup4>=4.11.0",
        "lxml>=4.9.0"
    ]
    
    # 可选依赖列表
    optional_deps = [
        "psutil>=5.9.0",
        "pillow>=9.0.0"
    ]
    
    # 安装核心依赖
    for dep in core_deps:
        if not run_command(f"pip install {dep}", f"安装 {dep}"):
            print(f"❌ 核心依赖 {dep} 安装失败")
            return False
    
    # 安装可选依赖（失败不影响继续）
    for dep in optional_deps:
        run_command(f"pip install {dep}", f"安装 {dep} (可选)")
    
    return True

def verify_installation():
    """验证安装"""
    print("\\n🔍 验证安装...")
    
    # 测试导入
    test_imports = [
        ("PyQt6.QtWidgets", "PyQt6核心组件"),
        ("PyQt6.QtCore", "PyQt6核心"),
        ("PyQt6.QtGui", "PyQt6GUI"),
        ("requests", "HTTP请求库"),
        ("bs4", "BeautifulSoup4")
    ]
    
    all_good = True
    
    for module, name in test_imports:
        try:
            __import__(module)
            print(f"✅ {name} 导入成功")
        except ImportError as e:
            print(f"❌ {name} 导入失败: {e}")
            all_good = False
    
    return all_good

def test_gui_creation():
    """测试GUI创建"""
    print("\\n🖥️ 测试GUI环境...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QCoreApplication
        
        # 创建测试应用
        app = QCoreApplication([])
        print("✅ PyQt6应用程序创建成功")
        
        # 检查PyQt6版本
        from PyQt6.QtCore import QT_VERSION_STR
        print(f"✅ PyQt6版本: {QT_VERSION_STR}")
        
        return True
        
    except Exception as e:
        print(f"❌ GUI环境测试失败: {e}")
        return False

def create_desktop_shortcut():
    """创建桌面快捷方式（Windows）"""
    if sys.platform != "win32":
        return
    
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        path = os.path.join(desktop, "PoE2 Build Generator.lnk")
        target = os.path.join(os.getcwd(), "run_gui.py")
        wDir = os.getcwd()
        icon = target
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = f'"{target}"'
        shortcut.WorkingDirectory = wDir
        shortcut.IconLocation = icon
        shortcut.save()
        
        print("✅ 桌面快捷方式创建成功")
        
    except ImportError:
        print("ℹ️ 跳过桌面快捷方式创建（需要安装 winshell 和 pywin32）")
    except Exception as e:
        print(f"⚠️ 桌面快捷方式创建失败: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("🎯 PoE2 Build Generator GUI 安装和设置")
    print("=" * 60)
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 安装依赖项
    if not install_dependencies():
        print("\\n❌ 依赖项安装失败，请手动安装后重试")
        sys.exit(1)
    
    # 验证安装
    if not verify_installation():
        print("\\n❌ 安装验证失败，请检查错误信息")
        sys.exit(1)
    
    # 测试GUI环境
    if not test_gui_creation():
        print("\\n❌ GUI环境测试失败，请检查系统兼容性")
        sys.exit(1)
    
    # 创建桌面快捷方式
    create_desktop_shortcut()
    
    print("\\n" + "=" * 60)
    print("🎉 GUI环境设置完成！")
    print("=" * 60)
    print("\\n📋 下一步操作:")
    print("1. 运行GUI应用: python run_gui.py")
    print("2. 或使用桌面快捷方式 (Windows)")
    print("3. 在设置页面配置PoB2路径和后端连接")
    print("\\n📖 更多信息请查看 GUI_README.md")
    
    # 询问是否立即启动
    try:
        response = input("\\n❓ 是否立即启动GUI？(y/N): ").strip().lower()
        if response in ['y', 'yes', '是']:
            print("\\n🚀 启动GUI应用程序...")
            os.system("python run_gui.py")
    except (KeyboardInterrupt, EOFError):
        print("\\n👋 安装完成，稍后可手动启动GUI")

if __name__ == "__main__":
    main()