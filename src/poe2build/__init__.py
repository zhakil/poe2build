"""
PoE2 Build Generator - 智能Path of Exile 2构筑生成器

基于真实PoE2数据源的智能构筑推荐系统，集成：
- PoB2本地集成：利用Path of Building Community进行精确计算
- RAG智能训练：基于poe.ninja真实Meta数据的AI推荐
- 弹性数据源：集成PoE2Scout、PoE2DB、poe.ninja等数据源
"""

# 暂时不导入核心模块，直到它们被创建
# from .core.ai_orchestrator import PoE2AIOrchestrator

# 导入数据模型供外部使用
from .models import *

__version__ = "2.0.0"
__author__ = "PoE2 Build Generator Team"
__email__ = "dev@poe2build.com"

__all__ = [
    # 数据模型将通过models包的__all__自动导入
]
