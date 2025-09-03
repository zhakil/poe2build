#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PoE2 Build Generator - 带控制台输出的GUI版本
"""

import sys
import os
import subprocess

# Windows控制台设置
if sys.platform.startswith('win'):
    # 分配控制台窗口
    try:
        import ctypes
        from ctypes import wintypes
        
        # 分配控制台
        kernel32 = ctypes.windll.kernel32
        kernel32.AllocConsole()
        
        # 重定向标准输出到控制台
        sys.stdout = open('CONOUT$', 'w', encoding='utf-8')
        sys.stderr = open('CONOUT$', 'w', encoding='utf-8')
        sys.stdin = open('CONIN$', 'r', encoding='utf-8')
        
        # 设置控制台标题
        kernel32.SetConsoleTitleW("PoE2 Build Generator - 控制台输出")
        
    except Exception as e:
        print(f"控制台设置错误: {e}")

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 60)
print("PoE2 Build Generator - 控制台模式启动")
print("=" * 60)
print()

try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
    from PyQt6.QtCore import Qt, pyqtSlot
    from PyQt6.QtGui import QFont
    
    from poe2build.gui.styles.poe2_theme import PoE2Theme
    from poe2build.gui.pages.welcome_page import WelcomePage
    
    print("✓ GUI模块导入成功")
    
except ImportError as e:
    print(f"✗ 导入错误: {e}")
    sys.exit(1)


class ConsoleMainWindow(QMainWindow):
    """带控制台输出的主窗口"""
    
    def __init__(self):
        super().__init__()
        print("正在初始化GUI窗口...")
        self.theme = PoE2Theme()
        self._setup_window()
        self._create_welcome_page()
        print("✓ GUI窗口初始化完成")
        
    def _setup_window(self):
        """设置主窗口"""
        self.setWindowTitle("PoE2 构筑生成器 - 控制台模式")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # 应用主题
        self.setPalette(self.theme.get_palette())
        self.setStyleSheet(self.theme.get_stylesheet())
        
    def _create_welcome_page(self):
        """创建欢迎页面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.welcome_page = WelcomePage()
        
        # 连接信号到控制台输出
        self.welcome_page.navigate_to.connect(self._on_navigate)
        self.welcome_page.build_selected.connect(self._on_build_selected)
        self.welcome_page.pob2_action.connect(self._on_pob2_action)
        
        layout.addWidget(self.welcome_page)
        
    @pyqtSlot(str)
    def _on_navigate(self, page: str):
        """处理页面导航"""
        print(f"\n🔗 导航操作: {page}")
        if page == "build_generator":
            print("  → 切换到构筑生成器页面")
        elif page == "settings":
            print("  → 打开设置页面")
        elif page == "help":
            print("  → 打开帮助页面")
        elif page == "market":
            print("  → 打开市场数据页面")
        else:
            print(f"  → 未知页面: {page}")
        print("-" * 40)
            
    @pyqtSlot(object)
    def _on_build_selected(self, build_data):
        """处理构筑选择"""
        print(f"\n⚔️ 构筑选择: {build_data}")
        print("  → 加载构筑详情...")
        print("  → 准备PoB2集成...")
        print("-" * 40)
        
    @pyqtSlot(str)
    def _on_pob2_action(self, action: str):
        """处理PoB2操作"""
        print(f"\n🔧 PoB2操作: {action}")
        if action == "configure":
            print("  → 打开PoB2配置对话框")
        elif action == "launch":
            print("  → 启动PoB2应用程序")
        else:
            print(f"  → 执行PoB2操作: {action}")
        print("-" * 40)
            
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        print("\n🚪 正在关闭应用程序...")
        print("再见!")
        event.accept()


def main():
    """主函数"""
    print("🚀 启动PoE2 Build Generator...")
    
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("PoE2 Build Generator Console")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("PoE2 Tools")
    
    # 设置字体
    font = QFont("Microsoft YaHei UI", 9)
    app.setFont(font)
    
    # 应用主题
    theme = PoE2Theme()
    app.setPalette(theme.get_palette())
    app.setStyleSheet(theme.get_stylesheet())
    
    try:
        # 创建主窗口
        window = ConsoleMainWindow()
        window.show()
        
        print("\n" + "=" * 60)
        print("✅ GUI应用程序已启动!")
        print("=" * 60)
        print()
        print("🎮 功能说明:")
        print("  - GUI窗口: 交互式Path of Building风格界面")
        print("  - 控制台: 实时显示用户操作和系统响应")
        print("  - 集成: PoB2数据源和AI推荐系统")
        print()
        print("🖱️ 操作提示:")
        print("  - 点击GUI中的任何按钮")
        print("  - 查看此控制台窗口的实时反馈")
        print("  - 所有操作都会在这里显示详细信息")
        print()
        print("🔍 当前状态: 等待用户交互...")
        print("=" * 60)
        
        # 运行应用程序
        return app.exec()
        
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())