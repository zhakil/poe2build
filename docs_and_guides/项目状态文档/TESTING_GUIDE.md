# PoE2 Build Generator 完整测试指南

本文档提供了Path of Exile 2 Build Generator项目的完整测试策略和使用指南。

## 📋 目录
- [测试架构概览](#测试架构概览)
- [快速开始](#快速开始)
- [测试类型详解](#测试类型详解)
- [测试工具和配置](#测试工具和配置)
- [CI/CD集成](#cicd集成)
- [最佳实践](#最佳实践)
- [故障排除](#故障排除)

## 🏗️ 测试架构概览

### 测试金字塔结构
```
           E2E Tests (少量)
         /              \
    Integration Tests (中等)
   /                      \
Unit Tests (大量) + Performance Tests
```

### 测试覆盖范围
- **单元测试 (Unit Tests)**: 95%+ 代码覆盖率目标
- **集成测试 (Integration Tests)**: 组件间交互测试
- **性能测试 (Performance Tests)**: 响应时间、吞吐量、内存使用
- **端到端测试 (E2E Tests)**: 完整用户场景验证

### 核心测试模块
```
tests/
├── unit/                     # 单元测试
│   ├── test_models_*.py      # 数据模型测试
│   ├── test_core_*.py        # 核心组件测试
│   ├── test_data_sources.py  # 数据源测试
│   └── test_rag_system.py    # RAG系统测试
├── integration/              # 集成测试
│   ├── test_end_to_end_workflow.py
│   └── test_api_integration.py
├── performance/              # 性能测试
│   ├── test_system_benchmarks.py
│   └── test_rag_performance.py
├── fixtures/                 # 测试数据和工具
│   ├── test_build_factory.py
│   ├── mock_responses/
│   └── sample_data/
└── conftest.py              # 全局测试配置
```

## 🚀 快速开始

### 1. 环境准备
```bash
# 安装依赖
pip install -r requirements.txt

# 安装测试依赖（自动安装）
python run_tests.py --install-deps

# 验证环境
python run_tests.py --validate-env
```

### 2. 运行基础测试
```bash
# 快速单元测试
python run_tests.py --types unit

# 完整测试套件
python run_tests.py --types all --mode full

# 烟雾测试（快速验证）
python run_tests.py --mode smoke
```

### 3. 查看测试报告
测试完成后，在 `test_reports/` 目录下查看：
- `test_report.html` - HTML测试报告
- `coverage/index.html` - 代码覆盖率报告
- `junit.xml` - JUnit格式报告

## 🔬 测试类型详解

### 单元测试 (Unit Tests)
**目标**: 测试每个模块的独立功能

```bash
# 运行所有单元测试
pytest -m "unit" -v

# 运行特定模块测试
pytest tests/unit/test_models_build.py -v

# 带覆盖率的单元测试
pytest -m "unit" --cov=src/poe2build --cov-report=html
```

**覆盖的核心组件**:
- ✅ PoE2角色模型 (`test_models_characters.py`)
- ✅ 构筑数据模型 (`test_models_build.py`)
- ✅ AI协调器核心功能 (`test_core_orchestrator.py`)
- ✅ 数据源组件 (`test_data_sources.py`)
- ✅ RAG系统组件 (`test_rag_system.py`)

### 集成测试 (Integration Tests)
**目标**: 测试系统组件间的交互

```bash
# 运行集成测试
pytest -m "integration" -v

# 长时间运行的集成测试
pytest -m "integration and slow" --timeout=600
```

**测试场景**:
- ✅ 端到端构筑推荐流程
- ✅ 外部API集成
- ✅ PoB2集成测试
- ✅ 数据一致性验证
- ✅ 并发请求处理

### 性能测试 (Performance Tests)
**目标**: 验证系统性能指标

```bash
# 运行性能测试
pytest -m "performance" -v

# 压力测试
python run_tests.py --mode stress --types performance
```

**性能基准**:
| 指标 | 目标值 | 测试场景 |
|------|--------|----------|
| 平均响应时间 | < 1000ms | 单个构筑推荐 |
| P95响应时间 | < 2000ms | 并发请求 |
| 吞吐量 | ≥ 10 req/s | 20并发用户 |
| 内存使用 | < 1GB | 持续负载 |
| 缓存命中率 | ≥ 85% | 重复请求 |

### 端到端测试 (E2E Tests)
**目标**: 验证完整的用户使用场景

```bash
# 运行E2E测试
pytest -m "e2e" -v --timeout=900
```

## 🛠️ 测试工具和配置

### 核心测试工具
- **pytest**: 测试框架
- **pytest-cov**: 覆盖率分析
- **pytest-html**: HTML报告生成
- **pytest-xdist**: 并行测试执行
- **pytest-mock**: Mock对象管理
- **pytest-asyncio**: 异步测试支持
- **pytest-timeout**: 测试超时控制
- **pytest-benchmark**: 性能基准测试

### 配置文件
```
pytest.ini           # pytest配置
tests/conftest.py    # 全局fixtures和配置
tests/test_config_advanced.py  # 高级测试环境配置
```

### 环境配置
支持多种测试环境:

```python
# 本地开发环境
python run_tests.py --env local --mode fast

# CI环境
python run_tests.py --env ci --mode full

# 性能测试环境
python run_tests.py --env performance --mode stress
```

## 🔄 CI/CD集成

### GitHub Actions工作流
配置文件: `.github/workflows/test.yml`

**触发条件**:
- Push到main/develop分支
- Pull Request
- 定时任务(每天深夜)
- 手动触发

**执行矩阵**:
- **Python版本**: 3.10, 3.11, 3.12
- **测试类型**: 单元、集成、性能、E2E
- **操作系统**: Ubuntu Latest

**工作流步骤**:
1. **代码质量检查** - Linting, 格式化, 安全检查
2. **单元测试** - 多Python版本并行执行
3. **集成测试** - Redis服务集成
4. **性能测试** - 基准测试和压力测试
5. **E2E测试** - 完整场景验证
6. **覆盖率报告** - 合并和上传到Codecov
7. **测试摘要** - 生成执行报告

### 本地CI模拟
```bash
# 模拟CI环境测试
python run_tests.py --env ci --code-quality --types all

# 快速CI验证
python run_tests.py --env ci --mode smoke
```

## ✅ 最佳实践

### 1. 测试编写规范
```python
# ✅ 良好的测试结构
@pytest.mark.unit
class TestBuildModel:
    def test_create_valid_build(self, sample_build_data):
        """测试创建有效构筑 - 明确的测试名称和文档"""
        # Arrange - 准备测试数据
        build_data = sample_build_data
        
        # Act - 执行被测试的操作
        build = PoE2Build(**build_data)
        
        # Assert - 验证结果
        assert build.name == build_data['name']
        assert build.level > 0
        assert_valid_build(build)  # 使用辅助函数
```

### 2. Mock使用策略
```python
# ✅ 适当的Mock使用
@patch('src.poe2build.data_sources.requests.get')
def test_api_call_with_mock(mock_get):
    """使用Mock隔离外部依赖"""
    mock_get.return_value.json.return_value = MOCK_API_RESPONSE
    
    result = api_client.fetch_data()
    
    assert result is not None
    mock_get.assert_called_once()
```

### 3. 测试数据管理
```python
# ✅ 使用工厂模式生成测试数据
from tests.fixtures.test_build_factory import TestBuildFactory

def test_multiple_builds():
    factory = TestBuildFactory(seed=42)  # 可重复的随机数
    builds = factory.create_build_batch(count=10)
    
    assert len(builds) == 10
    assert all(build.level >= 1 for build in builds)
```

### 4. 异步测试
```python
# ✅ 异步测试的正确写法
@pytest.mark.asyncio
async def test_async_build_generation():
    """测试异步构筑生成"""
    orchestrator = PoE2AIOrchestrator()
    await orchestrator.initialize()
    
    result = await orchestrator.generate_build_recommendations(request)
    
    assert 'recommendations' in result
    assert len(result['recommendations']) > 0
```

### 5. 性能测试最佳实践
```python
# ✅ 性能测试结构
@pytest.mark.performance
def test_response_time_benchmark(benchmark):
    """使用pytest-benchmark进行性能测试"""
    
    def run_build_generation():
        return orchestrator.generate_build_recommendations(standard_request)
    
    result = benchmark(run_build_generation)
    
    # 验证功能正确性
    assert 'recommendations' in result
    
    # 性能断言在benchmark中自动处理
```

## 🐛 故障排除

### 常见问题及解决方案

#### 1. 测试依赖问题
```bash
# 问题: ImportError或模块未找到
# 解决: 重新安装依赖
python run_tests.py --install-deps --upgrade
```

#### 2. 外部API超时
```bash
# 问题: API调用超时导致测试失败
# 解决: 使用Mock模式
python run_tests.py --env unit  # 单元测试自动使用Mock
```

#### 3. 内存不足
```bash
# 问题: 性能测试中内存溢出
# 解决: 降低并发度或使用快速模式
python run_tests.py --no-parallel --mode fast
```

#### 4. 覆盖率不足
```bash
# 问题: 代码覆盖率低于85%
# 解决: 查看具体未覆盖代码
pytest --cov=src/poe2build --cov-report=term-missing
# 然后针对性添加测试
```

#### 5. 测试执行缓慢
```bash
# 问题: 测试执行时间过长
# 解决: 使用并行执行和快速模式
python run_tests.py --mode fast --types unit
```

### 调试技巧

#### 1. 详细输出
```bash
# 查看详细测试输出
python run_tests.py --verbose --types unit

# 查看失败的测试详情
pytest tests/unit/test_specific.py::test_function -v -s
```

#### 2. 单独运行失败的测试
```bash
# 只运行失败的测试
pytest --lf  # last-failed

# 运行直到第一个失败
pytest -x
```

#### 3. 调试模式
```python
# 在测试中添加断点
def test_debug_example():
    build = create_test_build()
    
    import pdb; pdb.set_trace()  # 调试断点
    
    assert build.is_valid()
```

## 📊 测试指标和报告

### 关键指标追踪
- **代码覆盖率**: 目标 ≥ 85%
- **测试执行时间**: 单元测试 < 5分钟，完整套件 < 30分钟
- **测试通过率**: ≥ 98%
- **缺陷逃逸率**: < 5%

### 报告位置
```
test_reports/
├── test_report.html          # 主要HTML报告
├── junit.xml                 # JUnit格式报告
├── coverage/
│   └── index.html           # 覆盖率报告
├── performance/
│   └── benchmark.json       # 性能基准数据
└── test_config.json         # 测试配置记录
```

### CI报告集成
- **GitHub Actions**: 自动生成测试摘要
- **Codecov**: 覆盖率趋势分析
- **Artifacts**: 保存所有测试报告

## 🔮 未来改进计划

### 短期目标 (1-2个月)
- [ ] 增加更多边界情况测试
- [ ] 优化测试执行速度
- [ ] 增强性能测试覆盖率
- [ ] 改进Mock数据的真实性

### 长期目标 (3-6个月)
- [ ] 实现测试数据的自动生成
- [ ] 增加视觉回归测试
- [ ] 实现自动化的性能回归检测
- [ ] 集成更多第三方测试工具

---

## 📚 相关资源

- [pytest文档](https://docs.pytest.org/)
- [测试金字塔理论](https://martinfowler.com/articles/practical-test-pyramid.html)
- [Python测试最佳实践](https://realpython.com/python-testing/)
- [代码覆盖率指南](https://coverage.readthedocs.io/)

---

**维护者**: PoE2 Build Generator Team  
**最后更新**: 2024-01-15  
**文档版本**: 1.0

如有测试相关问题，请参考本指南或提交Issue到项目仓库。