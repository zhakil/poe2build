"""
PoB2本地客户端 - Path of Building Community (PoE2)本地安装接口
"""

import os
import subprocess
import json
import psutil
from pathlib import Path
from typing import Optional, Dict, List
import logging
import tempfile

from .path_detector import PoB2PathDetector

logger = logging.getLogger(__name__)


class PoB2LocalClient:
    """本地Path of Building Community (PoE2)客户端接口"""
    
    def __init__(self):
        self.installation_path: Optional[Path] = None
        self.executable_path: Optional[Path] = None
        self.version_info: Optional[Dict] = None
        self._detect_installation()
    
    def _detect_installation(self) -> bool:
        """智能检测PoB2安装路径"""
        
        logger.info("正在检测PoB2安装...")
        
        # 使用路径检测器查找PoB2安装
        detected_path = PoB2PathDetector.detect()
        
        if detected_path:
            pob2_path = Path(detected_path)
            if self._verify_pob2_installation(pob2_path):
                self.installation_path = pob2_path
                self.executable_path = self._find_executable(pob2_path)
                self.version_info = self._get_version_info()
                
                logger.info(f"PoB2检测成功: {self.installation_path}")
                logger.info(f"可执行文件: {self.executable_path}")
                logger.info(f"版本信息: {self.version_info}")
                
                return True
        
        logger.warning("未找到PoB2安装")
        return False
    
    def _verify_pob2_installation(self, path: Path) -> bool:
        """验证PoB2安装的有效性"""
        if not path.exists() or not path.is_dir():
            return False
        
        required_files = [
            'Path of Building.exe',  # 主执行文件
            'lua',                   # Lua脚本目录
            'Data'                   # 数据目录
        ]
        
        for required_file in required_files:
            file_path = path / required_file
            if not file_path.exists():
                logger.debug(f"缺少必需文件/目录: {file_path}")
                return False
        
        return True
    
    def _find_executable(self, installation_path: Path) -> Optional[Path]:
        """查找PoB2可执行文件"""
        return PoB2PathDetector.find_executable(installation_path)
    
    def _get_version_info(self) -> Dict:
        """获取PoB2版本信息"""
        try:
            if not self.executable_path:
                return {'version': 'unknown', 'build': 'unknown'}
            
            # 尝试从文件属性获取版本信息 (Windows)
            if os.name == 'nt':
                try:
                    import win32api
                    version_info = win32api.GetFileVersionInfo(str(self.executable_path), "\\")
                    version_ms = version_info['FileVersionMS']
                    version_ls = version_info['FileVersionLS']
                    version = f"{version_ms >> 16}.{version_ms & 0xFFFF}.{version_ls >> 16}.{version_ls & 0xFFFF}"
                    
                    return {
                        'version': version,
                        'build': version_ls & 0xFFFF,
                        'executable': str(self.executable_path),
                        'method': 'win32api'
                    }
                except ImportError:
                    logger.debug("win32api不可用，使用基础检测")
                except Exception as e:
                    logger.debug(f"版本检测失败: {e}")
            
            # 基础版本检测 - 通过文件修改时间和大小
            stat_info = self.executable_path.stat()
            return {
                'version': 'detected',
                'build': 'unknown',
                'executable': str(self.executable_path),
                'file_size': stat_info.st_size,
                'modified_time': stat_info.st_mtime,
                'method': 'basic'
            }
            
        except Exception as e:
            logger.warning(f"获取版本信息失败: {e}")
            return {'version': 'error', 'build': 'unknown', 'error': str(e)}
    
    def is_available(self) -> bool:
        """检查PoB2是否可用"""
        return self.installation_path is not None and self.executable_path is not None
    
    def is_running(self) -> bool:
        """检查PoB2是否正在运行"""
        if not self.executable_path:
            return False
        
        exe_name = self.executable_path.name
        try:
            for process in psutil.process_iter(['name']):
                if process.info['name'] == exe_name:
                    return True
        except Exception as e:
            logger.debug(f"检查运行状态失败: {e}")
        
        return False
    
    def get_installation_info(self) -> Dict:
        """获取PoB2安装信息"""
        return {
            'available': self.is_available(),
            'installation_path': str(self.installation_path) if self.installation_path else None,
            'executable_path': str(self.executable_path) if self.executable_path else None,
            'version_info': self.version_info,
            'running': self.is_running()
        }
    
    def validate_build_file(self, build_file_path: str) -> Dict:
        """验证构筑文件格式"""
        try:
            build_path = Path(build_file_path)
            if not build_path.exists():
                return {'valid': False, 'error': '文件不存在'}
            
            # 检查文件扩展名
            if build_path.suffix.lower() not in ['.xml', '.pob']:
                return {'valid': False, 'error': '不支持的文件格式'}
            
            # 读取文件内容进行基础验证
            with open(build_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # XML格式构筑文件验证
            if build_path.suffix.lower() == '.xml':
                if '<PathOfBuilding>' not in content or '</PathOfBuilding>' not in content:
                    return {'valid': False, 'error': 'XML格式无效'}
            
            return {
                'valid': True,
                'file_size': len(content),
                'format': build_path.suffix.lower()
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def launch_pob2(self, build_file_path: Optional[str] = None) -> bool:
        """启动PoB2应用程序"""
        if not self.is_available():
            logger.error("PoB2不可用，无法启动")
            return False
        
        try:
            cmd = [str(self.executable_path)]
            
            # 如果提供了构筑文件，作为参数传递
            if build_file_path:
                validation = self.validate_build_file(build_file_path)
                if validation['valid']:
                    cmd.append(build_file_path)
                else:
                    logger.warning(f"构筑文件验证失败: {validation['error']}")
            
            # 启动进程
            subprocess.Popen(
                cmd,
                cwd=self.installation_path,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            logger.info(f"PoB2启动成功: {cmd}")
            return True
            
        except Exception as e:
            logger.error(f"启动PoB2失败: {e}")
            return False
    
    def get_data_directory(self) -> Optional[Path]:
        """获取PoB2数据目录路径"""
        if not self.installation_path:
            return None
        
        data_dir = self.installation_path / "Data"
        return data_dir if data_dir.exists() else None
    
    def get_lua_directory(self) -> Optional[Path]:
        """获取PoB2 Lua脚本目录路径"""
        if not self.installation_path:
            return None
        
        lua_dir = self.installation_path / "lua"
        return lua_dir if lua_dir.exists() else None
    
    def check_dependencies(self) -> Dict:
        """检查PoB2依赖项"""
        dependencies = {
            'lua_directory': self.get_lua_directory() is not None,
            'data_directory': self.get_data_directory() is not None,
            'executable_accessible': self.executable_path and self.executable_path.exists()
        }
        
        # 检查关键Lua模块是否存在
        lua_dir = self.get_lua_directory()
        if lua_dir:
            critical_lua_files = [
                'Build.lua',
                'PassiveSpec.lua', 
                'TreeTab.lua',
                'CalcDefence.lua',
                'CalcOffence.lua'
            ]
            
            for lua_file in critical_lua_files:
                file_path = lua_dir / lua_file
                dependencies[f'lua_{lua_file.lower().replace(".lua", "")}'] = file_path.exists()
        
        # 检查数据文件
        data_dir = self.get_data_directory()
        if data_dir:
            critical_data_files = [
                'Skills',
                'PassiveSkillTree',
                'Stats'
            ]
            
            for data_item in critical_data_files:
                item_path = data_dir / data_item
                dependencies[f'data_{data_item.lower()}'] = item_path.exists()
        
        dependencies['overall_health'] = all(dependencies.values())
        
        return dependencies
    
    def create_temp_build_file(self, build_content: str, file_format: str = 'xml') -> Path:
        """创建临时构筑文件"""
        suffix = '.xml' if file_format == 'xml' else '.pob'
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=suffix,
            delete=False,
            encoding='utf-8'
        ) as temp_file:
            temp_file.write(build_content)
            temp_path = Path(temp_file.name)
        
        logger.debug(f"创建临时构筑文件: {temp_path}")
        return temp_path
    
    def cleanup_temp_files(self, temp_files: List[Path]):
        """清理临时文件"""
        for temp_file in temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    logger.debug(f"清理临时文件: {temp_file}")
            except Exception as e:
                logger.warning(f"清理临时文件失败 {temp_file}: {e}")
    
    def health_check(self) -> Dict:
        """综合健康检查"""
        health_info = {
            'pob2_available': self.is_available(),
            'pob2_running': self.is_running(),
            'installation_info': self.get_installation_info(),
            'dependencies': self.check_dependencies(),
            'detection_results': PoB2PathDetector.detect_all_methods()
        }
        
        # 计算整体健康状态
        critical_checks = [
            health_info['pob2_available'],
            health_info['dependencies'].get('overall_health', False)
        ]
        
        health_info['overall_healthy'] = all(critical_checks)
        health_info['status'] = 'healthy' if health_info['overall_healthy'] else 'degraded'
        
        return health_info