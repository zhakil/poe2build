"""
PoB2�B - Path of Building Community (PoE2)�!W

,!WЛ�t�PoB2����
- PoB2���K�
- �Qpn�e��
- PoB2���(
- AIq���Q

;���
- PoB2LocalClient: ,0PoB2�7��
- PoB2BuildImporter: �Q<�h
- PoB2CalculationEngine: ����h
- PoB2BuildGenerator: AI�Qh
- PoB2PathDetector: �s���Kh
"""

from .local_client import PoB2LocalClient
from .build_importer import PoB2BuildImporter
from .calculation_engine import PoB2CalculationEngine
from .build_generator import PoB2BuildGenerator
from .path_detector import PoB2PathDetector

__all__ = [
    'PoB2LocalClient',
    'PoB2BuildImporter', 
    'PoB2CalculationEngine',
    'PoB2BuildGenerator',
    'PoB2PathDetector'
]

# H,�o
__version__ = '1.0.0'
__author__ = 'PoE2 Build Generator Team'

# �w��p
def create_pob2_integration() -> 'PoB2BuildGenerator':
    """
    ��t�PoB2���
    
    Returns:
        PoB2BuildGenerator: Mn}��Qh��
    """
    client = PoB2LocalClient()
    return PoB2BuildGenerator(client)

def check_pob2_availability() -> dict:
    """
    ��PoB2�('
    
    Returns:
        dict: +�('�o�Wx
    """
    client = PoB2LocalClient()
    return client.health_check()