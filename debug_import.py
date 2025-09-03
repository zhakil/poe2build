#!/usr/bin/env python3
"""
调试导入问题
"""

import sys
from pathlib import Path

# 设置编码
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "core_ai_engine"))

print("测试导入步骤...")

# 第1步：测试数据源导入
try:
    print("[1/4] 测试数据源基础导入...")
    from core_ai_engine.src.poe2build.data_sources import BaseDataSource
    print("   OK - BaseDataSource导入成功")
except Exception as e:
    print(f"   ERROR - BaseDataSource导入失败: {e}")

# 第2步：测试四大数据源导入
try:
    print("[2/4] 测试四大数据源导入...")
    from core_ai_engine.src.poe2build.data_sources import (
        get_all_four_sources,
        health_check_all_sources,
        get_poe2scout_client,
        get_ninja_scraper,
        get_pob2_extractor,
        get_poe2db_client
    )
    print("   OK - 四大数据源导入成功")
except Exception as e:
    print(f"   ERROR - 四大数据源导入失败: {e}")
    import traceback
    traceback.print_exc()

# 第3步：测试RAG导入
try:
    print("[3/4] 测试RAG集成导入...")
    from core_ai_engine.src.poe2build.rag.four_sources_integration import (
        FourSourcesRAGTrainer,
        FourSourcesData,
        train_rag_with_four_sources
    )
    print("   OK - RAG集成导入成功")
except Exception as e:
    print(f"   ERROR - RAG集成导入失败: {e}")
    import traceback
    traceback.print_exc()

# 第4步：测试函数调用
try:
    print("[4/4] 测试健康检查函数...")
    sources = get_all_four_sources()
    print(f"   OK - 获取到{len(sources)}个数据源")
    
    health = health_check_all_sources()
    print(f"   OK - 健康检查返回{len(health)}个状态")
except Exception as e:
    print(f"   ERROR - 函数调用失败: {e}")
    import traceback
    traceback.print_exc()

print("\n导入测试完成!")