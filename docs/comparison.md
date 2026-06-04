# 五种 C++ → Python 桥接方案对比

仅聚焦**桥接机制本身**：C++ 代码如何变成 Python 可调用的对象。不涉及环境搭建、项目结构、分发方式等工程问题。

## 一图总览

| | pybind11 | nanobind | SWIG | Cython | CFFI/ctypes |
|---|---|---|---|---|---|
| **桥接代码写在哪** | C++ 源文件中 | C++ 源文件中 | `.i` 接口文件中 | `.pxd` + `.pyx` 文件中 | Python 端（ctypes） |
| **桥接产物** | `.pyd`（Python C 扩展） | `.pyd`（Python C 扩展） | `.pyd` + `.py` 包装 | `.pyd`（Python C 扩展） | 普通 `.dll`/`.so` |
| **依赖 C++ 编译器** | 是 | 是 | 是 | 是 | 否（仅编译 DLL 需要） |
| **需要 C++ 头文件** | 是 | 是 | 是 | 是 | 否（仅编译 DLL 需要） |
| **模板/STL 支持** | 原生 | 原生 | 需手动 `%template` | 需手动声明 | 不支持 |
| **调用开销** | 极低（直接 C ABI） | 极低（直接 C ABI） | 低（一层 Python 包装） | 极低（直接 C ABI） | 中（ctypes 类型转换） |
| **学习曲线** | 低 | 低 | 中 | 中高 | 极低 |

## 桥接原理

### pybind11 / nanobind — 在 C++ 侧写绑定

```cpp
// bindings.cpp — 桥接代码和 C++ 源码在同一个编译单元
#include <pybind11/pybind11.h>
#include "engine.h"

PYBIND11_MODULE(_core, m) {
    py::class_<Engine>(m, "Engine")
        .def(py::init<>())
        .def("update", &Engine::Update);    // C++ 方法 → Python 方法
}
```

**工作流**：C++ 编译器将这段代码 + 引擎代码 → 编译为一个 `.pyd`。Python `import` 时，CPython 直接加载并调用其中的 C 函数。**本质上就是在 `.pyd` 里写 Python C API 调用，pybind11 用模板元编程隐藏了这些调用**。

**调用链路**：
```
Python: engine.update(0.016)
  → CPython 调用 PyCFunction (C 函数指针)
    → pybind11 生成的 thunk 函数
      → pybind11 拆包参数（py::arg → float）
        → Engine::Update(0.016f)   ← 直接 C++ 调用，零额外开销
```

**类型映射**：编译期确定。`py::class_<Engine>` 在编译时生成所有必要的 Python C API 结构（`PyTypeObject`、`tp_methods` 等）。STL 容器（`std::vector`、`std::map`）自动转换为 Python `list`、`dict`。

### SWIG — 从接口文件生成绑定

```swig
// engine.i — 独立的接口描述文件
%module engine
%{
#include "engine.h"    // SWIG 会把这段原样插入生成的 .cxx
%}
%include "engine.h"     // SWIG 解析这个头文件，自动生成包装代码
```

**工作流**：
1. 编写 `.i` 接口文件（告诉 SWIG 要暴露什么）
2. SWIG 读取 `.i` → 生成 `_wrap.cxx`（C++ 胶水代码）+ `engine.py`（Python 包装）
3. 编译 `_wrap.cxx` → `_engine.pyd`
4. 用户 `import engine` → 执行 `engine.py` → `engine.py` import `_engine.pyd`

**调用链路**：
```
Python: engine.create_scene("Main")
  → engine.py 中的包装函数（纯 Python）
    → _engine.pyd 中的 C 函数（SWIG 生成）
      → 引擎 C++ 函数
```

**两层结构**是 SWIG 的独特之处：`.py` 是纯 Python（可读、可改、可调试），`.pyd` 是编译后的胶水代码。`%feature("autodoc")` 可以让 `.py` 文件自带 docstring。

**类型映射**：通过 typemap 系统。默认只处理基本类型（`int`、`float`、`char*`）。`std::string`、`std::vector` 需要额外 typemap 或 `%template` 指令。

### Cython — 用 Python 超集语言写 C 扩展

```cython
# _core.pxd — 声明 C API（类似 C 头文件）
cdef extern from "engine/c_api.h":
    ctypedef void* EngineHandle
    void engine_update(EngineHandle, float dt)

# _core.pyx — 实现 Python 包装类
cdef class Engine:
    cdef EngineHandle _handle

    def __cinit__(self):
        self._handle = engine_create()

    def update(self, float dt):
        engine_update(self._handle, dt)
```

**工作流**：
1. 编写 `.pxd`（类型声明）+ `.pyx`（实现代码）
2. Cython 编译器将 `.pyx` → 翻译为 `.cxx`（纯 C 代码，调用 Python C API）
3. C++ 编译器编译 `.cxx` → `.pyd`

**调用链路**：
```
Python: engine.update(0.016)
  → CPython 调用 PyCFunction
    → Cython 生成的 C 函数
      → C 函数调用（engine_update handle dt）
        → 引擎 C++ 实现
```

**独特优势**：`.pyx` 语法是 Python 超集——你可以写纯 Python 代码，也可以用 `cdef` 声明 C 类型变量，Cython 会编译为高效的 C 代码。`cdef class` 的内存布局是 C 结构体，属性访问是直接内存偏移，无字典查找。

**类型映射**：`cdef` 声明决定。`int` → C `int`，`float` → C `float`，`object` → Python 对象（保持 Python 语义）。`cdef extern` 完全由开发者手动声明 C 类型。

### CFFI / ctypes — 纯 C ABI，Python 侧加载

```python
# cffi_bridge.py — 全部在 Python 侧
import ctypes

_lib = ctypes.CDLL("engine_c.dll")        # 加载纯 C 共享库

_lib.engine_create.argtypes = []          # 声明参数类型
_lib.engine_create.restype = ctypes.c_void_p  # 声明返回类型

_lib.engine_update.argtypes = [ctypes.c_void_p, ctypes.c_float]

# Pythonic 包装
class Engine:
    def __init__(self):
        self._handle = _lib.engine_create()

    def update(self, dt):
        _lib.engine_update(self._handle, dt)
```

**工作流**：
1. C++ 代码编译为**纯 C 共享库**（`engine_c.dll`），所有导出函数用 `extern "C"`
2. Python 侧用 `ctypes.CDLL` 加载 `.dll`
3. 手写 Python 包装类，调用 `ctypes` 函数

**调用链路**：
```
Python: engine.update(0.016)
  → Engine.update()  (纯 Python)
    → _lib.engine_update(handle, 0.016)  (ctypes)
      → ctypes 将 Python float → C float
        → LoadLibrary 找到 engine_c.dll 中的函数
          → C 函数 engine_update(void*, float)
            → C++ 实现
```

**独特之处**：这是唯一**不需要 C++ 编译器来生成绑定**的方案。Python 侧的桥接代码是纯 Python（ctypes 是标准库）。代价是类型声明全部手动（`argtypes`、`restype`），且不支持 C++ 特性（模板、重载、类继承）。

## 产物文件来源

最终 `dist/Debug/enginepybind/` 目录下每个文件的"出身"：

### pybind11

| 文件 | 来源 | 生成方式 |
|------|------|----------|
| `__init__.py` | `bindings/pybind11/python/__init__.py` | CMake POST_BUILD 复制 |
| `_core.*.pyd` | `bindings/pybind11/src/pybind11_bindings.cpp` | pybind11 头文件 + C++ 编译器 → 单个 `.pyd` |
| `_core.pyi` | 运行时自省 `_core.pyd` | `pybind11-stubgen`（独立工具）→ import 模块 → 读取 `help()`/`__doc__` → 推断参数和返回类型 → 生成 `.pyi` |
| `py.typed` | — | `generate_stubs.py` 创建空文件（PEP 561） |

**核心流程**：手写 C++ → 编译器 → `.pyd`（打包所有 C++ 代码）。`.pyi` 由工具从已编译的 `.pyd` 内省生成。

### nanobind

| 文件 | 来源 | 生成方式 |
|------|------|----------|
| `__init__.py` | `bindings/nanobind/python/__init__.py` | CMake POST_BUILD 复制 |
| `_core.*.pyd` | `bindings/nanobind/src/nanobind_bindings.cpp` | nanobind 头文件 + C++ 编译器 → 单个 `.pyd` |
| `_core.pyi` | 运行时自省 `_core.pyd` | `nanobind.stubgen`（内置，精度最高） |
| `py.typed` | — | `generate_stubs.py` 创建 |

**核心流程**：与 pybind11 相同，但 `.pyi` 生成更精准（读 `__nb_signature__` 而非解析 docstring）。

### SWIG

| 文件 | 来源 | 生成方式 |
|------|------|----------|
| `__init__.py` | SWIG 生成的 `engine_swig.py` | SWIG 解析 `.i` → 生成 `.py`（纯 Python 包装代码）；CMake 复制为 `__init__.py` |
| `_engine_swig.pyd` | SWIG 生成的 `enginePYTHON_wrap.cxx` | SWIG 解析 `.i` + C 头文件 → 生成 `.cxx` → C++ 编译器 → `.pyd` |
| `py.typed` | — | `generate_stubs.py` 创建 |

**核心流程**：接口文件 `.i` → SWIG → 两个产物（`.py` + `.cxx`）→ `.py` 用作包入口，`.cxx` 编译为 `.pyd`。`.py` 本身可读、可 debug。

### Cython

| 文件 | 来源 | 生成方式 |
|------|------|----------|
| `__init__.py` | `bindings/cython/python/__init__.py` | CMake POST_BUILD 复制 |
| `_core.pyd` | `_core.pyx` + `_core.pxd` | Cython 编译器 → `_core.cxx` → C++ 编译器 → `.pyd` |
| `_core.pyi` | `_core.pyx` AST 解析 | `stubgen-pyx` 解析 `.pyx` 语法树 → 生成 `.pyi` |
| `py.typed` | — | `generate_stubs.py` 创建 |

**核心流程**：手写 `.pyx`（Python 超集）→ Cython → `.cxx` → 编译器 → `.pyd`。`.pyi` 从 `.pyx` 源码生成（非运行时）。

### CFFI / ctypes

| 文件 | 来源 | 生成方式 |
|------|------|----------|
| `__init__.py` | `bindings/cffi/python/__init__.py` | CMake POST_BUILD 复制 |
| `cffi_bridge.py` | `bindings/cffi/python/cffi_bridge.py` | 手写，CMake 复制 |
| `engine_c.dll` | `bindings/cffi/src/cffi_c_impl.cpp` | C++ 编译器 → 纯 C 共享库（非 Python 扩展） |
| `cffi_bridge.pyi` | `bindings/cffi/python/cffi_bridge.pyi` | 手写，CMake 复制 |
| `py.typed` | — | `generate_stubs.py` 创建 |

**核心流程**：C++ → 纯 C DLL + Python 手写包装代码。**唯一不需要"绑定工具"的方案**——`ctypes` 是标准库，`.pyi` 也是手写。每个文件来源都是明确的源码文件，无代码生成。

## 该选哪个

| 场景 | 推荐 |
|------|------|
| 新项目，需要暴露大量 C++ 类和方法 | **nanobind** — 最快编译，最小体积，Python 3.8+ |
| 已有 pybind11 代码，不想迁移 | **pybind11** — 生态最成熟，文档最丰富 |
| 同一个 C 库需要暴露给多种语言（Python + Java + C#） | **SWIG** — 一份 `.i` 生成多种语言绑定 |
| 需要手写高性能 C 扩展，混合 Python 和 C 逻辑 | **Cython** — Python 超集，适合科学计算 |
| C++ API 很简单，或只有 C ABI，不想引入任何绑定依赖 | **CFFI/ctypes** — 标准库，零额外依赖 |
