#!/usr/bin/env python3
"""
测试PoB2连接状态
"""

import sys
import os
from pathlib import Path

# 设置编码
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "core_ai_engine"))

try:
    from core_ai_engine.src.poe2build.data_sources.pob2.data_extractor import PoB2DataExtractor
    print("OK - 成功导入PoB2DataExtractor")
    
    # 测试本地模式
    print("\n[LOCAL] 测试本地PoB2安装检测...")
    extractor_local = PoB2DataExtractor(use_github=False)
    print(f"本地安装路径: {extractor_local.pob2_path}")
    print(f"本地模式可用: {extractor_local.is_available()}")
    
    if extractor_local.pob2_path:
        install_info = extractor_local.get_installation_info()
        print(f"安装信息: {install_info}")
    
    # 测试GitHub模式
    print("\n[GITHUB] 测试GitHub PoB2数据源...")
    extractor_github = PoB2DataExtractor(use_github=True)
    print(f"GitHub模式可用: {extractor_github.is_available()}")
    
    github_info = extractor_github.get_installation_info()
    print(f"GitHub信息: {github_info}")
    
    # 尝试获取技能宝石数据
    print("\n[GEMS] 测试技能宝石数据获取...")
    gems = extractor_github.get_skill_gems()
    print(f"获取到技能宝石数量: {len(gems)}")
    
    if gems:
        # 显示前3个技能宝石
        for i, (gem_id, gem) in enumerate(list(gems.items())[:3]):
            print(f"  {i+1}. {gem.name} ({gem_id}) - {gem.gem_type}")
    
    print("\nOK - PoB2连接测试完成")
    
except Exception as e:
    print(f"ERROR - PoB2连接测试失败: {e}")
    import traceback
    traceback.print_exc()