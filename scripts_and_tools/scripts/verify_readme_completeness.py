#!/usr/bin/env python3
"""
README.md 完整性验证脚本
验证README.md是否包含所有必要的Windows GUI部署内容
"""

import os
import sys
from pathlib import Path

def verify_readme_completeness():
    """验证README.md的完整性"""
    readme_path = Path(__file__).parent.parent / "README.md"
    
    if not readme_path.exists():
        print("❌ README.md 文件不存在")
        return False
    
    content = readme_path.read_text(encoding='utf-8')
    
    # 必须包含的关键部分
    required_sections = [
        # Phase 7 Windows GUI开发
        "Phase 7: Windows GUI应用开发",
        "Windows GUI架构设计",
        "GUI组件系统实现", 
        "主窗口和布局实现",
        "GUI与后端数据集成",
        "Windows系统特有功能",
        "应用主题和样式系统",
        
        # GUI环境设置
        "Windows GUI应用系统要求",
        "GUI开发专用环境检查",
        "GUI开发专用设置",
        
        # GUI架构图表
        "Windows GUI应用完整架构",
        "GUI数据流架构",
        
        # 性能指标
        "Windows GUI应用性能",
        "Windows系统兼容性",
        "硬件要求和性能表现",
        
        # 部署和打包
        "PyInstaller打包",
        "Inno Setup安装程序",
        "自动化构建和打包脚本",
        
        # 故障排除
        "PyQt6/GUI框架问题",
        "Windows系统集成问题",
        "GUI应用响应缓慢",
        
        # 使用示例
        "GUI版本使用示例",
        "异步任务处理示例"
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)
    
    # 必须包含的代码块和配置
    required_code_patterns = [
        "PyQt6",
        "pyinstaller",
        "build_exe.py", 
        "setup.iss",
        "poe2_gui_app.py",
        "AsyncWorker",
        "BuildRequestForm",
        "SystemTray",
        "windows_integration",
        "auto_updater"
    ]
    
    missing_code = []
    for pattern in required_code_patterns:
        if pattern not in content:
            missing_code.append(pattern)
    
    # 验证prompt文件引用
    required_prompts = [
        "prompts/13_windows_gui_architecture.txt",
        "prompts/14_gui_components.txt",
        "prompts/15_main_window.txt",
        "prompts/16_gui_data_integration.txt", 
        "prompts/17_windows_features.txt",
        "prompts/18_gui_themes.txt"
    ]
    
    missing_prompts = []
    for prompt in required_prompts:
        if prompt not in content:
            missing_prompts.append(prompt)
    
    # 统计信息
    total_lines = len(content.splitlines())
    code_blocks = content.count("```")
    mermaid_diagrams = content.count("```mermaid")
    
    print("=" * 60)
    print("README.md 完整性验证报告")
    print("=" * 60)
    print(f"📊 总行数: {total_lines}")
    print(f"📊 代码块数量: {code_blocks // 2}")  # 成对出现
    print(f"📊 架构图数量: {mermaid_diagrams}")
    print()
    
    # 报告结果
    success = True
    
    if missing_sections:
        print("❌ 缺失的必要章节:")
        for section in missing_sections:
            print(f"   - {section}")
        success = False
    else:
        print("✅ 所有必要章节都已包含")
    
    print()
    
    if missing_code:
        print("⚠️  缺失的代码示例或配置:")
        for code in missing_code:
            print(f"   - {code}")
        success = False
    else:
        print("✅ 所有必要的代码示例都已包含")
    
    print()
    
    if missing_prompts:
        print("⚠️  缺失的prompt文件引用:")
        for prompt in missing_prompts:
            print(f"   - {prompt}")
    else:
        print("✅ 所有GUI相关prompt文件都已引用")
    
    print()
    print("=" * 60)
    
    if success:
        print("🎉 README.md 完整性验证通过！")
        print("📖 文档包含了完整的Windows GUI应用部署指南")
        return True
    else:
        print("⚠️  README.md 需要进一步完善")
        print("📝 建议补充缺失的内容以确保完整性")
        return False

def check_gui_related_content():
    """专门检查GUI相关内容的完整性"""
    readme_path = Path(__file__).parent.parent / "README.md"
    content = readme_path.read_text(encoding='utf-8')
    
    # GUI特定内容检查
    gui_checks = {
        "GUI架构设计": [
            "MVC Pattern",
            "Model-View-Controller", 
            "QWidget",
            "QApplication"
        ],
        "Windows集成": [
            "系统托盘",
            "注册表操作",
            "文件关联",
            "Windows通知",
            "pywin32"
        ],
        "主题系统": [
            "PoE2主题",
            "Windows主题", 
            "QSS",
            "样式表"
        ],
        "异步处理": [
            "QThread",
            "异步工作器",
            "信号槽",
            "后台任务"
        ],
        "打包分发": [
            "PyInstaller",
            "Inno Setup",
            "Windows Installer",
            "可执行文件"
        ]
    }
    
    print("\n" + "=" * 50)
    print("GUI专项内容检查")
    print("=" * 50)
    
    for category, keywords in gui_checks.items():
        found_keywords = [kw for kw in keywords if kw in content]
        coverage = len(found_keywords) / len(keywords) * 100
        
        print(f"\n📋 {category}: {coverage:.1f}% 覆盖率")
        if coverage >= 75:
            print("   ✅ 覆盖充分")
        else:
            print("   ⚠️  覆盖不足，缺少:")
            missing = [kw for kw in keywords if kw not in content]
            for kw in missing:
                print(f"      - {kw}")

if __name__ == "__main__":
    print("开始验证 README.md 完整性...")
    print()
    
    # 基本完整性检查
    basic_check = verify_readme_completeness()
    
    # GUI专项检查  
    check_gui_related_content()
    
    print("\n" + "=" * 60)
    if basic_check:
        print("🚀 README.md 已准备就绪，可以指导用户完整部署!")
        sys.exit(0)
    else:
        print("❌ README.md 需要进一步完善后才能发布")
        sys.exit(1)