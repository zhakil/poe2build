"""
PoB2状态监控小组件

专门用于显示和管理PoB2服务状态的UI组件，提供：
1. PoB2本地客户端状态检测
2. PoB2 Web服务状态监控
3. 实时状态更新显示
4. 服务切换和配置
5. 故障诊断和恢复建议
"""

import logging
import time
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGroupBox, QProgressBar, QTextEdit, QComboBox,
    QCheckBox, QSpinBox, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt6.QtGui import QFont, QPalette

from ..styles.poe2_theme import PoE2Theme


logger = logging.getLogger(__name__)


@dataclass
class PoB2ServiceInfo:
    """PoB2服务信息"""
    name: str
    available: bool
    response_time_ms: Optional[float] = None
    version: Optional[str] = None
    path: Optional[str] = None
    error_message: Optional[str] = None
    last_check: Optional[float] = None


class PoB2StatusCheckThread(QThread):
    """PoB2状态检查线程"""
    
    # 信号定义
    status_updated = pyqtSignal(dict)  # 状态更新
    error_occurred = pyqtSignal(str)  # 错误发生
    
    def __init__(self, backend_client):
        super().__init__()
        self.backend_client = backend_client
        self.running = False
        self.check_interval = 10  # 秒
    
    def run(self):
        """执行状态检查"""
        self.running = True
        
        while self.running:
            try:
                # 异步获取PoB2状态
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    status = loop.run_until_complete(
                        self.backend_client.get_pob2_status()
                    )
                    self.status_updated.emit(status)
                finally:
                    loop.close()
                
                # 等待下次检查
                for _ in range(self.check_interval * 10):  # 100ms间隔检查停止
                    if not self.running:
                        break
                    self.msleep(100)
                    
            except Exception as e:
                self.error_occurred.emit(str(e))
                # 错误后等待更长时间再重试
                for _ in range(30 * 10):  # 30秒
                    if not self.running:
                        break
                    self.msleep(100)
    
    def stop(self):
        """停止检查"""
        self.running = False


class PoB2StatusWidget(QWidget):
    """
    PoB2状态监控小组件
    
    显示PoB2本地和Web服务的状态信息，提供诊断和配置功能
    """
    
    # 信号定义
    service_selected = pyqtSignal(str)  # 服务选择变化
    refresh_requested = pyqtSignal()  # 刷新请求
    settings_changed = pyqtSignal(dict)  # 设置变化
    
    def __init__(self, backend_client=None, parent=None):
        super().__init__(parent)
        
        self.backend_client = backend_client
        self.theme = PoE2Theme()
        
        # 状态数据
        self.current_status = {
            'available': False,
            'local_client': False,
            'web_client': False,
            'local_response_time': None,
            'web_response_time': None,
            'local_error': None,
            'web_error': None
        }
        
        # 状态检查线程
        self.status_thread: Optional[PoB2StatusCheckThread] = None
        
        self._init_ui()
        self._setup_styles()
        self._start_monitoring()
        
        logger.debug("PoB2StatusWidget 已初始化")
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # 标题和刷新按钮
        header_layout = QHBoxLayout()
        
        title_label = QLabel("PoB2 服务状态")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 刷新按钮
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self._refresh_status)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 状态监控标签页
        status_tab = self._create_status_tab()
        tab_widget.addTab(status_tab, "状态监控")
        
        # 服务配置标签页
        config_tab = self._create_config_tab()
        tab_widget.addTab(config_tab, "服务配置")
        
        # 诊断信息标签页
        diagnostics_tab = self._create_diagnostics_tab()
        tab_widget.addTab(diagnostics_tab, "诊断信息")
        
        layout.addWidget(tab_widget)
    
    def _create_status_tab(self) -> QWidget:
        """创建状态监控标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        # 总体状态
        overall_group = QGroupBox("总体状态")
        overall_layout = QVBoxLayout(overall_group)
        
        # 状态指示器
        status_layout = QHBoxLayout()
        
        self.status_icon = QLabel("●")
        self.status_icon.setFixedSize(20, 20)
        self.status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.status_icon)
        
        self.status_label = QLabel("检查中...")
        self.status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        overall_layout.addLayout(status_layout)
        
        # 快速信息
        self.quick_info_label = QLabel("正在检测PoB2服务...")
        self.quick_info_label.setWordWrap(True)
        overall_layout.addWidget(self.quick_info_label)
        
        layout.addWidget(overall_group)
        
        # 本地客户端状态
        local_group = QGroupBox("本地客户端 (推荐)")
        local_layout = QVBoxLayout(local_group)
        
        # 本地状态行
        local_status_layout = QHBoxLayout()
        
        self.local_status_icon = QLabel("●")
        self.local_status_icon.setFixedSize(16, 16)
        local_status_layout.addWidget(self.local_status_icon)
        
        self.local_status_label = QLabel("检查中...")
        local_status_layout.addWidget(self.local_status_label)
        
        local_status_layout.addStretch()
        
        self.local_response_label = QLabel("")
        self.local_response_label.setStyleSheet("color: gray; font-size: 10px;")
        local_status_layout.addWidget(self.local_response_label)
        
        local_layout.addLayout(local_status_layout)
        
        # 本地路径信息
        self.local_path_label = QLabel("")
        self.local_path_label.setStyleSheet("color: gray; font-size: 9px;")
        self.local_path_label.setWordWrap(True)
        local_layout.addWidget(self.local_path_label)
        
        layout.addWidget(local_group)
        
        # Web客户端状态
        web_group = QGroupBox("Web客户端 (备用)")
        web_layout = QVBoxLayout(web_group)
        
        # Web状态行
        web_status_layout = QHBoxLayout()
        
        self.web_status_icon = QLabel("●")
        self.web_status_icon.setFixedSize(16, 16)
        web_status_layout.addWidget(self.web_status_icon)
        
        self.web_status_label = QLabel("检查中...")
        web_status_layout.addWidget(self.web_status_label)
        
        web_status_layout.addStretch()
        
        self.web_response_label = QLabel("")
        self.web_response_label.setStyleSheet("color: gray; font-size: 10px;")
        web_status_layout.addWidget(self.web_response_label)
        
        web_layout.addLayout(web_status_layout)
        
        layout.addWidget(web_group)
        
        # 操作建议
        self.suggestions_frame = QFrame()
        self.suggestions_layout = QVBoxLayout(self.suggestions_frame)
        self.suggestions_frame.setVisible(False)
        layout.addWidget(self.suggestions_frame)
        
        return widget
    
    def _create_config_tab(self) -> QWidget:
        """创建服务配置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        # 服务优先级设置
        priority_group = QGroupBox("服务优先级")
        priority_layout = QVBoxLayout(priority_group)
        
        self.prefer_local_checkbox = QCheckBox("优先使用本地客户端")
        self.prefer_local_checkbox.setChecked(True)
        self.prefer_local_checkbox.stateChanged.connect(self._on_settings_changed)
        priority_layout.addWidget(self.prefer_local_checkbox)
        
        self.auto_fallback_checkbox = QCheckBox("本地不可用时自动切换到Web")
        self.auto_fallback_checkbox.setChecked(True)
        self.auto_fallback_checkbox.stateChanged.connect(self._on_settings_changed)
        priority_layout.addWidget(self.auto_fallback_checkbox)
        
        layout.addWidget(priority_group)
        
        # 检测设置
        detection_group = QGroupBox("检测设置")
        detection_layout = QVBoxLayout(detection_group)
        
        # 检测间隔
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("状态检查间隔:"))
        
        self.check_interval_spin = QSpinBox()
        self.check_interval_spin.setRange(5, 300)
        self.check_interval_spin.setValue(10)
        self.check_interval_spin.setSuffix(" 秒")
        self.check_interval_spin.valueChanged.connect(self._on_settings_changed)
        interval_layout.addWidget(self.check_interval_spin)
        
        interval_layout.addStretch()
        detection_layout.addLayout(interval_layout)
        
        # 超时设置
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("连接超时:"))
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 60)
        self.timeout_spin.setValue(10)
        self.timeout_spin.setSuffix(" 秒")
        self.timeout_spin.valueChanged.connect(self._on_settings_changed)
        timeout_layout.addWidget(self.timeout_spin)
        
        timeout_layout.addStretch()
        detection_layout.addLayout(timeout_layout)
        
        layout.addWidget(detection_group)
        
        # 高级设置
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QVBoxLayout(advanced_group)
        
        self.enable_logging_checkbox = QCheckBox("启用详细日志")
        self.enable_logging_checkbox.stateChanged.connect(self._on_settings_changed)
        advanced_layout.addWidget(self.enable_logging_checkbox)
        
        self.retry_failed_checkbox = QCheckBox("自动重试失败的连接")
        self.retry_failed_checkbox.setChecked(True)
        self.retry_failed_checkbox.stateChanged.connect(self._on_settings_changed)
        advanced_layout.addWidget(self.retry_failed_checkbox)
        
        layout.addWidget(advanced_group)
        
        return widget
    
    def _create_diagnostics_tab(self) -> QWidget:
        """创建诊断信息标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        # 系统信息
        system_group = QGroupBox("系统信息")
        system_layout = QVBoxLayout(system_group)
        
        self.system_info_text = QTextEdit()
        self.system_info_text.setReadOnly(True)
        self.system_info_text.setMaximumHeight(100)
        system_layout.addWidget(self.system_info_text)
        
        layout.addWidget(system_group)
        
        # 连接历史
        history_group = QGroupBox("连接历史")
        history_layout = QVBoxLayout(history_group)
        
        self.connection_history = QTextEdit()
        self.connection_history.setReadOnly(True)
        self.connection_history.setMaximumHeight(150)
        history_layout.addWidget(self.connection_history)
        
        layout.addWidget(history_group)
        
        # 错误日志
        error_group = QGroupBox("错误日志")
        error_layout = QVBoxLayout(error_group)
        
        self.error_log = QTextEdit()
        self.error_log.setReadOnly(True)
        self.error_log.setMaximumHeight(150)
        error_layout.addWidget(self.error_log)
        
        layout.addWidget(error_group)
        
        # 诊断操作
        actions_layout = QHBoxLayout()
        
        clear_log_button = QPushButton("清除日志")
        clear_log_button.clicked.connect(self._clear_logs)
        actions_layout.addWidget(clear_log_button)
        
        export_log_button = QPushButton("导出日志")
        export_log_button.clicked.connect(self._export_logs)
        actions_layout.addWidget(export_log_button)
        
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)
        
        return widget
    
    def _setup_styles(self):
        """设置样式"""
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {self.theme.get_color('border_secondary')};
                border-radius: 6px;
                margin: 8px 0;
                padding-top: 10px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 8px;
                padding: 0 5px;
                color: {self.theme.get_color('text_highlight')};
            }}
            
            QTextEdit {{
                background-color: {self.theme.get_color('background_secondary')};
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 4px;
                padding: 6px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 9px;
                color: {self.theme.get_color('text_primary')};
            }}
            
            QPushButton {{
                min-height: 24px;
                padding: 0 12px;
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 4px;
                background-color: {self.theme.get_color('button_primary')};
                color: {self.theme.get_color('text_primary')};
            }}
            
            QPushButton:hover {{
                background-color: {self.theme.get_color('button_hover')};
            }}
            
            QCheckBox {{
                color: {self.theme.get_color('text_primary')};
            }}
            
            QSpinBox {{
                padding: 4px;
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 3px;
                background-color: {self.theme.get_color('background_secondary')};
                color: {self.theme.get_color('text_primary')};
            }}
        """)
    
    def _start_monitoring(self):
        """开始监控PoB2状态"""
        if self.backend_client and not self.status_thread:
            self.status_thread = PoB2StatusCheckThread(self.backend_client)
            self.status_thread.status_updated.connect(self._update_status_display)
            self.status_thread.error_occurred.connect(self._handle_status_error)
            self.status_thread.start()
            
            logger.debug("PoB2状态监控已启动")
    
    def _stop_monitoring(self):
        """停止监控"""
        if self.status_thread:
            self.status_thread.stop()
            self.status_thread.wait(3000)  # 等待3秒
            self.status_thread = None
            
            logger.debug("PoB2状态监控已停止")
    
    def _refresh_status(self):
        """刷新状态"""
        self.refresh_requested.emit()
        
        if self.backend_client:
            # 手动触发状态检查
            QTimer.singleShot(100, self._manual_status_check)
    
    def _manual_status_check(self):
        """手动状态检查"""
        try:
            import asyncio
            
            # 在新线程中执行异步操作
            def run_async_check():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    status = loop.run_until_complete(
                        self.backend_client.get_pob2_status()
                    )
                    self._update_status_display(status)
                except Exception as e:
                    self._handle_status_error(str(e))
                finally:
                    loop.close()
            
            # 在新线程中运行
            from threading import Thread
            thread = Thread(target=run_async_check)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self._handle_status_error(str(e))
    
    def _update_status_display(self, status: Dict[str, Any]):
        """更新状态显示"""
        try:
            self.current_status = status.copy()
            
            # 更新总体状态
            if status.get('available', False):
                self.status_icon.setStyleSheet("color: #4CAF50; font-size: 16px;")  # 绿色
                self.status_label.setText("PoB2 服务可用")
                self.quick_info_label.setText("PoB2服务运行正常，构筑计算功能可用")
            else:
                self.status_icon.setStyleSheet("color: #F44336; font-size: 16px;")  # 红色
                self.status_label.setText("PoB2 服务不可用")
                self.quick_info_label.setText("PoB2服务不可用，将使用基础计算功能")
            
            # 更新本地客户端状态
            local_available = status.get('local_client', False)
            if local_available:
                self.local_status_icon.setStyleSheet("color: #4CAF50;")
                self.local_status_label.setText("本地客户端可用")
                
                response_time = status.get('local_response_time')
                if response_time is not None:
                    self.local_response_label.setText(f"{response_time:.1f}ms")
                
                # 尝试获取路径信息
                path_info = status.get('local_path', '路径未知')
                self.local_path_label.setText(f"路径: {path_info}")
            else:
                self.local_status_icon.setStyleSheet("color: #F44336;")
                self.local_status_label.setText("本地客户端不可用")
                self.local_response_label.setText("")
                
                error_msg = status.get('local_error', '未知错误')
                self.local_path_label.setText(f"错误: {error_msg}")
            
            # 更新Web客户端状态
            web_available = status.get('web_client', False)
            if web_available:
                self.web_status_icon.setStyleSheet("color: #4CAF50;")
                self.web_status_label.setText("Web客户端可用")
                
                response_time = status.get('web_response_time')
                if response_time is not None:
                    self.web_response_label.setText(f"{response_time:.1f}ms")
            else:
                self.web_status_icon.setStyleSheet("color: #F44336;")
                self.web_status_label.setText("Web客户端不可用")
                self.web_response_label.setText("")
            
            # 更新建议
            self._update_suggestions(status)
            
            # 记录连接历史
            self._log_connection_attempt(status)
            
            # 更新系统信息
            self._update_system_info()
            
            logger.debug("PoB2状态显示已更新")
            
        except Exception as e:
            logger.error(f"更新PoB2状态显示失败: {e}")
    
    def _update_suggestions(self, status: Dict[str, Any]):
        """更新操作建议"""
        suggestions = []
        
        if not status.get('available', False):
            if not status.get('local_client', False):
                suggestions.append("• 安装并启动Path of Building Community")
                suggestions.append("• 确认PoB2程序路径设置正确")
                suggestions.append("• 检查PoB2程序是否被防火墙阻止")
            
            if not status.get('web_client', False):
                suggestions.append("• 检查网络连接")
                suggestions.append("• 尝试更换DNS服务器")
        
        if suggestions:
            self.suggestions_frame.setVisible(True)
            
            # 清除现有建议
            for i in reversed(range(self.suggestions_layout.count())):
                child = self.suggestions_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)
            
            # 添加标题
            title_label = QLabel("解决建议:")
            title_font = QFont()
            title_font.setBold(True)
            title_label.setFont(title_font)
            self.suggestions_layout.addWidget(title_label)
            
            # 添加建议
            for suggestion in suggestions:
                suggestion_label = QLabel(suggestion)
                suggestion_label.setWordWrap(True)
                suggestion_label.setStyleSheet("margin-left: 8px; color: gray;")
                self.suggestions_layout.addWidget(suggestion_label)
        else:
            self.suggestions_frame.setVisible(False)
    
    def _log_connection_attempt(self, status: Dict[str, Any]):
        """记录连接尝试"""
        try:
            timestamp = time.strftime("%H:%M:%S")
            local_status = "✓" if status.get('local_client') else "✗"
            web_status = "✓" if status.get('web_client') else "✗"
            
            log_entry = f"[{timestamp}] 本地: {local_status} | Web: {web_status}"
            
            # 添加响应时间信息
            if status.get('local_response_time'):
                log_entry += f" | 本地响应: {status['local_response_time']:.1f}ms"
            if status.get('web_response_time'):
                log_entry += f" | Web响应: {status['web_response_time']:.1f}ms"
            
            # 添加到历史记录
            current_text = self.connection_history.toPlainText()
            lines = current_text.split('\n')
            
            # 保持最近50条记录
            if len(lines) >= 50:
                lines = lines[-49:]
            
            lines.append(log_entry)
            self.connection_history.setText('\n'.join(lines))
            
            # 滚动到底部
            self.connection_history.verticalScrollBar().setValue(
                self.connection_history.verticalScrollBar().maximum()
            )
            
        except Exception as e:
            logger.error(f"记录连接历史失败: {e}")
    
    def _update_system_info(self):
        """更新系统信息"""
        try:
            import platform
            import sys
            
            info_lines = [
                f"操作系统: {platform.system()} {platform.release()}",
                f"Python版本: {sys.version.split()[0]}",
                f"PyQt版本: {Qt.qVersion()}",
                f"当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                f"监控状态: {'运行中' if self.status_thread and self.status_thread.running else '已停止'}"
            ]
            
            self.system_info_text.setText('\n'.join(info_lines))
            
        except Exception as e:
            logger.error(f"更新系统信息失败: {e}")
    
    def _handle_status_error(self, error_message: str):
        """处理状态错误"""
        logger.error(f"PoB2状态检查错误: {error_message}")
        
        # 更新状态显示为错误
        self.status_icon.setStyleSheet("color: #FF9800; font-size: 16px;")  # 橙色
        self.status_label.setText("状态检查错误")
        self.quick_info_label.setText(f"状态检查失败: {error_message}")
        
        # 记录错误日志
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        error_entry = f"[{timestamp}] 错误: {error_message}"
        
        current_text = self.error_log.toPlainText()
        lines = current_text.split('\n')
        
        # 保持最近100条错误记录
        if len(lines) >= 100:
            lines = lines[-99:]
        
        lines.append(error_entry)
        self.error_log.setText('\n'.join(lines))
        
        # 滚动到底部
        self.error_log.verticalScrollBar().setValue(
            self.error_log.verticalScrollBar().maximum()
        )
    
    def _on_settings_changed(self):
        """处理设置变化"""
        try:
            settings = {
                'prefer_local': self.prefer_local_checkbox.isChecked(),
                'auto_fallback': self.auto_fallback_checkbox.isChecked(),
                'check_interval': self.check_interval_spin.value(),
                'timeout': self.timeout_spin.value(),
                'enable_logging': self.enable_logging_checkbox.isChecked(),
                'retry_failed': self.retry_failed_checkbox.isChecked()
            }
            
            # 更新检查间隔
            if self.status_thread:
                self.status_thread.check_interval = settings['check_interval']
            
            # 发送设置变化信号
            self.settings_changed.emit(settings)
            
            logger.debug("PoB2设置已更新")
            
        except Exception as e:
            logger.error(f"更新PoB2设置失败: {e}")
    
    def _clear_logs(self):
        """清除日志"""
        self.connection_history.clear()
        self.error_log.clear()
        logger.debug("PoB2日志已清除")
    
    def _export_logs(self):
        """导出日志"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出PoB2日志", "pob2_logs.txt", "Text files (*.txt)"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("=== PoB2状态监控日志 ===\n\n")
                    f.write(f"导出时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    f.write("=== 系统信息 ===\n")
                    f.write(self.system_info_text.toPlainText())
                    f.write("\n\n")
                    
                    f.write("=== 连接历史 ===\n")
                    f.write(self.connection_history.toPlainText())
                    f.write("\n\n")
                    
                    f.write("=== 错误日志 ===\n")
                    f.write(self.error_log.toPlainText())
                
                logger.info(f"PoB2日志已导出到: {file_path}")
        
        except Exception as e:
            logger.error(f"导出PoB2日志失败: {e}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return self.current_status.copy()
    
    def update_backend_client(self, backend_client):
        """更新后端客户端"""
        self.backend_client = backend_client
        
        # 重启监控
        self._stop_monitoring()
        if backend_client:
            self._start_monitoring()
    
    def cleanup(self):
        """清理资源"""
        self._stop_monitoring()
        logger.debug("PoB2StatusWidget 资源已清理")