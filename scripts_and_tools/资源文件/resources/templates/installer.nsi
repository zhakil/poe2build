; PoE2智能构筑生成器 NSIS安装脚本
; 支持完整的Windows系统集成和专业级安装体验
; 版本: 2.0.0

;--------------------------------
; 编译时配置
!define APP_NAME "PoE2智能构筑生成器"
!define APP_NAME_EN "PoE2Build"
!define APP_VERSION "2.0.0"
!define APP_PUBLISHER "PoE2Build Team"
!define APP_URL "https://github.com/poe2build/poe2build"
!define APP_EXECUTABLE "PoE2Build.exe"
!define APP_REGKEY "Software\${APP_PUBLISHER}\${APP_NAME_EN}"
!define UNINSTALL_REGKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME_EN}"

; 安装文件信息
VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "FileDescription" "${APP_NAME}安装程序"
VIAddVersionKey "LegalCopyright" "© 2024 ${APP_PUBLISHER}"

;--------------------------------
; 安装程序配置
Name "${APP_NAME} ${APP_VERSION}"
OutFile "PoE2Build_Setup_${APP_VERSION}.exe"
InstallDir "$PROGRAMFILES\${APP_PUBLISHER}\${APP_NAME_EN}"
InstallDirRegKey HKLM "${APP_REGKEY}" "InstallPath"
RequestExecutionLevel admin
ShowInstDetails show
ShowUnInstDetails show
SetCompressor /SOLID lzma

; 现代UI2界面
!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"
!include "WinVer.nsh"

;--------------------------------
; 界面配置
!define MUI_ABORTWARNING
!define MUI_ICON "assets\icons\poe2build.ico"
!define MUI_UNICON "assets\icons\poe2build.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "assets\images\installer_header.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "assets\images\installer_welcome.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "assets\images\installer_welcome.bmp"

; 安装页面
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY

; 自定义安装选项页面
Page custom ComponentsPageShow ComponentsPageLeave

!insertmacro MUI_PAGE_INSTFILES

; 完成页面配置
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXECUTABLE}"
!define MUI_FINISHPAGE_RUN_TEXT "启动 ${APP_NAME}"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.md"
!define MUI_FINISHPAGE_SHOWREADME_TEXT "查看使用指南"
!define MUI_FINISHPAGE_LINK "访问项目主页"
!define MUI_FINISHPAGE_LINK_LOCATION "${APP_URL}"
!insertmacro MUI_PAGE_FINISH

; 卸载页面
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; 语言文件
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

;--------------------------------
; 安装类型和组件
InstType "完整安装"
InstType "最小安装"
InstType "自定义安装"

;--------------------------------
; 变量定义
Var StartMenuFolder
Var CreateDesktopShortcut
Var CreateQuickLaunch  
Var EnableAutoStart
Var AssociateFiles
Var InstallVCRedist

;--------------------------------
; 自定义页面函数
Function ComponentsPageShow
    ; 创建自定义选项页面
    nsDialogs::Create 1018
    Pop $0
    
    ${NSD_CreateLabel} 0 0 100% 20u "安装选项配置:"
    Pop $0
    
    ${NSD_CreateCheckBox} 10 30u 280u 15u "创建桌面快捷方式"
    Pop $CreateDesktopShortcut
    ${NSD_Check} $CreateDesktopShortcut
    
    ${NSD_CreateCheckBox} 10 50u 280u 15u "创建快速启动栏快捷方式"
    Pop $CreateQuickLaunch
    
    ${NSD_CreateCheckBox} 10 70u 280u 15u "开机自动启动"
    Pop $EnableAutoStart
    
    ${NSD_CreateCheckBox} 10 90u 280u 15u "关联.poe2build文件类型"
    Pop $AssociateFiles
    ${NSD_Check} $AssociateFiles
    
    ${NSD_CreateCheckBox} 10 110u 280u 15u "安装Visual C++运行库（如果需要）"
    Pop $InstallVCRedist
    ${NSD_Check} $InstallVCRedist
    
    nsDialogs::Show
FunctionEnd

Function ComponentsPageLeave
    ; 保存用户选择
FunctionEnd

;--------------------------------
; 安装节
Section "!${APP_NAME} (必需)" SecCore
    SectionIn RO 1 2 3
    
    ; 设置安装目录
    SetOutPath "$INSTDIR"
    
    ; 停止正在运行的应用程序
    DetailPrint "检查正在运行的应用程序..."
    ${nsProcess::FindProcess} "${APP_EXECUTABLE}" $R0
    ${If} $R0 = 0
        MessageBox MB_YESNO|MB_ICONQUESTION "检测到${APP_NAME}正在运行。需要先关闭应用程序才能继续安装。是否自动关闭?" IDYES auto_close IDNO manual_close
        auto_close:
            DetailPrint "正在关闭应用程序..."
            ${nsProcess::KillProcess} "${APP_EXECUTABLE}" $R0
            Sleep 2000
            Goto check_again
        manual_close:
            MessageBox MB_OK|MB_ICONINFORMATION "请手动关闭${APP_NAME}后点击确定继续安装。"
        check_again:
    ${EndIf}
    
    ; 安装主程序文件
    DetailPrint "安装应用程序文件..."
    File /r "dist\*.*"
    
    ; 创建注册表项
    DetailPrint "配置系统注册表..."
    WriteRegStr HKLM "${APP_REGKEY}" "InstallPath" "$INSTDIR"
    WriteRegStr HKLM "${APP_REGKEY}" "Version" "${APP_VERSION}"
    WriteRegStr HKLM "${APP_REGKEY}" "Publisher" "${APP_PUBLISHER}"
    
    ; 写入卸载信息
    WriteRegStr HKLM "${UNINSTALL_REGKEY}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "${UNINSTALL_REGKEY}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "${UNINSTALL_REGKEY}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "${UNINSTALL_REGKEY}" "URLInfoAbout" "${APP_URL}"
    WriteRegStr HKLM "${UNINSTALL_REGKEY}" "DisplayIcon" "$INSTDIR\${APP_EXECUTABLE},0"
    WriteRegStr HKLM "${UNINSTALL_REGKEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "${UNINSTALL_REGKEY}" "QuietUninstallString" "$INSTDIR\Uninstall.exe /S"
    WriteRegDWORD HKLM "${UNINSTALL_REGKEY}" "NoModify" 1
    WriteRegDWORD HKLM "${UNINSTALL_REGKEY}" "NoRepair" 1
    
    ; 计算安装大小
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "${UNINSTALL_REGKEY}" "EstimatedSize" "$0"
    
    ; 创建卸载程序
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
SectionEnd

Section "开始菜单快捷方式" SecStartMenu
    SectionIn 1 3
    
    ; 创建开始菜单文件夹
    !define MUI_STARTMENUPAGE_DEFAULTFOLDER "${APP_PUBLISHER}"
    !define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKLM"
    !define MUI_STARTMENUPAGE_REGISTRY_KEY "${APP_REGKEY}"
    !define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "StartMenuFolder"
    
    SetShellVarContext all
    CreateDirectory "$SMPROGRAMS\${APP_PUBLISHER}"
    
    ; 主程序快捷方式
    CreateShortCut "$SMPROGRAMS\${APP_PUBLISHER}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE}" "" "$INSTDIR\${APP_EXECUTABLE}" 0
    
    ; 卸载快捷方式
    CreateShortCut "$SMPROGRAMS\${APP_PUBLISHER}\卸载 ${APP_NAME}.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0
    
    ; 帮助文档快捷方式
    IfFileExists "$INSTDIR\README.md" 0 +2
    CreateShortCut "$SMPROGRAMS\${APP_PUBLISHER}\使用指南.lnk" "$INSTDIR\README.md" "" "" 0
    
SectionEnd

Section "桌面快捷方式" SecDesktop
    SectionIn 3
    
    SetShellVarContext all
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE}" "" "$INSTDIR\${APP_EXECUTABLE}" 0
    
SectionEnd

Section "文件关联" SecFileAssoc
    SectionIn 1 3
    
    DetailPrint "注册文件关联..."
    
    ; 注册.poe2build文件类型
    WriteRegStr HKCR ".poe2build" "" "PoE2Build.BuildFile"
    WriteRegStr HKCR ".poe2build" "Content Type" "application/x-poe2build"
    
    ; 注册程序标识符
    WriteRegStr HKCR "PoE2Build.BuildFile" "" "PoE2构筑文件"
    WriteRegStr HKCR "PoE2Build.BuildFile\DefaultIcon" "" "$INSTDIR\${APP_EXECUTABLE},1"
    WriteRegStr HKCR "PoE2Build.BuildFile\shell" "" "open"
    WriteRegStr HKCR "PoE2Build.BuildFile\shell\open" "" "用${APP_NAME}打开(&O)"
    WriteRegStr HKCR "PoE2Build.BuildFile\shell\open\command" "" '"$INSTDIR\${APP_EXECUTABLE}" --open "%1"'
    
    ; 编辑操作
    WriteRegStr HKCR "PoE2Build.BuildFile\shell\edit" "" "编辑构筑(&E)"
    WriteRegStr HKCR "PoE2Build.BuildFile\shell\edit\command" "" '"$INSTDIR\${APP_EXECUTABLE}" --edit "%1"'
    
    ; 刷新Shell图标缓存
    System::Call 'shell32.dll::SHChangeNotify(l, l, i, i) v (0x08000000, 0, 0, 0)'
    
SectionEnd

Section "Visual C++运行库" SecVCRedist
    SectionIn 3
    
    DetailPrint "检查Visual C++运行库..."
    
    ; 检查是否已安装VC++ 2019/2022 Redistributable
    ReadRegStr $0 HKLM "SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" "Version"
    ${If} $0 == ""
        DetailPrint "安装Visual C++运行库..."
        File "redist\vc_redist.x64.exe"
        ExecWait '"$INSTDIR\vc_redist.x64.exe" /quiet /norestart' $0
        ${If} $0 != 0
            DetailPrint "Visual C++运行库安装可能失败，错误代码: $0"
        ${EndIf}
        Delete "$INSTDIR\vc_redist.x64.exe"
    ${Else}
        DetailPrint "Visual C++运行库已安装，版本: $0"
    ${EndIf}
    
SectionEnd

;--------------------------------
; 安装后处理
Section -Post
    
    ; 处理用户选择的选项
    ${NSD_GetState} $CreateDesktopShortcut $0
    ${If} $0 = ${BST_CHECKED}
        SetShellVarContext all
        CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE}" "" "$INSTDIR\${APP_EXECUTABLE}" 0
    ${EndIf}
    
    ${NSD_GetState} $CreateQuickLaunch $0
    ${If} $0 = ${BST_CHECKED}
        SetShellVarContext all
        CreateShortCut "$QUICKLAUNCH\${APP_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE}" "" "$INSTDIR\${APP_EXECUTABLE}" 0
    ${EndIf}
    
    ${NSD_GetState} $EnableAutoStart $0
    ${If} $0 = ${BST_CHECKED}
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "${APP_NAME_EN}" '"$INSTDIR\${APP_EXECUTABLE}" --minimized'
    ${EndIf}
    
    ; 设置应用程序权限
    DetailPrint "配置应用程序权限..."
    AccessControl::GrantOnFile "$INSTDIR" "(BU)" "FullAccess"
    
    ; 创建应用数据目录
    SetShellVarContext current
    CreateDirectory "$APPDATA\${APP_PUBLISHER}\${APP_NAME_EN}"
    CreateDirectory "$LOCALAPPDATA\${APP_PUBLISHER}\${APP_NAME_EN}"
    
    ; 复制默认配置文件
    IfFileExists "$INSTDIR\config\default_config.json" 0 +2
    CopyFiles /SILENT "$INSTDIR\config\default_config.json" "$APPDATA\${APP_PUBLISHER}\${APP_NAME_EN}\config.json"
    
    ; 注册应用程序到Windows防火墙
    DetailPrint "配置Windows防火墙..."
    nsExec::ExecToLog 'netsh advfirewall firewall add rule name="${APP_NAME}" dir=in action=allow program="$INSTDIR\${APP_EXECUTABLE}" enable=yes'
    
    ; 写入安装完成标志
    WriteRegStr HKLM "${APP_REGKEY}" "InstallComplete" "1"
    WriteRegStr HKLM "${APP_REGKEY}" "InstallDate" "$CMDLINE"  ; 可以改为实际日期
    
SectionEnd

;--------------------------------
; 节描述
LangString DESC_SecCore ${LANG_SIMPCHINESE} "应用程序核心文件（必需）"
LangString DESC_SecStartMenu ${LANG_SIMPCHINESE} "创建开始菜单快捷方式"
LangString DESC_SecDesktop ${LANG_SIMPCHINESE} "创建桌面快捷方式"
LangString DESC_SecFileAssoc ${LANG_SIMPCHINESE} "关联.poe2build文件类型"
LangString DESC_SecVCRedist ${LANG_SIMPCHINESE} "安装Visual C++运行库（应用程序运行必需）"

LangString DESC_SecCore ${LANG_ENGLISH} "Core application files (required)"
LangString DESC_SecStartMenu ${LANG_ENGLISH} "Create Start Menu shortcuts"
LangString DESC_SecDesktop ${LANG_ENGLISH} "Create Desktop shortcut"
LangString DESC_SecFileAssoc ${LANG_ENGLISH} "Associate .poe2build file type"
LangString DESC_SecVCRedist ${LANG_ENGLISH} "Install Visual C++ Redistributable (required for application)"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecCore} $(DESC_SecCore)
    !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} $(DESC_SecStartMenu)
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} $(DESC_SecDesktop)
    !insertmacro MUI_DESCRIPTION_TEXT ${SecFileAssoc} $(DESC_SecFileAssoc)
    !insertmacro MUI_DESCRIPTION_TEXT ${SecVCRedist} $(DESC_SecVCRedist)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

;--------------------------------
; 卸载节
Section "Uninstall"
    
    ; 停止运行中的应用程序
    DetailPrint "停止应用程序进程..."
    ${nsProcess::FindProcess} "${APP_EXECUTABLE}" $R0
    ${If} $R0 = 0
        ${nsProcess::KillProcess} "${APP_EXECUTABLE}" $R0
        Sleep 2000
    ${EndIf}
    
    ; 移除文件关联
    DetailPrint "移除文件关联..."
    DeleteRegKey HKCR ".poe2build"
    DeleteRegKey HKCR "PoE2Build.BuildFile"
    
    ; 移除自动启动
    DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "${APP_NAME_EN}"
    
    ; 移除防火墙规则
    nsExec::ExecToLog 'netsh advfirewall firewall delete rule name="${APP_NAME}"'
    
    ; 删除快捷方式
    SetShellVarContext all
    Delete "$DESKTOP\${APP_NAME}.lnk"
    Delete "$QUICKLAUNCH\${APP_NAME}.lnk"
    RMDir /r "$SMPROGRAMS\${APP_PUBLISHER}"
    
    ; 删除注册表项
    DeleteRegKey HKLM "${UNINSTALL_REGKEY}"
    DeleteRegKey HKLM "${APP_REGKEY}"
    
    ; 删除程序文件
    DetailPrint "删除应用程序文件..."
    RMDir /r "$INSTDIR"
    
    ; 询问是否删除用户数据
    MessageBox MB_YESNO|MB_ICONQUESTION "是否删除用户配置和数据文件？$\n$\n选择'否'将保留您的个人设置和构筑数据。" IDYES delete_userdata IDNO keep_userdata
    delete_userdata:
        DetailPrint "删除用户数据..."
        SetShellVarContext current
        RMDir /r "$APPDATA\${APP_PUBLISHER}\${APP_NAME_EN}"
        RMDir /r "$LOCALAPPDATA\${APP_PUBLISHER}\${APP_NAME_EN}"
        RMDir "$APPDATA\${APP_PUBLISHER}"
        RMDir "$LOCALAPPDATA\${APP_PUBLISHER}"
    keep_userdata:
    
    ; 刷新Shell
    System::Call 'shell32.dll::SHChangeNotify(l, l, i, i) v (0x08000000, 0, 0, 0)'
    
    DetailPrint "卸载完成"
    
SectionEnd

;--------------------------------
; 安装函数
Function .onInit
    
    ; 检查系统要求
    ${IfNot} ${AtLeastWin10}
        MessageBox MB_OK|MB_ICONSTOP "${APP_NAME}需要Windows 10或更高版本。"
        Abort
    ${EndIf}
    
    ; 检查是否已安装
    ReadRegStr $R0 HKLM "${UNINSTALL_REGKEY}" "UninstallString"
    ${If} $R0 != ""
        MessageBox MB_YESNOCANCEL|MB_ICONEXCLAMATION "${APP_NAME}已经安装。$\n$\n点击'是'卸载现有版本，点击'否'取消安装。" IDYES uninst IDNO quit
        quit:
            Abort
        uninst:
            ClearErrors
            ExecWait '$R0 /S _?=$INSTDIR'
            IfErrors no_remove_uninstaller done
            no_remove_uninstaller:
        done:
    ${EndIf}
    
    ; 初始化插件
    ${nsProcess::FindProcess} "${APP_EXECUTABLE}" $R0
    
FunctionEnd

Function .onInstSuccess
    ; 安装成功后的处理
    DetailPrint "${APP_NAME}安装成功！"
FunctionEnd

Function un.onInit
    MessageBox MB_YESNO|MB_ICONQUESTION "确实要完全移除${APP_NAME}及其所有组件吗？" IDYES +2
    Abort
FunctionEnd

Function un.onUninstSuccess
    MessageBox MB_OK|MB_ICONINFORMATION "${APP_NAME}已成功从您的计算机中移除。"
FunctionEnd