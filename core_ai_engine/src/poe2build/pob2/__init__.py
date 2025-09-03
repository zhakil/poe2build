"""
PoB2集成模块 - Path of Building Community (PoE2)集成

提供完整的PoB2集成功能：
- PoB2安装检测
- 构筑导入导出
- PoB2精确计算
- AI构筑生成与PoB2集成
- 高级构筑分析和优化

主要组件：
- PoB2LocalClient: 本地PoB2客户端
- PoB2BuildImporter: 构筑导入器
- PoB2CalculationEngine: 计算引擎包装器
- PoB2BuildGenerator: AI构筑生成器
- PoB2PathDetector: 路径检测器
- PoB2Calculator: 高级计算器和分析器
"""

from .local_client import PoB2LocalClient
from .build_importer import PoB2BuildImporter
from .calculation_engine import PoB2CalculationEngine
from .build_generator import PoB2BuildGenerator
from .path_detector import PoB2PathDetector
from .calculator import PoB2Calculator, PoB2CalculatorFallback

__all__ = [
    'PoB2LocalClient',
    'PoB2BuildImporter', 
    'PoB2CalculationEngine',
    'PoB2BuildGenerator',
    'PoB2PathDetector',
    'PoB2Calculator',
    'PoB2CalculatorFallback'
]

# 版本信息
__version__ = '1.0.0'
__author__ = 'PoE2 Build Generator Team'

# 便捷函数
def create_pob2_integration() -> 'PoB2BuildGenerator':
    """
    创建完整的PoB2集成实例
    
    Returns:
        PoB2BuildGenerator: 可用的构筑生成器实例
    """
    client = PoB2LocalClient()
    return PoB2BuildGenerator(client)

def create_pob2_calculator() -> 'PoB2Calculator':
    """
    创建PoB2计算器实例
    
    Returns:
        PoB2Calculator: 可用的计算器实例
    """
    return PoB2Calculator()

def check_pob2_availability() -> dict:
    """
    检查PoB2可用性
    
    Returns:
        dict: 包含可用性信息的状态字典
    """
    client = PoB2LocalClient()
    return client.health_check()