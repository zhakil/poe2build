"""
导航栏组件

左侧导航栏，包含页面切换按钮和状态指示器。
"""

from typing import List, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFrame, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont

from ..styles.poe2_theme import PoE2Theme


class NavigationButton(QPushButton):
    """导航按钮类"""
    
    def __init__(self, text: str, page_id: str, icon_name: str = None):
        super().__init__()
        self.page_id = page_id
        self.setText(text)
        self.setMinimumHeight(40)
        self.setCheckable(True)
        
        # 设置按钮样式
        theme = PoE2Theme()
        self.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding: 12px 16px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                color: {theme.get_color('text_primary')};
                background-color: transparent;
                transition: all 200ms ease-in-out;
            }}
            
            QPushButton:checked {{
                background-color: {theme.get_color('poe2_gold')};
                color: {theme.get_color('background_primary')};
                font-weight: 600;
            }}
            
            QPushButton:hover:!checked {{
                background-color: {theme.get_color('background_tertiary')};
                border-left: 3px solid {theme.get_color('poe2_gold')};
            }}
            
            QPushButton:pressed {{
                background-color: {theme.get_color('background_quaternary')};
            }}
        """)


class NavigationBar(QWidget):
    """导航栏组件"""
    
    # 信号定义
    page_requested = pyqtSignal(str)  # 请求切换页面信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.theme = PoE2Theme()
        self.buttons: Dict[str, NavigationButton] = {}
        self.current_page = ""
        
        self._init_ui()
        self._setup_pages()
    
    def _init_ui(self):
        """初始化用户界面"""
        # 设置固定宽度
        self.setFixedWidth(200)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # 应用标题
        title_label = QLabel("PoE2 构筑生成器")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_highlight')};
                font-size: 16px;
                font-weight: 600;
                padding: 12px 8px;
                border-bottom: 2px solid {self.theme.get_color('border_primary')};
                margin-bottom: 8px;
            }}
        """)
        layout.addWidget(title_label)
        
        # 导航按钮区域
        self.nav_layout = QVBoxLayout()
        self.nav_layout.setSpacing(2)
        layout.addLayout(self.nav_layout)
        
        # 添加弹性空间
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(spacer)
        
        # 状态区域
        self._setup_status_area(layout)
        
        # 设置整体样式
        self.setStyleSheet(f"""
            NavigationBar {{
                background-color: {self.theme.get_color('background_secondary')};
                border-right: 1px solid {self.theme.get_color('border_primary')};
            }}
        """)
    
    def _setup_pages(self):
        """设置页面按钮"""
        pages = [
            ("欢迎", "welcome", "home"),
            ("构筑生成器", "build_generator", "build"),
            ("构筑结果", "build_results", "results"),
            ("设置", "settings", "settings")
        ]
        
        for text, page_id, icon in pages:
            self.add_navigation_button(text, page_id, icon)
    
    def _setup_status_area(self, layout: QVBoxLayout):
        """设置状态区域"""
        # 分割线
        separator = QFrame()
        separator.setFrameStyle(QFrame.Shape.HLine)
        separator.setStyleSheet(f"color: {self.theme.get_color('border_primary')};")
        layout.addWidget(separator)
        
        # 状态标题
        status_title = QLabel("系统状态")
        status_title.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_secondary')};
                font-size: 12px;
                font-weight: 600;
                padding: 8px;
            }}
        """)
        layout.addWidget(status_title)
        
        # 后端状态
        self.backend_status = QLabel("🔴 后端离线")
        self.backend_status.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_primary')};
                font-size: 11px;
                padding: 4px 8px;
            }}
        """)
        layout.addWidget(self.backend_status)
        
        # PoB2状态
        self.pob2_status = QLabel("⚪ PoB2未检测")
        self.pob2_status.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_primary')};
                font-size: 11px;
                padding: 4px 8px;
            }}
        """)
        layout.addWidget(self.pob2_status)
    
    def add_navigation_button(self, text: str, page_id: str, icon_name: str = None):
        """添加导航按钮"""
        button = NavigationButton(text, page_id, icon_name)
        button.clicked.connect(lambda: self._on_button_clicked(page_id))
        
        self.buttons[page_id] = button
        self.nav_layout.addWidget(button)
    
    def _on_button_clicked(self, page_id: str):
        """处理按钮点击事件"""
        self.set_active_page(page_id)
        self.page_requested.emit(page_id)
    
    def set_active_page(self, page_id: str):
        """设置当前活跃页面"""
        # 取消所有按钮的选中状态
        for button in self.buttons.values():
            button.setChecked(False)
        
        # 设置指定按钮为选中状态
        if page_id in self.buttons:
            self.buttons[page_id].setChecked(True)
            self.current_page = page_id
    
    def update_backend_status(self, is_online: bool):
        """更新后端状态显示"""
        if is_online:
            self.backend_status.setText("🟢 后端在线")
        else:
            self.backend_status.setText("🔴 后端离线")
    
    def update_pob2_status(self, is_available: bool):
        """更新PoB2状态显示"""
        if is_available:
            self.pob2_status.setText("🟢 PoB2已连接")
        else:
            self.pob2_status.setText("🟡 PoB2未检测")
    
    def get_current_page(self) -> str:
        """获取当前活跃页面"""
        return self.current_page