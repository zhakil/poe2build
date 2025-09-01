"""
PoB2ÆB - Path of Building Community (PoE2)Æ!W

,!WĞ›Œt„PoB2ÆŸıì
- PoB2‰ÅÀKŒï„¡
- „QpnüeŒã
- PoB2¡—Î(
- AIq¨„„Q

;Äö
- PoB2LocalClient: ,0PoB2¢7ï¥ã
- PoB2BuildImporter: „Q<ãh
- PoB2CalculationEngine: ¡—ÎÅh
- PoB2BuildGenerator: AI„Qh
- PoB2PathDetector: èsğï„ÀKh
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

# H,áo
__version__ = '1.0.0'
__author__ = 'PoE2 Build Generator Team'

# ëwå‚ıp
def create_pob2_integration() -> 'PoB2BuildGenerator':
    """
    úŒt„PoB2Æ‹
    
    Returns:
        PoB2BuildGenerator: Mn}„„Qh‹
    """
    client = PoB2LocalClient()
    return PoB2BuildGenerator(client)

def check_pob2_availability() -> dict:
    """
    ÀåPoB2ï('
    
    Returns:
        dict: +ï('áo„Wx
    """
    client = PoB2LocalClient()
    return client.health_check()