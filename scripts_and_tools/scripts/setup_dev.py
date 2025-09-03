#!/usr/bin/env python3
"""开发环境自动化设置脚本"""
import os
import sys
import subprocess
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """执行命令并显示进度"""
    print(f"\n📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} 完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败: {e.stderr}")
        return False


def setup_development_environment():
    """设置开发环境"""
    print("🚀 PoE2 Build Generator - 开发环境设置")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        sys.exit(1)
    
    print(f"✅ Python版本: {sys.version}")
    
    # 检查是否已在项目根目录
    if not Path("pyproject.toml").exists():
        print("❌ 请在项目根目录运行此脚本")
        sys.exit(1)
    
    # 创建虚拟环境
    if not Path("venv").exists():
        if not run_command("python -m venv venv", "创建虚拟环境"):
            return False
    else:
        print("📦 虚拟环境已存在")
    
    # 激活虚拟环境并安装依赖
    if os.name == 'nt':  # Windows
        pip_path = "venv\\Scripts\\pip"
        python_path = "venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        pip_path = "venv/bin/pip"
        python_path = "venv/bin/python"
    
    if not run_command(f"{pip_path} install --upgrade pip", "升级pip"):
        return False
        
    if not run_command(f"{pip_path} install -r requirements.txt", "安装生产依赖"):
        return False
        
    if not run_command(f"{pip_path} install pytest pytest-asyncio pytest-cov black flake8 mypy pre-commit", "安装开发依赖"):
        return False
    
    # 安装pre-commit钩子
    if not run_command(f"{python_path} -m pre_commit install", "设置Git钩子"):
        print("⚠️  pre-commit设置失败，可能需要手动设置")
    
    # 创建必要的目录
    directories = [
        "data/cache",
        "data/rag", 
        "data/static",
        "data/samples",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 创建目录: {directory}")
    
    # 复制配置文件模板
    if not Path(".env").exists() and Path(".env.example").exists():
        import shutil
        shutil.copy(".env.example", ".env")
        print("📝 创建 .env 配置文件")
    
    print("\n🎉 开发环境设置完成!")
    print("\n📋 接下来的步骤:")
    if os.name == 'nt':
        print("   1. 激活虚拟环境: venv\\Scripts\\activate")
    else:
        print("   1. 激活虚拟环境: source venv/bin/activate")
    print("   2. 运行测试: python -m pytest tests/")
    print("   3. 启动应用: python poe2_ai_orchestrator.py")
    
    return True


if __name__ == "__main__":
    success = setup_development_environment()
    sys.exit(0 if success else 1)