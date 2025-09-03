"""
欢迎页面 - 全新PoB2风格首页界面

参考Path of Building 2设计的专业级PoE2构筑生成器首页，
包含AI推荐展示、PoB2集成状态、构筑历史、市场数据和系统状态等功能模块。
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, 
    QGridLayout, QSpacerItem, QSizePolicy, QScrollArea, QGroupBox,
    QProgressBar, QListWidget, QListWidgetItem, QTabWidget,
    QTextEdit, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QFont, QPixmap, QPainter, QPen, QBrush, QColor, QLinearGradient, QPalette

from ..styles.poe2_theme import PoE2Theme
from ..widgets.poe2_components import PoE2BaseWidget, BuildCard

try:
    from ...models.build import PoE2Build, PoE2BuildStats, PoE2BuildGoal
    from ...models.characters import PoE2CharacterClass, PoE2Ascendancy
except ImportError:
    # 模拟类用于测试
    PoE2Build = None
    PoE2BuildStats = None
    PoE2BuildGoal = None
    PoE2CharacterClass = None
    PoE2Ascendancy = None


class QuickStartCard(PoE2BaseWidget):
    """快速开始卡片组件 - 新手引导和快捷操作"""
    
    start_build_generation = pyqtSignal()
    open_pob2_integration = pyqtSignal()
    view_tutorials = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(280)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题区域
        header_layout = QHBoxLayout()
        
        title = QLabel("快速开始")
        title.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('poe2_gold')};
                font-size: 20px;
                font-weight: 700;
            }}
        """)
        
        subtitle = QLabel("开始您的PoE2构筑之旅")
        subtitle.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_secondary')};
                font-size: 14px;
                margin-top: 4px;
            }}
        """)
        
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        
        # 头部图标
        icon_label = QLabel("⚡")
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 32px;
                color: {self.theme.get_color('poe2_gold')};
            }}
        """)
        
        header_layout.addWidget(title_widget)
        header_layout.addStretch()
        header_layout.addWidget(icon_label)
        
        # 快捷操作按钮
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(12)
        
        # 主要操作按钮
        generate_btn = QPushButton("🤖 开始生成构筑")
        generate_btn.setProperty("poe2_style", "accent")
        generate_btn.setMinimumHeight(45)
        generate_btn.clicked.connect(self.start_build_generation)
        generate_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 16px;
                font-weight: 600;
                padding: 12px 24px;
            }}
        """)
        
        # 辅助操作按钮
        secondary_layout = QHBoxLayout()
        secondary_layout.setSpacing(8)
        
        pob2_btn = QPushButton("🔗 PoB2集成")
        pob2_btn.setProperty("poe2_style", "primary")
        pob2_btn.setMinimumHeight(35)
        pob2_btn.clicked.connect(self.open_pob2_integration)
        
        tutorial_btn = QPushButton("📚 使用教程")
        tutorial_btn.setProperty("poe2_style", "primary")
        tutorial_btn.setMinimumHeight(35)
        tutorial_btn.clicked.connect(self.view_tutorials)
        
        secondary_layout.addWidget(pob2_btn)
        secondary_layout.addWidget(tutorial_btn)
        
        buttons_layout.addWidget(generate_btn)
        buttons_layout.addLayout(secondary_layout)
        
        # 提示信息
        tip_label = QLabel("💡 提示: 首次使用建议先查看使用教程")
        tip_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_disabled')};
                font-size: 12px;
                padding: 8px;
                background-color: {self.theme.get_color('background_tertiary')};
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 6px;
            }}
        """)
        
        layout.addLayout(header_layout)
        layout.addLayout(buttons_layout)
        layout.addStretch()
        layout.addWidget(tip_label)
        
    def paintEvent(self, event):
        """自定义绘制背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 渐变背景
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(self.theme.get_color('background_secondary')))
        gradient.setColorAt(1, QColor(self.theme.get_color('background_tertiary')))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(self.theme.get_color('poe2_gold')), 2))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)


class AIRecommendationPanel(PoE2BaseWidget):
    """AI推荐展示面板 - 显示热门构筑推荐"""
    
    build_selected = pyqtSignal(object)
    refresh_recommendations = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recommendation_cards = []
        self._setup_ui()
        self._load_sample_recommendations()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 标题栏
        header_layout = QHBoxLayout()
        
        title = QLabel("🎯 AI智能推荐")
        title.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_highlight')};
                font-size: 18px;
                font-weight: 600;
            }}
        """)
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(32, 32)
        refresh_btn.setToolTip("刷新推荐")
        refresh_btn.clicked.connect(self.refresh_recommendations)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 16px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {self.theme.get_color('button_primary_hover')};
                border-color: {self.theme.get_color('poe2_gold')};
            }}
        """)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)
        
        # 推荐构筑展示区域
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.recommendations_layout = QVBoxLayout(scroll_widget)
        self.recommendations_layout.setSpacing(8)
        self.recommendations_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setMaximumHeight(400)
        
        layout.addLayout(header_layout)
        layout.addWidget(scroll_area)
        
    def _load_sample_recommendations(self):
        """加载示例推荐数据"""
        if not PoE2Build or not PoE2BuildStats:
            # 如果模型类不可用，显示占位符
            placeholder = QLabel("AI推荐功能需要完整的数据模型支持")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet(f"color: {self.theme.get_color('text_disabled')};")
            self.recommendations_layout.addWidget(placeholder)
            return
            
        # 创建示例推荐构筑
        sample_builds = [
            {
                'name': '火焰女巫 - 新手友好',
                'class': PoE2CharacterClass.WITCH,
                'ascendancy': None,
                'skill': '火球术',
                'cost': 2.5,
                'popularity': 85,
                'dps': 180000
            },
            {
                'name': '游侠弓箭手 - 清图之王',
                'class': PoE2CharacterClass.RANGER, 
                'ascendancy': None,
                'skill': '分裂箭',
                'cost': 8.0,
                'popularity': 72,
                'dps': 350000
            },
            {
                'name': '战士重击 - Boss终结者',
                'class': PoE2CharacterClass.WARRIOR,
                'ascendancy': None, 
                'skill': '重击',
                'cost': 15.0,
                'popularity': 68,
                'dps': 450000
            }
        ]
        
        for build_data in sample_builds:
            recommendation_item = self._create_recommendation_item(build_data)
            self.recommendations_layout.addWidget(recommendation_item)
            
    def _create_recommendation_item(self, build_data):
        """创建推荐项组件"""
        item_frame = QFrame()
        item_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.get_color('background_secondary')};
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 8px;
                padding: 12px;
            }}
            QFrame:hover {{
                border-color: {self.theme.get_color('poe2_gold')};
                background-color: {self.theme.get_color('background_tertiary')};
            }}
        """)
        item_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(item_frame)
        layout.setSpacing(12)
        
        # 职业图标
        class_icon = QLabel("⚔️" if build_data['class'] == PoE2CharacterClass.WARRIOR else 
                           "🏹" if build_data['class'] == PoE2CharacterClass.RANGER else "🔮")
        class_icon.setFixedSize(40, 40)
        class_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        class_icon.setStyleSheet(f"""
            QLabel {{
                background-color: {self.theme.get_color('background_tertiary')};
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 20px;
                font-size: 20px;
            }}
        """)
        
        # 构筑信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        name_label = QLabel(build_data['name'])
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_primary')};
                font-size: 14px;
                font-weight: 600;
            }}
        """)
        
        details_label = QLabel(f"主技能: {build_data['skill']} | 成本: {build_data['cost']:.1f} Divine")
        details_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_secondary')};
                font-size: 11px;
            }}
        """)
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(details_label)
        
        # 统计信息
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(2)
        
        popularity_label = QLabel(f"流行度: {build_data['popularity']}%")
        popularity_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('poe2_green')};
                font-size: 10px;
                font-weight: 500;
            }}
        """)
        
        dps_label = QLabel(f"DPS: {build_data['dps']:,.0f}")
        dps_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('poe2_red')};
                font-size: 10px;
                font-weight: 500;
            }}
        """)
        
        stats_layout.addWidget(popularity_label)
        stats_layout.addWidget(dps_label)
        
        layout.addWidget(class_icon)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addLayout(stats_layout)
        
        # 添加点击事件
        item_frame.mousePressEvent = lambda event, data=build_data: self._on_recommendation_clicked(data)
        
        return item_frame
        
    def _on_recommendation_clicked(self, build_data):
        """处理推荐项点击"""
        self.build_selected.emit(build_data)


class PoB2StatusPanel(PoE2BaseWidget):
    """PoB2集成状态面板 - 显示Path of Building 2连接状态"""
    
    pob2_configure = pyqtSignal()
    pob2_launch = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pob2_status = 'unknown'  # unknown, connected, disconnected, error
        self._setup_ui()
        self._start_status_check()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 标题
        title = QLabel("🔗 PoB2集成状态")
        title.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_highlight')};
                font-size: 16px;
                font-weight: 600;
            }}
        """)
        
        # 状态显示区域
        status_frame = QFrame()
        status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.get_color('background_secondary')};
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        
        status_layout = QVBoxLayout(status_frame)
        status_layout.setSpacing(8)
        
        # 状态指示器
        indicator_layout = QHBoxLayout()
        
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_disabled')};
                font-size: 16px;
            }}
        """)
        
        self.status_text = QLabel("检测中...")
        self.status_text.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_primary')};
                font-size: 13px;
                font-weight: 500;
            }}
        """)
        
        indicator_layout.addWidget(self.status_indicator)
        indicator_layout.addWidget(self.status_text)
        indicator_layout.addStretch()
        
        # 详细信息
        self.status_details = QLabel("正在扫描Path of Building Community安装...")
        self.status_details.setWordWrap(True)
        self.status_details.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_secondary')};
                font-size: 11px;
                line-height: 1.3;
            }}
        """)
        
        # 操作按钮
        buttons_layout = QHBoxLayout()
        
        self.configure_btn = QPushButton("配置PoB2")
        self.configure_btn.setProperty("poe2_style", "primary")
        self.configure_btn.clicked.connect(self.pob2_configure)
        
        self.launch_btn = QPushButton("启动PoB2")
        self.launch_btn.setProperty("poe2_style", "accent")
        self.launch_btn.clicked.connect(self.pob2_launch)
        self.launch_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.configure_btn)
        buttons_layout.addWidget(self.launch_btn)
        
        status_layout.addLayout(indicator_layout)
        status_layout.addWidget(self.status_details)
        status_layout.addLayout(buttons_layout)
        
        layout.addWidget(title)
        layout.addWidget(status_frame)
        
    def _start_status_check(self):
        """开始状态检查定时器"""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._check_pob2_status)
        self.status_timer.start(3000)  # 每3秒检查一次
        self._check_pob2_status()  # 立即执行一次检查
        
    def _check_pob2_status(self):
        """检查PoB2状态"""
        # 模拟状态检查逻辑
        import random
        statuses = ['connected', 'disconnected', 'error']
        new_status = random.choice(statuses) if hasattr(random, 'choice') else 'connected'
        
        if new_status != self.pob2_status:
            self.pob2_status = new_status
            self._update_status_display()
            
    def _update_status_display(self):
        """更新状态显示"""
        if self.pob2_status == 'connected':
            self.status_indicator.setStyleSheet(f"""
                QLabel {{
                    color: {self.theme.get_color('success')};
                    font-size: 16px;
                }}
            """)
            self.status_text.setText("已连接")
            self.status_details.setText("Path of Building Community已检测到，版本: v2.35.1\n可以使用完整的计算功能和构筑导入导出。")
            self.launch_btn.setEnabled(True)
            
        elif self.pob2_status == 'disconnected':
            self.status_indicator.setStyleSheet(f"""
                QLabel {{
                    color: {self.theme.get_color('warning')};
                    font-size: 16px;
                }}
            """)
            self.status_text.setText("未连接")
            self.status_details.setText("未检测到Path of Building Community安装。\n将使用基础功能，建议安装PoB2以获得最佳体验。")
            self.launch_btn.setEnabled(False)
            
        elif self.pob2_status == 'error':
            self.status_indicator.setStyleSheet(f"""
                QLabel {{
                    color: {self.theme.get_color('error')};
                    font-size: 16px;
                }}
            """)
            self.status_text.setText("连接错误")
            self.status_details.setText("检测到PoB2但连接失败，可能是权限问题或版本不兼容。\n请检查安装并重新配置。")
            self.launch_btn.setEnabled(False)


class RecentBuildsPanel(PoE2BaseWidget):
    """最近构筑历史面板 - 显示用户最近生成的构筑"""
    
    build_selected = pyqtSignal(object)
    clear_history = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recent_builds = []
        self._setup_ui()
        self._load_sample_history()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 标题栏
        header_layout = QHBoxLayout()
        
        title = QLabel("📚 最近构筑")
        title.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_highlight')};
                font-size: 16px;
                font-weight: 600;
            }}
        """)
        
        clear_btn = QPushButton("🗑️")
        clear_btn.setFixedSize(28, 28)
        clear_btn.setToolTip("清空历史")
        clear_btn.clicked.connect(self.clear_history)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {self.theme.get_color('error')};
                border-color: {self.theme.get_color('error')};
                color: white;
            }}
        """)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(clear_btn)
        
        # 构筑历史列表
        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(200)
        self.history_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.history_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.history_list.itemClicked.connect(self._on_history_item_clicked)
        
        # 空状态提示
        self.empty_label = QLabel("还没有构筑历史\n开始生成您的第一个构筑吧！")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_disabled')};
                font-size: 12px;
                line-height: 1.4;
                padding: 20px;
            }}
        """)
        self.empty_label.setVisible(False)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.history_list)
        layout.addWidget(self.empty_label)
        
    def _load_sample_history(self):
        """加载示例历史数据"""
        sample_history = [
            {'name': '火焰法师构筑', 'date': '2025-01-12 14:30', 'class': '女巫'},
            {'name': '弓箭游侠', 'date': '2025-01-11 19:45', 'class': '游侠'},
            {'name': '重击战士', 'date': '2025-01-10 16:20', 'class': '战士'}
        ]
        
        for build_data in sample_history:
            self._add_history_item(build_data)
            
    def _add_history_item(self, build_data):
        """添加历史项"""
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, build_data)
        
        # 创建自定义项目组件
        item_widget = QWidget()
        layout = QHBoxLayout(item_widget)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        
        # 构筑信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        name_label = QLabel(build_data['name'])
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_primary')};
                font-size: 12px;
                font-weight: 600;
            }}
        """)
        
        meta_label = QLabel(f"{build_data['class']} | {build_data['date']}")
        meta_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_disabled')};
                font-size: 10px;
            }}
        """)
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(meta_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        item.setSizeHint(item_widget.sizeHint())
        self.history_list.addItem(item)
        self.history_list.setItemWidget(item, item_widget)
        
    def _on_history_item_clicked(self, item):
        """处理历史项点击"""
        build_data = item.data(Qt.ItemDataRole.UserRole)
        self.build_selected.emit(build_data)


class MarketSummaryPanel(PoE2BaseWidget):
    """市场数据摘要面板 - 显示当前热门装备价格趋势"""
    
    view_full_market = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_sample_data()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 标题栏
        header_layout = QHBoxLayout()
        
        title = QLabel("📊 市场行情")
        title.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_highlight')};
                font-size: 16px;
                font-weight: 600;
            }}
        """)
        
        view_all_btn = QPushButton("查看全部")
        view_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {self.theme.get_color('border_primary')};
                color: {self.theme.get_color('text_secondary')};
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                border-color: {self.theme.get_color('poe2_gold')};
                color: {self.theme.get_color('text_primary')};
            }}
        """)
        view_all_btn.clicked.connect(self.view_full_market)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(view_all_btn)
        
        # 市场数据表格
        market_frame = QFrame()
        market_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.get_color('background_secondary')};
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        
        market_layout = QVBoxLayout(market_frame)
        market_layout.setSpacing(6)
        
        # 表头
        header_row = self._create_market_header()
        market_layout.addWidget(header_row)
        
        # 数据行容器
        self.market_data_layout = QVBoxLayout()
        self.market_data_layout.setSpacing(4)
        market_layout.addLayout(self.market_data_layout)
        
        layout.addLayout(header_layout)
        layout.addWidget(market_frame)
        
    def _create_market_header(self):
        """创建市场数据表头"""
        header_widget = QWidget()
        layout = QHBoxLayout(header_widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)
        
        headers = ["装备名称", "当前价格", "变化"]
        widths = [120, 80, 60]
        
        for header, width in zip(headers, widths):
            label = QLabel(header)
            label.setFixedWidth(width)
            label.setStyleSheet(f"""
                QLabel {{
                    color: {self.theme.get_color('text_secondary')};
                    font-size: 11px;
                    font-weight: 600;
                    padding: 2px;
                }}
            """)
            layout.addWidget(label)
            
        return header_widget
        
    def _load_sample_data(self):
        """加载示例市场数据"""
        sample_items = [
            {'name': '混沌之爪', 'price': '25.5 Divine', 'change': '+12%', 'trend': 'up'},
            {'name': '骨甲', 'price': '8.2 Divine', 'change': '-5%', 'trend': 'down'},
            {'name': '暴风之弓', 'price': '15.0 Divine', 'change': '+3%', 'trend': 'up'},
            {'name': '法师长袍', 'price': '12.8 Divine', 'change': '-2%', 'trend': 'down'}
        ]
        
        for item in sample_items:
            self._add_market_item(item)
            
    def _add_market_item(self, item_data):
        """添加市场项目"""
        item_widget = QWidget()
        layout = QHBoxLayout(item_widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)
        
        # 装备名称
        name_label = QLabel(item_data['name'])
        name_label.setFixedWidth(120)
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_primary')};
                font-size: 11px;
            }}
        """)
        
        # 当前价格
        price_label = QLabel(item_data['price'])
        price_label.setFixedWidth(80)
        price_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('poe2_gold')};
                font-size: 11px;
                font-weight: 600;
            }}
        """)
        
        # 价格变化
        change_color = self.theme.get_color('success') if item_data['trend'] == 'up' else self.theme.get_color('error')
        change_symbol = "▲" if item_data['trend'] == 'up' else "▼"
        
        change_label = QLabel(f"{change_symbol} {item_data['change']}")
        change_label.setFixedWidth(60)
        change_label.setStyleSheet(f"""
            QLabel {{
                color: {change_color};
                font-size: 10px;
                font-weight: 600;
            }}
        """)
        
        layout.addWidget(name_label)
        layout.addWidget(price_label)
        layout.addWidget(change_label)
        
        self.market_data_layout.addWidget(item_widget)


class SystemStatusPanel(PoE2BaseWidget):
    """系统状态监控面板 - 显示后端服务健康状态"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service_statuses = {
            'ai_engine': 'unknown',
            'poe2_scout': 'unknown', 
            'poe_ninja': 'unknown',
            'pob2_integration': 'unknown'
        }
        self._setup_ui()
        self._start_monitoring()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 标题
        title = QLabel("⚙️ 系统状态")
        title.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_highlight')};
                font-size: 16px;
                font-weight: 600;
            }}
        """)
        
        # 状态项目容器
        status_frame = QFrame()
        status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.get_color('background_secondary')};
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        
        self.status_layout = QVBoxLayout(status_frame)
        self.status_layout.setSpacing(8)
        
        # 创建状态项目
        self.status_widgets = {}
        services = [
            ('ai_engine', 'AI引擎', '智能构筑生成服务'),
            ('poe2_scout', 'PoE2Scout', '市场价格数据接口'),
            ('poe_ninja', 'PoE.Ninja', '构筑流行度数据'),
            ('pob2_integration', 'PoB2集成', 'Path of Building计算')
        ]
        
        for service_id, name, description in services:
            status_item = self._create_status_item(service_id, name, description)
            self.status_widgets[service_id] = status_item
            self.status_layout.addWidget(status_item)
            
        layout.addWidget(title)
        layout.addWidget(status_frame)
        
    def _create_status_item(self, service_id, name, description):
        """创建服务状态项目"""
        item_widget = QWidget()
        layout = QHBoxLayout(item_widget)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)
        
        # 状态指示器
        indicator = QLabel("●")
        indicator.setFixedSize(16, 16)
        indicator.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_disabled')};
                font-size: 12px;
            }}
        """)
        
        # 服务信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_primary')};
                font-size: 12px;
                font-weight: 600;
            }}
        """)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_secondary')};
                font-size: 10px;
            }}
        """)
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(desc_label)
        
        # 状态文本
        status_label = QLabel("检测中...")
        status_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_disabled')};
                font-size: 11px;
                font-weight: 500;
            }}
        """)
        
        layout.addWidget(indicator)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addWidget(status_label)
        
        # 保存引用以便更新
        item_widget.indicator = indicator
        item_widget.status_label = status_label
        
        return item_widget
        
    def _start_monitoring(self):
        """开始监控服务状态"""
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._check_services)
        self.monitor_timer.start(5000)  # 每5秒检查一次
        self._check_services()  # 立即执行一次
        
    def _check_services(self):
        """检查服务状态"""
        # 模拟服务状态检查
        import random
        statuses = ['healthy', 'warning', 'error']
        
        for service_id in self.service_statuses.keys():
            old_status = self.service_statuses[service_id]
            new_status = random.choice(statuses) if hasattr(random, 'choice') else 'healthy'
            
            if new_status != old_status:
                self.service_statuses[service_id] = new_status
                self._update_service_status(service_id, new_status)
                
    def _update_service_status(self, service_id, status):
        """更新服务状态显示"""
        if service_id not in self.status_widgets:
            return
            
        widget = self.status_widgets[service_id]
        
        if status == 'healthy':
            color = self.theme.get_color('success')
            text = "运行正常"
        elif status == 'warning':
            color = self.theme.get_color('warning')
            text = "运行缓慢"
        elif status == 'error':
            color = self.theme.get_color('error')
            text = "服务异常"
        else:
            color = self.theme.get_color('text_disabled')
            text = "未知状态"
            
        widget.indicator.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 12px;
            }}
        """)
        
        widget.status_label.setText(text)
        widget.status_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 11px;
                font-weight: 500;
            }}
        """)


class WelcomePage(QWidget):
    """全新PoB2风格欢迎页面类"""
    
    # 信号定义
    navigate_to = pyqtSignal(str)  # 导航信号
    build_selected = pyqtSignal(object)  # 构筑选择信号
    pob2_action = pyqtSignal(str)  # PoB2操作信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.theme = PoE2Theme()
        self._init_ui()
        self._setup_animations()
    
    def _init_ui(self):
        """初始化用户界面"""
        # 主布局 - 使用分割器实现响应式设计
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        
        # 创建标题区域
        self._create_header(main_layout)
        
        # 创建内容分割器
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧面板
        left_panel = self._create_left_panel()
        content_splitter.addWidget(left_panel)
        
        # 右侧面板
        right_panel = self._create_right_panel()
        content_splitter.addWidget(right_panel)
        
        # 设置分割器比例
        content_splitter.setSizes([450, 550])  # 左侧450，右侧550
        content_splitter.setChildrenCollapsible(False)
        
        main_layout.addWidget(content_splitter)
        
        # 底部状态栏
        self._create_status_bar(main_layout)
        
    def _create_header(self, layout: QVBoxLayout):
        """创建页面标题区域"""
        header_frame = QFrame()
        header_frame.setFixedHeight(100)
        header_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.theme.get_color('background_secondary')},
                    stop:1 {self.theme.get_color('background_tertiary')});
                border: 2px solid {self.theme.get_color('poe2_gold')};
                border-radius: 12px;
                margin-bottom: 8px;
            }}
        """)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(24, 16, 24, 16)
        header_layout.setSpacing(20)
        
        # 左侧标题信息
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        
        # 主标题
        title_label = QLabel("PoE2 构筑生成器")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('poe2_gold')};
                font-size: 28px;
                font-weight: 700;
            }}
        """)
        
        # 副标题
        subtitle_label = QLabel("AI驱动 • PoB2集成 • 专业级构筑工具")
        subtitle_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_primary')};
                font-size: 14px;
                font-weight: 500;
            }}
        """)
        
        # 版本标签
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_disabled')};
                font-size: 11px;
                background-color: {self.theme.get_color('background_tertiary')};
                padding: 2px 6px;
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 10px;
            }}
        """)
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        title_layout.addWidget(version_label)
        
        # 右侧logo区域
        logo_label = QLabel("⚡")
        logo_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('poe2_gold')};
                font-size: 48px;
                border: 2px solid {self.theme.get_color('poe2_gold')};
                border-radius: 30px;
                padding: 8px;
                background-color: {self.theme.get_color('background_primary')};
            }}
        """)
        logo_label.setFixedSize(60, 60)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addWidget(logo_label)
        
        layout.addWidget(header_frame)
    
    def _create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        left_panel = QWidget()
        layout = QVBoxLayout(left_panel)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(16)
        
        # 快速开始卡片
        quick_start = QuickStartCard()
        quick_start.start_build_generation.connect(lambda: self.navigate_to.emit("build_generator"))
        quick_start.open_pob2_integration.connect(lambda: self.pob2_action.emit("configure"))
        quick_start.view_tutorials.connect(lambda: self.navigate_to.emit("help"))
        
        # AI推荐面板
        ai_recommendations = AIRecommendationPanel()
        ai_recommendations.build_selected.connect(self.build_selected)
        ai_recommendations.refresh_recommendations.connect(lambda: print("刷新AI推荐"))
        
        layout.addWidget(quick_start)
        layout.addWidget(ai_recommendations)
        layout.addStretch()
        
        return left_panel
    
    def _create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        right_panel = QWidget()
        layout = QVBoxLayout(right_panel)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(16)
        
        # 使用选项卡组织右侧内容
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {self.theme.get_color('border_primary')};
                background-color: {self.theme.get_color('background_primary')};
                border-radius: 8px;
            }}
            QTabBar::tab {{
                background-color: {self.theme.get_color('background_secondary')};
                color: {self.theme.get_color('text_secondary')};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-size: 12px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background-color: {self.theme.get_color('poe2_gold')};
                color: {self.theme.get_color('background_primary')};
                font-weight: 600;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {self.theme.get_color('background_tertiary')};
                color: {self.theme.get_color('text_primary')};
            }}
        """)
        
        # 状态选项卡
        status_widget = QWidget()
        status_layout = QVBoxLayout(status_widget)
        status_layout.setSpacing(12)
        
        # PoB2状态面板
        pob2_status = PoB2StatusPanel()
        pob2_status.pob2_configure.connect(lambda: self.pob2_action.emit("configure"))
        pob2_status.pob2_launch.connect(lambda: self.pob2_action.emit("launch"))
        
        # 系统状态面板
        system_status = SystemStatusPanel()
        
        status_layout.addWidget(pob2_status)
        status_layout.addWidget(system_status)
        status_layout.addStretch()
        
        # 历史与市场选项卡
        history_market_widget = QWidget()
        hm_layout = QVBoxLayout(history_market_widget)
        hm_layout.setSpacing(12)
        
        # 最近构筑历史
        recent_builds = RecentBuildsPanel()
        recent_builds.build_selected.connect(self.build_selected)
        recent_builds.clear_history.connect(lambda: print("清空构筑历史"))
        
        # 市场数据摘要
        market_summary = MarketSummaryPanel()
        market_summary.view_full_market.connect(lambda: self.navigate_to.emit("market"))
        
        hm_layout.addWidget(recent_builds)
        hm_layout.addWidget(market_summary)
        hm_layout.addStretch()
        
        # 添加选项卡
        tab_widget.addTab(status_widget, "🔧 状态监控")
        tab_widget.addTab(history_market_widget, "📈 历史&市场")
        
        layout.addWidget(tab_widget)
        
        return right_panel
    
    def _create_status_bar(self, layout: QVBoxLayout):
        """创建底部状态栏"""
        status_frame = QFrame()
        status_frame.setFixedHeight(40)
        status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.get_color('background_secondary')};
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 6px;
                margin-top: 8px;
            }}
        """)
        
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(16, 8, 16, 8)
        status_layout.setSpacing(16)
        
        # 状态信息
        status_text = QLabel("就绪 | Path of Building Community集成 | AI引擎在线")
        status_text.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_secondary')};
                font-size: 11px;
            }}
        """)
        
        # 在线指示器
        online_indicator = QLabel("● 在线")
        online_indicator.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('success')};
                font-size: 11px;
                font-weight: 600;
            }}
        """)
        
        status_layout.addWidget(status_text)
        status_layout.addStretch()
        status_layout.addWidget(online_indicator)
        
        layout.addWidget(status_frame)
    
    def _setup_animations(self):
        """设置动画效果"""
        # 淡入动画
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # 启动淡入动画
        QTimer.singleShot(100, self.fade_animation.start)
    
    def resizeEvent(self, event):
        """处理窗口大小变化"""
        super().resizeEvent(event)
        # 可以在这里添加响应式布局调整逻辑