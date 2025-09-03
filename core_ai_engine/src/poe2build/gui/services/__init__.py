"""
GUI服务模块

包含GUI与后端系统的集成服务，提供：
- 后端通信客户端
- 数据转换器
- 状态管理器
- Windows系统集成服务
- 错误处理器
"""

from .backend_client import BackendClient
from .data_converter import DataConverter
from .status_manager import StatusManager

# Windows系统集成（可选，根据平台可用性）
try:
    from .windows_integration import (
        WindowsIntegrationService,
        get_windows_integration_service,
        initialize_windows_integration
    )
    WINDOWS_INTEGRATION_AVAILABLE = True
except ImportError:
    WINDOWS_INTEGRATION_AVAILABLE = False
    WindowsIntegrationService = None
    get_windows_integration_service = None
    initialize_windows_integration = None

__all__ = [
    'BackendClient',
    'DataConverter', 
    'StatusManager',
    'WINDOWS_INTEGRATION_AVAILABLE'
]

# 有条件地添加Windows集成到exports
if WINDOWS_INTEGRATION_AVAILABLE:
    __all__.extend([
        'WindowsIntegrationService',
        'get_windows_integration_service',
        'initialize_windows_integration'
    ])