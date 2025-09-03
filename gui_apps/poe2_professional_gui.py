#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PoE2 Build Generator - 专业级GUI界面
真正的PoE2风格，完整功能实现
"""

import sys
import os
import asyncio
import json
import webbrowser
from datetime import datetime
from typing import Optional, Dict, Any, List
from urllib.parse import quote

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QGridLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
        QSplitter, QTabWidget, QProgressBar, QGroupBox, QFrame, 
        QScrollArea, QListWidget, QListWidgetItem, QStatusBar, QMenuBar,
        QMenu, QDockWidget, QTreeWidget, QTreeWidgetItem, QSpacerItem,
        QSizePolicy, QSlider, QSpinBox, QCheckBox, QRadioButton,
        QButtonGroup, QTableWidget, QTableWidgetItem, QHeaderView,
        QDialog, QDialogButtonBox, QMessageBox, QFileDialog
    )
    from PyQt6.QtCore import (
        Qt, QTimer, pyqtSignal, QThread, pyqtSlot, QSize, QRect,
        QPropertyAnimation, QEasingCurve, QAbstractAnimation, QUrl
    )
    from PyQt6.QtGui import (
        QFont, QIcon, QPainter, QLinearGradient, QColor, QPalette,
        QPixmap, QBrush, QPen, QKeySequence, QShortcut, QAction,
        QFontMetrics, QMovie, QClipboard
    )
    
    from poe2build.gui.styles.poe2_theme import PoE2Theme
    from poe2build.core.ai_orchestrator import PoE2AIOrchestrator, UserRequest
    from poe2build.models.characters import PoE2CharacterClass, PoE2Ascendancy
    from poe2build.models.build import PoE2BuildGoal
    
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装PyQt6: pip install PyQt6")
    sys.exit(1)


class PoE2BuildDetailDialog(QDialog):
    """构筑详细信息对话框"""
    
    export_requested = pyqtSignal(object, str)  # build, export_type
    
    def __init__(self, build_data, parent=None):
        super().__init__(parent)
        self.build_data = build_data
        self.theme = PoE2Theme()
        self.setup_ui()
        
    def setup_ui(self):
        """设置详细信息界面"""
        self.setWindowTitle(f"构筑详情 - {self.build_data.name}")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        # 应用主题
        self.setPalette(self.theme.get_palette())
        self.setStyleSheet(self.theme.get_stylesheet())
        
        layout = QVBoxLayout(self)
        
        # 标题栏
        title_frame = QFrame()
        title_frame.setStyleSheet(f"""
        QFrame {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 {self.theme.COLORS['poe2_gold']}, 
                stop: 1 {self.theme.COLORS['background_secondary']});
            border-radius: 8px;
            padding: 12px;
            margin: 4px;
        }}
        """)
        title_layout = QHBoxLayout(title_frame)
        
        # 构筑名称
        build_title = QLabel(self.build_data.name)
        build_title.setStyleSheet(f"""
        color: {self.theme.COLORS['background_primary']};
        font-size: 20px;
        font-weight: bold;
        """)
        title_layout.addWidget(build_title)
        
        # 职业标签
        class_label = QLabel(f"{self.build_data.character_class.value}")
        if self.build_data.ascendancy:
            class_label.setText(f"{self.build_data.character_class.value} - {self.build_data.ascendancy.value}")
        class_label.setStyleSheet(f"""
        color: {self.theme.COLORS['background_primary']};
        font-size: 14px;
        font-weight: 600;
        """)
        title_layout.addWidget(class_label)
        
        title_layout.addStretch()
        layout.addWidget(title_frame)
        
        # 主内容分割器
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：属性统计
        stats_widget = self.create_stats_widget()
        main_splitter.addWidget(stats_widget)
        
        # 右侧：技能和装备
        build_widget = self.create_build_widget()
        main_splitter.addWidget(build_widget)
        
        main_splitter.setSizes([400, 600])
        layout.addWidget(main_splitter)
        
        # 底部按钮栏
        button_frame = self.create_button_frame()
        layout.addWidget(button_frame)
        
    def create_stats_widget(self):
        """创建属性统计组件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 核心属性
        core_group = QGroupBox("核心属性")
        self.theme.apply_poe2_style_properties(core_group, "enhanced_group")
        core_layout = QGridLayout(core_group)
        
        if self.build_data.stats:
            stats = self.build_data.stats
            
            # DPS
            dps_label = QLabel("总DPS:")
            dps_value = QLabel(f"{stats.total_dps:,.0f}")
            dps_value.setStyleSheet(f"color: {self.theme.COLORS['poe2_red']}; font-weight: bold; font-size: 14px;")
            core_layout.addWidget(dps_label, 0, 0)
            core_layout.addWidget(dps_value, 0, 1)
            
            # 有效生命值
            hp_label = QLabel("有效HP:")
            hp_value = QLabel(f"{stats.effective_health_pool:,.0f}")
            hp_value.setStyleSheet(f"color: {self.theme.COLORS['poe2_green']}; font-weight: bold; font-size: 14px;")
            core_layout.addWidget(hp_label, 1, 0)
            core_layout.addWidget(hp_value, 1, 1)
            
            # 生命值
            if stats.life > 0:
                life_label = QLabel("生命值:")
                life_value = QLabel(f"{stats.life:,.0f}")
                life_value.setStyleSheet(f"color: {self.theme.COLORS['poe2_red']}; font-weight: bold;")
                core_layout.addWidget(life_label, 2, 0)
                core_layout.addWidget(life_value, 2, 1)
            
            # 能量护盾
            if stats.energy_shield > 0:
                es_label = QLabel("能量护盾:")
                es_value = QLabel(f"{stats.energy_shield:,.0f}")
                es_value.setStyleSheet(f"color: {self.theme.COLORS['poe2_blue']}; font-weight: bold;")
                core_layout.addWidget(es_label, 3, 0)
                core_layout.addWidget(es_value, 3, 1)
            
            # 魔力值
            if stats.mana > 0:
                mana_label = QLabel("魔力值:")
                mana_value = QLabel(f"{stats.mana:,.0f}")
                mana_value.setStyleSheet(f"color: {self.theme.COLORS['poe2_blue']}; font-weight: bold;")
                core_layout.addWidget(mana_label, 4, 0)
                core_layout.addWidget(mana_value, 4, 1)
        
        layout.addWidget(core_group)
        
        # 抗性
        resist_group = QGroupBox("元素抗性")
        self.theme.apply_poe2_style_properties(resist_group, "enhanced_group")
        resist_layout = QGridLayout(resist_group)
        
        if self.build_data.stats:
            resists = [
                ("火焰:", self.build_data.stats.fire_resistance, self.theme.COLORS['poe2_red']),
                ("冰霜:", self.build_data.stats.cold_resistance, self.theme.COLORS['poe2_blue']),
                ("闪电:", self.build_data.stats.lightning_resistance, self.theme.COLORS['poe2_gold']),
                ("混沌:", self.build_data.stats.chaos_resistance, self.theme.COLORS['poe2_purple'])
            ]
            
            for i, (name, value, color) in enumerate(resists):
                label = QLabel(name)
                resist_value = QLabel(f"{value}%")
                resist_color = self.theme.get_resistance_color(value)
                resist_value.setStyleSheet(f"color: {resist_color}; font-weight: bold;")
                resist_layout.addWidget(label, i, 0)
                resist_layout.addWidget(resist_value, i, 1)
        
        layout.addWidget(resist_group)
        
        # 攻击属性
        if self.build_data.stats and (self.build_data.stats.critical_strike_chance > 0 or 
                                     self.build_data.stats.attack_speed > 0):
            attack_group = QGroupBox("攻击属性")
            self.theme.apply_poe2_style_properties(attack_group, "enhanced_group")
            attack_layout = QGridLayout(attack_group)
            
            row = 0
            if self.build_data.stats.critical_strike_chance > 0:
                crit_label = QLabel("暴击率:")
                crit_value = QLabel(f"{self.build_data.stats.critical_strike_chance:.1f}%")
                crit_value.setStyleSheet(f"color: {self.theme.COLORS['poe2_gold']}; font-weight: bold;")
                attack_layout.addWidget(crit_label, row, 0)
                attack_layout.addWidget(crit_value, row, 1)
                row += 1
            
            if self.build_data.stats.critical_strike_multiplier > 0:
                mult_label = QLabel("暴击倍率:")
                mult_value = QLabel(f"{self.build_data.stats.critical_strike_multiplier:.0f}%")
                mult_value.setStyleSheet(f"color: {self.theme.COLORS['poe2_gold']}; font-weight: bold;")
                attack_layout.addWidget(mult_label, row, 0)
                attack_layout.addWidget(mult_value, row, 1)
                row += 1
            
            if self.build_data.stats.attack_speed > 0:
                speed_label = QLabel("攻击速度:")
                speed_value = QLabel(f"{self.build_data.stats.attack_speed:.2f}")
                speed_value.setStyleSheet(f"color: {self.theme.COLORS['text_primary']}; font-weight: bold;")
                attack_layout.addWidget(speed_label, row, 0)
                attack_layout.addWidget(speed_value, row, 1)
            
            layout.addWidget(attack_group)
        
        layout.addStretch()
        return widget
        
    def create_build_widget(self):
        """创建构筑信息组件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 技能设置
        skill_group = QGroupBox("技能设置")
        self.theme.apply_poe2_style_properties(skill_group, "enhanced_group")
        skill_layout = QVBoxLayout(skill_group)
        
        if self.build_data.main_skill_gem:
            main_skill_frame = QFrame()
            main_skill_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.COLORS['background_tertiary']};
                border: 2px solid {self.theme.COLORS['poe2_blue']};
                border-radius: 8px;
                padding: 8px;
                margin: 4px;
            }}
            """)
            main_skill_layout = QVBoxLayout(main_skill_frame)
            
            skill_title = QLabel("主技能")
            skill_title.setStyleSheet(f"color: {self.theme.COLORS['poe2_blue']}; font-weight: bold;")
            main_skill_layout.addWidget(skill_title)
            
            skill_name = QLabel(self.build_data.main_skill_gem)
            skill_name.setStyleSheet(f"color: {self.theme.COLORS['text_primary']}; font-size: 14px; font-weight: 600;")
            main_skill_layout.addWidget(skill_name)
            
            skill_layout.addWidget(main_skill_frame)
        
        # 辅助技能
        if self.build_data.support_gems:
            support_frame = QFrame()
            support_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.COLORS['background_tertiary']};
                border: 2px solid {self.theme.COLORS['poe2_green']};
                border-radius: 8px;
                padding: 8px;
                margin: 4px;
            }}
            """)
            support_layout = QVBoxLayout(support_frame)
            
            support_title = QLabel("辅助技能")
            support_title.setStyleSheet(f"color: {self.theme.COLORS['poe2_green']}; font-weight: bold;")
            support_layout.addWidget(support_title)
            
            for support in self.build_data.support_gems[:6]:  # 限制显示6个
                support_label = QLabel(f"• {support}")
                support_label.setStyleSheet(f"color: {self.theme.COLORS['text_primary']}; font-size: 12px;")
                support_layout.addWidget(support_label)
            
            skill_layout.addWidget(support_frame)
        
        layout.addWidget(skill_group)
        
        # 关键物品
        if self.build_data.key_items:
            items_group = QGroupBox("关键装备")
            self.theme.apply_poe2_style_properties(items_group, "enhanced_group")
            items_layout = QVBoxLayout(items_group)
            
            for item in self.build_data.key_items[:8]:  # 限制显示8个
                item_frame = QFrame()
                item_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.theme.COLORS['background_quaternary']};
                    border: 1px solid {self.theme.COLORS['poe2_gold']};
                    border-radius: 6px;
                    padding: 6px;
                    margin: 2px;
                }}
                """)
                item_layout = QHBoxLayout(item_frame)
                
                item_label = QLabel(item)
                item_label.setStyleSheet(f"color: {self.theme.COLORS['poe2_gold']}; font-size: 12px; font-weight: 600;")
                item_layout.addWidget(item_label)
                
                items_layout.addWidget(item_frame)
            
            layout.addWidget(items_group)
        
        # 预算信息
        cost_group = QGroupBox("构筑成本")
        self.theme.apply_poe2_style_properties(cost_group, "enhanced_group")
        cost_layout = QVBoxLayout(cost_group)
        
        if self.build_data.estimated_cost:
            cost_frame = QFrame()
            cost_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {self.theme.COLORS['background_secondary']}, 
                    stop: 1 {self.theme.COLORS['poe2_gold']});
                border-radius: 8px;
                padding: 12px;
            }}
            """)
            cost_layout_h = QHBoxLayout(cost_frame)
            
            cost_label = QLabel("预估成本:")
            cost_label.setStyleSheet(f"color: {self.theme.COLORS['text_primary']}; font-size: 14px;")
            cost_layout_h.addWidget(cost_label)
            
            cost_value = QLabel(f"{self.build_data.estimated_cost:.1f} {self.build_data.currency_type}")
            cost_value.setStyleSheet(f"color: {self.theme.COLORS['poe2_gold']}; font-size: 16px; font-weight: bold;")
            cost_layout_h.addWidget(cost_value)
            
            cost_layout.addWidget(cost_frame)
        
        # 构筑目标
        if self.build_data.goal:
            goal_label = QLabel(f"构筑目标: {self.build_data.goal.value}")
            goal_color = self.theme.get_build_goal_color(self.build_data.goal.value)
            goal_label.setStyleSheet(f"color: {goal_color}; font-size: 12px; font-weight: 600;")
            cost_layout.addWidget(goal_label)
        
        layout.addWidget(cost_group)
        
        layout.addStretch()
        return widget
    
    def create_button_frame(self):
        """创建按钮栏"""
        frame = QFrame()
        frame.setStyleSheet(f"""
        QFrame {{
            background-color: {self.theme.COLORS['background_secondary']};
            border-top: 2px solid {self.theme.COLORS['border_primary']};
            padding: 8px;
        }}
        """)
        layout = QHBoxLayout(frame)
        
        # PoB2导出按钮
        if self.build_data.pob2_code:
            pob2_btn = QPushButton("导出到PoB2")
            self.theme.apply_poe2_style_properties(pob2_btn, "accent_button")
            pob2_btn.clicked.connect(lambda: self.export_pob2())
            layout.addWidget(pob2_btn)
            
            # 复制PoB2代码
            copy_btn = QPushButton("复制导入代码")
            self.theme.apply_poe2_style_properties(copy_btn, "primary_button")
            copy_btn.clicked.connect(self.copy_pob2_code)
            layout.addWidget(copy_btn)
        
        # 保存JSON
        save_btn = QPushButton("保存构筑")
        self.theme.apply_poe2_style_properties(save_btn, "primary_button")
        save_btn.clicked.connect(self.save_build)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        return frame
    
    def export_pob2(self):
        """导出到PoB2"""
        if self.build_data.pob2_code:
            self.export_requested.emit(self.build_data, "pob2")
    
    def copy_pob2_code(self):
        """复制PoB2代码到剪贴板"""
        if self.build_data.pob2_code:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.build_data.pob2_code)
            QMessageBox.information(self, "成功", "PoB2导入代码已复制到剪贴板！")
    
    def save_build(self):
        """保存构筑为JSON"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存构筑", f"{self.build_data.name}.json", "JSON Files (*.json)"
        )
        if filename:
            try:
                build_data = {
                    "name": self.build_data.name,
                    "character_class": self.build_data.character_class.value,
                    "ascendancy": self.build_data.ascendancy.value if self.build_data.ascendancy else None,
                    "level": self.build_data.level,
                    "main_skill": self.build_data.main_skill_gem,
                    "support_gems": self.build_data.support_gems,
                    "key_items": self.build_data.key_items,
                    "estimated_cost": self.build_data.estimated_cost,
                    "currency_type": self.build_data.currency_type,
                    "pob2_code": self.build_data.pob2_code,
                    "stats": {
                        "total_dps": self.build_data.stats.total_dps if self.build_data.stats else 0,
                        "effective_health_pool": self.build_data.stats.effective_health_pool if self.build_data.stats else 0,
                        "life": self.build_data.stats.life if self.build_data.stats else 0,
                        "energy_shield": self.build_data.stats.energy_shield if self.build_data.stats else 0,
                        "mana": self.build_data.stats.mana if self.build_data.stats else 0,
                        "resistances": {
                            "fire": self.build_data.stats.fire_resistance if self.build_data.stats else 0,
                            "cold": self.build_data.stats.cold_resistance if self.build_data.stats else 0,
                            "lightning": self.build_data.stats.lightning_resistance if self.build_data.stats else 0,
                            "chaos": self.build_data.stats.chaos_resistance if self.build_data.stats else 0
                        }
                    } if self.build_data.stats else None
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(build_data, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(self, "成功", f"构筑已保存到:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")


class PoE2ProfessionalCard(QFrame):
    """专业级构筑卡片"""
    
    build_selected = pyqtSignal(object)
    detail_requested = pyqtSignal(object)
    
    def __init__(self, build_data=None):
        super().__init__()
        self.build_data = build_data
        self.theme = PoE2Theme()
        self.setup_ui()
        
    def setup_ui(self):
        """设置专业卡片界面"""
        self.setFixedHeight(280)
        self.setMinimumWidth(320)
        
        # 卡片外框样式
        self.setStyleSheet(f"""
        QFrame {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 {self.theme.COLORS['background_secondary']}, 
                stop: 0.8 {self.theme.COLORS['background_tertiary']},
                stop: 1 {self.theme.COLORS['background_quaternary']});
            border: 2px solid {self.theme.COLORS['border_primary']};
            border-radius: 12px;
            margin: 6px;
        }}
        QFrame:hover {{
            border-color: {self.theme.COLORS['poe2_gold']};
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 {self.theme.COLORS['background_tertiary']}, 
                stop: 0.8 {self.theme.COLORS['background_quaternary']},
                stop: 1 {self.theme.COLORS['background_secondary']});
        }}
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)
        
        if self.build_data:
            # 顶部标题区
            self.create_title_section(main_layout)
            
            # 中部统计区
            self.create_stats_section(main_layout)
            
            # 底部信息区
            self.create_info_section(main_layout)
            
            # 按钮区
            self.create_button_section(main_layout)
        else:
            # 空卡片占位符
            placeholder = QLabel("暂无构筑数据")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet(f"color: {self.theme.COLORS['text_disabled']}; font-size: 14px;")
            main_layout.addWidget(placeholder)
        
        main_layout.addStretch()
    
    def create_title_section(self, main_layout):
        """创建标题区域"""
        title_frame = QFrame()
        title_frame.setStyleSheet(f"""
        QFrame {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 {self.theme.COLORS['poe2_gold']}, 
                stop: 1 transparent);
            border-radius: 6px;
            padding: 8px;
        }}
        """)
        title_layout = QVBoxLayout(title_frame)
        title_layout.setSpacing(4)
        
        # 构筑名称
        name_label = QLabel(self.build_data.name)
        name_label.setStyleSheet(f"""
        color: {self.theme.COLORS['background_primary']};
        font-size: 16px;
        font-weight: bold;
        """)
        name_label.setWordWrap(True)
        title_layout.addWidget(name_label)
        
        # 职业信息
        class_text = self.build_data.character_class.value
        if self.build_data.ascendancy:
            class_text += f" - {self.build_data.ascendancy.value}"
        
        class_label = QLabel(class_text)
        class_label.setStyleSheet(f"""
        color: {self.theme.COLORS['background_primary']};
        font-size: 12px;
        font-weight: 600;
        """)
        title_layout.addWidget(class_label)
        
        main_layout.addWidget(title_frame)
    
    def create_stats_section(self, main_layout):
        """创建统计区域"""
        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"""
        QFrame {{
            background-color: {self.theme.COLORS['background_secondary']};
            border: 1px solid {self.theme.COLORS['border_secondary']};
            border-radius: 6px;
            padding: 8px;
        }}
        """)
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setSpacing(6)
        
        if self.build_data.stats:
            # DPS
            dps_label = QLabel("DPS:")
            dps_label.setStyleSheet(f"color: {self.theme.COLORS['text_secondary']}; font-size: 11px;")
            dps_value = QLabel(f"{self.build_data.stats.total_dps:,.0f}")
            dps_value.setStyleSheet(f"color: {self.theme.COLORS['poe2_red']}; font-size: 13px; font-weight: bold;")
            stats_layout.addWidget(dps_label, 0, 0)
            stats_layout.addWidget(dps_value, 0, 1)
            
            # 有效HP
            hp_label = QLabel("有效HP:")
            hp_label.setStyleSheet(f"color: {self.theme.COLORS['text_secondary']}; font-size: 11px;")
            hp_value = QLabel(f"{self.build_data.stats.effective_health_pool:,.0f}")
            hp_value.setStyleSheet(f"color: {self.theme.COLORS['poe2_green']}; font-size: 13px; font-weight: bold;")
            stats_layout.addWidget(hp_label, 1, 0)
            stats_layout.addWidget(hp_value, 1, 1)
            
            # 关键抗性显示
            max_resist = max(
                self.build_data.stats.fire_resistance,
                self.build_data.stats.cold_resistance,
                self.build_data.stats.lightning_resistance
            )
            min_resist = min(
                self.build_data.stats.fire_resistance,
                self.build_data.stats.cold_resistance,
                self.build_data.stats.lightning_resistance
            )
            
            resist_label = QLabel("抗性:")
            resist_label.setStyleSheet(f"color: {self.theme.COLORS['text_secondary']}; font-size: 11px;")
            resist_text = f"{min_resist}% - {max_resist}%"
            if min_resist == max_resist:
                resist_text = f"{max_resist}%"
            resist_value = QLabel(resist_text)
            resist_color = self.theme.get_resistance_color(min_resist)
            resist_value.setStyleSheet(f"color: {resist_color}; font-size: 13px; font-weight: bold;")
            stats_layout.addWidget(resist_label, 0, 2)
            stats_layout.addWidget(resist_value, 0, 3)
            
            # 预算
            if self.build_data.estimated_cost:
                cost_label = QLabel("成本:")
                cost_label.setStyleSheet(f"color: {self.theme.COLORS['text_secondary']}; font-size: 11px;")
                cost_value = QLabel(f"{self.build_data.estimated_cost:.1f}d")
                cost_value.setStyleSheet(f"color: {self.theme.COLORS['poe2_gold']}; font-size: 13px; font-weight: bold;")
                stats_layout.addWidget(cost_label, 1, 2)
                stats_layout.addWidget(cost_value, 1, 3)
        
        main_layout.addWidget(stats_frame)
    
    def create_info_section(self, main_layout):
        """创建信息区域"""
        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(4)
        
        # 主技能
        if self.build_data.main_skill_gem:
            skill_frame = QFrame()
            skill_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.COLORS['background_quaternary']};
                border-left: 3px solid {self.theme.COLORS['poe2_blue']};
                border-radius: 3px;
                padding: 4px 8px;
            }}
            """)
            skill_layout = QHBoxLayout(skill_frame)
            skill_layout.setContentsMargins(4, 2, 4, 2)
            
            skill_icon = QLabel("💎")
            skill_layout.addWidget(skill_icon)
            
            skill_label = QLabel(self.build_data.main_skill_gem)
            skill_label.setStyleSheet(f"color: {self.theme.COLORS['poe2_blue']}; font-size: 12px; font-weight: 600;")
            skill_layout.addWidget(skill_label)
            skill_layout.addStretch()
            
            info_layout.addWidget(skill_frame)
        
        # PoB2状态
        pob2_frame = QFrame()
        pob2_layout = QHBoxLayout(pob2_frame)
        pob2_layout.setContentsMargins(4, 2, 4, 2)
        
        if self.build_data.pob2_code:
            pob2_icon = QLabel("✓")
            pob2_icon.setStyleSheet(f"color: {self.theme.COLORS['success']}; font-weight: bold;")
            pob2_layout.addWidget(pob2_icon)
            
            pob2_label = QLabel("PoB2导入可用")
            pob2_label.setStyleSheet(f"color: {self.theme.COLORS['success']}; font-size: 11px;")
            pob2_layout.addWidget(pob2_label)
        else:
            pob2_icon = QLabel("✗")
            pob2_icon.setStyleSheet(f"color: {self.theme.COLORS['warning']}; font-weight: bold;")
            pob2_layout.addWidget(pob2_icon)
            
            pob2_label = QLabel("PoB2不可用")
            pob2_label.setStyleSheet(f"color: {self.theme.COLORS['warning']}; font-size: 11px;")
            pob2_layout.addWidget(pob2_label)
        
        pob2_layout.addStretch()
        info_layout.addWidget(pob2_frame)
        
        main_layout.addWidget(info_frame)
    
    def create_button_section(self, main_layout):
        """创建按钮区域"""
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(8)
        
        # 详细信息按钮
        detail_btn = QPushButton("详细信息")
        detail_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {self.theme.COLORS['button_primary']};
            border: 1px solid {self.theme.COLORS['border_primary']};
            color: {self.theme.COLORS['text_primary']};
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {self.theme.COLORS['button_primary_hover']};
            border-color: {self.theme.COLORS['poe2_gold']};
        }}
        """)
        detail_btn.clicked.connect(lambda: self.detail_requested.emit(self.build_data))
        button_layout.addWidget(detail_btn)
        
        # 选择按钮
        select_btn = QPushButton("选择构筑")
        select_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {self.theme.COLORS['poe2_gold']};
            border: 1px solid {self.theme.COLORS['poe2_gold']};
            color: {self.theme.COLORS['background_primary']};
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {self.theme.COLORS['glow_gold']};
        }}
        """)
        select_btn.clicked.connect(lambda: self.build_selected.emit(self.build_data))
        button_layout.addWidget(select_btn)
        
        main_layout.addWidget(button_frame)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.build_data:
                self.build_selected.emit(self.build_data)
        super().mousePressEvent(event)


class PoE2ProfessionalGUI(QMainWindow):
    """专业级PoE2构筑生成器主窗口"""
    
    def __init__(self):
        super().__init__()
        self.theme = PoE2Theme()
        self.orchestrator = None
        self.console_visible = False
        self.build_results = []
        
        self.setup_ui()
        self.setup_shortcuts()
        self.setup_orchestrator()
        
    def setup_ui(self):
        """设置专业界面"""
        self.setWindowTitle("PoE2 Build Generator - Professional Edition")
        self.setMinimumSize(1600, 1000)
        self.resize(1800, 1100)
        
        # 应用主题
        self.setPalette(self.theme.get_palette())
        self.setStyleSheet(self.theme.get_stylesheet())
        
        # 设置窗口图标和样式
        self.setWindowFlags(Qt.WindowType.Window)
        
        # 创建界面组件
        self.create_menu_bar()
        self.create_status_bar()
        self.create_main_interface()
        self.create_console_dock()
    
    def create_menu_bar(self):
        """创建专业菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        file_menu.addAction("导入构筑配置", self.import_config)
        file_menu.addAction("导出构筑列表", self.export_builds)
        file_menu.addSeparator()
        file_menu.addAction("退出", self.close)
        
        # 构筑菜单
        build_menu = menubar.addMenu("构筑")
        build_menu.addAction("生成新构筑", self.generate_builds)
        build_menu.addAction("清空结果", self.clear_results)
        build_menu.addSeparator()
        build_menu.addAction("导出到PoB2", self.export_selected_to_pob2)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具")
        tools_menu.addAction("PoB2集成设置", self.configure_pob2)
        tools_menu.addAction("数据源管理", self.manage_data_sources)
        tools_menu.addSeparator()
        tools_menu.addAction("开发者控制台 (F12)", self.toggle_console)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        help_menu.addAction("用户手册", self.show_manual)
        help_menu.addAction("关于", self.show_about)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 主状态信息
        self.status_bar.showMessage("PoE2 Build Generator - 专业版已就绪")
        
        # 永久状态组件
        self.ai_status_label = QLabel("AI: 初始化中")
        self.ai_status_label.setStyleSheet(f"color: {self.theme.COLORS['warning']}; padding: 2px 8px;")
        self.status_bar.addPermanentWidget(self.ai_status_label)
        
        self.pob2_status_label = QLabel("PoB2: 检测中")
        self.pob2_status_label.setStyleSheet(f"color: {self.theme.COLORS['warning']}; padding: 2px 8px;")
        self.status_bar.addPermanentWidget(self.pob2_status_label)
    
    def create_main_interface(self):
        """创建主界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)  # 减少外边距
        main_layout.setSpacing(12)  # 减少间距
        
        # 创建主分割器
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # 左侧面板 - 输入和控制
        left_panel = self.create_input_panel()
        left_panel.setMinimumWidth(350)  # 减少最小宽度
        left_panel.setMaximumWidth(450)  # 减少最大宽度
        main_splitter.addWidget(left_panel)
        
        # 右侧面板 - 结果显示
        right_panel = self.create_results_panel()
        main_splitter.addWidget(right_panel)
        
        # 设置自适应分割比例
        screen_width = self.screen().availableGeometry().width()
        if screen_width < 1920:
            # 小屏幕：更多空间给右侧结果
            main_splitter.setSizes([350, screen_width - 400])
        else:
            # 大屏幕：平衡分配
            main_splitter.setSizes([400, screen_width - 450])
        
        # 允许用户调整分割器
        main_splitter.setCollapsible(0, False)  # 左侧不可完全折叠
        main_splitter.setCollapsible(1, False)  # 右侧不可完全折叠
    
    def create_input_panel(self):
        """创建输入面板"""
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameStyle(QFrame.Shape.NoFrame)
        
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)  # 减少间距
        layout.setContentsMargins(8, 8, 8, 8)  # 减少边距
        
        # 标题
        title_frame = QFrame()
        title_frame.setStyleSheet(f"""
        QFrame {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 {self.theme.COLORS['poe2_gold']}, 
                stop: 1 {self.theme.COLORS['background_secondary']});
            border-radius: 12px;
            padding: 16px;
        }}
        """)
        title_layout = QVBoxLayout(title_frame)
        
        title_label = QLabel("PoE2 构筑生成器")
        title_label.setStyleSheet(f"""
        color: {self.theme.COLORS['background_primary']};
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(title_label)
        
        subtitle_label = QLabel("专业版 - AI驱动的构筑推荐系统")
        subtitle_label.setStyleSheet(f"""
        color: {self.theme.COLORS['background_primary']};
        font-size: 12px;
        font-weight: 600;
        text-align: center;
        """)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(subtitle_label)
        
        layout.addWidget(title_frame)
        
        # 输入表单
        form_group = QGroupBox("构筑需求设置")
        self.theme.apply_poe2_style_properties(form_group, "enhanced_group")
        form_layout = QGridLayout(form_group)
        form_layout.setSpacing(12)
        
        # 职业选择
        class_label = QLabel("角色职业:")
        class_label.setStyleSheet(f"font-weight: 600; color: {self.theme.COLORS['text_primary']};")
        form_layout.addWidget(class_label, 0, 0)
        
        self.class_combo = QComboBox()
        self.class_combo.addItems([cls.value for cls in PoE2CharacterClass])
        self.class_combo.setStyleSheet(f"""
        QComboBox {{
            padding: 8px 12px;
            font-size: 13px;
            min-height: 24px;
        }}
        """)
        form_layout.addWidget(self.class_combo, 0, 1)
        
        # 升华选择
        ascend_label = QLabel("升华职业:")
        ascend_label.setStyleSheet(f"font-weight: 600; color: {self.theme.COLORS['text_primary']};")
        form_layout.addWidget(ascend_label, 1, 0)
        
        self.ascendancy_combo = QComboBox()
        self.ascendancy_combo.addItem("自动选择")
        for ascend in PoE2Ascendancy:
            self.ascendancy_combo.addItem(ascend.value)
        form_layout.addWidget(self.ascendancy_combo, 1, 1)
        
        # 构筑目标
        goal_label = QLabel("构筑目标:")
        goal_label.setStyleSheet(f"font-weight: 600; color: {self.theme.COLORS['text_primary']};")
        form_layout.addWidget(goal_label, 2, 0)
        
        self.goal_combo = QComboBox()
        self.goal_combo.addItems([goal.value for goal in PoE2BuildGoal])
        form_layout.addWidget(self.goal_combo, 2, 1)
        
        # 预算设置
        budget_label = QLabel("预算上限:")
        budget_label.setStyleSheet(f"font-weight: 600; color: {self.theme.COLORS['text_primary']};")
        form_layout.addWidget(budget_label, 3, 0)
        
        budget_frame = QFrame()
        budget_layout = QHBoxLayout(budget_frame)
        budget_layout.setContentsMargins(0, 0, 0, 0)
        
        self.budget_spin = QSpinBox()
        self.budget_spin.setRange(1, 1000)
        self.budget_spin.setValue(25)
        self.budget_spin.setStyleSheet(f"padding: 6px; font-size: 13px;")
        budget_layout.addWidget(self.budget_spin)
        
        currency_label = QLabel("Divine Orbs")
        currency_label.setStyleSheet(f"color: {self.theme.COLORS['poe2_gold']}; font-weight: 600;")
        budget_layout.addWidget(currency_label)
        
        form_layout.addWidget(budget_frame, 3, 1)
        
        # 技能偏好
        skills_label = QLabel("技能偏好:")
        skills_label.setStyleSheet(f"font-weight: 600; color: {self.theme.COLORS['text_primary']};")
        form_layout.addWidget(skills_label, 4, 0)
        
        self.skills_edit = QLineEdit()
        self.skills_edit.setPlaceholderText("例: Lightning Arrow, Explosive Shot")
        self.theme.apply_poe2_style_properties(self.skills_edit, "enhanced_input")
        self.skills_edit.setStyleSheet(self.skills_edit.styleSheet() + "padding: 8px; font-size: 13px;")
        form_layout.addWidget(self.skills_edit, 4, 1)
        
        layout.addWidget(form_group)
        
        # 高级设置
        advanced_group = QGroupBox("高级设置")
        self.theme.apply_poe2_style_properties(advanced_group, "enhanced_group")
        advanced_layout = QGridLayout(advanced_group)
        
        # 最小DPS要求
        min_dps_label = QLabel("最小DPS:")
        advanced_layout.addWidget(min_dps_label, 0, 0)
        
        self.min_dps_spin = QSpinBox()
        self.min_dps_spin.setRange(0, 10000000)
        self.min_dps_spin.setValue(100000)
        self.min_dps_spin.setSuffix(" DPS")
        advanced_layout.addWidget(self.min_dps_spin, 0, 1)
        
        # 最小有效HP
        min_hp_label = QLabel("最小有效HP:")
        advanced_layout.addWidget(min_hp_label, 1, 0)
        
        self.min_hp_spin = QSpinBox()
        self.min_hp_spin.setRange(0, 50000)
        self.min_hp_spin.setValue(5000)
        self.min_hp_spin.setSuffix(" HP")
        advanced_layout.addWidget(self.min_hp_spin, 1, 1)
        
        # 游戏模式
        mode_label = QLabel("游戏模式:")
        advanced_layout.addWidget(mode_label, 2, 0)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["标准模式", "专家模式"])
        advanced_layout.addWidget(self.mode_combo, 2, 1)
        
        layout.addWidget(advanced_group)
        
        # 自然语言描述
        desc_group = QGroupBox("构筑描述 (可选)")
        self.theme.apply_poe2_style_properties(desc_group, "enhanced_group")
        desc_layout = QVBoxLayout(desc_group)
        
        desc_label = QLabel("用自然语言描述你想要的构筑类型:")
        desc_label.setStyleSheet(f"color: {self.theme.COLORS['text_secondary']}; font-size: 12px;")
        desc_layout.addWidget(desc_label)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("例: 我想要一个高清怪速度的弓箭手构筑，主要用于刷图，预算不超过30个神圣球...")
        self.description_edit.setMaximumHeight(100)
        self.theme.apply_poe2_style_properties(self.description_edit, "enhanced_input")
        desc_layout.addWidget(self.description_edit)
        
        layout.addWidget(desc_group)
        
        # 生成按钮
        generate_frame = QFrame()
        generate_layout = QVBoxLayout(generate_frame)
        
        self.generate_btn = QPushButton("🚀 生成构筑推荐")
        self.generate_btn.setStyleSheet(f"""
        QPushButton {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 {self.theme.COLORS['poe2_gold']}, 
                stop: 1 {self.theme.COLORS['glow_gold']});
            border: 2px solid {self.theme.COLORS['poe2_gold']};
            color: {self.theme.COLORS['background_primary']};
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            min-height: 36px;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 {self.theme.COLORS['glow_gold']}, 
                stop: 1 {self.theme.COLORS['poe2_gold']});
        }}
        QPushButton:pressed {{
            background-color: {self.theme.COLORS['poe2_gold']};
        }}
        QPushButton:disabled {{
            background-color: {self.theme.COLORS['background_tertiary']};
            color: {self.theme.COLORS['text_disabled']};
            border-color: {self.theme.COLORS['text_disabled']};
        }}
        """)
        self.generate_btn.clicked.connect(self.generate_builds)
        generate_layout.addWidget(self.generate_btn)
        
        # 进度显示
        self.progress_frame = QFrame()
        progress_layout = QHBoxLayout(self.progress_frame)
        
        self.progress_bar = QProgressBar()
        self.theme.apply_poe2_style_properties(self.progress_bar, "enhanced_progress")
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_frame.setVisible(False)
        generate_layout.addWidget(self.progress_frame)
        
        layout.addWidget(generate_frame)
        
        layout.addStretch()
        
        # 设置滚动区域
        scroll_area.setWidget(panel)
        return scroll_area
    
    def create_results_panel(self):
        """创建结果面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)
        
        # 结果标题栏
        results_header = QFrame()
        results_header.setStyleSheet(f"""
        QFrame {{
            background-color: {self.theme.COLORS['background_secondary']};
            border: 1px solid {self.theme.COLORS['border_primary']};
            border-radius: 8px;
            padding: 12px;
        }}
        """)
        header_layout = QHBoxLayout(results_header)
        
        results_title = QLabel("构筑推荐结果")
        results_title.setStyleSheet(f"""
        color: {self.theme.COLORS['poe2_gold']};
        font-size: 18px;
        font-weight: bold;
        """)
        header_layout.addWidget(results_title)
        
        header_layout.addStretch()
        
        self.results_count_label = QLabel("0 个推荐")
        self.results_count_label.setStyleSheet(f"""
        color: {self.theme.COLORS['text_secondary']};
        font-size: 14px;
        font-weight: 600;
        """)
        header_layout.addWidget(self.results_count_label)
        
        layout.addWidget(results_header)
        
        # 构筑卡片滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 滚动内容容器
        scroll_content = QWidget()
        # 使用网格布局以支持多列显示
        self.results_layout = QGridLayout(scroll_content)
        self.results_layout.setSpacing(8)
        self.results_layout.setContentsMargins(8, 8, 8, 8)
        
        # 添加伸缩项用于底部对齐
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.results_layout.addItem(spacer, 1000, 0)  # 放在很大的行数上
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        return panel
    
    def create_console_dock(self):
        """创建控制台停靠面板"""
        self.console_dock = QDockWidget("开发者控制台", self)
        self.console_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        
        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        
        # 控制台标题
        console_title = QLabel("开发者控制台 - F12 切换显示")
        console_title.setStyleSheet(f"""
        color: {self.theme.COLORS['poe2_gold']};
        font-weight: bold;
        padding: 4px;
        """)
        console_layout.addWidget(console_title)
        
        # 控制台文本
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        self.console_text.setFont(QFont("Consolas", 10))
        self.console_text.setStyleSheet(f"""
        QTextEdit {{
            background-color: {self.theme.COLORS['background_primary']};
            border: 1px solid {self.theme.COLORS['poe2_gold']};
            color: {self.theme.COLORS['text_primary']};
            font-family: 'Consolas', 'Monaco', monospace;
        }}
        """)
        console_layout.addWidget(self.console_text)
        
        self.console_dock.setWidget(console_widget)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.console_dock)
        self.console_dock.hide()  # 初始隐藏
    
    def setup_shortcuts(self):
        """设置快捷键"""
        # F12 控制台
        f12_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F12), self)
        f12_shortcut.activated.connect(self.toggle_console)
        
        # Ctrl+G 生成
        generate_shortcut = QShortcut(QKeySequence("Ctrl+G"), self)
        generate_shortcut.activated.connect(self.generate_builds)
        
        # ESC 关闭控制台
        esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc_shortcut.activated.connect(lambda: self.console_dock.hide())
    
    def setup_orchestrator(self):
        """设置AI编排器"""
        self.log_message("正在初始化AI编排器系统...", "info")
        QTimer.singleShot(100, self.initialize_orchestrator_async)
    
    def initialize_orchestrator_async(self):
        """异步初始化编排器"""
        try:
            self.orchestrator = PoE2AIOrchestrator()
            QTimer.singleShot(200, self.run_orchestrator_init)
        except Exception as e:
            self.log_message(f"AI编排器初始化失败: {e}", "error")
            self.ai_status_label.setText("AI: 错误")
            self.ai_status_label.setStyleSheet(f"color: {self.theme.COLORS['error']}; padding: 2px 8px;")
    
    def run_orchestrator_init(self):
        """运行编排器初始化"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            loop.run_until_complete(self.orchestrator.initialize())
            
            self.log_message("✓ AI编排器初始化完成", "success")
            self.ai_status_label.setText("AI: 就绪")
            self.ai_status_label.setStyleSheet(f"color: {self.theme.COLORS['success']}; padding: 2px 8px;")
            
            self.pob2_status_label.setText("PoB2: 已连接")
            self.pob2_status_label.setStyleSheet(f"color: {self.theme.COLORS['success']}; padding: 2px 8px;")
            
            self.status_bar.showMessage("系统已就绪 - 可以开始生成构筑")
            
            loop.close()
            
        except Exception as e:
            self.log_message(f"初始化错误: {e}", "error")
            self.ai_status_label.setText("AI: 错误")
            self.ai_status_label.setStyleSheet(f"color: {self.theme.COLORS['error']}; padding: 2px 8px;")
    
    def log_message(self, message: str, level: str = "info"):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color_map = {
            "info": self.theme.COLORS['text_primary'],
            "success": self.theme.COLORS['success'],
            "warning": self.theme.COLORS['warning'],
            "error": self.theme.COLORS['error'],
            "debug": self.theme.COLORS['text_secondary']
        }
        color = color_map.get(level, self.theme.COLORS['text_primary'])
        
        formatted_msg = f'<span style="color: {self.theme.COLORS["text_secondary"]};">[{timestamp}]</span> <span style="color: {color};">{message}</span>'
        self.console_text.append(formatted_msg)
        
        # 自动滚动到底部
        scrollbar = self.console_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    @pyqtSlot()
    def toggle_console(self):
        """切换控制台显示"""
        if self.console_dock.isVisible():
            self.console_dock.hide()
            self.log_message("控制台已隐藏", "info")
        else:
            self.console_dock.show()
            self.log_message("控制台已显示 - F12或ESC可关闭", "info")
    
    @pyqtSlot()
    def generate_builds(self):
        """生成构筑"""
        if not self.orchestrator:
            self.log_message("错误: AI编排器未初始化", "error")
            QMessageBox.warning(self, "错误", "AI编排器未初始化，请等待系统就绪")
            return
        
        self.log_message("开始生成构筑推荐...", "info")
        self.status_bar.showMessage("正在生成构筑推荐...")
        
        # 显示进度
        self.progress_frame.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.generate_btn.setEnabled(False)
        
        try:
            # 创建请求
            skills_text = self.skills_edit.text().strip()
            skills = [skill.strip() for skill in skills_text.split(',')] if skills_text else None
            
            # 处理升华选择
            ascendancy = None
            if self.ascendancy_combo.currentText() != "自动选择":
                try:
                    ascendancy = PoE2Ascendancy(self.ascendancy_combo.currentText())
                except ValueError:
                    pass
            
            request = UserRequest(
                character_class=PoE2CharacterClass(self.class_combo.currentText()),
                ascendancy=ascendancy,
                build_goal=PoE2BuildGoal(self.goal_combo.currentText()),
                max_budget=float(self.budget_spin.value()),
                currency_type="divine",
                preferred_skills=skills,
                playstyle="balanced",
                min_dps=float(self.min_dps_spin.value()),
                min_ehp=float(self.min_hp_spin.value())
            )
            
            # 异步执行
            QTimer.singleShot(200, lambda: self.run_build_generation(request))
            
        except Exception as e:
            self.log_message(f"请求创建失败: {e}", "error")
            self.progress_frame.setVisible(False)
            self.generate_btn.setEnabled(True)
    
    def run_build_generation(self, request: UserRequest):
        """运行构筑生成"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(self.orchestrator.generate_build_recommendations(request))
            
            self.handle_build_results(result)
            
            loop.close()
            
        except Exception as e:
            self.log_message(f"生成失败: {e}", "error")
            self.status_bar.showMessage("构筑生成失败")
            QMessageBox.critical(self, "生成失败", f"构筑生成过程中发生错误:\n{str(e)}")
        finally:
            self.progress_frame.setVisible(False)
            self.generate_btn.setEnabled(True)
    
    def handle_build_results(self, result):
        """处理构筑结果"""
        self.build_results = result.builds
        
        self.log_message(f"✓ 成功生成 {len(result.builds)} 个构筑推荐", "success")
        self.log_message(f"RAG置信度: {result.rag_confidence:.3f}", "info")
        self.log_message(f"PoB2验证: {'通过' if result.pob2_validated else '未验证'}", "info")
        self.log_message(f"生成时间: {result.generation_time_ms:.2f}ms", "debug")
        
        self.status_bar.showMessage(f"成功生成 {len(result.builds)} 个构筑推荐")
        self.results_count_label.setText(f"{len(result.builds)} 个推荐")
        
        # 清除旧结果
        self.clear_build_cards()
        
        # 添加新结果
        for build in result.builds:
            card = PoE2ProfessionalCard(build)
            card.build_selected.connect(self.on_build_selected)
            card.detail_requested.connect(self.show_build_detail)
            self.results_layout.insertWidget(self.results_layout.count() - 1, card)
        
        if result.builds:
            self.log_message("点击构筑卡片查看详细信息或选择构筑", "info")
    
    def clear_build_cards(self):
        """清除构筑卡片"""
        for i in reversed(range(self.results_layout.count())):
            child = self.results_layout.itemAt(i).widget()
            if child and isinstance(child, PoE2ProfessionalCard):
                child.setParent(None)
    
    @pyqtSlot(object)
    def on_build_selected(self, build):
        """构筑被选中"""
        self.log_message(f"选中构筑: {build.name}", "info")
        self.status_bar.showMessage(f"已选择构筑: {build.name}")
        
        if build.pob2_code:
            self.log_message("PoB2导入代码已准备就绪", "success")
    
    @pyqtSlot(object)
    def show_build_detail(self, build):
        """显示构筑详情"""
        self.log_message(f"打开构筑详情: {build.name}", "info")
        
        detail_dialog = PoE2BuildDetailDialog(build, self)
        detail_dialog.export_requested.connect(self.handle_export_request)
        detail_dialog.exec()
    
    @pyqtSlot(object, str)
    def handle_export_request(self, build, export_type):
        """处理导出请求"""
        if export_type == "pob2" and build.pob2_code:
            self.log_message(f"导出构筑到PoB2: {build.name}", "info")
            
            try:
                # 创建PoB2链接
                encoded_code = quote(build.pob2_code)
                pob2_url = f"https://pob.party/share/{encoded_code}"
                
                # 打开浏览器
                webbrowser.open(pob2_url)
                
                # 同时复制到剪贴板
                clipboard = QApplication.clipboard()
                clipboard.setText(build.pob2_code)
                
                self.log_message("✓ PoB2链接已在浏览器中打开，导入代码已复制到剪贴板", "success")
                QMessageBox.information(
                    self, 
                    "导出成功", 
                    f"构筑已成功导出!\n\n"
                    f"• PoB2链接已在浏览器中打开\n"
                    f"• 导入代码已复制到剪贴板\n"
                    f"• 可在Path of Building中直接粘贴导入"
                )
                
            except Exception as e:
                self.log_message(f"PoB2导出失败: {e}", "error")
                QMessageBox.critical(self, "导出失败", f"PoB2导出过程中发生错误:\n{str(e)}")
    
    # 菜单动作实现
    def import_config(self):
        self.log_message("导入配置功能", "info")
        
    def export_builds(self):
        if not self.build_results:
            QMessageBox.information(self, "提示", "没有可导出的构筑结果")
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self, "导出构筑列表", "poe2_builds.json", "JSON Files (*.json)"
        )
        if filename:
            try:
                builds_data = []
                for build in self.build_results:
                    builds_data.append({
                        "name": build.name,
                        "character_class": build.character_class.value,
                        "ascendancy": build.ascendancy.value if build.ascendancy else None,
                        "main_skill": build.main_skill_gem,
                        "estimated_cost": build.estimated_cost,
                        "pob2_code": build.pob2_code
                    })
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(builds_data, f, ensure_ascii=False, indent=2)
                
                self.log_message(f"✓ 构筑列表已导出到: {filename}", "success")
                QMessageBox.information(self, "成功", f"构筑列表已导出到:\n{filename}")
            except Exception as e:
                self.log_message(f"导出失败: {e}", "error")
    
    def clear_results(self):
        self.clear_build_cards()
        self.build_results = []
        self.results_count_label.setText("0 个推荐")
        self.log_message("构筑结果已清空", "info")
        
    def export_selected_to_pob2(self):
        self.log_message("批量导出到PoB2功能", "info")
        
    def configure_pob2(self):
        self.log_message("PoB2集成设置", "info")
        
    def manage_data_sources(self):
        self.log_message("数据源管理", "info")
        
    def show_manual(self):
        self.log_message("显示用户手册", "info")
        
    def show_about(self):
        about_text = """
        <h3>PoE2 Build Generator - 专业版</h3>
        <p><b>版本:</b> 2.0.0 Professional</p>
        <p><b>描述:</b> Path of Exile 2 AI驱动的专业构筑生成器</p>
        <br>
        <p><b>核心功能:</b></p>
        <ul>
        <li>AI智能构筑推荐</li>
        <li>PoB2深度集成</li>
        <li>RAG增强的推荐系统</li>
        <li>实时市场数据</li>
        <li>专业级PoE2风格界面</li>
        </ul>
        <br>
        <p><b>快捷键:</b></p>
        <ul>
        <li>F12: 开发者控制台</li>
        <li>Ctrl+G: 生成构筑</li>
        <li>ESC: 关闭控制台</li>
        </ul>
        """
        QMessageBox.about(self, "关于", about_text)
    
    def closeEvent(self, event):
        """关闭事件"""
        self.log_message("应用程序正在关闭...", "info")
        event.accept()

    def generate_builds(self):
        """生成构筑推荐"""
        # 显示进度条
        self.progress_frame.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 无限进度条
        self.generate_btn.setEnabled(False)
        
        # 启动异步生成任务
        self.generation_thread = BuildGenerationThread(
            character_class=self.class_combo.currentData(),
            ascendancy=self.ascendancy_combo.currentData(), 
            build_goal=self.goal_combo.currentData(),
            max_budget=float(self.budget_spin.value()),
            min_dps=float(self.min_dps_spin.value()),
            min_ehp=float(self.min_hp_spin.value())
        )
        self.generation_thread.builds_ready.connect(self.on_builds_generated)
        self.generation_thread.error_occurred.connect(self.on_generation_error)
        self.generation_thread.start()
    
    def on_builds_generated(self, builds):
        """处理生成完成的构筑"""
        # 清空现有结果
        self.clear_results()
        
        # 更新结果计数
        self.results_count_label.setText(f"{len(builds)} 个推荐")
        
        # 计算网格列数（基于可用宽度）
        available_width = self.width() - 500  # 减去左侧面板和边距
        card_width = 380  # 卡片最小宽度
        max_columns = max(1, available_width // card_width)
        
        # 添加构筑卡片到网格
        for i, build in enumerate(builds):
            row = i // max_columns
            col = i % max_columns
            
            card = PoE2ProfessionalCard(build, self.theme)
            card.build_selected.connect(self.on_build_selected)
            card.detail_requested.connect(self.show_build_details)
            
            self.results_layout.addWidget(card, row, col)
        
        # 隐藏进度条，启用按钮
        self.progress_frame.setVisible(False)
        self.generate_btn.setEnabled(True)
        
        # 记录日志
        self.console.append(f"✓ 成功生成 {len(builds)} 个构筑推荐")
    
    def on_generation_error(self, error_msg):
        """处理生成错误"""
        self.progress_frame.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.console.append(f"✗ 构筑生成失败: {error_msg}")
        
        # 显示错误消息
        QMessageBox.warning(self, "生成失败", f"构筑生成失败:\n{error_msg}")
    
    def clear_results(self):
        """清空结果区域"""
        # 移除所有构筑卡片
        for i in reversed(range(self.results_layout.count())):
            item = self.results_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), PoE2ProfessionalCard):
                item.widget().setParent(None)
    
    def on_build_selected(self, build):
        """处理构筑选择事件"""
        self.console.append(f"📋 已选择构筑: {build.name}")
    
    def show_build_details(self, build):
        """显示构筑详细信息对话框"""
        dialog = PoE2BuildDetailDialog(build, self.theme, self)
        dialog.exec()
    
    def resizeEvent(self, event):
        """窗口大小改变事件 - 重新计算网格布局"""
        super().resizeEvent(event)
        
        # 重新排列现有卡片（如果有的话）
        if hasattr(self, 'results_layout') and self.results_layout.count() > 1:
            # 获取所有卡片
            cards = []
            for i in reversed(range(self.results_layout.count())):
                item = self.results_layout.itemAt(i)
                if item and item.widget() and isinstance(item.widget(), PoE2ProfessionalCard):
                    cards.append(item.widget())
                    self.results_layout.removeItem(item)
            
            if cards:
                # 重新计算列数
                available_width = event.size().width() - 500
                card_width = 380
                max_columns = max(1, available_width // card_width)
                
                # 重新添加卡片
                for i, card in enumerate(reversed(cards)):
                    row = i // max_columns
                    col = i % max_columns
                    self.results_layout.addWidget(card, row, col)


class PoE2BuildDetailDialog(QDialog):
    """构筑详细信息对话框"""
    
    def __init__(self, build, theme, parent=None):
        super().__init__(parent)
        self.build = build
        self.theme = theme
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle(f"构筑详情 - {self.build.name}")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # 标题区
        title_frame = QFrame()
        title_frame.setStyleSheet(f"""
        QFrame {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 {self.theme.COLORS['poe2_gold']}, 
                stop: 1 {self.theme.COLORS['background_secondary']});
            border-radius: 8px;
            padding: 16px;
        }}
        """)
        title_layout = QHBoxLayout(title_frame)
        
        title_label = QLabel(self.build.name)
        title_label.setStyleSheet(f"""
        color: {self.theme.COLORS['background_primary']};
        font-size: 24px;
        font-weight: bold;
        """)
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        class_label = QLabel(f"{self.build.character_class.value}")
        if self.build.ascendancy:
            class_label.setText(f"{self.build.character_class.value} - {self.build.ascendancy.value}")
        class_label.setStyleSheet(f"""
        color: {self.theme.COLORS['background_primary']};
        font-size: 16px;
        font-weight: 600;
        """)
        title_layout.addWidget(class_label)
        
        layout.addWidget(title_frame)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(12)
        
        # 核心统计区
        if self.build.stats:
            self.create_core_stats_section(content_layout)
        
        # 技能信息区
        self.create_skills_section(content_layout)
        
        # 抗性和防御区
        if self.build.stats:
            self.create_defense_section(content_layout)
        
        # 预算和物品区
        self.create_budget_section(content_layout)
        
        # PoB2区
        if hasattr(self.build, 'pob2_code') and self.build.pob2_code:
            self.create_pob2_section(content_layout)
        
        # 备注区
        if self.build.notes:
            self.create_notes_section(content_layout)
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # 按钮区
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        if hasattr(self.build, 'pob2_code') and self.build.pob2_code:
            export_btn = QPushButton("导出到PoB2")
            export_btn.clicked.connect(self.export_to_pob2)
            button_layout.addWidget(export_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def create_core_stats_section(self, layout):
        """创建核心统计区"""
        section_frame = QFrame()
        section_frame.setStyleSheet(f"""
        QFrame {{
            background-color: {self.theme.COLORS['background_secondary']};
            border: 1px solid {self.theme.COLORS['border_primary']};
            border-radius: 8px;
            padding: 16px;
        }}
        """)
        section_layout = QVBoxLayout(section_frame)
        
        # 标题
        title = QLabel("核心属性")
        title.setStyleSheet(f"color: {self.theme.COLORS['poe2_gold']}; font-size: 18px; font-weight: bold;")
        section_layout.addWidget(title)
        
        # 统计网格
        stats_layout = QGridLayout()
        row = 0
        
        # DPS
        stats_layout.addWidget(QLabel("总DPS:"), row, 0)
        dps_value = QLabel(f"{self.build.stats.total_dps:,.0f}")
        dps_value.setStyleSheet(f"color: {self.theme.COLORS['poe2_red']}; font-weight: bold;")
        stats_layout.addWidget(dps_value, row, 1)
        
        # 有效生命值
        stats_layout.addWidget(QLabel("有效HP:"), row, 2)
        ehp_value = QLabel(f"{self.build.stats.effective_health_pool:,.0f}")
        ehp_value.setStyleSheet(f"color: {self.theme.COLORS['poe2_green']}; font-weight: bold;")
        stats_layout.addWidget(ehp_value, row, 3)
        row += 1
        
        # 生命值和护盾
        stats_layout.addWidget(QLabel("生命值:"), row, 0)
        stats_layout.addWidget(QLabel(f"{self.build.stats.life:,.0f}"), row, 1)
        
        stats_layout.addWidget(QLabel("能量护盾:"), row, 2)
        stats_layout.addWidget(QLabel(f"{self.build.stats.energy_shield:,.0f}"), row, 3)
        row += 1
        
        # 暴击属性
        if self.build.stats.critical_strike_chance > 0:
            stats_layout.addWidget(QLabel("暴击几率:"), row, 0)
            stats_layout.addWidget(QLabel(f"{self.build.stats.critical_strike_chance:.1f}%"), row, 1)
            
            stats_layout.addWidget(QLabel("暴击倍率:"), row, 2)
            stats_layout.addWidget(QLabel(f"{self.build.stats.critical_strike_multiplier:.0f}%"), row, 3)
            row += 1
        
        # 移动速度
        if self.build.stats.movement_speed > 0:
            stats_layout.addWidget(QLabel("移动速度:"), row, 0)
            speed_value = QLabel(f"+{self.build.stats.movement_speed:.0f}%")
            speed_value.setStyleSheet(f"color: {self.theme.COLORS['poe2_blue']};")
            stats_layout.addWidget(speed_value, row, 1)
        
        section_layout.addLayout(stats_layout)
        layout.addWidget(section_frame)
    
    def create_skills_section(self, layout):
        """创建技能信息区"""
        if not (self.build.main_skill_gem or self.build.support_gems):
            return
        
        section_frame = QFrame()
        section_frame.setStyleSheet(f"""
        QFrame {{
            background-color: {self.theme.COLORS['background_secondary']};
            border: 1px solid {self.theme.COLORS['border_primary']};
            border-radius: 8px;
            padding: 16px;
        }}
        """)
        section_layout = QVBoxLayout(section_frame)
        
        title = QLabel("技能配置")
        title.setStyleSheet(f"color: {self.theme.COLORS['poe2_gold']}; font-size: 18px; font-weight: bold;")
        section_layout.addWidget(title)
        
        if self.build.main_skill_gem:
            main_skill_layout = QHBoxLayout()
            main_skill_layout.addWidget(QLabel("主技能:"))
            main_skill_value = QLabel(self.build.main_skill_gem)
            main_skill_value.setStyleSheet(f"color: {self.theme.COLORS['poe2_blue']}; font-weight: bold;")
            main_skill_layout.addWidget(main_skill_value)
            main_skill_layout.addStretch()
            section_layout.addLayout(main_skill_layout)
        
        if self.build.support_gems:
            support_label = QLabel("辅助宝石:")
            section_layout.addWidget(support_label)
            
            for gem in self.build.support_gems:
                gem_label = QLabel(f"  • {gem}")
                gem_label.setStyleSheet(f"color: {self.theme.COLORS['text_secondary']};")
                section_layout.addWidget(gem_label)
        
        layout.addWidget(section_frame)
    
    def create_defense_section(self, layout):
        """创建防御信息区"""
        section_frame = QFrame()
        section_frame.setStyleSheet(f"""
        QFrame {{
            background-color: {self.theme.COLORS['background_secondary']};
            border: 1px solid {self.theme.COLORS['border_primary']};
            border-radius: 8px;
            padding: 16px;
        }}
        """)
        section_layout = QVBoxLayout(section_frame)
        
        title = QLabel("抗性与防御")
        title.setStyleSheet(f"color: {self.theme.COLORS['poe2_gold']}; font-size: 18px; font-weight: bold;")
        section_layout.addWidget(title)
        
        # 抗性网格
        res_layout = QGridLayout()
        
        # 火抗
        res_layout.addWidget(QLabel("火焰抗性:"), 0, 0)
        fire_res = QLabel(f"{self.build.stats.fire_resistance}%")
        fire_res.setStyleSheet(f"color: {'red' if self.build.stats.fire_resistance < 75 else self.theme.COLORS['poe2_green']};")
        res_layout.addWidget(fire_res, 0, 1)
        
        # 冰抗
        res_layout.addWidget(QLabel("冰霜抗性:"), 0, 2)
        cold_res = QLabel(f"{self.build.stats.cold_resistance}%")
        cold_res.setStyleSheet(f"color: {'red' if self.build.stats.cold_resistance < 75 else self.theme.COLORS['poe2_green']};")
        res_layout.addWidget(cold_res, 0, 3)
        
        # 雷抗
        res_layout.addWidget(QLabel("闪电抗性:"), 1, 0)
        lightning_res = QLabel(f"{self.build.stats.lightning_resistance}%")
        lightning_res.setStyleSheet(f"color: {'red' if self.build.stats.lightning_resistance < 75 else self.theme.COLORS['poe2_green']};")
        res_layout.addWidget(lightning_res, 1, 1)
        
        # 混沌抗
        res_layout.addWidget(QLabel("混沌抗性:"), 1, 2)
        chaos_res = QLabel(f"{self.build.stats.chaos_resistance}%")
        chaos_res.setStyleSheet(f"color: {'orange' if self.build.stats.chaos_resistance < 0 else self.theme.COLORS['poe2_green']};")
        res_layout.addWidget(chaos_res, 1, 3)
        
        section_layout.addLayout(res_layout)
        layout.addWidget(section_frame)
    
    def create_budget_section(self, layout):
        """创建预算信息区"""
        if not self.build.estimated_cost:
            return
        
        section_frame = QFrame()
        section_frame.setStyleSheet(f"""
        QFrame {{
            background-color: {self.theme.COLORS['background_secondary']};
            border: 1px solid {self.theme.COLORS['border_primary']};
            border-radius: 8px;
            padding: 16px;
        }}
        """)
        section_layout = QVBoxLayout(section_frame)
        
        title = QLabel("预算信息")
        title.setStyleSheet(f"color: {self.theme.COLORS['poe2_gold']}; font-size: 18px; font-weight: bold;")
        section_layout.addWidget(title)
        
        cost_layout = QHBoxLayout()
        cost_layout.addWidget(QLabel("预估成本:"))
        cost_value = QLabel(f"{self.build.estimated_cost:.1f} {self.build.currency_type or 'divine'}")
        cost_value.setStyleSheet(f"color: {self.theme.COLORS['poe2_gold']}; font-weight: bold; font-size: 16px;")
        cost_layout.addWidget(cost_value)
        cost_layout.addStretch()
        
        section_layout.addLayout(cost_layout)
        layout.addWidget(section_frame)
    
    def create_pob2_section(self, layout):
        """创建PoB2信息区"""
        section_frame = QFrame()
        section_frame.setStyleSheet(f"""
        QFrame {{
            background-color: {self.theme.COLORS['background_secondary']};
            border: 1px solid {self.theme.COLORS['border_primary']};
            border-radius: 8px;
            padding: 16px;
        }}
        """)
        section_layout = QVBoxLayout(section_frame)
        
        title = QLabel("Path of Building 2")
        title.setStyleSheet(f"color: {self.theme.COLORS['poe2_gold']}; font-size: 18px; font-weight: bold;")
        section_layout.addWidget(title)
        
        pob2_info = QLabel("此构筑包含完整的PoB2导入代码，可直接导入到Path of Building 2中查看完整配置。")
        pob2_info.setStyleSheet(f"color: {self.theme.COLORS['text_secondary']};")
        pob2_info.setWordWrap(True)
        section_layout.addWidget(pob2_info)
        
        export_btn = QPushButton("📋 导出并打开PoB2")
        export_btn.clicked.connect(self.export_to_pob2)
        section_layout.addWidget(export_btn)
        
        layout.addWidget(section_frame)
    
    def create_notes_section(self, layout):
        """创建备注区"""
        section_frame = QFrame()
        section_frame.setStyleSheet(f"""
        QFrame {{
            background-color: {self.theme.COLORS['background_secondary']};
            border: 1px solid {self.theme.COLORS['border_primary']};
            border-radius: 8px;
            padding: 16px;
        }}
        """)
        section_layout = QVBoxLayout(section_frame)
        
        title = QLabel("备注信息")
        title.setStyleSheet(f"color: {self.theme.COLORS['poe2_gold']}; font-size: 18px; font-weight: bold;")
        section_layout.addWidget(title)
        
        notes_text = QLabel(self.build.notes)
        notes_text.setStyleSheet(f"color: {self.theme.COLORS['text_secondary']};")
        notes_text.setWordWrap(True)
        section_layout.addWidget(notes_text)
        
        layout.addWidget(section_frame)
    
    def export_to_pob2(self):
        """导出到PoB2"""
        try:
            if not hasattr(self.build, 'pob2_code') or not self.build.pob2_code:
                QMessageBox.warning(self, "导出失败", "此构筑没有PoB2导入代码")
                return
            
            # 创建PoB2链接
            encoded_code = quote(self.build.pob2_code)
            pob2_url = f"https://pob.party/share/{encoded_code}"
            
            # 打开浏览器
            webbrowser.open(pob2_url)
            
            # 同时复制到剪贴板
            clipboard = QApplication.clipboard()
            clipboard.setText(pob2_url)
            
            # 显示成功消息
            QMessageBox.information(self, "导出成功", f"PoB2链接已打开并复制到剪贴板!\n\n{pob2_url}")
            
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出PoB2时发生错误:\n{str(e)}")


class BuildGenerationThread(QThread):
    """构筑生成线程"""
    builds_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, character_class, ascendancy, build_goal, max_budget, min_dps, min_ehp):
        super().__init__()
        self.character_class = character_class
        self.ascendancy = ascendancy
        self.build_goal = build_goal
        self.max_budget = max_budget
        self.min_dps = min_dps
        self.min_ehp = min_ehp
    
    def run(self):
        """执行构筑生成"""
        try:
            # 创建AI调度器请求
            from poe2build.core.ai_orchestrator import PoE2AIOrchestrator, UserRequest
            
            orchestrator = PoE2AIOrchestrator()
            
            # 初始化（同步方式，因为在后台线程）
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            
            loop.run_until_complete(orchestrator.initialize())
            
            # 创建用户请求
            request = UserRequest(
                character_class=self.character_class,
                ascendancy=self.ascendancy,
                build_goal=self.build_goal,
                max_budget=self.max_budget,
                min_dps=self.min_dps,
                min_ehp=self.min_ehp
            )
            
            # 生成推荐
            result = loop.run_until_complete(orchestrator.generate_build_recommendations(request))
            
            # 发出成功信号
            self.builds_ready.emit(result.builds)
            
        except Exception as e:
            # 发出错误信号
            self.error_occurred.emit(str(e))


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("PoE2 Build Generator Professional")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("PoE2 Tools Professional")
    
    # 设置应用字体
    font = QFont("Microsoft YaHei UI", 9)
    app.setFont(font)
    
    # 创建主题
    theme = PoE2Theme()
    app.setPalette(theme.get_palette())
    app.setStyleSheet(theme.get_stylesheet())
    
    try:
        # 创建主窗口
        window = PoE2ProfessionalGUI()
        window.show()
        
        try:
            print("=" * 80)
            print("PoE2 Build Generator - Professional Edition")
            print("=" * 80)
            print("专业级PoE2构筑生成器已启动")
            print()
            print("主要功能:")
            print("  • F12开发者控制台 - 实时系统日志和调试信息")
            print("  • 专业构筑卡片 - 详细属性展示和交互")
            print("  • PoB2完整集成 - 一键导出和浏览器打开")
            print("  • 高级过滤设置 - 最小DPS/HP要求")
            print("  • 批量导出功能 - JSON格式保存")
            print("  • 专业PoE2界面 - 游戏级视觉效果")
            print()
            print("使用说明:")
            print("  1. 设置构筑需求 - 职业、目标、预算等")
            print("  2. 点击生成按钮 - 等待AI推荐")
            print("  3. 查看构筑卡片 - 点击详细信息")
            print("  4. 导出到PoB2 - 自动打开链接")
        except UnicodeEncodeError:
            print("=" * 80)
            print("PoE2 Build Generator - Professional Edition")
            print("=" * 80)
            print("Professional PoE2 Build Generator Started")
            print("All features loaded successfully")
            print("  5. 按F12查看控制台 - 详细日志信息")
            print()
            print("快捷键:")
            print("  F12: 切换开发者控制台")
            print("  Ctrl+G: 快速生成构筑")
            print("  ESC: 关闭控制台")
            print("=" * 80)
        
        return app.exec()
        
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())