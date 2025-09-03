#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PoE2 Build Generator - 全新首页界面演示

参考Path of Building 2设计的专业级PoE2构筑生成器首页界面演示程序。
展示新的UI设计、组件交互和功能模块。
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
    from PyQt6.QtCore import Qt, pyqtSlot
    from PyQt6.QtGui import QFont
    
    from poe2build.gui.styles.poe2_theme import PoE2Theme
    from poe2build.gui.pages.welcome_page import WelcomePage
    
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装PyQt6: pip install PyQt6")
    sys.exit(1)


class DemoMainWindow(QMainWindow):
    """演示主窗口"""
    
    def __init__(self):
        super().__init__()
        self.theme = PoE2Theme()
        self._setup_window()
        self._create_welcome_page()
        
    def _setup_window(self):
        """设置主窗口"""
        self.setWindowTitle("PoE2 构筑生成器 - 全新首页界面演示")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # 应用主题
        self.setPalette(self.theme.get_palette())
        self.setStyleSheet(self.theme.get_stylesheet())
        
        # 设置窗口图标（如果有的话）
        self.setWindowFlags(Qt.WindowType.Window)
        
    def _create_welcome_page(self):
        """创建欢迎页面"""
        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建欢迎页面
        self.welcome_page = WelcomePage()
        
        # 连接信号
        self.welcome_page.navigate_to.connect(self._on_navigate)
        self.welcome_page.build_selected.connect(self._on_build_selected)
        self.welcome_page.pob2_action.connect(self._on_pob2_action)
        
        layout.addWidget(self.welcome_page)
        
    @pyqtSlot(str)
    def _on_navigate(self, page: str):
        """处理页面导航"""
        print(f"导航请求: {page}")
        # 在实际应用中，这里会切换到相应的页面
        if page == "build_generator":
            print("切换到构筑生成器页面")
        elif page == "settings":
            print("打开设置页面")
        elif page == "help":
            print("打开帮助页面")
        elif page == "market":
            print("打开市场数据页面")
        else:
            print(f"未知页面: {page}")
            
    @pyqtSlot(object)
    def _on_build_selected(self, build_data):
        """处理构筑选择"""
        print(f"选择构筑: {build_data}")
        # 在实际应用中，这里会显示构筑详情或加载构筑
        
    @pyqtSlot(str)
    def _on_pob2_action(self, action: str):
        """处理PoB2操作"""
        print(f"PoB2操作: {action}")
        if action == "configure":
            print("打开PoB2配置对话框")
        elif action == "launch":
            print("启动PoB2应用程序")
        else:
            print(f"未知PoB2操作: {action}")
            
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        print("关闭演示程序...")
        event.accept()


def main():
    """主函数"""
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("PoE2 Build Generator")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("PoE2 Tools")
    
    # 设置应用程序字体
    font = QFont("Microsoft YaHei UI", 9)  # 中文友好字体
    app.setFont(font)
    
    # 创建主题
    theme = PoE2Theme()
    
    # 应用全局主题
    app.setPalette(theme.get_palette())
    app.setStyleSheet(theme.get_stylesheet())
    
    try:
        # 创建主窗口
        window = DemoMainWindow()
        window.show()
        
        # 显示使用说明
        print("="*60)
        print("PoE2 Build Generator - 全新首页界面演示")
        print("="*60)
        print()
        print("功能特性:")
        print("[界面] 左侧面板:")
        print("  - 快速开始卡片 - 新手引导和快捷操作")
        print("  - AI智能推荐 - 热门构筑推荐展示")
        print()
        print("[工具] 右侧面板 (选项卡):")
        print("  - 状态监控:")
        print("    * PoB2集成状态面板")
        print("    * 系统服务监控面板")
        print("  - 历史&市场:")
        print("    * 最近构筑历史")
        print("    * 市场数据摘要")
        print()
        print("[设计] 特色:")
        print("  - Path of Building 2风格的深色主题")
        print("  - 金色高亮效果和专业配色")
        print("  - 响应式分割器布局")
        print("  - 平滑动画和悬停效果")
        print("  - 实时状态监控和更新")
        print()
        print("[功能] 交互:")
        print("  - 点击按钮查看控制台输出")
        print("  - 推荐构筑点击选择")
        print("  - PoB2状态实时模拟")
        print("  - 服务状态动态更新")
        print()
        print("[提示] 使用说明:")
        print("  - 所有按钮和组件都可以交互")
        print("  - 查看控制台了解功能响应")
        print("  - 拖拽中央分割器调整面板大小")
        print("="*60)
        
        # 运行应用程序
        return app.exec()
        
    except Exception as e:
        print(f"程序运行错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())