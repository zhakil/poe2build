#!/usr/bin/env python3
"""
PoB2 GitHub 文件下载器
从 PathOfBuildingCommunity/PathOfBuilding-PoE2 项目下载必要的数据文件
"""

import os
import requests
import json
from pathlib import Path
from typing import List, Dict, Optional
import time

class PoB2GitHubDownloader:
    """PoB2 GitHub文件下载器"""
    
    def __init__(self, cache_dir: str = "data_storage/pob2_cache"):
        self.github_api_base = "https://api.github.com/repos/PathOfBuildingCommunity/PathOfBuilding-PoE2"
        self.github_raw_base = "https://raw.githubusercontent.com/PathOfBuildingCommunity/PathOfBuilding-PoE2"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 使用dev分支(最新开发版本)
        self.branch = "dev"
        
    def get_repository_structure(self) -> Dict:
        """获取仓库结构"""
        try:
            # 获取src目录结构
            response = requests.get(f"{self.github_api_base}/contents/src", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"无法获取仓库结构: {response.status_code}")
                return {}
        except Exception as e:
            print(f"获取仓库结构失败: {e}")
            return {}
    
    def download_file(self, file_path: str, save_path: Optional[str] = None) -> bool:
        """下载单个文件"""
        try:
            url = f"{self.github_raw_base}/{self.branch}/{file_path}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                if save_path is None:
                    # 使用相对路径保存到缓存目录
                    save_path = self.cache_dir / Path(file_path).name
                
                save_path = Path(save_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                
                size_kb = len(response.content) / 1024
                print(f"下载成功: {file_path} -> {save_path} ({size_kb:.1f}KB)")
                return True
            else:
                print(f"下载失败: {file_path} (HTTP {response.status_code})")
                return False
                
        except Exception as e:
            print(f"下载异常: {file_path} - {e}")
            return False
    
    def download_data_directory(self) -> Dict[str, bool]:
        """下载Data目录中的重要文件"""
        data_files = [
            "src/Data/Gems.lua",
            "src/Data/Bases.lua", 
            "src/Data/Global.lua",
            "src/Data/Costs.lua",
            "src/Data/Minions.lua",
            "src/Data/SkillStatMap.lua",
            "src/GameVersions.lua"
        ]
        
        results = {}
        print("下载 PoB2 Data 目录文件:")
        
        for file_path in data_files:
            success = self.download_file(file_path)
            results[file_path] = success
            if success:
                time.sleep(0.5)  # 避免请求过快
                
        return results
    
    def download_tree_data(self) -> Dict[str, bool]:
        """下载天赋树相关数据"""
        # 先获取TreeData目录结构
        try:
            tree_api_url = f"{self.github_api_base}/contents/src/TreeData"
            response = requests.get(tree_api_url, timeout=10)
            
            results = {}
            if response.status_code == 200:
                tree_dirs = response.json()
                print("下载 PoB2 TreeData 文件:")
                
                for tree_dir in tree_dirs:
                    if tree_dir['type'] == 'dir':
                        dir_name = tree_dir['name']
                        # 下载每个目录的内容
                        dir_url = f"{self.github_api_base}/contents/src/TreeData/{dir_name}"
                        dir_response = requests.get(dir_url, timeout=10)
                        
                        if dir_response.status_code == 200:
                            files_in_dir = dir_response.json()
                            for file_info in files_in_dir:
                                if file_info['type'] == 'file':
                                    file_path = f"src/TreeData/{dir_name}/{file_info['name']}"
                                    save_path = self.cache_dir / "TreeData" / dir_name / file_info['name']
                                    success = self.download_file(file_path, save_path)
                                    results[file_path] = success
                                    time.sleep(0.3)
            
            return results
            
        except Exception as e:
            print(f"下载天赋树数据失败: {e}")
            return {}
    
    def create_data_summary(self) -> Dict:
        """创建下载数据的摘要"""
        summary = {
            "download_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "github_branch": self.branch,
            "cache_directory": str(self.cache_dir),
            "files": []
        }
        
        # 扫描缓存目录
        if self.cache_dir.exists():
            for file_path in self.cache_dir.rglob("*"):
                if file_path.is_file():
                    size_kb = file_path.stat().st_size / 1024
                    summary["files"].append({
                        "name": file_path.name,
                        "relative_path": str(file_path.relative_to(self.cache_dir)),
                        "size_kb": round(size_kb, 1)
                    })
        
        # 保存摘要
        summary_file = self.cache_dir / "download_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return summary
    
def main():
    """下载PoB2数据文件"""
    print("=== PoB2 GitHub 数据文件下载器 ===")
    
    downloader = PoB2GitHubDownloader()
    
    # 1. 下载Data目录文件
    data_results = downloader.download_data_directory()
    
    print(f"\nData目录下载结果:")
    success_count = sum(1 for success in data_results.values() if success)
    print(f"成功: {success_count}/{len(data_results)} 个文件")
    
    # 2. 下载TreeData目录
    tree_results = downloader.download_tree_data()
    
    if tree_results:
        print(f"\nTreeData目录下载结果:")
        tree_success = sum(1 for success in tree_results.values() if success)
        print(f"成功: {tree_success}/{len(tree_results)} 个文件")
    
    # 3. 创建摘要
    summary = downloader.create_data_summary()
    
    print(f"\n=== 下载完成 ===")
    print(f"缓存目录: {downloader.cache_dir}")
    print(f"总文件数: {len(summary['files'])}")
    print(f"总大小: {sum(f['size_kb'] for f in summary['files']):.1f}KB")
    
    return summary

if __name__ == "__main__":
    summary = main()