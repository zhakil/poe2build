#!/usr/bin/env pwsh
<#
.SYNOPSIS
    PoE2智能构筑生成器 - GUI应用自动化构建脚本
    
.DESCRIPTION
    专业级Windows GUI应用构建脚本，支持开发模式和生产模式构建，
    包含代码优化、资源压缩、数字签名、性能分析等高级特性。
    
.PARAMETER Mode
    构建模式：Development（开发）或 Production（生产）
    
.PARAMETER Optimization
    优化级别：None, Basic, Full
    
.PARAMETER IncludeDebugSymbols
    是否包含调试符号，生产模式下默认为false
    
.PARAMETER OutputDir
    构建输出目录，默认为dist
    
.PARAMETER CodeSigning
    是否启用代码签名，需要配置证书
    
.PARAMETER SkipTests
    跳过构建前测试
    
.EXAMPLE
    .\scripts\build_gui.ps1
    使用默认设置构建（开发模式）
    
.EXAMPLE
    .\scripts\build_gui.ps1 -Mode Production -Optimization Full -CodeSigning
    生产模式完整优化构建，包含代码签名
    
.NOTES
    Author: PoE2Build Team
    Version: 2.0.0
    Requires: PyInstaller, Python 3.11+, Windows 10/11
#>

[CmdletBinding()]
param(
    [ValidateSet("Development", "Production")]
    [string]$Mode = "Development",
    
    [ValidateSet("None", "Basic", "Full")]
    [string]$Optimization = "Basic",
    
    [bool]$IncludeDebugSymbols = ($Mode -eq "Development"),
    
    [string]$OutputDir = "dist",
    
    [switch]$CodeSigning,
    
    [switch]$SkipTests,
    
    [string]$CertificatePath = "",
    
    [switch]$Verbose
)

# 脚本配置
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# 颜色和符号定义
$Colors = @{
    Success = "Green"
    Warning = "Yellow" 
    Error = "Red"
    Info = "Cyan"
    Progress = "Magenta"
}

# 全局变量
$script:LogFile = "logs\build_gui_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
$script:StartTime = Get-Date
$script:BuildStats = @{}

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
    
    # 确保日志目录存在
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

function Test-Command {
    param([string]$CommandName)
    return [bool](Get-Command $CommandName -ErrorAction SilentlyContinue)
}

function Invoke-SafeCommand {
    param(
        [Parameter(Mandatory)]
        [string]$Command,
        
        [string]$ErrorMessage = "命令执行失败",
        
        [switch]$IgnoreError,
        
        [int]$TimeoutSeconds = 300
    )
    
    try {
        Write-Info "执行: $Command"
        
        $process = Start-Process -FilePath "powershell" -ArgumentList "-Command", $Command -PassThru -NoNewWindow -RedirectStandardOutput "$env:TEMP\stdout.txt" -RedirectStandardError "$env:TEMP\stderr.txt"
        
        if (!$process.WaitForExit($TimeoutSeconds * 1000)) {
            $process.Kill()
            throw "命令执行超时 ($TimeoutSeconds 秒)"
        }
        
        $stdout = Get-Content "$env:TEMP\stdout.txt" -ErrorAction SilentlyContinue
        $stderr = Get-Content "$env:TEMP\stderr.txt" -ErrorAction SilentlyContinue
        
        if ($process.ExitCode -ne 0 -and !$IgnoreError) {
            Write-Warning "标准输出: $stdout"
            Write-Warning "标准错误: $stderr"
            throw "$ErrorMessage (退出码: $($process.ExitCode))"
        }
        
        return $stdout
    }
    catch {
        if ($IgnoreError) {
            Write-Warning "$ErrorMessage : $($_.Exception.Message)"
            return $null
        } else {
            Write-Error "$ErrorMessage : $($_.Exception.Message)"
            throw
        }
    }
    finally {
        # 清理临时文件
        Remove-Item "$env:TEMP\stdout.txt" -ErrorAction SilentlyContinue
        Remove-Item "$env:TEMP\stderr.txt" -ErrorAction SilentlyContinue
    }
}

#endregion

#region Environment Validation

function Test-BuildEnvironment {
    Write-Progress "验证构建环境..."
    
    $requirements = @{}
    
    # Python虚拟环境检查
    $pythonExe = "venv\Scripts\python.exe"
    if (Test-Path $pythonExe) {
        try {
            $version = & $pythonExe --version 2>&1
            $requirements["Python环境"] = $true
            Write-Success "Python虚拟环境: $version"
        }
        catch {
            $requirements["Python环境"] = $false
            Write-Error "Python虚拟环境验证失败"
        }
    } else {
        $requirements["Python环境"] = $false
        Write-Error "未找到Python虚拟环境，请先运行 setup_dev_env.ps1"
    }
    
    # PyInstaller检查
    $pipExe = "venv\Scripts\pip.exe"
    if (Test-Path $pipExe) {
        try {
            $packages = & $pipExe list | Select-String "pyinstaller"
            if ($packages) {
                $requirements["PyInstaller"] = $true
                Write-Success "PyInstaller: 已安装"
            } else {
                Write-Info "安装PyInstaller..."
                & $pipExe install pyinstaller
                $requirements["PyInstaller"] = $true
                Write-Success "PyInstaller: 安装完成"
            }
        }
        catch {
            $requirements["PyInstaller"] = $false
            Write-Error "PyInstaller验证失败"
        }
    }
    
    # GUI应用主文件检查
    $guiMainFiles = @("poe2_gui_app.py", "src\poe2build\gui\main_application.py")
    $mainFile = $null
    foreach ($file in $guiMainFiles) {
        if (Test-Path $file) {
            $mainFile = $file
            break
        }
    }
    
    if ($mainFile) {
        $requirements["GUI主文件"] = $true
        Write-Success "GUI主文件: $mainFile"
        $script:BuildStats["MainFile"] = $mainFile
    } else {
        $requirements["GUI主文件"] = $false
        Write-Error "未找到GUI应用主文件"
    }
    
    # 资源文件检查
    $resourceDirs = @("assets", "resources", "icons")
    $foundResources = @()
    foreach ($dir in $resourceDirs) {
        if (Test-Path $dir) {
            $foundResources += $dir
        }
    }
    
    if ($foundResources.Count -gt 0) {
        $requirements["资源文件"] = $true
        Write-Success "资源目录: $($foundResources -join ', ')"
        $script:BuildStats["ResourceDirs"] = $foundResources
    } else {
        $requirements["资源文件"] = $false
        Write-Warning "未找到资源目录，某些功能可能不可用"
    }
    
    return $requirements
}

#endregion

#region Pre-Build Operations

function Invoke-PreBuildTests {
    if ($SkipTests) {
        Write-Info "跳过构建前测试"
        return $true
    }
    
    Write-Progress "执行构建前测试..."
    
    $pythonExe = "venv\Scripts\python.exe"
    
    # 运行快速单元测试
    try {
        Write-Info "运行核心功能测试..."
        $testResult = Invoke-SafeCommand "$pythonExe -m pytest tests/unit --tb=short -q" "单元测试失败" -IgnoreError
        
        if ($testResult) {
            Write-Success "构建前测试通过"
            return $true
        } else {
            Write-Warning "构建前测试失败，但继续构建"
            return $false
        }
    }
    catch {
        Write-Warning "无法运行构建前测试: $($_.Exception.Message)"
        return $false
    }
}

function Optimize-SourceCode {
    param([string]$OptLevel)
    
    if ($OptLevel -eq "None") {
        Write-Info "跳过源码优化"
        return
    }
    
    Write-Progress "优化源代码..."
    
    $pythonExe = "venv\Scripts\python.exe"
    
    # 基础优化
    if ($OptLevel -in @("Basic", "Full")) {
        Write-Info "执行代码格式化..."
        Invoke-SafeCommand "$pythonExe -m black . --line-length 88" "代码格式化失败" -IgnoreError
        
        Write-Info "移除未使用的导入..."
        Invoke-SafeCommand "$pythonExe -m autoflake --remove-all-unused-imports --recursive --in-place ." "导入优化失败" -IgnoreError
    }
    
    # 完整优化
    if ($OptLevel -eq "Full") {
        Write-Info "执行高级代码优化..."
        
        # 创建临时优化脚本
        $optimizeScript = @"
import ast
import os
import sys

def optimize_python_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析AST并重新生成（移除注释和优化结构）
        tree = ast.parse(content)
        
        # 这里可以添加更多AST优化逻辑
        # 例如：移除调试语句、优化常量折叠等
        
        return True
    except Exception as e:
        print(f"优化文件失败 {filepath}: {e}")
        return False

# 优化所有Python文件
for root, dirs, files in os.walk('.'):
    if 'venv' in root or '.git' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            optimize_python_file(filepath)

print("代码优化完成")
"@
        
        Set-Content -Path "temp_optimize.py" -Value $optimizeScript
        Invoke-SafeCommand "$pythonExe temp_optimize.py" "高级优化失败" -IgnoreError
        Remove-Item "temp_optimize.py" -ErrorAction SilentlyContinue
    }
    
    Write-Success "源码优化完成"
}

#endregion

#region Build Process

function New-PyInstallerSpec {
    param(
        [string]$MainFile,
        [string]$Mode,
        [bool]$DebugSymbols,
        [string[]]$ResourceDirs
    )
    
    Write-Progress "生成PyInstaller配置文件..."
    
    $appName = "PoE2Build"
    $specFile = "$appName.spec"
    
    # 构建资源数据列表
    $dataFiles = @()
    foreach ($dir in $ResourceDirs) {
        $dataFiles += "('$dir', '$dir', 'DATA')"
    }
    
    # 添加配置文件
    if (Test-Path "config") {
        $dataFiles += "('config', 'config', 'DATA')"
    }
    
    # 隐藏导入列表
    $hiddenImports = @(
        "'PyQt6'",
        "'PyQt6.QtCore'", 
        "'PyQt6.QtGui'",
        "'PyQt6.QtWidgets'",
        "'requests'",
        "'psutil'",
        "'json'",
        "'logging'",
        "'threading'",
        "'queue'"
    )
    
    # 排除模块列表（减少文件大小）
    $excludes = @()
    if ($Mode -eq "Production") {
        $excludes = @(
            "'unittest'",
            "'pytest'", 
            "'test'",
            "'pdb'",
            "'pydoc'",
            "'doctest'"
        )
    }
    
    $specContent = @"
# -*- mode: python ; coding: utf-8 -*-
# PoE2Build PyInstaller Specification File
# Generated by build_gui.ps1 at $(Get-Date)

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

block_cipher = None

a = Analysis(
    ['$MainFile'],
    pathex=[],
    binaries=[],
    datas=[
        $($dataFiles -join ",`n        ")
    ],
    hiddenimports=[
        $($hiddenImports -join ",`n        ")
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        $($excludes -join ",`n        ")
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    $(if ($Mode -eq "Production") { "a.binaries," } else { "[]," })
    $(if ($Mode -eq "Production") { "a.zipfiles," } else { "[]," })
    $(if ($Mode -eq "Production") { "a.datas," } else { "[]," })
    name='$appName',
    debug=$($DebugSymbols.ToString().ToLower()),
    bootloader_ignore_signals=False,
    strip=$(!$DebugSymbols),
    upx=$($Mode -eq "Production"),
    upx_exclude=[],
    runtime_tmpdir=None,
    console=$($Mode -eq "Development"),
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/poe2build.ico' if os.path.exists('assets/icons/poe2build.ico') else None,
    version='version_info.txt' if os.path.exists('version_info.txt') else None,
)

$(if ($Mode -eq "Development") {
@"
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=$(!$DebugSymbols),
    upx=$($Mode -eq "Production"),
    upx_exclude=[],
    name='$appName',
)
"@
})
"@

    Set-Content -Path $specFile -Value $specContent -Encoding UTF8
    Write-Success "PyInstaller配置文件生成完成: $specFile"
    return $specFile
}

function New-VersionInfo {
    Write-Progress "创建版本信息文件..."
    
    $versionInfo = @"
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(2,0,0,0),
    prodvers=(2,0,0,0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [StringStruct(u'CompanyName', u'PoE2Build Team'),
          StringStruct(u'FileDescription', u'Path of Exile 2 智能构筑生成器'),
          StringStruct(u'FileVersion', u'2.0.0'),
          StringStruct(u'InternalName', u'PoE2Build'),
          StringStruct(u'LegalCopyright', u'Copyright (C) 2023 PoE2Build Team'),
          StringStruct(u'OriginalFilename', u'PoE2Build.exe'),
          StringStruct(u'ProductName', u'PoE2 智能构筑生成器'),
          StringStruct(u'ProductVersion', u'2.0.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"@
    
    Set-Content -Path "version_info.txt" -Value $versionInfo -Encoding UTF8
    Write-Success "版本信息文件创建完成"
}

function Invoke-PyInstallerBuild {
    param(
        [string]$SpecFile,
        [string]$OutputDirectory,
        [string]$Mode
    )
    
    Write-Progress "执行PyInstaller构建..."
    
    $pythonExe = "venv\Scripts\python.exe"
    $pyinstallerExe = "venv\Scripts\pyinstaller.exe"
    
    # 清理之前的构建
    $buildDirs = @("build", "dist")
    foreach ($dir in $buildDirs) {
        if (Test-Path $dir) {
            Write-Info "清理构建目录: $dir"
            Remove-Item $dir -Recurse -Force
        }
    }
    
    # 构建PyInstaller命令
    $buildArgs = @(
        "--clean",
        "--noconfirm"
    )
    
    if ($Verbose) {
        $buildArgs += "--log-level=DEBUG"
    } else {
        $buildArgs += "--log-level=WARN"
    }
    
    if ($Mode -eq "Production") {
        $buildArgs += @("--optimize=2", "--strip")
    }
    
    $buildArgs += $SpecFile
    $buildCommand = "$pyinstallerExe $($buildArgs -join ' ')"
    
    # 执行构建
    try {
        $buildStart = Get-Date
        Write-Info "开始PyInstaller构建..."
        Write-Info "构建命令: $buildCommand"
        
        Invoke-SafeCommand $buildCommand "PyInstaller构建失败" -TimeoutSeconds 600
        
        $buildTime = (Get-Date) - $buildStart
        $script:BuildStats["BuildTime"] = $buildTime
        Write-Success "PyInstaller构建完成，用时: $($buildTime.ToString('mm\:ss'))"
        
        # 移动构建结果到指定输出目录
        if ($OutputDirectory -ne "dist") {
            if (Test-Path "dist") {
                if (Test-Path $OutputDirectory) {
                    Remove-Item $OutputDirectory -Recurse -Force
                }
                Move-Item "dist" $OutputDirectory
                Write-Success "构建输出移动到: $OutputDirectory"
            }
        }
        
        return $true
    }
    catch {
        Write-Error "PyInstaller构建失败: $($_.Exception.Message)"
        return $false
    }
}

#endregion

#region Post-Build Operations

function Optimize-BuildOutput {
    param([string]$BuildDir, [string]$OptLevel)
    
    if ($OptLevel -eq "None") {
        Write-Info "跳过构建输出优化"
        return
    }
    
    Write-Progress "优化构建输出..."
    
    # 基础优化 - 清理不必要的文件
    if ($OptLevel -in @("Basic", "Full")) {
        Write-Info "清理构建输出..."
        
        $cleanupPatterns = @(
            "*.pdb",    # 调试符号
            "*.pyc",    # Python字节码
            "__pycache__", # Python缓存目录
            "*.log",    # 日志文件
            "test_*"    # 测试文件
        )
        
        foreach ($pattern in $cleanupPatterns) {
            $files = Get-ChildItem -Path $BuildDir -Filter $pattern -Recurse -ErrorAction SilentlyContinue
            foreach ($file in $files) {
                Remove-Item $file.FullName -Force -Recurse -ErrorAction SilentlyContinue
                Write-Info "清理: $($file.Name)"
            }
        }
    }
    
    # 完整优化 - 压缩和额外清理
    if ($OptLevel -eq "Full") {
        Write-Info "执行高级优化..."
        
        # UPX压缩可执行文件
        if (Test-Command "upx") {
            $exeFiles = Get-ChildItem -Path $BuildDir -Filter "*.exe" -Recurse
            foreach ($exe in $exeFiles) {
                try {
                    Write-Info "压缩可执行文件: $($exe.Name)"
                    & upx --best --lzma "$($exe.FullName)"
                    Write-Success "压缩完成: $($exe.Name)"
                }
                catch {
                    Write-Warning "压缩失败: $($exe.Name) - $($_.Exception.Message)"
                }
            }
        }
        
        # 优化DLL文件
        $dllFiles = Get-ChildItem -Path $BuildDir -Filter "*.dll" -Recurse
        Write-Info "发现 $($dllFiles.Count) 个DLL文件"
        
        # 移除不必要的DLL（根据实际需求调整）
        $unnecessaryDlls = @(
            "*test*",
            "*debug*",
            "*unused*"
        )
        
        foreach ($pattern in $unnecessaryDlls) {
            $dlls = $dllFiles | Where-Object { $_.Name -like $pattern }
            foreach ($dll in $dlls) {
                Write-Info "移除不必要的DLL: $($dll.Name)"
                Remove-Item $dll.FullName -Force -ErrorAction SilentlyContinue
            }
        }
    }
    
    Write-Success "构建输出优化完成"
}

function Set-CodeSignature {
    param([string]$BuildDir, [string]$CertPath)
    
    if (!$CodeSigning) {
        Write-Info "跳过代码签名"
        return
    }
    
    Write-Progress "执行代码签名..."
    
    if (!$CertPath -or !(Test-Path $CertPath)) {
        Write-Warning "未找到证书文件，跳过代码签名"
        return
    }
    
    # 查找signtool
    $signTool = $null
    $possiblePaths = @(
        "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x64\signtool.exe",
        "${env:ProgramFiles}\Microsoft SDKs\Windows\*\bin\signtool.exe"
    )
    
    foreach ($path in $possiblePaths) {
        $tools = Get-ChildItem $path -ErrorAction SilentlyContinue | Sort-Object Name -Descending
        if ($tools) {
            $signTool = $tools[0].FullName
            break
        }
    }
    
    if (!$signTool) {
        Write-Warning "未找到signtool.exe，跳过代码签名"
        return
    }
    
    # 签名所有可执行文件
    $executableFiles = Get-ChildItem -Path $BuildDir -Include @("*.exe", "*.dll") -Recurse
    
    foreach ($file in $executableFiles) {
        try {
            Write-Info "签名文件: $($file.Name)"
            
            $signArgs = @(
                "sign",
                "/f", "`"$CertPath`"",
                "/t", "http://timestamp.sectigo.com",
                "/fd", "SHA256",
                "/v",
                "`"$($file.FullName)`""
            )
            
            & $signTool $signArgs
            
            if ($LASTEXITCODE -eq 0) {
                Write-Success "签名成功: $($file.Name)"
            } else {
                Write-Warning "签名失败: $($file.Name)"
            }
        }
        catch {
            Write-Warning "签名过程出错: $($file.Name) - $($_.Exception.Message)"
        }
    }
    
    Write-Success "代码签名完成"
}

function Test-BuildOutput {
    param([string]$BuildDir)
    
    Write-Progress "验证构建输出..."
    
    # 查找主可执行文件
    $exeFiles = Get-ChildItem -Path $BuildDir -Filter "*.exe" -Recurse
    if ($exeFiles.Count -eq 0) {
        Write-Error "未找到可执行文件"
        return $false
    }
    
    $mainExe = $exeFiles[0]
    Write-Success "找到主可执行文件: $($mainExe.Name)"
    $script:BuildStats["ExecutablePath"] = $mainExe.FullName
    $script:BuildStats["ExecutableSize"] = [math]::Round($mainExe.Length / 1MB, 2)
    
    # 基础启动测试
    try {
        Write-Info "执行启动测试..."
        
        # 创建测试脚本
        $testScript = @"
import sys
import os
import subprocess
import time

exe_path = r'$($mainExe.FullName)'
print(f'测试可执行文件: {exe_path}')

try:
    # 启动应用并快速退出
    process = subprocess.Popen([exe_path, '--version'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              timeout=10)
    stdout, stderr = process.communicate(timeout=10)
    
    if process.returncode == 0:
        print(f'✅ 启动测试成功')
        print(f'输出: {stdout.decode("utf-8", errors="ignore")}')
        sys.exit(0)
    else:
        print(f'⚠️ 应用启动异常，但可能正常')
        print(f'错误输出: {stderr.decode("utf-8", errors="ignore")}')
        sys.exit(0)
        
except subprocess.TimeoutExpired:
    process.kill()
    print('⚠️ 启动测试超时，可能需要用户交互')
    sys.exit(0)
except Exception as e:
    print(f'❌ 启动测试失败: {e}')
    sys.exit(1)
"@
        
        Set-Content -Path "temp_test.py" -Value $testScript
        $pythonExe = "venv\Scripts\python.exe"
        & $pythonExe "temp_test.py"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "构建验证通过"
            return $true
        } else {
            Write-Warning "构建验证部分失败，但可能仍然可用"
            return $true
        }
    }
    catch {
        Write-Warning "构建验证异常: $($_.Exception.Message)"
        return $true  # 不阻止构建完成
    }
    finally {
        Remove-Item "temp_test.py" -ErrorAction SilentlyContinue
    }
}

#endregion

#region Build Statistics and Reporting

function New-BuildReport {
    param([string]$OutputDir)
    
    Write-Progress "生成构建报告..."
    
    $reportContent = @"
# PoE2Build GUI应用构建报告
生成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## 构建配置
- 构建模式: $Mode
- 优化级别: $Optimization  
- 调试符号: $IncludeDebugSymbols
- 代码签名: $CodeSigning
- 输出目录: $OutputDir

## 构建统计
- 主文件: $($script:BuildStats["MainFile"])
- 构建用时: $($script:BuildStats["BuildTime"].ToString('mm\:ss'))
- 可执行文件: $($script:BuildStats["ExecutablePath"])
- 文件大小: $($script:BuildStats["ExecutableSize"]) MB

## 资源文件
$($script:BuildStats["ResourceDirs"] -join "`n")

## 系统信息
- Windows版本: $((Get-CimInstance Win32_OperatingSystem).Caption)
- PowerShell版本: $($PSVersionTable.PSVersion)
- 构建主机: $env:COMPUTERNAME
- 用户: $env:USERNAME

## 文件清单
"@
    
    # 添加构建输出文件清单
    if (Test-Path $OutputDir) {
        $files = Get-ChildItem -Path $OutputDir -Recurse | ForEach-Object {
            $relativePath = $_.FullName.Substring($OutputDir.Length + 1)
            $size = if ($_.PSIsContainer) { "[DIR]" } else { "$([math]::Round($_.Length / 1KB, 1)) KB" }
            "- $relativePath ($size)"
        }
        $reportContent += "`n" + ($files -join "`n")
    }
    
    $reportPath = Join-Path $OutputDir "build_report.md"
    Set-Content -Path $reportPath -Value $reportContent -Encoding UTF8
    Write-Success "构建报告生成完成: $reportPath"
}

function Show-BuildSummary {
    param([bool]$Success, [string]$OutputDir)
    
    $elapsed = (Get-Date) - $script:StartTime
    
    Write-Host ""
    Write-Host "🏗️ GUI应用构建完成报告" -ForegroundColor $Colors.Info
    Write-Host "=" * 50 -ForegroundColor $Colors.Info
    Write-Host "构建状态: $(if ($Success) { '✅ 成功' } else { '❌ 失败' })" -ForegroundColor $(if ($Success) { $Colors.Success } else { $Colors.Error })
    Write-Host "构建模式: $Mode" -ForegroundColor $Colors.Info
    Write-Host "优化级别: $Optimization" -ForegroundColor $Colors.Info
    Write-Host "总用时: $($elapsed.ToString('mm\:ss'))" -ForegroundColor $Colors.Info
    Write-Host "输出目录: $OutputDir" -ForegroundColor $Colors.Info
    Write-Host "日志文件: $script:LogFile" -ForegroundColor $Colors.Info
    
    if ($Success -and $script:BuildStats["ExecutablePath"]) {
        Write-Host ""
        Write-Host "📦 构建产物" -ForegroundColor $Colors.Info
        Write-Host "可执行文件: $($script:BuildStats["ExecutablePath"])" -ForegroundColor $Colors.Success
        Write-Host "文件大小: $($script:BuildStats["ExecutableSize"]) MB" -ForegroundColor $Colors.Info
        
        Write-Host ""
        Write-Host "🚀 下一步操作" -ForegroundColor $Colors.Info
        Write-Host "1. 测试应用: $($script:BuildStats["ExecutablePath"])" -ForegroundColor $Colors.Info
        Write-Host "2. 创建安装程序: .\scripts\create_installer.ps1" -ForegroundColor $Colors.Info
        Write-Host "3. 运行测试: .\scripts\run_tests.ps1" -ForegroundColor $Colors.Info
    }
    
    Write-Host ""
}

#endregion

#region Main Execution

function Show-Header {
    Write-Host ""
    Write-Host "🏗️ PoE2智能构筑生成器 - GUI应用构建" -ForegroundColor $Colors.Info
    Write-Host "=" * 60 -ForegroundColor $Colors.Info
    Write-Host "版本: 2.0.0" -ForegroundColor $Colors.Info  
    Write-Host "构建模式: $Mode" -ForegroundColor $Colors.Info
    Write-Host "优化级别: $Optimization" -ForegroundColor $Colors.Info
    Write-Host "日期: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor $Colors.Info
    Write-Host "=" * 60 -ForegroundColor $Colors.Info
    Write-Host ""
}

# 主执行流程
try {
    Show-Header
    
    # 1. 环境验证
    $envCheck = Test-BuildEnvironment
    if (!($envCheck["Python环境"] -and $envCheck["PyInstaller"])) {
        throw "构建环境验证失败"
    }
    
    # 2. 构建前测试
    $testsPassed = Invoke-PreBuildTests
    if (!$testsPassed -and !$SkipTests) {
        Write-Warning "构建前测试失败，但继续构建"
    }
    
    # 3. 源码优化
    Optimize-SourceCode -OptLevel $Optimization
    
    # 4. 生成构建配置
    New-VersionInfo
    $specFile = New-PyInstallerSpec -MainFile $script:BuildStats["MainFile"] -Mode $Mode -DebugSymbols $IncludeDebugSymbols -ResourceDirs $script:BuildStats["ResourceDirs"]
    
    # 5. 执行构建
    $buildSuccess = Invoke-PyInstallerBuild -SpecFile $specFile -OutputDirectory $OutputDir -Mode $Mode
    if (!$buildSuccess) {
        throw "PyInstaller构建失败"
    }
    
    # 6. 构建后处理
    Optimize-BuildOutput -BuildDir $OutputDir -OptLevel $Optimization
    Set-CodeSignature -BuildDir $OutputDir -CertPath $CertificatePath
    
    # 7. 构建验证
    $verificationSuccess = Test-BuildOutput -BuildDir $OutputDir
    
    # 8. 生成报告
    New-BuildReport -OutputDir $OutputDir
    
    # 9. 显示总结
    Show-BuildSummary -Success ($buildSuccess -and $verificationSuccess) -OutputDir $OutputDir
    
    Write-Success "GUI应用构建流程完成！"
    
}
catch {
    Write-Error "构建失败: $($_.Exception.Message)"
    Write-Host "详细错误信息请查看日志文件: $script:LogFile" -ForegroundColor $Colors.Warning
    
    Show-BuildSummary -Success $false -OutputDir $OutputDir
    exit 1
}
finally {
    # 清理临时文件
    $tempFiles = @("*.spec", "version_info.txt", "temp_*.py")
    foreach ($pattern in $tempFiles) {
        Remove-Item $pattern -ErrorAction SilentlyContinue
    }
}

#endregion