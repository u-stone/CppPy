# CFFI + C API — ABI 级 Python/C 互操作方案详解

## 概述

CFFI（C Foreign Function Interface）是 Python 与 C 语言互操作的两种主要方式之一（另一种是 ctypes）。与 pybind11/nanobind/Cython 这些"需要编译"的方案不同，CFFI 在最低层次工作——直接通过 C ABI（Application Binary Interface）调用动态链接库中的函数。这意味着 CFFI 不需要 C++ 编译器来生成绑定，不需要模板实例化，甚至不需要头文件（虽然通常会通过它来解析声明）。

本项目的 CFFI 方案采用了一种混合架构：
1. **C 共享库**（`engine_c.dll` / `libengine_c.so`）：将引擎功能编译为独立的动态链接库，所有需要暴露的函数使用 `extern "C"` 导出，避免 C++ name mangling。
2. **ctypes 桥接层**（`cffi_bridge.py`）：使用 Python 标准库 `ctypes` 模块加载共享库，声明每个函数的参数和返回类型。
3. **可选的 CFFI 构建器**（`cffi_build.py`）：使用 `cffi` 第三方包解析 C 头文件并生成 ABI 模式的绑定模块。

这种架构是 ABI 稳定性最高的方案——只要共享库的 `extern "C"` 接口不变，Python 端不需要重新编译任何东西。

## 依赖环境

### 系统要求

- **C 共享库的编译器**：支持 C++17 的 MSVC、GCC 8+、或 Clang 7+（仅用于编译 `engine_c` 共享库）
- **CMake**：3.20+
- **Python**：3.6+（`ctypes` 是标准库，无需额外安装）
- **Windows 额外要求**：需要 `.def` 文件或 `__declspec(dllexport)` 来显式导出 DLL 符号

### Python 包

`ctypes` 是 Python 标准库的一部分，开箱即用。CFFI 是可选的增强：

```bash
pip install cffi>=1.16.0  # 可选，仅在使用 cffi_build.py 时
```

### 构建系统集成

CFFI 方案的 CMake 配置分为两步：构建共享库和复制 Python 包装文件。

**第一步：构建 C 共享库**

```cmake
# bindings/cffi/CMakeLists.txt

# ① 构建共享库（而非静态链接）
add_library(engine_c SHARED src/cffi_c_impl.cpp)

# ② 包含引擎头文件以便调用 C API
target_include_directories(engine_c PRIVATE ${CMAKE_SOURCE_DIR}/engine/include)

# ③ 链接引擎静态库和系统线程库
target_link_libraries(engine_c PRIVATE engine Threads::Threads)

# ④ Windows 需要 .def 文件来显式导出符号
if(WIN32)
  target_sources(engine_c PRIVATE src/engine_c.def)
endif()

# ⑤ 输出到统一位置
set_target_properties(engine_c PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/_build/cffi"
)

# ⑥ POST_BUILD: 组装 Python 包到 dist/<Config>/enginecffi/
set(_pkg "${CMAKE_SOURCE_DIR}/dist/$<CONFIG>/enginecffi")
add_custom_command(TARGET engine_c POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E make_directory "${_pkg}"
  COMMAND ${CMAKE_COMMAND} -E rename "$<TARGET_FILE:engine_c>" "${_pkg}/engine_c$<TARGET_FILE_SUFFIX:engine_c>"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${CMAKE_CURRENT_SOURCE_DIR}/python/cffi_bridge.py"
    "${_pkg}/"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${CMAKE_CURRENT_SOURCE_DIR}/python/cffi_build.py"
    "${_pkg}/"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${CMAKE_CURRENT_SOURCE_DIR}/python/__init__.py"
    "${_pkg}/"
)
```

**第二步：理解共享库实现**

`cffi_c_impl.cpp` 是所有方案中最简单的绑定源文件——仅 11 行：

```cpp
// bindings/cffi/src/cffi_c_impl.cpp
// Re-exports the C API functions as a standalone shared library (engine_c).
// The C API functions are already defined in engine/src/c_api.cpp and
// linked via the engine static library. This file just provides the
// compilation unit and any additional cffi-specific C thunks.

#include "engine/c_api.h"

// No additional code needed — the engine static library provides all
// extern "C" symbols, and linking them into this shared library makes
// them available via dlopen / LoadLibrary for cffi/ctypes.
```

这个文件的"存在"本身就是这个方案精髓的体现：C API 的所有实现都在 `engine/src/c_api.cpp`（209 行）中，通过 `engine` 静态库链接，这个文件只是确保 CMake 有一个源文件可以编译为共享库。

**Windows 符号导出**

在 Windows 上，DLL 默认不导出符号。需要 `.def` 文件显式声明：

```
; bindings/cffi/src/engine_c.def
LIBRARY engine_c
EXPORTS
  engine_create
  engine_destroy
  engine_init
  engine_shutdown
  engine_is_initialized
  engine_update
  scene_create
  scene_destroy
  scene_get_by_name
  scene_object_count
  go_create
  go_destroy
  go_name
  go_id
  go_add_component
  go_remove_component
  go_get_component
  component_type_name
  engine_mass_spawn
  engine_subscribe
  engine_unsubscribe
  engine_publish_event
```

这是 Windows 上 CFFI/ctypes 方案的"额外成本"——Linux/macOS 默认导出所有符号，而 Windows 需要显式声明。

## 核心技术细节

### C ABI 设计原则

CFFI 方案的基石是 C API 的 ABI 兼容性。`engine/c_api.h` 的设计原则：

```c
// engine/include/engine/c_api.h

#ifndef ENGINE_C_API_H_
#define ENGINE_C_API_H_

// ① Pure-C ABI，所有类型都是 opaque handles (void*)
// ② 设计用于 cffi/ctypes 消费
// ③ 签名中不含任何 STL 类型

#ifdef __cplusplus
extern "C" {  // ④ 禁用 C++ name mangling，确保 ABI 稳定性
#endif

#include <stdint.h>

// ⑤ 所有句柄都是 void* — ctypes 直接映射为 c_void_p
typedef void* EngineHandle;
typedef void* SceneHandle;
typedef void* GameObjectHandle;
typedef void* ComponentHandle;

// ⑥ 回调函数类型（函数指针）— ctypes 映射为 CFUNCTYPE
typedef void (*EventCallback)(const char* event_type, const char* json_data,
                              void* user_data);

// ⑦ 生命周期管理：create/init → update → shutdown/destroy
EngineHandle engine_create(void);
void engine_destroy(EngineHandle engine);
int engine_init(EngineHandle engine, const char* config_json);
void engine_shutdown(EngineHandle engine);
int engine_is_initialized(EngineHandle engine);

// ⑧ 核心更新循环
void engine_update(EngineHandle engine, float dt);

// ⑨ Scene/GameObject/Component 的 CRUD 操作
SceneHandle scene_create(EngineHandle engine, const char* name);
SceneHandle scene_get_by_name(EngineHandle engine, const char* name);
int scene_object_count(SceneHandle scene);

GameObjectHandle go_create(SceneHandle scene, const char* name);
const char* go_name(GameObjectHandle go);
int64_t go_id(GameObjectHandle go);

// ⑩ 组件系统：按名称（字符串）创建和查找
ComponentHandle go_add_component(GameObjectHandle go, const char* type_name);
ComponentHandle go_get_component(GameObjectHandle go, const char* type_name);
const char* component_type_name(ComponentHandle comp);

// ⑪ 批量操作：演示原始数组
void engine_mass_spawn(EngineHandle engine, const char* scene_name, int count,
                       const char* prefix);

// ⑫ 事件系统：C 函数指针回调
int engine_subscribe(EngineHandle engine, const char* event_type,
                     EventCallback callback, void* user_data);
void engine_unsubscribe(EngineHandle engine, int subscription_id);
void engine_publish_event(EngineHandle engine, const char* event_type,
                          const char* json_data);

#ifdef __cplusplus
}
#endif

#endif  // ENGINE_C_API_H_
```

**C API 设计要点**：

1. **Opaque Handle 模式**：所有 C++ 对象（EngineFacade、Scene、GameObject）通过 `void*` 传递。Python 端看到的永远是不透明指针，无法直接访问内部字段。

2. **无 STL 泄漏**：`const char*` 代替 `std::string`，`int` 代替 `size_t`（`size_t` 在不同平台宽度不同会导致 ctypes 映射问题），`int64_t` 代替 `long long`。

3. **返回码约定**：`int` 返回值用于 Boolean（1=成功/True, 0=失败/False），方便 ctypes 直接映射为 `c_int`。

4. **指针稳定性**：`go_name()` 返回 `const char*` 指向对象内部存储的 C 字符串指针，在其生命周期内有效。

### C API 实现 — 从 C++ 到 C 的桥梁

`engine/src/c_api.cpp` 是 C API 到 C++ 引擎内部的"薄翻译层"：

```cpp
// engine/src/c_api.cpp — C API 实现（节选）

namespace {
// ① 内部状态结构体 — 包含 C++ 引擎实例
struct CEngineState {
  engine::EngineFacade facade;
  std::unordered_map<int, EventCallback> callbacks;
  std::mutex callback_mutex;
  int next_sub_id = 1;
};

// ② 类型转换辅助函数 — void* ↔ C++ 类型
CEngineState* ToState(EngineHandle h) {
  return static_cast<CEngineState*>(h);
}
engine::Scene* ToScene(SceneHandle h) {
  return static_cast<engine::Scene*>(h);
}
engine::GameObject* ToGO(GameObjectHandle h) {
  return static_cast<engine::GameObject*>(h);
}
}  // namespace

extern "C" {

// ③ 构造 — new CEngineState，封装 EngineFacade
EngineHandle engine_create(void) {
  std::cout << "[C API] engine_create" << std::endl;
  auto* state = new CEngineState();
  return static_cast<EngineHandle>(state);
}

// ④ 析构 — delete 释放内存
void engine_destroy(EngineHandle engine) {
  std::cout << "[C API] engine_destroy" << std::endl;
  delete ToState(engine);
}

// ⑤ 翻译调用 — const char* → std::string → C++ Init
int engine_init(EngineHandle engine, const char* config_json) {
  return ToState(engine)->facade.Init(config_json ? config_json : "{}") ? 1 : 0;
}

// ⑥ 组件创建 — 字符串比较选择具体类型
ComponentHandle go_add_component(GameObjectHandle go, const char* type_name) {
  if (!type_name) return nullptr;
  auto* obj = ToGO(go);
  if (std::strcmp(type_name, "Transform") == 0) {
    return static_cast<ComponentHandle>(
        &obj->AddComponent<engine::TransformComponent>());
  } else if (std::strcmp(type_name, "AI") == 0) {
    return static_cast<ComponentHandle>(
        &obj->AddComponent<engine::AIComponent>());
  }
  return nullptr;
}

}  // extern "C"
```

这个实现的"翻译层"模式：
- C++ 对象创建（`new`）→ `void*` 返回
- C 字符串 → `std::string` → C++ 方法调用
- C++ 方法返回值 → C 兼容类型
- 生命周期完全通过 `create`/`destroy` 函数对管理

### ctypes 桥接层 — Python 端包装

`cffi_bridge.py` 是 Python 端的核心文件。它使用纯 Python（`ctypes` 标准库）实现以下功能：

```python
# bindings/cffi/python/cffi_bridge.py

import os
import ctypes
import platform

# ① 加载共享库
_lib_dir = os.path.dirname(__file__)
if platform.system() == "Windows":
    _lib = ctypes.CDLL(os.path.join(_lib_dir, "engine_c.dll"))
else:
    _lib = ctypes.CDLL(os.path.join(_lib_dir, "libengine_c.so"))

# ② 声明每个函数的签名（参数类型 + 返回类型）
# 这是 ctypes 的关键步骤 —— 没有它，Python 无法正确传递和接收参数

_lib.engine_create.argtypes = []               # 无参数
_lib.engine_create.restype = ctypes.c_void_p   # 返回 void*

_lib.engine_init.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
_lib.engine_init.restype = ctypes.c_int        # 返回 int (作为 bool)

_lib.engine_update.argtypes = [ctypes.c_void_p, ctypes.c_float]
_lib.engine_update.restype = None              # 返回 void

_lib.go_id.argtypes = [ctypes.c_void_p]
_lib.go_id.restype = ctypes.c_int64            # 返回 int64_t

_lib.go_name.argtypes = [ctypes.c_void_p]
_lib.go_name.restype = ctypes.c_char_p         # 返回 const char* (→ bytes)

# ③ 回调函数类型定义
EventCallback = ctypes.CFUNCTYPE(
    None,                    # 返回类型: void
    ctypes.c_char_p,         # 参数1: const char* event_type
    ctypes.c_char_p,         # 参数2: const char* json_data
    ctypes.c_void_p          # 参数3: void* user_data
)

_lib.engine_subscribe.argtypes = [
    ctypes.c_void_p, ctypes.c_char_p, EventCallback, ctypes.c_void_p
]
_lib.engine_subscribe.restype = ctypes.c_int
```

**ctypes 类型映射表**：

| C 类型 | ctypes 类型 | Python 类型 |
|--------|-------------|-------------|
| `void*` | `c_void_p` | `int` 或 `None` |
| `int` | `c_int` | `int` |
| `int64_t` | `c_int64` | `int` |
| `float` | `c_float` | `float` |
| `const char*` | `c_char_p` | `bytes` |
| `void` | `None` (restype) | `None` |
| `void (*)(...)` | `CFUNCTYPE` | callable |

### Pythonic 包装类

原始 ctypes 调用很不 Pythonic。`cffi_bridge.py` 提供了一层 Python 包装来改善 API：

```python
# Python 包装类 — 隐藏 ctypes 的粗糙细节

class Engine:
    """Wrapper around C EngineHandle — ctypes-based."""

    def __init__(self, config_json="{}"):
        self._handle = _lib.engine_create()
        self._callbacks = {}
        self._callback_refs = {}  # 防止 ctypes 回调被 GC 回收

    def init(self, config_json="{}"):
        return bool(_lib.engine_init(
            self._handle, config_json.encode('utf-8')))

    def shutdown(self):
        _lib.engine_shutdown(self._handle)

    @property
    def is_initialized(self):
        return bool(_lib.engine_is_initialized(self._handle))

    def update(self, dt):
        _lib.engine_update(self._handle, dt)

    def create_scene(self, name):
        h = _lib.scene_create(self._handle, name.encode('utf-8'))
        return Scene(h, self._handle) if h else None

    def subscribe(self, event_type, callback):
        # ④ 在 Python 中构建 C 回调桥接
        def _bridge(evt_type, json_data, user_data):
            et = evt_type.decode('utf-8') if evt_type else ''
            jd = json_data.decode('utf-8') if json_data else ''
            callback(jd)

        cb = EventCallback(_bridge)
        self._callback_refs[id(callback)] = cb  # ⑤ 防止 GC
        return _lib.engine_subscribe(
            self._handle, event_type.encode('utf-8'), cb, None
        )

    def publish_event(self, event_type, data):
        _lib.engine_publish_event(
            self._handle, event_type.encode('utf-8'), data.encode('utf-8')
        )

    def __del__(self):
        if self._handle:
            _lib.engine_destroy(self._handle)

class GameObject:
    """Wrapper around a C GameObjectHandle."""

    def __init__(self, handle, engine_handle):
        self._handle = handle
        self._engine_handle = engine_handle

    @property
    def name(self):
        result = _lib.go_name(self._handle)
        return result.decode('utf-8') if result else ""

    @property
    def id(self):
        return _lib.go_id(self._handle)

    def add_component(self, type_name):
        h = _lib.go_add_component(self._handle, type_name.encode('utf-8'))
        return Component(h) if h else None
```

**ctypes 回调的关键陷阱（④⑤）**：

- `EventCallback(_bridge)` 创建一个 C 函数指针，指向 Python 函数 `_bridge`。
- 如果这个 C 函数指针被 Python GC 回收，后续 C 代码在事件触发时调用该指针将导致 segfault。
- 解决方法是将 ctypes callback 对象保存在 `self._callback_refs` 字典中（⑤），防止其被 GC。

### CFFI 模块（可选替代方案）

`cffi` 第三方包提供了比 ctypes 更高级的接口，可以直接从 C 头文件生成绑定：

```python
# bindings/cffi/python/cffi_build.py — 可选的 cffi 构建器

from cffi import FFI

ffi = FFI()

# 读取 C API 头文件
header_path = "engine/include/engine/c_api.h"
with open(header_path) as f:
    header_content = f.read()

# 过滤 C++ 语法（cffi 只理解纯 C 声明）
lines = []
for line in header_content.splitlines():
    if line.startswith("#include"):  # 跳过 #include
        continue
    if 'extern "C"' in line:         # 跳过 extern "C"
        continue
    lines.append(line)

clean_header = "\n".join(lines)

# 将纯 C 声明喂给 cffi
ffi.cdef(clean_header)

# 编译或 ABI 模式加载
ffi.set_source("_enginecffi", None)
ffi.compile()
```

cffi 有两种模式：
- **API 模式**（`ffi.set_source` + `ffi.compile`）：需要 C 编译器，生成 `.pyd`/`.so` 文件，在编译时验证声明完整性。
- **ABI 模式**（`ffi.dlopen`）：纯运行时，不编译，直接从 `.so`/`.dll` 加载，类似于 ctypes。

## 实现复杂度分析

### 代码量

| 组件 | 行数 | 描述 |
|------|------|------|
| `c_api.h` | 64 行 | 纯 C 头文件（API 契约）|
| `c_api.cpp` | 209 行 | C API 实现（C → C++ 翻译） |
| `cffi_c_impl.cpp` | 11 行 | 共享库入口 |
| `engine_c.def` | 23 行 | Windows DLL 导出符号 |
| `cffi_bridge.py` | 199 行 | Python ctypes 包装 |
| `cffi_build.py` | 51 行 | 可选的 cffi 构建器 |
| `CMakeLists.txt` | 25 行 | 构建配置 |

CFFI 方案的总代码量最高（582 行），但这分散在多个层次：C 头文件、C 实现、Python ctypes 包装、Windows 导出文件。每一层都独立且职责清晰。

### 学习曲线

CFFI/ctypes 的学习曲线呈现"入门低，精通中"的特点：

**入门容易**：
- ctypes 是 Python 标准库，无需额外安装
- 基础用法（加载 DLL、调用简单函数）只需几分钟
- 无需学习新语言或 DSL

**精通需要理解**：
1. **C 类型到 ctypes 类型的准确映射**：`c_int` vs `c_long` vs `c_int64`，平台差异（32位/64位）对 `c_long` 的影响
2. **回调函数生命周期**：C 函数指针的 GC 问题
3. **内存管理**：谁负责释放 `const char*` 返回的字符串？C 函数返回的 heap 指针
4. **结构体布局**：如果 C API 暴露结构体，需要 `ctypes.Structure` 精确匹配对齐和字段顺序
5. **Windows 差异**：`stdcall` vs `cdecl` 调用约定，`.def` 文件和 `__declspec(dllexport)`

### 调试体验

ctypes 的错误处理与 Python 异常系统集成良好：

- **参数类型错误**：ctypes 抛出 `ArgumentError`，指出期望类型和实际类型
- **找不到函数**：`AttributeError`，提示 DLL 中不存在该符号
- **Segfault**：最可怕的情况——通常是参数类型声明错误或内存管理 bug。需要用 C 调试器分析
- **回调 GC 后崩溃**：Python 错误信息不明确指出是 callback 被 GC。现象是突然的 segfault

## 易用性评估

### Python 端使用

```python
# 方式一：直接使用 Pythonic 包装类（推荐）
from cffi_bridge import Engine

engine = Engine()
engine.init('{"app": "cffi_demo"}')

scene = engine.create_scene("MainScene")
player = scene.create_object("Player")
enemy = scene.create_object("Enemy")

print(f"Objects: {player.name} (id={player.id}), {enemy.name}")  # names are str!

t = player.add_component("Transform")
print(f"Component: {t.type_name}")  # "Transform"

engine.subscribe("damage", lambda data: print(f"Damage: {data}"))
engine.publish_event("damage", '{"amount": 60}')

for i in range(3):
    engine.update(0.016)

engine.mass_spawn("MainScene", 8, "CffiObj")
print(f"After mass spawn: {scene.object_count} objects")

engine.shutdown()
```

```python
# 方式二：直接使用 ctypes 底层 API（无包装类）
import ctypes

lib = ctypes.CDLL("engine_c.dll")
lib.engine_create.argtypes = []
lib.engine_create.restype = ctypes.c_void_p

engine = lib.engine_create()  # 返回一个整数（指针地址）
lib.engine_init(engine, b'{"app": "raw_ctypes"}')  # 手动编码
lib.engine_update(engine, 0.016)
lib.engine_destroy(engine)
```

两种方式展示了 CFFI 方案的灵活性——可以写高层 Pythonic 包装，也可以直接下到 `int` 作为指针的层次。

### 优点总结

1. **零编译依赖**：Python 端完全不需要 C/C++ 编译器，`import ctypes` 即可
2. **跨 Python 版本**：ctypes API 自 Python 2.5 以来保持稳定
3. **ABI 稳定性**：共享库的 C ABI 极其稳定。更新引擎实现不需要重新编译 Python 端的包装
4. **分发简单**：只需 `.dll`/`.so` + `.py` 文件，无需关心 Python 版本特定的编译产物（如 `.cp312-win_amd64.pyd`）
5. **调试透明**：可以随时在 Python REPL 中直接调用 C 函数
6. **进程隔离潜力**：`multiprocessing` 可以与 CFFI 共享库配合使用（每个进程独立加载 DLL）

### 缺点总结

1. **C API 设计额外工作**：需要维护一个纯 C 的 ABI 层（`c_api.h` + `c_api.cpp`），这本身是工程开销
2. **无 STL 支持**：不能暴露 `std::vector`、`std::shared_ptr`、模板函数
3. **Opaque handles 限制**：Python 端无法直接访问 C++ 对象内部状态
4. **性能开销**：每次跨 C/Python 边界调用都是 FFI 调用，比 pybind11 的 inline 包装慢
5. **字符串编解码成本**：`const char*` ↔ `str` 的双向编码
6. **平台差异**：Windows 需要 `.def` 文件，`c_long` 宽度因平台而异
7. **类型安全缺失**：ctypes 的类型检查发生在运行时，而非编译时

## 编译、安装与使用

### 编译

```bash
cd CppPy
python scripts/manage.py setup
python scripts/manage.py build              # 或 --scheme cffi
```

编译产物位于 `dist/<Config>/enginecffi/`：

```
dist/Debug/enginecffi/
├── __init__.py                  # from .cffi_bridge import Engine, Scene, ...
├── cffi_bridge.py               # 手写的 Pythonic 包装器（ctypes）
├── cffi_bridge.pyi              # 手写类型存根
├── cffi_build.py                # CFFI builder（可选）
├── engine_c.dll                 # 纯 C 共享库
└── py.typed
```

### 安装与使用

将 `dist/<Config>/` 加入 `PYTHONPATH`：

```bash
export PYTHONPATH="$(pwd)/dist/Debug"
```

```python
import enginecffi
engine = enginecffi.Engine()
engine.init('{}')
```

注意：CFFI/ctypes 方案通过 `ctypes.CDLL` 加载 `engine_c.dll`，因此 `.py` 和 `.dll` 必须在同一目录。CppPy 的 CMake POST_BUILD 已自动处理这一点。

### 打包分发

```bash
python scripts/manage.py package --scheme cffi --config Release
# 产物: dist/enginecffi-0.1.0.zip
```

## 物理文件与 Python 类型存根 (`.pyi`)

### 产物物理文件

CFFI/ctypes 方案的产物结构与其他 4 种方案有本质区别——它不生成 Python C 扩展模块，而是：

| 文件 | 类型 | 说明 |
|------|------|------|
| `enginecffi/__init__.py` | 包入口，执行 `from .cffi_bridge import Component, Engine, GameObject, Scene` |
| `enginecffi/cffi_bridge.py` | **纯 Python 代码** | 手写的 Pythonic OOP 包装器，通过 `ctypes.CDLL()` 加载 `engine_c.dll` |
| `enginecffi/cffi_bridge.pyi` | **手写类型存根** | 手工维护的 `.pyi` 文件 |
| `enginecffi/engine_c.dll` | **纯 C 共享库** | 编译自 `cffi_c_impl.cpp`，只使用 `extern "C"` ABI |
| `enginecffi/py.typed` | PEP 561 标记 | 告知类型检查器此包有类型信息 |

### Python 如何发现和加载

```
用户代码: import enginecffi (将 dist/<Config>/ 加入 PYTHONPATH)
  └─ enginecffi/__init__.py: from .cffi_bridge import Engine, ...
       └─ cffi_bridge.py: _lib_dir = os.path.dirname(__file__)
            └─ ctypes.CDLL(os.path.join(_lib_dir, "engine_c.dll"))
                 └─ LoadLibrary() 加载 engine_c.dll
                      └─ _lib.engine_create() 调用 C 函数
```

**关键点**：`cffi_bridge.py` 通过 `os.path.dirname(__file__)` 确定自己的目录，然后在同目录下搜索 `engine_c.dll`。因此 `.py` 和 `.dll` 都在 `enginecffi/` 包内。CMake POST_BUILD 使用 `$<CONFIG>` 生成器表达式确保所有文件集结到 `dist/<Config>/enginecffi/`。

### 类型存根：手写方案

CFFI/ctypes 是所有 5 种方案中**唯一没有任何自动化存根生成的方案**。解决方案是手工编写并维护 `cffi_bridge.pyi` 文件：

```python
# bindings/cffi/python/cffi_bridge.pyi（手工维护）
class Engine:
    def __init__(self, config_json: str = "{}") -> None: ...
    def init(self, config_json: str = "{}") -> bool: ...
    def shutdown(self) -> None: ...
    def update(self, dt: float) -> None: ...
    def create_scene(self, name: str) -> Optional[Scene]: ...

class Scene:
    def create_object(self, name: str) -> Optional[GameObject]: ...
    @property
    def object_count(self) -> int: ...
```

**维护原则**：
- `.pyi` 文件是 `cffi_bridge.py` 的类型级镜像，不含实现
- 当 `cffi_bridge.py` 的公开 API 变化时，必须同步更新 `.pyi`
- 使用 `...`（Ellipsis）作为方法体，告诉类型检查器"签名仅用于检查"
- 搭配 `py.typed` 标记文件使 PEP 561 生效

**为什么不自动生成**：ctypes 的类型系统在运行时才能确定（`argtypes` / `restype` 是运行时属性），没有编译期类型信息可供提取。CFFI 的 `ffi.cdef()` 有类型声明，但 CppPy 的 ctypes 路径不经过 CFFI 的 builder。

### 用户可见效果

- IDE 在用户 `import cffi_bridge` 时读取 `.pyi` 获得完整的类型提示
- 与手写纯 Python 库的体验一致
- 需要开发者手动维护来回同步 `.py` 和 `.pyi`——这是 CFFI/ctypes 的固有代价

## 适用场景推荐

CFFI + C API 最适合以下场景：

- **ABI 稳定性要求极高**：共享库接口一旦定义好基本不需要变化，但内部实现可能频繁更新
- **纯 Python 分发需求**：用户无需安装 C++ 编译器即可使用绑定
- **跨进程或多解释器环境**：需要 `multiprocessing` 或嵌入 Python 的场景
- **遗留 C 库的 Python 化**：虽然有 C++ 实现，但只需暴露 C 级别的 API
- **对编译产物格式敏感**：希望使用系统标准的 `.dll`/`.so` 而不是 Python 版本特定的 `.pyd`

不太适合以下场景：

- **需要暴露 C++ 模板 API**：模板函数、STL 容器在 C ABI 层无法表达
- **高性能要求**：跨 FFI 边界的调用开销不可忽容
- **面向对象的 Python API**：手动维护包装类比 pybind11 的自动生成工作量更大
- **频繁修改 API**：每次修改 C 函数签名都需要同步更新 Python 端的 `argtypes`/`restype`

## 五种方案对比总结

| 维度 | pybind11 | nanobind | SWIG | Cython | CFFI + C |
|------|----------|----------|------|--------|----------|
| **绑定代码量** | 110 行 | 112 行 | 36 行 (.i) | 169 行 (.pyx+.pxd) | 199 行 (.py) |
| **构建复杂度** | 低 | 低 | 中 | 高 | 中 |
| **运行时性能** | 高 | 最高 | 中 | 高 | 中低 |
| **STL 支持** | 极好 | 极好 | 有限 | 手动 | 无 |
| **多语言支持** | Python only | Python only | 20+ 语言 | Python only | C ABI (任意) |
| **C++ 模板** | 手动实例化 | 手动实例化 | %template | 手动 | 不支持 |
| **学习曲线** | 中 | 中低 | 中高 | 高 | 低 |
| **编译时间** | 中长 | 中 | 中 | 中 | 短 |
| **二进制体积** | 中 | 小 | 大 | 中 | 小 |
| **分发难度** | 需匹配 Python 版本 | 需匹配 Python 版本 | 需匹配 Python 版本 | 需匹配 Python 版本 | DLL 通用 |
| **成熟度** | 极成熟 | 较新 | 极成熟 | 极成熟 | 极成熟 |

选择建议：
- **个人项目/快速原型**：pybind11 — API 最友好
- **新项目/资源受限**：nanobind — pybind11 的下一代
- **多语言分发**：SWIG — 一次编写，到处绑定
- **科学计算/高性能**：Cython — 与 NumPy 生态深度融合
- **系统集成/ABI 稳定**：CFFI — 最小的分发复杂度
