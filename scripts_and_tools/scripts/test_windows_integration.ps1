#!/usr/bin/env pwsh
<#
.SYNOPSIS
    PoE2智能构筑生成器 - Windows系统集成功能测试脚本
    
.DESCRIPTION
    全面测试Windows系统集成功能，包括：
    - 系统托盘功能
    - 文件关联
    - 注册表操作
    - Windows通知系统
    - 自动启动管理
    - 权限验证
    
.PARAMETER TestSuite
    测试套件：All, TrayIcon, FileAssoc, Registry, Notifications, AutoStart
    
.PARAMETER Verbose
    详细输出模式
    
.PARAMETER Interactive
    交互测试模式
    
.EXAMPLE
    .\scripts\test_windows_integration.ps1
    运行所有Windows集成测试
    
.EXAMPLE
    .\scripts\test_windows_integration.ps1 -TestSuite TrayIcon -Interactive
    交互式测试系统托盘功能
    
.NOTES
    Author: PoE2Build Team  
    Version: 2.0.0
    Requires: Windows 10+, Python 3.11+, PyQt6
#>

[CmdletBinding()]
param(
    [ValidateSet("All", "TrayIcon", "FileAssoc", "Registry", "Notifications", "AutoStart")]
    [string[]]$TestSuite = @("All"),
    
    [switch]$Verbose,
    
    [switch]$Interactive
)

# 脚本配置
$ErrorActionPreference = "Continue"  # 允许测试失败继续执行
$ProgressPreference = "SilentlyContinue"

# 颜色定义
$Colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Cyan"
    Progress = "Magenta"
    Test = "White"
}

# 全局变量
$script:LogFile = "logs\test_windows_integration_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
$script:StartTime = Get-Date
$script:TestResults = @{}
$script:TestStats = @{
    Passed = 0
    Failed = 0
    Skipped = 0
    Total = 0
}

#region Helper Functions

function Write-ColorOutput {
    param(
        [Parameter(Mandatory)]
        [string]$Message,
        
        [Parameter(Mandatory)]
        [string]$Color
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    
    # 确保日志目录存在
    if (!(Test-Path -Path (Split-Path $script:LogFile -Parent))) {
        New-Item -ItemType Directory -Path (Split-Path $script:LogFile -Parent) -Force | Out-Null
    }
    Add-Content -Path $script:LogFile -Value $logMessage
    
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success { param([string]$Message) Write-ColorOutput -Message "✅ $Message" -Color $Colors.Success }
function Write-Warning { param([string]$Message) Write-ColorOutput -Message "⚠️ $Message" -Color $Colors.Warning }
function Write-Error { param([string]$Message) Write-ColorOutput -Message "❌ $Message" -Color $Colors.Error }
function Write-Info { param([string]$Message) Write-ColorOutput -Message "ℹ️ $Message" -Color $Colors.Info }
function Write-Progress { param([string]$Message) Write-ColorOutput -Message "🔄 $Message" -Color $Colors.Progress }
function Write-Test { param([string]$Message) Write-ColorOutput -Message "🧪 $Message" -Color $Colors.Test }

function Test-Result {
    param(
        [string]$TestName,
        [bool]$Passed,
        [string]$Details = ""
    )
    
    $script:TestResults[$TestName] = @{
        Passed = $Passed
        Details = $Details
        Timestamp = Get-Date
    }
    
    $script:TestStats.Total++
    if ($Passed) {
        $script:TestStats.Passed++
        Write-Success "PASS: $TestName $(if($Details) { "- $Details" })"
    } else {
        $script:TestStats.Failed++
        Write-Error "FAIL: $TestName $(if($Details) { "- $Details" })"
    }
}

function Test-Skip {
    param(
        [string]$TestName,
        [string]$Reason = ""
    )
    
    $script:TestResults[$TestName] = @{
        Passed = $null
        Skipped = $true
        Details = $Reason
        Timestamp = Get-Date
    }
    
    $script:TestStats.Skipped++
    $script:TestStats.Total++
    Write-Warning "SKIP: $TestName $(if($Reason) { "- $Reason" })"
}

#endregion

#region Environment Tests

function Test-Environment {
    Write-Progress "测试环境验证..."
    
    # Python环境检查
    $pythonExe = "venv\Scripts\python.exe"
    if (Test-Path $pythonExe) {
        try {
            $version = & $pythonExe --version 2>&1
            Test-Result "Python环境" $true "版本: $version"
        } catch {
            Test-Result "Python环境" $false "Python执行失败"
        }
    } else {
        Test-Skip "Python环境" "虚拟环境不存在"
    }
    
    # PyQt6检查
    try {
        $qtCheck = & $pythonExe -c "import PyQt6; print('PyQt6可用')" 2>&1
        if ($qtCheck -like "*PyQt6可用*") {
            Test-Result "PyQt6依赖" $true
        } else {
            Test-Result "PyQt6依赖" $false "PyQt6导入失败"
        }
    } catch {
        Test-Result "PyQt6依赖" $false "无法检查PyQt6"
    }
    
    # Windows版本检查
    try {
        $osInfo = Get-CimInstance Win32_OperatingSystem
        $winVersion = "$($osInfo.Caption) (Build $($osInfo.BuildNumber))"
        
        if ($osInfo.BuildNumber -ge 17763) {  # Windows 10 1809+
            Test-Result "Windows版本" $true $winVersion
        } else {
            Test-Result "Windows版本" $false "需要Windows 10 1809或更高版本"
        }
    } catch {
        Test-Result "Windows版本" $false "无法检查Windows版本"
    }
    
    # 管理员权限检查
    try {
        $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
        $isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        
        Test-Result "管理员权限" $isAdmin $(if ($isAdmin) { "具有管理员权限" } else { "普通用户权限" })
    } catch {
        Test-Result "管理员权限" $false "权限检查失败"
    }
}

#endregion

#region Windows Integration Module Tests

function Test-WindowsIntegrationModule {
    Write-Progress "测试Windows集成模块..."
    
    $pythonExe = "venv\Scripts\python.exe"
    
    # 模块导入测试
    $importTest = @"
import sys
import os
sys.path.insert(0, '.')

try:
    from src.poe2build.gui.services.windows_integration import (
        WindowsIntegrationService,
        TrayIconManager, 
        RegistryManager,
        FileAssociationManager,
        AutoStartManager,
        WindowsNotificationManager
    )
    print('SUCCESS: 所有Windows集成模块导入成功')
except ImportError as e:
    print(f'ERROR: 模块导入失败 - {e}')
except Exception as e:
    print(f'ERROR: 其他错误 - {e}')
"@
    
    try {
        $result = & $pythonExe -c $importTest 2>&1
        if ($result -like "*SUCCESS*") {
            Test-Result "模块导入" $true "所有Windows集成组件可用"
        } else {
            Test-Result "模块导入" $false $result
        }
    } catch {
        Test-Result "模块导入" $false "Python执行失败"
    }
    
    # 服务初始化测试
    $initTest = @"
import sys
import os
sys.path.insert(0, '.')

try:
    from src.poe2build.gui.services.windows_integration import get_windows_integration_service
    
    # 模拟可执行文件路径
    service = get_windows_integration_service('test_app.exe')
    
    if service:
        print('SUCCESS: Windows集成服务初始化成功')
        
        # 测试系统信息获取
        info = service.get_system_info()
        if info and 'platform' in info:
            print(f'SUCCESS: 系统信息获取成功 - {info["platform"]}')
        else:
            print('WARNING: 系统信息获取失败')
    else:
        print('ERROR: Windows集成服务初始化失败')
        
except Exception as e:
    print(f'ERROR: {e}')
"@
    
    try {
        $result = & $pythonExe -c $initTest 2>&1
        if ($result -like "*SUCCESS: Windows集成服务初始化成功*") {
            Test-Result "服务初始化" $true "集成服务正常初始化"
        } else {
            Test-Result "服务初始化" $false $result
        }
    } catch {
        Test-Result "服务初始化" $false "初始化测试失败"
    }
}

#endregion

#region Tray Icon Tests

function Test-TrayIcon {
    Write-Progress "测试系统托盘功能..."
    
    if (!$Interactive) {
        Test-Skip "托盘图标显示" "需要交互模式"
        return
    }
    
    Write-Test "测试系统托盘图标..."
    Write-Info "此测试需要GUI环境和用户交互"
    
    $trayTest = @"
import sys
import os
sys.path.insert(0, '.')

try:
    from PyQt6.QtWidgets import QApplication
    from src.poe2build.gui.services.windows_integration import TrayIconManager
    
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 创建托盘图标管理器
    tray = TrayIconManager()
    
    if tray.tray_icon and tray.tray_icon.isVisible():
        print('SUCCESS: 系统托盘图标创建并显示成功')
        
        # 测试通知功能
        from src.poe2build.gui.services.windows_integration import NotificationConfig
        config = NotificationConfig(
            title='测试通知',
            message='这是一个测试通知消息',
            icon='info',
            duration=3000
        )
        
        tray.show_notification(config)
        print('SUCCESS: 通知发送成功')
    else:
        print('ERROR: 托盘图标创建失败')
        
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
"@
    
    # 询问用户是否进行交互测试
    $userChoice = Read-Host "是否测试系统托盘功能？这将显示托盘图标和通知 (y/N)"
    
    if ($userChoice -eq 'y' -or $userChoice -eq 'Y') {
        try {
            Write-Info "启动托盘测试，请查看系统托盘区域..."
            $result = & $pythonExe -c $trayTest 2>&1
            
            if ($result -like "*SUCCESS: 系统托盘图标创建并显示成功*") {
                Test-Result "托盘图标显示" $true "图标创建成功"
            } else {
                Test-Result "托盘图标显示" $false $result
            }
            
            if ($result -like "*SUCCESS: 通知发送成功*") {
                Test-Result "系统通知" $true "通知功能正常"
            } else {
                Test-Result "系统通知" $false "通知功能异常"
            }
            
            Write-Info "请手动检查托盘区域是否显示PoE2Build图标"
            Read-Host "按Enter继续..."
            
        } catch {
            Test-Result "托盘图标显示" $false "测试执行失败"
        }
    } else {
        Test-Skip "托盘图标显示" "用户跳过交互测试"
    }
}

#endregion

#region Registry Tests

function Test-Registry {
    Write-Progress "测试注册表操作..."
    
    $registryTest = @"
import sys
import os
sys.path.insert(0, '.')

try:
    from src.poe2build.gui.services.windows_integration import RegistryManager, RegistryHive
    
    manager = RegistryManager()
    test_key = 'SOFTWARE\\PoE2Build\\Test'
    test_value = 'TestValue'
    test_data = 'TestData_123'
    
    # 测试写入
    success = manager.set_value(RegistryHive.HKEY_CURRENT_USER, test_key, test_value, test_data)
    if success:
        print('SUCCESS: 注册表写入成功')
        
        # 测试读取
        data = manager.get_value(RegistryHive.HKEY_CURRENT_USER, test_key, test_value)
        if data == test_data:
            print('SUCCESS: 注册表读取成功')
            
            # 测试删除
            delete_success = manager.delete_key(RegistryHive.HKEY_CURRENT_USER, test_key)
            if delete_success:
                print('SUCCESS: 注册表删除成功')
            else:
                print('WARNING: 注册表删除失败')
        else:
            print(f'ERROR: 注册表读取失败，期望: {test_data}，实际: {data}')
    else:
        print('ERROR: 注册表写入失败')
        
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
"@
    
    try {
        $result = & $pythonExe -c $registryTest 2>&1
        
        if ($result -like "*SUCCESS: 注册表写入成功*") {
            Test-Result "注册表写入" $true
        } else {
            Test-Result "注册表写入" $false $result
        }
        
        if ($result -like "*SUCCESS: 注册表读取成功*") {
            Test-Result "注册表读取" $true
        } else {
            Test-Result "注册表读取" $false $result
        }
        
        if ($result -like "*SUCCESS: 注册表删除成功*") {
            Test-Result "注册表删除" $true
        } else {
            Test-Result "注册表删除" $false $result
        }
        
    } catch {
        Test-Result "注册表操作" $false "测试执行失败"
    }
}

#endregion

#region File Association Tests

function Test-FileAssociation {
    Write-Progress "测试文件关联..."
    
    $fileAssocTest = @"
import sys
import os
sys.path.insert(0, '.')

try:
    from src.poe2build.gui.services.windows_integration import (
        RegistryManager, 
        FileAssociationManager, 
        FileAssociation
    )
    
    registry = RegistryManager()
    manager = FileAssociationManager(registry)
    
    # 创建测试文件关联
    association = FileAssociation(
        extension='poe2test',
        prog_id='PoE2Build.TestFile',
        description='PoE2Build测试文件',
        icon_path='test_icon.ico',
        command='test_app.exe "%1"'
    )
    
    # 测试注册
    success = manager.register_file_association(association)
    if success:
        print('SUCCESS: 文件关联注册成功')
        
        # 测试取消注册
        unregister_success = manager.unregister_file_association('poe2test', 'PoE2Build.TestFile')
        if unregister_success:
            print('SUCCESS: 文件关联取消成功')
        else:
            print('WARNING: 文件关联取消失败')
    else:
        print('ERROR: 文件关联注册失败')
        
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
"@
    
    try {
        $result = & $pythonExe -c $fileAssocTest 2>&1
        
        if ($result -like "*SUCCESS: 文件关联注册成功*") {
            Test-Result "文件关联注册" $true
        } else {
            Test-Result "文件关联注册" $false $result
        }
        
        if ($result -like "*SUCCESS: 文件关联取消成功*") {
            Test-Result "文件关联取消" $true
        } else {
            Test-Result "文件关联取消" $false $result
        }
        
    } catch {
        Test-Result "文件关联操作" $false "测试执行失败"
    }
}

#endregion

#region Auto Start Tests

function Test-AutoStart {
    Write-Progress "测试自动启动管理..."
    
    $autoStartTest = @"
import sys
import os
sys.path.insert(0, '.')

try:
    from src.poe2build.gui.services.windows_integration import RegistryManager, AutoStartManager
    
    registry = RegistryManager()
    manager = AutoStartManager(registry)
    test_exe_path = 'C:\\Test\\TestApp.exe'
    
    # 测试启用自动启动
    enable_success = manager.enable_auto_start(test_exe_path)
    if enable_success:
        print('SUCCESS: 自动启动启用成功')
        
        # 测试检查状态
        is_enabled = manager.is_auto_start_enabled()
        if is_enabled:
            print('SUCCESS: 自动启动状态检查成功')
            
            # 测试禁用自动启动
            disable_success = manager.disable_auto_start()
            if disable_success:
                print('SUCCESS: 自动启动禁用成功')
                
                # 再次检查状态
                is_disabled = not manager.is_auto_start_enabled()
                if is_disabled:
                    print('SUCCESS: 自动启动禁用状态确认')
                else:
                    print('WARNING: 自动启动状态确认失败')
            else:
                print('WARNING: 自动启动禁用失败')
        else:
            print('ERROR: 自动启动状态检查失败')
    else:
        print('ERROR: 自动启动启用失败')
        
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
"@
    
    try {
        $result = & $pythonExe -c $autoStartTest 2>&1
        
        if ($result -like "*SUCCESS: 自动启动启用成功*") {
            Test-Result "自动启动启用" $true
        } else {
            Test-Result "自动启动启用" $false $result
        }
        
        if ($result -like "*SUCCESS: 自动启动状态检查成功*") {
            Test-Result "自动启动状态检查" $true
        } else {
            Test-Result "自动启动状态检查" $false $result
        }
        
        if ($result -like "*SUCCESS: 自动启动禁用成功*") {
            Test-Result "自动启动禁用" $true
        } else {
            Test-Result "自动启动禁用" $false $result
        }
        
    } catch {
        Test-Result "自动启动管理" $false "测试执行失败"
    }
}

#endregion

#region Notifications Tests

function Test-Notifications {
    Write-Progress "测试Windows通知系统..."
    
    if (!$Interactive) {
        Test-Skip "原生通知显示" "需要交互模式"
        return
    }
    
    Write-Test "测试Windows原生通知..."
    
    $notificationTest = @"
import sys
import os
sys.path.insert(0, '.')

try:
    from src.poe2build.gui.services.windows_integration import (
        WindowsNotificationManager, 
        NotificationConfig
    )
    
    manager = WindowsNotificationManager()
    
    # 测试Toast通知
    config = NotificationConfig(
        title='PoE2Build测试通知',
        message='这是Windows集成测试中的通知消息',
        icon='info',
        duration=5000
    )
    
    success = manager.show_toast_notification(config)
    if success:
        print('SUCCESS: Toast通知发送成功')
    else:
        # 尝试气球通知
        balloon_success = manager.show_balloon_notification(config)
        if balloon_success:
            print('SUCCESS: 气球通知发送成功')
        else:
            print('ERROR: 所有通知方式都失败')
        
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
"@
    
    $userChoice = Read-Host "是否测试Windows原生通知？这将显示系统通知 (y/N)"
    
    if ($userChoice -eq 'y' -or $userChoice -eq 'Y') {
        try {
            Write-Info "发送测试通知，请查看屏幕右下角..."
            $result = & $pythonExe -c $notificationTest 2>&1
            
            if ($result -like "*SUCCESS: *通知发送成功*") {
                Test-Result "原生通知显示" $true "通知系统正常工作"
                Write-Info "请检查是否收到了系统通知"
                Read-Host "按Enter继续..."
            } else {
                Test-Result "原生通知显示" $false $result
            }
            
        } catch {
            Test-Result "原生通知显示" $false "通知测试执行失败"
        }
    } else {
        Test-Skip "原生通知显示" "用户跳过交互测试"
    }
}

#endregion

#region Test Summary and Reporting

function Show-TestSummary {
    $elapsed = (Get-Date) - $script:StartTime
    
    Write-Host ""
    Write-Host "🧪 Windows集成功能测试报告" -ForegroundColor $Colors.Info
    Write-Host "=" * 50 -ForegroundColor $Colors.Info
    Write-Host "测试总用时: $($elapsed.ToString('mm\:ss'))" -ForegroundColor $Colors.Info
    Write-Host "日志文件: $script:LogFile" -ForegroundColor $Colors.Info
    Write-Host ""
    
    Write-Host "📊 测试统计:" -ForegroundColor $Colors.Info
    Write-Host "总测试数: $($script:TestStats.Total)" -ForegroundColor $Colors.Info
    Write-Host "通过: $($script:TestStats.Passed)" -ForegroundColor $Colors.Success
    Write-Host "失败: $($script:TestStats.Failed)" -ForegroundColor $Colors.Error
    Write-Host "跳过: $($script:TestStats.Skipped)" -ForegroundColor $Colors.Warning
    
    $successRate = if ($script:TestStats.Total -gt 0) { 
        [math]::Round(($script:TestStats.Passed / ($script:TestStats.Total - $script:TestStats.Skipped)) * 100, 1) 
    } else { 
        0 
    }
    Write-Host "成功率: $successRate%" -ForegroundColor $(if ($successRate -ge 80) { $Colors.Success } elseif ($successRate -ge 60) { $Colors.Warning } else { $Colors.Error })
    
    Write-Host ""
    Write-Host "📋 详细结果:" -ForegroundColor $Colors.Info
    
    foreach ($testName in $script:TestResults.Keys | Sort-Object) {
        $result = $script:TestResults[$testName]
        if ($result.Skipped) {
            Write-Host "  ⏭️ $testName - 跳过: $($result.Details)" -ForegroundColor $Colors.Warning
        } elseif ($result.Passed) {
            Write-Host "  ✅ $testName $(if($result.Details) { "- $($result.Details)" })" -ForegroundColor $Colors.Success
        } else {
            Write-Host "  ❌ $testName $(if($result.Details) { "- $($result.Details)" })" -ForegroundColor $Colors.Error
        }
    }
    
    Write-Host ""
    
    if ($script:TestStats.Failed -gt 0) {
        Write-Host "⚠️ 部分测试失败，请检查日志文件获取详细信息" -ForegroundColor $Colors.Warning
        Write-Host "💡 建议操作:" -ForegroundColor $Colors.Info
        Write-Host "  1. 检查Python虚拟环境是否正确设置" -ForegroundColor $Colors.Info
        Write-Host "  2. 确保PyQt6和Windows扩展库已安装" -ForegroundColor $Colors.Info  
        Write-Host "  3. 以管理员身份运行以获得完整权限测试" -ForegroundColor $Colors.Info
        Write-Host "  4. 检查Windows版本兼容性" -ForegroundColor $Colors.Info
    } else {
        Write-Host "🎉 所有测试通过！Windows集成功能正常" -ForegroundColor $Colors.Success
    }
    
    Write-Host ""
}

#endregion

#region Main Execution

function Show-Header {
    Write-Host ""
    Write-Host "🧪 PoE2智能构筑生成器 - Windows集成测试" -ForegroundColor $Colors.Info
    Write-Host "=" * 60 -ForegroundColor $Colors.Info
    Write-Host "版本: 2.0.0" -ForegroundColor $Colors.Info
    Write-Host "测试套件: $($TestSuite -join ', ')" -ForegroundColor $Colors.Info
    Write-Host "交互模式: $Interactive" -ForegroundColor $Colors.Info
    Write-Host "日期: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor $Colors.Info
    Write-Host "=" * 60 -ForegroundColor $Colors.Info
    Write-Host ""
}

# 主执行流程
try {
    Show-Header
    
    # 展开测试套件
    if ($TestSuite -contains "All") {
        $TestSuite = @("TrayIcon", "FileAssoc", "Registry", "Notifications", "AutoStart")
    }
    
    # 始终运行环境测试
    Test-Environment
    Test-WindowsIntegrationModule
    
    # 运行指定的测试套件
    foreach ($suite in $TestSuite) {
        switch ($suite) {
            "TrayIcon" { Test-TrayIcon }
            "FileAssoc" { Test-FileAssociation }
            "Registry" { Test-Registry }
            "Notifications" { Test-Notifications }
            "AutoStart" { Test-AutoStart }
        }
    }
    
    # 显示测试总结
    Show-TestSummary
    
    # 返回适当的退出码
    if ($script:TestStats.Failed -gt 0) {
        exit 1
    } else {
        exit 0
    }
    
} catch {
    Write-Error "测试执行失败: $($_.Exception.Message)"
    Write-Host "详细错误信息请查看日志文件: $script:LogFile" -ForegroundColor $Colors.Warning
    exit 1
}

#endregion