# SWIG — 自动化多语言绑定生成器详解

## 概述

SWIG（Simplified Wrapper and Interface Generator）是一个经典且成熟的自动化绑定生成工具，最初于 1995 年发布，至今已有近三十年的历史。与 pybind11/nanobind 这种嵌入 C++ 代码的方案不同，SWIG 采用"接口定义文件"的方式：开发者编写 `.i` 文件声明需要暴露的 C/C++ 接口，SWIG 读取后自动生成对应的 Python C API 粘合代码（`_module.pyd`）和纯 Python 包装文件（`module.py`）。

SWIG 的核心优势在于**多语言支持**——同一个 `.i` 文件可以生成 Python、Java、C#、Ruby、Lua、Go 等 20+ 种语言的绑定代码。对于需要将同一 C++ 库暴露给多种语言的跨平台项目，SWIG 是独特的"一次编写，到处绑定"解决方案。

在本项目 CppPy 中，SWIG 绑定直接包装纯 C API（`engine/c_api.h`），展示了 SWIG 从 C 头文件自动生成 Python 绑定的经典工作流。

## 依赖环境

### 系统要求

- **SWIG 可执行文件**：版本 4.0+（推荐 4.4+，本项目使用 4.4.0）
- **编译器**：支持 C++17 的 MSVC、GCC 8+、或 Clang 7+
- **CMake**：3.20+（含 `UseSWIG` 模块）
- **Python**：3.6+（开发库，含 Python.h 头文件）
- **PCRE**（可选）：SWIG 构建时依赖，用于正则表达式处理

### 安装 SWIG

SWIG 的安装方式因平台而异：

**Windows**（本项目采用预编译二进制方式）：

```bash
# 从 SourceForge 下载 swigwin 预编译包
# https://sourceforge.net/projects/swig/files/swigwin/swigwin-4.4.0/

# 解压后将 swig.exe 所在目录加入 PATH，或直接在 CMake 中指定
```

**Linux**：
```bash
sudo apt install swig           # Debian/Ubuntu
sudo dnf install swig           # Fedora
pacman -S swig                  # Arch
```

**macOS**：
```bash
brew install swig
```

**从源码编译**（本项目探索过但最终采用了预编译方案）：
```bash
cd swig-4.4.1
./configure --prefix=/usr/local
make
sudo make install
```

源码编译面临的挑战（记录于本项目开发过程）：
1. PCRE2 依赖（需要安装 `libpcre2-dev` 或 `mingw-w64-x86_64-pcre2`）
2. Bison 依赖（需要安装 `bison`）
3. Windows 上 MinGW/MSVC ABI 不兼容问题——使用 clang 编译的 SWIG 无法链接 MinGW 构建的 PCRE2

### 构建系统集成

本项目的 SWIG CMake 配置：

```cmake
# top-level CMakeLists.txt — SWIG 部分
if(BUILD_SWIG)
  # 指向预编译的 swig.exe 及其标准库
  get_filename_component(_swig_exe "${THIRDPARTY_DIR}/swig-install/swig.exe"
    ABSOLUTE)
  set(SWIG_EXECUTABLE "${_swig_exe}"
      CACHE FILEPATH "Path to swig executable")
  set(SWIG_DIR "${THIRDPARTY_DIR}/swig-install/Lib"
      CACHE PATH "Path to swig library")

  find_package(SWIG QUIET)  # CMake 内置的 FindSWIG 模块
  if(SWIG_FOUND)
    include(UseSWIG)         # CMake 内置的 UseSWIG 模块
    add_subdirectory(bindings/swig)
  else()
    message(WARNING "SWIG not found -- skipping SWIG bindings")
  endif()
endif()
```

`bindings/swig/CMakeLists.txt` 展示了 SWIG 在 CMake 中的标准用法：

```cmake
find_package(Python3 REQUIRED COMPONENTS Development)

set(SWIG_MODULE_engine_swig_name engine_swig)

# SWIG 接口文件的 C++ 属性配置
set_property(SOURCE src/engine.i PROPERTY CPLUSPLUS ON)
set_property(SOURCE src/engine.i PROPERTY SWIG_MODULE_NAME engine_swig)
set_property(SOURCE src/engine.i PROPERTY SWIG_FLAGS
  "-I${CMAKE_SOURCE_DIR}/engine/include")

# swig_add_library 是 UseSWIG 提供的 CMake 宏
swig_add_library(engine_swig
  LANGUAGE python
  SOURCES src/engine.i
)

target_link_libraries(engine_swig PRIVATE engine ${Python3_LIBRARIES})

target_include_directories(engine_swig PRIVATE
  ${CMAKE_SOURCE_DIR}/engine/include
  ${Python3_INCLUDE_DIRS}
)

# 输出配置
set_target_properties(${SWIG_MODULE_engine_swig_name} PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/_build/swig"
)

# SWIG 会生成 engine_swig.py（Python 包装）和 _engine_swig.pyd（C 扩展）
# 需要将 .py 文件复制到与 .pyd 相同的输出目录
add_custom_command(TARGET engine_swig POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${CMAKE_CURRENT_BINARY_DIR}/engine_swig.py"
    "$<TARGET_FILE_DIR:engine_swig>/engine_swig/"
)
```

构建流程中，SWIG 做了两件事：
1. 从 `engine.i` 生成 `enginePYTHON_wrap.cxx`（C++ 粘合源文件）
2. 同时生成 `engine_swig.py`（Python 端包装代码）

## 核心技术细节

### .i 接口文件

SWIG 的核心是 `.i` 接口文件。它是 C/C++ 的超集，支持三类内容：
- **直接包含的 C/C++ 代码**（`%{ %}` 块中，直接复制到生成的包装文件中）
- **SWIG 指令**（以 `%` 开头，如 `%include`、`%inline`、`%module`）
- **普通 C/C++ 声明**（被 SWIG 解析并为其生成包装函数）

本项目完整的 `.i` 文件：

```swig
// bindings/swig/src/engine.i — SWIG interface file
// Wraps the pure-C API so SWIG can auto-generate Python glue.
//
// SWIG 4.x maps char* ↔ Python bytes by default. To keep things simple we
// stay with that behaviour and let demo.py handle encode/decode.

%module engine_swig        // ① 定义 Python 模块名

%begin %{                   // ② 生成代码的最顶部（在所有 SWIG 内容之前）
#define SWIG_PYTHON_STRICT_BYTE_CHAR  // 强制 char* → bytes 行为
%}

%{                          // ③ %{ %} 块：直接插入生成 C++ 文件的 C++ 代码
#include "engine/c_api.h"   // 使包装函数可以调用真实的 C API
%}

// ④ 确保 int64_t 映射为 Python int（而非不透明指针）
%include "stdint.i"

// ⑤ 自动包装 c_api.h 中所有 extern "C" 函数
%include "engine/c_api.h"

// ⑥ %inline 提供 Python 友好的组合函数
%inline %{
  void* engine_create_and_init(const char* config_json) {
    void* engine = engine_create();
    engine_init(engine, config_json);
    return engine;
  }

  void engine_run_ticks(void* engine, int ticks, float dt) {
    for (int i = 0; i < ticks; ++i) {
      engine_update(engine, dt);
    }
  }
%}
```

#### 关键语法详解

**① `%module engine_swig`**

定义生成的 Python 模块名称。它决定了：
- Python 中 `import engine_swig` 的模块名
- 生成的 C++ 包装文件名（`engine_swigPYTHON_wrap.cxx`）
- 生成的 Python 文件名（`engine_swig.py`）

**② `%begin %{ %}`**

`%begin` 块确保代码出现在生成文件的最顶部（在 SWIG 自身的头文件之前）。`SWIG_PYTHON_STRICT_BYTE_CHAR` 是 SWIG Python 模块的内部宏，当定义它时，SWIG 的所有 `char*` 类型映射将严格使用 Python `bytes` 对象（而非尝试模糊的 `str` 到 `bytes` 转换），避免 Python 3 下的编码歧义。

**③ `%{ %} 块（裸插入块）**

SWIG 的最基本语法。`%{` 和 `%}` 之间的内容被逐字复制到生成的 `.cxx` 文件中。通常用于：
- 包含必要的 C/C++ 头文件
- 定义辅助宏
- 声明静态变量

**④ `%include "stdint.i"`**

SWIG 标准库中的类型映射文件。`stdint.i` 为 `int64_t`、`uint32_t` 等标准整数类型提供从 C 到 Python `int` 的正确类型映射。如果不包含此文件，SWIG 会将 `int64_t` 视为不透明类型（未知结构体），Python 端得到 `<Swig Object of type 'int64_t *'>` 而非整数，并产生内存泄漏警告。

**⑤ `%include "engine/c_api.h"`**

这是 SWIG 最强大的特性：直接包含 C/C++ 头文件，SWIG 解析其中的函数声明、结构体、枚举和宏，自动生成 Python 绑定。SWIG 会处理以下内容：
- 函数声明 → Python 可调用函数
- 结构体和 `typedef` → Python 类（如果不透明指针，则为 SwigPyObject）
- 枚举 → Python 整数常量
- `#define` 常量 → Python 模块级常量

**⑥ `%inline %{ %}`**

内联代码块：其中定义的函数声明被 SWIG 解析生成包装，同时实现被复制到生成的 `.cxx` 文件中。这是添加 Python 辅助函数的最佳位置——既被导出到 Python，又不需要单独创建 `.cpp` 源文件。

### 类型映射系统（Typemaps）

SWIG 的类型映射（Typemap）是其最强大也最复杂的特性。它允许精细控制 C/C++ 类型与 Python 类型之间的转换规则。

在本项目中，默认的 `char* ↔ bytes` 映射导致 Python 端必须显式编解码。为了解决这个问题，我们曾尝试添加自定义 typemap（但发现与 SWIG 默认代码冲突，最终选择了保留 bytes 方案）：

```swig
// 尝试的自定义 typemap（因与 SWIG 内部 m 产生冲突而弃用，但展示了概念）
// Python str → const char*（参数转换）
%typemap(in) const char* {
  if ($input == Py_None) {
    $1 = NULL;
  } else if (PyUnicode_Check($input)) {
    $1 = PyUnicode_AsUTF8($input);
  } else {
    SWIG_exception_fail(SWIG_TypeError, "expected str or None");
  }
}

// const char* → Python str（返回值转换）
%typemap(out) const char* {
  if ($1) {
    $result = PyUnicode_FromString($1);
  } else {
    $result = Py_None;
    Py_INCREF(Py_None);
  }
}
```

Typemap 冲突的原因：SWIG 在 Python 3 模式下已有默认的 `char*` 处理逻辑（声明 `argN` 和 `allocN` 变量并在函数调用后清理）。自定义 typemap 的变量命名与 SWIG 内部机制不兼容，导致编译错误。正确做法是使用 `%typemap(in, noblock=1)` 或完整替换 `in`、`argout`、`freearg` 三个 typemap。

### 输出文件结构

SWIG 生成两个关键文件：

**1. `_engine_swig.pyd`**（Windows）或 `_engine_swig.so`（Linux）
- 编译后的原生 C 扩展模块
- 包含所有包装函数的实现
- 其符号（函数）通过 `engine_swig.py` 调用

**2. `engine_swig.py`**
- 自动生成的纯 Python 文件
- 提供代理对象和 Python 端转换逻辑
- 当 Python 执行 `import engine_swig` 时，首先加载此文件，它再导入 `_engine_swig`

生成文件的关系链：
```
Python: import engine_swig
  → engine_swig.py (Python 代理层)
    → import _engine_swig (C 扩展)
      → enginePYTHON_wrap.cxx (包装函数)
        → engine_c_api.h 中声明的 C 函数
          → engine 库 (C++ 实现)
```

## 实现复杂度分析

### 代码量

| 组件 | 行数 | 描述 |
|------|------|------|
| `engine.i` | 36 行 | SWIG 接口定义 |
| `CMakeLists.txt` | 32 行 | CMake 构建配置（比其他方案多，因需 SWIG 特殊配置） |
| `demo.py` | 78 行 | Python 示例（含 encode/decode 辅助函数） |
| 生成代码 | ~4200 行 | SWIG 自动生成，不需维护 |

SWIG 的人写代码最少（36 行 `.i`），但自动生成的包装代码最庞大（4200+ 行 C++）。

### 学习曲线

**SWIG 的学习曲线呈"先陡后平"形状**。初始障碍包括：

1. **理解 `.i` 文件的语法**：`%{ %}`、`%include`、`%inline`、`%module` 等指令需要学习
2. **TypeMap 调试**：当类型转换出错时，需要理解 SWIG 生成代码的内部才能定位问题
3. **构建系统集成**：CMake 的 `UseSWIG` 模块行为有时不直观——例如 SWIG 包含路径由 `SWIG_FLAGS` source property 而非 `target_include_directories` 控制
4. **Python 版本问题**：SWIG 4.x 终于将 Python 3 作为默认，但旧的教程和文档大多基于 Python 2，信息混杂

但一旦越过初始障碍，SWIG 的复杂度不会再显著增加——因为大部分工作已经是"写 C 头文件 + `%include`"。

### 实际开发中遇到的问题

本项目中遇到的具体问题：

1. **SWIG 找不到 `%include` 的头文件**：解决方式是设置 `SWIG_FLAGS: -I${CMAKE_SOURCE_DIR}/engine/include`（而非期望 `target_include_directories` 对 SWIG 生效）。

2. **`-py3` 标志被弃用**：SWIG 4.x 忽略 `-py3`（Python 3 已是默认），产生烦人的警告。移除即可。

3. **`int64_t` 未正确映射**：默认情况下被当作不透明指针。需要 `%include "stdint.i"`。

4. **Python `str` → `const char*` 自动转换失败**：这是 SWIG 4.x 的预期行为——`char*` 映射为 Python `bytes`。在 Demo 中通过 `_enc()`/`_dec()` 辅助函数处理。

### 调试体验

调试 SWIG 绑定的挑战在于多了一个中间层：
- SWIG 生成代码中的错误信息不友好（大型自动生成文件，行号无意义）
- 需要同时理解 `.i` 文件和生成的 `.cxx` 文件
- Python traceback 通常能正确定位到 SWIG 包装函数，但排查根源需要查看生成的 C++ 代码

## 易用性评估

### Python 端使用

```python
import engine_swig

# 注意：字符串参数需要编码为 bytes
engine = engine_swig.engine_create_and_init(b'{"app": "swig_demo"}')

initialized = engine_swig.engine_is_initialized(engine)
print(f"Engine initialized: {bool(initialized)}")

# scene_create 的参数也是 bytes
scene = engine_swig.scene_create(engine, b"MainScene")

# 创建 GameObjects
player = engine_swig.go_create(scene, b"Player")
enemy = engine_swig.go_create(scene, b"Enemy")

# 获取名称（返回 bytes，需要解码）
pname = engine_swig.go_name(player).decode("utf-8")
pid = engine_swig.go_id(player)   # int64_t 正确映射为 Python int
print(f"Objects: {pname} (id={pid})")

# 添加组件
t_comp = engine_swig.go_add_component(player, b"Transform")
ai_comp = engine_swig.go_add_component(enemy, b"AI")
print(engine_swig.component_type_name(t_comp).decode("utf-8"))  # "Transform"

# 批量生成
engine_swig.engine_mass_spawn(engine, b"MainScene", 10, b"SwarmUnit")
count = engine_swig.scene_object_count(scene)
print(f"After mass spawn: {count} objects")

# 更新循环
for i in range(3):
    engine_swig.engine_update(engine, 0.016)

engine_swig.engine_shutdown(engine)
engine_swig.engine_destroy(engine)
```

### 编码辅助层

为了简化 Python 端使用，可以在 `.i` 文件中添加编码辅助函数：

```swig
%inline %{
  // 在 SWIG 层处理编码
  #include <Python.h>
  // ... 但 typemap 冲突使这种方案复杂化，本项目选择了在 Python 侧处理
%}
```

或者通过 Python wrapper 隐藏 bytes 细节：
```python
# 可在上层包装中处理编解码
class EngineWrapper:
    def __init__(self, config_json="{}"):
        self._handle = engine_swig.engine_create_and_init(
            config_json.encode("utf-8"))
    def create_scene(self, name):
        return engine_swig.scene_create(self._handle, name.encode("utf-8"))
```

### 优点总结

1. **多语言原生支持**：同一 `.i` 文件可生成 20+ 种语言的绑定，这是 SWIG 不可替代的优势
2. **最小的人类代码量**：仅需 36 行 `.i` 文件即可绑定完整 C API
3. **自动从 C 头文件生成**：`%include "c_api.h"` 即可，无需逐个注册函数
4. **成熟稳定**：近 30 年的开发和测试，处理了大量边界情况
5. **适合 C 风格 API**：对于纯 C 的 ABI（opaque handles + free functions），SWIG 是最自然的方案
6. **构建系统集成**：CMake 内置 `UseSWIG` 模块，支持良好

### 缺点总结

1. **C++ 模板支持有限**：`%template` 指令需要为每个实例化显式声明，不像 pybind11 那样自然
2. **生成的代码不可读**：4200 行自动生成的 C++ 包装代码难以理解和调试
3. **类型系统不灵活**：自定义类型转换需要学习 typemap 语法
4. **Python 3 bytes/str 问题**：默认 `char* ↔ bytes` 映射不符合 Python 程序员的直觉预期
5. **构建时间**：SWIG 预处理 + 生成的代码编译比直接编写的绑定稍长
6. **调试困难**：错误可能出现在 `.i` 文件、生成的 `.cxx` 文件或 Python 层，排查链较长

## 编译、安装与使用

### 编译

```bash
cd CppPy
python scripts/manage.py setup              # 自动下载 swigwin 到 3rdparty/swig-install/
python scripts/manage.py build              # 编译所有方案（或 --scheme swig）
```

编译产物位于 `dist/<Config>/engine_swig/`：

```
dist/Debug/engine_swig/
├── __init__.py                  # SWIG 生成的 Python 包装器（可直接阅读）
├── _engine_swig.pyd             # SWIG 编译的 C 扩展
└── py.typed
```

### 安装与使用

将 `dist/<Config>/` 加入 `PYTHONPATH` 后即可导入：

```bash
export PYTHONPATH="$(pwd)/dist/Debug"
```

```python
import engine_swig
# SWIG 包装的是纯 C API，函数名直接对应 c_api.h
engine = engine_swig.engine_create_and_init('{"app": "demo"}')
# ...
```

注意：SWIG 4.x 默认将 `char*` 映射为 Python `bytes`，字符串参数需要 `.encode('utf-8')`。

### 打包分发

```bash
python scripts/manage.py package --scheme swig --config Release
# 产物: dist/engine_swig-0.1.0.zip
```

## 物理文件与 API 文档

### 产物物理文件

SWIG 方案产生**两个**关键文件：

| 文件 | 类型 | 说明 |
|------|------|------|
| `engine_swig/__init__.py` | **纯 Python** 包装文件 | SWIG 生成的 `engine_swig.py` 复制而来，作为包的入口，可直接阅读 |
| `engine_swig/_engine_swig.pyd` | **二进制** C 扩展模块 | SWIG 编译生成的粘合代码，放在包内以支持 SWIG 4.4 的相对导入 |
| `engine_swig/py.typed` | PEP 561 标记 | 告知类型检查器此包有类型信息 |

### Python 如何发现和加载

当用户 `import engine_swig` 时：

1. Python 在 `PYTHONPATH` 中找到 `engine_swig/` 包目录
2. 执行 `engine_swig/__init__.py`（即 SWIG 生成的包装器代码）
3. SWIG 4.4+ 检测到自己在包内，使用 `from . import _engine_swig` 相对导入找到包内的 `_engine_swig.pyd` 并加载

因此**两个文件必须在同一目录**。在多配置生成器下，CppPy 使用 `$<TARGET_FILE_DIR:engine_swig>` 生成器表达式确保包装 `.py` 被复制到与 `.pyd` 相同的配置子目录。

### API 文档方案

SWIG 本身不生成 `.pyi` 类型存根。但有三种互补的方式提供 API 文档：

#### 方式一：SWIG 自动 docstring（已启用）

在 `.i` 文件中添加 `%feature("autodoc", "1")` 后，生成的 `engine_swig.py` 自带函数签名 docstring：
```python
# engine_swig.py (生成结果)
def engine_create_and_init(config_json):
    r"""engine_create_and_init(char const * config_json) -> void *"""
    return _engine_swig.engine_create_and_init(config_json)
```

用户可以在 Python 终端使用 `help(engine_swig)` 查看。

#### 方式二：直接阅读 engine_swig.py（推荐）

`engine_swig.py` 本身是纯 Python 代码，人类可读。所有暴露的函数都在文件中清晰列出。用户可以用任何编辑器打开浏览 API。

#### 方式三：mypy stubgen（有限支持）

CppPy 尝试使用 mypy 的 `stubgen` 为 SWIG 模块生成 `.pyi`：
```bash
stubgen -m engine_swig -o <output_dir>/
```
但 SWIG 包装器的绝对导入 `import _engine_swig` 会导致 stubgen 报错：`No parent module -- cannot perform relative import`。这是 SWIG 生成的包装器结构导致的已知限制。因此 CppPy 不依赖 stubgen，而是创建 `py.typed` 标记文件并建议用户直接阅读 `engine_swig.py`。

#### 方式四：Doxygen 注释传递（可选）

如果 C 头文件中有 Doxygen 注释，SWIG 支持通过 `-doxygen` 标志将其转换为 Python docstring：
```swig
// 在 .i 文件中
%feature("autodoc", "1");  // 生成函数签名 docstring
// 编译时: swig -c++ -python -doxygen engine.i
```

### 用户可见效果

- `help(engine_swig)` 显示所有导出函数的签名列表
- `engine_swig.py` 可直接在编辑器中打开以浏览完整 API
- `py.typed` 标记文件告知类型检查器此包有类型信息

## 适用场景推荐

SWIG 最适合以下场景：

- **需要将同一 C/C++ 库暴露给多种编程语言** 的跨语言项目
- **C 风格 API**（opaque handles, free functions）包装——SWIG 对此类 API 的支持最为自然
- **大型遗留 C/C++ 代码库** 的 Python 化——`%include` 头文件即可快速生成绑定
- **团队不希望维护手写绑定代码**——绑定代码由 SWIG 自动生成，只需维护 `.i` 文件

不太适合以下场景：

- **高度模板化的现代 C++ 库**——每个模板实例化都需要手动 `%template`
- **对 Python 端 API 体验有极致要求**——SWIG 生成的 Python API 有"C 味"
- **需要频繁迭代绑定配置**——SWIG 的生成 → 编译周期比直接编写的方案慢
