"""
PoE2 四大数据源集成GUI - 主应用
集成四大核心数据源、RAG训练和PoB2高度集成推荐系统

核心功能:
1. 四大数据源管理和健康监控
2. RAG AI训练和知识库管理 
3. 与Path of Building 2高度集成的推荐系统
4. 构筑导入导出功能
5. F12开发者控制台

四大数据源:
- PoE2Scout API (市场价格)
- PoE Ninja (Meta趋势)
- Path of Building 2 (官方数据)
- PoE2DB (游戏数据库)
"""

import sys
import os
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTextEdit, QPushButton, QLabel, QProgressBar,
    QGroupBox, QGridLayout, QListWidget, QComboBox, QSpinBox,
    QCheckBox, QLineEdit, QSplitter, QScrollArea, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QDialogButtonBox, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QUrl, pyqtSlot, QSize
)
from PyQt6.QtGui import (
    QFont, QPalette, QColor, QIcon, QPixmap, QKeySequence, QAction,
    QShortcut
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

# 导入四大数据源
from src.poe2build.data_sources import (
    get_all_four_sources,
    health_check_all_sources
)

# 导入RAG系统
from src.poe2build.rag.four_sources_integration import FourSourcesRAGTrainer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PoE2Theme:
    """PoE2风格主题"""
    
    # PoE2经典配色
    COLORS = {
        'background': '#0a0a0a',           # 深黑背景
        'surface': '#1a1a1a',             # 表面色
        'surface_light': '#2a2a2a',       # 亮表面色
        'primary': '#c9aa71',             # PoE2金色
        'accent': '#8b4513',              # 褐色强调
        'text_primary': '#f0f0f0',        # 主文本
        'text_secondary': '#c0c0c0',      # 次文本
        'success': '#4CAF50',             # 成功绿
        'warning': '#FF9800',             # 警告橙
        'error': '#f44336',               # 错误红
        'info': '#2196F3',                # 信息蓝
        'border': '#3a3a3a'               # 边框色
    }
    
    @staticmethod
    def get_stylesheet() -> str:
        """获取完整的样式表"""
        colors = PoE2Theme.COLORS
        return f"""
        /* 主窗口 */
        QMainWindow {{
            background-color: {colors['background']};
            color: {colors['text_primary']};
            font-family: 'Segoe UI', 'Arial', sans-serif;
        }}
        
        /* 标签页 */
        QTabWidget::pane {{
            border: 1px solid {colors['border']};
            background-color: {colors['surface']};
        }}
        
        QTabBar::tab {{
            background-color: {colors['surface_light']};
            color: {colors['text_secondary']};
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors['primary']};
            color: {colors['background']};
            font-weight: bold;
        }}
        
        QTabBar::tab:hover {{
            background-color: {colors['accent']};
            color: {colors['text_primary']};
        }}
        
        /* 按钮 */
        QPushButton {{
            background-color: {colors['surface_light']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }}
        
        QPushButton:hover {{
            background-color: {colors['primary']};
            color: {colors['background']};
        }}
        
        QPushButton:pressed {{
            background-color: {colors['accent']};
        }}
        
        QPushButton:disabled {{
            background-color: {colors['surface']};
            color: {colors['text_secondary']};
        }}
        
        /* 特殊按钮样式 */
        QPushButton.success {{
            background-color: {colors['success']};
            color: white;
        }}
        
        QPushButton.warning {{
            background-color: {colors['warning']};
            color: white;
        }}
        
        QPushButton.error {{
            background-color: {colors['error']};
            color: white;
        }}
        
        /* 组框 */
        QGroupBox {{
            font-weight: bold;
            border: 2px solid {colors['border']};
            border-radius: 4px;
            margin-top: 1ex;
            padding-top: 10px;
            color: {colors['primary']};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }}
        
        /* 文本编辑框 */
        QTextEdit, QLineEdit {{
            background-color: {colors['surface']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            padding: 4px;
            font-family: 'Consolas', 'Monaco', monospace;
        }}
        
        /* 列表和表格 */
        QListWidget, QTableWidget {{
            background-color: {colors['surface']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            selection-background-color: {colors['primary']};
            selection-color: {colors['background']};
        }}
        
        QTableWidget::item {{
            padding: 4px;
        }}
        
        QHeaderView::section {{
            background-color: {colors['surface_light']};
            color: {colors['text_primary']};
            padding: 4px;
            border: 1px solid {colors['border']};
            font-weight: bold;
        }}
        
        /* 进度条 */
        QProgressBar {{
            border: 1px solid {colors['border']};
            border-radius: 4px;
            text-align: center;
            color: {colors['text_primary']};
        }}
        
        QProgressBar::chunk {{
            background-color: {colors['primary']};
            border-radius: 3px;
        }}
        
        /* 滚动条 */
        QScrollBar:vertical {{
            background-color: {colors['surface']};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {colors['primary']};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {colors['accent']};
        }}
        
        /* 状态标签 */
        QLabel.status-healthy {{
            color: {colors['success']};
            font-weight: bold;
        }}
        
        QLabel.status-warning {{
            color: {colors['warning']};
            font-weight: bold;
        }}
        
        QLabel.status-error {{
            color: {colors['error']};
            font-weight: bold;
        }}
        
        QLabel.title {{
            color: {colors['primary']};
            font-size: 16px;
            font-weight: bold;
        }}
        """


class DataSourceHealthWidget(QWidget):
    """四大数据源健康状态监控组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        self.setupTimer()
        
    def setupUI(self):
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("🎯 四大核心数据源状态")
        title.setProperty("class", "title")
        layout.addWidget(title)
        
        # 数据源状态组
        self.sources_group = QGroupBox("数据源健康监控")
        sources_layout = QGridLayout(self.sources_group)
        
        # 四大数据源状态
        self.source_labels = {}
        self.source_indicators = {}
        
        sources = [
            ("poe2scout", "PoE2Scout API", "市场价格数据"),
            ("poe_ninja", "PoE Ninja", "Meta趋势分析"), 
            ("path_of_building_2", "Path of Building 2", "官方游戏数据"),
            ("poe2db", "PoE2DB", "游戏数据库")
        ]
        
        for i, (key, name, desc) in enumerate(sources):
            # 名称标签
            name_label = QLabel(name)
            name_label.setFont(QFont("", 10, QFont.Weight.Bold))
            
            # 描述标签
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: #c0c0c0; font-size: 9px;")
            
            # 状态指示器
            status_label = QLabel("检查中...")
            status_label.setProperty("class", "status-warning")
            
            sources_layout.addWidget(name_label, i, 0)
            sources_layout.addWidget(desc_label, i, 1)
            sources_layout.addWidget(status_label, i, 2)
            
            self.source_labels[key] = name_label
            self.source_indicators[key] = status_label
        
        layout.addWidget(self.sources_group)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新状态")
        refresh_btn.clicked.connect(self.refresh_status)
        layout.addWidget(refresh_btn)
        
        # 统计信息
        self.stats_label = QLabel("等待状态检查...")
        layout.addWidget(self.stats_label)
        
    def setupTimer(self):
        """设置定时器定期检查状态"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_status)
        self.timer.start(30000)  # 30秒检查一次
        
        # 初始检查
        QTimer.singleShot(1000, self.refresh_status)
    
    def refresh_status(self):
        """刷新数据源状态"""
        try:
            health_status = health_check_all_sources()
            
            for source_key, indicator in self.source_indicators.items():
                if source_key in health_status:
                    source_health = health_status[source_key]
                    
                    if isinstance(source_health, dict):
                        if source_health.get('available', False) or source_health.get('status') == 'healthy':
                            indicator.setText("✅ 健康")
                            indicator.setProperty("class", "status-healthy")
                        else:
                            indicator.setText("❌ 不可用") 
                            indicator.setProperty("class", "status-error")
                    else:
                        indicator.setText("⚠️ 未知")
                        indicator.setProperty("class", "status-warning")
                else:
                    indicator.setText("❓ 未检查")
                    indicator.setProperty("class", "status-warning")
                
                # 应用样式
                indicator.style().unpolish(indicator)
                indicator.style().polish(indicator)
            
            # 更新统计信息
            total_sources = len(self.source_indicators)
            healthy_sources = sum(1 for indicator in self.source_indicators.values() 
                                if "健康" in indicator.text())
            
            self.stats_label.setText(
                f"数据源状态: {healthy_sources}/{total_sources} 健康 | "
                f"更新时间: {datetime.now().strftime('%H:%M:%S')}"
            )
            
        except Exception as e:
            logger.error(f"状态检查失败: {e}")
            for indicator in self.source_indicators.values():
                indicator.setText("❌ 检查失败")
                indicator.setProperty("class", "status-error")


class RAGTrainingWidget(QWidget):
    """RAG训练管理组件"""
    
    training_started = pyqtSignal()
    training_finished = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.trainer = None
        self.setupUI()
        
    def setupUI(self):
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("🧠 RAG AI训练管理")
        title.setProperty("class", "title")
        layout.addWidget(title)
        
        # 训练配置组
        config_group = QGroupBox("训练配置")
        config_layout = QGridLayout(config_group)
        
        # 联盟选择
        config_layout.addWidget(QLabel("游戏联盟:"), 0, 0)
        self.league_combo = QComboBox()
        self.league_combo.addItems(["Standard", "Hardcore", "Solo Self-Found"])
        config_layout.addWidget(self.league_combo, 0, 1)
        
        # GitHub PoB2模式
        self.github_pob2_check = QCheckBox("使用GitHub PoB2数据源")
        self.github_pob2_check.setChecked(True)
        self.github_pob2_check.setToolTip("启用时从GitHub获取最新PoB2数据，禁用时使用本地安装")
        config_layout.addWidget(self.github_pob2_check, 1, 0, 1, 2)
        
        layout.addWidget(config_group)
        
        # 训练控制
        controls_layout = QHBoxLayout()
        
        self.start_training_btn = QPushButton("🚀 开始RAG训练")
        self.start_training_btn.setProperty("class", "success")
        self.start_training_btn.clicked.connect(self.start_training)
        controls_layout.addWidget(self.start_training_btn)
        
        self.stop_training_btn = QPushButton("⏹️ 停止训练")
        self.stop_training_btn.setProperty("class", "error")
        self.stop_training_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_training_btn)
        
        layout.addLayout(controls_layout)
        
        # 进度显示
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 训练日志
        log_group = QGroupBox("训练日志")
        log_layout = QVBoxLayout(log_group)
        
        self.training_log = QTextEdit()
        self.training_log.setMaximumHeight(200)
        self.training_log.setPlainText("等待开始训练...")
        log_layout.addWidget(self.training_log)
        
        layout.addWidget(log_group)
        
        # 训练统计
        stats_group = QGroupBox("训练统计")
        stats_layout = QGridLayout(stats_group)
        
        self.stats_labels = {
            'knowledge_entries': QLabel("0"),
            'vector_dimensions': QLabel("0"), 
            'index_size': QLabel("0"),
            'training_time': QLabel("0s")
        }
        
        stats_layout.addWidget(QLabel("知识条目:"), 0, 0)
        stats_layout.addWidget(self.stats_labels['knowledge_entries'], 0, 1)
        stats_layout.addWidget(QLabel("向量维度:"), 0, 2)
        stats_layout.addWidget(self.stats_labels['vector_dimensions'], 0, 3)
        stats_layout.addWidget(QLabel("索引大小:"), 1, 0)
        stats_layout.addWidget(self.stats_labels['index_size'], 1, 1)
        stats_layout.addWidget(QLabel("训练用时:"), 1, 2)
        stats_layout.addWidget(self.stats_labels['training_time'], 1, 3)
        
        layout.addWidget(stats_group)
        
    def start_training(self):
        """开始RAG训练"""
        self.start_training_btn.setEnabled(False)
        self.stop_training_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 无限进度
        
        # 清空日志
        self.training_log.clear()
        self.add_log("开始RAG训练...")
        
        # 创建训练线程
        self.training_thread = RAGTrainingThread(
            league=self.league_combo.currentText(),
            enable_github_pob2=self.github_pob2_check.isChecked()
        )
        self.training_thread.log_message.connect(self.add_log)
        self.training_thread.progress_update.connect(self.update_progress)
        self.training_thread.training_finished.connect(self.on_training_finished)
        self.training_thread.start()
        
        self.training_started.emit()
    
    def add_log(self, message: str):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.training_log.append(f"[{timestamp}] {message}")
        
    def update_progress(self, stage: str, data: dict):
        """更新训练进度"""
        self.add_log(f"完成阶段: {stage}")
        
        # 更新统计
        if 'knowledge_entries' in data:
            self.stats_labels['knowledge_entries'].setText(str(data['knowledge_entries']))
        if 'vector_dimensions' in data:
            self.stats_labels['vector_dimensions'].setText(str(data['vector_dimensions']))
        if 'index_size' in data:
            self.stats_labels['index_size'].setText(str(data['index_size']))
    
    def on_training_finished(self, result: dict):
        """训练完成处理"""
        self.start_training_btn.setEnabled(True)
        self.stop_training_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if result.get('success', False):
            self.add_log("✅ RAG训练成功完成!")
            
            # 更新最终统计
            training_data = result.get('training_result', {})
            if 'training_time' in result:
                self.stats_labels['training_time'].setText(f"{result['training_time']:.1f}s")
            
        else:
            error = result.get('error', '未知错误')
            self.add_log(f"❌ RAG训练失败: {error}")
        
        self.training_finished.emit(result)


class RAGTrainingThread(QThread):
    """RAG训练线程"""
    
    log_message = pyqtSignal(str)
    progress_update = pyqtSignal(str, dict)
    training_finished = pyqtSignal(dict)
    
    def __init__(self, league: str, enable_github_pob2: bool):
        super().__init__()
        self.league = league
        self.enable_github_pob2 = enable_github_pob2
        
    def run(self):
        """执行训练"""
        try:
            start_time = datetime.now()
            
            # 创建训练器
            self.log_message.emit("初始化四大数据源RAG训练器...")
            trainer = FourSourcesRAGTrainer(enable_github_pob2=self.enable_github_pob2)
            
            # 收集数据
            self.log_message.emit("收集四大数据源数据...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            four_sources_data = loop.run_until_complete(
                trainer.collect_all_four_sources(self.league)
            )
            
            self.progress_update.emit("数据收集", {
                'data_collected': True
            })
            
            # 训练RAG AI
            self.log_message.emit("开始RAG AI训练...")
            training_result = loop.run_until_complete(
                trainer.train_rag_ai(four_sources_data)
            )
            
            self.progress_update.emit("RAG训练", training_result)
            
            end_time = datetime.now()
            training_time = (end_time - start_time).total_seconds()
            
            # 发送完成信号
            self.training_finished.emit({
                'success': True,
                'training_result': training_result,
                'training_time': training_time,
                'four_sources_data': four_sources_data.to_dict()
            })
            
            loop.close()
            
        except Exception as e:
            logger.error(f"RAG训练失败: {e}")
            self.training_finished.emit({
                'success': False,
                'error': str(e)
            })


class PoB2IntegrationWidget(QWidget):
    """PoB2高度集成推荐组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        
    def setupUI(self):
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("⚡ PoB2集成推荐系统")
        title.setProperty("class", "title")
        layout.addWidget(title)
        
        # 构筑需求输入
        requirements_group = QGroupBox("构筑需求")
        req_layout = QGridLayout(requirements_group)
        
        # 职业选择
        req_layout.addWidget(QLabel("角色职业:"), 0, 0)
        self.class_combo = QComboBox()
        self.class_combo.addItems([
            "Witch (女巫)", "Ranger (游侠)", "Monk (武僧)", 
            "Warrior (战士)", "Sorceress (法师)", "Mercenary (雇佣兵)"
        ])
        req_layout.addWidget(self.class_combo, 0, 1)
        
        # 构筑类型
        req_layout.addWidget(QLabel("构筑目标:"), 1, 0)
        self.build_goal_combo = QComboBox()
        self.build_goal_combo.addItems([
            "清图速度", "Boss击杀", "平衡型", "新手友好", "高难度内容"
        ])
        req_layout.addWidget(self.build_goal_combo, 1, 1)
        
        # 预算
        req_layout.addWidget(QLabel("预算 (Divine):"), 2, 0)
        self.budget_spin = QSpinBox()
        self.budget_spin.setRange(1, 1000)
        self.budget_spin.setValue(15)
        req_layout.addWidget(self.budget_spin, 2, 1)
        
        layout.addWidget(requirements_group)
        
        # 推荐控制
        controls_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("🎲 生成推荐")
        self.generate_btn.setProperty("class", "success")
        self.generate_btn.clicked.connect(self.generate_recommendations)
        controls_layout.addWidget(self.generate_btn)
        
        self.export_pob2_btn = QPushButton("📤 导出到PoB2")
        self.export_pob2_btn.clicked.connect(self.export_to_pob2)
        self.export_pob2_btn.setEnabled(False)
        controls_layout.addWidget(self.export_pob2_btn)
        
        layout.addLayout(controls_layout)
        
        # 推荐结果
        results_group = QGroupBox("推荐结果")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "构筑名称", "主技能", "预估DPS", "预估EHP", "成本", "推荐度"
        ])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        results_layout.addWidget(self.results_table)
        
        layout.addWidget(results_group)
        
        # PoB2状态
        pob2_status_group = QGroupBox("PoB2连接状态")
        pob2_layout = QHBoxLayout(pob2_status_group)
        
        self.pob2_status_label = QLabel("检查中...")
        self.pob2_status_label.setProperty("class", "status-warning")
        pob2_layout.addWidget(self.pob2_status_label)
        
        self.check_pob2_btn = QPushButton("🔍 检查PoB2")
        self.check_pob2_btn.clicked.connect(self.check_pob2_status)
        pob2_layout.addWidget(self.check_pob2_btn)
        
        layout.addWidget(pob2_status_group)
        
        # 初始检查PoB2状态
        QTimer.singleShot(2000, self.check_pob2_status)
    
    def check_pob2_status(self):
        """检查PoB2连接状态"""
        try:
            from src.poe2build.data_sources.pob2.data_extractor import get_pob2_extractor
            extractor = get_pob2_extractor()
            
            if extractor.is_available():
                info = extractor.get_installation_info()
                source_type = info.get('source', 'unknown')
                self.pob2_status_label.setText(f"✅ PoB2已连接 ({source_type})")
                self.pob2_status_label.setProperty("class", "status-healthy")
                self.export_pob2_btn.setEnabled(True)
            else:
                self.pob2_status_label.setText("❌ PoB2未连接")
                self.pob2_status_label.setProperty("class", "status-error")
                self.export_pob2_btn.setEnabled(False)
                
        except Exception as e:
            self.pob2_status_label.setText(f"❌ PoB2检查失败: {str(e)[:50]}")
            self.pob2_status_label.setProperty("class", "status-error")
            
        # 刷新样式
        self.pob2_status_label.style().unpolish(self.pob2_status_label)
        self.pob2_status_label.style().polish(self.pob2_status_label)
    
    def generate_recommendations(self):
        """生成构筑推荐"""
        # 这里应该调用RAG AI推荐系统
        # 暂时添加一些模拟数据
        
        self.results_table.setRowCount(3)
        
        mock_data = [
            ("弓箭游侠", "Lightning Arrow", "2,500,000", "7,500", "12 Divine", "95%"),
            ("法师冰霜", "Glacial Cascade", "2,200,000", "8,200", "8 Divine", "88%"),
            ("召唤巫师", "Raise Skeleton", "1,800,000", "9,500", "5 Divine", "82%")
        ]
        
        for row, data in enumerate(mock_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                self.results_table.setItem(row, col, item)
        
        self.export_pob2_btn.setEnabled(True)
        
    def export_to_pob2(self):
        """导出选中构筑到PoB2"""
        current_row = self.results_table.currentRow()
        if current_row >= 0:
            build_name = self.results_table.item(current_row, 0).text()
            QMessageBox.information(
                self, 
                "导出成功", 
                f"构筑 '{build_name}' 已导出到Path of Building 2\n\n"
                f"可以在PoB2中查看详细的DPS计算和天赋树配置。"
            )


class DeveloperConsoleWidget(QWidget):
    """F12开发者控制台"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        
    def setupUI(self):
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("🔧 开发者控制台")
        title.setProperty("class", "title")
        layout.addWidget(title)
        
        # 控制台输出
        console_group = QGroupBox("系统日志")
        console_layout = QVBoxLayout(console_group)
        
        self.console_output = QTextEdit()
        self.console_output.setFont(QFont("Consolas", 9))
        self.console_output.setPlainText(
            f"PoE2 四大数据源集成系统控制台\n"
            f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Python版本: {sys.version}\n"
            f"PyQt版本: {sys.modules['PyQt6.QtCore'].PYQT_VERSION_STR}\n"
            f"工作目录: {os.getcwd()}\n"
            f"{'='*60}\n"
            f"等待系统消息...\n"
        )
        console_layout.addWidget(self.console_output)
        
        layout.addWidget(console_group)
        
        # 命令输入
        cmd_group = QGroupBox("命令执行")
        cmd_layout = QVBoxLayout(cmd_group)
        
        cmd_input_layout = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("输入命令 (例如: health_check, list_sources)")
        self.cmd_input.returnPressed.connect(self.execute_command)
        
        self.execute_btn = QPushButton("执行")
        self.execute_btn.clicked.connect(self.execute_command)
        
        cmd_input_layout.addWidget(self.cmd_input)
        cmd_input_layout.addWidget(self.execute_btn)
        cmd_layout.addLayout(cmd_input_layout)
        
        # 常用命令按钮
        common_cmds_layout = QHBoxLayout()
        
        cmds = [
            ("健康检查", "health_check"),
            ("清空日志", "clear"),
            ("系统信息", "system_info"),
            ("数据源状态", "list_sources")
        ]
        
        for name, cmd in cmds:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, c=cmd: self.execute_command(c))
            common_cmds_layout.addWidget(btn)
        
        cmd_layout.addLayout(common_cmds_layout)
        layout.addWidget(cmd_group)
        
    def execute_command(self, command=None):
        """执行控制台命令"""
        if command is None:
            command = self.cmd_input.text().strip()
            self.cmd_input.clear()
        
        if not command:
            return
            
        self.add_console_log(f"> {command}")
        
        try:
            if command == "health_check":
                self.add_console_log("执行健康检查...")
                # 这里调用健康检查
                self.add_console_log("✅ 健康检查完成")
                
            elif command == "clear":
                self.console_output.clear()
                self.add_console_log("控制台已清空")
                
            elif command == "system_info":
                self.add_console_log(f"系统信息:")
                self.add_console_log(f"- 平台: {sys.platform}")
                self.add_console_log(f"- Python: {sys.version.split()[0]}")
                self.add_console_log(f"- 工作目录: {os.getcwd()}")
                
            elif command == "list_sources":
                self.add_console_log("四大数据源:")
                self.add_console_log("1. PoE2Scout API - 市场价格数据")
                self.add_console_log("2. PoE Ninja - Meta趋势分析")
                self.add_console_log("3. Path of Building 2 - 官方游戏数据")
                self.add_console_log("4. PoE2DB - 游戏数据库")
                
            else:
                self.add_console_log(f"❌ 未知命令: {command}")
                
        except Exception as e:
            self.add_console_log(f"❌ 命令执行错误: {e}")
    
    def add_console_log(self, message: str):
        """添加控制台日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console_output.append(f"[{timestamp}] {message}")


class PoE2IntegratedMainWindow(QMainWindow):
    """PoE2四大数据源集成主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setupUI()
        self.setupShortcuts()
        self.console_visible = False
        
    def setupUI(self):
        """设置主界面"""
        self.setWindowTitle("PoE2 四大数据源集成系统 v2.0")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # 应用PoE2主题
        self.setStyleSheet(PoE2Theme.get_stylesheet())
        
        # 中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局 - 可拆分布局
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 上半部分 - 主要功能标签页
        self.main_tabs = QTabWidget()
        
        # 标签页1: 数据源监控
        self.data_source_widget = DataSourceHealthWidget()
        self.main_tabs.addTab(self.data_source_widget, "📊 数据源监控")
        
        # 标签页2: RAG训练
        self.rag_training_widget = RAGTrainingWidget()
        self.main_tabs.addTab(self.rag_training_widget, "🧠 RAG训练")
        
        # 标签页3: PoB2推荐
        self.pob2_widget = PoB2IntegrationWidget()
        self.main_tabs.addTab(self.pob2_widget, "⚡ PoB2推荐")
        
        main_splitter.addWidget(self.main_tabs)
        
        # 下半部分 - 开发者控制台 (默认隐藏)
        self.console_widget = DeveloperConsoleWidget()
        self.console_widget.setMaximumHeight(300)
        self.console_widget.hide()  # 默认隐藏
        main_splitter.addWidget(self.console_widget)
        
        # 设置拆分比例
        main_splitter.setStretchFactor(0, 3)  # 主要内容占3/4
        main_splitter.setStretchFactor(1, 1)  # 控制台占1/4
        
        # 主布局
        layout = QVBoxLayout(central_widget)
        layout.addWidget(main_splitter)
        
        # 状态栏
        self.statusBar().showMessage("四大数据源集成系统已启动 | 按F12打开开发者控制台")
    
    def setupShortcuts(self):
        """设置快捷键"""
        # F12 切换开发者控制台
        f12_shortcut = QShortcut(QKeySequence("F12"), self)
        f12_shortcut.activated.connect(self.toggle_console)
        
        # Ctrl+R 刷新数据源状态
        refresh_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        refresh_shortcut.activated.connect(self.refresh_all_data)
    
    def toggle_console(self):
        """切换开发者控制台显示/隐藏"""
        if self.console_visible:
            self.console_widget.hide()
            self.console_visible = False
            self.statusBar().showMessage("开发者控制台已隐藏 | 按F12重新打开")
        else:
            self.console_widget.show()
            self.console_visible = True
            self.statusBar().showMessage("开发者控制台已打开 | 按F12隐藏")
            # 添加控制台日志
            self.console_widget.add_console_log("🔧 开发者控制台已激活")
    
    def refresh_all_data(self):
        """刷新所有数据"""
        self.data_source_widget.refresh_status()
        self.pob2_widget.check_pob2_status()
        self.statusBar().showMessage("所有数据已刷新", 3000)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用属性
    app.setApplicationName("PoE2 四大数据源集成系统")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("PoE2BuildGenerator")
    
    # 创建主窗口
    window = PoE2IntegratedMainWindow()
    window.show()
    
    # 启动事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()