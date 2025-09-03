"""
PoE2构筑生成器主窗口

主窗口类，包含菜单栏、工具栏、状态栏和主要内容区域。
支持多页面导航和响应式布局。
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QMenuBar, QMenu, QStatusBar, 
    QToolBar, QLabel, QPushButton, QSplitter,
    QMessageBox, QProgressBar, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QKeySequence, QAction

from .pages.welcome_page import WelcomePage
from .pages.build_generator_page import BuildGeneratorPage
from .pages.build_results_page import BuildResultsPage
from .pages.settings_page import SettingsPage
from .widgets.navigation_bar import NavigationBar
from .styles.poe2_theme import PoE2Theme


class MainWindow(QMainWindow):
    """PoE2构筑生成器主窗口类"""
    
    # 信号定义
    page_changed = pyqtSignal(str)  # 页面切换信号
    backend_action_requested = pyqtSignal(str, dict)  # 后端操作请求信号
    
    def __init__(self, orchestrator=None, parent=None):
        super().__init__(parent)
        
        # 后端编排器引用
        self.orchestrator = orchestrator
        
        # 主题引用
        self.theme = PoE2Theme()
        
        # 页面字典
        self.pages: Dict[str, QWidget] = {}
        
        # 当前页面
        self.current_page = "welcome"
        
        # 后端状态
        self.backend_status = False
        
        # 初始化UI
        self._init_ui()
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_statusbar()
        self._create_pages()
        self._connect_signals()
        
        # 设置定时器用于状态更新
        self._setup_timers()
        
        # 显示欢迎页面
        self.show_page("welcome")
    
    def _init_ui(self):
        """初始化用户界面"""
        # 设置窗口属性
        self.setWindowTitle("PoE2 Build Generator")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # 设置窗口居中显示
        self._center_window()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建内容区域分割器
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(content_splitter)
        
        # 创建导航栏
        self.navigation_bar = NavigationBar()
        self.navigation_bar.setMaximumWidth(200)
        self.navigation_bar.setMinimumWidth(180)
        content_splitter.addWidget(self.navigation_bar)
        
        # 创建页面堆叠部件
        self.stacked_widget = QStackedWidget()
        content_splitter.addWidget(self.stacked_widget)
        
        # 设置分割器比例
        content_splitter.setStretchFactor(0, 0)  # 导航栏不拉伸
        content_splitter.setStretchFactor(1, 1)  # 内容区域拉伸
        
        # 设置页面切换动画
        self._setup_page_animation()
    
    def _setup_menubar(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        # 新建构筑
        new_build_action = QAction("新建构筑(&N)", self)
        new_build_action.setShortcut(QKeySequence.StandardKey.New)
        new_build_action.setStatusTip("创建新的构筑配置")
        new_build_action.triggered.connect(lambda: self.show_page("build_generator"))
        file_menu.addAction(new_build_action)
        
        # 导入构筑
        import_build_action = QAction("导入构筑(&I)", self)
        import_build_action.setShortcut(QKeySequence("Ctrl+I"))
        import_build_action.setStatusTip("从PoB2导入构筑")
        import_build_action.triggered.connect(self._import_build)
        file_menu.addAction(import_build_action)
        
        # 导出构筑
        export_build_action = QAction("导出构筑(&E)", self)
        export_build_action.setShortcut(QKeySequence("Ctrl+E"))
        export_build_action.setStatusTip("导出构筑到PoB2")
        export_build_action.triggered.connect(self._export_build)
        file_menu.addAction(export_build_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("退出应用程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")
        
        # 偏好设置
        preferences_action = QAction("偏好设置(&P)", self)
        preferences_action.setShortcut(QKeySequence.StandardKey.Preferences)
        preferences_action.setStatusTip("打开应用程序设置")
        preferences_action.triggered.connect(lambda: self.show_page("settings"))
        edit_menu.addAction(preferences_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        
        # 刷新数据
        refresh_action = QAction("刷新数据(&R)", self)
        refresh_action.setShortcut(QKeySequence.StandardKey.Refresh)
        refresh_action.setStatusTip("刷新游戏数据和市场信息")
        refresh_action.triggered.connect(self._refresh_data)
        tools_menu.addAction(refresh_action)
        
        # PoB2集成检测
        pob2_check_action = QAction("检测PoB2(&D)", self)
        pob2_check_action.setStatusTip("检测Path of Building Community安装")
        pob2_check_action.triggered.connect(self._check_pob2_integration)
        tools_menu.addAction(pob2_check_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        # 关于
        about_action = QAction("关于(&A)", self)
        about_action.setStatusTip("显示应用程序信息")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """设置工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)
        
        # 新建构筑按钮
        new_action = QAction("新建构筑", self)
        new_action.setStatusTip("创建新的构筑配置")
        new_action.triggered.connect(lambda: self.show_page("build_generator"))
        toolbar.addAction(new_action)
        
        toolbar.addSeparator()
        
        # 刷新数据按钮
        refresh_action = QAction("刷新数据", self)
        refresh_action.setStatusTip("刷新游戏数据")
        refresh_action.triggered.connect(self._refresh_data)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # PoB2状态按钮
        self.pob2_status_action = QAction("PoB2状态", self)
        self.pob2_status_action.setStatusTip("检查Path of Building Community状态")
        self.pob2_status_action.triggered.connect(self._check_pob2_integration)
        toolbar.addAction(self.pob2_status_action)
    
    def _setup_statusbar(self):
        """设置状态栏"""
        statusbar = self.statusBar()
        
        # 后端状态标签
        self.backend_status_label = QLabel("后端状态: 离线")
        statusbar.addWidget(self.backend_status_label)
        
        statusbar.addPermanentWidget(QLabel(" | "))
        
        # PoB2状态标签
        self.pob2_status_label = QLabel("PoB2: 未检测")
        statusbar.addPermanentWidget(self.pob2_status_label)
        
        statusbar.addPermanentWidget(QLabel(" | "))
        
        # 进度条（隐藏状态）
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        statusbar.addPermanentWidget(self.progress_bar)
        
        # 版本信息
        version_label = QLabel("v1.0.0")
        statusbar.addPermanentWidget(version_label)
    
    def _create_pages(self):
        """创建应用程序页面"""
        # 创建各个页面
        self.pages["welcome"] = WelcomePage()
        self.pages["build_generator"] = BuildGeneratorPage(orchestrator=self.orchestrator)
        self.pages["build_results"] = BuildResultsPage()
        self.pages["settings"] = SettingsPage()
        
        # 将页面添加到堆叠部件
        for page_name, page_widget in self.pages.items():
            self.stacked_widget.addWidget(page_widget)
        
        # 连接页面信号
        if hasattr(self.pages["build_generator"], "build_generated"):
            self.pages["build_generator"].build_generated.connect(self._on_build_generated)
    
    def _connect_signals(self):
        """连接信号和槽"""
        # 连接导航栏信号
        self.navigation_bar.page_requested.connect(self.show_page)
        
        # 连接页面变化信号
        self.page_changed.connect(self.navigation_bar.set_active_page)
    
    def _setup_timers(self):
        """设置定时器"""
        # 状态更新定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(30000)  # 每30秒更新一次
        
        # 初始状态更新
        QTimer.singleShot(1000, self._update_status)  # 1秒后执行首次更新
    
    def _center_window(self):
        """将窗口居中显示"""
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())
    
    def _setup_page_animation(self):
        """设置页面切换动画"""
        self.page_animation = QPropertyAnimation(self.stacked_widget, b"geometry")
        self.page_animation.setDuration(300)
        self.page_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # 连接页面切换完成信号
        self.page_animation.finished.connect(self._on_page_animation_finished)
        
        # 页面切换状态
        self.is_animating = False
    
    def show_page(self, page_name: str):
        """显示指定页面（带动画效果）"""
        if page_name in self.pages and not self.is_animating:
            if page_name == self.current_page:
                return  # 已经是当前页面
                
            self.is_animating = True
            page_widget = self.pages[page_name]
            
            # 设置页面切换动画
            old_index = self.stacked_widget.currentIndex()
            new_index = self.stacked_widget.indexOf(page_widget)
            
            self.stacked_widget.setCurrentWidget(page_widget)
            self.current_page = page_name
            self.page_changed.emit(page_name)
            
            # 更新窗口标题
            page_titles = {
                "welcome": "PoE2 Build Generator",
                "build_generator": "构筑生成器 - PoE2 Build Generator",
                "build_results": "构筑结果 - PoE2 Build Generator", 
                "settings": "设置 - PoE2 Build Generator"
            }
            self.setWindowTitle(page_titles.get(page_name, "PoE2 Build Generator"))
            
            # 触发页面加载事件
            if hasattr(page_widget, 'on_page_show'):
                page_widget.on_page_show()
                
            # 短暂延迟后结束动画状态
            QTimer.singleShot(300, self._on_page_animation_finished)
    
    def _on_page_animation_finished(self):
        """页面动画完成回调"""
        self.is_animating = False
    
    def update_backend_status(self, is_healthy: bool):
        """更新后端状态"""
        self.backend_status = is_healthy
        status_text = "在线" if is_healthy else "离线"
        color = self.theme.get_status_color("healthy" if is_healthy else "error")
        
        self.backend_status_label.setText(f"后端状态: {status_text}")
        self.backend_status_label.setStyleSheet(f"color: {color};")
    
    def show_progress(self, message: str, max_value: int = 0):
        """显示进度条"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(max_value)
        self.progress_bar.setValue(0)
        self.statusBar().showMessage(message)
    
    def update_progress(self, value: int, message: str = ""):
        """更新进度条"""
        self.progress_bar.setValue(value)
        if message:
            self.statusBar().showMessage(message)
    
    def hide_progress(self):
        """隐藏进度条"""
        self.progress_bar.setVisible(False)
        self.statusBar().clearMessage()
    
    def _update_status(self):
        """更新状态信息"""
        if self.orchestrator:
            # 使用线程异步检查状态，避免阻塞GUI
            from threading import Thread
            import asyncio
            
            def check_status():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    async def async_health_check():
                        try:
                            health_status = await self.orchestrator.health_check()
                            is_healthy = health_status.get('overall_status') == 'healthy'
                            return is_healthy, None
                        except Exception as e:
                            return False, str(e)
                    
                    # 执行异步健康检查
                    is_healthy, error = loop.run_until_complete(async_health_check())
                    
                    # 使用QTimer.singleShot在主线程中更新UI
                    QTimer.singleShot(0, lambda: self._update_status_ui(is_healthy, error))
                    
                except Exception as e:
                    print(f"状态检查异步执行失败: {e}")
                    QTimer.singleShot(0, lambda: self.update_backend_status(False))
                finally:
                    try:
                        loop.close()
                    except:
                        pass
            
            # 在独立线程中执行状态检查
            thread = Thread(target=check_status)
            thread.daemon = True
            thread.start()
    
    def _update_status_ui(self, is_healthy: bool, error: str = None):
        """在主线程中更新状态UI"""
        try:
            if error:
                print(f"状态更新失败: {error}")
                self.update_backend_status(False)
                return
            
            self.update_backend_status(is_healthy)
            
            # 检查PoB2状态（如果可用）
            if hasattr(self.orchestrator, 'pob2_client'):
                try:
                    # 这里可能也需要异步调用，但暂时使用同步调用
                    pob2_available = hasattr(self.orchestrator.pob2_client, 'is_available') and \
                                   self.orchestrator.pob2_client.is_available()
                    pob2_text = "已连接" if pob2_available else "未检测到"
                    pob2_color = self.theme.get_status_color("healthy" if pob2_available else "warning")
                    self.pob2_status_label.setText(f"PoB2: {pob2_text}")
                    self.pob2_status_label.setStyleSheet(f"color: {pob2_color};")
                except Exception as pob2_error:
                    print(f"PoB2状态检查失败: {pob2_error}")
                    self.pob2_status_label.setText("PoB2: 未知")
                    self.pob2_status_label.setStyleSheet(f"color: {self.theme.get_status_color('warning')};")
                
        except Exception as e:
            print(f"状态UI更新失败: {e}")
            self.update_backend_status(False)
    
    def _import_build(self):
        """导入构筑"""
        # TODO: 实现构筑导入功能
        QMessageBox.information(self, "功能开发中", "构筑导入功能正在开发中...")
    
    def _export_build(self):
        """导出构筑"""
        # TODO: 实现构筑导出功能
        QMessageBox.information(self, "功能开发中", "构筑导出功能正在开发中...")
    
    def _refresh_data(self):
        """刷新数据"""
        self.show_progress("正在刷新数据...", 100)
        
        def refresh_complete():
            self.hide_progress()
            self.statusBar().showMessage("数据刷新完成", 3000)
            self._update_status()
        
        # 模拟刷新过程
        QTimer.singleShot(2000, refresh_complete)
    
    def _check_pob2_integration(self):
        """检查PoB2集成状态"""
        if self.orchestrator and hasattr(self.orchestrator, 'pob2_client'):
            pob2_client = self.orchestrator.pob2_client
            if pob2_client.is_available():
                install_path = pob2_client.installation_path
                QMessageBox.information(
                    self, 
                    "PoB2集成状态", 
                    f"Path of Building Community已检测到！\\n安装路径: {install_path}"
                )
            else:
                QMessageBox.warning(
                    self, 
                    "PoB2集成状态", 
                    "未检测到Path of Building Community安装。\\n\\n"
                    "部分功能可能不可用。请确保已安装Path of Building Community。"
                )
        else:
            QMessageBox.warning(self, "PoB2集成状态", "后端编排器不可用，无法检查PoB2状态。")
    
    def _show_about(self):
        """显示关于对话框"""
        about_text = f"""
        <h3>PoE2 Build Generator</h3>
        <p><b>版本:</b> 1.0.0</p>
        <p><b>描述:</b> Path of Exile 2构筑生成器</p>
        <p><b>特性:</b></p>
        <ul>
            <li>AI驱动的构筑推荐</li>
            <li>Path of Building Community集成</li>
            <li>实时市场数据分析</li>
            <li>响应式暗色主题界面</li>
        </ul>
        <p><b>技术栈:</b> Python, PyQt5, AI/ML</p>
        """
        
        QMessageBox.about(self, "关于 PoE2 Build Generator", about_text)
    
    def _on_build_generated(self, build_data: Dict[str, Any]):
        """处理构筑生成完成事件"""
        # 将构筑数据传递给结果页面
        if "build_results" in self.pages:
            self.pages["build_results"].display_build_results(build_data)
        
        # 切换到结果页面
        self.show_page("build_results")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止定时器
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        
        # 保存窗口状态
        # TODO: 实现窗口状态保存
        
        event.accept()