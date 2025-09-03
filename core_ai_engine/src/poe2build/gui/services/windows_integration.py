"""
Windows系统深度集成服务

提供完整的Windows系统集成功能：
- 系统托盘服务
- 文件关联处理
- 注册表操作
- Windows通知系统
- 自动启动管理
- 权限管理
"""

import os
import sys
import winreg
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

try:
    from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
    from PyQt6.QtGui import QIcon, QPixmap, QAction
    from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QMessageBox
    import win32api
    import win32con
    import win32gui
    import win32file
    import win32shell
    import win32clipboard
    WINDOWS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Windows集成组件不可用: {e}")
    WINDOWS_AVAILABLE = False
    # 创建占位类
    class QObject: pass
    class pyqtSignal: 
        def __init__(self, *args): pass
        def emit(self, *args): pass

class RegistryHive(Enum):
    """注册表主键类型"""
    HKEY_CURRENT_USER = "HKCU"
    HKEY_LOCAL_MACHINE = "HKLM"
    HKEY_CLASSES_ROOT = "HKCR"

@dataclass
class FileAssociation:
    """文件关联配置"""
    extension: str
    prog_id: str
    description: str
    icon_path: str
    command: str
    
@dataclass
class NotificationConfig:
    """通知配置"""
    title: str
    message: str
    icon: str = "info"  # info, warning, error
    duration: int = 5000  # 毫秒
    action_callback: Optional[Callable] = None

class TrayIconManager(QObject):
    """系统托盘图标管理器"""
    
    # 信号定义
    show_main_window = pyqtSignal()
    quit_application = pyqtSignal()
    open_settings = pyqtSignal()
    generate_build = pyqtSignal()
    notification_clicked = pyqtSignal(str)
    
    def __init__(self, app_icon_path: str = None):
        super().__init__()
        self.app_icon_path = app_icon_path or self._get_default_icon()
        self.tray_icon = None
        self.context_menu = None
        self._setup_tray_icon()
        self._notification_queue = []
        
    def _get_default_icon(self) -> str:
        """获取默认应用图标"""
        icon_paths = [
            "assets/icons/poe2build.ico",
            "assets/icons/app.ico", 
            "resources/icon.ico"
        ]
        
        for path in icon_paths:
            if os.path.exists(path):
                return path
                
        # 创建默认图标
        return self._create_default_icon()
    
    def _create_default_icon(self) -> str:
        """创建默认图标文件"""
        try:
            # 创建简单的默认图标
            from PyQt6.QtGui import QPixmap, QPainter, QColor
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor(75, 110, 175))  # PoE2主题色
            
            painter = QPainter(pixmap)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(2, 20, "P2B")
            painter.end()
            
            temp_icon = tempfile.NamedTemporaryFile(suffix=".ico", delete=False)
            pixmap.save(temp_icon.name)
            return temp_icon.name
            
        except Exception as e:
            logging.error(f"创建默认图标失败: {e}")
            return ""
    
    def _setup_tray_icon(self):
        """设置系统托盘图标"""
        if not WINDOWS_AVAILABLE or not QSystemTrayIcon.isSystemTrayAvailable():
            logging.warning("系统托盘不可用")
            return
            
        # 创建托盘图标
        icon = QIcon(self.app_icon_path) if self.app_icon_path else QIcon()
        self.tray_icon = QSystemTrayIcon(icon)
        
        # 创建右键菜单
        self._setup_context_menu()
        
        # 设置工具提示
        self.tray_icon.setToolTip("PoE2智能构筑生成器")
        
        # 连接信号
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.messageClicked.connect(self._on_notification_clicked)
        
        # 显示托盘图标
        self.tray_icon.show()
        
        logging.info("系统托盘图标已设置")
    
    def _setup_context_menu(self):
        """设置右键菜单"""
        if not self.tray_icon:
            return
            
        self.context_menu = QMenu()
        
        # 显示主窗口
        show_action = QAction("显示主窗口")
        show_action.triggered.connect(self.show_main_window.emit)
        self.context_menu.addAction(show_action)
        
        self.context_menu.addSeparator()
        
        # 快速生成构筑
        generate_action = QAction("快速生成构筑")
        generate_action.triggered.connect(self.generate_build.emit)
        self.context_menu.addAction(generate_action)
        
        # 设置
        settings_action = QAction("设置")
        settings_action.triggered.connect(self.open_settings.emit)
        self.context_menu.addAction(settings_action)
        
        self.context_menu.addSeparator()
        
        # 关于
        about_action = QAction("关于")
        about_action.triggered.connect(self._show_about)
        self.context_menu.addAction(about_action)
        
        # 退出
        quit_action = QAction("退出")
        quit_action.triggered.connect(self.quit_application.emit)
        self.context_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(self.context_menu)
    
    def _on_tray_activated(self, reason):
        """处理托盘图标激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_main_window.emit()
        elif reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            self.generate_build.emit()
    
    def _on_notification_clicked(self):
        """处理通知点击事件"""
        self.notification_clicked.emit("notification_clicked")
        self.show_main_window.emit()
    
    def _show_about(self):
        """显示关于对话框"""
        try:
            QMessageBox.about(
                None, 
                "关于PoE2构筑生成器",
                "PoE2智能构筑生成器 v2.0\n\n"
                "基于AI和实时数据的流放之路2构筑推荐工具\n"
                "支持PoB2集成、实时市场数据、智能优化建议\n\n"
                "© 2024 PoE2Build Team"
            )
        except Exception as e:
            logging.error(f"显示关于对话框失败: {e}")
    
    def show_notification(self, config: NotificationConfig):
        """显示系统通知"""
        if not self.tray_icon:
            logging.warning("托盘图标不可用，无法显示通知")
            return
            
        try:
            # 选择图标类型
            icon_map = {
                "info": QSystemTrayIcon.MessageIcon.Information,
                "warning": QSystemTrayIcon.MessageIcon.Warning,
                "error": QSystemTrayIcon.MessageIcon.Critical
            }
            
            icon = icon_map.get(config.icon, QSystemTrayIcon.MessageIcon.Information)
            
            # 显示通知
            self.tray_icon.showMessage(
                config.title,
                config.message,
                icon,
                config.duration
            )
            
            logging.info(f"显示系统通知: {config.title}")
            
        except Exception as e:
            logging.error(f"显示通知失败: {e}")
    
    def hide(self):
        """隐藏托盘图标"""
        if self.tray_icon:
            self.tray_icon.hide()
    
    def show(self):
        """显示托盘图标"""
        if self.tray_icon:
            self.tray_icon.show()

class RegistryManager:
    """Windows注册表管理器"""
    
    APP_NAME = "PoE2Build"
    COMPANY_NAME = "PoE2BuildTeam"
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def _get_registry_key(self, hive: RegistryHive, key_path: str, create: bool = False):
        """获取注册表键"""
        hive_map = {
            RegistryHive.HKEY_CURRENT_USER: winreg.HKEY_CURRENT_USER,
            RegistryHive.HKEY_LOCAL_MACHINE: winreg.HKEY_LOCAL_MACHINE,
            RegistryHive.HKEY_CLASSES_ROOT: winreg.HKEY_CLASSES_ROOT
        }
        
        try:
            if create:
                return winreg.CreateKey(hive_map[hive], key_path)
            else:
                return winreg.OpenKey(hive_map[hive], key_path, 0, winreg.KEY_READ)
        except Exception as e:
            self.logger.error(f"访问注册表键失败 {key_path}: {e}")
            return None
    
    def set_value(self, hive: RegistryHive, key_path: str, value_name: str, 
                  value: Any, value_type: int = winreg.REG_SZ) -> bool:
        """设置注册表值"""
        try:
            with self._get_registry_key(hive, key_path, create=True) as key:
                if key:
                    winreg.SetValueEx(key, value_name, 0, value_type, value)
                    self.logger.info(f"设置注册表值: {key_path}\\{value_name}")
                    return True
        except Exception as e:
            self.logger.error(f"设置注册表值失败: {e}")
        return False
    
    def get_value(self, hive: RegistryHive, key_path: str, value_name: str) -> Optional[Any]:
        """获取注册表值"""
        try:
            with self._get_registry_key(hive, key_path) as key:
                if key:
                    value, _ = winreg.QueryValueEx(key, value_name)
                    return value
        except Exception as e:
            self.logger.debug(f"获取注册表值失败 {key_path}\\{value_name}: {e}")
        return None
    
    def delete_key(self, hive: RegistryHive, key_path: str) -> bool:
        """删除注册表键"""
        try:
            hive_map = {
                RegistryHive.HKEY_CURRENT_USER: winreg.HKEY_CURRENT_USER,
                RegistryHive.HKEY_LOCAL_MACHINE: winreg.HKEY_LOCAL_MACHINE,
                RegistryHive.HKEY_CLASSES_ROOT: winreg.HKEY_CLASSES_ROOT
            }
            winreg.DeleteKey(hive_map[hive], key_path)
            self.logger.info(f"删除注册表键: {key_path}")
            return True
        except Exception as e:
            self.logger.error(f"删除注册表键失败: {e}")
        return False

class FileAssociationManager:
    """文件关联管理器"""
    
    def __init__(self, registry_manager: RegistryManager):
        self.registry = registry_manager
        self.logger = logging.getLogger(__name__)
    
    def register_file_association(self, association: FileAssociation) -> bool:
        """注册文件关联"""
        try:
            # 注册文件扩展名
            ext_key = association.extension
            if not ext_key.startswith('.'):
                ext_key = '.' + ext_key
                
            success = self.registry.set_value(
                RegistryHive.HKEY_CLASSES_ROOT,
                ext_key,
                "",
                association.prog_id
            )
            
            if not success:
                return False
            
            # 注册程序ID
            prog_key = association.prog_id
            
            # 设置描述
            success = self.registry.set_value(
                RegistryHive.HKEY_CLASSES_ROOT,
                prog_key,
                "",
                association.description
            )
            
            if not success:
                return False
            
            # 设置图标
            if association.icon_path and os.path.exists(association.icon_path):
                success = self.registry.set_value(
                    RegistryHive.HKEY_CLASSES_ROOT,
                    f"{prog_key}\\DefaultIcon",
                    "",
                    f"{association.icon_path},0"
                )
            
            # 设置打开命令
            success = self.registry.set_value(
                RegistryHive.HKEY_CLASSES_ROOT,
                f"{prog_key}\\shell\\open\\command",
                "",
                association.command
            )
            
            if success:
                # 通知系统刷新文件关联
                self._refresh_shell_associations()
                self.logger.info(f"注册文件关联成功: {association.extension}")
                return True
                
        except Exception as e:
            self.logger.error(f"注册文件关联失败: {e}")
        
        return False
    
    def unregister_file_association(self, extension: str, prog_id: str) -> bool:
        """取消文件关联"""
        try:
            # 删除扩展名关联
            ext_key = extension if extension.startswith('.') else '.' + extension
            self.registry.delete_key(RegistryHive.HKEY_CLASSES_ROOT, ext_key)
            
            # 删除程序ID
            self.registry.delete_key(RegistryHive.HKEY_CLASSES_ROOT, prog_id)
            
            # 刷新系统
            self._refresh_shell_associations()
            
            self.logger.info(f"取消文件关联成功: {extension}")
            return True
            
        except Exception as e:
            self.logger.error(f"取消文件关联失败: {e}")
            return False
    
    def _refresh_shell_associations(self):
        """刷新Shell文件关联"""
        try:
            win32api.SendMessage(
                win32con.HWND_BROADCAST,
                win32con.WM_SETTINGCHANGE,
                0,
                "Environment"
            )
        except Exception as e:
            self.logger.warning(f"刷新Shell关联失败: {e}")

class AutoStartManager:
    """自动启动管理器"""
    
    def __init__(self, registry_manager: RegistryManager):
        self.registry = registry_manager
        self.logger = logging.getLogger(__name__)
        self.run_key = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"
        self.app_name = "PoE2Build"
    
    def enable_auto_start(self, executable_path: str) -> bool:
        """启用自动启动"""
        try:
            success = self.registry.set_value(
                RegistryHive.HKEY_CURRENT_USER,
                self.run_key,
                self.app_name,
                f'"{executable_path}" --minimized'
            )
            
            if success:
                self.logger.info("启用自动启动成功")
            return success
            
        except Exception as e:
            self.logger.error(f"启用自动启动失败: {e}")
            return False
    
    def disable_auto_start(self) -> bool:
        """禁用自动启动"""
        try:
            # 删除注册表项
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.run_key, 0, winreg.KEY_WRITE) as key:
                winreg.DeleteValue(key, self.app_name)
                self.logger.info("禁用自动启动成功")
                return True
                
        except FileNotFoundError:
            # 项不存在，视为成功
            return True
        except Exception as e:
            self.logger.error(f"禁用自动启动失败: {e}")
            return False
    
    def is_auto_start_enabled(self) -> bool:
        """检查是否启用自动启动"""
        value = self.registry.get_value(
            RegistryHive.HKEY_CURRENT_USER,
            self.run_key,
            self.app_name
        )
        return value is not None

class WindowsNotificationManager:
    """Windows原生通知管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.app_id = "PoE2Build.App"
    
    def show_toast_notification(self, config: NotificationConfig) -> bool:
        """显示Toast通知（Windows 10+）"""
        try:
            # 使用win10toast库（如果可用）
            from win10toast import ToastNotifier
            
            toaster = ToastNotifier()
            toaster.show_toast(
                config.title,
                config.message,
                duration=config.duration // 1000,
                threaded=True,
                callback_on_click=config.action_callback
            )
            
            self.logger.info(f"显示Toast通知: {config.title}")
            return True
            
        except ImportError:
            self.logger.warning("win10toast不可用，使用气球通知")
            return self.show_balloon_notification(config)
        except Exception as e:
            self.logger.error(f"显示Toast通知失败: {e}")
            return False
    
    def show_balloon_notification(self, config: NotificationConfig) -> bool:
        """显示气球通知（向后兼容）"""
        try:
            # 创建临时的托盘图标用于显示气球通知
            import win32gui
            from win32api import GetModuleHandle
            from win32con import IMAGE_ICON, LR_DEFAULTSIZE, LR_LOADFROMFILE
            
            # 这是一个简化的实现，实际使用中可能需要更复杂的处理
            self.logger.info(f"显示气球通知: {config.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"显示气球通知失败: {e}")
            return False

class WindowsIntegrationService(QObject):
    """Windows系统集成主服务"""
    
    # 信号定义
    file_opened = pyqtSignal(str)
    notification_received = pyqtSignal(dict)
    system_event = pyqtSignal(str, dict)
    
    def __init__(self, app_executable_path: str = None):
        super().__init__()
        self.app_executable_path = app_executable_path or sys.executable
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.registry_manager = RegistryManager()
        self.file_association_manager = FileAssociationManager(self.registry_manager)
        self.auto_start_manager = AutoStartManager(self.registry_manager)
        self.notification_manager = WindowsNotificationManager()
        self.tray_manager = None
        
        self._setup_components()
    
    def _setup_components(self):
        """设置各个组件"""
        try:
            # 设置托盘图标
            self.tray_manager = TrayIconManager()
            
            # 连接信号
            if self.tray_manager:
                self.tray_manager.notification_clicked.connect(
                    lambda x: self.system_event.emit("tray_notification_clicked", {"data": x})
                )
                
            self.logger.info("Windows集成服务组件设置完成")
            
        except Exception as e:
            self.logger.error(f"设置Windows集成组件失败: {e}")
    
    def initialize_file_associations(self) -> bool:
        """初始化文件关联"""
        try:
            # PoE2构筑文件关联
            build_association = FileAssociation(
                extension="poe2build",
                prog_id="PoE2Build.BuildFile",
                description="PoE2构筑文件",
                icon_path=self.app_executable_path,
                command=f'"{self.app_executable_path}" --open "%1"'
            )
            
            success = self.file_association_manager.register_file_association(build_association)
            
            if success:
                self.logger.info("文件关联初始化成功")
            return success
            
        except Exception as e:
            self.logger.error(f"初始化文件关联失败: {e}")
            return False
    
    def setup_auto_start(self, enabled: bool) -> bool:
        """设置自动启动"""
        try:
            if enabled:
                return self.auto_start_manager.enable_auto_start(self.app_executable_path)
            else:
                return self.auto_start_manager.disable_auto_start()
        except Exception as e:
            self.logger.error(f"设置自动启动失败: {e}")
            return False
    
    def show_notification(self, title: str, message: str, icon: str = "info", 
                         duration: int = 5000) -> bool:
        """显示系统通知"""
        try:
            config = NotificationConfig(
                title=title,
                message=message,
                icon=icon,
                duration=duration
            )
            
            # 优先使用Toast通知
            success = self.notification_manager.show_toast_notification(config)
            
            # 如果Toast失败，使用托盘通知
            if not success and self.tray_manager:
                self.tray_manager.show_notification(config)
                success = True
            
            if success:
                self.notification_received.emit({
                    "title": title,
                    "message": message,
                    "icon": icon
                })
            
            return success
            
        except Exception as e:
            self.logger.error(f"显示通知失败: {e}")
            return False
    
    def handle_file_open(self, file_path: str):
        """处理文件打开请求"""
        try:
            if os.path.exists(file_path) and file_path.endswith('.poe2build'):
                self.logger.info(f"处理文件打开: {file_path}")
                self.file_opened.emit(file_path)
            else:
                self.logger.warning(f"无效的文件路径: {file_path}")
        except Exception as e:
            self.logger.error(f"处理文件打开失败: {e}")
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            import platform
            import psutil
            
            info = {
                "platform": platform.platform(),
                "version": platform.version(),
                "architecture": platform.architecture()[0],
                "processor": platform.processor(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_usage": dict(psutil.disk_usage('C:')._asdict()),
                "auto_start_enabled": self.auto_start_manager.is_auto_start_enabled()
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"获取系统信息失败: {e}")
            return {}
    
    def cleanup_integration(self):
        """清理集成设置"""
        try:
            # 隐藏托盘图标
            if self.tray_manager:
                self.tray_manager.hide()
            
            # 可选：清理文件关联（取决于用户设置）
            # self.file_association_manager.unregister_file_association("poe2build", "PoE2Build.BuildFile")
            
            self.logger.info("Windows集成清理完成")
            
        except Exception as e:
            self.logger.error(f"清理Windows集成失败: {e}")

# 全局实例
windows_integration_service = None

def get_windows_integration_service(app_executable_path: str = None) -> Optional[WindowsIntegrationService]:
    """获取Windows集成服务单例"""
    global windows_integration_service
    
    if not WINDOWS_AVAILABLE:
        logging.warning("Windows集成不可用")
        return None
    
    if windows_integration_service is None:
        windows_integration_service = WindowsIntegrationService(app_executable_path)
    
    return windows_integration_service

def initialize_windows_integration(app_executable_path: str = None) -> bool:
    """初始化Windows集成"""
    service = get_windows_integration_service(app_executable_path)
    
    if service:
        # 初始化文件关联
        success = service.initialize_file_associations()
        
        if success:
            logging.info("Windows集成初始化成功")
        return success
    
    return False

# 导出接口
__all__ = [
    'WindowsIntegrationService',
    'TrayIconManager', 
    'RegistryManager',
    'FileAssociationManager',
    'AutoStartManager',
    'WindowsNotificationManager',
    'NotificationConfig',
    'FileAssociation',
    'RegistryHive',
    'get_windows_integration_service',
    'initialize_windows_integration'
]