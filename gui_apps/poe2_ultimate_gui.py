#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PoE2 Build Generator - 终极专业版GUI
包含完整的网页风格F12控制台、所有功能按钮、完整日志系统
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
        QDialog, QDialogButtonBox, QMessageBox, QFileDialog, QTextBrowser
    )
    from PyQt6.QtCore import (
        Qt, QTimer, pyqtSignal, QThread, pyqtSlot, QSize, QRect,
        QPropertyAnimation, QEasingCurve, QAbstractAnimation, QUrl
    )
    from PyQt6.QtGui import (
        QFont, QIcon, QPainter, QLinearGradient, QColor, QPalette,
        QPixmap, QBrush, QPen, QKeySequence, QShortcut, QAction,
        QFontMetrics, QMovie, QClipboard, QSyntaxHighlighter,
        QTextCharFormat, QTextDocument
    )
    
    from poe2build.gui.styles.poe2_theme import PoE2Theme
    from poe2build.core.ai_orchestrator import PoE2AIOrchestrator, UserRequest
    from poe2build.models.characters import PoE2CharacterClass, PoE2Ascendancy
    from poe2build.models.build import PoE2BuildGoal
    
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装PyQt6: pip install PyQt6")
    sys.exit(1)


class WebStyleConsole(QTextBrowser):
    """网页风格的控制台组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(True)
        self.setOpenExternalLinks(False)
        self.setup_console_style()
        self.log_buffer = []
        self.max_lines = 1000
        
    def setup_console_style(self):
        """设置控制台样式"""
        self.setStyleSheet("""
        QTextBrowser {
            background-color: #1e1e1e;
            color: #d4d4d4;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 12px;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 8px;
        }
        QTextBrowser::scrollbar:vertical {
            background-color: #2d2d2d;
            width: 12px;
            border-radius: 6px;
        }
        QTextBrowser::handle:vertical {
            background-color: #555555;
            border-radius: 6px;
            min-height: 20px;
        }
        QTextBrowser::handle:vertical:hover {
            background-color: #666666;
        }
        """)
        
        # 设置HTML模板
        self.html_template = """
        <!DOCTYPE html>
        <html>
        <head>
        <style>
        body {{
            background-color: #1e1e1e;
            color: #d4d4d4;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 12px;
            margin: 0;
            padding: 8px;
            line-height: 1.4;
        }}
        .log-entry {{
            margin: 2px 0;
            padding: 2px 0;
            border-bottom: 1px solid #333;
        }}
        .timestamp {{
            color: #888888;
            font-size: 11px;
        }}
        .log-level-info {{
            color: #4ec9b0;
        }}
        .log-level-warning {{
            color: #dcdcaa;
        }}
        .log-level-error {{
            color: #f44747;
        }}
        .log-level-debug {{
            color: #9cdcfe;
        }}
        .log-level-success {{
            color: #4ec9b0;
            font-weight: bold;
        }}
        .log-message {{
            margin-left: 10px;
        }}
        .system-info {{
            color: #ce9178;
            font-style: italic;
        }}
        .user-action {{
            color: #569cd6;
            font-weight: bold;
        }}
        .build-info {{
            color: #dcdcaa;
            background-color: #2d2d2d;
            padding: 4px;
            border-left: 3px solid #dcdcaa;
            margin: 4px 0;
        }}
        </style>
        </head>
        <body>
        {content}
        </body>
        </html>
        """
    
    def log(self, message: str, level: str = "info", category: str = "system"):
        """添加日志条目"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # 创建日志条目
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'category': category,
            'message': message
        }
        
        self.log_buffer.append(log_entry)
        
        # 限制缓冲区大小
        if len(self.log_buffer) > self.max_lines:
            self.log_buffer = self.log_buffer[-self.max_lines:]
        
        self.update_display()
    
    def update_display(self):
        """更新显示内容"""
        content_lines = []
        
        for entry in self.log_buffer[-100:]:  # 显示最后100条
            timestamp_span = f'<span class="timestamp">[{entry["timestamp"]}]</span>'
            level_span = f'<span class="log-level-{entry["level"]}">[{entry["level"].upper()}]</span>'
            category_span = f'<span class="{entry["category"]}">[{entry["category"].upper()}]</span>'
            message_span = f'<span class="log-message">{entry["message"]}</span>'
            
            log_line = f'<div class="log-entry">{timestamp_span} {level_span} {category_span} {message_span}</div>'
            content_lines.append(log_line)
        
        html_content = self.html_template.format(content='\n'.join(content_lines))
        self.setHtml(html_content)
        
        # 滚动到底部
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear(self):
        """清空控制台"""
        self.log_buffer.clear()
        self.setHtml(self.html_template.format(content=""))


class PoE2UltimateCard(QFrame):
    """终极版构筑卡片"""
    build_selected = pyqtSignal(object)
    detail_requested = pyqtSignal(object)
    export_requested = pyqtSignal(object)
    
    def __init__(self, build_data, theme, parent=None):
        super().__init__(parent)
        self.build_data = build_data
        self.theme = theme
        self.setFixedSize(380, 280)
        self.setMouseTracking(True)
        self.setup_ui()
        self.setup_animations()
    
    def setup_ui(self):
        """设置UI"""
        self.setStyleSheet(f"""
        PoE2UltimateCard {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 {self.theme.COLORS['background_primary']}, 
                stop: 1 {self.theme.COLORS['background_secondary']});
            border: 2px solid {self.theme.COLORS['border_primary']};
            border-radius: 12px;
        }}
        PoE2UltimateCard:hover {{
            border-color: {self.theme.COLORS['poe2_gold']};
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 {self.theme.COLORS['background_secondary']}, 
                stop: 1 {self.theme.COLORS['background_primary']});
        }}
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        # 标题区域
        self.create_title_section(main_layout)
        
        # 统计区域
        self.create_stats_section(main_layout)
        
        # 技能区域
        self.create_skills_section(main_layout)
        
        # 按钮区域
        self.create_buttons_section(main_layout)
        
        main_layout.addStretch()
    
    def create_title_section(self, main_layout):
        """创建标题区域"""
        title_frame = QFrame()
        title_layout = QVBoxLayout(title_frame)
        
        # 构筑名称
        name_label = QLabel(self.build_data.name)
        name_label.setStyleSheet(f"""
        color: {self.theme.COLORS['poe2_gold']};
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
        color: {self.theme.COLORS['text_secondary']};
        font-size: 12px;
        """)
        title_layout.addWidget(class_label)
        
        main_layout.addWidget(title_frame)
    
    def create_stats_section(self, main_layout):
        """创建统计区域"""
        stats_frame = QFrame()
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setSpacing(8)
        
        if self.build_data.stats:
            # DPS
            dps_label = QLabel("DPS:")
            dps_label.setStyleSheet(f"color: {self.theme.COLORS['text_secondary']}; font-size: 11px;")
            dps_value = QLabel(f"{self.build_data.stats.total_dps:,.0f}")
            dps_value.setStyleSheet(f"color: {self.theme.COLORS['poe2_red']}; font-size: 14px; font-weight: bold;")
            stats_layout.addWidget(dps_label, 0, 0)
            stats_layout.addWidget(dps_value, 0, 1)
            
            # 有效HP
            hp_label = QLabel("有效HP:")
            hp_label.setStyleSheet(f"color: {self.theme.COLORS['text_secondary']}; font-size: 11px;")
            hp_value = QLabel(f"{self.build_data.stats.effective_health_pool:,.0f}")
            hp_value.setStyleSheet(f"color: {self.theme.COLORS['poe2_green']}; font-size: 14px; font-weight: bold;")
            stats_layout.addWidget(hp_label, 1, 0)
            stats_layout.addWidget(hp_value, 1, 1)
            
            # 抗性状态
            res_status = "✓ 三抗满足" if self.build_data.stats.is_resistance_capped() else "⚠ 抗性不足"
            res_color = self.theme.COLORS['poe2_green'] if self.build_data.stats.is_resistance_capped() else "orange"
            res_label = QLabel(res_status)
            res_label.setStyleSheet(f"color: {res_color}; font-size: 11px;")
            stats_layout.addWidget(res_label, 0, 2, 1, 2)
            
            # 预算
            if self.build_data.estimated_cost:
                cost_label = QLabel("预算:")
                cost_label.setStyleSheet(f"color: {self.theme.COLORS['text_secondary']}; font-size: 11px;")
                cost_value = QLabel(f"{self.build_data.estimated_cost:.1f} divine")
                cost_value.setStyleSheet(f"color: {self.theme.COLORS['poe2_gold']}; font-size: 12px; font-weight: bold;")
                stats_layout.addWidget(cost_label, 1, 2)
                stats_layout.addWidget(cost_value, 1, 3)
        
        main_layout.addWidget(stats_frame)
    
    def create_skills_section(self, main_layout):
        """创建技能区域"""
        if not self.build_data.main_skill_gem:
            return
            
        skills_frame = QFrame()
        skills_layout = QVBoxLayout(skills_frame)
        
        skill_label = QLabel(f"主技能: {self.build_data.main_skill_gem}")
        skill_label.setStyleSheet(f"""
        color: {self.theme.COLORS['poe2_blue']};
        font-size: 12px;
        font-weight: 600;
        """)
        skills_layout.addWidget(skill_label)
        
        if self.build_data.support_gems and len(self.build_data.support_gems) > 0:
            support_text = f"辅助: {', '.join(self.build_data.support_gems[:2])}"
            if len(self.build_data.support_gems) > 2:
                support_text += f" +{len(self.build_data.support_gems)-2}个"
            
            support_label = QLabel(support_text)
            support_label.setStyleSheet(f"""
            color: {self.theme.COLORS['text_secondary']};
            font-size: 11px;
            """)
            skills_layout.addWidget(support_label)
        
        main_layout.addWidget(skills_frame)
    
    def create_buttons_section(self, main_layout):
        """创建按钮区域"""
        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setSpacing(8)
        
        # 详情按钮
        details_btn = QPushButton("📋 详情")
        details_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {self.theme.COLORS['background_secondary']};
            color: {self.theme.COLORS['text_primary']};
            border: 1px solid {self.theme.COLORS['border_primary']};
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 11px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {self.theme.COLORS['poe2_blue']};
            border-color: {self.theme.COLORS['poe2_blue']};
        }}
        """)
        details_btn.clicked.connect(lambda: self.detail_requested.emit(self.build_data))
        buttons_layout.addWidget(details_btn)
        
        # 导出按钮
        if hasattr(self.build_data, 'pob2_code') and self.build_data.pob2_code:
            export_btn = QPushButton("🔗 导出")
            export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme.COLORS['poe2_gold']};
                color: {self.theme.COLORS['background_primary']};
                border: 1px solid {self.theme.COLORS['poe2_gold']};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {self.theme.COLORS['glow_gold']};
            }}
            """)
            export_btn.clicked.connect(lambda: self.export_requested.emit(self.build_data))
            buttons_layout.addWidget(export_btn)
        
        # 选择按钮
        select_btn = QPushButton("✓ 选择")
        select_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {self.theme.COLORS['poe2_green']};
            color: {self.theme.COLORS['background_primary']};
            border: 1px solid {self.theme.COLORS['poe2_green']};
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 11px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {self.theme.COLORS['poe2_red']};
            border-color: {self.theme.COLORS['poe2_red']};
        }}
        """)
        select_btn.clicked.connect(lambda: self.build_selected.emit(self.build_data))
        buttons_layout.addWidget(select_btn)
        
        main_layout.addWidget(buttons_frame)
    
    def setup_animations(self):
        """设置动画效果"""
        self.scale_animation = QPropertyAnimation(self, b"geometry")
        self.scale_animation.setDuration(200)
        self.scale_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 缩放动画
            current_rect = self.geometry()
            smaller_rect = QRect(
                current_rect.x() + 2,
                current_rect.y() + 2,
                current_rect.width() - 4,
                current_rect.height() - 4
            )
            self.scale_animation.setStartValue(current_rect)
            self.scale_animation.setEndValue(smaller_rect)
            self.scale_animation.start()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 恢复原始大小
            current_rect = self.geometry()
            original_rect = QRect(
                current_rect.x() - 2,
                current_rect.y() - 2,
                current_rect.width() + 4,
                current_rect.height() + 4
            )
            self.scale_animation.setStartValue(current_rect)
            self.scale_animation.setEndValue(original_rect)
            self.scale_animation.start()
        super().mouseReleaseEvent(event)


class PoE2UltimateGUI(QMainWindow):
    """终极专业版PoE2构筑生成器"""
    
    def __init__(self):
        super().__init__()
        self.theme = PoE2Theme()
        self.orchestrator = None
        self.current_builds = []
        
        # 设置窗口
        self.setWindowTitle("PoE2 Build Generator - Ultimate Professional Edition")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)
        
        # 应用主题
        self.setStyleSheet(f"""
        QMainWindow {{
            background-color: {self.theme.COLORS['background_primary']};
            color: {self.theme.COLORS['text_primary']};
        }}
        """)
        
        # 创建界面
        self.create_menu_bar()
        self.create_main_interface()
        self.create_console_dock()
        self.create_status_bar()
        self.setup_shortcuts()
        
        # 初始化AI调度器
        self.init_orchestrator()
        
        # 记录启动日志
        self.log_message("PoE2 Build Generator Ultimate 已启动", "success", "system")
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        import_action = QAction("导入构筑", self)
        import_action.triggered.connect(self.import_build)
        file_menu.addAction(import_action)
        
        export_action = QAction("导出所有构筑", self)
        export_action.triggered.connect(self.export_all_builds)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        console_action = QAction("切换控制台", self)
        console_action.setShortcut(QKeySequence("F12"))
        console_action.triggered.connect(self.toggle_console)
        view_menu.addAction(console_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_main_interface(self):
        """创建主界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(16)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧输入面板
        left_panel = self.create_input_panel()
        left_panel.setMinimumWidth(400)
        left_panel.setMaximumWidth(500)
        splitter.addWidget(left_panel)
        
        # 右侧结果面板
        right_panel = self.create_results_panel()
        splitter.addWidget(right_panel)
        
        # 设置比例
        splitter.setSizes([450, 1150])
    
    def create_input_panel(self):
        """创建输入面板"""
        panel = QFrame()
        panel.setStyleSheet(f"""
        QFrame {{
            background-color: {self.theme.COLORS['background_secondary']};
            border: 1px solid {self.theme.COLORS['border_primary']};
            border-radius: 8px;
        }}
        """)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # 标题
        title_label = QLabel("构筑生成器")
        title_label.setStyleSheet(f"""
        color: {self.theme.COLORS['poe2_gold']};
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        padding: 16px;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 基本设置组
        basic_group = self.create_basic_settings_group()
        layout.addWidget(basic_group)
        
        # 高级设置组
        advanced_group = self.create_advanced_settings_group()
        layout.addWidget(advanced_group)
        
        # 生成按钮
        self.generate_btn = QPushButton("🎯 生成推荐构筑")
        self.generate_btn.setStyleSheet(f"""
        QPushButton {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 {self.theme.COLORS['poe2_gold']}, 
                stop: 1 {self.theme.COLORS['background_secondary']});
            color: {self.theme.COLORS['background_primary']};
            border: 2px solid {self.theme.COLORS['poe2_gold']};
            border-radius: 8px;
            padding: 12px;
            font-size: 16px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 {self.theme.COLORS['glow_gold']}, 
                stop: 1 {self.theme.COLORS['poe2_gold']});
        }}
        QPushButton:disabled {{
            background-color: {self.theme.COLORS['background_tertiary']};
            color: {self.theme.COLORS['text_disabled']};
            border-color: {self.theme.COLORS['text_disabled']};
        }}
        """)
        self.generate_btn.clicked.connect(self.generate_builds)
        layout.addWidget(self.generate_btn)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.theme.apply_poe2_style_properties(self.progress_bar, "enhanced_progress")
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        return panel
    
    def create_basic_settings_group(self):
        """创建基本设置组"""
        group = QGroupBox("基本设置")
        group.setStyleSheet(f"""
        QGroupBox {{
            color: {self.theme.COLORS['poe2_blue']};
            font-size: 16px;
            font-weight: bold;
            border: 2px solid {self.theme.COLORS['border_primary']};
            border-radius: 8px;
            margin-top: 12px;
            padding: 8px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
        }}
        """)
        
        layout = QGridLayout(group)
        layout.setSpacing(12)
        
        # 职业选择
        layout.addWidget(QLabel("职业:"), 0, 0)
        self.class_combo = QComboBox()
        for char_class in PoE2CharacterClass:
            self.class_combo.addItem(char_class.value, char_class)
        self.theme.apply_poe2_style_properties(self.class_combo, "enhanced_combo")
        layout.addWidget(self.class_combo, 0, 1)
        
        # 升华选择
        layout.addWidget(QLabel("升华:"), 1, 0)
        self.ascendancy_combo = QComboBox()
        self.ascendancy_combo.addItem("任意", None)
        for ascendancy in PoE2Ascendancy:
            self.ascendancy_combo.addItem(ascendancy.value, ascendancy)
        self.theme.apply_poe2_style_properties(self.ascendancy_combo, "enhanced_combo")
        layout.addWidget(self.ascendancy_combo, 1, 1)
        
        # 构筑目标
        layout.addWidget(QLabel("目标:"), 2, 0)
        self.goal_combo = QComboBox()
        for goal in PoE2BuildGoal:
            self.goal_combo.addItem(goal.value, goal)
        self.theme.apply_poe2_style_properties(self.goal_combo, "enhanced_combo")
        layout.addWidget(self.goal_combo, 2, 1)
        
        # 预算
        layout.addWidget(QLabel("最大预算:"), 3, 0)
        self.budget_spin = QSpinBox()
        self.budget_spin.setRange(1, 1000)
        self.budget_spin.setValue(50)
        self.budget_spin.setSuffix(" divine")
        self.theme.apply_poe2_style_properties(self.budget_spin, "enhanced_spin")
        layout.addWidget(self.budget_spin, 3, 1)
        
        return group
    
    def create_advanced_settings_group(self):
        """创建高级设置组"""
        group = QGroupBox("高级过滤")
        group.setStyleSheet(f"""
        QGroupBox {{
            color: {self.theme.COLORS['poe2_red']};
            font-size: 16px;
            font-weight: bold;
            border: 2px solid {self.theme.COLORS['border_primary']};
            border-radius: 8px;
            margin-top: 12px;
            padding: 8px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
        }}
        """)
        
        layout = QGridLayout(group)
        layout.setSpacing(12)
        
        # 最小DPS
        layout.addWidget(QLabel("最小DPS:"), 0, 0)
        self.min_dps_spin = QSpinBox()
        self.min_dps_spin.setRange(0, 10000000)
        self.min_dps_spin.setValue(300000)
        self.min_dps_spin.setSuffix(" DPS")
        self.theme.apply_poe2_style_properties(self.min_dps_spin, "enhanced_spin")
        layout.addWidget(self.min_dps_spin, 0, 1)
        
        # 最小有效HP
        layout.addWidget(QLabel("最小有效HP:"), 1, 0)
        self.min_hp_spin = QSpinBox()
        self.min_hp_spin.setRange(0, 50000)
        self.min_hp_spin.setValue(6000)
        self.min_hp_spin.setSuffix(" HP")
        self.theme.apply_poe2_style_properties(self.min_hp_spin, "enhanced_spin")
        layout.addWidget(self.min_hp_spin, 1, 1)
        
        # 抗性要求
        self.require_res_checkbox = QCheckBox("要求三抗满足75%")
        self.require_res_checkbox.setChecked(True)
        self.theme.apply_poe2_style_properties(self.require_res_checkbox, "enhanced_checkbox")
        layout.addWidget(self.require_res_checkbox, 2, 0, 1, 2)
        
        return group
    
    def create_results_panel(self):
        """创建结果面板"""
        panel = QFrame()
        panel.setStyleSheet(f"""
        QFrame {{
            background-color: {self.theme.COLORS['background_primary']};
            border: 1px solid {self.theme.COLORS['border_primary']};
            border-radius: 8px;
        }}
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 结果标题
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
        QFrame {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 {self.theme.COLORS['poe2_gold']}, 
                stop: 1 {self.theme.COLORS['background_secondary']});
            border-radius: 8px;
            padding: 12px;
        }}
        """)
        header_layout = QHBoxLayout(header_frame)
        
        results_title = QLabel("推荐构筑")
        results_title.setStyleSheet(f"""
        color: {self.theme.COLORS['background_primary']};
        font-size: 20px;
        font-weight: bold;
        """)
        header_layout.addWidget(results_title)
        
        header_layout.addStretch()
        
        self.results_count_label = QLabel("0 个推荐")
        self.results_count_label.setStyleSheet(f"""
        color: {self.theme.COLORS['background_primary']};
        font-size: 14px;
        font-weight: 600;
        """)
        header_layout.addWidget(self.results_count_label)
        
        layout.addWidget(header_frame)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(f"""
        QScrollArea {{
            border: none;
            background-color: transparent;
        }}
        QScrollBar:vertical {{
            background-color: {self.theme.COLORS['background_secondary']};
            width: 12px;
            border-radius: 6px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {self.theme.COLORS['poe2_gold']};
            border-radius: 6px;
            min-height: 20px;
        }}
        """)
        
        # 结果容器
        self.results_widget = QWidget()
        self.results_layout = QGridLayout(self.results_widget)
        self.results_layout.setSpacing(16)
        self.results_layout.setContentsMargins(8, 8, 8, 8)
        
        # 添加伸缩项
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.results_layout.addItem(spacer, 100, 0)
        
        scroll_area.setWidget(self.results_widget)
        layout.addWidget(scroll_area)
        
        return panel
    
    def create_console_dock(self):
        """创建控制台停靠窗口"""
        self.console_dock = QDockWidget("开发者控制台 (F12)", self)
        self.console_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea)
        
        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        console_layout.setSpacing(8)
        
        # 控制台工具栏
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet(f"""
        QFrame {{
            background-color: {self.theme.COLORS['background_secondary']};
            border: 1px solid {self.theme.COLORS['border_primary']};
            border-radius: 4px;
            padding: 6px;
        }}
        """)
        toolbar_layout = QHBoxLayout(toolbar_frame)
        
        # 清空按钮
        clear_btn = QPushButton("🗑 清空")
        clear_btn.setFixedSize(80, 28)
        clear_btn.clicked.connect(self.clear_console)
        toolbar_layout.addWidget(clear_btn)
        
        # 导出日志按钮
        export_log_btn = QPushButton("💾 导出")
        export_log_btn.setFixedSize(80, 28)
        export_log_btn.clicked.connect(self.export_logs)
        toolbar_layout.addWidget(export_log_btn)
        
        toolbar_layout.addStretch()
        
        # 状态指示器
        self.console_status_label = QLabel("● 控制台活跃")
        self.console_status_label.setStyleSheet(f"color: {self.theme.COLORS['poe2_green']};")
        toolbar_layout.addWidget(self.console_status_label)
        
        console_layout.addWidget(toolbar_frame)
        
        # 网页风格控制台
        self.console = WebStyleConsole()
        console_layout.addWidget(self.console)
        
        self.console_dock.setWidget(console_widget)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.console_dock)
        self.console_dock.hide()
        
        # 设置样式
        self.console_dock.setStyleSheet(f"""
        QDockWidget {{
            color: {self.theme.COLORS['text_primary']};
            font-weight: bold;
        }}
        QDockWidget::title {{
            background-color: {self.theme.COLORS['background_secondary']};
            padding: 8px;
            border: 1px solid {self.theme.COLORS['border_primary']};
        }}
        """)
    
    def create_status_bar(self):
        """创建状态栏"""
        status_bar = self.statusBar()
        status_bar.setStyleSheet(f"""
        QStatusBar {{
            background-color: {self.theme.COLORS['background_secondary']};
            border: 1px solid {self.theme.COLORS['border_primary']};
            color: {self.theme.COLORS['text_primary']};
        }}
        """)
        
        # AI状态标签
        self.ai_status_label = QLabel("AI: 初始化中...")
        status_bar.addWidget(self.ai_status_label)
        
        # 分隔符
        status_bar.addPermanentWidget(QLabel("|"))
        
        # 构筑计数
        self.build_count_label = QLabel("构筑: 0")
        status_bar.addPermanentWidget(self.build_count_label)
        
        # 分隔符
        status_bar.addPermanentWidget(QLabel("|"))
        
        # 时间标签
        self.time_label = QLabel()
        self.update_time()
        status_bar.addPermanentWidget(self.time_label)
        
        # 时间更新定时器
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
    
    def setup_shortcuts(self):
        """设置快捷键"""
        # F12切换控制台
        f12_shortcut = QShortcut(QKeySequence("F12"), self)
        f12_shortcut.activated.connect(self.toggle_console)
        
        # Ctrl+G生成构筑
        generate_shortcut = QShortcut(QKeySequence("Ctrl+G"), self)
        generate_shortcut.activated.connect(self.generate_builds)
        
        # Ctrl+L清空控制台
        clear_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        clear_shortcut.activated.connect(self.clear_console)
    
    def init_orchestrator(self):
        """初始化AI调度器"""
        self.log_message("正在初始化AI调度器...", "info", "system")
        
        def init_complete():
            self.ai_status_label.setText("AI: 就绪")
            self.log_message("AI调度器初始化完成", "success", "system")
        
        def init_error(error):
            self.ai_status_label.setText("AI: 错误")
            self.log_message(f"AI调度器初始化失败: {error}", "error", "system")
        
        # 在后台线程中初始化
        self.init_thread = InitializationThread()
        self.init_thread.success.connect(init_complete)
        self.init_thread.error.connect(init_error)
        self.init_thread.orchestrator_ready.connect(self.set_orchestrator)
        self.init_thread.start()
    
    def set_orchestrator(self, orchestrator):
        """设置AI调度器"""
        self.orchestrator = orchestrator
    
    def generate_builds(self):
        """生成构筑"""
        if not self.orchestrator:
            self.log_message("AI调度器未就绪，请稍候重试", "warning", "user_action")
            QMessageBox.warning(self, "警告", "AI调度器未就绪，请稍候重试")
            return
        
        # 显示进度
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("🔄 生成中...")
        
        # 记录用户操作
        request_info = f"{self.class_combo.currentText()} - {self.goal_combo.currentText()}"
        self.log_message(f"用户请求生成构筑: {request_info}", "info", "user_action")
        
        # 创建生成线程
        self.generation_thread = BuildGenerationThread(
            character_class=self.class_combo.currentData(),
            ascendancy=self.ascendancy_combo.currentData(),
            build_goal=self.goal_combo.currentData(),
            max_budget=float(self.budget_spin.value()),
            min_dps=float(self.min_dps_spin.value()),
            min_ehp=float(self.min_hp_spin.value()),
            require_resistance_cap=self.require_res_checkbox.isChecked(),
            orchestrator=self.orchestrator
        )
        
        self.generation_thread.builds_ready.connect(self.on_builds_generated)
        self.generation_thread.error_occurred.connect(self.on_generation_error)
        self.generation_thread.start()
    
    def on_builds_generated(self, builds):
        """处理生成完成的构筑"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("🎯 生成推荐构筑")
        
        # 清空现有结果
        self.clear_results()
        
        # 更新构筑列表
        self.current_builds = builds
        self.results_count_label.setText(f"{len(builds)} 个推荐")
        self.build_count_label.setText(f"构筑: {len(builds)}")
        
        # 显示构筑卡片
        self.display_builds(builds)
        
        # 记录日志
        self.log_message(f"成功生成 {len(builds)} 个构筑推荐", "success", "build_info")
        for i, build in enumerate(builds[:3]):  # 记录前3个构筑的详情
            stats_info = f"DPS: {build.stats.total_dps:,.0f}, HP: {build.stats.effective_health_pool:,.0f}" if build.stats else "无统计数据"
            self.log_message(f"构筑 {i+1}: {build.name} ({stats_info})", "debug", "build_info")
    
    def on_generation_error(self, error_msg):
        """处理生成错误"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("🎯 生成推荐构筑")
        
        # 记录错误
        self.log_message(f"构筑生成失败: {error_msg}", "error", "system")
        
        # 显示错误对话框
        QMessageBox.critical(self, "生成失败", f"构筑生成失败:\n\n{error_msg}")
    
    def display_builds(self, builds):
        """显示构筑"""
        # 计算列数
        available_width = self.width() - 600
        card_width = 380
        max_columns = max(1, available_width // (card_width + 16))
        
        for i, build in enumerate(builds):
            row = i // max_columns
            col = i % max_columns
            
            card = PoE2UltimateCard(build, self.theme)
            card.build_selected.connect(self.on_build_selected)
            card.detail_requested.connect(self.show_build_details)
            card.export_requested.connect(self.export_build)
            
            self.results_layout.addWidget(card, row, col)
        
        self.log_message(f"显示构筑卡片: {len(builds)} 个，{max_columns} 列布局", "debug", "system")
    
    def clear_results(self):
        """清空结果"""
        for i in reversed(range(self.results_layout.count())):
            item = self.results_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), PoE2UltimateCard):
                item.widget().setParent(None)
    
    def on_build_selected(self, build):
        """处理构筑选择"""
        self.log_message(f"用户选择构筑: {build.name}", "info", "user_action")
        
        # 这里可以添加选择构筑后的逻辑
        QMessageBox.information(self, "构筑已选择", f"已选择构筑: {build.name}\n\n这里可以添加更多操作，如保存到收藏夹等。")
    
    def show_build_details(self, build):
        """显示构筑详情"""
        self.log_message(f"显示构筑详情: {build.name}", "info", "user_action")
        
        from poe2_professional_gui import PoE2BuildDetailDialog
        dialog = PoE2BuildDetailDialog(build, self.theme, self)
        dialog.exec()
    
    def export_build(self, build):
        """导出构筑"""
        try:
            if not hasattr(build, 'pob2_code') or not build.pob2_code:
                self.log_message(f"构筑 {build.name} 没有PoB2代码", "warning", "user_action")
                QMessageBox.warning(self, "导出失败", "此构筑没有PoB2导入代码")
                return
            
            # 创建PoB2链接
            encoded_code = quote(build.pob2_code)
            pob2_url = f"https://pob.party/share/{encoded_code}"
            
            # 打开浏览器
            webbrowser.open(pob2_url)
            
            # 复制到剪贴板
            clipboard = QApplication.clipboard()
            clipboard.setText(pob2_url)
            
            self.log_message(f"导出构筑 {build.name} 到PoB2: {pob2_url[:50]}...", "success", "user_action")
            
            # 显示成功消息
            QMessageBox.information(self, "导出成功", f"PoB2链接已打开并复制到剪贴板!\n\n{pob2_url}")
            
        except Exception as e:
            error_msg = str(e)
            self.log_message(f"导出失败: {error_msg}", "error", "system")
            QMessageBox.critical(self, "导出失败", f"导出PoB2时发生错误:\n{error_msg}")
    
    def toggle_console(self):
        """切换控制台显示"""
        if self.console_dock.isVisible():
            self.console_dock.hide()
            self.log_message("控制台已隐藏", "debug", "system")
        else:
            self.console_dock.show()
            self.log_message("控制台已显示", "debug", "system")
    
    def clear_console(self):
        """清空控制台"""
        self.console.clear()
        self.log_message("控制台已清空", "info", "system")
    
    def export_logs(self):
        """导出日志"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "导出日志", 
            f"poe2_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 
            "文本文件 (*.txt)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("PoE2 Build Generator - 日志导出\n")
                    f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for entry in self.console.log_buffer:
                        f.write(f"[{entry['timestamp']}] [{entry['level'].upper()}] [{entry['category'].upper()}] {entry['message']}\n")
                
                self.log_message(f"日志已导出到: {filename}", "success", "system")
                QMessageBox.information(self, "导出成功", f"日志已成功导出到:\n{filename}")
                
            except Exception as e:
                error_msg = str(e)
                self.log_message(f"日志导出失败: {error_msg}", "error", "system")
                QMessageBox.critical(self, "导出失败", f"日志导出失败:\n{error_msg}")
    
    def import_build(self):
        """导入构筑"""
        self.log_message("用户请求导入构筑", "info", "user_action")
        # TODO: 实现构筑导入功能
        QMessageBox.information(self, "功能开发中", "构筑导入功能正在开发中...")
    
    def export_all_builds(self):
        """导出所有构筑"""
        if not self.current_builds:
            QMessageBox.warning(self, "无构筑", "没有可导出的构筑")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "导出所有构筑", 
            f"poe2_builds_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
            "JSON文件 (*.json)"
        )
        
        if filename:
            try:
                builds_data = []
                for build in self.current_builds:
                    builds_data.append({
                        "name": build.name,
                        "character_class": build.character_class.value,
                        "ascendancy": build.ascendancy.value if build.ascendancy else None,
                        "level": build.level,
                        "main_skill": build.main_skill_gem,
                        "support_gems": build.support_gems,
                        "estimated_cost": build.estimated_cost,
                        "pob2_code": getattr(build, 'pob2_code', None),
                        "stats": {
                            "total_dps": build.stats.total_dps,
                            "effective_health_pool": build.stats.effective_health_pool,
                            "life": build.stats.life,
                            "energy_shield": build.stats.energy_shield,
                            "resistances": {
                                "fire": build.stats.fire_resistance,
                                "cold": build.stats.cold_resistance,
                                "lightning": build.stats.lightning_resistance,
                                "chaos": build.stats.chaos_resistance
                            }
                        } if build.stats else None,
                        "notes": build.notes
                    })
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(builds_data, f, ensure_ascii=False, indent=2)
                
                self.log_message(f"已导出 {len(builds_data)} 个构筑到: {filename}", "success", "user_action")
                QMessageBox.information(self, "导出成功", f"已成功导出 {len(builds_data)} 个构筑到:\n{filename}")
                
            except Exception as e:
                error_msg = str(e)
                self.log_message(f"构筑导出失败: {error_msg}", "error", "system")
                QMessageBox.critical(self, "导出失败", f"构筑导出失败:\n{error_msg}")
    
    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h2>PoE2 Build Generator - Ultimate Professional Edition</h2>
        <p>版本: 3.0.0</p>
        <p>一个专业的Path of Exile 2构筑生成器</p>
        
        <h3>主要特性:</h3>
        <ul>
        <li>🤖 AI驱动的构筑推荐系统</li>
        <li>🎯 基于用户偏好的智能匹配</li>
        <li>📊 真实的DPS和生存能力计算</li>
        <li>🔗 完整的PoB2集成支持</li>
        <li>🖥️ 网页风格的开发者控制台</li>
        <li>💎 专业的PoE2主题界面</li>
        <li>📈 详细的构筑统计和分析</li>
        </ul>
        
        <h3>快捷键:</h3>
        <ul>
        <li>F12: 切换开发者控制台</li>
        <li>Ctrl+G: 生成构筑</li>
        <li>Ctrl+L: 清空控制台</li>
        </ul>
        """
        QMessageBox.about(self, "关于", about_text)
    
    def update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(current_time)
    
    def log_message(self, message: str, level: str = "info", category: str = "system"):
        """记录日志消息"""
        if hasattr(self, 'console'):
            self.console.log(message, level, category)
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        
        # 重新排列构筑卡片
        if hasattr(self, 'current_builds') and self.current_builds:
            self.clear_results()
            self.display_builds(self.current_builds)
    
    def closeEvent(self, event):
        """关闭事件"""
        self.log_message("应用程序即将关闭", "info", "system")
        
        # 停止定时器
        if hasattr(self, 'time_timer'):
            self.time_timer.stop()
        
        # 停止后台线程
        if hasattr(self, 'generation_thread') and self.generation_thread.isRunning():
            self.generation_thread.terminate()
            self.generation_thread.wait()
        
        if hasattr(self, 'init_thread') and self.init_thread.isRunning():
            self.init_thread.terminate()
            self.init_thread.wait()
        
        event.accept()


class InitializationThread(QThread):
    """初始化线程"""
    success = pyqtSignal()
    error = pyqtSignal(str)
    orchestrator_ready = pyqtSignal(object)
    
    def run(self):
        """运行初始化"""
        try:
            orchestrator = PoE2AIOrchestrator()
            
            # 创建事件循环
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            
            # 初始化
            loop.run_until_complete(orchestrator.initialize())
            
            self.orchestrator_ready.emit(orchestrator)
            self.success.emit()
            
        except Exception as e:
            self.error.emit(str(e))


class BuildGenerationThread(QThread):
    """构筑生成线程"""
    builds_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, character_class, ascendancy, build_goal, max_budget, 
                 min_dps, min_ehp, require_resistance_cap, orchestrator):
        super().__init__()
        self.character_class = character_class
        self.ascendancy = ascendancy
        self.build_goal = build_goal
        self.max_budget = max_budget
        self.min_dps = min_dps
        self.min_ehp = min_ehp
        self.require_resistance_cap = require_resistance_cap
        self.orchestrator = orchestrator
    
    def run(self):
        """执行构筑生成"""
        try:
            # 创建用户请求
            request = UserRequest(
                character_class=self.character_class,
                ascendancy=self.ascendancy,
                build_goal=self.build_goal,
                max_budget=self.max_budget,
                min_dps=self.min_dps,
                min_ehp=self.min_ehp,
                require_resistance_cap=self.require_resistance_cap
            )
            
            # 创建事件循环
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            
            # 生成推荐
            result = loop.run_until_complete(
                self.orchestrator.generate_build_recommendations(request)
            )
            
            # 发出成功信号
            self.builds_ready.emit(result.builds)
            
        except Exception as e:
            # 发出错误信号
            self.error_occurred.emit(str(e))


def main():
    """主函数"""
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("PoE2 Build Generator Ultimate")
        app.setApplicationVersion("3.0.0")
        
        # 设置应用图标（如果有的话）
        # app.setWindowIcon(QIcon("icon.png"))
        
        # 创建主窗口
        window = PoE2UltimateGUI()
        window.show()
        
        # 启动信息
        try:
            print("=" * 80)
            print("PoE2 Build Generator - Ultimate Professional Edition")
            print("=" * 80)
            print("终极专业版PoE2构筑生成器已启动")
            print()
            print("主要功能:")
            print("  • 网页风格F12开发者控制台 - 完整日志系统")
            print("  • 智能AI构筑推荐 - 基于真实数据和用户偏好")
            print("  • 专业构筑卡片界面 - 详细属性展示和交互")
            print("  • 完整PoB2集成 - 一键导出和浏览器打开")
            print("  • 响应式网格布局 - 自适应屏幕尺寸")
            print("  • 高级过滤和搜索 - 精确匹配用户需求")
            print()
            print("快捷键:")
            print("  F12: 切换开发者控制台")
            print("  Ctrl+G: 快速生成构筑")
            print("  Ctrl+L: 清空控制台")
            print("=" * 80)
        except UnicodeEncodeError:
            print("=" * 80)
            print("PoE2 Build Generator - Ultimate Professional Edition")
            print("=" * 80)
            print("Ultimate Professional PoE2 Build Generator Started")
            print("All features loaded successfully")
            print("=" * 80)
        
        return app.exec()
        
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())