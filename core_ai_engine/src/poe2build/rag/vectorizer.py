"""
RAG向量化引擎 - PoE2构筑数据向量化

这个模块负责将PoE2构筑数据转换为向量表示，用于语义相似性搜索。
使用sentence-transformers进行文本嵌入，支持多维度特征向量化。
"""

import os
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

# 可选依赖导入
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    FAISS_AVAILABLE = False

# 依赖检查函数
def check_dependencies():
    """检查向量化依赖是否可用"""
    missing = []
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        missing.append("sentence-transformers")
    if not FAISS_AVAILABLE:
        missing.append("faiss-cpu")
    
    if missing:
        raise ImportError(f"向量化依赖缺失: {', '.join(missing)}. 请运行 pip install {' '.join(missing)}")

from .models import PoE2BuildData, RAGDataModel, DataQuality

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class VectorConfig:
    """向量化配置"""
    model_name: str = "all-MiniLM-L6-v2"         # Sentence-BERT模型
    vector_dimension: int = 384                   # 向量维度
    max_sequence_length: int = 512               # 最大序列长度
    batch_size: int = 32                         # 批处理大小
    use_normalize: bool = True                   # 是否标准化向量
    cache_dir: str = "data/models"               # 模型缓存目录
    
class PoE2BuildVectorizer:
    """PoE2构筑向量化引擎
    
    负责将PoE2构筑数据转换为可用于相似性搜索的向量表示。
    支持多种文本特征的组合和权重调整。
    """
    
    def __init__(self, config: Optional[VectorConfig] = None):
        """初始化向量化引擎
        
        Args:
            config: 向量化配置，如果为None则使用默认配置
        """
        self.config = config or VectorConfig()
        self.model = None
        self._model_loaded = False
        self._setup_directories()
        
        # 特征权重配置
        self.feature_weights = {
            'class_skill': 0.4,      # 职业+技能特征
            'equipment': 0.2,        # 装备特征
            'keystones': 0.15,       # 关键天赋特征
            'stats': 0.15,           # 属性特征  
            'goal_budget': 0.1       # 目标+预算特征
        }
        
        # 缓存
        self._text_cache = {}        # 文本生成缓存
        self._vector_cache = {}      # 向量缓存
        
    def _setup_directories(self):
        """创建必要的目录"""
        cache_dir = Path(self.config.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (cache_dir / "sentence_transformers").mkdir(exist_ok=True)
        (cache_dir / "vectors").mkdir(exist_ok=True)
        
    def _load_model(self):
        """延迟加载sentence-transformers模型"""
        if self._model_loaded:
            return
        
        # 检查依赖
        check_dependencies()
            
        logger.info(f"加载Sentence-Transformer模型: {self.config.model_name}")
        try:
            # 设置缓存目录
            os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(Path(self.config.cache_dir) / "sentence_transformers")
            
            self.model = SentenceTransformer(
                self.config.model_name,
                cache_folder=os.environ['SENTENCE_TRANSFORMERS_HOME']
            )
            
            # 验证模型维度
            test_vector = self.model.encode(["test"])
            actual_dim = test_vector.shape[1]
            if actual_dim != self.config.vector_dimension:
                logger.warning(f"模型维度 {actual_dim} 与配置 {self.config.vector_dimension} 不匹配，更新配置")
                self.config.vector_dimension = actual_dim
            
            self._model_loaded = True
            logger.info(f"模型加载成功，向量维度: {self.config.vector_dimension}")
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise RuntimeError(f"无法加载Sentence-Transformer模型: {e}")
    
    def generate_build_text(self, build: PoE2BuildData, feature_type: str = "comprehensive") -> str:
        """生成构筑的文本描述用于向量化
        
        Args:
            build: PoE2构筑数据
            feature_type: 特征类型 - "comprehensive", "class_skill", "equipment", etc.
            
        Returns:
            用于向量化的文本描述
        """
        # 检查缓存
        cache_key = f"{build.similarity_hash}_{feature_type}"
        if cache_key in self._text_cache:
            return self._text_cache[cache_key]
        
        if feature_type == "comprehensive":
            text = self._generate_comprehensive_text(build)
        elif feature_type == "class_skill":
            text = self._generate_class_skill_text(build)
        elif feature_type == "equipment":
            text = self._generate_equipment_text(build)
        elif feature_type == "keystones":
            text = self._generate_keystones_text(build)
        elif feature_type == "stats":
            text = self._generate_stats_text(build)
        elif feature_type == "goal_budget":
            text = self._generate_goal_budget_text(build)
        else:
            text = build.build_description or self._generate_comprehensive_text(build)
        
        # 缓存结果
        self._text_cache[cache_key] = text
        return text
    
    def _generate_comprehensive_text(self, build: PoE2BuildData) -> str:
        """生成综合文本描述"""
        parts = []
        
        # 职业和升华
        if build.character_class:
            class_desc = build.character_class
            if build.ascendancy:
                class_desc += f" {build.ascendancy}"
            parts.append(class_desc)
        
        # 主技能和辅助
        if build.main_skill_setup.main_skill:
            skill_desc = build.main_skill_setup.main_skill
            if build.main_skill_setup.support_gems:
                support_gems = " ".join(build.main_skill_setup.support_gems[:4])
                skill_desc += f" with {support_gems} support"
            parts.append(skill_desc)
        
        # 关键装备
        equipment_parts = []
        if build.weapon and build.weapon.name:
            equipment_parts.append(f"weapon {build.weapon.name}")
        if build.body_armour and build.body_armour.name:
            equipment_parts.append(f"armor {build.body_armour.name}")
        if equipment_parts:
            parts.append(" ".join(equipment_parts))
        
        # 关键天赋
        if build.passive_keystones:
            keystones = " ".join(build.passive_keystones[:3])
            parts.append(f"keystones {keystones}")
        
        # 构筑目标和预算
        goal_desc = f"goal {build.build_goal.value}"
        if build.total_cost > 0:
            goal_desc += f" budget {build.total_cost:.1f} {build.currency_type}"
        parts.append(goal_desc)
        
        # 关键属性
        if build.offensive_stats.dps > 0:
            dps_tier = "high" if build.offensive_stats.dps > 2000000 else "medium" if build.offensive_stats.dps > 500000 else "low"
            parts.append(f"{dps_tier} damage")
        
        ehp = build.defensive_stats.effective_health_pool()
        if ehp > 0:
            defense_tier = "high" if ehp > 8000 else "medium" if ehp > 5000 else "low"
            parts.append(f"{defense_tier} defense")
        
        return " ".join(parts)
    
    def _generate_class_skill_text(self, build: PoE2BuildData) -> str:
        """生成职业技能特征文本"""
        parts = []
        
        if build.character_class:
            parts.append(build.character_class)
        if build.ascendancy:
            parts.append(build.ascendancy)
        if build.main_skill_setup.main_skill:
            parts.append(build.main_skill_setup.main_skill)
            parts.extend(build.main_skill_setup.support_gems[:3])
        
        return " ".join(parts)
    
    def _generate_equipment_text(self, build: PoE2BuildData) -> str:
        """生成装备特征文本"""
        parts = []
        
        equipment_slots = [
            build.weapon, build.offhand, build.helmet, 
            build.body_armour, build.gloves, build.boots,
            build.belt, build.amulet
        ]
        
        for item in equipment_slots:
            if item and item.name:
                parts.append(f"{item.type} {item.name}")
        
        # 戒指单独处理
        for i, ring in enumerate(build.rings[:2]):
            if ring and ring.name:
                parts.append(f"ring {ring.name}")
        
        return " ".join(parts)
    
    def _generate_keystones_text(self, build: PoE2BuildData) -> str:
        """生成关键天赋特征文本"""
        parts = []
        
        if build.passive_keystones:
            parts.extend(build.passive_keystones)
        if build.major_nodes:
            parts.extend(build.major_nodes[:5])  # 只取前5个主要节点
        
        return " ".join(parts)
    
    def _generate_stats_text(self, build: PoE2BuildData) -> str:
        """生成属性特征文本"""
        parts = []
        
        # 攻击属性
        if build.offensive_stats.dps > 0:
            dps = build.offensive_stats.dps
            if dps > 5000000:
                parts.append("very high damage")
            elif dps > 2000000:
                parts.append("high damage")
            elif dps > 500000:
                parts.append("medium damage")
            else:
                parts.append("low damage")
        
        # 防御属性
        ehp = build.defensive_stats.effective_health_pool()
        if ehp > 0:
            if ehp > 10000:
                parts.append("very high defense")
            elif ehp > 7000:
                parts.append("high defense")
            elif ehp > 4000:
                parts.append("medium defense")
            else:
                parts.append("low defense")
        
        # 抗性
        if build.defensive_stats.is_resistance_capped():
            parts.append("resistance capped")
        
        return " ".join(parts) if parts else "moderate stats"
    
    def _generate_goal_budget_text(self, build: PoE2BuildData) -> str:
        """生成目标预算特征文本"""
        parts = []
        
        parts.append(build.build_goal.value)
        parts.append(build.budget_tier)
        
        if build.total_cost > 0:
            if build.total_cost < 1:
                parts.append("very budget")
            elif build.total_cost < 5:
                parts.append("budget friendly")
            elif build.total_cost < 20:
                parts.append("medium cost")
            else:
                parts.append("expensive")
        
        return " ".join(parts)
    
    def vectorize_build(self, build: PoE2BuildData, use_multi_features: bool = True) -> np.ndarray:
        """向量化单个构筑
        
        Args:
            build: PoE2构筑数据
            use_multi_features: 是否使用多特征向量化
            
        Returns:
            构筑的向量表示
        """
        self._load_model()
        
        if not use_multi_features:
            # 单一综合特征
            text = self.generate_build_text(build, "comprehensive")
            vector = self.model.encode([text])[0]
        else:
            # 多特征向量化
            vectors = []
            weights = []
            
            for feature_type, weight in self.feature_weights.items():
                text = self.generate_build_text(build, feature_type)
                if text.strip():  # 只处理非空文本
                    feature_vector = self.model.encode([text])[0]
                    vectors.append(feature_vector * weight)
                    weights.append(weight)
            
            if not vectors:
                # 如果没有有效特征，使用综合描述
                text = self.generate_build_text(build, "comprehensive")
                vector = self.model.encode([text])[0]
            else:
                # 加权平均
                vector = np.sum(vectors, axis=0)
                # 重新标准化
                if np.linalg.norm(vector) > 0:
                    vector = vector / np.linalg.norm(vector)
        
        # 标准化
        if self.config.use_normalize and np.linalg.norm(vector) > 0:
            vector = vector / np.linalg.norm(vector)
        
        return vector.astype(np.float32)
    
    def vectorize_builds(self, builds: List[PoE2BuildData], 
                        use_multi_features: bool = True,
                        show_progress: bool = True) -> np.ndarray:
        """批量向量化构筑数据
        
        Args:
            builds: 构筑数据列表
            use_multi_features: 是否使用多特征向量化
            show_progress: 是否显示进度
            
        Returns:
            构筑向量矩阵 [num_builds, vector_dim]
        """
        if not builds:
            return np.array([]).reshape(0, self.config.vector_dimension)
        
        self._load_model()
        
        logger.info(f"开始向量化 {len(builds)} 个构筑...")
        
        vectors = []
        batch_size = self.config.batch_size
        
        for i in range(0, len(builds), batch_size):
            batch = builds[i:i+batch_size]
            batch_vectors = []
            
            for build in batch:
                try:
                    vector = self.vectorize_build(build, use_multi_features)
                    batch_vectors.append(vector)
                except Exception as e:
                    logger.warning(f"构筑向量化失败 {build.similarity_hash}: {e}")
                    # 使用零向量作为占位符
                    zero_vector = np.zeros(self.config.vector_dimension, dtype=np.float32)
                    batch_vectors.append(zero_vector)
            
            vectors.extend(batch_vectors)
            
            if show_progress and i % (batch_size * 10) == 0:
                progress = (i + batch_size) / len(builds) * 100
                logger.info(f"向量化进度: {progress:.1f}% ({i + batch_size}/{len(builds)})")
        
        result = np.array(vectors, dtype=np.float32)
        logger.info(f"向量化完成: {result.shape}")
        
        return result
    
    def vectorize_text(self, text: str) -> np.ndarray:
        """向量化任意文本 (用于查询)
        
        Args:
            text: 要向量化的文本
            
        Returns:
            文本的向量表示
        """
        self._load_model()
        
        vector = self.model.encode([text])[0]
        
        if self.config.use_normalize and np.linalg.norm(vector) > 0:
            vector = vector / np.linalg.norm(vector)
        
        return vector.astype(np.float32)
    
    def save_vectors(self, vectors: np.ndarray, build_hashes: List[str], 
                    output_path: str, metadata: Optional[Dict] = None):
        """保存向量数据到文件
        
        Args:
            vectors: 向量矩阵
            build_hashes: 对应的构筑哈希列表
            output_path: 输出文件路径
            metadata: 元数据信息
        """
        save_data = {
            "vectors": vectors.tolist(),
            "build_hashes": build_hashes,
            "vector_dimension": self.config.vector_dimension,
            "model_name": self.config.model_name,
            "timestamp": datetime.now().isoformat(),
            "config": asdict(self.config),
            "metadata": metadata or {}
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"向量数据已保存到: {output_path}")
    
    def load_vectors(self, input_path: str) -> Tuple[np.ndarray, List[str], Dict]:
        """从文件加载向量数据
        
        Args:
            input_path: 输入文件路径
            
        Returns:
            (向量矩阵, 构筑哈希列表, 元数据)
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        vectors = np.array(data["vectors"], dtype=np.float32)
        build_hashes = data["build_hashes"]
        metadata = data.get("metadata", {})
        
        # 验证向量维度
        if vectors.shape[1] != self.config.vector_dimension:
            logger.warning(f"加载的向量维度 {vectors.shape[1]} 与当前配置 {self.config.vector_dimension} 不匹配")
        
        logger.info(f"从 {input_path} 加载了 {vectors.shape[0]} 个向量")
        return vectors, build_hashes, metadata
    
    def clear_cache(self):
        """清理缓存"""
        self._text_cache.clear()
        self._vector_cache.clear()
        logger.info("向量化缓存已清理")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计"""
        return {
            "text_cache_size": len(self._text_cache),
            "vector_cache_size": len(self._vector_cache)
        }

# 工厂函数
def create_vectorizer(model_name: str = "all-MiniLM-L6-v2", 
                     cache_dir: str = "data/models") -> PoE2BuildVectorizer:
    """创建向量化引擎的工厂函数
    
    Args:
        model_name: Sentence-Transformer模型名称
        cache_dir: 模型缓存目录
        
    Returns:
        配置好的向量化引擎实例
    """
    config = VectorConfig(
        model_name=model_name,
        cache_dir=cache_dir
    )
    return PoE2BuildVectorizer(config)

# 测试和工具函数
def test_vectorization():
    """测试向量化功能"""
    from .models import PoE2BuildData, SkillGemSetup, ItemInfo, BuildGoal
    
    # 创建测试构筑
    test_build = PoE2BuildData(
        character_class="Ranger",
        ascendancy="Deadeye", 
        level=85,
        main_skill_setup=SkillGemSetup(
            main_skill="Lightning Arrow",
            support_gems=["Added Lightning Damage", "Elemental Damage with Attacks", "Multistrike"]
        ),
        weapon=ItemInfo(name="Windripper", type="bow"),
        passive_keystones=["Point Blank", "Iron Reflexes"],
        build_goal=BuildGoal.CLEAR_SPEED,
        total_cost=12.5
    )
    
    # 创建向量化引擎
    vectorizer = create_vectorizer()
    
    # 测试向量化
    print("测试文本生成...")
    comprehensive_text = vectorizer.generate_build_text(test_build, "comprehensive")
    print(f"综合描述: {comprehensive_text}")
    
    class_skill_text = vectorizer.generate_build_text(test_build, "class_skill")
    print(f"职业技能: {class_skill_text}")
    
    print("\n测试向量化...")
    vector = vectorizer.vectorize_build(test_build)
    print(f"向量维度: {vector.shape}")
    print(f"向量范围: [{vector.min():.4f}, {vector.max():.4f}]")
    print(f"向量模长: {np.linalg.norm(vector):.4f}")
    
    return vectorizer, test_build, vector

if __name__ == "__main__":
    # 运行测试
    vectorizer, test_build, vector = test_vectorization()
    print("RAG向量化引擎测试完成!")