"""
PoB2路径检测器 - 跨平台支持Path of Building Community (PoE2)安装检测
"""

import os
import glob
import psutil
from pathlib import Path
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class PoB2PathDetector:
    """跨平台PoB2路径检测器"""
    
    @staticmethod
    def get_search_paths() -> List[str]:
        """获取平台特定的搜索路径"""
        
        if os.name == 'nt':  # Windows
            return [
                # Steam路径
                "C:/Program Files (x86)/Steam/steamapps/common/Path of Exile 2/Path of Building Community (PoE2)",
                "D:/Steam/steamapps/common/Path of Exile 2/Path of Building Community (PoE2)",
                "E:/Steam/steamapps/common/Path of Exile 2/Path of Building Community (PoE2)",
                "F:/steam/steamapps/common/Path of Exile 2/Path of Building Community (PoE2)",
                
                # Epic Games路径
                "C:/Program Files/Epic Games/Path of Exile 2/Path of Building Community (PoE2)",
                "D:/Epic Games/Path of Exile 2/Path of Building Community (PoE2)",
                
                # 独立安装路径
                "C:/Path of Building Community (PoE2)",
                "D:/Games/Path of Building Community (PoE2)",
                "C:/Program Files/Path of Building Community (PoE2)",
                
                # 用户目录
                f"{os.path.expanduser('~')}/Documents/Path of Building Community (PoE2)",
                f"{os.path.expanduser('~')}/Games/Path of Building Community (PoE2)"
            ]
        else:  # Linux/Mac
            return [
                f"{os.path.expanduser('~')}/.steam/steam/steamapps/common/Path of Exile 2/Path of Building Community (PoE2)",
                f"{os.path.expanduser('~')}/Games/Path of Building Community (PoE2)",
                "/opt/Path of Building Community (PoE2)",
                "/usr/local/games/Path of Building Community (PoE2)"
            ]
    
    @staticmethod
    def detect_via_registry() -> Optional[str]:
        """通过Windows注册表检测（Windows专用）"""
        if os.name != 'nt':
            return None
            
        try:
            import winreg
            
            # 检查Steam注册表
            steam_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Valve\\Steam")
            steam_path = winreg.QueryValueEx(steam_key, "InstallPath")[0]
            potential_path = os.path.join(steam_path, "steamapps", "common", "Path of Exile 2", "Path of Building Community (PoE2)")
            
            if os.path.exists(potential_path):
                return potential_path
                
        except Exception as e:
            logger.debug(f"Registry detection failed: {e}")
        
        return None
    
    @staticmethod
    def detect_via_process() -> Optional[str]:
        """通过运行中的进程检测"""
        try:
            for process in psutil.process_iter(['pid', 'name', 'exe']):
                process_name = process.info.get('name', '')
                if 'Path of Building' in process_name or 'PathOfBuilding' in process_name:
                    exe_path = process.info.get('exe')
                    if exe_path:
                        return os.path.dirname(exe_path)
        except Exception as e:
            logger.debug(f"Process detection failed: {e}")
        
        return None
    
    @staticmethod
    def detect_via_glob_search() -> Optional[str]:
        """通过全局搜索检测PoB2安装"""
        
        # 搜索模式
        search_patterns = [
            # Steam默认路径模式
            "*/steamapps/common/Path of Exile 2/Path of Building Community (PoE2)",
            # Epic Games路径模式
            "*/Epic Games/Path of Exile 2/Path of Building Community (PoE2)",
            # 独立安装路径模式
            "*/Path of Building Community (PoE2)",
            "*/PoB2",
            "*/*Path of Building*PoE2*"
        ]
        
        # 搜索所有驱动器 (Windows) 或根目录 (Linux/Mac)
        drives = ['C:', 'D:', 'E:', 'F:', 'G:'] if os.name == 'nt' else ['/']
        
        for drive in drives:
            for pattern in search_patterns:
                full_pattern = os.path.join(drive, pattern)
                
                try:
                    matches = glob.glob(full_pattern, recursive=True)
                    
                    for match in matches:
                        pob2_path = Path(match)
                        if PoB2PathDetector._verify_pob2_installation(pob2_path):
                            logger.info(f"Found PoB2 installation via glob search: {pob2_path}")
                            return str(pob2_path)
                            
                except Exception as e:
                    logger.debug(f"Glob search failed for pattern {full_pattern}: {e}")
                    continue
        
        return None
    
    @staticmethod
    def _verify_pob2_installation(path: Path) -> bool:
        """验证PoB2安装的有效性"""
        if not path.exists() or not path.is_dir():
            return False
        
        # 必须存在的文件和目录
        required_files = [
            'Path of Building.exe',  # 主执行文件
            'lua',                   # Lua脚本目录
            'Data'                   # 数据目录
        ]
        
        for required_file in required_files:
            file_path = path / required_file
            if not file_path.exists():
                logger.debug(f"Missing required file/directory: {file_path}")
                return False
        
        return True
    
    @staticmethod
    def find_executable(installation_path: Path) -> Optional[Path]:
        """在安装目录中查找PoB2可执行文件"""
        possible_exes = [
            'Path of Building.exe',
            'PathOfBuilding.exe', 
            'PoB.exe',
            'PoB2.exe'
        ]
        
        for exe_name in possible_exes:
            exe_path = installation_path / exe_name
            if exe_path.exists() and exe_path.is_file():
                return exe_path
        
        return None
    
    @staticmethod
    def detect_all_methods() -> Dict[str, Optional[str]]:
        """使用所有检测方法尝试找到PoB2安装"""
        detection_results = {
            'registry': PoB2PathDetector.detect_via_registry(),
            'process': PoB2PathDetector.detect_via_process(), 
            'glob_search': PoB2PathDetector.detect_via_glob_search(),
            'predefined_paths': None
        }
        
        # 检查预定义路径
        for path_str in PoB2PathDetector.get_search_paths():
            path = Path(path_str)
            if PoB2PathDetector._verify_pob2_installation(path):
                detection_results['predefined_paths'] = str(path)
                break
        
        return detection_results
    
    @staticmethod
    def detect() -> Optional[str]:
        """主检测方法 - 按优先级尝试所有检测方式"""
        
        # 1. 首先尝试运行中的进程检测（最可靠）
        process_path = PoB2PathDetector.detect_via_process()
        if process_path:
            logger.info(f"PoB2 detected via running process: {process_path}")
            return process_path
        
        # 2. 尝试Windows注册表检测
        registry_path = PoB2PathDetector.detect_via_registry()
        if registry_path:
            logger.info(f"PoB2 detected via registry: {registry_path}")
            return registry_path
        
        # 3. 检查预定义路径
        for path_str in PoB2PathDetector.get_search_paths():
            path = Path(path_str)
            if PoB2PathDetector._verify_pob2_installation(path):
                logger.info(f"PoB2 detected via predefined path: {path}")
                return str(path)
        
        # 4. 最后尝试全局搜索（最耗时）
        glob_path = PoB2PathDetector.detect_via_glob_search()
        if glob_path:
            logger.info(f"PoB2 detected via glob search: {glob_path}")
            return glob_path
        
        logger.warning("PoB2 installation not found using any detection method")
        return None