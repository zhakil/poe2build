"""
设置页面

应用程序配置和偏好设置页面。
"""

from typing import Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QPushButton, QComboBox, QLineEdit, QSpinBox,
    QCheckBox, QGroupBox, QTabWidget, QTextEdit, QFileDialog,
    QFrame, QGridLayout, QSlider, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

from ..styles.poe2_theme import PoE2Theme


class SettingsPage(QWidget):
    """设置页面类"""
    
    # 信号定义
    settings_changed = pyqtSignal(dict)  # 设置变更信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.theme = PoE2Theme()
        self.current_settings = self._load_default_settings()
        
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)
        
        # 页面标题
        title_label = QLabel("应用程序设置")
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
        
        # 创建设置标签页
        self._create_settings_tabs(content_layout)
        
        # 创建底部操作按钮
        self._create_action_buttons(content_layout)
    
    def _create_settings_tabs(self, layout: QVBoxLayout):
        """创建设置标签页"""
        tab_widget = QTabWidget()
        
        # 常规设置
        general_tab = self._create_general_tab()
        tab_widget.addTab(general_tab, "常规")
        
        # 后端设置
        backend_tab = self._create_backend_tab()
        tab_widget.addTab(backend_tab, "后端")
        
        # 界面设置
        ui_tab = self._create_ui_tab()
        tab_widget.addTab(ui_tab, "界面")
        
        # PoB2集成设置
        pob2_tab = self._create_pob2_tab()
        tab_widget.addTab(pob2_tab, "PoB2集成")
        
        # 高级设置
        advanced_tab = self._create_advanced_tab()
        tab_widget.addTab(advanced_tab, "高级")
        
        layout.addWidget(tab_widget)
    
    def _create_general_tab(self) -> QWidget:
        """创建常规设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # 语言设置
        language_group = QGroupBox("语言设置")
        language_layout = QGridLayout(language_group)
        
        language_label = QLabel("界面语言:")
        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文", "English", "繁體中文"])
        language_layout.addWidget(language_label, 0, 0)
        language_layout.addWidget(self.language_combo, 0, 1)
        
        layout.addWidget(language_group)
        
        # 启动设置
        startup_group = QGroupBox("启动设置")
        startup_layout = QVBoxLayout(startup_group)
        
        self.auto_check_updates = QCheckBox("启动时检查更新")
        self.auto_check_updates.setChecked(True)
        startup_layout.addWidget(self.auto_check_updates)
        
        self.remember_window_state = QCheckBox("记住窗口位置和大小")
        self.remember_window_state.setChecked(True)
        startup_layout.addWidget(self.remember_window_state)
        
        self.start_with_welcome = QCheckBox("启动时显示欢迎页面")
        self.start_with_welcome.setChecked(True)
        startup_layout.addWidget(self.start_with_welcome)
        
        layout.addWidget(startup_group)
        
        # 数据设置
        data_group = QGroupBox("数据设置")
        data_layout = QGridLayout(data_group)
        
        # 缓存设置
        cache_label = QLabel("数据缓存时间:")
        self.cache_spin = QSpinBox()
        self.cache_spin.setRange(1, 120)
        self.cache_spin.setValue(30)
        self.cache_spin.setSuffix(" 分钟")
        data_layout.addWidget(cache_label, 0, 0)
        data_layout.addWidget(self.cache_spin, 0, 1)
        
        # 自动刷新
        refresh_label = QLabel("自动刷新间隔:")
        self.refresh_spin = QSpinBox()
        self.refresh_spin.setRange(5, 60)
        self.refresh_spin.setValue(15)
        self.refresh_spin.setSuffix(" 分钟")
        data_layout.addWidget(refresh_label, 1, 0)
        data_layout.addWidget(self.refresh_spin, 1, 1)
        
        layout.addWidget(data_group)
        
        return widget
    
    def _create_backend_tab(self) -> QWidget:
        """创建后端设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # AI设置
        ai_group = QGroupBox("AI设置")
        ai_layout = QGridLayout(ai_group)
        
        # API端点
        api_label = QLabel("AI API端点:")
        self.api_endpoint = QLineEdit()
        self.api_endpoint.setPlaceholderText("http://localhost:8000")
        ai_layout.addWidget(api_label, 0, 0)
        ai_layout.addWidget(self.api_endpoint, 0, 1)
        
        # API密钥
        api_key_label = QLabel("API密钥:")
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setPlaceholderText("输入API密钥 (可选)")
        ai_layout.addWidget(api_key_label, 1, 0)
        ai_layout.addWidget(self.api_key, 1, 1)
        
        # 超时设置
        timeout_label = QLabel("请求超时:")
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setValue(60)
        self.timeout_spin.setSuffix(" 秒")
        ai_layout.addWidget(timeout_label, 2, 0)
        ai_layout.addWidget(self.timeout_spin, 2, 1)
        
        layout.addWidget(ai_group)
        
        # 数据源设置
        datasource_group = QGroupBox("数据源设置")
        datasource_layout = QVBoxLayout(datasource_group)
        
        # 启用的数据源
        self.enable_poe2scout = QCheckBox("启用PoE2Scout市场数据")
        self.enable_poe2scout.setChecked(True)
        datasource_layout.addWidget(self.enable_poe2scout)
        
        self.enable_poeninja = QCheckBox("启用poe.ninja构筑数据")
        self.enable_poeninja.setChecked(True)
        datasource_layout.addWidget(self.enable_poeninja)
        
        self.enable_poe2db = QCheckBox("启用PoE2DB物品数据")
        self.enable_poe2db.setChecked(True)
        datasource_layout.addWidget(self.enable_poe2db)
        
        layout.addWidget(datasource_group)
        
        # 连接测试
        test_group = QGroupBox("连接测试")
        test_layout = QHBoxLayout(test_group)
        
        self.test_button = QPushButton("测试后端连接")
        self.test_button.clicked.connect(self._test_backend_connection)
        test_layout.addWidget(self.test_button)
        
        self.test_status = QLabel("未测试")
        test_layout.addWidget(self.test_status)
        
        layout.addWidget(test_group)
        
        return widget
    
    def _create_ui_tab(self) -> QWidget:
        """创建界面设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # 主题设置
        theme_group = QGroupBox("主题设置")
        theme_layout = QGridLayout(theme_group)
        
        theme_label = QLabel("主题:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["PoE2暗色主题", "经典暗色", "浅色主题"])
        theme_layout.addWidget(theme_label, 0, 0)
        theme_layout.addWidget(self.theme_combo, 0, 1)
        
        # 字体大小
        font_size_label = QLabel("字体大小:")
        self.font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setRange(8, 16)
        self.font_size_slider.setValue(12)
        self.font_size_value = QLabel("12px")
        self.font_size_slider.valueChanged.connect(
            lambda v: self.font_size_value.setText(f"{v}px")
        )
        
        font_layout = QHBoxLayout()
        font_layout.addWidget(self.font_size_slider)
        font_layout.addWidget(self.font_size_value)
        
        theme_layout.addWidget(font_size_label, 1, 0)
        theme_layout.addLayout(font_layout, 1, 1)
        
        layout.addWidget(theme_group)
        
        # 界面行为
        behavior_group = QGroupBox("界面行为")
        behavior_layout = QVBoxLayout(behavior_group)
        
        self.show_tooltips = QCheckBox("显示工具提示")
        self.show_tooltips.setChecked(True)
        behavior_layout.addWidget(self.show_tooltips)
        
        self.smooth_scrolling = QCheckBox("启用平滑滚动")
        self.smooth_scrolling.setChecked(True)
        behavior_layout.addWidget(self.smooth_scrolling)
        
        self.minimize_to_tray = QCheckBox("最小化到系统托盘")
        self.minimize_to_tray.setChecked(False)
        behavior_layout.addWidget(self.minimize_to_tray)
        
        layout.addWidget(behavior_group)
        
        # 显示设置
        display_group = QGroupBox("显示设置")
        display_layout = QGridLayout(display_group)
        
        # DPI缩放
        dpi_label = QLabel("DPI缩放:")
        self.dpi_combo = QComboBox()
        self.dpi_combo.addItems(["自动", "100%", "125%", "150%", "200%"])
        display_layout.addWidget(dpi_label, 0, 0)
        display_layout.addWidget(self.dpi_combo, 0, 1)
        
        layout.addWidget(display_group)
        
        return widget
    
    def _create_pob2_tab(self) -> QWidget:
        """创建PoB2集成设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # PoB2路径设置
        path_group = QGroupBox("Path of Building Community路径")
        path_layout = QGridLayout(path_group)
        
        # 自动检测
        auto_detect_button = QPushButton("自动检测PoB2")
        auto_detect_button.clicked.connect(self._auto_detect_pob2)
        path_layout.addWidget(auto_detect_button, 0, 0)
        
        self.pob2_status_label = QLabel("未检测")
        path_layout.addWidget(self.pob2_status_label, 0, 1)
        
        # 手动设置路径
        path_label = QLabel("PoB2安装路径:")
        self.pob2_path = QLineEdit()
        self.pob2_path.setPlaceholderText("选择Path of Building Community安装目录")
        
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self._browse_pob2_path)
        
        path_layout.addWidget(path_label, 1, 0)
        path_layout.addWidget(self.pob2_path, 1, 1)
        path_layout.addWidget(browse_button, 1, 2)
        
        layout.addWidget(path_group)
        
        # 集成设置
        integration_group = QGroupBox("集成设置")
        integration_layout = QVBoxLayout(integration_group)
        
        self.auto_export = QCheckBox("自动导出构筑到PoB2")
        self.auto_export.setChecked(False)
        integration_layout.addWidget(self.auto_export)
        
        self.validate_builds = QCheckBox("验证构筑有效性")
        self.validate_builds.setChecked(True)
        integration_layout.addWidget(self.validate_builds)
        
        self.use_pob2_calc = QCheckBox("使用PoB2计算引擎")
        self.use_pob2_calc.setChecked(True)
        integration_layout.addWidget(self.use_pob2_calc)
        
        layout.addWidget(integration_group)
        
        # 备用设置
        fallback_group = QGroupBox("备用设置")
        fallback_layout = QVBoxLayout(fallback_group)
        
        fallback_label = QLabel("当PoB2不可用时:")
        self.fallback_combo = QComboBox()
        self.fallback_combo.addItems([
            "使用内置计算器",
            "使用Web版PoB2",
            "禁用计算功能"
        ])
        
        fallback_layout.addWidget(fallback_label)
        fallback_layout.addWidget(self.fallback_combo)
        
        layout.addWidget(fallback_group)
        
        return widget
    
    def _create_advanced_tab(self) -> QWidget:
        """创建高级设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # 调试设置
        debug_group = QGroupBox("调试设置")
        debug_layout = QVBoxLayout(debug_group)
        
        self.enable_debug = QCheckBox("启用调试模式")
        self.enable_debug.setChecked(False)
        debug_layout.addWidget(self.enable_debug)
        
        self.verbose_logging = QCheckBox("详细日志记录")
        self.verbose_logging.setChecked(False)
        debug_layout.addWidget(self.verbose_logging)
        
        self.save_requests = QCheckBox("保存API请求日志")
        self.save_requests.setChecked(False)
        debug_layout.addWidget(self.save_requests)
        
        layout.addWidget(debug_group)
        
        # 性能设置
        performance_group = QGroupBox("性能设置")
        performance_layout = QGridLayout(performance_group)
        
        # 并发请求数
        concurrent_label = QLabel("最大并发请求:")
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 10)
        self.concurrent_spin.setValue(3)
        performance_layout.addWidget(concurrent_label, 0, 0)
        performance_layout.addWidget(self.concurrent_spin, 0, 1)
        
        # 内存限制
        memory_label = QLabel("内存缓存限制:")
        self.memory_spin = QSpinBox()
        self.memory_spin.setRange(50, 1000)
        self.memory_spin.setValue(200)
        self.memory_spin.setSuffix(" MB")
        performance_layout.addWidget(memory_label, 1, 0)
        performance_layout.addWidget(self.memory_spin, 1, 1)
        
        layout.addWidget(performance_group)
        
        # 数据管理
        data_group = QGroupBox("数据管理")
        data_layout = QVBoxLayout(data_group)
        
        # 清理按钮
        clear_cache_button = QPushButton("清理缓存数据")
        clear_cache_button.clicked.connect(self._clear_cache)
        data_layout.addWidget(clear_cache_button)
        
        reset_settings_button = QPushButton("重置所有设置")
        reset_settings_button.clicked.connect(self._reset_settings)
        data_layout.addWidget(reset_settings_button)
        
        export_settings_button = QPushButton("导出设置")
        export_settings_button.clicked.connect(self._export_settings)
        data_layout.addWidget(export_settings_button)
        
        import_settings_button = QPushButton("导入设置")
        import_settings_button.clicked.connect(self._import_settings)
        data_layout.addWidget(import_settings_button)
        
        layout.addWidget(data_group)
        
        return widget
    
    def _create_action_buttons(self, layout: QVBoxLayout):
        """创建操作按钮"""
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.setSpacing(16)
        
        # 恢复默认
        restore_button = QPushButton("恢复默认")
        restore_button.clicked.connect(self._restore_defaults)
        button_layout.addWidget(restore_button)
        
        # 应用设置
        apply_button = QPushButton("应用设置")
        apply_button.setProperty("accent", True)
        apply_button.clicked.connect(self._apply_settings)
        button_layout.addWidget(apply_button)
        
        layout.addLayout(button_layout)
    
    def _load_default_settings(self) -> Dict[str, Any]:
        """加载默认设置"""
        return {
            'language': '简体中文',
            'auto_check_updates': True,
            'remember_window_state': True,
            'start_with_welcome': True,
            'cache_timeout': 30,
            'refresh_interval': 15,
            'api_endpoint': 'http://localhost:8000',
            'api_key': '',
            'timeout': 60,
            'enable_poe2scout': True,
            'enable_poeninja': True,
            'enable_poe2db': True,
            'theme': 'PoE2暗色主题',
            'font_size': 12,
            'show_tooltips': True,
            'smooth_scrolling': True,
            'minimize_to_tray': False,
            'dpi_scaling': '自动',
            'pob2_path': '',
            'auto_export': False,
            'validate_builds': True,
            'use_pob2_calc': True,
            'fallback_mode': '使用内置计算器',
            'debug_mode': False,
            'verbose_logging': False,
            'save_requests': False,
            'max_concurrent': 3,
            'memory_limit': 200
        }
    
    def _load_settings(self):
        """加载设置到界面"""
        # TODO: 从配置文件加载设置
        # 这里使用默认设置填充界面
        settings = self.current_settings
        
        # 常规设置
        self.language_combo.setCurrentText(settings['language'])
        self.auto_check_updates.setChecked(settings['auto_check_updates'])
        self.remember_window_state.setChecked(settings['remember_window_state'])
        self.start_with_welcome.setChecked(settings['start_with_welcome'])
        self.cache_spin.setValue(settings['cache_timeout'])
        self.refresh_spin.setValue(settings['refresh_interval'])
        
        # 后端设置
        self.api_endpoint.setText(settings['api_endpoint'])
        self.api_key.setText(settings['api_key'])
        self.timeout_spin.setValue(settings['timeout'])
        self.enable_poe2scout.setChecked(settings['enable_poe2scout'])
        self.enable_poeninja.setChecked(settings['enable_poeninja'])
        self.enable_poe2db.setChecked(settings['enable_poe2db'])
        
        # 界面设置
        self.theme_combo.setCurrentText(settings['theme'])
        self.font_size_slider.setValue(settings['font_size'])
        self.show_tooltips.setChecked(settings['show_tooltips'])
        self.smooth_scrolling.setChecked(settings['smooth_scrolling'])
        self.minimize_to_tray.setChecked(settings['minimize_to_tray'])
        self.dpi_combo.setCurrentText(settings['dpi_scaling'])
        
        # PoB2设置
        self.pob2_path.setText(settings['pob2_path'])
        self.auto_export.setChecked(settings['auto_export'])
        self.validate_builds.setChecked(settings['validate_builds'])
        self.use_pob2_calc.setChecked(settings['use_pob2_calc'])
        self.fallback_combo.setCurrentText(settings['fallback_mode'])
        
        # 高级设置
        self.enable_debug.setChecked(settings['debug_mode'])
        self.verbose_logging.setChecked(settings['verbose_logging'])
        self.save_requests.setChecked(settings['save_requests'])
        self.concurrent_spin.setValue(settings['max_concurrent'])
        self.memory_spin.setValue(settings['memory_limit'])
    
    def _save_settings(self) -> Dict[str, Any]:
        """保存当前设置"""
        settings = {
            'language': self.language_combo.currentText(),
            'auto_check_updates': self.auto_check_updates.isChecked(),
            'remember_window_state': self.remember_window_state.isChecked(),
            'start_with_welcome': self.start_with_welcome.isChecked(),
            'cache_timeout': self.cache_spin.value(),
            'refresh_interval': self.refresh_spin.value(),
            'api_endpoint': self.api_endpoint.text(),
            'api_key': self.api_key.text(),
            'timeout': self.timeout_spin.value(),
            'enable_poe2scout': self.enable_poe2scout.isChecked(),
            'enable_poeninja': self.enable_poeninja.isChecked(),
            'enable_poe2db': self.enable_poe2db.isChecked(),
            'theme': self.theme_combo.currentText(),
            'font_size': self.font_size_slider.value(),
            'show_tooltips': self.show_tooltips.isChecked(),
            'smooth_scrolling': self.smooth_scrolling.isChecked(),
            'minimize_to_tray': self.minimize_to_tray.isChecked(),
            'dpi_scaling': self.dpi_combo.currentText(),
            'pob2_path': self.pob2_path.text(),
            'auto_export': self.auto_export.isChecked(),
            'validate_builds': self.validate_builds.isChecked(),
            'use_pob2_calc': self.use_pob2_calc.isChecked(),
            'fallback_mode': self.fallback_combo.currentText(),
            'debug_mode': self.enable_debug.isChecked(),
            'verbose_logging': self.verbose_logging.isChecked(),
            'save_requests': self.save_requests.isChecked(),
            'max_concurrent': self.concurrent_spin.value(),
            'memory_limit': self.memory_spin.value()
        }
        
        self.current_settings = settings
        return settings
    
    def _test_backend_connection(self):
        """测试后端连接"""
        self.test_button.setEnabled(False)
        self.test_status.setText("测试中...")
        
        # 模拟测试过程
        def test_complete():
            self.test_button.setEnabled(True)
            # TODO: 实际的连接测试
            self.test_status.setText("连接成功")
            self.test_status.setStyleSheet(f"color: {self.theme.get_color('success')};")
        
        QTimer.singleShot(2000, test_complete)
    
    def _auto_detect_pob2(self):
        """自动检测PoB2"""
        # TODO: 实现PoB2自动检测
        self.pob2_status_label.setText("检测中...")
        
        def detect_complete():
            # 模拟检测结果
            self.pob2_status_label.setText("检测成功")
            self.pob2_status_label.setStyleSheet(f"color: {self.theme.get_color('success')};")
            self.pob2_path.setText("C:/Program Files/Path of Building Community/")
        
        QTimer.singleShot(1500, detect_complete)
    
    def _browse_pob2_path(self):
        """浏览PoB2路径"""
        folder = QFileDialog.getExistingDirectory(
            self, 
            "选择Path of Building Community安装目录",
            "C:/Program Files/"
        )
        if folder:
            self.pob2_path.setText(folder)
    
    def _clear_cache(self):
        """清理缓存"""
        # TODO: 实现缓存清理
        print("清理缓存...")
    
    def _reset_settings(self):
        """重置设置"""
        self.current_settings = self._load_default_settings()
        self._load_settings()
    
    def _export_settings(self):
        """导出设置"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "导出设置",
            "poe2build_settings.json",
            "JSON files (*.json)"
        )
        if filename:
            # TODO: 实现设置导出
            print(f"导出设置到: {filename}")
    
    def _import_settings(self):
        """导入设置"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "导入设置",
            "",
            "JSON files (*.json)"
        )
        if filename:
            # TODO: 实现设置导入
            print(f"从文件导入设置: {filename}")
    
    def _restore_defaults(self):
        """恢复默认设置"""
        self._reset_settings()
    
    def _apply_settings(self):
        """应用设置"""
        settings = self._save_settings()
        
        # 发射设置变更信号
        self.settings_changed.emit(settings)
        
        # TODO: 保存设置到文件
        print("设置已应用")