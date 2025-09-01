"""
单元测试 - RAG系统组件

测试RAG(检索增强生成)系统的所有组件：
- 向量化器 (Vectorizer)
- 知识库管理 (Knowledge Base)
- 检索系统 (Retrieval System)
- AI增强引擎 (Enhanced Engine)
"""

import pytest
import numpy as np
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from src.poe2build.rag.vectorizer import (
    BuildVectorizer, 
    VectorizedBuild, 
    SimilarityCalculator
)
from src.poe2build.rag.knowledge_base import (
    KnowledgeBase, 
    BuildDocument, 
    IndexedDocument
)
from src.poe2build.rag.retrieval import (
    RetrievalSystem, 
    RetrievalQuery, 
    RetrievalResult
)
from src.poe2build.rag.ai_enhanced import (
    AIEnhancedEngine, 
    EnhancedRecommendation,
    ContextualPrompt
)
from src.poe2build.models.build import PoE2Build, PoE2BuildStats
from src.poe2build.models.characters import PoE2CharacterClass, PoE2Ascendancy


@pytest.mark.unit
class TestBuildVectorizer:
    """测试构筑向量化器"""
    
    def setup_method(self):
        """测试设置"""
        # Mock sentence-transformers模型
        with patch('sentence_transformers.SentenceTransformer'):
            self.vectorizer = BuildVectorizer(model_name='test-model')
        
    def test_vectorizer_initialization(self):
        """测试向量化器初始化"""
        assert self.vectorizer.model_name == 'test-model'
        assert self.vectorizer.vector_dim > 0
        assert hasattr(self.vectorizer, '_model')
        
    def test_build_to_text_conversion(self, sample_build):
        """测试构筑转文本"""
        text = self.vectorizer._build_to_text(sample_build)
        
        # 验证文本包含关键信息
        assert sample_build.name.lower() in text.lower()
        assert sample_build.character_class.value.lower() in text.lower()
        assert sample_build.main_skill_gem.lower() in text.lower()
        
        if sample_build.ascendancy:
            assert sample_build.ascendancy.value.lower() in text.lower()
            
        # 验证支援宝石信息
        for gem in sample_build.support_gems:
            assert gem.lower() in text.lower()
            
    def test_vectorize_build(self, sample_build):
        """测试构筑向量化"""
        # Mock模型输出
        mock_vector = np.random.rand(384).astype(np.float32)  # 典型的sentence-transformers维度
        self.vectorizer._model.encode = Mock(return_value=mock_vector)
        
        # 执行向量化
        vectorized = self.vectorizer.vectorize_build(sample_build)
        
        # 验证结果
        assert isinstance(vectorized, VectorizedBuild)
        assert vectorized.build_id == sample_build.id
        assert vectorized.build_name == sample_build.name
        assert vectorized.vector.shape == (384,)
        assert vectorized.character_class == sample_build.character_class
        
        # 验证模型调用
        self.vectorizer._model.encode.assert_called_once()
        
    def test_batch_vectorization(self, sample_builds_list):
        """测试批量向量化"""
        # Mock批量输出
        batch_size = len(sample_builds_list)
        mock_vectors = np.random.rand(batch_size, 384).astype(np.float32)
        self.vectorizer._model.encode = Mock(return_value=mock_vectors)
        
        # 执行批量向量化
        vectorized_builds = self.vectorizer.vectorize_builds(sample_builds_list)
        
        # 验证结果
        assert len(vectorized_builds) == batch_size
        for i, vectorized in enumerate(vectorized_builds):
            assert isinstance(vectorized, VectorizedBuild)
            assert np.array_equal(vectorized.vector, mock_vectors[i])
            assert vectorized.build_name == sample_builds_list[i].name
            
    def test_vector_similarity_calculation(self):
        """测试向量相似度计算"""
        # 创建测试向量
        vector1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vector2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        vector3 = np.array([1.0, 0.0, 0.0], dtype=np.float32)  # 与vector1相同
        
        calculator = SimilarityCalculator()
        
        # 测试余弦相似度
        sim_12 = calculator.cosine_similarity(vector1, vector2)
        sim_13 = calculator.cosine_similarity(vector1, vector3)
        
        assert abs(sim_12 - 0.0) < 1e-6  # 正交向量，相似度为0
        assert abs(sim_13 - 1.0) < 1e-6  # 相同向量，相似度为1
        
        # 测试欧几里得距离
        dist_12 = calculator.euclidean_distance(vector1, vector2)
        dist_13 = calculator.euclidean_distance(vector1, vector3)
        
        assert dist_12 > dist_13  # 不同向量距离更大
        assert abs(dist_13) < 1e-6  # 相同向量距离为0


@pytest.mark.unit
class TestKnowledgeBase:
    """测试知识库管理"""
    
    def setup_method(self):
        """测试设置"""
        with patch('faiss.IndexFlatIP'):
            self.knowledge_base = KnowledgeBase(vector_dim=384)
        
    def test_knowledge_base_initialization(self):
        """测试知识库初始化"""
        assert self.knowledge_base.vector_dim == 384
        assert self.knowledge_base.document_count == 0
        assert hasattr(self.knowledge_base, '_index')
        assert hasattr(self.knowledge_base, '_documents')
        
    def test_build_document_creation(self, sample_build):
        """测试构筑文档创建"""
        document = BuildDocument.from_build(sample_build)
        
        assert document.build_id == sample_build.id
        assert document.name == sample_build.name
        assert document.character_class == sample_build.character_class.value
        assert document.level == sample_build.level
        assert document.main_skill == sample_build.main_skill_gem
        assert set(document.support_gems) == set(sample_build.support_gems)
        assert document.estimated_cost == sample_build.estimated_cost
        
    def test_add_documents(self, sample_builds_list):
        """测试添加文档到知识库"""
        # 创建文档
        documents = [BuildDocument.from_build(build) for build in sample_builds_list]
        
        # 创建Mock向量
        mock_vectors = np.random.rand(len(documents), 384).astype(np.float32)
        
        # Mock vectorizer
        mock_vectorizer = Mock()
        mock_vectorized_builds = []
        for i, doc in enumerate(documents):
            mock_vectorized = VectorizedBuild(
                build_id=doc.build_id,
                build_name=doc.name,
                vector=mock_vectors[i],
                character_class=sample_builds_list[i].character_class,
                metadata={'document_index': i}
            )
            mock_vectorized_builds.append(mock_vectorized)
        
        mock_vectorizer.vectorize_builds.return_value = mock_vectorized_builds
        
        # 添加文档
        indexed_docs = self.knowledge_base.add_documents(documents, mock_vectorizer)
        
        # 验证结果
        assert len(indexed_docs) == len(documents)
        assert self.knowledge_base.document_count == len(documents)
        
        for i, indexed_doc in enumerate(indexed_docs):
            assert isinstance(indexed_doc, IndexedDocument)
            assert indexed_doc.document_id == documents[i].build_id
            assert indexed_doc.index_position == i
            
    def test_search_similar_documents(self):
        """测试相似文档搜索"""
        # Mock FAISS索引搜索
        mock_scores = np.array([0.95, 0.87, 0.72], dtype=np.float32)
        mock_indices = np.array([0, 2, 1], dtype=np.int64)
        
        self.knowledge_base._index.search = Mock(return_value=(mock_scores.reshape(1, -1), mock_indices.reshape(1, -1)))
        
        # 模拟文档数据
        self.knowledge_base._documents = {
            0: BuildDocument(build_id='build_1', name='Build 1', character_class='Sorceress'),
            1: BuildDocument(build_id='build_2', name='Build 2', character_class='Ranger'),  
            2: BuildDocument(build_id='build_3', name='Build 3', character_class='Sorceress')
        }
        
        # 执行搜索
        query_vector = np.random.rand(384).astype(np.float32)
        results = self.knowledge_base.search_similar(query_vector, k=3, min_similarity=0.7)
        
        # 验证结果
        assert len(results) == 3
        
        # 验证排序（按相似度降序）
        assert results[0].similarity_score == 0.95
        assert results[1].similarity_score == 0.87
        assert results[2].similarity_score == 0.72
        
        # 验证文档内容
        assert results[0].document.name == 'Build 1'
        assert results[2].document.name == 'Build 2'
        
    def test_filter_by_criteria(self):
        """测试按条件过滤文档"""
        # 设置模拟文档
        self.knowledge_base._documents = {
            0: BuildDocument(
                build_id='build_1', 
                name='Lightning Sorceress',
                character_class='Sorceress',
                level=90,
                estimated_cost=15.0
            ),
            1: BuildDocument(
                build_id='build_2',
                name='Budget Ranger', 
                character_class='Ranger',
                level=85,
                estimated_cost=3.0
            ),
            2: BuildDocument(
                build_id='build_3',
                name='Endgame Sorceress',
                character_class='Sorceress', 
                level=95,
                estimated_cost=50.0
            )
        }
        
        # 过滤条件：Sorceress职业，预算<20
        filtered = self.knowledge_base.filter_documents(
            character_class='Sorceress',
            max_budget=20.0
        )
        
        # 验证结果
        assert len(filtered) == 1
        assert filtered[0].name == 'Lightning Sorceress'
        assert filtered[0].character_class == 'Sorceress'
        assert filtered[0].estimated_cost <= 20.0


@pytest.mark.unit
@pytest.mark.asyncio
class TestRetrievalSystem:
    """测试检索系统"""
    
    def setup_method(self):
        """测试设置"""
        self.mock_knowledge_base = Mock(spec=KnowledgeBase)
        self.mock_vectorizer = Mock(spec=BuildVectorizer)
        
        self.retrieval_system = RetrievalSystem(
            knowledge_base=self.mock_knowledge_base,
            vectorizer=self.mock_vectorizer
        )
        
    async def test_retrieval_query_creation(self):
        """测试检索查询创建"""
        query = RetrievalQuery(
            query_text="Lightning damage sorceress build for endgame",
            character_class=PoE2CharacterClass.SORCERESS,
            max_budget=20.0,
            min_dps=500000,
            preferred_skills=["Lightning Bolt", "Chain Lightning"],
            k=5,
            min_similarity=0.7
        )
        
        assert query.query_text == "Lightning damage sorceress build for endgame"
        assert query.character_class == PoE2CharacterClass.SORCERESS
        assert query.k == 5
        assert "Lightning Bolt" in query.preferred_skills
        
    async def test_semantic_search(self):
        """测试语义搜索"""
        # 创建查询
        query = RetrievalQuery(
            query_text="High DPS lightning build",
            character_class=PoE2CharacterClass.SORCERESS,
            k=3
        )
        
        # Mock向量化结果
        mock_query_vector = np.random.rand(384).astype(np.float32)
        self.mock_vectorizer.vectorize_text.return_value = mock_query_vector
        
        # Mock搜索结果
        mock_documents = [
            BuildDocument(build_id='1', name='Lightning Build 1', character_class='Sorceress'),
            BuildDocument(build_id='2', name='Lightning Build 2', character_class='Sorceress')
        ]
        
        mock_results = [
            RetrievalResult(
                document=mock_documents[0],
                similarity_score=0.89,
                rank=1
            ),
            RetrievalResult(
                document=mock_documents[1],
                similarity_score=0.82,
                rank=2
            )
        ]
        
        self.mock_knowledge_base.search_similar.return_value = mock_results
        
        # 执行检索
        results = await self.retrieval_system.search(query)
        
        # 验证结果
        assert len(results) == 2
        assert results[0].similarity_score > results[1].similarity_score
        assert all(result.document.character_class == 'Sorceress' for result in results)
        
        # 验证调用
        self.mock_vectorizer.vectorize_text.assert_called_once_with(query.query_text)
        self.mock_knowledge_base.search_similar.assert_called_once()
        
    async def test_hybrid_search_with_filters(self):
        """测试混合搜索（语义搜索+过滤）"""
        query = RetrievalQuery(
            query_text="Budget friendly build",
            character_class=PoE2CharacterClass.RANGER,
            max_budget=10.0,
            min_level=80,
            k=5
        )
        
        # Mock过滤结果
        filtered_docs = [
            BuildDocument(
                build_id='budget_1', 
                name='Budget Ranger 1',
                character_class='Ranger',
                level=82,
                estimated_cost=8.0
            )
        ]
        
        self.mock_knowledge_base.filter_documents.return_value = filtered_docs
        
        # Mock语义搜索
        mock_vector = np.random.rand(384).astype(np.float32)
        self.mock_vectorizer.vectorize_text.return_value = mock_vector
        
        search_results = [
            RetrievalResult(
                document=filtered_docs[0],
                similarity_score=0.75,
                rank=1
            )
        ]
        
        self.mock_knowledge_base.search_similar_in_subset.return_value = search_results
        
        # 执行混合搜索
        results = await self.retrieval_system.hybrid_search(query)
        
        # 验证结果
        assert len(results) == 1
        assert results[0].document.character_class == 'Ranger'
        assert results[0].document.estimated_cost <= query.max_budget
        assert results[0].document.level >= query.min_level
        
    async def test_retrieval_with_reranking(self):
        """测试带重新排序的检索"""
        query = RetrievalQuery(
            query_text="Endgame boss killer",
            preferred_skills=["Lightning Bolt"],
            k=10,
            rerank=True
        )
        
        # Mock初始搜索结果
        initial_results = []
        for i in range(10):
            doc = BuildDocument(
                build_id=f'build_{i}',
                name=f'Build {i}',
                main_skill='Lightning Bolt' if i % 3 == 0 else 'Other Skill'
            )
            result = RetrievalResult(
                document=doc,
                similarity_score=0.8 - i * 0.05,
                rank=i + 1
            )
            initial_results.append(result)
            
        self.mock_knowledge_base.search_similar.return_value = initial_results
        self.mock_vectorizer.vectorize_text.return_value = np.random.rand(384).astype(np.float32)
        
        # 执行搜索
        results = await self.retrieval_system.search_with_reranking(query)
        
        # 验证重新排序效果（具有首选技能的构筑应该排在前面）
        lightning_builds = [r for r in results if r.document.main_skill == 'Lightning Bolt']
        other_builds = [r for r in results if r.document.main_skill != 'Lightning Bolt']
        
        # Lightning Bolt构筑应该排在前面
        assert len(lightning_builds) > 0
        if len(lightning_builds) > 1:
            assert results.index(lightning_builds[0]) < results.index(other_builds[0])


@pytest.mark.unit
@pytest.mark.asyncio 
class TestAIEnhancedEngine:
    """测试AI增强引擎"""
    
    def setup_method(self):
        """测试设置"""
        self.mock_retrieval = Mock(spec=RetrievalSystem)
        self.mock_llm_client = AsyncMock()
        
        self.ai_engine = AIEnhancedEngine(
            retrieval_system=self.mock_retrieval,
            llm_client=self.mock_llm_client
        )
        
    async def test_contextual_prompt_creation(self):
        """测试上下文提示创建"""
        # 创建用户请求
        user_request = {
            'character_class': 'Sorceress',
            'build_goal': 'endgame_content',
            'max_budget': 20.0,
            'preferred_skills': ['Lightning Bolt']
        }
        
        # 创建检索结果
        retrieval_results = [
            RetrievalResult(
                document=BuildDocument(
                    build_id='similar_1',
                    name='Similar Lightning Build',
                    character_class='Sorceress',
                    main_skill='Lightning Bolt',
                    estimated_dps=850000
                ),
                similarity_score=0.89,
                rank=1
            )
        ]
        
        # 创建上下文提示
        prompt = self.ai_engine._create_contextual_prompt(user_request, retrieval_results)
        
        assert isinstance(prompt, ContextualPrompt)
        assert user_request['character_class'] in prompt.user_context
        assert 'Similar Lightning Build' in prompt.retrieved_context
        assert 'Lightning Bolt' in prompt.skill_context
        
    async def test_generate_recommendations(self):
        """测试生成推荐"""
        user_request = {
            'character_class': 'Sorceress',
            'build_goal': 'endgame_content',
            'max_budget': 15.0
        }
        
        # Mock检索结果
        mock_retrieval_results = [
            RetrievalResult(
                document=BuildDocument(
                    build_id='ref_1',
                    name='Reference Build 1',
                    character_class='Sorceress',
                    estimated_dps=750000
                ),
                similarity_score=0.85,
                rank=1
            )
        ]
        
        self.mock_retrieval.search.return_value = mock_retrieval_results
        
        # Mock LLM响应
        mock_llm_response = '''
        {
            "recommendations": [
                {
                    "name": "AI Enhanced Lightning Sorceress",
                    "character_class": "Sorceress",
                    "ascendancy": "Stormweaver",
                    "level": 92,
                    "main_skill": "Lightning Bolt",
                    "support_gems": ["Added Lightning", "Lightning Penetration", "Elemental Focus"],
                    "estimated_dps": 820000,
                    "estimated_ehp": 8200,
                    "estimated_cost": 14.5,
                    "confidence": 0.87,
                    "reasoning": "Optimized based on similar successful builds"
                }
            ]
        }
        '''
        
        self.mock_llm_client.complete.return_value = mock_llm_response
        
        # 执行生成
        recommendations = await self.ai_engine.generate_recommendations(user_request)
        
        # 验证结果
        assert len(recommendations) == 1
        
        rec = recommendations[0]
        assert isinstance(rec, EnhancedRecommendation)
        assert rec.name == "AI Enhanced Lightning Sorceress"
        assert rec.character_class == "Sorceress"
        assert rec.estimated_cost <= user_request['max_budget']
        assert rec.confidence > 0.8
        assert rec.reasoning is not None
        
        # 验证调用
        self.mock_retrieval.search.assert_called_once()
        self.mock_llm_client.complete.assert_called_once()
        
    async def test_recommendation_with_fallback(self):
        """测试带备用方案的推荐生成"""
        user_request = {
            'character_class': 'Monk',
            'build_goal': 'budget_friendly',
            'max_budget': 5.0
        }
        
        # Mock检索失败
        self.mock_retrieval.search.side_effect = Exception("Retrieval failed")
        
        # Mock备用数据
        fallback_data = [
            {
                'name': 'Fallback Budget Monk',
                'character_class': 'Monk',
                'estimated_cost': 3.0,
                'source': 'fallback_cache'
            }
        ]
        
        with patch.object(self.ai_engine, '_get_fallback_recommendations') as mock_fallback:
            mock_fallback.return_value = [EnhancedRecommendation(**fallback_data[0])]
            
            # 执行生成（应该使用备用方案）
            recommendations = await self.ai_engine.generate_recommendations(user_request)
            
            # 验证备用方案
            assert len(recommendations) == 1
            assert recommendations[0].name == 'Fallback Budget Monk'
            assert recommendations[0].source == 'fallback_cache'
            
    async def test_recommendation_quality_scoring(self):
        """测试推荐质量评分"""
        # 创建不同质量的推荐
        recommendations = [
            EnhancedRecommendation(
                name="High Quality Build",
                character_class="Sorceress",
                estimated_dps=900000,
                estimated_ehp=8500,
                estimated_cost=18.0,
                confidence=0.92,
                source_similarity=0.89
            ),
            EnhancedRecommendation(
                name="Medium Quality Build",
                character_class="Sorceress",
                estimated_dps=600000,
                estimated_ehp=7000,
                estimated_cost=12.0,
                confidence=0.78,
                source_similarity=0.75
            ),
            EnhancedRecommendation(
                name="Low Quality Build",
                character_class="Sorceress",
                estimated_dps=300000,
                estimated_ehp=5000,
                estimated_cost=8.0,
                confidence=0.65,
                source_similarity=0.62
            )
        ]
        
        # 计算质量评分
        scored_recommendations = self.ai_engine._score_recommendations(recommendations)
        
        # 验证排序（按质量评分降序）
        assert scored_recommendations[0].name == "High Quality Build"
        assert scored_recommendations[-1].name == "Low Quality Build"
        
        # 验证质量评分递减
        scores = [rec.quality_score for rec in scored_recommendations]
        assert all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
