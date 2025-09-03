"""
状态管理器

负责管理GUI应用的各种状态，提供：
1. 实时状态更新和进度反馈
2. 系统健康状态监控
3. PoB2服务状态跟踪
4. 用户操作状态管理
5. 错误状态处理
"""

import logging
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication


logger = logging.getLogger(__name__)


class SystemStatus(Enum):
    """系统整体状态"""
    STARTING = "starting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    ERROR = "error"
    OFFLINE = "offline"


class ComponentType(Enum):
    """组件类型"""
    BACKEND = "backend"
    POB2_LOCAL = "pob2_local"
    POB2_WEB = "pob2_web"
    RAG_ENGINE = "rag_engine"
    MARKET_API = "market_api"
    CACHE = "cache"


@dataclass
class ComponentStatus:
    """组件状态信息"""
    name: str
    type: ComponentType
    status: str  # healthy, degraded, error, offline
    last_check: float = field(default_factory=time.time)
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgressInfo:
    """进度信息"""
    current: int  # 0-100
    stage: str
    message: str
    start_time: float = field(default_factory=time.time)
    estimated_total_time: Optional[float] = None
    sub_tasks: List[str] = field(default_factory=list)


@dataclass
class ErrorInfo:
    """错误信息"""
    error_id: str
    error_type: str
    message: str
    component: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    recoverable: bool = True
    recovery_action: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class StatusManager(QObject):
    """
    状态管理器主类
    
    统一管理应用的各种状态信息，提供实时更新和通知功能
    """
    
    # 信号定义
    system_status_changed = pyqtSignal(str)  # 系统整体状态变化
    component_status_changed = pyqtSignal(str, dict)  # 组件状态变化
    progress_updated = pyqtSignal(dict)  # 进度更新
    error_occurred = pyqtSignal(dict)  # 错误发生
    error_resolved = pyqtSignal(str)  # 错误解决
    notification_posted = pyqtSignal(dict)  # 通知消息
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 状态存储
        self._system_status = SystemStatus.STARTING
        self._component_statuses: Dict[str, ComponentStatus] = {}
        self._current_progress: Optional[ProgressInfo] = None
        self._active_errors: Dict[str, ErrorInfo] = {}
        self._status_history: List[Dict[str, Any]] = []
        
        # 配置
        self.max_history_size = 100
        self.status_check_interval = 30000  # 30秒
        self.error_retry_delay = 5000  # 5秒
        
        # 定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._periodic_status_check)
        
        # 通知配置
        self.notification_handlers: List[Callable] = []
        
        logger.info("StatusManager 已初始化")
    
    def start_monitoring(self):
        """开始状态监控"""
        logger.info("开始状态监控")
        self.status_timer.start(self.status_check_interval)
        self._set_system_status(SystemStatus.HEALTHY)
    
    def stop_monitoring(self):
        """停止状态监控"""
        logger.info("停止状态监控")
        self.status_timer.stop()
        self._set_system_status(SystemStatus.OFFLINE)
    
    def update_component_status(self, component_name: str, 
                              status_data: Dict[str, Any]):
        """
        更新组件状态
        
        Args:
            component_name: 组件名称
            status_data: 状态数据
        """
        try:
            # 解析组件类型
            component_type = self._parse_component_type(component_name)
            
            # 创建或更新组件状态
            if component_name in self._component_statuses:
                component_status = self._component_statuses[component_name]
                # 更新现有状态
                component_status.status = status_data.get('status', 'unknown')
                component_status.last_check = time.time()
                component_status.response_time_ms = status_data.get('response_time_ms')
                component_status.error_message = status_data.get('error_message')
                component_status.metadata.update(status_data.get('metadata', {}))
            else:
                # 创建新状态
                component_status = ComponentStatus(
                    name=component_name,
                    type=component_type,
                    status=status_data.get('status', 'unknown'),
                    response_time_ms=status_data.get('response_time_ms'),
                    error_message=status_data.get('error_message'),
                    metadata=status_data.get('metadata', {})
                )
                self._component_statuses[component_name] = component_status
            
            # 发送状态变化信号
            self.component_status_changed.emit(component_name, {
                'type': component_type.value,
                'status': component_status.status,
                'response_time_ms': component_status.response_time_ms,
                'error_message': component_status.error_message,
                'last_check': component_status.last_check,
                'metadata': component_status.metadata
            })
            
            # 更新系统整体状态
            self._update_system_status()
            
            logger.debug(f"组件状态已更新: {component_name} -> {component_status.status}")
            
        except Exception as e:
            logger.error(f"更新组件状态失败 {component_name}: {e}")
            self._handle_error(f"status_update_{component_name}", str(e))
    
    def update_progress(self, progress: int, stage: str, message: str,
                       estimated_total_time: Optional[float] = None,
                       sub_tasks: Optional[List[str]] = None):
        """
        更新进度信息
        
        Args:
            progress: 进度百分比 (0-100)
            stage: 当前阶段
            message: 进度消息
            estimated_total_time: 预估总时间(秒)
            sub_tasks: 子任务列表
        """
        try:
            # 创建或更新进度信息
            if self._current_progress is None:
                self._current_progress = ProgressInfo(
                    current=progress,
                    stage=stage,
                    message=message,
                    estimated_total_time=estimated_total_time,
                    sub_tasks=sub_tasks or []
                )
            else:
                self._current_progress.current = progress
                self._current_progress.stage = stage
                self._current_progress.message = message
                if estimated_total_time is not None:
                    self._current_progress.estimated_total_time = estimated_total_time
                if sub_tasks is not None:
                    self._current_progress.sub_tasks = sub_tasks
            
            # 计算额外信息
            elapsed_time = time.time() - self._current_progress.start_time
            remaining_time = None
            
            if progress > 0 and estimated_total_time:
                remaining_time = max(0, estimated_total_time - elapsed_time)
            elif progress > 5:  # 有一定进度时才估算
                estimated_total = elapsed_time * 100 / progress
                remaining_time = max(0, estimated_total - elapsed_time)
            
            # 构建进度数据
            progress_data = {
                'progress': progress,
                'stage': stage,
                'message': message,
                'elapsed_time': elapsed_time,
                'remaining_time': remaining_time,
                'sub_tasks': self._current_progress.sub_tasks,
                'timestamp': time.time()
            }
            
            # 发送进度更新信号
            self.progress_updated.emit(progress_data)
            
            # 完成时清除进度
            if progress >= 100:
                self._current_progress = None
            
            logger.debug(f"进度已更新: {progress}% - {stage} - {message}")
            
        except Exception as e:
            logger.error(f"更新进度失败: {e}")
    
    def report_error(self, error_id: str, error_type: str, message: str,
                    component: Optional[str] = None, recoverable: bool = True,
                    recovery_action: Optional[str] = None,
                    details: Optional[Dict[str, Any]] = None):
        """
        报告错误
        
        Args:
            error_id: 错误唯一标识
            error_type: 错误类型
            message: 错误消息
            component: 相关组件
            recoverable: 是否可恢复
            recovery_action: 恢复操作建议
            details: 错误详情
        """
        try:
            # 创建错误信息
            error_info = ErrorInfo(
                error_id=error_id,
                error_type=error_type,
                message=message,
                component=component,
                recoverable=recoverable,
                recovery_action=recovery_action,
                details=details or {}
            )
            
            # 存储错误
            self._active_errors[error_id] = error_info
            
            # 构建错误数据
            error_data = {
                'error_id': error_id,
                'error_type': error_type,
                'message': message,
                'component': component,
                'timestamp': error_info.timestamp,
                'recoverable': recoverable,
                'recovery_action': recovery_action,
                'details': details or {}
            }
            
            # 发送错误信号
            self.error_occurred.emit(error_data)
            
            # 更新系统状态
            self._update_system_status()
            
            # 记录到历史
            self._add_to_history('error', error_data)
            
            logger.error(f"错误已报告: {error_id} - {message}")
            
            # 发送通知
            self._post_notification({
                'type': 'error',
                'title': f'{error_type} 错误',
                'message': message,
                'actions': [recovery_action] if recovery_action else []
            })
            
        except Exception as e:
            logger.error(f"报告错误失败 {error_id}: {e}")
    
    def resolve_error(self, error_id: str):
        """
        解决错误
        
        Args:
            error_id: 错误ID
        """
        try:
            if error_id in self._active_errors:
                del self._active_errors[error_id]
                
                # 发送错误解决信号
                self.error_resolved.emit(error_id)
                
                # 更新系统状态
                self._update_system_status()
                
                # 记录到历史
                self._add_to_history('error_resolved', {'error_id': error_id})
                
                logger.info(f"错误已解决: {error_id}")
                
                # 发送通知
                self._post_notification({
                    'type': 'success',
                    'title': '错误已解决',
                    'message': f'错误 {error_id} 已成功解决'
                })
            
        except Exception as e:
            logger.error(f"解决错误失败 {error_id}: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统整体状态"""
        return {
            'status': self._system_status.value,
            'component_count': len(self._component_statuses),
            'healthy_components': sum(
                1 for c in self._component_statuses.values() 
                if c.status == 'healthy'
            ),
            'error_count': len(self._active_errors),
            'has_progress': self._current_progress is not None,
            'last_update': time.time()
        }
    
    def get_component_statuses(self) -> Dict[str, Dict[str, Any]]:
        """获取所有组件状态"""
        statuses = {}
        for name, status in self._component_statuses.items():
            statuses[name] = {
                'type': status.type.value,
                'status': status.status,
                'last_check': status.last_check,
                'response_time_ms': status.response_time_ms,
                'error_message': status.error_message,
                'metadata': status.metadata
            }
        return statuses
    
    def get_active_errors(self) -> Dict[str, Dict[str, Any]]:
        """获取活跃错误列表"""
        errors = {}
        for error_id, error_info in self._active_errors.items():
            errors[error_id] = {
                'error_type': error_info.error_type,
                'message': error_info.message,
                'component': error_info.component,
                'timestamp': error_info.timestamp,
                'recoverable': error_info.recoverable,
                'recovery_action': error_info.recovery_action,
                'details': error_info.details
            }
        return errors
    
    def get_current_progress(self) -> Optional[Dict[str, Any]]:
        """获取当前进度信息"""
        if not self._current_progress:
            return None
        
        elapsed_time = time.time() - self._current_progress.start_time
        remaining_time = None
        
        if self._current_progress.current > 5:
            estimated_total = elapsed_time * 100 / self._current_progress.current
            remaining_time = max(0, estimated_total - elapsed_time)
        
        return {
            'progress': self._current_progress.current,
            'stage': self._current_progress.stage,
            'message': self._current_progress.message,
            'elapsed_time': elapsed_time,
            'remaining_time': remaining_time,
            'sub_tasks': self._current_progress.sub_tasks
        }
    
    def get_status_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取状态历史"""
        return self._status_history[-limit:]
    
    def add_notification_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """添加通知处理器"""
        self.notification_handlers.append(handler)
    
    def remove_notification_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """移除通知处理器"""
        if handler in self.notification_handlers:
            self.notification_handlers.remove(handler)
    
    def clear_errors(self):
        """清除所有错误"""
        error_ids = list(self._active_errors.keys())
        for error_id in error_ids:
            self.resolve_error(error_id)
    
    def reset_progress(self):
        """重置进度信息"""
        self._current_progress = None
        self.progress_updated.emit({
            'progress': 0,
            'stage': 'idle',
            'message': '等待操作...',
            'elapsed_time': 0,
            'remaining_time': None,
            'sub_tasks': []
        })
    
    def _parse_component_type(self, component_name: str) -> ComponentType:
        """解析组件类型"""
        name_lower = component_name.lower()
        
        if 'backend' in name_lower or 'orchestrator' in name_lower:
            return ComponentType.BACKEND
        elif 'pob2_local' in name_lower or 'local' in name_lower:
            return ComponentType.POB2_LOCAL
        elif 'pob2_web' in name_lower or 'web' in name_lower:
            return ComponentType.POB2_WEB
        elif 'rag' in name_lower:
            return ComponentType.RAG_ENGINE
        elif 'market' in name_lower or 'api' in name_lower:
            return ComponentType.MARKET_API
        elif 'cache' in name_lower:
            return ComponentType.CACHE
        else:
            return ComponentType.BACKEND  # 默认类型
    
    def _set_system_status(self, status: SystemStatus):
        """设置系统状态"""
        if self._system_status != status:
            old_status = self._system_status
            self._system_status = status
            
            # 发送状态变化信号
            self.system_status_changed.emit(status.value)
            
            # 记录到历史
            self._add_to_history('system_status_change', {
                'old_status': old_status.value,
                'new_status': status.value
            })
            
            logger.info(f"系统状态变更: {old_status.value} -> {status.value}")
    
    def _update_system_status(self):
        """根据组件状态更新系统整体状态"""
        if not self._component_statuses:
            self._set_system_status(SystemStatus.STARTING)
            return
        
        # 统计组件状态
        healthy_count = sum(1 for c in self._component_statuses.values() if c.status == 'healthy')
        total_count = len(self._component_statuses)
        error_count = len(self._active_errors)
        
        # 确定系统状态
        if error_count > 0:
            if error_count > total_count / 2:
                self._set_system_status(SystemStatus.ERROR)
            else:
                self._set_system_status(SystemStatus.DEGRADED)
        elif healthy_count == total_count:
            self._set_system_status(SystemStatus.HEALTHY)
        elif healthy_count >= total_count * 0.7:
            self._set_system_status(SystemStatus.DEGRADED)
        else:
            self._set_system_status(SystemStatus.ERROR)
    
    def _handle_error(self, error_id: str, message: str, component: Optional[str] = None):
        """处理内部错误"""
        self.report_error(
            error_id=error_id,
            error_type="InternalError",
            message=message,
            component=component,
            recoverable=True
        )
    
    def _periodic_status_check(self):
        """定期状态检查"""
        try:
            # 检查组件状态是否过期
            current_time = time.time()
            expired_components = []
            
            for name, status in self._component_statuses.items():
                if current_time - status.last_check > 60:  # 60秒超时
                    expired_components.append(name)
            
            # 标记过期组件
            for name in expired_components:
                self.update_component_status(name, {
                    'status': 'offline',
                    'error_message': '组件响应超时'
                })
            
            # 清理旧的历史记录
            if len(self._status_history) > self.max_history_size:
                self._status_history = self._status_history[-self.max_history_size:]
            
        except Exception as e:
            logger.error(f"定期状态检查失败: {e}")
    
    def _add_to_history(self, event_type: str, data: Dict[str, Any]):
        """添加到历史记录"""
        history_entry = {
            'timestamp': time.time(),
            'event_type': event_type,
            'data': data
        }
        self._status_history.append(history_entry)
    
    def _post_notification(self, notification: Dict[str, Any]):
        """发送通知"""
        try:
            # 添加时间戳
            notification['timestamp'] = time.time()
            
            # 发送信号
            self.notification_posted.emit(notification)
            
            # 调用外部处理器
            for handler in self.notification_handlers:
                try:
                    handler(notification)
                except Exception as e:
                    logger.error(f"通知处理器执行失败: {e}")
        
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        self.stop_monitoring()
        self._component_statuses.clear()
        self._active_errors.clear()
        self._status_history.clear()
        self._current_progress = None
        self.notification_handlers.clear()
        logger.info("StatusManager 资源已清理")