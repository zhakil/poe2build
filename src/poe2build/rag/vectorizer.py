"""构筑数据向量化器 - 使用sentence-transformers生成向量索引"""

import numpy as np
import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    faiss = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from .data_collector import RAGBuildData, PoE2NinjaRAGCollector


@dataclass
class VectorIndex:
    """向量索引数据结构"""
    index: Any  # FAISS索引对象
    build_ids: List[str]  # 构筑ID映射
    embeddings: np.ndarray  # 原始嵌入向量
    metadata: Dict[str, Any]  # 元数据信息
    
    def get_size(self) -> int:
        """获取索引大小"""
        return len(self.build_ids)
    
    def get_dimension(self) -> int:
        """获取向量维度"""
        return self.embeddings.shape[1] if len(self.embeddings) > 0 else 0


@dataclass
class VectorizationStats:
    """向量化统计信息"""
    total_builds: int = 0
    vectorized_builds: int = 0
    failed_builds: int = 0
    vector_dimension: int = 0
    index_size: int = 0
    processing_time: float = 0.0
    created_at: datetime = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_builds': self.total_builds,
            'vectorized_builds': self.vectorized_builds,
            'failed_builds': self.failed_builds,
            'vector_dimension': self.vector_dimension,
            'index_size': self.index_size,
            'processing_time': self.processing_time,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PoE2RAGVectorizer:
    """PoE2构筑数据向量化器"""
    
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2",
                 data_dir: Path = None):
        
        self._logger = logging.getLogger(f"{__name__}.PoE2RAGVectorizer")
        
        # 数据存储
        self.data_dir = data_dir or Path.cwd() / 'data' / 'rag'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 向量数据文件
        self.index_file = self.data_dir / 'vector_index.faiss'
        self.metadata_file = self.data_dir / 'vector_metadata.json'
        self.embeddings_file = self.data_dir / 'embeddings.npy'
        self.build_ids_file = self.data_dir / 'build_ids.json'
        
        # 模型配置
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.vector_dimension = 384  # all-MiniLM-L6-v2默认维度
        
        # 向量索引
        self.vector_index: Optional[VectorIndex] = None
        self._index_loaded = False
        
        # 数据采集器
        self.data_collector = PoE2NinjaRAGCollector(data_dir)
        
        # 检查依赖
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            self._logger.error("sentence-transformers或faiss未安装，将使用Mock模式")
    
    async def initialize(self) -> bool:
        """初始化向量化器"""
        try:
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                self._logger.warning("依赖模块不可用，使用Mock模式")
                return True
            
            # 初始化模型
            self._logger.info(f"初始化sentence-transformers模型: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.vector_dimension = self.model.get_sentence_embedding_dimension()
            
            # 尝试加载现有索引
            if await self._load_existing_index():
                self._logger.info("成功加载现有向量索引")
            else:
                self._logger.info("未找到现有索引，将创建新索引")
            
            return True
            
        except Exception as e:
            self._logger.error(f"初始化向量化器失败: {e}")
            return False
    
    async def build_vector_index(self, force_rebuild: bool = False) -> VectorizationStats:
        """构建向量索引"""
        start_time = datetime.now()
        stats = VectorizationStats(created_at=start_time)
        
        try:
            # 检查是否需要重建
            if not force_rebuild and self._index_loaded and self.vector_index:
                self._logger.info("向量索引已存在，跳过重建")
                stats.vectorized_builds = self.vector_index.get_size()
                stats.vector_dimension = self.vector_index.get_dimension()
                return stats
            
            self._logger.info("开始构建向量索引...")
            
            # 获取构筑数据
            await self.data_collector.collect_all_builds()
            all_builds = self.data_collector.get_all_builds()
            
            if not all_builds:
                self._logger.warning("未找到构筑数据，无法构建索引")
                return stats
            
            stats.total_builds = len(all_builds)
            
            # 生成文本描述和向量
            descriptions = []
            build_ids = []
            valid_builds = []
            
            for rag_data in all_builds:
                try:
                    # 生成增强描述
                    enhanced_desc = self._create_enhanced_description(rag_data)
                    descriptions.append(enhanced_desc)
                    build_ids.append(rag_data.build_id)
                    valid_builds.append(rag_data)
                    
                except Exception as e:
                    self._logger.error(f"处理构筑{rag_data.build_id}失败: {e}")
                    stats.failed_builds += 1
            
            if not descriptions:
                self._logger.error("没有有效的构筑描述，无法构建索引")
                return stats
            
            # 生成嵌入向量
            self._logger.info(f"为{len(descriptions)}个构筑生成嵌入向量...")
            embeddings = await self._generate_embeddings(descriptions)
            
            if embeddings is None:
                self._logger.error("生成嵌入向量失败")
                return stats
            
            # 创建FAISS索引
            vector_index = await self._create_faiss_index(embeddings, build_ids)
            
            if vector_index is None:
                self._logger.error("创建FAISS索引失败")
                return stats
            
            # 添加元数据
            vector_index.metadata = {
                'model_name': self.model_name,
                'vector_dimension': self.vector_dimension,
                'created_at': start_time.isoformat(),
                'total_builds': len(valid_builds),
                'build_data_mapping': {
                    build_id: {
                        'character_class': rag_data.build.character_class.value,
                        'level': rag_data.build.level,
                        'main_skill': rag_data.build.main_skill_gem,
                        'tags': rag_data.tags,
                        'popularity_score': rag_data.popularity_score
                    }
                    for build_id, rag_data in zip(build_ids, valid_builds)
                }
            }
            
            self.vector_index = vector_index
            self._index_loaded = True
            
            # 保存索引
            await self._save_vector_index()
            
            # 更新统计信息
            stats.vectorized_builds = len(build_ids)
            stats.vector_dimension = self.vector_dimension
            stats.index_size = vector_index.get_size()
            stats.processing_time = (datetime.now() - start_time).total_seconds()
            
            self._logger.info(f"向量索引构建完成: {stats.vectorized_builds}个构筑，"
                            f"维度{stats.vector_dimension}，耗时{stats.processing_time:.2f}秒")
            
            return stats
            
        except Exception as e:
            self._logger.error(f"构建向量索引失败: {e}")
            stats.processing_time = (datetime.now() - start_time).total_seconds()
            return stats
    
    def _create_enhanced_description(self, rag_data: RAGBuildData) -> str:
        """创建增强的构筑描述"""
        parts = [rag_data.description]  # 使用基础描述
        
        # 添加标签信息
        if rag_data.tags:
            tag_text = " ".join(rag_data.tags)
            parts.append(f"标签: {tag_text}")
        
        # 添加详细统计信息
        if rag_data.build.stats:
            stats = rag_data.build.stats
            stats_parts = []
            
            if stats.total_dps > 0:
                stats_parts.append(f"总DPS {int(stats.total_dps)}")
            
            if stats.life > 0:
                stats_parts.append(f"生命值 {int(stats.life)}")
            
            if stats.energy_shield > 0:
                stats_parts.append(f"能量护盾 {int(stats.energy_shield)}")
            
            # 抗性信息
            resistances = [
                f"火抗{stats.fire_resistance}%",
                f"冰抗{stats.cold_resistance}%", 
                f"雷抗{stats.lightning_resistance}%",
                f"混沌抗{stats.chaos_resistance}%"
            ]
            stats_parts.extend(resistances)
            
            if stats_parts:
                parts.append("属性: " + " ".join(stats_parts))
        
        # 添加物品信息
        if rag_data.build.key_items:
            items_text = " ".join(rag_data.build.key_items[:3])  # 最多3个关键物品
            parts.append(f"关键物品: {items_text}")
        
        # 添加天赋信息
        if rag_data.build.passive_keystones:
            keystones_text = " ".join(rag_data.build.passive_keystones[:3])
            parts.append(f"关键天赋: {keystones_text}")
        
        return " | ".join(parts)
    
    async def _generate_embeddings(self, descriptions: List[str]) -> Optional[np.ndarray]:
        """生成嵌入向量"""
        try:
            if not SENTENCE_TRANSFORMERS_AVAILABLE or not self.model:
                # Mock模式：生成随机向量
                return np.random.rand(len(descriptions), self.vector_dimension).astype(np.float32)
            
            # 使用sentence-transformers生成向量
            embeddings = self.model.encode(descriptions, convert_to_numpy=True)
            return embeddings.astype(np.float32)
            
        except Exception as e:
            self._logger.error(f"生成嵌入向量失败: {e}")
            return None
    
    async def _create_faiss_index(self, embeddings: np.ndarray, build_ids: List[str]) -> Optional[VectorIndex]:
        """创建FAISS索引"""
        try:
            if not SENTENCE_TRANSFORMERS_AVAILABLE or faiss is None:
                # Mock模式：创建简单索引
                return VectorIndex(
                    index=None,  # Mock索引
                    build_ids=build_ids,
                    embeddings=embeddings,
                    metadata={}
                )
            
            # 创建FAISS索引 (使用内积索引)
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatIP(dimension)
            
            # 归一化向量以便使用余弦相似度
            faiss.normalize_L2(embeddings)
            
            # 添加向量到索引
            index.add(embeddings)
            
            return VectorIndex(
                index=index,
                build_ids=build_ids,
                embeddings=embeddings,
                metadata={}
            )
            
        except Exception as e:
            self._logger.error(f"创建FAISS索引失败: {e}")
            return None
    
    async def _save_vector_index(self):
        """保存向量索引到文件"""
        try:
            if not self.vector_index:
                return
            
            # 保存FAISS索引
            if SENTENCE_TRANSFORMERS_AVAILABLE and self.vector_index.index is not None:
                faiss.write_index(self.vector_index.index, str(self.index_file))
            
            # 保存嵌入向量
            np.save(self.embeddings_file, self.vector_index.embeddings)
            
            # 保存构筑ID映射
            with open(self.build_ids_file, 'w', encoding='utf-8') as f:
                json.dump(self.vector_index.build_ids, f, indent=2)
            
            # 保存元数据
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.vector_index.metadata, f, indent=2, ensure_ascii=False)
            
            self._logger.info("向量索引已保存到磁盘")
            
        except Exception as e:
            self._logger.error(f"保存向量索引失败: {e}")
    
    async def _load_existing_index(self) -> bool:
        """加载现有的向量索引"""
        try:
            # 检查必要文件是否存在
            if not all(f.exists() for f in [
                self.embeddings_file, self.build_ids_file, self.metadata_file
            ]):
                return False
            
            # 加载嵌入向量
            embeddings = np.load(self.embeddings_file)
            
            # 加载构筑ID映射
            with open(self.build_ids_file, 'r', encoding='utf-8') as f:
                build_ids = json.load(f)
            
            # 加载元数据
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # 加载FAISS索引
            index = None
            if SENTENCE_TRANSFORMERS_AVAILABLE and self.index_file.exists():
                try:
                    index = faiss.read_index(str(self.index_file))
                except Exception as e:
                    self._logger.warning(f"加载FAISS索引失败，将重新创建: {e}")
                    index = await self._recreate_faiss_index(embeddings)
            
            self.vector_index = VectorIndex(
                index=index,
                build_ids=build_ids,
                embeddings=embeddings,
                metadata=metadata
            )
            
            self._index_loaded = True
            return True
            
        except Exception as e:
            self._logger.error(f"加载现有索引失败: {e}")
            return False
    
    async def _recreate_faiss_index(self, embeddings: np.ndarray):
        """重新创建FAISS索引"""
        try:
            if not SENTENCE_TRANSFORMERS_AVAILABLE or faiss is None:
                return None
            
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatIP(dimension)
            
            # 归一化并添加向量
            normalized_embeddings = embeddings.copy()
            faiss.normalize_L2(normalized_embeddings)
            index.add(normalized_embeddings)
            
            return index
        except Exception as e:
            self._logger.error(f"重新创建FAISS索引失败: {e}")
            return None
    
    async def add_builds_to_index(self, new_builds: List[RAGBuildData]) -> int:
        """向现有索引添加新构筑"""
        try:
            if not self.vector_index or not new_builds:
                return 0
            
            # 生成新构筑的描述和向量
            descriptions = []
            build_ids = []
            
            for rag_data in new_builds:
                # 检查是否已存在
                if rag_data.build_id not in self.vector_index.build_ids:
                    enhanced_desc = self._create_enhanced_description(rag_data)
                    descriptions.append(enhanced_desc)
                    build_ids.append(rag_data.build_id)
            
            if not descriptions:
                return 0
            
            # 生成新向量
            new_embeddings = await self._generate_embeddings(descriptions)
            if new_embeddings is None:
                return 0
            
            # 添加到现有索引
            if SENTENCE_TRANSFORMERS_AVAILABLE and self.vector_index.index is not None:
                faiss.normalize_L2(new_embeddings)
                self.vector_index.index.add(new_embeddings)
            
            # 更新数据结构
            self.vector_index.build_ids.extend(build_ids)
            self.vector_index.embeddings = np.vstack([
                self.vector_index.embeddings, new_embeddings
            ])
            
            # 保存更新后的索引
            await self._save_vector_index()
            
            self._logger.info(f"向索引添加了{len(build_ids)}个新构筑")
            return len(build_ids)
            
        except Exception as e:
            self._logger.error(f"添加构筑到索引失败: {e}")
            return 0
    
    def get_vector_stats(self) -> Dict[str, Any]:
        """获取向量化统计信息"""
        stats = {
            'index_loaded': self._index_loaded,
            'model_name': self.model_name,
            'vector_dimension': self.vector_dimension,
            'data_dir': str(self.data_dir)
        }
        
        if self.vector_index:
            stats.update({
                'total_vectors': self.vector_index.get_size(),
                'vector_dimension': self.vector_index.get_dimension(),
                'index_metadata': self.vector_index.metadata
            })
        
        return stats
    
    def get_build_vector(self, build_id: str) -> Optional[np.ndarray]:
        """获取指定构筑的向量"""
        try:
            if not self.vector_index or build_id not in self.vector_index.build_ids:
                return None
            
            index = self.vector_index.build_ids.index(build_id)
            return self.vector_index.embeddings[index]
            
        except Exception as e:
            self._logger.error(f"获取构筑向量失败: {e}")
            return None
    
    async def cleanup(self):
        """清理资源"""
        try:
            if hasattr(self, 'model') and self.model:
                # sentence-transformers模型通常不需要显式清理
                self.model = None
            
            self.vector_index = None
            self._index_loaded = False
            
            self._logger.info("向量化器资源已清理")
        except Exception as e:
            self._logger.error(f"清理向量化器资源失败: {e}")


# 便捷函数
async def create_vector_index(data_dir: Path = None, 
                            model_name: str = "all-MiniLM-L6-v2", 
                            force_rebuild: bool = False) -> VectorizationStats:
    """创建向量索引的便捷函数"""
    vectorizer = PoE2RAGVectorizer(model_name, data_dir)
    if await vectorizer.initialize():
        return await vectorizer.build_vector_index(force_rebuild)
    else:
        raise RuntimeError("向量化器初始化失败")