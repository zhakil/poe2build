#!/usr/bin/env pwsh
<#
.SYNOPSIS
    PoE2智能构筑生成器 - Windows安装程序生成脚本
    
.DESCRIPTION
    专业级Windows安装程序创建脚本，支持多种安装格式（Inno Setup、MSI、便携版、Chocolatey）。
    包含数字签名、系统集成、企业部署支持等高级特性。
    
.PARAMETER Formats
    安装程序格式：Setup, MSI, Portable, Chocolatey, All
    
.PARAMETER Version
    应用程序版本号，默认从应用获取
    
.PARAMETER BuildDir
    构建输出目录，默认为dist
    
.PARAMETER OutputDir
    安装程序输出目录，默认为releases
    
.PARAMETER CodeSigning
    是否启用代码签名
    
.PARAMETER CertificatePath
    代码签名证书路径
    
.PARAMETER Silent
    静默模式，减少交互
    
.EXAMPLE
    .\scripts\create_installer.ps1
    创建标准Inno Setup安装程序
    
.EXAMPLE
    .\scripts\create_installer.ps1 -Formats @("Setup","MSI","Portable") -CodeSigning
    创建多格式安装包并启用代码签名
    
.NOTES
    Author: PoE2Build Team
    Version: 2.0.0
    Requires: Inno Setup 6.0+, WiX Toolset (for MSI), Windows 10/11
#>

[CmdletBinding()]
param(
    [ValidateSet("Setup", "NSIS", "MSI", "Portable", "Chocolatey", "All")]
    [string[]]$Formats = @("NSIS"),
    
    [string]$Version = "",
    
    [string]$BuildDir = "dist",
    
    [string]$OutputDir = "releases",
    
    [switch]$CodeSigning,
    
    [string]$CertificatePath = "",
    
    [switch]$Silent,
    
    [string]$CompanyName = "PoE2Build Team",
    
    [string]$AppName = "PoE2 智能构筑生成器",
    
    [string]$AppId = "PoE2Build"
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
$script:LogFile = "logs\create_installer_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
$script:StartTime = Get-Date
$script:InstallerStats = @{}

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

function Get-AppVersion {
    if ($Version) {
        return $Version
    }
    
    # 尝试从应用获取版本
    $pythonExe = "venv\Scripts\python.exe"
    if (Test-Path $pythonExe) {
        try {
            $versionOutput = & $pythonExe -c "
import sys, os
sys.path.insert(0, '.')
try:
    from poe2_ai_orchestrator import __version__
    print(__version__)
except:
    try:
        with open('pyproject.toml', 'r') as f:
            content = f.read()
            import re
            match = re.search(r'version = \"([^\"]+)\"', content)
            if match:
                print(match.group(1))
            else:
                print('2.0.0')
    except:
        print('2.0.0')
" 2>$null
            
            if ($versionOutput) {
                return $versionOutput.Trim()
            }
        }
        catch {
            Write-Warning "无法自动获取版本号，使用默认版本 2.0.0"
        }
    }
    
    return "2.0.0"
}

#endregion

#region Environment Validation

function Test-InstallerTools {
    Write-Progress "检测安装程序工具..."
    
    $tools = @{}
    
    # Inno Setup检测
    $innoSetupPaths = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )
    
    foreach ($path in $innoSetupPaths) {
        if (Test-Path $path) {
            $tools["InnoSetup"] = $path
            Write-Success "Inno Setup: $path"
            break
        }
    }
    
    if (!$tools["InnoSetup"]) {
        Write-Warning "未找到Inno Setup，将跳过Setup格式"
    }
    
    # NSIS检测
    $nsisPath = $null
    $nsisPossiblePaths = @(
        "${env:ProgramFiles}\NSIS\makensis.exe",
        "${env:ProgramFiles(x86)}\NSIS\makensis.exe",
        "C:\NSIS\makensis.exe"
    )
    
    foreach ($path in $nsisPossiblePaths) {
        if (Test-Path $path) {
            $tools["NSIS"] = $path
            Write-Success "NSIS: $path"
            break
        }
    }
    
    if (!$tools["NSIS"]) {
        Write-Warning "未找到NSIS，将跳过NSIS格式"
    }
    
    # WiX Toolset检测（MSI）
    $wixPath = "${env:ProgramFiles(x86)}\WiX Toolset v3.11\bin\candle.exe"
    if (Test-Path $wixPath) {
        $tools["WiX"] = $wixPath
        Write-Success "WiX Toolset: 已安装"
    } else {
        Write-Warning "未找到WiX Toolset，将跳过MSI格式"
    }
    
    # 7-Zip检测（便携版）
    $sevenZipPaths = @(
        "${env:ProgramFiles}\7-Zip\7z.exe",
        "${env:ProgramFiles(x86)}\7-Zip\7z.exe"
    )
    
    foreach ($path in $sevenZipPaths) {
        if (Test-Path $path) {
            $tools["7Zip"] = $path
            Write-Success "7-Zip: $path"
            break
        }
    }
    
    if (!$tools["7Zip"]) {
        Write-Warning "未找到7-Zip，便携版将使用PowerShell压缩"
    }
    
    # Chocolatey检测
    if (Test-Command "choco") {
        $tools["Chocolatey"] = "choco"
        Write-Success "Chocolatey: 已安装"
    } else {
        Write-Warning "未找到Chocolatey，将跳过Chocolatey包"
    }
    
    return $tools
}

function Test-BuildOutput {
    param([string]$BuildPath)
    
    Write-Progress "验证构建输出..."
    
    if (!(Test-Path $BuildPath)) {
        Write-Error "构建目录不存在: $BuildPath"
        throw "构建输出验证失败"
    }
    
    # 查找主可执行文件
    $exeFiles = Get-ChildItem -Path $BuildPath -Filter "*.exe" -Recurse
    if ($exeFiles.Count -eq 0) {
        Write-Error "未找到可执行文件"
        throw "构建输出验证失败"
    }
    
    $mainExe = $exeFiles | Where-Object { $_.Name -like "*PoE2Build*" -or $_.Name -like "*poe2*" } | Select-Object -First 1
    if (!$mainExe) {
        $mainExe = $exeFiles[0]
    }
    
    Write-Success "主可执行文件: $($mainExe.Name)"
    $script:InstallerStats["MainExecutable"] = $mainExe.FullName
    $script:InstallerStats["ExecutableName"] = $mainExe.Name
    $script:InstallerStats["BuildPath"] = $BuildPath
    
    return $true
}

#endregion

#region Inno Setup Installer

function New-InnoSetupScript {
    param([string]$Version, [string]$BuildPath)
    
    Write-Progress "创建Inno Setup脚本..."
    
    $scriptContent = @"
; PoE2智能构筑生成器 Inno Setup安装脚本
; 生成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
; 版本: $Version

#define MyAppName "$AppName"
#define MyAppVersion "$Version"
#define MyAppPublisher "$CompanyName"
#define MyAppURL "https://github.com/zhakil/poe2build"
#define MyAppExeName "$($script:InstallerStats["ExecutableName"])"
#define MyAppId "$AppId"

[Setup]
; 应用基本信息
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
LicenseFile=LICENSE
InfoBeforeFile=README.md
OutputDir=$OutputDir
OutputBaseFilename=PoE2Build_Setup_v{#MyAppVersion}
SetupIconFile=assets\icons\poe2build.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; 系统要求
MinVersion=10.0.17763
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin

; 数字签名配置
$(if ($CodeSigning -and $CertificatePath) { "SignTool=signtool" })

; 界面配置
DisableWelcomePage=no
DisableProgramGroupPage=no
ShowLanguageDialog=no
SetupLogging=yes

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "额外图标:"; Flags: unchecked
Name: "quicklaunchicon"; Description: "创建快速启动栏图标"; GroupDescription: "额外图标:"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
Source: "$BuildPath\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; 注意: 不要在任何共享的系统文件上使用"Flags: ignoreversion"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Registry]
; 文件关联 .poe2build
Root: HKCR; Subkey: ".poe2build"; ValueType: string; ValueName: ""; ValueData: "PoE2BuildFile"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "PoE2BuildFile"; ValueType: string; ValueName: ""; ValueData: "PoE2 构筑文件"; Flags: uninsdeletekey
Root: HKCR; Subkey: "PoE2BuildFile\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKCR; Subkey: "PoE2BuildFile\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

; 应用路径注册
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{#MyAppExeName}"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{#MyAppExeName}"; ValueType: string; ValueName: "Path"; ValueData: "{app}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\cache"
Type: filesandordirs; Name: "{userappdata}\{#MyAppName}"

[Code]
// 系统要求检查
function InitializeSetup(): Boolean;
var
  Version: TWindowsVersion;
  DotNetVersion: string;
begin
  GetWindowsVersionEx(Version);
  
  // Windows 10 1809+ 检查
  if Version.NTPlatform and ((Version.Major > 10) or 
     ((Version.Major = 10) and (Version.Minor = 0) and (Version.Build >= 17763))) then
  begin
    // 检查 .NET Framework (可选)
    if RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full', 'Version', DotNetVersion) then
    begin
      if CompareStr(DotNetVersion, '4.7.2') >= 0 then
      begin
        Result := True;
      end
      else
      begin
        if MsgBox('需要 .NET Framework 4.7.2 或更高版本。是否继续安装？', mbConfirmation, MB_YESNO) = IDYES then
          Result := True
        else
          Result := False;
      end;
    end
    else
    begin
      Result := True; // 如果无法检测，允许继续
    end;
  end
  else
  begin
    MsgBox('需要 Windows 10 (版本 1809) 或更高版本。', mbError, MB_OK);
    Result := False;
  end;
end;

// 磁盘空间检查
function NextButtonClick(CurPageID: Integer): Boolean;
var
  DiskSpace: Integer;
begin
  Result := True;
  
  if CurPageID = wpSelectDir then
  begin
    DiskSpace := DiskFree(0) div (1024 * 1024); // MB
    if DiskSpace < 500 then // 需要至少500MB空间
    begin
      MsgBox('磁盘空间不足。需要至少500MB可用空间。', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

// 安装完成后的设置
procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigDir: string;
begin
  if CurStep = ssPostInstall then
  begin
    // 创建用户配置目录
    ConfigDir := ExpandConstant('{userappdata}\{#MyAppName}');
    if not DirExists(ConfigDir) then
      CreateDir(ConfigDir);
    
    // 创建日志目录
    if not DirExists(ExpandConstant('{app}\logs')) then
      CreateDir(ExpandConstant('{app}\logs'));
  end;
end;
"@

    $scriptPath = "temp_installer.iss"
    Set-Content -Path $scriptPath -Value $scriptContent -Encoding UTF8
    Write-Success "Inno Setup脚本创建完成: $scriptPath"
    return $scriptPath
}

function New-InnoSetupInstaller {
    param([hashtable]$Tools, [string]$Version, [string]$BuildPath)
    
    if (!$Tools["InnoSetup"]) {
        Write-Warning "Inno Setup不可用，跳过Setup安装程序"
        return
    }
    
    Write-Progress "创建Inno Setup安装程序..."
    
    try {
        # 创建输出目录
        if (!(Test-Path $OutputDir)) {
            New-Item -ItemType Directory $OutputDir -Force | Out-Null
        }
        
        # 生成安装脚本
        $scriptPath = New-InnoSetupScript -Version $Version -BuildPath $BuildPath
        
        # 编译安装程序
        $isccExe = $Tools["InnoSetup"]
        $compileCommand = "`"$isccExe`" `"$scriptPath`""
        
        Write-Info "编译安装程序..."
        Write-Info "命令: $compileCommand"
        
        $process = Start-Process -FilePath $isccExe -ArgumentList "`"$scriptPath`"" -Wait -PassThru -NoNewWindow
        
        if ($process.ExitCode -eq 0) {
            $installerFile = Get-ChildItem -Path $OutputDir -Filter "PoE2Build_Setup_v*.exe" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if ($installerFile) {
                $script:InstallerStats["SetupInstaller"] = $installerFile.FullName
                Write-Success "Inno Setup安装程序创建成功: $($installerFile.Name)"
                
                # 代码签名
                if ($CodeSigning -and $CertificatePath) {
                    Set-CodeSignature -FilePath $installerFile.FullName -CertPath $CertificatePath
                }
            } else {
                Write-Warning "未找到生成的安装程序文件"
            }
        } else {
            Write-Error "Inno Setup编译失败，退出码: $($process.ExitCode)"
        }
    }
    catch {
        Write-Error "Inno Setup安装程序创建失败: $($_.Exception.Message)"
    }
    finally {
        # 清理临时文件
        Remove-Item "temp_installer.iss" -ErrorAction SilentlyContinue
    }
}

#endregion

#region NSIS Installer

function New-NSISInstaller {
    param([hashtable]$Tools, [string]$Version, [string]$BuildPath)
    
    if (!$Tools["NSIS"]) {
        Write-Warning "NSIS不可用，跳过NSIS安装程序"
        return
    }
    
    Write-Progress "创建NSIS安装程序..."
    
    try {
        # 确保输出目录存在
        if (!(Test-Path $OutputDir)) {
            New-Item -ItemType Directory $OutputDir -Force | Out-Null
        }
        
        # 创建临时构建目录
        $tempBuildDir = "temp_nsis_build"
        if (Test-Path $tempBuildDir) {
            Remove-Item $tempBuildDir -Recurse -Force
        }
        New-Item -ItemType Directory $tempBuildDir -Force | Out-Null
        
        # 复制应用程序文件
        Write-Info "复制应用程序文件..."
        Copy-Item -Path "$BuildPath\*" -Destination $tempBuildDir -Recurse -Force
        
        # 复制NSIS模板并自定义
        $templatePath = "resources\templates\installer.nsi"
        if (!(Test-Path $templatePath)) {
            Write-Error "NSIS模板文件不存在: $templatePath"
            throw "NSIS模板不存在"
        }
        
        # 读取模板并替换占位符
        $nsiContent = Get-Content $templatePath -Raw -Encoding UTF8
        
        # 替换路径和版本信息
        $replacements = @{
            'dist\*.*' = "$tempBuildDir\*.*"
            '2.0.0' = $Version
        }
        
        foreach ($placeholder in $replacements.Keys) {
            $nsiContent = $nsiContent.Replace($placeholder, $replacements[$placeholder])
        }
        
        # 创建自定义NSI脚本
        $customNsiPath = "temp_installer.nsi"
        Set-Content -Path $customNsiPath -Value $nsiContent -Encoding UTF8
        
        # 构建NSIS安装程序
        $nsisExe = $Tools["NSIS"]
        $nsisArgs = @(
            "/V2",
            "/DVERSION=$Version",
            "/DOUTPUT_DIR=$OutputDir",
            $customNsiPath
        )
        
        Write-Info "构建NSIS安装程序..."
        Write-Info "命令: $nsisExe $($nsisArgs -join ' ')"
        
        $buildStart = Get-Date
        $process = Start-Process -FilePath $nsisExe -ArgumentList $nsisArgs -Wait -PassThru -NoNewWindow
        $buildTime = (Get-Date) - $buildStart
        
        if ($process.ExitCode -eq 0) {
            # 查找生成的安装程序
            $installerPattern = "PoE2Build_Setup_*.exe"
            $installerFile = Get-ChildItem -Path $OutputDir -Filter $installerPattern | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            
            if ($installerFile) {
                $script:InstallerStats["NSISInstaller"] = $installerFile.FullName
                $installerSize = [math]::Round($installerFile.Length / 1MB, 2)
                
                Write-Success "NSIS安装程序创建成功: $($installerFile.Name)"
                Write-Info "文件大小: $installerSize MB"
                Write-Info "构建用时: $($buildTime.ToString('mm\:ss'))"
                
                # 代码签名
                if ($CodeSigning -and $CertificatePath) {
                    Set-CodeSignature -FilePath $installerFile.FullName -CertPath $CertificatePath
                }
                
                # 验证安装程序
                Test-NSISInstaller -InstallerPath $installerFile.FullName
                
            } else {
                Write-Warning "未找到生成的NSIS安装程序文件"
            }
        } else {
            Write-Error "NSIS构建失败，退出码: $($process.ExitCode)"
        }
    }
    catch {
        Write-Error "NSIS安装程序创建失败: $($_.Exception.Message)"
    }
    finally {
        # 清理临时文件
        if (Test-Path $tempBuildDir) {
            Remove-Item $tempBuildDir -Recurse -Force -ErrorAction SilentlyContinue
        }
        Remove-Item $customNsiPath -ErrorAction SilentlyContinue
    }
}

function Test-NSISInstaller {
    param([string]$InstallerPath)
    
    Write-Progress "验证NSIS安装程序..."
    
    try {
        if (!(Test-Path $InstallerPath)) {
            Write-Warning "安装程序文件不存在"
            return $false
        }
        
        $installerInfo = Get-Item $InstallerPath
        Write-Success "安装程序验证通过"
        Write-Info "文件大小: $([math]::Round($installerInfo.Length / 1MB, 2)) MB"
        
        # 签名验证
        if ($CodeSigning) {
            try {
                $signature = Get-AuthenticodeSignature $InstallerPath
                if ($signature.Status -eq "Valid") {
                    Write-Success "数字签名验证通过"
                } else {
                    Write-Warning "数字签名验证失败: $($signature.Status)"
                }
            }
            catch {
                Write-Warning "无法验证数字签名: $($_.Exception.Message)"
            }
        }
        
        return $true
    }
    catch {
        Write-Error "安装程序验证失败: $($_.Exception.Message)"
        return $false
    }
}

#endregion

#region MSI Installer

function New-WixScript {
    param([string]$Version, [string]$BuildPath)
    
    Write-Progress "创建WiX脚本..."
    
    $guid = [System.Guid]::NewGuid().ToString()
    $upgradeGuid = [System.Guid]::NewGuid().ToString()
    
    $wixContent = @"
<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*" Name="$AppName" Language="2052" Version="$Version" 
           Manufacturer="$CompanyName" UpgradeCode="{$upgradeGuid}">
    
    <Package InstallerVersion="200" Compressed="yes" InstallScope="perMachine" />
    
    <MajorUpgrade DowngradeErrorMessage="已安装更新的版本。" />
    <MediaTemplate EmbedCab="yes" />
    
    <!-- 功能定义 -->
    <Feature Id="ProductFeature" Title="主程序" Level="1">
      <ComponentGroupRef Id="ProductComponents" />
    </Feature>
    
    <!-- 目录结构 -->
    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFilesFolder">
        <Directory Id="INSTALLFOLDER" Name="$AppName" />
      </Directory>
    </Directory>
    
    <!-- 组件组 -->
    <ComponentGroup Id="ProductComponents" Directory="INSTALLFOLDER">
      <Component Id="MainExecutable" Guid="{$([System.Guid]::NewGuid())}">
        <File Id="MainExe" Source="$BuildPath\$($script:InstallerStats["ExecutableName"])" KeyPath="yes" />
      </Component>
    </ComponentGroup>
    
    <!-- UI配置 -->
    <UIRef Id="WixUI_InstallDir" />
    <Property Id="WIXUI_INSTALLDIR" Value="INSTALLFOLDER" />
    
  </Product>
</Wix>
"@

    $wixPath = "temp_installer.wxs"
    Set-Content -Path $wixPath -Value $wixContent -Encoding UTF8
    Write-Success "WiX脚本创建完成: $wixPath"
    return $wixPath
}

function New-MSIInstaller {
    param([hashtable]$Tools, [string]$Version, [string]$BuildPath)
    
    if (!$Tools["WiX"]) {
        Write-Warning "WiX Toolset不可用，跳过MSI安装程序"
        return
    }
    
    Write-Progress "创建MSI安装程序..."
    
    try {
        # 生成WiX脚本
        $wixScript = New-WixScript -Version $Version -BuildPath $BuildPath
        
        # 编译MSI
        $candleExe = $Tools["WiX"]
        $lightExe = $candleExe.Replace("candle.exe", "light.exe")
        
        # Candle编译
        Write-Info "编译WiX源文件..."
        & $candleExe $wixScript
        
        # Light链接
        Write-Info "链接MSI安装程序..."
        $msiOutput = "$OutputDir\PoE2Build_v$Version.msi"
        & $lightExe "temp_installer.wixobj" -out $msiOutput -ext WixUIExtension
        
        if (Test-Path $msiOutput) {
            $script:InstallerStats["MSIInstaller"] = $msiOutput
            Write-Success "MSI安装程序创建成功: $msiOutput"
            
            # 代码签名
            if ($CodeSigning -and $CertificatePath) {
                Set-CodeSignature -FilePath $msiOutput -CertPath $CertificatePath
            }
        }
    }
    catch {
        Write-Error "MSI安装程序创建失败: $($_.Exception.Message)"
    }
    finally {
        # 清理临时文件
        Remove-Item "temp_installer.wxs" -ErrorAction SilentlyContinue
        Remove-Item "temp_installer.wixobj" -ErrorAction SilentlyContinue
        Remove-Item "temp_installer.wixpdb" -ErrorAction SilentlyContinue
    }
}

#endregion

#region Portable Version

function New-PortableVersion {
    param([hashtable]$Tools, [string]$Version, [string]$BuildPath)
    
    Write-Progress "创建便携版..."
    
    try {
        $portableDir = "temp_portable"
        $portableZip = "$OutputDir\PoE2Build_Portable_v$Version.zip"
        
        # 创建便携版目录
        if (Test-Path $portableDir) {
            Remove-Item $portableDir -Recurse -Force
        }
        New-Item -ItemType Directory $portableDir -Force | Out-Null
        
        # 复制应用文件
        Copy-Item -Path "$BuildPath\*" -Destination $portableDir -Recurse -Force
        
        # 创建便携版标识文件
        $portableMarker = @"
# PoE2Build 便携版

这是PoE2智能构筑生成器的便携版本。

## 使用说明

1. 解压到任意目录
2. 直接运行 $($script:InstallerStats["ExecutableName"])
3. 所有配置和缓存文件将保存在当前目录

## 版本信息

- 版本: $Version
- 构建日期: $(Get-Date -Format 'yyyy-MM-dd')
- 类型: 便携版

## 系统要求

- Windows 10 (1809) 或更高版本
- .NET Framework 4.7.2 或更高版本

## 支持

- 项目主页: https://github.com/zhakil/poe2build
- 问题反馈: https://github.com/zhakil/poe2build/issues
"@
        Set-Content -Path "$portableDir\便携版说明.txt" -Value $portableMarker -Encoding UTF8
        
        # 创建启动脚本
        $launchScript = @"
@echo off
cd /d "%~dp0"
echo 启动 PoE2Build 便携版...
start "" "$($script:InstallerStats["ExecutableName"])"
"@
        Set-Content -Path "$portableDir\启动PoE2Build.bat" -Value $launchScript -Encoding Default
        
        # 压缩便携版
        if ($Tools["7Zip"]) {
            Write-Info "使用7-Zip压缩便携版..."
            & $Tools["7Zip"] a -tzip "$portableZip" "$portableDir\*" -mx=9
        } else {
            Write-Info "使用PowerShell压缩便携版..."
            Compress-Archive -Path "$portableDir\*" -DestinationPath $portableZip -CompressionLevel Optimal -Force
        }
        
        if (Test-Path $portableZip) {
            $script:InstallerStats["PortableVersion"] = $portableZip
            Write-Success "便携版创建成功: $portableZip"
        }
        
    }
    catch {
        Write-Error "便携版创建失败: $($_.Exception.Message)"
    }
    finally {
        # 清理临时目录
        if (Test-Path $portableDir) {
            Remove-Item $portableDir -Recurse -Force
        }
    }
}

#endregion

#region Chocolatey Package

function New-ChocolateyPackage {
    param([hashtable]$Tools, [string]$Version, [string]$BuildPath)
    
    if (!$Tools["Chocolatey"]) {
        Write-Warning "Chocolatey不可用，跳过Chocolatey包"
        return
    }
    
    Write-Progress "创建Chocolatey包..."
    
    try {
        $chocoDir = "temp_chocolatey"
        $toolsDir = "$chocoDir\tools"
        
        # 创建目录结构
        if (Test-Path $chocoDir) {
            Remove-Item $chocoDir -Recurse -Force
        }
        New-Item -ItemType Directory $toolsDir -Force | Out-Null
        
        # 复制应用文件
        Copy-Item -Path "$BuildPath\*" -Destination $toolsDir -Recurse -Force
        
        # 创建nuspec文件
        $nuspecContent = @"
<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2015/06/nuspec.xsd">
  <metadata>
    <id>poe2build</id>
    <version>$Version</version>
    <packageSourceUrl>https://github.com/zhakil/poe2build</packageSourceUrl>
    <owners>$CompanyName</owners>
    <title>$AppName</title>
    <authors>$CompanyName</authors>
    <projectUrl>https://github.com/zhakil/poe2build</projectUrl>
    <iconUrl>https://raw.githubusercontent.com/zhakil/poe2build/main/assets/icons/poe2build.png</iconUrl>
    <copyright>Copyright (c) 2023 $CompanyName</copyright>
    <licenseUrl>https://github.com/zhakil/poe2build/blob/main/LICENSE</licenseUrl>
    <requireLicenseAcceptance>false</requireLicenseAcceptance>
    <docsUrl>https://github.com/zhakil/poe2build/wiki</docsUrl>
    <bugTrackerUrl>https://github.com/zhakil/poe2build/issues</bugTrackerUrl>
    <tags>poe2 pathofexile2 build generator game utility</tags>
    <summary>Path of Exile 2 智能构筑生成器</summary>
    <description>
Path of Exile 2智能构筑生成器是专为《流放之路2》设计的智能构筑推荐系统。

## 主要特性
- 基于真实PoE2数据源的智能构筑推荐
- 集成PoB2计算引擎
- Windows原生GUI界面
- 支持多种构筑风格和预算配置

## 系统要求
- Windows 10 (1809) 或更高版本
- .NET Framework 4.7.2 或更高版本
    </description>
    <dependencies>
      <dependency id="dotnetfx" version="4.7.2" />
    </dependencies>
  </metadata>
  <files>
    <file src="tools\**" target="tools" />
  </files>
</package>
"@
        Set-Content -Path "$chocoDir\poe2build.nuspec" -Value $nuspecContent -Encoding UTF8
        
        # 创建安装脚本
        $installScript = @"
`$ErrorActionPreference = 'Stop'

`$packageName = 'poe2build'
`$toolsDir = "`$(Split-Path -parent `$MyInvocation.MyCommand.Definition)"
`$exePath = Join-Path `$toolsDir '$($script:InstallerStats["ExecutableName"])'

# 创建开始菜单快捷方式
Install-ChocolateyShortcut -ShortcutFilePath "`$env:ALLUSERSPROFILE\Microsoft\Windows\Start Menu\Programs\$AppName.lnk" -TargetPath `$exePath

Write-Host "$AppName 安装完成！" -ForegroundColor Green
Write-Host "可执行文件位置: `$exePath" -ForegroundColor Yellow
"@
        Set-Content -Path "$toolsDir\chocolateyinstall.ps1" -Value $installScript -Encoding UTF8
        
        # 创建卸载脚本
        $uninstallScript = @"
`$ErrorActionPreference = 'Stop'

`$shortcutPath = "`$env:ALLUSERSPROFILE\Microsoft\Windows\Start Menu\Programs\$AppName.lnk"
if (Test-Path `$shortcutPath) {
    Remove-Item `$shortcutPath -Force
}

Write-Host "$AppName 卸载完成！" -ForegroundColor Green
"@
        Set-Content -Path "$toolsDir\chocolateyuninstall.ps1" -Value $uninstallScript -Encoding UTF8
        
        # 打包
        Write-Info "打包Chocolatey包..."
        $originalLocation = Get-Location
        Set-Location $chocoDir
        
        & choco pack --output-directory $OutputDir
        
        Set-Location $originalLocation
        
        $nupkgFile = Get-ChildItem -Path $OutputDir -Filter "poe2build.*.nupkg" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($nupkgFile) {
            $script:InstallerStats["ChocolateyPackage"] = $nupkgFile.FullName
            Write-Success "Chocolatey包创建成功: $($nupkgFile.Name)"
        }
        
    }
    catch {
        Write-Error "Chocolatey包创建失败: $($_.Exception.Message)"
    }
    finally {
        # 清理临时目录
        if (Test-Path $chocoDir) {
            Remove-Item $chocoDir -Recurse -Force
        }
    }
}

#endregion

#region Code Signing

function Set-CodeSignature {
    param([string]$FilePath, [string]$CertPath)
    
    if (!$CodeSigning -or !$CertPath -or !(Test-Path $CertPath)) {
        return
    }
    
    Write-Progress "执行代码签名: $(Split-Path $FilePath -Leaf)"
    
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
    
    try {
        $signArgs = @(
            "sign",
            "/f", "`"$CertPath`"",
            "/t", "http://timestamp.sectigo.com",
            "/fd", "SHA256",
            "/v",
            "`"$FilePath`""
        )
        
        & $signTool $signArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "代码签名成功: $(Split-Path $FilePath -Leaf)"
        } else {
            Write-Warning "代码签名失败: $(Split-Path $FilePath -Leaf)"
        }
    }
    catch {
        Write-Warning "代码签名异常: $($_.Exception.Message)"
    }
}

#endregion

#region Checksums and Verification

function New-ChecksumFile {
    Write-Progress "生成校验文件..."
    
    $checksumPath = "$OutputDir\checksums.txt"
    $checksumContent = @()
    
    $checksumContent += "# PoE2Build v$($script:InstallerStats["Version"]) 校验文件"
    $checksumContent += "# 生成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    $checksumContent += ""
    
    # 计算所有生成文件的校验和
    $installerFiles = Get-ChildItem -Path $OutputDir -File | Where-Object { $_.Name -ne "checksums.txt" }
    
    foreach ($file in $installerFiles) {
        try {
            $hash = Get-FileHash -Path $file.FullName -Algorithm SHA256
            $checksumContent += "$($hash.Hash.ToLower())  $($file.Name)"
            Write-Success "校验和计算: $($file.Name)"
        }
        catch {
            Write-Warning "校验和计算失败: $($file.Name)"
        }
    }
    
    Set-Content -Path $checksumPath -Value $checksumContent -Encoding UTF8
    Write-Success "校验文件生成完成: checksums.txt"
}

#endregion

#region Summary and Reporting

function Show-InstallerSummary {
    param([string]$Version)
    
    $elapsed = (Get-Date) - $script:StartTime
    
    Write-Host ""
    Write-Host "📦 安装程序创建完成报告" -ForegroundColor $Colors.Info
    Write-Host "=" * 50 -ForegroundColor $Colors.Info
    Write-Host "应用版本: $Version" -ForegroundColor $Colors.Info
    Write-Host "构建时间: $($elapsed.ToString('mm\:ss'))" -ForegroundColor $Colors.Info
    Write-Host "输出目录: $OutputDir" -ForegroundColor $Colors.Info
    Write-Host "日志文件: $script:LogFile" -ForegroundColor $Colors.Info
    Write-Host ""
    
    Write-Host "🎁 生成的安装包:" -ForegroundColor $Colors.Info
    
    if ($script:InstallerStats["SetupInstaller"]) {
        $file = Get-Item $script:InstallerStats["SetupInstaller"]
        Write-Host "✅ Inno Setup: $($file.Name) ($([math]::Round($file.Length / 1MB, 2)) MB)" -ForegroundColor $Colors.Success
    }
    
    if ($script:InstallerStats["NSISInstaller"]) {
        $file = Get-Item $script:InstallerStats["NSISInstaller"]
        Write-Host "✅ NSIS: $($file.Name) ($([math]::Round($file.Length / 1MB, 2)) MB)" -ForegroundColor $Colors.Success
    }
    
    if ($script:InstallerStats["MSIInstaller"]) {
        $file = Get-Item $script:InstallerStats["MSIInstaller"]  
        Write-Host "✅ MSI: $($file.Name) ($([math]::Round($file.Length / 1MB, 2)) MB)" -ForegroundColor $Colors.Success
    }
    
    if ($script:InstallerStats["PortableVersion"]) {
        $file = Get-Item $script:InstallerStats["PortableVersion"]
        Write-Host "✅ 便携版: $($file.Name) ($([math]::Round($file.Length / 1MB, 2)) MB)" -ForegroundColor $Colors.Success
    }
    
    if ($script:InstallerStats["ChocolateyPackage"]) {
        $file = Get-Item $script:InstallerStats["ChocolateyPackage"]
        Write-Host "✅ Chocolatey: $($file.Name) ($([math]::Round($file.Length / 1MB, 2)) MB)" -ForegroundColor $Colors.Success
    }
    
    Write-Host ""
    Write-Host "🚀 下一步操作:" -ForegroundColor $Colors.Info
    Write-Host "1. 测试安装程序在不同Windows版本上的兼容性" -ForegroundColor $Colors.Info
    Write-Host "2. 运行安装后的应用程序验证" -ForegroundColor $Colors.Info
    Write-Host "3. 上传到GitHub Releases或分发渠道" -ForegroundColor $Colors.Info
    Write-Host ""
}

#endregion

#region Main Execution

function Show-Header {
    Write-Host ""
    Write-Host "📦 PoE2智能构筑生成器 - 安装程序生成" -ForegroundColor $Colors.Info
    Write-Host "=" * 60 -ForegroundColor $Colors.Info
    Write-Host "版本: 2.0.0" -ForegroundColor $Colors.Info
    Write-Host "目标格式: $($Formats -join ', ')" -ForegroundColor $Colors.Info  
    Write-Host "日期: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor $Colors.Info
    Write-Host "=" * 60 -ForegroundColor $Colors.Info
    Write-Host ""
}

# 主执行流程
try {
    Show-Header
    
    # 如果指定了All，展开所有格式
    if ($Formats -contains "All") {
        $Formats = @("Setup", "NSIS", "MSI", "Portable", "Chocolatey")
    }
    
    # 获取应用版本
    $appVersion = Get-AppVersion
    $script:InstallerStats["Version"] = $appVersion
    Write-Success "应用版本: $appVersion"
    
    # 验证构建输出
    $buildValid = Test-BuildOutput -BuildPath $BuildDir
    if (!$buildValid) {
        throw "构建输出验证失败"
    }
    
    # 检测安装工具
    $availableTools = Test-InstallerTools
    
    # 创建输出目录
    if (!(Test-Path $OutputDir)) {
        New-Item -ItemType Directory $OutputDir -Force | Out-Null
        Write-Success "输出目录创建: $OutputDir"
    }
    
    # 生成各种格式的安装程序
    foreach ($format in $Formats) {
        switch ($format) {
            "Setup" {
                New-InnoSetupInstaller -Tools $availableTools -Version $appVersion -BuildPath $BuildDir
            }
            "NSIS" {
                New-NSISInstaller -Tools $availableTools -Version $appVersion -BuildPath $BuildDir
            }
            "MSI" {
                New-MSIInstaller -Tools $availableTools -Version $appVersion -BuildPath $BuildDir  
            }
            "Portable" {
                New-PortableVersion -Tools $availableTools -Version $appVersion -BuildPath $BuildDir
            }
            "Chocolatey" {
                New-ChocolateyPackage -Tools $availableTools -Version $appVersion -BuildPath $BuildDir
            }
        }
    }
    
    # 生成校验文件
    New-ChecksumFile
    
    # 显示总结
    Show-InstallerSummary -Version $appVersion
    
    Write-Success "安装程序生成流程完成！"
    
}
catch {
    Write-Error "安装程序生成失败: $($_.Exception.Message)"
    Write-Host "详细错误信息请查看日志文件: $script:LogFile" -ForegroundColor $Colors.Warning
    exit 1
}
finally {
    # 清理临时文件
    $tempFiles = @("temp_*.iss", "temp_*.wxs", "temp_*.wixobj", "temp_*.wixpdb")
    foreach ($pattern in $tempFiles) {
        Remove-Item $pattern -ErrorAction SilentlyContinue
    }
}

#endregion