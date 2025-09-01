#!/usr/bin/env pwsh
<#
.SYNOPSIS
    PoE2智能构筑生成器 - Windows开发环境自动设置脚本
    
.DESCRIPTION
    一键式开发环境配置脚本，自动完成Python虚拟环境创建、依赖安装、IDE配置、
    Git钩子设置等所有开发环境准备工作。专为Windows GUI应用开发优化。
    
.PARAMETER SkipIDE
    跳过IDE配置（VSCode、PyCharm）
    
.PARAMETER SkipGitHooks
    跳过Git钩子配置
    
.PARAMETER InstallLocation
    指定虚拟环境安装位置，默认为项目根目录下的venv
    
.PARAMETER PythonVersion
    指定Python版本要求，默认为3.11+
    
.EXAMPLE
    .\scripts\setup_dev_env.ps1
    运行完整的环境设置
    
.EXAMPLE
    .\scripts\setup_dev_env.ps1 -SkipIDE -SkipGitHooks
    仅设置基础Python环境，跳过IDE和Git配置
    
.NOTES
    Author: PoE2Build Team
    Version: 2.0.0
    Requires: PowerShell 5.1+, Python 3.11+, Windows 10/11
#>

[CmdletBinding()]
param(
    [switch]$SkipIDE,
    [switch]$SkipGitHooks,
    [string]$InstallLocation = "venv",
    [string]$PythonVersion = "3.11"
)

# 脚本配置
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# 颜色配置
$Colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Cyan"
    Progress = "Magenta"
}

# 全局变量
$script:LogFile = "logs\setup_dev_env_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
$script:StartTime = Get-Date

#region Helper Functions

function Write-ColorOutput {
    param(
        [Parameter(Mandatory)]
        [string]$Message,
        
        [Parameter(Mandatory)]
        [string]$Color,
        
        [switch]$NoNewline
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    
    # 写入日志文件
    if (!(Test-Path -Path (Split-Path $script:LogFile -Parent))) {
        New-Item -ItemType Directory -Path (Split-Path $script:LogFile -Parent) -Force | Out-Null
    }
    Add-Content -Path $script:LogFile -Value $logMessage
    
    # 控制台输出
    if ($NoNewline) {
        Write-Host $Message -ForegroundColor $Color -NoNewline
    } else {
        Write-Host $Message -ForegroundColor $Color
    }
}

function Write-Success { param([string]$Message) Write-ColorOutput -Message "✅ $Message" -Color $Colors.Success }
function Write-Warning { param([string]$Message) Write-ColorOutput -Message "⚠️ $Message" -Color $Colors.Warning }
function Write-Error { param([string]$Message) Write-ColorOutput -Message "❌ $Message" -Color $Colors.Error }
function Write-Info { param([string]$Message) Write-ColorOutput -Message "ℹ️ $Message" -Color $Colors.Info }
function Write-Progress { param([string]$Message) Write-ColorOutput -Message "🔄 $Message" -Color $Colors.Progress }

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-Command {
    param([string]$CommandName)
    return [bool](Get-Command $CommandName -ErrorAction SilentlyContinue)
}

function Invoke-SafeCommand {
    param(
        [Parameter(Mandatory)]
        [string]$Command,
        
        [string]$ErrorMessage = "命令执行失败",
        
        [switch]$IgnoreError
    )
    
    try {
        Write-Info "执行: $Command"
        Invoke-Expression $Command
        if ($LASTEXITCODE -ne 0 -and !$IgnoreError) {
            throw "$ErrorMessage (退出码: $LASTEXITCODE)"
        }
    }
    catch {
        if ($IgnoreError) {
            Write-Warning "$ErrorMessage : $($_.Exception.Message)"
        } else {
            Write-Error "$ErrorMessage : $($_.Exception.Message)"
            throw
        }
    }
}

#endregion

#region Environment Detection

function Test-SystemRequirements {
    Write-Progress "检测系统要求..."
    
    $requirements = @{
        "Windows版本" = $false
        "PowerShell版本" = $false
        "磁盘空间" = $false
        "网络连接" = $false
    }
    
    # Windows版本检查
    $os = Get-CimInstance -ClassName Win32_OperatingSystem
    $osVersion = [System.Version]$os.Version
    if ($osVersion -ge [System.Version]"10.0.17763") {  # Windows 10 1809+
        $requirements["Windows版本"] = $true
        Write-Success "Windows版本: $($os.Caption) (Build $($os.BuildNumber))"
    } else {
        Write-Warning "Windows版本可能不完全兼容: $($os.Caption)"
    }
    
    # PowerShell版本检查
    if ($PSVersionTable.PSVersion -ge [System.Version]"5.1") {
        $requirements["PowerShell版本"] = $true
        Write-Success "PowerShell版本: $($PSVersionTable.PSVersion)"
    } else {
        Write-Error "需要PowerShell 5.1或更高版本"
    }
    
    # 磁盘空间检查（需要至少3GB）
    $drive = Get-PSDrive -Name (Split-Path $PWD -Qualifier).TrimEnd(':')
    $freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
    if ($freeSpaceGB -ge 3) {
        $requirements["磁盘空间"] = $true
        Write-Success "可用磁盘空间: $freeSpaceGB GB"
    } else {
        Write-Warning "磁盘空间不足: $freeSpaceGB GB (建议至少3GB)"
    }
    
    # 网络连接检查
    try {
        $null = Invoke-RestMethod -Uri "https://pypi.org/simple/" -TimeoutSec 10
        $requirements["网络连接"] = $true
        Write-Success "网络连接正常"
    }
    catch {
        Write-Warning "网络连接可能存在问题，可能影响依赖包下载"
    }
    
    return $requirements
}

function Test-PythonInstallation {
    Write-Progress "检测Python安装..."
    
    $pythonCommands = @("python", "python3", "py")
    $pythonInfo = @{}
    
    foreach ($cmd in $pythonCommands) {
        if (Test-Command $cmd) {
            try {
                $version = & $cmd --version 2>&1
                $versionMatch = [regex]::Match($version, "Python (\d+\.\d+\.\d+)")
                if ($versionMatch.Success) {
                    $pythonVersion = [System.Version]$versionMatch.Groups[1].Value
                    $pythonInfo[$cmd] = @{
                        Version = $pythonVersion
                        Path = (Get-Command $cmd).Source
                        Compatible = $pythonVersion -ge [System.Version]$PythonVersion
                    }
                }
            }
            catch {
                Write-Warning "无法获取 $cmd 版本信息"
            }
        }
    }
    
    # 选择最佳Python版本
    $bestPython = $pythonInfo.GetEnumerator() | 
        Where-Object { $_.Value.Compatible } |
        Sort-Object { $_.Value.Version } -Descending |
        Select-Object -First 1
    
    if ($bestPython) {
        Write-Success "找到兼容的Python: $($bestPython.Key) $($bestPython.Value.Version)"
        return $bestPython
    } else {
        $availableVersions = $pythonInfo.Values | ForEach-Object { $_.Version } | Sort-Object -Descending
        if ($availableVersions) {
            Write-Error "需要Python $PythonVersion+，当前版本: $($availableVersions -join ', ')"
        } else {
            Write-Error "未找到Python安装，请先安装Python $PythonVersion+"
        }
        return $null
    }
}

#endregion

#region Virtual Environment Setup

function New-VirtualEnvironment {
    param([string]$PythonCommand, [string]$VenvPath)
    
    Write-Progress "创建Python虚拟环境..."
    
    # 清理现有虚拟环境
    if (Test-Path $VenvPath) {
        Write-Info "检测到现有虚拟环境，正在清理..."
        try {
            Remove-Item $VenvPath -Recurse -Force
            Write-Success "现有虚拟环境已清理"
        }
        catch {
            Write-Error "无法清理现有虚拟环境: $($_.Exception.Message)"
            throw
        }
    }
    
    # 创建新的虚拟环境
    try {
        Write-Info "使用 $PythonCommand 创建虚拟环境..."
        & $PythonCommand -m venv $VenvPath
        if ($LASTEXITCODE -ne 0) {
            throw "虚拟环境创建失败"
        }
        Write-Success "虚拟环境创建成功: $VenvPath"
    }
    catch {
        Write-Error "虚拟环境创建失败: $($_.Exception.Message)"
        throw
    }
    
    # 验证虚拟环境
    $activateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        Write-Success "虚拟环境验证成功"
        return $activateScript
    } else {
        Write-Error "虚拟环境创建不完整"
        throw "虚拟环境验证失败"
    }
}

function Install-Dependencies {
    param([string]$VenvPath)
    
    Write-Progress "安装项目依赖..."
    
    $pipExecutable = Join-Path $VenvPath "Scripts\pip.exe"
    if (!(Test-Path $pipExecutable)) {
        Write-Error "未找到pip可执行文件"
        throw "pip不可用"
    }
    
    # 升级pip
    Write-Info "升级pip到最新版本..."
    Invoke-SafeCommand "$pipExecutable install --upgrade pip" "pip升级失败"
    
    # 依赖文件列表
    $dependencyFiles = @(
        @{ File = "requirements.txt"; Name = "核心依赖" },
        @{ File = "requirements-gui.txt"; Name = "GUI依赖" },
        @{ File = "requirements-dev.txt"; Name = "开发工具依赖" }
    )
    
    foreach ($dep in $dependencyFiles) {
        if (Test-Path $dep.File) {
            Write-Info "安装$($dep.Name): $($dep.File)"
            try {
                Invoke-SafeCommand "$pipExecutable install -r $($dep.File)" "$($dep.Name)安装失败"
                Write-Success "$($dep.Name)安装完成"
            }
            catch {
                Write-Warning "$($dep.Name)安装失败，继续执行其他安装"
            }
        } else {
            Write-Warning "依赖文件不存在: $($dep.File)"
        }
    }
    
    # 安装额外的Windows特定依赖
    $windowsDeps = @("pywin32", "pyinstaller")
    foreach ($dep in $windowsDeps) {
        Write-Info "安装Windows依赖: $dep"
        Invoke-SafeCommand "$pipExecutable install $dep" "$dep 安装失败" -IgnoreError
    }
    
    # 验证关键依赖
    Write-Progress "验证关键依赖安装..."
    $keyDependencies = @("requests", "PyQt6", "psutil")
    $pythonExecutable = Join-Path $VenvPath "Scripts\python.exe"
    
    foreach ($dep in $keyDependencies) {
        try {
            & $pythonExecutable -c "import $dep; print(f'✅ $dep: {$dep.__version__ if hasattr($dep, '__version__') else 'OK'}')"
            if ($LASTEXITCODE -eq 0) {
                Write-Success "$dep 验证通过"
            }
        }
        catch {
            Write-Warning "$dep 验证失败"
        }
    }
}

#endregion

#region IDE Configuration

function Set-VSCodeConfiguration {
    Write-Progress "配置VSCode开发环境..."
    
    if (!(Test-Command "code")) {
        Write-Warning "VSCode未安装或不在PATH中，跳过配置"
        return
    }
    
    # 创建.vscode目录
    $vscodeDir = ".vscode"
    if (!(Test-Path $vscodeDir)) {
        New-Item -ItemType Directory $vscodeDir -Force | Out-Null
    }
    
    # 设置VSCode工作区配置
    $workspaceSettings = @{
        "python.pythonPath" = ".\venv\Scripts\python.exe"
        "python.linting.enabled" = $true
        "python.linting.pylintEnabled" = $true
        "python.formatting.provider" = "black"
        "python.formatting.blackArgs" = @("--line-length", "88")
        "files.associations" = @{
            "*.poe2build" = "json"
        }
        "editor.formatOnSave" = $true
        "editor.rulers" = @(88)
        "terminal.integrated.defaultProfile.windows" = "PowerShell"
    } | ConvertTo-Json -Depth 3
    
    Set-Content -Path "$vscodeDir\settings.json" -Value $workspaceSettings -Encoding UTF8
    
    # 推荐扩展配置
    $extensions = @{
        "recommendations" = @(
            "ms-python.python",
            "ms-python.black-formatter",
            "ms-python.pylint",
            "ms-toolsai.jupyter",
            "ms-vscode.powershell",
            "redhat.vscode-yaml"
        )
    } | ConvertTo-Json -Depth 2
    
    Set-Content -Path "$vscodeDir\extensions.json" -Value $extensions -Encoding UTF8
    
    # 调试配置
    $launchConfig = @{
        "version" = "0.2.0"
        "configurations" = @(
            @{
                "name" = "PoE2 Console App"
                "type" = "python"
                "request" = "launch"
                "program" = "poe2_ai_orchestrator.py"
                "console" = "integratedTerminal"
                "cwd" = "`${workspaceFolder}"
            },
            @{
                "name" = "PoE2 GUI App"
                "type" = "python" 
                "request" = "launch"
                "program" = "poe2_gui_app.py"
                "console" = "integratedTerminal"
                "cwd" = "`${workspaceFolder}"
                "args" = @("--debug")
            }
        )
    } | ConvertTo-Json -Depth 4
    
    Set-Content -Path "$vscodeDir\launch.json" -Value $launchConfig -Encoding UTF8
    Write-Success "VSCode配置完成"
}

function Set-PyCharmConfiguration {
    Write-Progress "配置PyCharm开发环境..."
    
    $ideaDir = ".idea"
    if (!(Test-Path $ideaDir)) {
        New-Item -ItemType Directory $ideaDir -Force | Out-Null
    }
    
    # Python解释器配置
    $miscXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<project version="4">
  <component name="ProjectRootManager" version="2" project-jdk-name="Python 3.11 (poe2build)" project-jdk-type="Python SDK" />
</project>
"@
    Set-Content -Path "$ideaDir\misc.xml" -Value $miscXml -Encoding UTF8
    
    # 模块配置
    $modulesXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<project version="4">
  <component name="ProjectModuleManager">
    <modules>
      <module fileurl="file://`$PROJECT_DIR`$/.idea/poe2build.iml" filepath="`$PROJECT_DIR`$/.idea/poe2build.iml" />
    </modules>
  </component>
</project>
"@
    Set-Content -Path "$ideaDir\modules.xml" -Value $modulesXml -Encoding UTF8
    
    Write-Success "PyCharm配置完成"
}

#endregion

#region Git Configuration

function Set-GitHooks {
    Write-Progress "配置Git钩子..."
    
    if (!(Test-Path ".git")) {
        Write-Warning "不是Git仓库，跳过Git钩子配置"
        return
    }
    
    $hooksDir = ".git\hooks"
    
    # Pre-commit钩子
    $preCommitHook = @"
#!/bin/sh
# PoE2Build Pre-commit Hook
echo "🔍 运行pre-commit检查..."

# 激活虚拟环境
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
fi

# 运行代码格式化检查
echo "📝 检查代码格式..."
python -m black --check --diff . || {
    echo "❌ 代码格式检查失败，请运行: python -m black ."
    exit 1
}

# 运行基础测试
echo "🧪 运行快速测试..."
python -m pytest tests/unit --tb=short --quiet || {
    echo "❌ 基础测试失败"
    exit 1
}

echo "✅ Pre-commit检查通过"
"@
    Set-Content -Path "$hooksDir\pre-commit" -Value $preCommitHook -Encoding UTF8
    
    # 如果支持chmod，设置执行权限
    if (Test-Command "chmod") {
        chmod +x "$hooksDir\pre-commit"
    }
    
    Write-Success "Git钩子配置完成"
}

#endregion

#region Configuration Files

function New-ConfigurationFiles {
    Write-Progress "创建配置文件..."
    
    # .env配置文件
    if (!(Test-Path ".env")) {
        $envContent = @"
# PoE2 Build Generator Environment Configuration
# 复制并重命名为 .env，然后根据需要修改

# 应用配置
APP_NAME=PoE2Build
APP_VERSION=2.0.0
DEBUG=false

# GUI配置
GUI_THEME=poe2_dark
GUI_STARTUP_MODE=normal
GUI_LOG_LEVEL=INFO

# API配置
POE2_SCOUT_RATE_LIMIT=30
POE2_NINJA_RATE_LIMIT=10
POE2DB_RATE_LIMIT=20

# 缓存配置
CACHE_ENABLED=true
CACHE_TTL_MARKET=600
CACHE_TTL_BUILDS=1800

# PoB2集成配置
POB2_AUTO_DETECT=true
POB2_PATH=""  # 留空自动检测

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/poe2build.log
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=5
"@
        Set-Content -Path ".env.example" -Value $envContent -Encoding UTF8
        Copy-Item ".env.example" ".env"
        Write-Success "环境配置文件创建完成"
    }
    
    # GUI配置文件
    $configDir = "config"
    if (!(Test-Path $configDir)) {
        New-Item -ItemType Directory $configDir -Force | Out-Null
    }
    
    $guiConfig = @{
        "theme" = "poe2_dark"
        "window" = @{
            "width" = 1200
            "height" = 800
            "resizable" = $true
            "center_on_startup" = $true
        }
        "performance" = @{
            "animation_enabled" = $true
            "gpu_acceleration" = $true
            "memory_limit_mb" = 200
        }
        "features" = @{
            "auto_update" = $true
            "system_tray" = $true
            "notifications" = $true
        }
    } | ConvertTo-Json -Depth 3
    
    Set-Content -Path "$configDir\gui_settings.json" -Value $guiConfig -Encoding UTF8
    Write-Success "GUI配置文件创建完成"
}

#endregion

#region Environment Verification

function Test-EnvironmentSetup {
    Write-Progress "验证环境设置..."
    
    $verificationResults = @{}
    $pythonExecutable = Join-Path $InstallLocation "Scripts\python.exe"
    
    # 测试Python环境
    try {
        $version = & $pythonExecutable --version 2>&1
        $verificationResults["Python虚拟环境"] = $true
        Write-Success "Python虚拟环境: $version"
    }
    catch {
        $verificationResults["Python虚拟环境"] = $false
        Write-Error "Python虚拟环境验证失败"
    }
    
    # 测试关键模块导入
    $testModules = @("requests", "PyQt6.QtWidgets", "psutil")
    foreach ($module in $testModules) {
        try {
            $testScript = "import $module; print('OK')"
            $result = & $pythonExecutable -c $testScript 2>&1
            if ($result -eq "OK") {
                $verificationResults[$module] = $true
                Write-Success "模块 $module: 可用"
            } else {
                $verificationResults[$module] = $false
                Write-Warning "模块 $module: 不可用"
            }
        }
        catch {
            $verificationResults[$module] = $false
            Write-Warning "模块 $module: 导入失败"
        }
    }
    
    # 测试应用启动
    if (Test-Path "poe2_ai_orchestrator.py") {
        try {
            $testResult = & $pythonExecutable "poe2_ai_orchestrator.py" "--version" 2>&1
            $verificationResults["应用启动"] = $true
            Write-Success "应用启动测试: 通过"
        }
        catch {
            $verificationResults["应用启动"] = $false
            Write-Warning "应用启动测试: 失败"
        }
    }
    
    return $verificationResults
}

#endregion

#region Main Execution

function Show-Header {
    Write-Host ""
    Write-Host "🚀 PoE2智能构筑生成器 - Windows开发环境设置" -ForegroundColor $Colors.Info
    Write-Host "=" * 60 -ForegroundColor $Colors.Info
    Write-Host "版本: 2.0.0" -ForegroundColor $Colors.Info
    Write-Host "平台: Windows 10/11" -ForegroundColor $Colors.Info
    Write-Host "日期: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor $Colors.Info
    Write-Host "=" * 60 -ForegroundColor $Colors.Info
    Write-Host ""
}

function Show-Summary {
    param([hashtable]$Results)
    
    $elapsed = (Get-Date) - $script:StartTime
    
    Write-Host ""
    Write-Host "📊 环境设置完成报告" -ForegroundColor $Colors.Info
    Write-Host "=" * 40 -ForegroundColor $Colors.Info
    Write-Host "总用时: $($elapsed.ToString('mm\:ss'))" -ForegroundColor $Colors.Info
    Write-Host "日志文件: $script:LogFile" -ForegroundColor $Colors.Info
    Write-Host ""
    
    $successful = 0
    $total = $Results.Count
    
    foreach ($result in $Results.GetEnumerator()) {
        if ($result.Value) {
            Write-Success "$($result.Key): 完成"
            $successful++
        } else {
            Write-Warning "$($result.Key): 失败"
        }
    }
    
    Write-Host ""
    if ($successful -eq $total) {
        Write-Host "🎉 环境设置完全成功！" -ForegroundColor $Colors.Success
        Write-Host ""
        Write-Host "下一步操作:" -ForegroundColor $Colors.Info
        Write-Host "1. 激活虚拟环境: venv\Scripts\Activate.ps1" -ForegroundColor $Colors.Info
        Write-Host "2. 运行应用: python poe2_ai_orchestrator.py" -ForegroundColor $Colors.Info
        Write-Host "3. 开始开发: code . (如果使用VSCode)" -ForegroundColor $Colors.Info
    } else {
        Write-Host "⚠️ 环境设置部分完成 ($successful/$total)" -ForegroundColor $Colors.Warning
        Write-Host "请查看日志文件了解详细信息: $script:LogFile" -ForegroundColor $Colors.Warning
    }
    
    Write-Host ""
}

# 主执行流程
try {
    Show-Header
    
    # 检查管理员权限
    if (Test-Administrator) {
        Write-Warning "检测到管理员权限，建议使用普通用户权限运行"
    }
    
    # 系统要求检测
    $systemReqs = Test-SystemRequirements
    
    # Python环境检测
    $pythonInfo = Test-PythonInstallation
    if (!$pythonInfo) {
        throw "Python环境检测失败"
    }
    
    # 创建虚拟环境
    $activateScript = New-VirtualEnvironment -PythonCommand $pythonInfo.Key -VenvPath $InstallLocation
    
    # 安装依赖
    Install-Dependencies -VenvPath $InstallLocation
    
    # IDE配置
    if (!$SkipIDE) {
        Set-VSCodeConfiguration
        Set-PyCharmConfiguration
    } else {
        Write-Info "跳过IDE配置"
    }
    
    # Git钩子配置
    if (!$SkipGitHooks) {
        Set-GitHooks
    } else {
        Write-Info "跳过Git钩子配置"
    }
    
    # 创建配置文件
    New-ConfigurationFiles
    
    # 环境验证
    $verificationResults = Test-EnvironmentSetup
    
    # 显示总结
    Show-Summary -Results $verificationResults
    
}
catch {
    Write-Error "环境设置失败: $($_.Exception.Message)"
    Write-Host "详细错误信息请查看日志文件: $script:LogFile" -ForegroundColor $Colors.Warning
    exit 1
}

#endregion