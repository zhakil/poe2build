"""
基础GUI组件库

提供PoE2应用程序的基础组件类，确保一致性和复用性。
包含基础小部件、表单组件、布局助手等。
"""

from typing import Optional, Dict, Any, Callable, Union
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QGroupBox, QComboBox,
    QLineEdit, QTextEdit, QSpinBox, QCheckBox, QRadioButton,
    QProgressBar, QScrollArea, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QFont, QPainter, QPaintEvent

from ..styles.poe2_theme import PoE2Theme


class PoE2BaseWidget(QWidget):
    """
    PoE2基础组件类
    
    所有自定义组件的基类，提供统一的样式和行为。
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme = PoE2Theme()
        self._setup_base_style()
        
    def _setup_base_style(self):
        """设置基础样式"""
        self.setStyleSheet(f"""
            PoE2BaseWidget {{
                background-color: {self.theme.get_color('background_primary')};
                color: {self.theme.get_color('text_primary')};
            }}
        """)
        
    def apply_theme_style(self, style_name: str):
        """应用主题样式"""
        if hasattr(self.theme, 'apply_poe2_style_properties'):
            self.theme.apply_poe2_style_properties(self, style_name)


class PoE2GroupBox(QGroupBox):
    """PoE2风格分组框"""
    
    def __init__(self, title: str, enhanced: bool = False, parent=None):
        super().__init__(title, parent)
        self.theme = PoE2Theme()
        self.enhanced = enhanced
        self._setup_style()
        
    def _setup_style(self):
        """设置样式"""
        if self.enhanced:
            self.setProperty("poe2_enhanced", "true")
        
        self.setStyleSheet(f"""
            QGroupBox {{
                font-size: 14px;
                font-weight: 600;
                color: {self.theme.get_color('text_primary')};
                border: 2px solid {self.theme.get_color('border_primary')};
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
                background-color: {self.theme.get_color('background_secondary')};
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: {self.theme.get_color('text_highlight')};
                background-color: {self.theme.get_color('background_primary')};
            }}
            
            QGroupBox[poe2_enhanced="true"] {{
                border-color: {self.theme.get_color('poe2_gold')};
            }}
            
            QGroupBox[poe2_enhanced="true"]::title {{
                color: {self.theme.get_color('poe2_gold')};
            }}
        """)


class PoE2Button(QPushButton):
    """PoE2风格按钮"""
    
    def __init__(self, text: str, button_type: str = "primary", parent=None):
        super().__init__(text, parent)
        self.theme = PoE2Theme()
        self.button_type = button_type
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_style()
        self._setup_animations()
        
    def _setup_style(self):
        """设置按钮样式"""
        if self.button_type == "accent":
            self.setProperty("poe2_style", "accent")
        else:
            self.setProperty("poe2_style", "primary")
            
        base_style = f"""
            QPushButton {{
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
                min-height: 20px;
                font-size: 13px;
            }}
        """
        
        if self.button_type == "accent":
            style = base_style + f"""
                QPushButton {{
                    background-color: {self.theme.get_color('poe2_gold')};
                    color: {self.theme.get_color('background_primary')};
                    border: 2px solid {self.theme.get_color('poe2_gold')};
                    font-weight: 600;
                }}
                
                QPushButton:hover {{
                    background-color: {self.theme.get_color('poe2_gold_hover')};
                }}
                
                QPushButton:pressed {{
                    background-color: {self.theme.get_color('button_accent_pressed')};
                }}
            """
        else:
            style = base_style + f"""
                QPushButton {{
                    background-color: {self.theme.get_color('button_primary')};
                    color: {self.theme.get_color('text_primary')};
                    border: 1px solid {self.theme.get_color('border_primary')};
                }}
                
                QPushButton:hover {{
                    background-color: {self.theme.get_color('button_primary_hover')};
                    border-color: {self.theme.get_color('border_hover')};
                }}
                
                QPushButton:pressed {{
                    background-color: {self.theme.get_color('button_primary_pressed')};
                }}
                
                QPushButton:disabled {{
                    background-color: {self.theme.get_color('background_tertiary')};
                    color: {self.theme.get_color('text_disabled')};
                    border-color: {self.theme.get_color('text_disabled')};
                }}
            """
            
        self.setStyleSheet(style)
    
    def _setup_animations(self):
        """设置按钮动画"""
        # 可以在这里添加按钮的动画效果
        pass


class PoE2ComboBox(QComboBox):
    """PoE2风格下拉框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme = PoE2Theme()
        self._setup_style()
        
    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.theme.get_color('input_background')};
                border: 1px solid {self.theme.get_color('input_border')};
                color: {self.theme.get_color('text_primary')};
                padding: 8px 12px;
                border-radius: 6px;
                min-height: 20px;
            }}
            
            QComboBox:hover {{
                border-color: {self.theme.get_color('border_hover')};
            }}
            
            QComboBox:focus {{
                border-color: {self.theme.get_color('poe2_gold')};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border: 4px solid transparent;
                border-top: 6px solid {self.theme.get_color('text_primary')};
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {self.theme.get_color('background_secondary')};
                border: 1px solid {self.theme.get_color('border_primary')};
                selection-background-color: {self.theme.get_color('poe2_gold')};
                selection-color: {self.theme.get_color('background_primary')};
                outline: none;
            }}
        """)


class PoE2LineEdit(QLineEdit):
    """PoE2风格输入框"""
    
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.theme = PoE2Theme()
        if placeholder:
            self.setPlaceholderText(placeholder)
        self._setup_style()
        
    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.theme.get_color('input_background')};
                border: 1px solid {self.theme.get_color('input_border')};
                color: {self.theme.get_color('text_primary')};
                padding: 8px;
                border-radius: 6px;
                selection-background-color: {self.theme.get_color('poe2_gold')};
                selection-color: {self.theme.get_color('background_primary')};
            }}
            
            QLineEdit:focus {{
                border-color: {self.theme.get_color('poe2_gold')};
            }}
        """)


class PoE2TextEdit(QTextEdit):
    """PoE2风格文本编辑器"""
    
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.theme = PoE2Theme()
        if placeholder:
            self.setPlaceholderText(placeholder)
        self._setup_style()
        
    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.theme.get_color('input_background')};
                border: 1px solid {self.theme.get_color('input_border')};
                color: {self.theme.get_color('text_primary')};
                padding: 8px;
                border-radius: 6px;
                selection-background-color: {self.theme.get_color('poe2_gold')};
                selection-color: {self.theme.get_color('background_primary')};
            }}
            
            QTextEdit:focus {{
                border-color: {self.theme.get_color('poe2_gold')};
            }}
        """)


class PoE2ProgressBar(QProgressBar):
    """PoE2风格进度条"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme = PoE2Theme()
        self._setup_style()
        
    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet(f"""
            QProgressBar {{
                background-color: {self.theme.get_color('background_secondary')};
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 6px;
                text-align: center;
                color: {self.theme.get_color('text_primary')};
                font-weight: 500;
            }}
            
            QProgressBar::chunk {{
                background-color: {self.theme.get_color('poe2_gold')};
                border-radius: 5px;
            }}
        """)


class PoE2Card(QFrame):
    """PoE2风格卡片容器"""
    
    # 信号定义
    clicked = pyqtSignal()
    
    def __init__(self, title: str = "", clickable: bool = False, parent=None):
        super().__init__(parent)
        self.theme = PoE2Theme()
        self.title = title
        self.clickable = clickable
        self.is_hovered = False
        
        if clickable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            
        self._setup_ui()
        self._setup_style()
        
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        if self.title:
            title_label = QLabel(self.title)
            title_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.theme.get_color('text_highlight')};
                    font-size: 16px;
                    font-weight: 600;
                    margin-bottom: 4px;
                }}
            """)
            layout.addWidget(title_label)
            
    def _setup_style(self):
        """设置样式"""
        self.setProperty("poe2_card", "true")
        
        base_style = f"""
            QFrame[poe2_card="true"] {{
                background-color: {self.theme.get_color('background_secondary')};
                border: 2px solid {self.theme.get_color('border_primary')};
                border-radius: 10px;
            }}
        """
        
        if self.clickable:
            style = base_style + f"""
                QFrame[poe2_card="true"]:hover {{
                    border-color: {self.theme.get_color('poe2_gold')};
                    background-color: {self.theme.get_color('background_tertiary')};
                }}
            """
        else:
            style = base_style
            
        self.setStyleSheet(style)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if self.clickable and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        self.is_hovered = True
        if self.clickable:
            self.update()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.is_hovered = False
        if self.clickable:
            self.update()
        super().leaveEvent(event)


class PoE2StatusIndicator(QWidget):
    """PoE2状态指示器"""
    
    def __init__(self, status: str = "unknown", text: str = "", parent=None):
        super().__init__(parent)
        self.theme = PoE2Theme()
        self.status = status
        self.text = text
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        
        # 状态图标
        self.status_icon = QLabel()
        self.status_icon.setFixedSize(12, 12)
        layout.addWidget(self.status_icon)
        
        # 状态文本
        self.status_text = QLabel(self.text)
        self.status_text.setStyleSheet(f"color: {self.theme.get_color('text_primary')};")
        layout.addWidget(self.status_text)
        
        self.update_status(self.status, self.text)
        
    def update_status(self, status: str, text: str = ""):
        """更新状态"""
        self.status = status
        if text:
            self.text = text
            self.status_text.setText(text)
            
        # 状态颜色映射
        status_colors = {
            'healthy': self.theme.get_color('success'),
            'warning': self.theme.get_color('warning'),
            'error': self.theme.get_color('error'),
            'offline': self.theme.get_color('text_disabled'),
            'loading': self.theme.get_color('info')
        }
        
        # 状态图标
        status_icons = {
            'healthy': '🟢',
            'warning': '🟡',
            'error': '🔴',
            'offline': '⚫',
            'loading': '🔄'
        }
        
        color = status_colors.get(status, self.theme.get_color('text_secondary'))
        icon = status_icons.get(status, '⚪')
        
        self.status_icon.setText(icon)
        self.status_text.setStyleSheet(f"color: {color};")


class PoE2FormSection:
    """PoE2表单区域助手类"""
    
    @staticmethod
    def create_form_row(label_text: str, widget: QWidget, 
                       description: str = "", parent=None) -> QWidget:
        """创建表单行"""
        row_widget = QWidget(parent)
        layout = QVBoxLayout(row_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # 标签
        label = QLabel(label_text)
        theme = PoE2Theme()
        label.setStyleSheet(f"""
            QLabel {{
                color: {theme.get_color('text_primary')};
                font-weight: 500;
                font-size: 13px;
            }}
        """)
        layout.addWidget(label)
        
        # 输入组件
        layout.addWidget(widget)
        
        # 描述文本（可选）
        if description:
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet(f"""
                QLabel {{
                    color: {theme.get_color('text_secondary')};
                    font-size: 11px;
                    margin-top: 2px;
                }}
            """)
            layout.addWidget(desc_label)
            
        return row_widget
    
    @staticmethod
    def create_button_row(buttons: list, alignment=Qt.AlignmentFlag.AlignCenter,
                         spacing: int = 12, parent=None) -> QWidget:
        """创建按钮行"""
        row_widget = QWidget(parent)
        layout = QHBoxLayout(row_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(spacing)
        layout.setAlignment(alignment)
        
        for button in buttons:
            layout.addWidget(button)
            
        return row_widget


class PoE2LayoutHelper:
    """PoE2布局助手类"""
    
    @staticmethod
    def create_vertical_spacer(size: int = 20) -> QSpacerItem:
        """创建垂直间隔"""
        return QSpacerItem(20, size, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
    
    @staticmethod
    def create_horizontal_spacer(size: int = 20) -> QSpacerItem:
        """创建水平间隔"""
        return QSpacerItem(size, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
    
    @staticmethod
    def create_expanding_spacer(vertical: bool = True) -> QSpacerItem:
        """创建弹性间隔"""
        if vertical:
            return QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        else:
            return QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
    
    @staticmethod
    def wrap_in_scroll_area(widget: QWidget, max_height: int = None) -> QScrollArea:
        """将组件包装在滚动区域中"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setWidget(widget)
        
        if max_height:
            scroll_area.setMaximumHeight(max_height)
            
        # 应用主题样式
        theme = PoE2Theme()
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: transparent;
            }}
        """)
        
        return scroll_area


# 预设配置
class PoE2Presets:
    """PoE2预设配置"""
    
    BUTTON_SIZES = {
        'small': (80, 30),
        'medium': (120, 36),
        'large': (160, 42),
        'extra_large': (200, 48)
    }
    
    SPACING = {
        'tight': 4,
        'normal': 8,
        'loose': 12,
        'extra_loose': 16
    }
    
    MARGINS = {
        'none': (0, 0, 0, 0),
        'small': (8, 8, 8, 8),
        'normal': (16, 16, 16, 16),
        'large': (24, 24, 24, 24)
    }