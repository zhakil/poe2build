# PoE2构筑生成器 - Windows系统深度集成

本文档详细介绍PoE2智能构筑生成器的Windows系统集成功能，包括系统托盘、文件关联、自动启动、Windows通知等高级特性。

## 目录

- [功能概述](#功能概述)
- [系统要求](#系统要求)
- [安装和配置](#安装和配置)
- [核心功能](#核心功能)
- [使用指南](#使用指南)
- [开发接口](#开发接口)
- [故障排除](#故障排除)
- [高级配置](#高级配置)

## 功能概述

### 🎯 主要特性

- **系统托盘集成** - 最小化到系统托盘，后台运行
- **文件关联处理** - 自动关联.poe2build文件类型
- **Windows通知系统** - 原生Toast通知和气球提示
- **自动启动管理** - 开机自动启动配置
- **注册表操作** - 安全的系统配置管理
- **权限管理** - 智能权限检测和提升
- **Windows Shell集成** - 右键菜单和快捷操作

### 🛡️ 安全特性

- 最小权限原则运行
- 安全的注册表操作
- 数字签名验证
- 用户数据保护
- 恶意软件防护

## 系统要求

### 📋 基本要求

- **操作系统**: Windows 10 (版本1809) 或更高
- **架构**: x64 (64位)
- **内存**: 最少512MB可用内存
- **存储**: 最少100MB可用空间
- **.NET Framework**: 4.7.2或更高版本

### 🔧 开发环境要求

- **Python**: 3.11或更高版本
- **PyQt6**: 6.4.0或更高版本  
- **pywin32**: 306或更高版本
- **Visual C++ Redistributable**: 2019或2022版本

### ⚡ 可选组件

- **NSIS**: 3.x (用于创建安装程序)
- **Inno Setup**: 6.x (备选安装程序工具)
- **Windows SDK**: 用于数字签名
- **7-Zip**: 用于便携版打包

## 安装和配置

### 🚀 快速安装

1. **下载安装程序**
   ```powershell
   # 下载最新版本安装程序
   Invoke-WebRequest -Uri "https://github.com/yourusername/poe2build/releases/latest" -OutFile "PoE2Build_Setup.exe"
   
   # 运行安装程序
   .\PoE2Build_Setup.exe
   ```

2. **安装依赖项**
   ```powershell
   # 安装Windows专用依赖
   pip install -r requirements-windows.txt
   ```

3. **验证安装**
   ```powershell
   # 运行集成测试
   .\scripts\test_windows_integration.ps1
   ```

### 🔧 手动配置

1. **配置Python虚拟环境**
   ```powershell
   # 创建虚拟环境
   python -m venv venv
   
   # 激活虚拟环境
   .\venv\Scripts\Activate.ps1
   
   # 安装依赖
   pip install -r requirements-windows.txt
   ```

2. **初始化Windows集成**
   ```python
   from src.poe2build.gui.services import initialize_windows_integration
   
   # 初始化系统集成
   success = initialize_windows_integration("path/to/app.exe")
   if success:
       print("Windows集成初始化成功")
   ```

## 核心功能

### 🎛️ 系统托盘管理

#### 基本使用

```python
from src.poe2build.gui.services.windows_integration import TrayIconManager

# 创建托盘图标管理器
tray = TrayIconManager("assets/icons/app.ico")

# 连接信号
tray.show_main_window.connect(show_app_window)
tray.quit_application.connect(quit_app)

# 显示系统通知
from src.poe2build.gui.services.windows_integration import NotificationConfig

config = NotificationConfig(
    title="构筑生成完成",
    message="您的PoE2构筑已成功生成！",
    icon="info",
    duration=5000
)

tray.show_notification(config)
```

#### 高级配置

```python
# 自定义右键菜单
def setup_custom_menu():
    menu = tray.context_menu
    
    # 添加自定义动作
    action = QAction("快速导出构筑", menu)
    action.triggered.connect(export_build_quick)
    menu.insertAction(menu.actions()[2], action)  # 在第3个位置插入
```

### 📁 文件关联管理

#### 注册文件类型

```python
from src.poe2build.gui.services.windows_integration import (
    RegistryManager, 
    FileAssociationManager, 
    FileAssociation
)

registry = RegistryManager()
manager = FileAssociationManager(registry)

# 创建.poe2build文件关联
association = FileAssociation(
    extension="poe2build",
    prog_id="PoE2Build.BuildFile",
    description="PoE2构筑文件",
    icon_path="C:\\Program Files\\PoE2Build\\app.exe",
    command='"C:\\Program Files\\PoE2Build\\app.exe" --open "%1"'
)

# 注册关联
success = manager.register_file_association(association)
```

#### 处理文件打开

```python
import sys

class MainApplication:
    def __init__(self):
        # 检查命令行参数
        if len(sys.argv) > 1 and sys.argv[1] == "--open":
            file_path = sys.argv[2] if len(sys.argv) > 2 else None
            if file_path:
                self.open_build_file(file_path)
    
    def open_build_file(self, file_path):
        """处理通过文件关联打开的构筑文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                build_data = json.load(f)
            
            # 加载构筑数据到界面
            self.load_build_data(build_data)
            
        except Exception as e:
            self.show_error(f"无法打开构筑文件: {e}")
```

### 🔔 Windows通知系统

#### Toast通知

```python
from src.poe2build.gui.services.windows_integration import WindowsNotificationManager

manager = WindowsNotificationManager()

# 发送Toast通知
config = NotificationConfig(
    title="PoE2Build通知",
    message="构筑计算已完成，DPS: 1,234,567",
    icon="info",
    duration=10000,
    action_callback=lambda: self.show_results()
)

success = manager.show_toast_notification(config)
```

#### 气球通知（向后兼容）

```python
# 如果Toast不可用，自动回退到气球通知
if not success:
    success = manager.show_balloon_notification(config)
```

### ⚙️ 自动启动管理

#### 启用/禁用自动启动

```python
from src.poe2build.gui.services.windows_integration import AutoStartManager

registry = RegistryManager()
auto_start = AutoStartManager(registry)

# 启用自动启动
app_path = "C:\\Program Files\\PoE2Build\\PoE2Build.exe"
success = auto_start.enable_auto_start(app_path)

# 检查状态
is_enabled = auto_start.is_auto_start_enabled()

# 禁用自动启动
success = auto_start.disable_auto_start()
```

#### 带启动参数的自动启动

```python
# 自动启动时最小化到托盘
app_path_with_args = f'"{app_path}" --minimized --silent'
success = auto_start.enable_auto_start(app_path_with_args)
```

### 🗂️ 注册表操作

#### 基本注册表访问

```python
from src.poe2build.gui.services.windows_integration import RegistryManager, RegistryHive

registry = RegistryManager()

# 写入配置
registry.set_value(
    RegistryHive.HKEY_CURRENT_USER,
    "SOFTWARE\\PoE2Build\\Settings",
    "Language",
    "zh-CN"
)

# 读取配置
language = registry.get_value(
    RegistryHive.HKEY_CURRENT_USER,
    "SOFTWARE\\PoE2Build\\Settings", 
    "Language"
)

# 删除配置
registry.delete_key(
    RegistryHive.HKEY_CURRENT_USER,
    "SOFTWARE\\PoE2Build\\TestKey"
)
```

#### 安全最佳实践

```python
class SafeRegistryManager:
    def __init__(self):
        self.registry = RegistryManager()
        self.app_key_base = "SOFTWARE\\PoE2Build"
    
    def save_user_setting(self, setting_name, value):
        """安全地保存用户设置"""
        try:
            key_path = f"{self.app_key_base}\\UserSettings"
            return self.registry.set_value(
                RegistryHive.HKEY_CURRENT_USER,
                key_path,
                setting_name,
                str(value)
            )
        except Exception as e:
            logging.error(f"保存设置失败: {e}")
            return False
    
    def cleanup_on_uninstall(self):
        """卸载时清理注册表"""
        try:
            self.registry.delete_key(
                RegistryHive.HKEY_CURRENT_USER,
                self.app_key_base
            )
        except Exception as e:
            logging.warning(f"注册表清理失败: {e}")
```

## 使用指南

### 🎮 用户界面集成

#### 在主窗口中集成Windows功能

```python
from PyQt6.QtWidgets import QMainWindow, QSystemTrayIcon
from src.poe2build.gui.services.windows_integration import get_windows_integration_service

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.windows_service = get_windows_integration_service()
        self.setup_ui()
        self.setup_windows_integration()
    
    def setup_windows_integration(self):
        if self.windows_service:
            # 连接文件打开信号
            self.windows_service.file_opened.connect(self.open_build_file)
            
            # 连接系统事件信号
            self.windows_service.system_event.connect(self.handle_system_event)
            
            # 设置托盘图标
            self.setup_tray_icon()
    
    def setup_tray_icon(self):
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = self.windows_service.tray_manager
            
            # 连接托盘信号
            self.tray_icon.show_main_window.connect(self.show_and_activate)
            self.tray_icon.quit_application.connect(self.close)
    
    def closeEvent(self, event):
        """重写关闭事件，最小化到托盘而不是退出"""
        if self.tray_icon and self.tray_icon.tray_icon.isVisible():
            self.hide()
            self.windows_service.show_notification(
                "PoE2Build继续运行",
                "应用程序已最小化到系统托盘",
                "info"
            )
            event.ignore()
        else:
            event.accept()
```

#### 设置页面集成

```python
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.windows_service = get_windows_integration_service()
        self.setup_windows_settings()
    
    def setup_windows_settings(self):
        layout = QVBoxLayout()
        
        # 自动启动复选框
        self.auto_start_checkbox = QCheckBox("开机自动启动")
        if self.windows_service:
            auto_start_manager = self.windows_service.auto_start_manager
            self.auto_start_checkbox.setChecked(
                auto_start_manager.is_auto_start_enabled()
            )
            self.auto_start_checkbox.toggled.connect(self.toggle_auto_start)
        
        # 通知设置
        self.notifications_checkbox = QCheckBox("启用系统通知")
        self.notifications_checkbox.setChecked(True)
        
        # 托盘设置
        self.minimize_to_tray_checkbox = QCheckBox("最小化到系统托盘")
        self.minimize_to_tray_checkbox.setChecked(True)
        
        layout.addWidget(self.auto_start_checkbox)
        layout.addWidget(self.notifications_checkbox)
        layout.addWidget(self.minimize_to_tray_checkbox)
        
        self.setLayout(layout)
    
    def toggle_auto_start(self, checked):
        if self.windows_service:
            self.windows_service.setup_auto_start(checked)
```

### 📝 构建和打包

#### 使用PyInstaller构建

```powershell
# 基础构建
.\scripts\build_gui.ps1 -Mode Production

# 高级构建（包含签名和优化）
.\scripts\build_gui.ps1 -Mode Production -Optimization Full -CodeSigning -CertificatePath "cert.pfx"
```

#### 创建安装程序

```powershell
# 创建NSIS安装程序
.\scripts\create_installer.ps1 -Formats NSIS

# 创建多格式安装包
.\scripts\create_installer.ps1 -Formats @("NSIS", "MSI", "Portable") -CodeSigning
```

#### 安装程序功能

生成的安装程序包含以下功能：

- ✅ 完整的Windows系统集成
- ✅ 文件关联自动配置
- ✅ 开始菜单和桌面快捷方式
- ✅ 自动启动选项
- ✅ 卸载程序
- ✅ 用户数据保护
- ✅ Windows防火墙配置
- ✅ 数字签名验证

## 开发接口

### 🔌 核心API

#### WindowsIntegrationService

```python
class WindowsIntegrationService:
    """Windows系统集成主服务"""
    
    def __init__(self, app_executable_path: str = None)
    def initialize_file_associations(self) -> bool
    def setup_auto_start(self, enabled: bool) -> bool
    def show_notification(self, title: str, message: str, icon: str = "info", duration: int = 5000) -> bool
    def handle_file_open(self, file_path: str)
    def get_system_info(self) -> Dict[str, Any]
    def cleanup_integration(self)
```

#### 信号和事件

```python
# 可连接的Qt信号
file_opened = pyqtSignal(str)           # 文件被打开
notification_received = pyqtSignal(dict) # 收到通知
system_event = pyqtSignal(str, dict)    # 系统事件
```

#### 实用工具函数

```python
# 全局访问函数
def get_windows_integration_service(app_executable_path: str = None) -> Optional[WindowsIntegrationService]
def initialize_windows_integration(app_executable_path: str = None) -> bool
```

### 🧪 测试接口

```python
# 运行完整测试套件
python -m pytest tests/integration/test_windows_integration.py -v

# 运行特定功能测试
.\scripts\test_windows_integration.ps1 -TestSuite TrayIcon -Interactive

# 自动化测试
.\scripts\test_windows_integration.ps1 -TestSuite @("Registry", "FileAssoc", "AutoStart")
```

## 故障排除

### ❗ 常见问题

#### 1. 托盘图标不显示

**原因**: 系统托盘功能被禁用或PyQt6未正确安装

**解决方案**:
```powershell
# 检查系统托盘设置
Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer" | Select-Object EnableAutoTray

# 重新安装PyQt6
pip uninstall PyQt6
pip install PyQt6>=6.4.0

# 测试托盘功能
.\scripts\test_windows_integration.ps1 -TestSuite TrayIcon -Interactive
```

#### 2. 文件关联失败

**原因**: 缺少管理员权限或注册表访问受限

**解决方案**:
```powershell
# 以管理员身份运行PowerShell
Start-Process powershell -Verb RunAs

# 手动注册文件关联
reg add "HKCR\.poe2build" /ve /d "PoE2Build.BuildFile" /f
reg add "HKCR\PoE2Build.BuildFile\shell\open\command" /ve /d "\"C:\Program Files\PoE2Build\PoE2Build.exe\" --open \"%1\"" /f
```

#### 3. 通知不工作

**原因**: Windows通知系统被禁用或应用权限不足

**解决方案**:
```powershell
# 检查通知设置
Get-WindowsCapability -Online | Where-Object Name -like "*Notifications*"

# 启用Toast通知
New-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings\PoE2Build" -Name "ShowInActionCenter" -Value 1 -PropertyType DWORD -Force

# 测试通知功能
.\scripts\test_windows_integration.ps1 -TestSuite Notifications -Interactive
```

#### 4. 自动启动无效

**原因**: 用户权限不足或应用路径不正确

**解决方案**:
```python
# 检查当前自动启动状态
from src.poe2build.gui.services.windows_integration import *

registry = RegistryManager()
auto_start = AutoStartManager(registry)

# 获取当前设置
current_value = registry.get_value(
    RegistryHive.HKEY_CURRENT_USER,
    "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
    "PoE2Build"
)

print(f"当前自动启动设置: {current_value}")

# 重新设置正确的路径
app_path = os.path.abspath("PoE2Build.exe")
auto_start.enable_auto_start(app_path)
```

### 🔍 调试模式

启用详细日志记录：

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('windows_integration_debug.log'),
        logging.StreamHandler()
    ]
)

# 创建集成服务
service = get_windows_integration_service()
```

### 📊 性能监控

```python
import time
import psutil

def monitor_integration_performance():
    """监控Windows集成功能的性能"""
    process = psutil.Process()
    
    # 记录初始状态
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # 执行集成功能测试
    start_time = time.time()
    
    service = get_windows_integration_service()
    service.show_notification("性能测试", "测试通知消息")
    
    end_time = time.time()
    
    # 记录结果
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    execution_time = (end_time - start_time) * 1000  # ms
    
    print(f"内存使用: {initial_memory:.2f}MB -> {final_memory:.2f}MB")
    print(f"执行时间: {execution_time:.2f}ms")
```

## 高级配置

### ⚙️ 系统级配置

#### 企业部署配置

```ini
; enterprise.ini - 企业部署配置文件
[WindowsIntegration]
EnableSystemTray=true
EnableFileAssociation=true
EnableAutoStart=false
EnableNotifications=true
NotificationLevel=info

[Security]
RequireDigitalSignature=true
AllowRegistryModification=true
RestrictFileAccess=false

[Updates]
AutoCheckUpdates=true
UpdateChannel=stable
```

#### 组策略配置

使用组策略管理Windows集成功能：

```powershell
# 创建组策略模板
$gpoPath = "\\domain.local\sysvol\domain.local\Policies\PolicyDefinitions"

# 复制ADMX模板文件
Copy-Item "templates\PoE2Build.admx" "$gpoPath\"
Copy-Item "templates\PoE2Build.adml" "$gpoPath\zh-CN\"
```

#### 注册表部署脚本

```batch
@echo off
REM PoE2Build企业部署脚本

REM 配置默认设置
reg add "HKLM\SOFTWARE\PoE2Build\Defaults" /v "EnableTrayIcon" /t REG_DWORD /d 1 /f
reg add "HKLM\SOFTWARE\PoE2Build\Defaults" /v "AutoStart" /t REG_DWORD /d 0 /f
reg add "HKLM\SOFTWARE\PoE2Build\Defaults" /v "NotificationLevel" /t REG_SZ /d "info" /f

REM 配置安全策略
reg add "HKLM\SOFTWARE\PoE2Build\Security" /v "RequireElevation" /t REG_DWORD /d 0 /f
reg add "HKLM\SOFTWARE\PoE2Build\Security" /v "AllowFileAssoc" /t REG_DWORD /d 1 /f

echo PoE2Build企业配置完成
pause
```

### 🔧 自定义集成

#### 扩展托盘菜单

```python
class CustomTrayManager(TrayIconManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_custom_menu_items()
    
    def add_custom_menu_items(self):
        if not self.context_menu:
            return
        
        # 添加分隔符
        self.context_menu.addSeparator()
        
        # 添加自定义菜单项
        export_action = QAction("导出所有构筑", self.context_menu)
        export_action.triggered.connect(self.export_all_builds)
        self.context_menu.addAction(export_action)
        
        import_action = QAction("批量导入构筑", self.context_menu)
        import_action.triggered.connect(self.import_builds)
        self.context_menu.addAction(import_action)
        
        # 添加子菜单
        tools_menu = self.context_menu.addMenu("工具")
        
        calc_action = QAction("构筑计算器", tools_menu)
        calc_action.triggered.connect(self.open_calculator)
        tools_menu.addAction(calc_action)
        
        compare_action = QAction("构筑对比", tools_menu)
        compare_action.triggered.connect(self.open_comparator)
        tools_menu.addAction(compare_action)
    
    def export_all_builds(self):
        # 实现批量导出逻辑
        pass
    
    def import_builds(self):
        # 实现批量导入逻辑
        pass
```

#### 自定义通知类型

```python
class CustomNotificationManager(WindowsNotificationManager):
    def __init__(self):
        super().__init__()
        self.notification_types = {
            'build_complete': {
                'icon': 'success',
                'duration': 8000,
                'sound': 'build_complete.wav'
            },
            'error': {
                'icon': 'error', 
                'duration': 15000,
                'sound': 'error.wav'
            },
            'update_available': {
                'icon': 'info',
                'duration': 10000,
                'sound': 'notify.wav'
            }
        }
    
    def show_typed_notification(self, notification_type: str, title: str, message: str):
        """显示特定类型的通知"""
        if notification_type not in self.notification_types:
            notification_type = 'info'
        
        config_template = self.notification_types[notification_type]
        
        config = NotificationConfig(
            title=title,
            message=message,
            icon=config_template['icon'],
            duration=config_template['duration']
        )
        
        # 播放声音（如果有）
        if 'sound' in config_template:
            self.play_notification_sound(config_template['sound'])
        
        return self.show_toast_notification(config)
    
    def play_notification_sound(self, sound_file: str):
        """播放通知声音"""
        import winsound
        try:
            sound_path = f"assets/sounds/{sound_file}"
            if os.path.exists(sound_path):
                winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as e:
            logging.warning(f"播放通知声音失败: {e}")
```

---

## 📞 技术支持

如果您在使用Windows集成功能时遇到问题，请按以下步骤获取帮助：

### 1. 自助诊断
```powershell
# 运行集成测试
.\scripts\test_windows_integration.ps1 -Verbose

# 检查日志文件
Get-Content "logs\windows_integration_*.log" -Tail 50
```

### 2. 收集系统信息
```python
from src.poe2build.gui.services.windows_integration import get_windows_integration_service

service = get_windows_integration_service()
if service:
    system_info = service.get_system_info()
    print(json.dumps(system_info, indent=2))
```

### 3. 联系支持
- **GitHub Issues**: [提交问题报告](https://github.com/yourusername/poe2build/issues)
- **技术文档**: 查看项目Wiki获取更多信息
- **社区讨论**: 参与GitHub Discussions

---

**最后更新**: 2024年01月
**版本**: 2.0.0
**维护者**: PoE2Build开发团队