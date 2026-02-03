# 测试文档

## 概述

本项目使用 pytest 作为测试框架，包含单元测试和集成测试。

## 测试结构

```
tests/
├── conftest.py              # pytest 配置和共享 fixtures
├── unit/                    # 单元测试
│   ├── test_common.py       # 测试通用工具模块
│   ├── test_config_validator.py  # 测试配置验证模块
│   └── test_tagging_service.py   # 测试标签服务模块
└── integration/             # 集成测试（待添加）
```

## 运行测试

### 运行所有测试

```bash
pytest
```

### 运行单元测试

```bash
pytest tests/unit/
```

### 运行特定测试文件

```bash
pytest tests/unit/test_common.py
```

### 运行特定测试类

```bash
pytest tests/unit/test_common.py::TestSetupWindowsEncoding
```

### 运行特定测试方法

```bash
pytest tests/unit/test_common.py::TestSetupWindowsEncoding::test_setup_windows_encoding_on_windows
```

### 显示详细输出

```bash
pytest -v
```

### 显示测试覆盖率

```bash
pytest --cov=src --cov-report=html
```

覆盖率报告将生成在 `htmlcov/` 目录中。

### 运行带标记的测试

```bash
pytest -m unit        # 只运行单元测试
pytest -m integration # 只运行集成测试
pytest -m slow        # 只运行慢速测试
```

## 测试标记

- `unit`: 单元测试
- `integration`: 集成测试
- `slow`: 慢速测试
- `api`: API 测试

## 编写测试

### 测试文件命名

测试文件应以 `test_` 开头，例如 `test_common.py`。

### 测试类命名

测试类应以 `Test` 开头，例如 `TestSetupWindowsEncoding`。

### 测试方法命名

测试方法应以 `test_` 开头，例如 `test_setup_windows_encoding_on_windows`。

### 使用 Fixtures

在 `conftest.py` 中定义的 fixtures 可以在所有测试中使用：

```python
def test_example(mock_nav_repo, sample_songs):
    # 使用 fixtures
    songs = sample_songs
    repo = mock_nav_repo
```

### Mock 对象

使用 `unittest.mock` 来模拟外部依赖：

```python
from unittest.mock import Mock, patch

def test_example():
    mock_obj = Mock()
    mock_obj.method.return_value = "test"
    
    with patch('module.path.to.function', return_value="mocked"):
        # 测试代码
        pass
```

## 添加新测试

1. 在 `tests/unit/` 或 `tests/integration/` 中创建新的测试文件
2. 按照命名规范命名测试文件、类和方法
3. 在 `conftest.py` 中添加需要的 fixtures（如果需要）
4. 运行测试验证

## 测试覆盖率目标

- 核心模块覆盖率目标：80%+
- 工具模块覆盖率目标：90%+
- 服务模块覆盖率目标：75%+

## CI/CD 集成

测试可以在 CI/CD 流程中自动运行：

```yaml
# 示例 GitHub Actions 配置
- name: Run tests
  run: |
    pip install -r requirements-dev.txt
    pytest --cov=src --cov-report=xml
```

## 故障排除

### 导入错误

如果遇到导入错误，确保项目根目录在 Python 路径中：

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 依赖问题

安装开发依赖：

```bash
pip install -r requirements-dev.txt
```

### 数据库连接错误

单元测试使用 mock 对象，不需要真实的数据库连接。如果遇到数据库相关错误，检查是否正确使用了 mock。
