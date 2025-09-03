"""
错误处理和用户反馈组件

提供完整的错误处理和用户反馈机制，包括：
1. 错误对话框和通知
2. 重试机制
3. 用户友好的错误消息
4. 错误日志记录
5. 恢复操作建议
"""

import logging
import traceback
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QWidget, QFrame, QScrollArea,
    QGroupBox, QProgressBar, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QFont

from ..styles.poe2_theme import PoE2Theme


logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """错误严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationType(Enum):
    """通知类型"""
    SUCCESS = "success"
    INFO = "info" 
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ErrorContext:
    """错误上下文信息"""
    error_id: str
    title: str
    message: str
    severity: ErrorSeverity
    component: Optional[str] = None
    details: Optional[str] = None
    traceback_info: Optional[str] = None
    recoverable: bool = True
    retry_action: Optional[Callable] = None
    recovery_suggestions: List[str] = None
    
    def __post_init__(self):
        if self.recovery_suggestions is None:
            self.recovery_suggestions = []


class ErrorDialog(QDialog):
    """错误对话框"""
    
    # 信号定义
    retry_requested = pyqtSignal(str)  # 重试请求
    details_toggled = pyqtSignal(bool)  # 详情切换
    
    def __init__(self, error_context: ErrorContext, parent=None):
        super().__init__(parent)
        
        self.error_context = error_context
        self.theme = PoE2Theme()
        self.showing_details = False
        
        self._init_ui()
        self._setup_styles()
        
    def _init_ui(self):
        """初始化界面"""
        self.setWindowTitle(f"错误 - {self.error_context.title}")
        self.setModal(True)
        self.resize(500, 300)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建错误信息区域
        self._create_error_info(layout)
        
        # 创建恢复建议区域
        if self.error_context.recovery_suggestions:
            self._create_recovery_suggestions(layout)
        
        # 创建详情区域
        if self.error_context.details or self.error_context.traceback_info:
            self._create_details_section(layout)
        
        # 创建按钮区域
        self._create_buttons(layout)
    
    def _create_error_info(self, layout: QVBoxLayout):
        """创建错误信息区域"""
        info_frame = QFrame()
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        # 错误图标
        icon_label = QLabel()
        icon_size = 48
        
        severity_icons = {
            ErrorSeverity.INFO: "ℹ️",
            ErrorSeverity.WARNING: "⚠️", 
            ErrorSeverity.ERROR: "❌",
            ErrorSeverity.CRITICAL: "🚨"
        }
        
        icon_text = severity_icons.get(self.error_context.severity, "❌")
        icon_label.setText(icon_text)
        icon_label.setStyleSheet(f"font-size: {icon_size}px;")
        icon_label.setFixedSize(icon_size + 20, icon_size + 20)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        info_layout.addWidget(icon_label)
        
        # 错误文本信息
        text_layout = QVBoxLayout()
        
        # 错误标题
        title_label = QLabel(self.error_context.title)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        text_layout.addWidget(title_label)
        
        # 错误消息
        message_label = QLabel(self.error_context.message)
        message_label.setWordWrap(True)
        text_layout.addWidget(message_label)
        
        # 组件信息
        if self.error_context.component:
            component_label = QLabel(f"组件: {self.error_context.component}")
            component_label.setStyleSheet("color: gray; font-size: 11px;")
            text_layout.addWidget(component_label)
        
        info_layout.addLayout(text_layout)
        layout.addWidget(info_frame)
    
    def _create_recovery_suggestions(self, layout: QVBoxLayout):
        """创建恢复建议区域"""
        suggestions_group = QGroupBox("解决建议")
        suggestions_layout = QVBoxLayout(suggestions_group)
        
        for i, suggestion in enumerate(self.error_context.recovery_suggestions, 1):
            suggestion_label = QLabel(f"{i}. {suggestion}")
            suggestion_label.setWordWrap(True)
            suggestions_layout.addWidget(suggestion_label)
        
        layout.addWidget(suggestions_group)
    
    def _create_details_section(self, layout: QVBoxLayout):
        """创建详情区域"""
        # 详情切换按钮
        self.details_button = QPushButton("显示详情")
        self.details_button.clicked.connect(self._toggle_details)
        layout.addWidget(self.details_button)
        
        # 详情文本区域（初始隐藏）
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(200)
        
        # 设置详情内容
        details_content = []
        
        if self.error_context.details:
            details_content.append("详细信息:")
            details_content.append(self.error_context.details)
            details_content.append("")
        
        if self.error_context.traceback_info:
            details_content.append("技术详情:")
            details_content.append(self.error_context.traceback_info)
        
        self.details_text.setText("\n".join(details_content))
        self.details_text.setVisible(False)
        
        layout.addWidget(self.details_text)
    
    def _create_buttons(self, layout: QVBoxLayout):
        """创建按钮区域"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        # 重试按钮（如果支持重试）
        if self.error_context.recoverable and self.error_context.retry_action:
            retry_button = QPushButton("重试")
            retry_button.setProperty("accent", True)
            retry_button.clicked.connect(self._on_retry)
            button_layout.addWidget(retry_button)
        
        # 确定按钮
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        ok_button.setDefault(True)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
    
    def _toggle_details(self):
        """切换详情显示"""
        self.showing_details = not self.showing_details
        
        if self.showing_details:
            self.details_text.setVisible(True)
            self.details_button.setText("隐藏详情")
            self.resize(self.width(), self.height() + 200)
        else:
            self.details_text.setVisible(False)
            self.details_button.setText("显示详情")
            self.resize(self.width(), self.height() - 200)
        
        self.details_toggled.emit(self.showing_details)
    
    def _on_retry(self):
        """处理重试"""
        self.retry_requested.emit(self.error_context.error_id)
        self.accept()
    
    def _setup_styles(self):
        """设置样式"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.theme.get_color('background_primary')};
                color: {self.theme.get_color('text_primary')};
            }}
            
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
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
            }}
            
            QPushButton {{
                min-height: 32px;
                padding: 0 16px;
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 4px;
                background-color: {self.theme.get_color('button_primary')};
                color: {self.theme.get_color('text_primary')};
            }}
            
            QPushButton:hover {{
                background-color: {self.theme.get_color('button_hover')};
            }}
            
            QPushButton[accent=true] {{
                background-color: {self.theme.get_color('poe2_gold')};
                color: {self.theme.get_color('background_primary')};
                font-weight: bold;
            }}
            
            QPushButton[accent=true]:hover {{
                background-color: {self.theme.get_color('poe2_gold_hover')};
            }}
        """)


class NotificationWidget(QWidget):
    """通知小组件"""
    
    # 信号定义
    notification_closed = pyqtSignal(str)  # 通知关闭
    action_clicked = pyqtSignal(str, str)  # 操作点击
    
    def __init__(self, notification_id: str, notification_type: NotificationType,
                 title: str, message: str, actions: List[str] = None,
                 auto_close: bool = True, duration: int = 5000, parent=None):
        super().__init__(parent)
        
        self.notification_id = notification_id
        self.notification_type = notification_type
        self.title = title
        self.message = message
        self.actions = actions or []
        self.auto_close = auto_close
        self.duration = duration
        
        self.theme = PoE2Theme()
        
        self._init_ui()
        self._setup_styles()
        
        # 自动关闭定时器
        if auto_close:
            self.auto_close_timer = QTimer()
            self.auto_close_timer.timeout.connect(self._auto_close)
            self.auto_close_timer.start(duration)
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # 标题和关闭按钮
        header_layout = QHBoxLayout()
        
        # 通知图标和标题
        title_layout = QHBoxLayout()
        
        # 图标
        type_icons = {
            NotificationType.SUCCESS: "✅",
            NotificationType.INFO: "ℹ️",
            NotificationType.WARNING: "⚠️",
            NotificationType.ERROR: "❌"
        }
        
        icon_label = QLabel(type_icons.get(self.notification_type, "ℹ️"))
        icon_label.setFixedSize(20, 20)
        title_layout.addWidget(icon_label)
        
        # 标题文本
        title_label = QLabel(self.title)
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # 关闭按钮
        close_button = QPushButton("×")
        close_button.setFixedSize(24, 24)
        close_button.clicked.connect(self._close_notification)
        header_layout.addWidget(close_button)
        
        layout.addLayout(header_layout)
        
        # 消息内容
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # 操作按钮
        if self.actions:
            actions_layout = QHBoxLayout()
            actions_layout.setSpacing(8)
            
            for action in self.actions:
                action_button = QPushButton(action)
                action_button.clicked.connect(
                    lambda checked, a=action: self._on_action_clicked(a)
                )
                actions_layout.addWidget(action_button)
            
            layout.addLayout(actions_layout)
        
        # 进度条（自动关闭时显示）
        if self.auto_close:
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, self.duration)
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximumHeight(4)
            self.progress_bar.setTextVisible(False)
            layout.addWidget(self.progress_bar)
            
            # 进度更新定时器
            self.progress_timer = QTimer()
            self.progress_timer.timeout.connect(self._update_progress)
            self.progress_timer.start(100)  # 每100ms更新一次
            self.start_time = QTimer()
            self.start_time.start()
    
    def _setup_styles(self):
        """设置样式"""
        type_colors = {
            NotificationType.SUCCESS: "#4CAF50",
            NotificationType.INFO: "#2196F3",
            NotificationType.WARNING: "#FF9800", 
            NotificationType.ERROR: "#F44336"
        }
        
        bg_color = type_colors.get(self.notification_type, "#2196F3")
        
        self.setStyleSheet(f"""
            NotificationWidget {{
                background-color: {self.theme.get_color('background_secondary')};
                border: 2px solid {bg_color};
                border-radius: 8px;
                margin: 4px;
            }}
            
            QLabel {{
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
            
            QProgressBar {{
                border: none;
                background-color: {self.theme.get_color('background_primary')};
                border-radius: 2px;
            }}
            
            QProgressBar::chunk {{
                background-color: {bg_color};
                border-radius: 2px;
            }}
        """)
    
    def _close_notification(self):
        """关闭通知"""
        if hasattr(self, 'auto_close_timer'):
            self.auto_close_timer.stop()
        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()
        
        self.notification_closed.emit(self.notification_id)
        self.hide()
    
    def _auto_close(self):
        """自动关闭"""
        self._close_notification()
    
    def _on_action_clicked(self, action: str):
        """处理操作点击"""
        self.action_clicked.emit(self.notification_id, action)
        self._close_notification()
    
    def _update_progress(self):
        """更新进度条"""
        if hasattr(self, 'progress_bar') and hasattr(self, 'start_time'):
            elapsed = self.start_time.elapsed()
            self.progress_bar.setValue(min(elapsed, self.duration))


class ErrorHandler(QWidget):
    """
    错误处理器主类
    
    统一处理应用中的所有错误和通知
    """
    
    # 信号定义
    error_handled = pyqtSignal(str)  # 错误已处理
    notification_posted = pyqtSignal(dict)  # 通知已发布
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.theme = PoE2Theme()
        self.active_notifications: Dict[str, NotificationWidget] = {}
        self.error_count = 0
        self.notification_count = 0
        
        self._init_ui()
        
        logger.info("ErrorHandler 已初始化")
    
    def _init_ui(self):
        """初始化界面"""
        # 通知容器布局
        self.notifications_layout = QVBoxLayout(self)
        self.notifications_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.notifications_layout.setContentsMargins(0, 0, 0, 0)
        self.notifications_layout.setSpacing(4)
    
    def handle_error(self, error: Exception, context: Optional[str] = None,
                    title: Optional[str] = None, show_dialog: bool = True,
                    recoverable: bool = True, retry_action: Optional[Callable] = None) -> str:
        """
        处理错误
        
        Args:
            error: 异常对象
            context: 错误上下文
            title: 错误标题
            show_dialog: 是否显示对话框
            recoverable: 是否可恢复
            retry_action: 重试操作
            
        Returns:
            错误ID
        """
        try:
            # 生成错误ID
            self.error_count += 1
            error_id = f"error_{self.error_count}_{int(QTimer().remainingTime())}"
            
            # 确定错误严重程度
            severity = self._determine_severity(error, context)
            
            # 生成错误标题
            if not title:
                title = f"{type(error).__name__}"
                if context:
                    title += f" - {context}"
            
            # 生成用户友好的错误消息
            user_message = self._generate_user_message(error, context)
            
            # 生成恢复建议
            recovery_suggestions = self._generate_recovery_suggestions(error, context)
            
            # 创建错误上下文
            error_context = ErrorContext(
                error_id=error_id,
                title=title,
                message=user_message,
                severity=severity,
                component=context,
                details=str(error),
                traceback_info=traceback.format_exc(),
                recoverable=recoverable,
                retry_action=retry_action,
                recovery_suggestions=recovery_suggestions
            )
            
            # 记录错误日志
            self._log_error(error_context)
            
            # 显示错误对话框
            if show_dialog and severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
                self._show_error_dialog(error_context)
            else:
                # 显示通知
                self._show_error_notification(error_context)
            
            # 发送错误处理信号
            self.error_handled.emit(error_id)
            
            return error_id
            
        except Exception as e:
            logger.error(f"处理错误失败: {e}")
            # 显示基础错误对话框
            QMessageBox.critical(self, "系统错误", f"错误处理系统出现异常:\n{str(e)}")
            return "error_handler_failed"
    
    def show_notification(self, notification_type: NotificationType, title: str,
                         message: str, actions: List[str] = None,
                         auto_close: bool = True, duration: int = 5000) -> str:
        """
        显示通知
        
        Args:
            notification_type: 通知类型
            title: 标题
            message: 消息
            actions: 操作按钮
            auto_close: 自动关闭
            duration: 持续时间(毫秒)
            
        Returns:
            通知ID
        """
        try:
            # 生成通知ID
            self.notification_count += 1
            notification_id = f"notification_{self.notification_count}_{int(QTimer().remainingTime())}"
            
            # 创建通知小组件
            notification = NotificationWidget(
                notification_id=notification_id,
                notification_type=notification_type,
                title=title,
                message=message,
                actions=actions or [],
                auto_close=auto_close,
                duration=duration,
                parent=self
            )
            
            # 连接信号
            notification.notification_closed.connect(self._on_notification_closed)
            notification.action_clicked.connect(self._on_notification_action)
            
            # 添加到布局
            self.notifications_layout.insertWidget(0, notification)
            self.active_notifications[notification_id] = notification
            
            # 限制通知数量
            self._limit_notifications()
            
            # 发送通知信号
            self.notification_posted.emit({
                'id': notification_id,
                'type': notification_type.value,
                'title': title,
                'message': message,
                'actions': actions or []
            })
            
            logger.debug(f"通知已显示: {notification_id}")
            return notification_id
            
        except Exception as e:
            logger.error(f"显示通知失败: {e}")
            return ""
    
    def close_notification(self, notification_id: str):
        """关闭指定通知"""
        if notification_id in self.active_notifications:
            notification = self.active_notifications[notification_id]
            notification._close_notification()
    
    def clear_all_notifications(self):
        """清除所有通知"""
        notification_ids = list(self.active_notifications.keys())
        for notification_id in notification_ids:
            self.close_notification(notification_id)
    
    def _determine_severity(self, error: Exception, context: Optional[str]) -> ErrorSeverity:
        """确定错误严重程度"""
        error_type = type(error).__name__
        
        # 严重错误
        if error_type in ['SystemError', 'MemoryError', 'OSError']:
            return ErrorSeverity.CRITICAL
        
        # 一般错误
        if error_type in ['ValueError', 'TypeError', 'KeyError', 'AttributeError']:
            return ErrorSeverity.ERROR
        
        # 警告级别
        if error_type in ['Warning', 'UserWarning', 'DeprecationWarning']:
            return ErrorSeverity.WARNING
        
        # 基于上下文判断
        if context:
            context_lower = context.lower()
            if any(word in context_lower for word in ['critical', 'fatal', 'system']):
                return ErrorSeverity.CRITICAL
            elif any(word in context_lower for word in ['network', 'connection', 'api']):
                return ErrorSeverity.WARNING
        
        # 默认为错误级别
        return ErrorSeverity.ERROR
    
    def _generate_user_message(self, error: Exception, context: Optional[str]) -> str:
        """生成用户友好的错误消息"""
        error_type = type(error).__name__
        error_message = str(error)
        
        # 常见错误的友好消息
        friendly_messages = {
            'ConnectionError': '网络连接失败，请检查网络设置',
            'TimeoutError': '操作超时，请稍后重试',
            'FileNotFoundError': '找不到指定的文件',
            'PermissionError': '权限不足，请以管理员身份运行',
            'ValueError': '输入数据格式不正确',
            'KeyError': '缺少必要的数据字段',
            'ImportError': '缺少必要的程序组件'
        }
        
        if error_type in friendly_messages:
            return friendly_messages[error_type]
        
        # 如果有上下文，添加上下文信息
        if context:
            return f"{context}时发生错误: {error_message}"
        
        return error_message
    
    def _generate_recovery_suggestions(self, error: Exception, 
                                     context: Optional[str]) -> List[str]:
        """生成恢复建议"""
        error_type = type(error).__name__
        suggestions = []
        
        # 基于错误类型的建议
        error_suggestions = {
            'ConnectionError': [
                '检查网络连接是否正常',
                '确认服务器地址是否正确',
                '尝试关闭防火墙或杀毒软件',
                '稍后重试'
            ],
            'TimeoutError': [
                '检查网络连接速度',
                '稍后重试',
                '减少并发操作数量'
            ],
            'FileNotFoundError': [
                '确认文件路径是否正确',
                '检查文件是否存在',
                '尝试重新安装程序'
            ],
            'PermissionError': [
                '以管理员身份运行程序',
                '检查文件或文件夹权限',
                '确认磁盘空间充足'
            ],
            'ValueError': [
                '检查输入数据格式',
                '参考帮助文档中的示例',
                '重新填写表单'
            ]
        }
        
        suggestions.extend(error_suggestions.get(error_type, []))
        
        # 基于上下文的建议
        if context:
            context_lower = context.lower()
            if 'pob2' in context_lower:
                suggestions.extend([
                    '检查PoB2是否正确安装',
                    '更新PoB2到最新版本',
                    '重启PoB2程序'
                ])
            elif 'api' in context_lower or 'network' in context_lower:
                suggestions.extend([
                    '检查网络连接',
                    '稍后重试',
                    '切换到离线模式'
                ])
        
        # 通用建议
        if not suggestions:
            suggestions = [
                '尝试重新启动程序',
                '检查程序是否为最新版本',
                '查看日志文件获取更多信息',
                '联系技术支持'
            ]
        
        return suggestions
    
    def _log_error(self, error_context: ErrorContext):
        """记录错误日志"""
        log_level = {
            ErrorSeverity.INFO: logging.INFO,
            ErrorSeverity.WARNING: logging.WARNING,
            ErrorSeverity.ERROR: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }
        
        level = log_level.get(error_context.severity, logging.ERROR)
        
        logger.log(
            level,
            f"[{error_context.error_id}] {error_context.title}: {error_context.message}"
        )
        
        if error_context.traceback_info:
            logger.debug(f"[{error_context.error_id}] Traceback: {error_context.traceback_info}")
    
    def _show_error_dialog(self, error_context: ErrorContext):
        """显示错误对话框"""
        dialog = ErrorDialog(error_context, self)
        dialog.retry_requested.connect(self._on_retry_requested)
        dialog.exec()
    
    def _show_error_notification(self, error_context: ErrorContext):
        """显示错误通知"""
        notification_type = {
            ErrorSeverity.INFO: NotificationType.INFO,
            ErrorSeverity.WARNING: NotificationType.WARNING,
            ErrorSeverity.ERROR: NotificationType.ERROR,
            ErrorSeverity.CRITICAL: NotificationType.ERROR
        }
        
        actions = []
        if error_context.recoverable and error_context.retry_action:
            actions.append("重试")
        
        self.show_notification(
            notification_type=notification_type.get(
                error_context.severity, 
                NotificationType.ERROR
            ),
            title=error_context.title,
            message=error_context.message,
            actions=actions,
            auto_close=error_context.severity in [ErrorSeverity.INFO, ErrorSeverity.WARNING],
            duration=8000 if error_context.severity == ErrorSeverity.WARNING else 5000
        )
    
    def _limit_notifications(self):
        """限制通知数量"""
        max_notifications = 5
        
        if len(self.active_notifications) > max_notifications:
            # 移除最旧的通知
            oldest_id = min(self.active_notifications.keys())
            self.close_notification(oldest_id)
    
    def _on_notification_closed(self, notification_id: str):
        """处理通知关闭"""
        if notification_id in self.active_notifications:
            notification = self.active_notifications[notification_id]
            self.notifications_layout.removeWidget(notification)
            notification.deleteLater()
            del self.active_notifications[notification_id]
    
    def _on_notification_action(self, notification_id: str, action: str):
        """处理通知操作"""
        logger.info(f"通知操作: {notification_id} -> {action}")
        
        # 这里可以添加具体的操作处理逻辑
        if action == "重试":
            # 触发重试逻辑
            pass
    
    def _on_retry_requested(self, error_id: str):
        """处理重试请求"""
        logger.info(f"重试请求: {error_id}")
        
        # 这里可以添加重试逻辑