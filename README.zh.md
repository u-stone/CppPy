# CppPy — C++ 游戏引擎与 Python 绑定方案验证项目

对比 5 种将 C++17 游戏引擎内核桥接到 Python 3.x 的方案。

## 绑定方案

| 方案 | 方式 | 模块 |
|------|------|------|
| **pybind11** | 头文件绑定，`PYBIND11_MODULE` 宏 | `enginepybind` |
| **nanobind** | pybind11 作者的下一代重写 | `enginenanobind` |
| **SWIG** | `.i` 接口文件自动生成粘合代码 | `engineswig` |
| **Cython** | `.pyx` → 编译为 C 扩展 | `enginecython` |
| **CFFI + ctypes** | 纯 C `extern "C"` ABI | `enginecffi` |

## 快速开始

```bash
# 1. 初始化（创建虚拟环境，安装依赖，配置 CMake）
python scripts/manage.py setup

# 2. 编译（C++ 引擎 + 5 个 Python 包 → dist/）
python scripts/manage.py build

# 3. 安装（可编辑模式，此后从任意目录 import）
python scripts/manage.py develop
```

```python
>>> import enginepybind
>>> engine = enginepybind.Engine()
>>> engine.init('{"app":"demo"}')
>>> engine.update(0.016)
>>> engine.shutdown()
```

验证：

```bash
python scripts/manage.py run     # 运行所有示例
python scripts/manage.py test    # 22 项 pytest 冒烟测试
python scripts/manage.py lint    # clang-format + flake8 + black
```

## 全部命令

| 命令 | 说明 |
|------|------|
| `setup` | 创建 venv，安装依赖，cmake 配置 |
| `build` | 编译 C++ 引擎和全部绑定方案 → `dist/` |
| `develop` | `pip install -e .` — 从任意目录 import |
| `run` | 运行所有示例脚本 |
| `test` | 运行 22 项 pytest 冒烟测试 |
| `format` | 自动格式化 C++（clang-format）和 Python（black） |
| `lint` | 格式检查（clang-format、flake8、black） |
| `tidy` | 引擎源码静态分析（clang-tidy） |
| `wheel` | 构建标准 `.whl` 用于 `pip install` |
| `package` | 将 `dist/` 打包为 `.zip` 分发包 |

所有命令自动使用 venv Python，无需手动激活。

## 分发

### Wheel — 标准 Python 打包 (`pip install`)

```bash
python scripts/manage.py wheel --config Release
pip install dist/enginepybind-0.1.0-*.whl
```

`.whl` 包含 `__init__.py`、`_core.pyd`、`_core.pyi`、`py.typed`。与 NumPy、PyTorch 同款标准格式。

### 可编辑安装 — 开发使用

```bash
python scripts/manage.py develop      # = pip install -e .
```

在 `venv/site-packages/` 中创建 egg-link → `dist/Debug/`。重新编译即可更新。

### PYTHONPATH — 零安装

```bash
PYTHONPATH=dist/Debug python                  # Linux / macOS
$env:PYTHONPATH="dist\Debug"; python           # Windows PowerShell
```

### Zip 压缩包 — 快速分发

```bash
python scripts/manage.py package --config Release
# → dist/enginepybind-0.1.0.zip
```

## VS Code

**只需一项配置**（已在 `.vscode/settings.json` 中）：

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/build/venv/Scripts/python.exe"
}
```

原理：`pip install -e .` 将包注册到 `venv/site-packages/`，Pylance 通过解释器自动发现——无需 `extraPaths`，无需终端 `PYTHONPATH`。

**调试**（`.vscode/launch.json`，按 `F5`）：
- `Python: Current File` — 调试当前文件
- `pytest: Current Test` — 调试单个测试
- `pytest: All Tests` — 调试全部测试

## 构建单个方案

```bash
python scripts/manage.py setup --scheme pybind11
python scripts/manage.py build --scheme pybind11
python scripts/manage.py run --scheme pybind11
```

## 环境要求

- CMake >= 3.20
- Python >= 3.9
- C++17 编译器（GCC 9+, Clang 10+, MSVC 2019+）
- SWIG（可选，setup 自动下载）
- Cython、pybind11、nanobind（setup 通过 pip 安装）

## 项目结构

```
CppPy/
├── engine/          # 共享 C++17 游戏引擎（静态库）
│   ├── include/     # 头文件：facade, scene, game_object, event_bus 等
│   └── src/         # 实现文件
├── bindings/        # 每种绑定方案一个子目录 + python/__init__.py 包入口
│   ├── pybind11/
│   ├── nanobind/
│   ├── swig/
│   ├── cython/
│   └── cffi/
├── examples/        # 每种方案的示例脚本
├── tests/           # pytest 冒烟测试（22 项，覆盖 5 个方案）
├── scripts/         # manage.py 编排脚本 + 存根/wheel 工具
├── dist/            # 构建产物 — 自包含 Python 包 + .whl
├── docs/            # 每种方案的技术文档
└── tools/           # .clang-format, .clang-tidy, cpp-python-bindings.skill
```

## 引擎 API 层次

- **C API**（`c_api.h`）：纯 `extern "C"` 函数，opaque `void*` 句柄。ABI 稳定，供 cffi/ctypes 和 SWIG 使用。
- **C++ 模板 API**（`cpp_api.h`）：模板、`std::vector`、`std::optional`、`std::shared_ptr`。供 pybind11 和 nanobind 使用。

## 技术文档

每种方案在 `docs/` 下有详细技术文档：

| 方案 | 文档 | 涵盖主题 |
|------|------|----------|
| pybind11 | [docs/pybind11.md](docs/pybind11.md) | STL 自动转换、GIL 管理、返回值策略 |
| nanobind | [docs/nanobind.md](docs/nanobind.md) | 更小体积、更快编译、自动 GIL |
| SWIG | [docs/swig.md](docs/swig.md) | `.i` 接口文件、typemap、多语言支持 |
| Cython | [docs/cython.md](docs/cython.md) | `.pxd`/`.pyx` 工作流、`cdef class`、接近原生性能 |
| CFFI + C API | [docs/cffi.md](docs/cffi.md) | 纯 C ABI、ctypes/CDLL、五种方案横向对比 |

**[docs/troubleshooting.md](docs/troubleshooting.md)** —— 踩坑记录与解决方案。

## 设计目标

1. **公平对比** — 所有方案共享同一个引擎核心，暴露相同的功能集
2. **真实场景** — 场景管理、组件系统、事件系统、多线程支持
3. **可验证** — 每种方案都有对应的 demo 脚本和 pytest 测试
4. **可扩展** — 清晰的目录结构，易于添加新的绑定方案或功能

## 许可协议

MIT
