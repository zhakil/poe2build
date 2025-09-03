#!/usr/bin/env python3
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "core_ai_engine"))

try:
    from core_ai_engine.src.poe2build.data_sources.pob2.data_extractor import PoB2DataExtractor
    print("SUCCESS: 导入PoB2DataExtractor")
    
    extractor = PoB2DataExtractor(use_github=True)
    print(f"GitHub可用: {extractor.is_available()}")
    print(f"仓库: {extractor.GITHUB_REPO}")
    print(f"URL: {extractor.GITHUB_RAW_BASE}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()