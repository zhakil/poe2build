"""
向量索引构建器 - FAISS向量数据库管理

负责构建和管理FAISS向量索引，支持高效的相似性搜索。
提供增量更新、索引持久化和优化功能。
"""

import os
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
from dataclasses import dataclass, asdict

import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    FAISS_AVAILABLE = False

def check_faiss_dependency():
    """检查FAISS依赖"""
    if not FAISS_AVAILABLE:
        raise ImportError("FAISS依赖缺失: pip install faiss-cpu")

from .models import PoE2BuildData, RAGDataModel
from .vectorizer import PoE2BuildVectorizer, VectorConfig

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class IndexConfig:
    """索引配置"""
    index_type: str = "IndexFlatIP"          # FAISS索引类型
    similarity_metric: str = "cosine"        # 相似度度量: "cosine", "l2", "dot"
    vector_dimension: int = 384              # 向量维度
    nprobe: int = 10                        # 搜索时的探针数量
    use_gpu: bool = False                   # 是否使用GPU (需要faiss-gpu)
    index_path: str = "data/indexes"        # 索引存储路径
    auto_save: bool = True                  # 是否自动保存
    
    # 索引优化配置
    clustering_nlist: int = 1024            # 聚类数量 (用于IVF索引)
    pq_m: int = 64                         # PQ压缩的子向量数量
    use_opq: bool = True                   # 是否使用OPQ预处理

class PoE2BuildIndexBuilder:
    """PoE2构筑向量索引构建器
    
    基于FAISS构建高效的向量索引，支持大规模构筑数据的快速相似性搜索。
    """
    
    def __init__(self, config: Optional[IndexConfig] = None):
        """初始化索引构建器
        
        Args:
            config: 索引配置，如果为None则使用默认配置
        """
        self.config = config or IndexConfig()
        self.vectorizer = None
        self.index = None
        self.build_metadata = {}  # build_hash -> metadata mapping
        self._setup_directories()
        
    def _setup_directories(self):
        """创建必要的目录"""
        index_dir = Path(self.config.index_path)
        index_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (index_dir / "indexes").mkdir(exist_ok=True)
        (index_dir / "metadata").mkdir(exist_ok=True)
        (index_dir / "backups").mkdir(exist_ok=True)
    
    def set_vectorizer(self, vectorizer: PoE2BuildVectorizer):
        """设置向量化引擎"""
        self.vectorizer = vectorizer
        # 同步向量维度
        self.config.vector_dimension = vectorizer.config.vector_dimension
        
    def _create_index(self, num_vectors: int):
        """创建FAISS索引
        
        Args:
            num_vectors: 向量数量，用于选择合适的索引类型
            
        Returns:
            创建的FAISS索引
        """
        check_faiss_dependency()
        d = self.config.vector_dimension
        
        if num_vectors < 1000:
            # 小数据集使用暴力搜索
            if self.config.similarity_metric == "cosine":
                index = faiss.IndexFlatIP(d)
            else:
                index = faiss.IndexFlatL2(d)
            logger.info(f"创建Flat索引 (向量数: {num_vectors})")
            
        elif num_vectors < 50000:
            # 中等数据集使用IVF
            nlist = min(self.config.clustering_nlist, num_vectors // 10)
            
            if self.config.similarity_metric == "cosine":
                quantizer = faiss.IndexFlatIP(d)
                index = faiss.IndexIVFFlat(quantizer, d, nlist)
            else:
                quantizer = faiss.IndexFlatL2(d)
                index = faiss.IndexIVFFlat(quantizer, d, nlist)
            
            index.nprobe = self.config.nprobe
            logger.info(f"创建IVF索引 (向量数: {num_vectors}, nlist: {nlist})")
            
        else:
            # 大数据集使用IVF + PQ压缩
            nlist = min(self.config.clustering_nlist, num_vectors // 20)
            m = min(self.config.pq_m, d // 4)
            
            quantizer = faiss.IndexFlatL2(d)
            index = faiss.IndexIVFPQ(quantizer, d, nlist, m, 8)
            index.nprobe = self.config.nprobe
            
            logger.info(f"创建IVF+PQ索引 (向量数: {num_vectors}, nlist: {nlist}, m: {m})")
            
            # 可选的OPQ预处理
            if self.config.use_opq:
                opq = faiss.OPQMatrix(d, m)
                index = faiss.IndexPreTransform(opq, index)
                logger.info("启用OPQ预处理")
        
        # GPU支持 (需要faiss-gpu)
        if self.config.use_gpu:
            try:
                index = faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, index)
                logger.info("索引已移至GPU")
            except Exception as e:
                logger.warning(f"无法使用GPU，继续使用CPU: {e}")
        
        return index
    
    def build_index(self, builds: List[PoE2BuildData], 
                   vectorizer: Optional[PoE2BuildVectorizer] = None,
                   show_progress: bool = True) -> Dict[str, Any]:
        """构建向量索引
        
        Args:
            builds: 构筑数据列表
            vectorizer: 向量化引擎，如果为None则使用已设置的引擎
            show_progress: 是否显示进度
            
        Returns:
            索引构建统计信息
        """
        if not builds:
            raise ValueError("构筑数据列表不能为空")
        
        if vectorizer:
            self.set_vectorizer(vectorizer)
        elif not self.vectorizer:
            # 使用默认向量化引擎
            from .vectorizer import create_vectorizer
            self.set_vectorizer(create_vectorizer())
        
        logger.info(f"开始构建索引，构筑数量: {len(builds)}")
        start_time = datetime.now()
        
        # 1. 向量化构筑数据
        logger.info("正在向量化构筑数据...")
        vectors = self.vectorizer.vectorize_builds(builds, show_progress=show_progress)
        
        # 2. 创建索引
        logger.info("创建FAISS索引...")
        self.index = self._create_index(len(builds))
        
        # 3. 预处理向量 (如果使用余弦相似度)
        processed_vectors = vectors.copy()
        if self.config.similarity_metric == "cosine":
            # 标准化向量用于内积计算余弦相似度
            norms = np.linalg.norm(processed_vectors, axis=1, keepdims=True)
            processed_vectors = processed_vectors / np.maximum(norms, 1e-8)
        
        # 4. 训练索引 (如果需要)
        if hasattr(self.index, 'train') and not self.index.is_trained:
            logger.info("训练索引...")
            self.index.train(processed_vectors)
        
        # 5. 添加向量到索引
        logger.info("添加向量到索引...")
        self.index.add(processed_vectors)
        
        # 6. 构建元数据映射
        self.build_metadata = {}
        for i, build in enumerate(builds):
            self.build_metadata[i] = {
                'build_hash': build.similarity_hash,
                'character_class': build.character_class,
                'ascendancy': build.ascendancy,
                'main_skill': build.main_skill_setup.main_skill,
                'level': build.level,
                'total_cost': build.total_cost,
                'build_goal': build.build_goal.value,
                'data_quality': build.data_quality.value,
                'popularity_rank': build.popularity_rank,
                'index_position': i
            }
        
        # 7. 自动保存
        if self.config.auto_save:
            self.save_index()
        
        # 8. 计算统计信息
        build_time = (datetime.now() - start_time).total_seconds()
        
        stats = {
            'total_builds': len(builds),
            'vector_dimension': self.config.vector_dimension,
            'index_type': type(self.index).__name__,
            'build_time_seconds': build_time,
            'memory_usage_mb': self._estimate_memory_usage(),
            'similarity_metric': self.config.similarity_metric,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"索引构建完成: {stats}")
        return stats
    
    def add_builds(self, new_builds: List[PoE2BuildData], 
                  rebuild_threshold: float = 0.3) -> Dict[str, Any]:
        """增量添加构筑到现有索引
        
        Args:
            new_builds: 新的构筑数据列表
            rebuild_threshold: 重建阈值，当新增数据超过现有数据的此比例时重建索引
            
        Returns:
            添加操作统计信息
        """
        if not self.index:
            logger.warning("索引不存在，将使用新构筑创建索引")
            return self.build_index(new_builds)
        
        if not new_builds:
            return {'added_builds': 0, 'action': 'no_new_builds'}
        
        current_size = self.index.ntotal
        new_size = len(new_builds)
        
        # 检查是否需要重建
        if new_size / (current_size + new_size) > rebuild_threshold:
            logger.info(f"新增数据比例 {new_size/(current_size + new_size):.2%} 超过阈值，重建索引")
            # 需要获取原有构筑数据，这里简化处理
            return {'action': 'rebuild_required', 'current_size': current_size, 'new_size': new_size}
        
        logger.info(f"增量添加 {new_size} 个构筑到现有索引...")
        
        # 向量化新构筑
        new_vectors = self.vectorizer.vectorize_builds(new_builds)
        
        # 预处理向量
        if self.config.similarity_metric == "cosine":
            norms = np.linalg.norm(new_vectors, axis=1, keepdims=True)
            new_vectors = new_vectors / np.maximum(norms, 1e-8)
        
        # 添加到索引
        start_idx = current_size
        self.index.add(new_vectors)
        
        # 更新元数据
        for i, build in enumerate(new_builds):
            idx = start_idx + i
            self.build_metadata[idx] = {
                'build_hash': build.similarity_hash,
                'character_class': build.character_class,
                'ascendancy': build.ascendancy,
                'main_skill': build.main_skill_setup.main_skill,
                'level': build.level,
                'total_cost': build.total_cost,
                'build_goal': build.build_goal.value,
                'data_quality': build.data_quality.value,
                'popularity_rank': build.popularity_rank,
                'index_position': idx
            }
        
        if self.config.auto_save:
            self.save_index()
        
        stats = {
            'added_builds': new_size,
            'total_builds': self.index.ntotal,
            'action': 'incremental_add',
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"增量添加完成: {stats}")
        return stats
    
    def save_index(self, custom_path: Optional[str] = None) -> str:
        """保存索引到文件
        
        Args:
            custom_path: 自定义保存路径，如果为None则使用默认路径
            
        Returns:
            保存的文件路径
        """
        if not self.index:
            raise ValueError("索引不存在，无法保存")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if custom_path:
            save_dir = Path(custom_path)
        else:
            save_dir = Path(self.config.index_path) / "indexes"
        
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存索引文件
        index_file = save_dir / f"poe2_build_index_{timestamp}.faiss"
        
        # 将GPU索引转回CPU以便保存
        index_to_save = self.index
        if hasattr(self.index, 'device') and self.index.device >= 0:
            index_to_save = faiss.index_gpu_to_cpu(self.index)
        
        faiss.write_index(index_to_save, str(index_file))
        
        # 保存元数据
        metadata_file = save_dir / f"poe2_build_metadata_{timestamp}.json"
        metadata = {
            'build_metadata': self.build_metadata,
            'config': asdict(self.config),
            'index_info': {
                'type': type(self.index).__name__,
                'total_vectors': self.index.ntotal,
                'vector_dimension': self.config.vector_dimension,
                'save_timestamp': datetime.now().isoformat()
            }
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # 创建最新索引的符号链接
        latest_index = save_dir / "latest_index.faiss"
        latest_metadata = save_dir / "latest_metadata.json"
        
        try:
            if latest_index.exists():
                latest_index.unlink()
            if latest_metadata.exists():
                latest_metadata.unlink()
            
            latest_index.symlink_to(index_file.name)
            latest_metadata.symlink_to(metadata_file.name)
        except OSError:
            # Windows可能不支持符号链接，直接复制文件
            import shutil
            shutil.copy2(index_file, latest_index)
            shutil.copy2(metadata_file, latest_metadata)
        
        logger.info(f"索引已保存: {index_file}")
        logger.info(f"元数据已保存: {metadata_file}")
        
        return str(index_file)
    
    def load_index(self, index_path: Optional[str] = None, 
                  metadata_path: Optional[str] = None) -> Dict[str, Any]:
        """从文件加载索引
        
        Args:
            index_path: 索引文件路径，如果为None则使用最新索引
            metadata_path: 元数据文件路径，如果为None则自动推断
            
        Returns:
            加载的索引信息
        """
        if index_path is None:
            # 使用最新索引
            index_path = Path(self.config.index_path) / "indexes" / "latest_index.faiss"
            if not index_path.exists():
                raise FileNotFoundError(f"未找到索引文件: {index_path}")
        
        if metadata_path is None:
            # 自动推断元数据路径
            index_path = Path(index_path)
            metadata_path = index_path.parent / "latest_metadata.json"
            if not metadata_path.exists():
                # 尝试基于索引文件名推断
                metadata_name = index_path.stem.replace("index", "metadata") + ".json"
                metadata_path = index_path.parent / metadata_name
        
        logger.info(f"加载索引: {index_path}")
        
        # 加载索引
        self.index = faiss.read_index(str(index_path))
        
        # 移动到GPU (如果配置启用)
        if self.config.use_gpu:
            try:
                self.index = faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, self.index)
                logger.info("索引已移至GPU")
            except Exception as e:
                logger.warning(f"无法使用GPU: {e}")
        
        # 加载元数据
        if metadata_path and Path(metadata_path).exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            self.build_metadata = metadata['build_metadata']
            # 转换字符串键为整数
            self.build_metadata = {int(k): v for k, v in self.build_metadata.items()}
            
            config_data = metadata.get('config', {})
            # 更新配置
            for key, value in config_data.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            index_info = metadata.get('index_info', {})
        else:
            logger.warning(f"元数据文件不存在: {metadata_path}")
            index_info = {}
        
        info = {
            'index_path': str(index_path),
            'metadata_path': str(metadata_path) if metadata_path else None,
            'total_vectors': self.index.ntotal,
            'vector_dimension': self.index.d,
            'index_type': type(self.index).__name__,
            'metadata_count': len(self.build_metadata),
            'load_timestamp': datetime.now().isoformat()
        }
        info.update(index_info)
        
        logger.info(f"索引加载完成: {info}")
        return info
    
    def _estimate_memory_usage(self) -> float:
        """估算索引内存使用量 (MB)"""
        if not self.index:
            return 0.0
        
        # 基础估算: 每个向量使用float32 (4字节) * 维度
        vector_memory = self.index.ntotal * self.config.vector_dimension * 4 / (1024 * 1024)
        
        # 索引结构开销 (粗略估算)
        overhead = vector_memory * 0.2
        
        return vector_memory + overhead
    
    def get_index_stats(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        if not self.index:
            return {'status': 'no_index'}
        
        stats = {
            'total_vectors': self.index.ntotal,
            'vector_dimension': self.index.d,
            'index_type': type(self.index).__name__,
            'is_trained': getattr(self.index, 'is_trained', True),
            'memory_usage_mb': self._estimate_memory_usage(),
            'metadata_count': len(self.build_metadata),
            'similarity_metric': self.config.similarity_metric
        }
        
        # IVF索引特定信息
        if hasattr(self.index, 'nlist'):
            stats['nlist'] = self.index.nlist
            stats['nprobe'] = self.index.nprobe
        
        return stats
    
    def optimize_index(self) -> Dict[str, Any]:
        """优化索引性能"""
        if not self.index:
            raise ValueError("索引不存在，无法优化")
        
        logger.info("开始优化索引...")
        
        optimization_info = {
            'original_memory_mb': self._estimate_memory_usage(),
            'optimizations_applied': []
        }
        
        # 对于IVF索引，调整nprobe参数
        if hasattr(self.index, 'nprobe'):
            original_nprobe = self.index.nprobe
            # 基于数据规模动态调整
            optimal_nprobe = min(32, max(1, self.index.ntotal // 1000))
            self.index.nprobe = optimal_nprobe
            
            if optimal_nprobe != original_nprobe:
                optimization_info['optimizations_applied'].append(
                    f"调整nprobe: {original_nprobe} -> {optimal_nprobe}"
                )
        
        # 记录最终内存使用
        optimization_info['final_memory_mb'] = self._estimate_memory_usage()
        optimization_info['memory_saved_mb'] = (
            optimization_info['original_memory_mb'] - 
            optimization_info['final_memory_mb']
        )
        
        logger.info(f"索引优化完成: {optimization_info}")
        return optimization_info
    
    def create_backup(self) -> str:
        """创建索引备份"""
        if not self.index:
            raise ValueError("索引不存在，无法备份")
        
        backup_dir = Path(self.config.index_path) / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"backup_{timestamp}"
        backup_path.mkdir(exist_ok=True)
        
        # 保存索引和元数据
        index_file = backup_path / "index.faiss"
        metadata_file = backup_path / "metadata.json"
        
        # 保存索引
        index_to_save = self.index
        if hasattr(self.index, 'device') and self.index.device >= 0:
            index_to_save = faiss.index_gpu_to_cpu(self.index)
        
        faiss.write_index(index_to_save, str(index_file))
        
        # 保存元数据
        metadata = {
            'build_metadata': self.build_metadata,
            'config': asdict(self.config),
            'backup_info': {
                'timestamp': datetime.now().isoformat(),
                'total_vectors': self.index.ntotal,
                'vector_dimension': self.index.d
            }
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"索引备份已创建: {backup_path}")
        return str(backup_path)

# 工厂函数
def create_index_builder(similarity_metric: str = "cosine",
                        index_path: str = "data/indexes",
                        use_gpu: bool = False) -> PoE2BuildIndexBuilder:
    """创建索引构建器的工厂函数
    
    Args:
        similarity_metric: 相似度度量方式
        index_path: 索引存储路径
        use_gpu: 是否使用GPU
        
    Returns:
        配置好的索引构建器实例
    """
    config = IndexConfig(
        similarity_metric=similarity_metric,
        index_path=index_path,
        use_gpu=use_gpu
    )
    return PoE2BuildIndexBuilder(config)

# 测试函数
def test_index_building():
    """测试索引构建功能"""
    from .models import PoE2BuildData, SkillGemSetup, BuildGoal
    from .vectorizer import create_vectorizer
    
    # 创建测试数据
    test_builds = []
    for i in range(100):
        build = PoE2BuildData(
            character_class=["Ranger", "Witch", "Marauder"][i % 3],
            ascendancy=["Deadeye", "Elementalist", "Juggernaut"][i % 3],
            level=80 + i % 20,
            main_skill_setup=SkillGemSetup(
                main_skill=["Lightning Arrow", "Fireball", "Cyclone"][i % 3],
                support_gems=["Added Lightning", "Elemental Damage"]
            ),
            build_goal=[BuildGoal.CLEAR_SPEED, BuildGoal.BOSS_KILLING, BuildGoal.BALANCED][i % 3],
            total_cost=float(i % 50)
        )
        test_builds.append(build)
    
    # 创建向量化引擎和索引构建器
    vectorizer = create_vectorizer()
    index_builder = create_index_builder()
    index_builder.set_vectorizer(vectorizer)
    
    # 构建索引
    print("构建索引...")
    stats = index_builder.build_index(test_builds)
    print(f"索引构建统计: {stats}")
    
    # 获取索引信息
    index_stats = index_builder.get_index_stats()
    print(f"索引统计: {index_stats}")
    
    # 优化索引
    optimization_info = index_builder.optimize_index()
    print(f"优化信息: {optimization_info}")
    
    return index_builder, test_builds

if __name__ == "__main__":
    # 运行测试
    index_builder, test_builds = test_index_building()
    print("索引构建器测试完成!")