"""
构筑生成器页面

用户输入构筑偏好和生成AI推荐构筑的主要页面。
集成了新的后端服务架构，提供完整的错误处理和状态反馈。
"""

from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, 
    QTextEdit, QSpinBox, QGroupBox, QTabWidget,
    QProgressBar, QScrollArea, QFrame, QSpacerItem, QSizePolicy,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer

from ..styles.poe2_theme import PoE2Theme
from ..services.backend_client import BackendClient
from ..services.data_converter import DataConverter
from ..services.status_manager import StatusManager
from ..widgets.error_handler import ErrorHandler, NotificationType
from ..widgets.pob2_status_widget import PoB2StatusWidget


# 移除旧的WorkerThread类，现在使用BackendClient内置的线程处理


class BuildGeneratorPage(QWidget):
    """构筑生成器页面类"""
    
    # 信号定义
    build_generated = pyqtSignal(dict)  # 构筑生成完成信号
    
    def __init__(self, orchestrator=None, backend_config: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        
        self.orchestrator = orchestrator
        self.theme = PoE2Theme()
        
        # 初始化服务组件
        self.backend_client = BackendClient(backend_config, self)
        self.data_converter = DataConverter()
        self.status_manager = StatusManager(self)
        self.error_handler = ErrorHandler(self)
        
        # 状态追踪
        self.is_generating = False
        self.current_request_id: Optional[str] = None
        
        self._init_ui()
        self._setup_services()
        self._setup_defaults()
    
    def _init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # 页面标题
        title_label = QLabel("AI构筑生成器")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_highlight')};
                font-size: 24px;
                font-weight: 600;
                padding-bottom: 12px;
                border-bottom: 2px solid {self.theme.get_color('poe2_gold')};
            }}
        """)
        main_layout.addWidget(title_label)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_layout.addWidget(scroll_area)
        
        # 滚动内容容器
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setSpacing(20)
        
        # 创建表单区域
        self._create_form_sections(content_layout)
        
        # 创建操作按钮区域
        self._create_action_buttons(content_layout)
        
        # 创建进度条区域
        self._create_progress_section(content_layout)
        
        # 创建PoB2状态区域
        self._create_pob2_status_section(content_layout)
        
        # 创建错误处理区域
        self._create_error_section(content_layout)
    
    def _create_form_sections(self, layout: QVBoxLayout):
        """创建表单区域"""
        # 标签页容器
        tab_widget = QTabWidget()
        
        # 基本设置标签页
        basic_tab = self._create_basic_tab()
        tab_widget.addTab(basic_tab, "基本设置")
        
        # 高级设置标签页
        advanced_tab = self._create_advanced_tab()
        tab_widget.addTab(advanced_tab, "高级设置")
        
        # 预算设置标签页
        budget_tab = self._create_budget_tab()
        tab_widget.addTab(budget_tab, "预算设置")
        
        layout.addWidget(tab_widget)
    
    def _create_basic_tab(self) -> QWidget:
        """创建基本设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # 职业选择分组
        class_group = QGroupBox("职业选择")
        class_layout = QGridLayout(class_group)
        
        # 职业下拉框
        class_label = QLabel("职业:")
        self.class_combo = QComboBox()
        self.class_combo.addItems([
            "选择职业...",
            "女巫 (Witch)", "法师 (Sorceress)", "游侠 (Ranger)",
            "僧侣 (Monk)", "战士 (Warrior)", "女猎手 (Huntress)"
        ])
        class_layout.addWidget(class_label, 0, 0)
        class_layout.addWidget(self.class_combo, 0, 1)
        
        # 专精选择
        ascendancy_label = QLabel("专精:")
        self.ascendancy_combo = QComboBox()
        self.ascendancy_combo.addItem("自动选择最佳专精")
        class_layout.addWidget(ascendancy_label, 1, 0)
        class_layout.addWidget(self.ascendancy_combo, 1, 1)
        
        layout.addWidget(class_group)
        
        # 构筑风格分组
        style_group = QGroupBox("构筑风格")
        style_layout = QGridLayout(style_group)
        
        # 武器类型
        weapon_label = QLabel("主要武器:")
        self.weapon_combo = QComboBox()
        self.weapon_combo.addItems([
            "自动推荐", "弓", "法杖", "长杖", "单手剑", "双手剑",
            "锤", "斧", "爪", "长矛", "十字弓", "魔杖"
        ])
        style_layout.addWidget(weapon_label, 0, 0)
        style_layout.addWidget(self.weapon_combo, 0, 1)
        
        # 构筑目标
        goal_label = QLabel("构筑目标:")
        self.goal_combo = QComboBox()
        self.goal_combo.addItems([
            "全能型 (平衡)", "高DPS (输出)", "高生存 (防御)",
            "快速刷图", "Boss击杀", "新手友好"
        ])
        style_layout.addWidget(goal_label, 1, 0)
        style_layout.addWidget(self.goal_combo, 1, 1)
        
        layout.addWidget(style_group)
        
        # 游戏模式分组
        mode_group = QGroupBox("游戏模式")
        mode_layout = QGridLayout(mode_group)
        
        # 模式选择
        mode_label = QLabel("模式:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["标准模式", "专家模式"])
        mode_layout.addWidget(mode_label, 0, 0)
        mode_layout.addWidget(self.mode_combo, 0, 1)
        
        # 等级范围
        level_label = QLabel("目标等级:")
        self.level_spin = QSpinBox()
        self.level_spin.setRange(1, 100)
        self.level_spin.setValue(90)
        mode_layout.addWidget(level_label, 1, 0)
        mode_layout.addWidget(self.level_spin, 1, 1)
        
        layout.addWidget(mode_group)
        
        return widget
    
    def _create_advanced_tab(self) -> QWidget:
        """创建高级设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # PoB2集成设置
        pob2_group = QGroupBox("PoB2集成")
        pob2_layout = QGridLayout(pob2_group)
        
        # 生成导入代码
        pob2_import_label = QLabel("生成PoB2导入代码:")
        self.pob2_import_combo = QComboBox()
        self.pob2_import_combo.addItems(["是", "否"])
        pob2_layout.addWidget(pob2_import_label, 0, 0)
        pob2_layout.addWidget(self.pob2_import_combo, 0, 1)
        
        # 计算精确数值
        pob2_calc_label = QLabel("使用PoB2计算:")
        self.pob2_calc_combo = QComboBox()
        self.pob2_calc_combo.addItems(["是", "否"])
        pob2_layout.addWidget(pob2_calc_label, 1, 0)
        pob2_layout.addWidget(self.pob2_calc_combo, 1, 1)
        
        layout.addWidget(pob2_group)
        
        # AI设置分组
        ai_group = QGroupBox("AI生成设置")
        ai_layout = QGridLayout(ai_group)
        
        # 推荐数量
        count_label = QLabel("推荐数量:")
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 10)
        self.count_spin.setValue(3)
        ai_layout.addWidget(count_label, 0, 0)
        ai_layout.addWidget(self.count_spin, 0, 1)
        
        # 创新程度
        creativity_label = QLabel("创新程度:")
        self.creativity_combo = QComboBox()
        self.creativity_combo.addItems([
            "保守 (基于成熟构筑)", "中等", "创新 (探索新构筑)"
        ])
        ai_layout.addWidget(creativity_label, 1, 0)
        ai_layout.addWidget(self.creativity_combo, 1, 1)
        
        layout.addWidget(ai_group)
        
        # 额外需求
        requirements_group = QGroupBox("特殊要求")
        requirements_layout = QVBoxLayout(requirements_group)
        
        requirements_label = QLabel("额外要求或偏好 (可选):")
        self.requirements_text = QTextEdit()
        self.requirements_text.setMaximumHeight(100)
        self.requirements_text.setPlaceholderText("例如: 希望使用特定技能、避免某种装备类型、偏好某种游戏风格等...")
        
        requirements_layout.addWidget(requirements_label)
        requirements_layout.addWidget(self.requirements_text)
        
        layout.addWidget(requirements_group)
        
        return widget
    
    def _create_budget_tab(self) -> QWidget:
        """创建预算设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # 预算设置分组
        budget_group = QGroupBox("预算限制")
        budget_layout = QGridLayout(budget_group)
        
        # 货币类型
        currency_label = QLabel("货币类型:")
        self.currency_combo = QComboBox()
        self.currency_combo.addItems([
            "Divine Orb", "Exalted Orb", "Chaos Orb", "无限制"
        ])
        budget_layout.addWidget(currency_label, 0, 0)
        budget_layout.addWidget(self.currency_combo, 0, 1)
        
        # 预算金额
        amount_label = QLabel("预算金额:")
        self.amount_spin = QSpinBox()
        self.amount_spin.setRange(0, 999999)
        self.amount_spin.setValue(50)
        self.amount_spin.setSuffix(" (设置为0表示无限制)")
        budget_layout.addWidget(amount_label, 1, 0)
        budget_layout.addWidget(self.amount_spin, 1, 1)
        
        layout.addWidget(budget_group)
        
        # 预算分配建议
        allocation_group = QGroupBox("预算分配指导")
        allocation_layout = QVBoxLayout(allocation_group)
        
        allocation_text = QLabel("""
        <b>推荐预算分配:</b><br>
        • <b>武器:</b> 40-50% (主要DPS来源)<br>
        • <b>防具:</b> 30-35% (生存保障)<br>
        • <b>饰品:</b> 15-20% (属性补充)<br>
        • <b>药剂:</b> 5-10% (辅助增强)
        """)
        allocation_text.setWordWrap(True)
        allocation_text.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_secondary')};
                padding: 12px;
                background-color: {self.theme.get_color('background_secondary')};
                border-radius: 6px;
            }}
        """)
        
        allocation_layout.addWidget(allocation_text)
        layout.addWidget(allocation_group)
        
        return widget
    
    def _create_action_buttons(self, layout: QVBoxLayout):
        """创建操作按钮区域"""
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.setSpacing(16)
        
        # 重置按钮
        reset_button = QPushButton("重置设置")
        reset_button.setMinimumSize(120, 40)
        reset_button.clicked.connect(self._reset_form)
        button_layout.addWidget(reset_button)
        
        # 生成构筑按钮
        self.generate_button = QPushButton("生成AI构筑推荐")
        self.generate_button.setProperty("accent", True)
        self.generate_button.setMinimumSize(200, 40)
        self.generate_button.clicked.connect(self._start_generation)
        button_layout.addWidget(self.generate_button)
        
        # 取消按钮（初始隐藏）
        self.cancel_button = QPushButton("取消生成")
        self.cancel_button.setMinimumSize(120, 40)
        self.cancel_button.clicked.connect(self._cancel_generation)
        self.cancel_button.setVisible(False)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def _create_progress_section(self, layout: QVBoxLayout):
        """创建进度条区域"""
        # 进度条容器（初始隐藏）
        self.progress_frame = QFrame()
        progress_layout = QVBoxLayout(self.progress_frame)
        progress_layout.setSpacing(8)
        
        # 进度标签
        self.progress_label = QLabel("准备生成...")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet(f"color: {self.theme.get_color('text_secondary')};")
        progress_layout.addWidget(self.progress_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        # 初始隐藏
        self.progress_frame.setVisible(False)
        
        layout.addWidget(self.progress_frame)
    
    def _create_pob2_status_section(self, layout: QVBoxLayout):
        """创建PoB2状态区域"""
        # PoB2状态组
        pob2_group = QGroupBox("PoB2 服务状态")
        pob2_layout = QVBoxLayout(pob2_group)
        
        # PoB2状态小组件
        self.pob2_status_widget = PoB2StatusWidget(self.backend_client, self)
        self.pob2_status_widget.setMaximumHeight(200)
        pob2_layout.addWidget(self.pob2_status_widget)
        
        # 初始状态设为收起
        pob2_group.setVisible(False)
        
        # 切换按钮
        self.pob2_toggle_button = QPushButton("显示 PoB2 状态")
        self.pob2_toggle_button.clicked.connect(
            lambda: self._toggle_pob2_status(pob2_group)
        )
        
        layout.addWidget(self.pob2_toggle_button)
        layout.addWidget(pob2_group)
    
    def _create_error_section(self, layout: QVBoxLayout):
        """创建错误处理区域"""
        # 错误处理小组件（通知显示区域）
        self.error_handler.setMaximumHeight(150)
        layout.addWidget(self.error_handler)
    
    def _toggle_pob2_status(self, pob2_group: QGroupBox):
        """切换PoB2状态显示"""
        is_visible = pob2_group.isVisible()
        pob2_group.setVisible(not is_visible)
        
        if is_visible:
            self.pob2_toggle_button.setText("显示 PoB2 状态")
        else:
            self.pob2_toggle_button.setText("隐藏 PoB2 状态")
    
    def _setup_services(self):
        """设置服务连接"""
        # 连接后端客户端信号
        self.backend_client.progress_updated.connect(self._on_progress_updated)
        self.backend_client.build_generated.connect(self._on_build_generated)
        self.backend_client.error_occurred.connect(self._on_error_occurred)
        self.backend_client.status_changed.connect(self._on_backend_status_changed)
        self.backend_client.pob2_status_changed.connect(self._on_pob2_status_changed)
        
        # 连接状态管理器信号
        self.status_manager.progress_updated.connect(self._update_progress_display)
        self.status_manager.error_occurred.connect(self._handle_service_error)
        
        # 启动状态监控
        self.status_manager.start_monitoring()
        
        # 异步初始化后端
        QTimer.singleShot(100, self._initialize_backend)
    
    def _initialize_backend(self):
        """初始化后端连接"""
        try:
            # 在新线程中初始化后端
            from threading import Thread
            import asyncio
            
            def init_backend():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    success = loop.run_until_complete(self.backend_client.initialize())
                    if success:
                        self.error_handler.show_notification(
                            NotificationType.SUCCESS,
                            "后端已连接",
                            "AI构筑推荐系统已就绪"
                        )
                    else:
                        self.error_handler.show_notification(
                            NotificationType.WARNING,
                            "后端连接失败",
                            "系统将使用降级模式运行"
                        )
                except Exception as e:
                    self._handle_initialization_error(str(e))
                finally:
                    loop.close()
            
            thread = Thread(target=init_backend)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self._handle_initialization_error(str(e))
    
    def _handle_initialization_error(self, error_message: str):
        """处理初始化错误"""
        self.error_handler.handle_error(
            Exception(f"后端初始化失败: {error_message}"),
            context="后端服务初始化",
            title="初始化错误",
            show_dialog=False,
            recoverable=True
        )
    
    def _setup_defaults(self):
        """设置默认值"""
        # 连接职业变化信号以更新专精选项
        self.class_combo.currentTextChanged.connect(self._update_ascendancy_options)
    
    def _update_ascendancy_options(self, class_name: str):
        """更新专精选项"""
        # 清空现有选项
        self.ascendancy_combo.clear()
        self.ascendancy_combo.addItem("自动选择最佳专精")
        
        # 根据职业添加对应专精
        ascendancy_map = {
            "女巫 (Witch)": ["血法师", "地狱女巫", "暴风使"],
            "法师 (Sorceress)": ["魔化师", "时空法师", "斯特姆法师"],
            "游侠 (Ranger)": ["猎手", "刺客", "女猎手"],
            "僧侣 (Monk)": ["武僧", "魂师", "符师"],
            "战士 (Warrior)": ["斗士", "奴隶主", "泰坦"],
            "女猎手 (Huntress)": ["剑舞者", "女武神", "女猎手"]
        }
        
        if class_name in ascendancy_map:
            self.ascendancy_combo.addItems(ascendancy_map[class_name])
    
    def _reset_form(self):
        """重置表单"""
        self.class_combo.setCurrentIndex(0)
        self.ascendancy_combo.setCurrentIndex(0)
        self.weapon_combo.setCurrentIndex(0)
        self.goal_combo.setCurrentIndex(0)
        self.mode_combo.setCurrentIndex(0)
        self.level_spin.setValue(90)
        self.pob2_import_combo.setCurrentIndex(0)
        self.pob2_calc_combo.setCurrentIndex(0)
        self.count_spin.setValue(3)
        self.creativity_combo.setCurrentIndex(1)
        self.requirements_text.clear()
        self.currency_combo.setCurrentIndex(0)
        self.amount_spin.setValue(50)
    
    def _start_generation(self):
        """开始构筑生成"""
        # 检查是否正在生成
        if self.is_generating:
            self._show_error("构筑生成正在进行中，请等待完成")
            return
        
        # 验证输入
        if self.class_combo.currentIndex() == 0:
            self._show_error("请选择职业")
            return
        
        # 检查后端状态
        if self.backend_client.is_busy():
            self._show_error("后端系统忙碌，请稍后再试")
            return
        
        try:
            # 收集表单数据
            gui_data = self._collect_form_data()
            
            # 使用数据转换器转换数据
            conversion_result = self.data_converter.gui_to_backend_request(gui_data)
            if not conversion_result.success:
                self._show_error(f"数据验证失败: {conversion_result.error}")
                return
            
            # 显示进度条
            self.progress_frame.setVisible(True)
            self._set_generation_state(True)
            
            # 启动后端生成
            success = self.backend_client.generate_build_async(gui_data)
            if not success:
                self._show_error("无法启动构筑生成，请检查后端连接")
                self._set_generation_state(False)
                return
            
            # 更新状态管理器
            self.status_manager.update_progress(
                0, "initializing", "开始生成AI构筑推荐..."
            )
            
            self.error_handler.show_notification(
                NotificationType.INFO,
                "生成开始",
                "AI构筑推荐生成已启动，请耐心等待...",
                auto_close=True,
                duration=3000
            )
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                context="构筑生成启动",
                title="启动失败",
                show_dialog=False,
                recoverable=True
            )
            self._set_generation_state(False)
    
    def _set_generation_state(self, generating: bool):
        """设置生成状态"""
        self.is_generating = generating
        self.generate_button.setEnabled(not generating)
        self.cancel_button.setVisible(generating)
        
        if generating:
            self.generate_button.setText("生成中...")
            self.progress_frame.setVisible(True)
        else:
            self.generate_button.setText("生成AI构筑推荐")
            self.progress_frame.setVisible(False)
    
    def _cancel_generation(self):
        """取消构筑生成"""
        if not self.is_generating:
            return
        
        # 显示确认对话框
        reply = QMessageBox.question(
            self, "确认取消",
            "确定要取消当前的构筑生成吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 取消后端请求
            success = self.backend_client.cancel_current_request()
            if success:
                self.error_handler.show_notification(
                    NotificationType.INFO,
                    "已取消",
                    "构筑生成已被用户取消"
                )
            
            # 重置状态
            self._set_generation_state(False)
            self.status_manager.reset_progress()
    
    def _collect_form_data(self) -> Dict[str, Any]:
        """收集表单数据"""
        return {
            'game': 'poe2',
            'mode': 'hardcore' if self.mode_combo.currentText() == '专家模式' else 'standard',
            'preferences': {
                'class': self.class_combo.currentText().split(' ')[0],
                'ascendancy': self.ascendancy_combo.currentText() if self.ascendancy_combo.currentIndex() > 0 else None,
                'weapon_type': self.weapon_combo.currentText() if self.weapon_combo.currentIndex() > 0 else None,
                'goal': self._map_goal_to_backend(self.goal_combo.currentText()),
                'level': self.level_spin.value(),
                'budget': {
                    'amount': self.amount_spin.value() if self.amount_spin.value() > 0 else None,
                    'currency': self.currency_combo.currentText().lower().replace(' ', '_')
                },
                'pob2_integration': {
                    'generate_import_code': self.pob2_import_combo.currentText() == '是',
                    'calculate_stats': self.pob2_calc_combo.currentText() == '是',
                    'validate_build': True
                },
                'ai_settings': {
                    'recommendation_count': self.count_spin.value(),
                    'creativity_level': self.creativity_combo.currentIndex(),
                    'special_requirements': self.requirements_text.toPlainText()
                }
            }
        }
    
    def _map_goal_to_backend(self, goal_text: str) -> str:
        """将UI目标映射到后端格式"""
        goal_mapping = {
            "全能型 (平衡)": "balanced",
            "高DPS (输出)": "high_dps", 
            "高生存 (防御)": "tanky",
            "快速刷图": "clear_speed",
            "Boss击杀": "boss_killing",
            "新手友好": "beginner_friendly"
        }
        return goal_mapping.get(goal_text, "balanced")
    
    # 新的事件处理方法
    def _on_progress_updated(self, progress_data: Dict[str, Any]):
        """处理进度更新"""
        progress = progress_data.get('progress', 0)
        message = progress_data.get('message', '处理中...')
        stage = progress_data.get('stage', 'processing')
        
        # 更新进度条
        self.progress_bar.setValue(progress)
        self.progress_label.setText(f"{message} ({progress}%)")
        
        # 更新状态管理器
        self.status_manager.update_progress(
            progress, stage, message,
            estimated_total_time=progress_data.get('remaining_time')
        )
    
    def _on_build_generated(self, result_data: Dict[str, Any]):
        """处理构筑生成完成"""
        try:
            self._set_generation_state(False)
            
            if result_data.get('success', False):
                # 使用数据转换器处理结果
                builds = result_data.get('builds', [])
                
                self.error_handler.show_notification(
                    NotificationType.SUCCESS,
                    "生成完成",
                    f"成功生成 {len(builds)} 个AI构筑推荐",
                    auto_close=True,
                    duration=4000
                )
                
                # 发射构筑生成完成信号
                self.build_generated.emit(result_data)
                
                # 更新状态管理器
                self.status_manager.update_progress(
                    100, "completed", "构筑推荐生成完成！"
                )
                
                # 延迟重置进度
                QTimer.singleShot(2000, self.status_manager.reset_progress)
                
            else:
                error_msg = result_data.get('error', '生成失败')
                self._handle_generation_error(error_msg)
                
        except Exception as e:
            self.error_handler.handle_error(
                e,
                context="构筑生成完成处理",
                title="结果处理错误",
                show_dialog=False
            )
            self._set_generation_state(False)
    
    def _on_error_occurred(self, error_data: Dict[str, Any]):
        """处理错误发生"""
        error_message = error_data.get('error', '未知错误')
        error_type = error_data.get('error_type', 'GeneralError')
        
        self._set_generation_state(False)
        
        # 使用错误处理器显示错误
        self.error_handler.report_error(
            error_id=f"generation_error_{int(QTimer().remainingTime())}",
            error_type=error_type,
            message=error_message,
            component="构筑生成",
            recoverable=True,
            recovery_action="重新尝试生成构筑"
        )
        
        # 重置进度
        self.status_manager.reset_progress()
    
    def _on_backend_status_changed(self, status: str):
        """处理后端状态变化"""
        self.status_manager.update_component_status('backend', {
            'status': status,
            'response_time_ms': None,
            'error_message': None if status == 'healthy' else '后端连接异常'
        })
        
        # 如果后端出现问题且正在生成，则停止生成
        if status in ['error', 'offline'] and self.is_generating:
            self._set_generation_state(False)
            self.error_handler.show_notification(
                NotificationType.ERROR,
                "后端连接中断",
                "构筑生成已停止，请检查后端连接"
            )
    
    def _on_pob2_status_changed(self, status_data: Dict[str, Any]):
        """处理PoB2状态变化"""
        # 更新PoB2状态小组件
        if hasattr(self, 'pob2_status_widget'):
            self.pob2_status_widget._update_status_display(status_data)
    
    def _update_progress_display(self, progress_data: Dict[str, Any]):
        """更新进度显示（来自状态管理器）"""
        # 这个方法处理来自状态管理器的进度更新
        # 避免重复更新，只处理不同来源的进度信息
        pass
    
    def _handle_service_error(self, error_data: Dict[str, Any]):
        """处理服务错误"""
        self.error_handler.show_notification(
            NotificationType.WARNING,
            "服务警告",
            error_data.get('message', '服务出现问题')
        )
    
    def _handle_generation_error(self, error_message: str):
        """处理生成错误"""
        self.error_handler.handle_error(
            Exception(error_message),
            context="构筑生成",
            title="生成失败",
            show_dialog=True,
            recoverable=True,
            retry_action=self._start_generation
        )
    
    def _show_error(self, message: str):
        """显示简单错误消息"""
        self.error_handler.show_notification(
            NotificationType.ERROR,
            "输入错误",
            message,
            auto_close=True,
            duration=4000
        )
    
    def cleanup(self):
        """清理资源"""
        try:
            # 取消正在进行的生成
            if self.is_generating:
                self.backend_client.cancel_current_request()
            
            # 清理服务组件
            self.backend_client.cleanup()
            self.status_manager.cleanup()
            
            if hasattr(self, 'pob2_status_widget'):
                self.pob2_status_widget.cleanup()
                
        except Exception as e:
            print(f"清理资源时出错: {e}")  # 使用print避免循环依赖