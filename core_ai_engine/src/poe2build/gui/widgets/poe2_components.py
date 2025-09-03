"""
PoE2专业UI组件库

基于Path of Exile 2视觉设计语言的专用组件集合，
包含构筑卡片、职业选择器、技能树预览、装备展示等核心组件。
"""

import sys
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QProgressBar, QComboBox,
    QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, 
    QGraphicsLineItem, QGraphicsTextItem, QSizePolicy,
    QButtonGroup, QRadioButton, QGroupBox, QApplication,
    QStackedWidget, QSplitter, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPointF
from PyQt6.QtGui import (
    QPainter, QPaintEvent, QColor, QBrush, QPen, QFont, 
    QFontMetrics, QPixmap, QIcon, QLinearGradient, QRadialGradient,
    QPainterPath, QTransform
)

from ..styles.poe2_theme import PoE2Theme

# 条件导入，用于测试环境
try:
    from ...models.build import PoE2Build, PoE2BuildStats, PoE2BuildGoal
    from ...models.characters import PoE2CharacterClass, PoE2Ascendancy
    from ...utils.poe2_constants import PoE2Constants
except ImportError:
    # 模拟类用于测试
    PoE2Build = None
    PoE2BuildStats = None
    PoE2BuildGoal = None
    PoE2CharacterClass = None
    PoE2Ascendancy = None
    PoE2Constants = None


class PoE2AnimationState(Enum):
    """PoE2动画状态枚举"""
    IDLE = "idle"
    HOVER = "hover" 
    PRESSED = "pressed"
    LOADING = "loading"


class PoE2BaseWidget(QWidget):
    """PoE2基础组件类，提供通用的样式和动画功能"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme = PoE2Theme()
        self.animation_state = PoE2AnimationState.IDLE
        self.hover_animation = None
        self._setup_animations()
        
    def _setup_animations(self):
        """设置动画效果"""
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(200)
        self.hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def enterEvent(self, event):
        """鼠标进入事件"""
        self.animation_state = PoE2AnimationState.HOVER
        self.update()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.animation_state = PoE2AnimationState.IDLE
        self.update()
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        self.animation_state = PoE2AnimationState.PRESSED
        self.update()
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self.animation_state = PoE2AnimationState.HOVER
        self.update()
        super().mouseReleaseEvent(event)


class BuildCard(PoE2BaseWidget):
    """构筑卡片组件 - 展示构筑核心信息"""
    
    # 信号定义
    clicked = pyqtSignal(object)  # 发送PoE2Build对象
    favorited = pyqtSignal(object)  # 收藏信号
    view_details = pyqtSignal(object)  # 查看详情信号
    
    def __init__(self, build: PoE2Build, parent=None):
        super().__init__(parent)
        self.build = build
        self.is_favorited = False
        self.setFixedSize(320, 280)  # 固定卡片大小
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI结构"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # 标题区域
        title_layout = QHBoxLayout()
        
        # 构筑名称
        self.name_label = QLabel(self.build.name)
        self.name_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_highlight')};
                font-size: 16px;
                font-weight: 600;
            }}
        """)
        
        # 收藏按钮
        self.favorite_btn = QPushButton("★")
        self.favorite_btn.setFixedSize(24, 24)
        self.favorite_btn.clicked.connect(self._on_favorite_clicked)
        self.favorite_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {self.theme.get_color('text_secondary')};
                font-size: 18px;
            }}
            QPushButton:hover {{
                color: {self.theme.get_color('poe2_gold')};
            }}
        """)
        
        title_layout.addWidget(self.name_label)
        title_layout.addStretch()
        title_layout.addWidget(self.favorite_btn)
        
        # 职业和升华信息
        class_layout = QHBoxLayout()
        
        # 职业图标（模拟）
        self.class_icon = QLabel("⚔️")  # 可替换为实际图标
        self.class_icon.setFixedSize(32, 32)
        self.class_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.class_icon.setStyleSheet(f"""
            QLabel {{
                background-color: {self.theme.get_color('background_tertiary')};
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 16px;
                font-size: 20px;
            }}
        """)
        
        # 职业和升华文本
        class_info = f"{self.build.character_class.value}"
        if self.build.ascendancy:
            class_info += f" - {self.build.ascendancy.value}"
        self.class_label = QLabel(class_info)
        self.class_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_primary')};
                font-size: 12px;
            }}
        """)
        
        # 等级标签
        self.level_label = QLabel(f"Level {self.build.level}")
        self.level_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_secondary')};
                font-size: 11px;
                background-color: {self.theme.get_color('background_tertiary')};
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 8px;
                padding: 2px 6px;
            }}
        """)
        
        class_layout.addWidget(self.class_icon)
        class_layout.addWidget(self.class_label)
        class_layout.addStretch()
        class_layout.addWidget(self.level_label)
        
        # 主技能
        if self.build.main_skill_gem:
            self.skill_label = QLabel(f"主技能: {self.build.main_skill_gem}")
            self.skill_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.theme.get_color('poe2_blue')};
                    font-size: 11px;
                    font-style: italic;
                }}
            """)
        else:
            self.skill_label = QLabel("主技能: 未指定")
            self.skill_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.theme.get_color('text_disabled')};
                    font-size: 11px;
                    font-style: italic;
                }}
            """)
        
        # 统计数据区域
        if self.build.stats:
            stats_widget = self._create_stats_widget()
        else:
            stats_widget = QLabel("统计数据不可用")
            stats_widget.setStyleSheet(f"color: {self.theme.get_color('text_disabled')};")
            stats_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 成本信息
        cost_layout = QHBoxLayout()
        if self.build.estimated_cost:
            cost_text = f"{self.build.estimated_cost:.1f} {self.build.currency_type.upper()}"
            cost_color = self.theme.get_cost_tier_color(self.build.estimated_cost)
        else:
            cost_text = "成本未知"
            cost_color = self.theme.get_color('text_disabled')
            
        self.cost_label = QLabel(cost_text)
        self.cost_label.setStyleSheet(f"""
            QLabel {{
                color: {cost_color};
                font-size: 12px;
                font-weight: 500;
            }}
        """)
        
        # 目标标签
        if self.build.goal:
            goal_color = self.theme.get_goal_color(self.build.goal)
            self.goal_label = QLabel(self.build.goal.value.replace('_', ' ').title())
            self.goal_label.setStyleSheet(f"""
                QLabel {{
                    color: {goal_color};
                    font-size: 10px;
                    background-color: {self.theme.get_color('background_tertiary')};
                    border: 1px solid {goal_color};
                    border-radius: 6px;
                    padding: 1px 4px;
                }}
            """)
        else:
            self.goal_label = QLabel("")
        
        cost_layout.addWidget(self.cost_label)
        cost_layout.addStretch()
        cost_layout.addWidget(self.goal_label)
        
        # 详情按钮
        self.details_btn = QPushButton("查看详情")
        self.details_btn.clicked.connect(lambda: self.view_details.emit(self.build))
        self.details_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme.get_color('button_accent')};
                color: {self.theme.get_color('background_primary')};
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {self.theme.get_color('button_accent_hover')};
            }}
            QPushButton:pressed {{
                background-color: {self.theme.get_color('button_accent_pressed')};
            }}
        """)
        
        # 添加到布局
        layout.addLayout(title_layout)
        layout.addLayout(class_layout)
        layout.addWidget(self.skill_label)
        layout.addWidget(stats_widget)
        layout.addLayout(cost_layout)
        layout.addStretch()
        layout.addWidget(self.details_btn)
        
    def _create_stats_widget(self) -> QWidget:
        """创建统计数据展示组件"""
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(6)
        
        # DPS和EHP
        main_stats_layout = QGridLayout()
        
        # DPS
        dps_label = QLabel("DPS")
        dps_label.setStyleSheet(f"color: {self.theme.get_color('text_secondary')}; font-size: 10px;")
        dps_value = QLabel(f"{self.build.stats.total_dps:,.0f}")
        dps_value.setStyleSheet(f"color: {self.theme.get_color('poe2_red')}; font-size: 12px; font-weight: 600;")
        
        # EHP
        ehp_label = QLabel("EHP")
        ehp_label.setStyleSheet(f"color: {self.theme.get_color('text_secondary')}; font-size: 10px;")
        ehp_value = QLabel(f"{self.build.stats.effective_health_pool:,.0f}")
        ehp_value.setStyleSheet(f"color: {self.theme.get_color('poe2_green')}; font-size: 12px; font-weight: 600;")
        
        main_stats_layout.addWidget(dps_label, 0, 0)
        main_stats_layout.addWidget(dps_value, 1, 0)
        main_stats_layout.addWidget(ehp_label, 0, 1)
        main_stats_layout.addWidget(ehp_value, 1, 1)
        
        # 抗性条
        resistance_widget = self._create_resistance_bars()
        
        stats_layout.addLayout(main_stats_layout)
        stats_layout.addWidget(resistance_widget)
        
        return stats_widget
        
    def _create_resistance_bars(self) -> QWidget:
        """创建抗性条组件"""
        resistance_widget = QWidget()
        res_layout = QVBoxLayout(resistance_widget)
        res_layout.setContentsMargins(0, 0, 0, 0)
        res_layout.setSpacing(2)
        
        resistances = [
            ("火抗", self.build.stats.fire_resistance, self.theme.get_color('poe2_red')),
            ("冰抗", self.build.stats.cold_resistance, self.theme.get_color('poe2_blue')),
            ("雷抗", self.build.stats.lightning_resistance, self.theme.get_color('poe2_gold'))
        ]
        
        for name, value, color in resistances:
            bar_layout = QHBoxLayout()
            bar_layout.setContentsMargins(0, 0, 0, 0)
            
            # 抗性名称
            name_label = QLabel(name)
            name_label.setFixedWidth(30)
            name_label.setStyleSheet(f"color: {self.theme.get_color('text_secondary')}; font-size: 9px;")
            
            # 抗性进度条
            progress = QProgressBar()
            progress.setFixedHeight(8)
            progress.setMinimum(-60)
            progress.setMaximum(80)
            progress.setValue(value)
            progress.setTextVisible(False)
            
            # 根据抗性值设置颜色
            if value >= 75:
                bar_color = self.theme.get_color('success')
            elif value >= 0:
                bar_color = self.theme.get_color('warning')
            else:
                bar_color = self.theme.get_color('error')
                
            progress.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {self.theme.get_color('background_tertiary')};
                    border: 1px solid {self.theme.get_color('border_primary')};
                    border-radius: 4px;
                }}
                QProgressBar::chunk {{
                    background-color: {bar_color};
                    border-radius: 3px;
                }}
            """)
            
            # 抗性数值
            value_label = QLabel(f"{value}%")
            value_label.setFixedWidth(30)
            value_label.setStyleSheet(f"color: {bar_color}; font-size: 9px; font-weight: 600;")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            bar_layout.addWidget(name_label)
            bar_layout.addWidget(progress)
            bar_layout.addWidget(value_label)
            
            res_layout.addLayout(bar_layout)
        
        return resistance_widget
        
    def _on_favorite_clicked(self):
        """处理收藏按钮点击"""
        self.is_favorited = not self.is_favorited
        if self.is_favorited:
            self.favorite_btn.setText("★")
            self.favorite_btn.setStyleSheet(self.favorite_btn.styleSheet().replace(
                self.theme.get_color('text_secondary'), 
                self.theme.get_color('poe2_gold')
            ))
        else:
            self.favorite_btn.setText("☆")
            self.favorite_btn.setStyleSheet(self.favorite_btn.styleSheet().replace(
                self.theme.get_color('poe2_gold'), 
                self.theme.get_color('text_secondary')
            ))
        self.favorited.emit(self.build)
        
    def mousePressEvent(self, event):
        """处理卡片点击"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.build)
        super().mousePressEvent(event)
        
    def paintEvent(self, event: QPaintEvent):
        """自定义绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # 背景颜色根据状态变化
        if self.animation_state == PoE2AnimationState.HOVER:
            bg_color = QColor(self.theme.get_color('background_secondary'))
            border_color = QColor(self.theme.get_color('poe2_gold'))
        elif self.animation_state == PoE2AnimationState.PRESSED:
            bg_color = QColor(self.theme.get_color('background_tertiary'))
            border_color = QColor(self.theme.get_color('poe2_gold'))
        else:
            bg_color = QColor(self.theme.get_color('background_secondary'))
            border_color = QColor(self.theme.get_color('border_primary'))
            
        # 绘制背景和边框
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 2))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8, 8)
        
        # 如果是收藏的构筑，添加金色光晕效果
        if self.is_favorited:
            gradient = QRadialGradient(rect.center(), rect.width() / 2)
            gradient.setColorAt(0, QColor(self.theme.get_color('poe2_gold')).lighter(120))
            gradient.setColorAt(0.7, QColor(self.theme.get_color('poe2_gold')).lighter(110))
            gradient.setColorAt(1, QColor(0, 0, 0, 0))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 6, 6)


class EquipmentDisplay(PoE2BaseWidget):
    """装备展示组件 - 显示装备槽位和装备信息"""
    
    # 信号定义
    equipment_selected = pyqtSignal(str, object)  # 发送槽位名称和装备对象
    equipment_updated = pyqtSignal(str, object)  # 装备更新信号
    
    # 装备槽位定义
    EQUIPMENT_SLOTS = {
        'helmet': {'name': '头盔', 'position': (1, 0), 'icon': '⛑️'},
        'amulet': {'name': '项链', 'position': (1, 1), 'icon': '📿'},
        'chest': {'name': '胸甲', 'position': (2, 0), 'icon': '🛡️'},
        'gloves': {'name': '手套', 'position': (3, 0), 'icon': '🧤'},
        'belt': {'name': '腰带', 'position': (3, 1), 'icon': '🎗️'},
        'boots': {'name': '鞋子', 'position': (4, 0), 'icon': '👢'},
        'main_hand': {'name': '主手', 'position': (1, 2), 'icon': '⚔️'},
        'off_hand': {'name': '副手', 'position': (2, 2), 'icon': '🛡️'},
        'ring1': {'name': '戒指1', 'position': (0, 3), 'icon': '💍'},
        'ring2': {'name': '戒指2', 'position': (1, 3), 'icon': '💍'},
        'flask1': {'name': '药剂1', 'position': (3, 2), 'icon': '🧪'},
        'flask2': {'name': '药剂2', 'position': (3, 3), 'icon': '🧪'},
        'flask3': {'name': '药剂3', 'position': (4, 2), 'icon': '🧪'},
        'flask4': {'name': '药剂4', 'position': (4, 3), 'icon': '🧪'},
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.equipment_slots = {}
        self.equipped_items = {}
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI结构"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 标题
        title = QLabel("装备配置")
        title.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_highlight')};
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 8px;
            }}
        """)
        
        # 装备槽位网格
        equipment_frame = QFrame()
        equipment_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.get_color('background_secondary')};
                border: 2px solid {self.theme.get_color('border_primary')};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        
        equipment_layout = QGridLayout(equipment_frame)
        equipment_layout.setSpacing(8)
        
        # 创建装备槽位
        for slot_id, slot_info in self.EQUIPMENT_SLOTS.items():
            slot_widget = self._create_equipment_slot(slot_id, slot_info)
            self.equipment_slots[slot_id] = slot_widget
            row, col = slot_info['position']
            equipment_layout.addWidget(slot_widget, row, col)
            
        # 装备统计信息
        stats_frame = self._create_equipment_stats_frame()
        
        layout.addWidget(title)
        layout.addWidget(equipment_frame)
        layout.addWidget(stats_frame)
        layout.addStretch()
        
    def _create_equipment_slot(self, slot_id: str, slot_info: Dict) -> QWidget:
        """创建装备槽位组件"""
        slot_widget = QFrame()
        slot_widget.setFixedSize(64, 64)
        slot_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        slot_widget.setProperty("slot_id", slot_id)
        
        # 设置样式
        slot_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.get_color('background_tertiary')};
                border: 2px solid {self.theme.get_color('border_primary')};
                border-radius: 8px;
            }}
            QFrame:hover {{
                border-color: {self.theme.get_color('poe2_gold')};
                background-color: {self.theme.get_color('button_primary_hover')};
            }}
        """)
        
        layout = QVBoxLayout(slot_widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # 装备图标
        icon_label = QLabel(slot_info['icon'])
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 24px;")
        
        # 装备名称标签（初始隐藏）
        name_label = QLabel(slot_info['name'])
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet(f"""
            color: {self.theme.get_color('text_secondary')};
            font-size: 8px;
            font-weight: 500;
        """)
        
        layout.addWidget(icon_label)
        layout.addWidget(name_label)
        
        # 添加鼠标事件处理
        slot_widget.mousePressEvent = lambda event, sid=slot_id: self._on_slot_clicked(sid, event)
        slot_widget.setToolTip(f"{slot_info['name']}\n点击查看详情")
        
        return slot_widget
        
    def _create_equipment_stats_frame(self) -> QWidget:
        """创建装备统计信息框架"""
        stats_frame = QGroupBox("装备统计")
        stats_frame.setStyleSheet(f"""
            QGroupBox {{
                font-size: 14px;
                font-weight: 600;
                color: {self.theme.get_color('text_primary')};
                border: 2px solid {self.theme.get_color('border_primary')};
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: {self.theme.get_color('text_highlight')};
            }}
        """)
        
        layout = QGridLayout(stats_frame)
        layout.setSpacing(8)
        
        # 添加统计标签
        stats_labels = [
            ("总防御", "0", 0, 0),
            ("总生命", "0", 0, 1), 
            ("总法力", "0", 1, 0),
            ("总抗性", "0%", 1, 1),
            ("装备等级", "0", 2, 0),
            ("装备价值", "0 Divine", 2, 1)
        ]
        
        self.equipment_stats_labels = {}
        
        for stat_name, default_value, row, col in stats_labels:
            # 统计名称
            name_label = QLabel(stat_name)
            name_label.setStyleSheet(f"""
                color: {self.theme.get_color('text_secondary')};
                font-size: 10px;
            """)
            
            # 统计数值
            value_label = QLabel(default_value)
            value_label.setStyleSheet(f"""
                color: {self.theme.get_color('text_primary')};
                font-size: 12px;
                font-weight: 600;
            """)
            
            self.equipment_stats_labels[stat_name.lower()] = value_label
            
            stat_layout = QVBoxLayout()
            stat_layout.setContentsMargins(0, 0, 0, 0)
            stat_layout.setSpacing(2)
            stat_layout.addWidget(name_label)
            stat_layout.addWidget(value_label)
            
            stat_widget = QWidget()
            stat_widget.setLayout(stat_layout)
            layout.addWidget(stat_widget, row, col)
            
        return stats_frame
        
    def _on_slot_clicked(self, slot_id: str, event):
        """处理装备槽位点击"""
        if event.button() == Qt.MouseButton.LeftButton:
            current_item = self.equipped_items.get(slot_id)
            self.equipment_selected.emit(slot_id, current_item)
            
    def equip_item(self, slot_id: str, item_data: Dict):
        """装备物品到指定槽位"""
        if slot_id in self.equipment_slots:
            self.equipped_items[slot_id] = item_data
            self._update_slot_display(slot_id, item_data)
            self._update_equipment_stats()
            self.equipment_updated.emit(slot_id, item_data)
            
    def _update_slot_display(self, slot_id: str, item_data: Dict):
        """更新槽位显示"""
        slot_widget = self.equipment_slots[slot_id]
        
        if item_data:
            # 根据装备品质设置边框颜色
            quality_colors = {
                'normal': self.theme.get_color('text_secondary'),
                'magic': self.theme.get_color('poe2_blue'),
                'rare': self.theme.get_color('poe2_gold'), 
                'unique': self.theme.get_color('error')
            }
            border_color = quality_colors.get(item_data.get('quality', 'normal'), 
                                            self.theme.get_color('border_primary'))
            
            slot_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.theme.get_color('background_tertiary')};
                    border: 2px solid {border_color};
                    border-radius: 8px;
                }}
                QFrame:hover {{
                    border-color: {border_color};
                    background-color: {self.theme.get_color('button_primary_hover')};
                }}
            """)
            
            # 更新工具提示
            tooltip = f"{item_data.get('name', '未知装备')}\n{item_data.get('description', '')}"
            slot_widget.setToolTip(tooltip)
        else:
            # 恢复空槽位样式
            slot_info = self.EQUIPMENT_SLOTS[slot_id]
            slot_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.theme.get_color('background_tertiary')};
                    border: 2px solid {self.theme.get_color('border_primary')};
                    border-radius: 8px;
                }}
                QFrame:hover {{
                    border-color: {self.theme.get_color('poe2_gold')};
                    background-color: {self.theme.get_color('button_primary_hover')};
                }}
            """)
            slot_widget.setToolTip(f"{slot_info['name']}\n点击查看详情")
            
    def _update_equipment_stats(self):
        """更新装备统计信息"""
        # 计算装备统计数据（示例实现）
        total_defense = sum(item.get('defense', 0) for item in self.equipped_items.values())
        total_life = sum(item.get('life', 0) for item in self.equipped_items.values())
        total_mana = sum(item.get('mana', 0) for item in self.equipped_items.values())
        total_resistance = sum(item.get('resistance_sum', 0) for item in self.equipped_items.values())
        avg_level = sum(item.get('level', 0) for item in self.equipped_items.values()) / max(len(self.equipped_items), 1)
        total_value = sum(item.get('value', 0) for item in self.equipped_items.values())
        
        # 更新显示
        if 'total_defense' in self.equipment_stats_labels:
            self.equipment_stats_labels['total_defense'].setText(f"{total_defense:,.0f}")
        if 'total_health' in self.equipment_stats_labels:
            self.equipment_stats_labels['总生命'].setText(f"{total_life:,.0f}")
        if 'total_mana' in self.equipment_stats_labels:
            self.equipment_stats_labels['总法力'].setText(f"{total_mana:,.0f}")
        if 'total_resistance' in self.equipment_stats_labels:
            self.equipment_stats_labels['总抗性'].setText(f"{total_resistance:.0f}%")
        if 'equipment_level' in self.equipment_stats_labels:
            self.equipment_stats_labels['装备等级'].setText(f"{avg_level:.0f}")
        if 'equipment_value' in self.equipment_stats_labels:
            self.equipment_stats_labels['装备价值'].setText(f"{total_value:.1f} Divine")


class StatsDisplay(PoE2BaseWidget):
    """数据仪表板组件 - 展示构筑统计数据"""
    
    def __init__(self, stats: Optional[Any] = None, parent=None):
        super().__init__(parent)
        self.stats = stats
        self.stat_widgets = {}
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI结构"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 标题
        title = QLabel("构筑数据仪表板")
        title.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_highlight')};
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 8px;
            }}
        """)
        
        # 创建统计区域
        main_stats_frame = self._create_main_stats_frame()
        resistance_frame = self._create_resistance_frame()
        advanced_stats_frame = self._create_advanced_stats_frame()
        
        layout.addWidget(title)
        layout.addWidget(main_stats_frame)
        layout.addWidget(resistance_frame)
        layout.addWidget(advanced_stats_frame)
        layout.addStretch()
        
    def _create_main_stats_frame(self) -> QWidget:
        """创建主要统计数据框架"""
        frame = QGroupBox("核心数据")
        frame.setStyleSheet(f"""
            QGroupBox {{
                font-size: 14px;
                font-weight: 600;
                color: {self.theme.get_color('text_primary')};
                border: 2px solid {self.theme.get_color('border_primary')};
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: {self.theme.get_color('text_highlight')};
            }}
        """)
        
        layout = QGridLayout(frame)
        layout.setSpacing(16)
        
        # 主要统计数据
        main_stats = [
            ("总DPS", "total_dps", self.theme.get_color('poe2_red'), "伤害每秒"),
            ("有效血量", "effective_health_pool", self.theme.get_color('poe2_green'), "生存能力"),
            ("生命值", "life", self.theme.get_color('success'), "生命点数"),
            ("能量护盾", "energy_shield", self.theme.get_color('poe2_blue'), "护盾点数"),
            ("法力值", "mana", self.theme.get_color('info'), "技能资源"),
            ("移动速度", "movement_speed", self.theme.get_color('poe2_gold'), "移动效率")
        ]
        
        for i, (name, attr, color, description) in enumerate(main_stats):
            stat_widget = self._create_stat_widget(name, attr, color, description, is_main=True)
            self.stat_widgets[attr] = stat_widget
            row = i // 3
            col = i % 3
            layout.addWidget(stat_widget, row, col)
            
        return frame
        
    def _create_resistance_frame(self) -> QWidget:
        """创建抗性展示框架"""
        frame = QGroupBox("抗性数据")
        frame.setStyleSheet(f"""
            QGroupBox {{
                font-size: 14px;
                font-weight: 600;
                color: {self.theme.get_color('text_primary')};
                border: 2px solid {self.theme.get_color('border_primary')};
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: {self.theme.get_color('text_highlight')};
            }}
        """)
        
        layout = QHBoxLayout(frame)
        layout.setSpacing(12)
        
        # 抗性数据
        resistances = [
            ("火抗", "fire_resistance", self.theme.get_color('poe2_red')),
            ("冰抗", "cold_resistance", self.theme.get_color('poe2_blue')),
            ("雷抗", "lightning_resistance", self.theme.get_color('poe2_gold')),
            ("混沌抗", "chaos_resistance", self.theme.get_color('poe2_purple'))
        ]
        
        for name, attr, color in resistances:
            resist_widget = self._create_resistance_widget(name, attr, color)
            self.stat_widgets[attr] = resist_widget
            layout.addWidget(resist_widget)
            
        return frame
        
    def _create_advanced_stats_frame(self) -> QWidget:
        """创建高级统计数据框架"""
        frame = QGroupBox("高级数据")
        frame.setStyleSheet(f"""
            QGroupBox {{
                font-size: 14px;
                font-weight: 600;
                color: {self.theme.get_color('text_primary')};
                border: 2px solid {self.theme.get_color('border_primary')};
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: {self.theme.get_color('text_highlight')};
            }}
        """)
        
        layout = QGridLayout(frame)
        layout.setSpacing(12)
        
        # 高级统计数据
        advanced_stats = [
            ("暴击率", "critical_strike_chance", "%"),
            ("暴击倍率", "critical_strike_multiplier", "%"),
            ("攻击速度", "attack_speed", "次/秒"),
            ("施法速度", "cast_speed", "次/秒"),
            ("格挡率", "block_chance", "%"),
            ("闪避率", "dodge_chance", "%")
        ]
        
        for i, (name, attr, unit) in enumerate(advanced_stats):
            stat_widget = self._create_simple_stat_widget(name, attr, unit)
            self.stat_widgets[attr] = stat_widget
            row = i // 3
            col = i % 3 
            layout.addWidget(stat_widget, row, col)
            
        return frame
        
    def _create_stat_widget(self, name: str, attr: str, color: str, 
                           description: str, is_main: bool = False) -> QWidget:
        """创建统计数据小部件"""
        widget = QFrame()
        widget.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.get_color('background_tertiary')};
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 8px;
                padding: 8px;
            }}
            QFrame:hover {{
                border-color: {color};
            }}
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # 统计名称
        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet(f"""
            color: {self.theme.get_color('text_secondary')};
            font-size: {'12px' if is_main else '10px'};
            font-weight: 500;
        """)
        
        # 统计数值
        value_label = QLabel("0")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        value_label.setStyleSheet(f"""
            color: {color};
            font-size: {'16px' if is_main else '14px'};
            font-weight: 600;
        """)
        
        # 描述标签
        if is_main:
            desc_label = QLabel(description)
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc_label.setStyleSheet(f"""
                color: {self.theme.get_color('text_disabled')};
                font-size: 8px;
            """)
            layout.addWidget(desc_label)
            
        layout.addWidget(name_label)
        layout.addWidget(value_label)
        
        # 存储标签引用以便更新
        widget.name_label = name_label
        widget.value_label = value_label
        widget.setToolTip(f"{name}: {description}")
        
        return widget
        
    def _create_resistance_widget(self, name: str, attr: str, color: str) -> QWidget:
        """创建抗性小部件"""
        widget = QFrame()
        widget.setFixedWidth(100)
        widget.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.get_color('background_tertiary')};
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 8px;
                padding: 8px;
            }}
            QFrame:hover {{
                border-color: {color};
            }}
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # 抗性名称
        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet(f"""
            color: {self.theme.get_color('text_secondary')};
            font-size: 11px;
            font-weight: 500;
        """)
        
        # 抗性进度条
        progress = QProgressBar()
        progress.setFixedHeight(12)
        progress.setMinimum(-60)
        progress.setMaximum(80)
        progress.setValue(0)
        progress.setTextVisible(False)
        progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {self.theme.get_color('background_primary')};
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 6px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 5px;
            }}
        """)
        
        # 抗性数值
        value_label = QLabel("0%")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet(f"""
            color: {color};
            font-size: 12px;
            font-weight: 600;
        """)
        
        layout.addWidget(name_label)
        layout.addWidget(progress)
        layout.addWidget(value_label)
        
        # 存储引用
        widget.progress = progress
        widget.value_label = value_label
        
        return widget
        
    def _create_simple_stat_widget(self, name: str, attr: str, unit: str) -> QWidget:
        """创建简单统计小部件"""
        widget = QFrame()
        widget.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.get_color('background_tertiary')};
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 6px;
                padding: 6px;
            }}
        """)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # 名称标签
        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            color: {self.theme.get_color('text_secondary')};
            font-size: 10px;
        """)
        
        # 数值标签
        value_label = QLabel(f"0{unit}")
        value_label.setStyleSheet(f"""
            color: {self.theme.get_color('text_primary')};
            font-size: 11px;
            font-weight: 600;
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        layout.addWidget(name_label)
        layout.addStretch()
        layout.addWidget(value_label)
        
        # 存储引用
        widget.value_label = value_label
        widget.unit = unit
        
        return widget
        
    def update_stats(self, stats):
        """更新统计数据显示"""
        self.stats = stats
        if not stats:
            return
            
        # 更新主要统计数据
        main_stats_mapping = {
            'total_dps': ('total_dps', lambda x: f"{x:,.0f}"),
            'effective_health_pool': ('effective_health_pool', lambda x: f"{x:,.0f}"),
            'life': ('life', lambda x: f"{x:,.0f}"),
            'energy_shield': ('energy_shield', lambda x: f"{x:,.0f}"),
            'mana': ('mana', lambda x: f"{x:,.0f}"),
            'movement_speed': ('movement_speed', lambda x: f"{x:.0f}%")
        }
        
        for attr, (stat_attr, formatter) in main_stats_mapping.items():
            if attr in self.stat_widgets and hasattr(stats, stat_attr):
                value = getattr(stats, stat_attr, 0)
                self.stat_widgets[attr].value_label.setText(formatter(value))
                
        # 更新抗性
        resistance_mapping = {
            'fire_resistance': 'fire_resistance',
            'cold_resistance': 'cold_resistance', 
            'lightning_resistance': 'lightning_resistance',
            'chaos_resistance': 'chaos_resistance'
        }
        
        for attr, stat_attr in resistance_mapping.items():
            if attr in self.stat_widgets and hasattr(stats, stat_attr):
                value = getattr(stats, stat_attr, 0)
                widget = self.stat_widgets[attr]
                widget.progress.setValue(value)
                widget.value_label.setText(f"{value}%")
                
                # 根据抗性值设置颜色
                if value >= 75:
                    color = self.theme.get_color('success')
                elif value >= 0:
                    color = self.theme.get_color('warning')
                else:
                    color = self.theme.get_color('error')
                    
                widget.value_label.setStyleSheet(f"""
                    color: {color};
                    font-size: 12px;
                    font-weight: 600;
                """)
                
        # 更新高级统计数据
        advanced_stats_mapping = {
            'critical_strike_chance': ('critical_strike_chance', lambda x: f"{x:.1f}"),
            'critical_strike_multiplier': ('critical_strike_multiplier', lambda x: f"{x:.0f}"),
            'attack_speed': ('attack_speed', lambda x: f"{x:.2f}"),
            'cast_speed': ('cast_speed', lambda x: f"{x:.2f}"),
            'block_chance': ('block_chance', lambda x: f"{x:.1f}"),
            'dodge_chance': ('dodge_chance', lambda x: f"{x:.1f}")
        }
        
        for attr, (stat_attr, formatter) in advanced_stats_mapping.items():
            if attr in self.stat_widgets and hasattr(stats, stat_attr):
                value = getattr(stats, stat_attr, 0)
                widget = self.stat_widgets[attr]
                formatted_value = formatter(value)
                widget.value_label.setText(f"{formatted_value}{widget.unit}")


class ClassSelector(PoE2BaseWidget):
    """职业选择器组件 - 可视化职业选择"""
    
    # 信号定义
    class_selected = pyqtSignal(object)  # 发送PoE2CharacterClass对象
    ascendancy_selected = pyqtSignal(object)  # 发送PoE2Ascendancy对象
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_class = None
        self.selected_ascendancy = None
        self.class_buttons = {}
        self.ascendancy_buttons = {}
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI结构"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 标题
        title = QLabel("选择角色职业")
        title.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_highlight')};
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 8px;
            }}
        """)
        
        # 职业选择区域
        class_group = QGroupBox("基础职业")
        class_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 14px;
                font-weight: 600;
                color: {self.theme.get_color('text_primary')};
                border: 2px solid {self.theme.get_color('border_primary')};
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: {self.theme.get_color('text_highlight')};
            }}
        """)
        
        class_layout = QGridLayout(class_group)
        class_layout.setSpacing(8)
        
        # 创建职业按钮
        classes = [
            (PoE2CharacterClass.WITCH, "女巫", "🔮", "元素法术专家"),
            (PoE2CharacterClass.RANGER, "游侠", "🏹", "远程物理专家"),
            (PoE2CharacterClass.WARRIOR, "战士", "⚔️", "近战防御专家"),
            (PoE2CharacterClass.MONK, "武僧", "👊", "格斗敏捷专家"),
            (PoE2CharacterClass.SORCERESS, "女法师", "⚡", "闪电法术专家"),
            (PoE2CharacterClass.MERCENARY, "雇佣兵", "💀", "crossbow专家")
        ]
        
        self.class_button_group = QButtonGroup()
        
        for i, (class_enum, name, icon, description) in enumerate(classes):
            button = self._create_class_button(class_enum, name, icon, description)
            self.class_buttons[class_enum] = button
            self.class_button_group.addButton(button)
            
            row = i // 3
            col = i % 3
            class_layout.addWidget(button, row, col)
            
        # 升华职业选择区域
        self.ascendancy_group = QGroupBox("升华职业")
        self.ascendancy_group.setStyleSheet(class_group.styleSheet())
        self.ascendancy_layout = QGridLayout(self.ascendancy_group)
        self.ascendancy_layout.setSpacing(8)
        
        # 初始时隐藏升华选择
        self.ascendancy_group.setVisible(False)
        
        # 添加到主布局
        layout.addWidget(title)
        layout.addWidget(class_group)
        layout.addWidget(self.ascendancy_group)
        layout.addStretch()
        
    def _create_class_button(self, class_enum: PoE2CharacterClass, name: str, 
                           icon: str, description: str) -> QRadioButton:
        """创建职业选择按钮"""
        button = QRadioButton()
        button.setFixedSize(140, 80)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 自定义绘制
        button.setStyleSheet(f"""
            QRadioButton {{
                background-color: {self.theme.get_color('background_secondary')};
                border: 2px solid {self.theme.get_color('border_primary')};
                border-radius: 8px;
                padding: 8px;
            }}
            QRadioButton:hover {{
                border-color: {self.theme.get_color('poe2_gold')};
                background-color: {self.theme.get_color('background_tertiary')};
            }}
            QRadioButton:checked {{
                border-color: {self.theme.get_color('poe2_gold')};
                background-color: {self.theme.get_color('button_accent_pressed')};
            }}
            QRadioButton::indicator {{
                width: 0px;
                height: 0px;
            }}
        """)
        
        # 创建按钮内容
        button_layout = QVBoxLayout(button)
        button_layout.setContentsMargins(4, 4, 4, 4)
        button_layout.setSpacing(2)
        
        # 图标
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 24px;")
        
        # 名称
        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet(f"""
            color: {self.theme.get_color('text_primary')};
            font-size: 12px;
            font-weight: 600;
        """)
        
        # 描述
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"""
            color: {self.theme.get_color('text_secondary')};
            font-size: 9px;
        """)
        
        button_layout.addWidget(icon_label)
        button_layout.addWidget(name_label)
        button_layout.addWidget(desc_label)
        
        # 连接信号
        button.toggled.connect(lambda checked, cls=class_enum: self._on_class_selected(cls, checked))
        
        return button
        
    def _on_class_selected(self, class_enum: PoE2CharacterClass, checked: bool):
        """处理职业选择"""
        if checked:
            self.selected_class = class_enum
            self.class_selected.emit(class_enum)
            self._update_ascendancy_options(class_enum)
        
    def _update_ascendancy_options(self, class_enum: PoE2CharacterClass):
        """更新升华职业选项"""
        # 清除现有升华按钮
        for button in self.ascendancy_buttons.values():
            button.setParent(None)
        self.ascendancy_buttons.clear()
        
        # 获取可用升华
        from ...models.characters import ASCENDANCY_MAPPING
        available_ascendancies = ASCENDANCY_MAPPING.get(class_enum, [])
        
        if available_ascendancies:
            # 创建新的升华按钮
            self.ascendancy_button_group = QButtonGroup()
            
            for i, ascendancy in enumerate(available_ascendancies):
                button = self._create_ascendancy_button(ascendancy)
                self.ascendancy_buttons[ascendancy] = button
                self.ascendancy_button_group.addButton(button)
                
                row = i // 3
                col = i % 3
                self.ascendancy_layout.addWidget(button, row, col)
            
            self.ascendancy_group.setVisible(True)
        else:
            self.ascendancy_group.setVisible(False)
            
    def _create_ascendancy_button(self, ascendancy: PoE2Ascendancy) -> QRadioButton:
        """创建升华职业按钮"""
        button = QRadioButton(ascendancy.value)
        button.setFixedHeight(40)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        button.setStyleSheet(f"""
            QRadioButton {{
                background-color: {self.theme.get_color('background_secondary')};
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 6px;
                padding: 8px 12px;
                color: {self.theme.get_color('text_primary')};
                font-size: 11px;
                font-weight: 500;
            }}
            QRadioButton:hover {{
                border-color: {self.theme.get_color('poe2_gold')};
                background-color: {self.theme.get_color('background_tertiary')};
            }}
            QRadioButton:checked {{
                border-color: {self.theme.get_color('poe2_gold')};
                background-color: {self.theme.get_color('button_accent')};
                color: {self.theme.get_color('background_primary')};
            }}
            QRadioButton::indicator {{
                width: 0px;
                height: 0px;
            }}
        """)
        
        # 连接信号
        button.toggled.connect(lambda checked, asc=ascendancy: self._on_ascendancy_selected(asc, checked))
        
        return button
        
    def _on_ascendancy_selected(self, ascendancy: PoE2Ascendancy, checked: bool):
        """处理升华职业选择"""
        if checked:
            self.selected_ascendancy = ascendancy
            self.ascendancy_selected.emit(ascendancy)
            
    def get_selection(self) -> Dict[str, Any]:
        """获取当前选择"""
        return {
            'character_class': self.selected_class,
            'ascendancy': self.selected_ascendancy
        }


# 扩展主题类以支持新的颜色方法
def extend_theme():
    """扩展PoE2Theme类，添加组件特定的颜色方法"""
    
    def get_cost_tier_color(self, cost: float) -> str:
        """根据成本获取颜色"""
        if cost <= 1:
            return self.get_color('success')  # 绿色 - 便宜
        elif cost <= 5:
            return self.get_color('poe2_gold')  # 金色 - 中等
        elif cost <= 15:
            return self.get_color('warning')  # 橙色 - 昂贵
        else:
            return self.get_color('error')  # 红色 - 极贵
            
    def get_goal_color(self, goal: PoE2BuildGoal) -> str:
        """根据构筑目标获取颜色"""
        goal_colors = {
            PoE2BuildGoal.LEAGUE_START: self.get_color('success'),
            PoE2BuildGoal.BUDGET_FRIENDLY: self.get_color('poe2_green'), 
            PoE2BuildGoal.CLEAR_SPEED: self.get_color('poe2_blue'),
            PoE2BuildGoal.BOSS_KILLING: self.get_color('poe2_red'),
            PoE2BuildGoal.ENDGAME_CONTENT: self.get_color('poe2_purple')
        }
        return goal_colors.get(goal, self.get_color('text_primary'))
    
    # 动态添加方法到PoE2Theme类
    PoE2Theme.get_cost_tier_color = get_cost_tier_color
    PoE2Theme.get_goal_color = get_goal_color

# 在导入时扩展主题
extend_theme()


if __name__ == "__main__":
    """测试组件"""
    app = QApplication(sys.argv)
    
    # 应用PoE2主题
    theme = PoE2Theme()
    app.setPalette(theme.get_palette())
    app.setStyleSheet(theme.get_stylesheet())
    
    # 创建测试窗口
    window = QWidget()
    window.setWindowTitle("PoE2 专业UI组件测试")
    window.resize(1400, 900)
    window.setStyleSheet(f"""
        QWidget {{
            background-color: {theme.get_color('background_primary')};
        }}
    """)
    
    # 主布局
    main_layout = QHBoxLayout(window)
    main_layout.setSpacing(16)
    main_layout.setContentsMargins(16, 16, 16, 16)
    
    # 左侧区域 - 构筑卡片和职业选择器
    left_widget = QWidget()
    left_layout = QVBoxLayout(left_widget)
    left_layout.setSpacing(16)
    
    # 测试构筑卡片
    try:
        from ...models.build import PoE2Build, PoE2BuildStats, PoE2BuildGoal
        from ...models.characters import PoE2CharacterClass, PoE2Ascendancy
        
        # 创建测试构筑数据
        test_stats = PoE2BuildStats(
            total_dps=450000,
            effective_health_pool=7500,
            fire_resistance=77,
            cold_resistance=75,
            lightning_resistance=78,
            chaos_resistance=-25,
            life=5000,
            energy_shield=2500,
            mana=1200,
            critical_strike_chance=65.0,
            critical_strike_multiplier=350.0,
            attack_speed=1.85,
            cast_speed=2.1,
            movement_speed=125.0,
            block_chance=35.0,
            dodge_chance=15.0
        )
        
        builds_data = [
            ("火焰法师构筑", PoE2CharacterClass.WITCH, PoE2Ascendancy.INFERNALIST, "火球术", 12.5),
            ("游侠弓箭手", PoE2CharacterClass.RANGER, PoE2Ascendancy.DEADEYE, "分裂箭", 8.0),
            ("战士猛击者", PoE2CharacterClass.WARRIOR, PoE2Ascendancy.TITAN, "重击", 15.0)
        ]
        
        # 创建构筑卡片组件
        cards_title = QLabel("构筑卡片展示")
        cards_title.setStyleSheet(f"""
            QLabel {{
                color: {theme.get_color('text_highlight')};
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 8px;
            }}
        """)
        
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(8)
        
        # 添加多个不同的构筑卡片
        for i, (name, char_class, ascendancy, skill, cost) in enumerate(builds_data):
            test_build = PoE2Build(
                name=name,
                character_class=char_class,
                ascendancy=ascendancy,
                level=85 + i*5,
                stats=test_stats,
                estimated_cost=cost,
                currency_type="divine",
                goal=PoE2BuildGoal.ENDGAME_CONTENT,
                main_skill_gem=skill
            )
            
            card = BuildCard(test_build)
            card.clicked.connect(lambda build, b=test_build: print(f"点击了构筑: {b.name}"))
            card.favorited.connect(lambda build, b=test_build: print(f"收藏状态变更: {b.name}"))
            scroll_layout.addWidget(card)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedHeight(300)
        
        # 职业选择器
        class_title = QLabel("职业选择器")
        class_title.setStyleSheet(f"""
            QLabel {{
                color: {theme.get_color('text_highlight')};
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 8px;
            }}
        """)
        
        class_selector = ClassSelector()
        class_selector.class_selected.connect(lambda cls: print(f"选择职业: {cls.value}"))
        class_selector.ascendancy_selected.connect(lambda asc: print(f"选择升华: {asc.value}"))
        
        left_layout.addWidget(cards_title)
        left_layout.addWidget(scroll_area)
        left_layout.addWidget(class_title)
        left_layout.addWidget(class_selector)
        left_layout.addStretch()
        
    except ImportError as e:
        error_label = QLabel(f"模型导入错误: {str(e)}")
        error_label.setStyleSheet(f"color: {theme.get_color('error')}; font-size: 14px;")
        left_layout.addWidget(error_label)
    
    # 右侧区域 - 装备展示和数据仪表板
    right_widget = QWidget()
    right_layout = QVBoxLayout(right_widget)
    right_layout.setSpacing(16)
    
    # 装备展示组件
    equipment_title = QLabel("装备展示组件")
    equipment_title.setStyleSheet(f"""
        QLabel {{
            color: {theme.get_color('text_highlight')};
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
        }}
    """)
    
    equipment_display = EquipmentDisplay()
    equipment_display.equipment_selected.connect(
        lambda slot, item: print(f"点击装备槽位: {slot}, 当前装备: {item}")
    )
    
    # 添加一些测试装备
    test_equipment = [
        ("helmet", {"name": "龙鳞头盔", "quality": "rare", "defense": 250, "life": 75}),
        ("chest", {"name": "圣殿护甲", "quality": "unique", "defense": 800, "life": 120}),
        ("main_hand", {"name": "烈焰之剑", "quality": "magic", "defense": 0, "damage": 450}),
    ]
    
    for slot, item_data in test_equipment:
        equipment_display.equip_item(slot, item_data)
    
    equipment_display.setFixedHeight(350)
    
    # 数据仪表板组件
    stats_title = QLabel("数据仪表板")
    stats_title.setStyleSheet(f"""
        QLabel {{
            color: {theme.get_color('text_highlight')};
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
        }}
    """)
    
    stats_display = StatsDisplay()
    
    # 更新统计数据（如果有的话）
    try:
        if 'test_stats' in locals():
            stats_display.update_stats(test_stats)
    except:
        pass
    
    right_layout.addWidget(equipment_title)
    right_layout.addWidget(equipment_display)
    right_layout.addWidget(stats_title)
    right_layout.addWidget(stats_display)
    right_layout.addStretch()
    
    # 添加到主布局
    main_layout.addWidget(left_widget, 1)
    main_layout.addWidget(right_widget, 1)
    
    # 显示窗口
    window.show()
    
    # 显示使用说明
    print("=== PoE2 专业UI组件测试程序 ===")
    print("左侧:")
    print("- 构筑卡片展示: 显示不同的构筑信息，支持收藏和点击")
    print("- 职业选择器: 可视化的职业和升华选择界面")
    print("右侧:")
    print("- 装备展示: 装备槽位展示，支持装备管理")
    print("- 数据仪表板: 构筑统计数据的可视化展示")
    print("=== 功能特性 ===")
    print("- Path of Exile 2风格的暗色主题")
    print("- 金色高亮效果和悬停动画")
    print("- 响应式布局和专业数据展示")
    print("- 完整的信号和槽机制支持")
    print("===========================")
    
    sys.exit(app.exec())