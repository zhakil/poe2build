"""Path of Building Community PoE2安装检测器"""

import os
import platform
import subprocess
import winreg
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import json

try:
    import psutil
except ImportError:
    psutil = None


class PoB2Platform(Enum):
    """PoB2支持的平台枚举"""
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"


class PoB2InstallType(Enum):
    """PoB2安装类型枚举"""
    STEAM = "steam"
    EPIC = "epic"
    STANDALONE = "standalone"
    PORTABLE = "portable"
    MANUAL = "manual"
    UNKNOWN = "unknown"


@dataclass
class PoB2Installation:
    """PoB2安装信息"""
    path: Path
    executable: Path
    install_type: PoB2InstallType
    version: Optional[str] = None
    platform: Optional[PoB2Platform] = None
    is_valid: bool = False
    last_modified: Optional[float] = None
    config_dir: Optional[Path] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'path': str(self.path),
            'executable': str(self.executable),
            'install_type': self.install_type.value,
            'version': self.version,
            'platform': self.platform.value if self.platform else None,
            'is_valid': self.is_valid,
            'last_modified': self.last_modified,
            'config_dir': str(self.config_dir) if self.config_dir else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PoB2Installation':
        """从字典创建实例"""
        return cls(
            path=Path(data['path']),
            executable=Path(data['executable']),
            install_type=PoB2InstallType(data['install_type']),
            version=data.get('version'),
            platform=PoB2Platform(data['platform']) if data.get('platform') else None,
            is_valid=data.get('is_valid', False),
            last_modified=data.get('last_modified'),
            config_dir=Path(data['config_dir']) if data.get('config_dir') else None
        )


class PoB2PathDetector:
    """Path of Building Community PoE2安装路径检测器"""
    
    def __init__(self):
        self._logger = logging.getLogger(f"{__name__}.PoB2PathDetector")
        self.current_platform = self._detect_platform()
        self.cache_file = Path.home() / '.poe2build' / 'pob2_cache.json'
        
        # PoB2可执行文件名
        self.executable_names = {
            PoB2Platform.WINDOWS: ['Path of Building.exe', 'PathOfBuilding.exe', 'pob.exe'],
            PoB2Platform.MACOS: ['Path of Building', 'PathOfBuilding.app'],
            PoB2Platform.LINUX: ['PathOfBuilding', 'Path of Building', 'pob']
        }
    
    def _detect_platform(self) -> PoB2Platform:
        """检测当前平台"""
        system = platform.system().lower()
        if system == 'windows':
            return PoB2Platform.WINDOWS
        elif system == 'darwin':
            return PoB2Platform.MACOS
        elif system == 'linux':
            return PoB2Platform.LINUX
        else:
            self._logger.warning(f"未知平台: {system}, 默认使用Linux")
            return PoB2Platform.LINUX
    
    async def detect_installations(self, use_cache: bool = True) -> List[PoB2Installation]:
        """检测所有PoB2安装"""
        installations = []
        
        # 尝试从缓存加载
        if use_cache:
            cached_installations = self._load_cache()
            if cached_installations:
                self._logger.info(f"从缓存加载到 {len(cached_installations)} 个PoB2安装")
                # 验证缓存的安装是否仍然有效
                valid_installations = []
                for install in cached_installations:
                    if await self._validate_installation(install):
                        valid_installations.append(install)
                
                if valid_installations:
                    return valid_installations
        
        # 执行全面检测
        self._logger.info("开始检测PoB2安装...")
        
        # 按平台检测
        if self.current_platform == PoB2Platform.WINDOWS:
            installations.extend(await self._detect_windows_installations())
        elif self.current_platform == PoB2Platform.MACOS:
            installations.extend(await self._detect_macos_installations())
        elif self.current_platform == PoB2Platform.LINUX:
            installations.extend(await self._detect_linux_installations())
        
        # 验证所有找到的安装
        valid_installations = []
        for install in installations:
            if await self._validate_installation(install):
                valid_installations.append(install)
        
        # 保存到缓存
        if valid_installations:
            self._save_cache(valid_installations)
        
        self._logger.info(f"检测到 {len(valid_installations)} 个有效的PoB2安装")
        return valid_installations
    
    async def _detect_windows_installations(self) -> List[PoB2Installation]:
        """检测Windows平台的PoB2安装"""
        installations = []
        
        # Steam安装位置
        steam_paths = self._get_steam_paths_windows()
        for steam_path in steam_paths:
            pob2_path = steam_path / 'steamapps' / 'common' / 'Path of Building Community PoE2'
            install = await self._check_path_for_pob2(pob2_path, PoB2InstallType.STEAM)
            if install:
                installations.append(install)
        
        # Epic Games安装位置
        epic_paths = self._get_epic_paths_windows()
        for epic_path in epic_paths:
            install = await self._check_path_for_pob2(epic_path, PoB2InstallType.EPIC)
            if install:
                installations.append(install)
        
        # 常见独立安装位置
        standalone_paths = [
            Path('C:/Program Files/Path of Building Community PoE2'),
            Path('C:/Program Files (x86)/Path of Building Community PoE2'),
            Path.home() / 'AppData' / 'Local' / 'Path of Building Community PoE2',
            Path('C:/Path of Building Community PoE2'),
            Path('D:/Path of Building Community PoE2'),
        ]
        
        for path in standalone_paths:
            install = await self._check_path_for_pob2(path, PoB2InstallType.STANDALONE)
            if install:
                installations.append(install)
        
        # 检查注册表
        registry_paths = self._get_registry_paths_windows()
        for path in registry_paths:
            install = await self._check_path_for_pob2(Path(path), PoB2InstallType.STANDALONE)
            if install:
                installations.append(install)
        
        return installations
    
    async def _detect_macos_installations(self) -> List[PoB2Installation]:
        """检测macOS平台的PoB2安装"""
        installations = []
        
        # Steam安装位置
        steam_path = Path.home() / 'Library' / 'Application Support' / 'Steam' / 'steamapps' / 'common' / 'Path of Building Community PoE2'
        install = await self._check_path_for_pob2(steam_path, PoB2InstallType.STEAM)
        if install:
            installations.append(install)
        
        # 应用程序目录
        app_paths = [
            Path('/Applications/Path of Building Community PoE2.app'),
            Path.home() / 'Applications' / 'Path of Building Community PoE2.app',
            Path('/Applications/Path of Building.app'),
            Path.home() / 'Applications' / 'Path of Building.app'
        ]
        
        for path in app_paths:
            install = await self._check_path_for_pob2(path, PoB2InstallType.STANDALONE)
            if install:
                installations.append(install)
        
        return installations
    
    async def _detect_linux_installations(self) -> List[PoB2Installation]:
        """检测Linux平台的PoB2安装"""
        installations = []
        
        # Steam安装位置
        steam_paths = [
            Path.home() / '.steam' / 'steam' / 'steamapps' / 'common' / 'Path of Building Community PoE2',
            Path.home() / '.local' / 'share' / 'Steam' / 'steamapps' / 'common' / 'Path of Building Community PoE2'
        ]
        
        for steam_path in steam_paths:
            install = await self._check_path_for_pob2(steam_path, PoB2InstallType.STEAM)
            if install:
                installations.append(install)
        
        # 常见Linux安装位置
        linux_paths = [
            Path('/opt/Path of Building Community PoE2'),
            Path.home() / '.local' / 'bin' / 'Path of Building Community PoE2',
            Path.home() / 'bin' / 'Path of Building Community PoE2',
            Path('/usr/local/bin/PathOfBuilding'),
            Path.home() / 'PathOfBuilding'
        ]
        
        for path in linux_paths:
            install = await self._check_path_for_pob2(path, PoB2InstallType.STANDALONE)
            if install:
                installations.append(install)
        
        return installations
    
    async def _check_path_for_pob2(self, path: Path, install_type: PoB2InstallType) -> Optional[PoB2Installation]:
        """检查指定路径是否包含PoB2安装"""
        if not path.exists():
            return None
        
        # 查找可执行文件
        executable = None
        for exe_name in self.executable_names[self.current_platform]:
            exe_path = path / exe_name
            if exe_path.exists():
                executable = exe_path
                break
            
            # 在子目录中查找
            for subdir in path.rglob(exe_name):
                if subdir.is_file():
                    executable = subdir
                    break
        
        if not executable:
            return None
        
        # 检查是否为PoE2版本
        if not await self._is_poe2_version(executable):
            return None
        
        # 获取版本信息
        version = await self._get_version(executable)
        
        # 获取配置目录
        config_dir = await self._get_config_directory(path)
        
        installation = PoB2Installation(
            path=path,
            executable=executable,
            install_type=install_type,
            version=version,
            platform=self.current_platform,
            is_valid=True,
            last_modified=executable.stat().st_mtime,
            config_dir=config_dir
        )
        
        return installation
    
    async def _validate_installation(self, installation: PoB2Installation) -> bool:
        """验证安装的有效性"""
        try:
            # 检查可执行文件是否存在
            if not installation.executable.exists():
                self._logger.warning(f"可执行文件不存在: {installation.executable}")
                return False
            
            # 检查是否可执行
            if not os.access(installation.executable, os.X_OK):
                self._logger.warning(f"文件无执行权限: {installation.executable}")
                return False
            
            # 检查修改时间是否变化（简单的版本更新检测）
            current_mtime = installation.executable.stat().st_mtime
            if installation.last_modified and current_mtime != installation.last_modified:
                self._logger.info(f"PoB2可执行文件已更新: {installation.executable}")
                installation.last_modified = current_mtime
            
            # 验证是否为PoE2版本
            if not await self._is_poe2_version(installation.executable):
                self._logger.warning(f"不是PoE2版本的Path of Building: {installation.executable}")
                return False
            
            return True
            
        except Exception as e:
            self._logger.error(f"验证PoB2安装失败: {e}")
            return False
    
    async def _is_poe2_version(self, executable: Path) -> bool:
        """检查是否为PoE2版本的Path of Building"""
        try:
            # 方法1: 检查可执行文件版本信息
            if self.current_platform == PoB2Platform.WINDOWS:
                # 在Windows上使用file properties检查
                result = subprocess.run([
                    'powershell', '-Command',
                    f'(Get-ItemProperty "{executable}").VersionInfo.ProductName'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    product_name = result.stdout.strip()
                    if 'PoE2' in product_name or 'Path of Exile 2' in product_name:
                        return True
            
            # 方法2: 检查安装目录中的相关文件
            install_dir = executable.parent
            poe2_indicators = [
                'PoE2', 'poe2', 'Path of Exile 2',
                'data/poe2', 'Data/PoE2'
            ]
            
            for item in install_dir.rglob('*'):
                if item.is_file() or item.is_dir():
                    for indicator in poe2_indicators:
                        if indicator.lower() in item.name.lower():
                            return True
            
            # 方法3: 尝试运行并检查输出
            try:
                result = subprocess.run([
                    str(executable), '--version'
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    output = result.stdout + result.stderr
                    if 'PoE2' in output or 'Path of Exile 2' in output:
                        return True
            except subprocess.TimeoutExpired:
                # 超时可能意味着程序启动了GUI，这也是可接受的
                return True
            except Exception:
                pass
            
            # 默认假设是PoE2版本（保守策略）
            return True
            
        except Exception as e:
            self._logger.error(f"检查PoE2版本失败: {e}")
            return True  # 默认认为是有效的
    
    async def _get_version(self, executable: Path) -> Optional[str]:
        """获取PoB2版本"""
        try:
            # 尝试运行 --version 参数
            result = subprocess.run([
                str(executable), '--version'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                version_output = result.stdout.strip()
                if version_output:
                    return version_output
            
            # 从文件属性获取版本（Windows）
            if self.current_platform == PoB2Platform.WINDOWS:
                result = subprocess.run([
                    'powershell', '-Command',
                    f'(Get-ItemProperty "{executable}").VersionInfo.ProductVersion'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    version = result.stdout.strip()
                    if version:
                        return version
            
        except Exception as e:
            self._logger.debug(f"获取版本失败: {e}")
        
        return None
    
    async def _get_config_directory(self, install_path: Path) -> Optional[Path]:
        """获取配置目录"""
        possible_config_dirs = [
            install_path / 'Data',
            install_path / 'data',
            install_path / 'Config',
            install_path / 'config'
        ]
        
        for config_dir in possible_config_dirs:
            if config_dir.exists() and config_dir.is_dir():
                return config_dir
        
        return None
    
    def _get_steam_paths_windows(self) -> List[Path]:
        """获取Windows Steam安装路径"""
        steam_paths = []
        
        try:
            # 从注册表获取Steam路径
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
            steam_path = winreg.QueryValueEx(key, "SteamPath")[0]
            steam_paths.append(Path(steam_path))
            winreg.CloseKey(key)
        except Exception:
            pass
        
        # 默认Steam路径
        default_paths = [
            Path('C:/Program Files (x86)/Steam'),
            Path('C:/Program Files/Steam'),
            Path.home() / 'AppData' / 'Roaming' / 'Steam'
        ]
        
        steam_paths.extend([p for p in default_paths if p.exists()])
        return steam_paths
    
    def _get_epic_paths_windows(self) -> List[Path]:
        """获取Windows Epic Games安装路径"""
        epic_paths = []
        
        # Epic Games默认安装位置
        default_epic = Path('C:/Program Files/Epic Games/Path of Building Community PoE2')
        if default_epic.exists():
            epic_paths.append(default_epic)
        
        return epic_paths
    
    def _get_registry_paths_windows(self) -> List[str]:
        """从Windows注册表获取安装路径"""
        paths = []
        
        try:
            import winreg
            
            # 查找Path of Building相关的注册表项
            registry_keys = [
                (winreg.HKEY_CURRENT_USER, r"Software\Path of Building"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Path of Building"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Path of Building")
            ]
            
            for hkey, subkey in registry_keys:
                try:
                    key = winreg.OpenKey(hkey, subkey)
                    install_path = winreg.QueryValueEx(key, "InstallPath")[0]
                    paths.append(install_path)
                    winreg.CloseKey(key)
                except Exception:
                    pass
                    
        except ImportError:
            self._logger.warning("winreg模块不可用，跳过注册表检测")
        except Exception as e:
            self._logger.debug(f"注册表检测失败: {e}")
        
        return paths
    
    def _load_cache(self) -> List[PoB2Installation]:
        """从缓存加载安装信息"""
        try:
            if not self.cache_file.exists():
                return []
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            installations = []
            for item in data.get('installations', []):
                try:
                    installation = PoB2Installation.from_dict(item)
                    installations.append(installation)
                except Exception as e:
                    self._logger.error(f"解析缓存安装信息失败: {e}")
            
            return installations
            
        except Exception as e:
            self._logger.error(f"加载缓存失败: {e}")
            return []
    
    def _save_cache(self, installations: List[PoB2Installation]):
        """保存安装信息到缓存"""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'version': '1.0',
                'platform': self.current_platform.value,
                'last_scan': os.time.time() if hasattr(os, 'time') else 0,
                'installations': [install.to_dict() for install in installations]
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self._logger.debug(f"缓存已保存到: {self.cache_file}")
            
        except Exception as e:
            self._logger.error(f"保存缓存失败: {e}")
    
    async def find_best_installation(self) -> Optional[PoB2Installation]:
        """找到最佳的PoB2安装"""
        installations = await self.detect_installations()
        
        if not installations:
            return None
        
        # 按优先级排序
        def installation_priority(install: PoB2Installation) -> Tuple[int, float]:
            # 安装类型优先级
            type_priority = {
                PoB2InstallType.STEAM: 1,
                PoB2InstallType.STANDALONE: 2,
                PoB2InstallType.EPIC: 3,
                PoB2InstallType.PORTABLE: 4,
                PoB2InstallType.MANUAL: 5,
                PoB2InstallType.UNKNOWN: 6
            }
            
            priority = type_priority.get(install.install_type, 10)
            # 使用修改时间作为次要排序条件（更新的优先）
            mtime = install.last_modified or 0
            
            return (priority, -mtime)
        
        installations.sort(key=installation_priority)
        return installations[0]
    
    async def add_manual_installation(self, path: str) -> Optional[PoB2Installation]:
        """手动添加安装路径"""
        try:
            install_path = Path(path).resolve()
            
            if not install_path.exists():
                self._logger.error(f"路径不存在: {install_path}")
                return None
            
            installation = await self._check_path_for_pob2(install_path, PoB2InstallType.MANUAL)
            
            if not installation:
                self._logger.error(f"在指定路径未找到有效的PoB2安装: {install_path}")
                return None
            
            # 加载现有缓存并添加新安装
            cached_installations = self._load_cache()
            
            # 检查是否已存在
            for existing in cached_installations:
                if existing.path == installation.path:
                    self._logger.info(f"安装路径已存在，更新信息: {installation.path}")
                    cached_installations.remove(existing)
                    break
            
            cached_installations.append(installation)
            self._save_cache(cached_installations)
            
            self._logger.info(f"手动添加PoB2安装: {installation.path}")
            return installation
            
        except Exception as e:
            self._logger.error(f"添加手动安装失败: {e}")
            return None