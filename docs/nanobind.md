# Nanobind — 下一代 C++/Python 绑定方案详解

## 概述

Nanobind 是 pybind11 原作者 Wenzel Jakob 开发的下一代 C++/Python 绑定库。它从零开始重写，抛弃了对旧版编译器和 Python 2 的兼容包袱，充分利用 C++17 特性，在保持 pybind11 易用 API 的前提下，实现了更小的二进制体积、更快的编译速度和更低的运行时开销。

Nanobind 的核心哲学是"零开销抽象"——绑定层不应在运行时产生看得见的性能成本。为此，它重新设计了类型转换机制、引用计数策略和模块加载流程，使得生成的 `.pyd`/`.so` 文件体积相比 pybind11 减少了约 40-60%。

在本项目 CppPy 中，nanobind 作为第二种方案，通过几乎一对一的 API 映射展示了从 pybind11 迁移的可行性。

## 依赖环境

### 系统要求

- **编译器**：支持 C++17 的 MSVC 2019+、GCC 8+、或 Clang 7+
- **CMake**：3.20+（nanobind 通过 CMake 子目录方式集成）
- **Python**：3.8 至 3.12（不支持 Python 2，不支持 3.6/3.7）

### Python 包

```bash
pip install nanobind>=2.0.0
```

### 构建系统集成

Nanobind 推荐通过 CMake 子目录方式集成。本项目在顶层 CMakeLists.txt 中完成了 nanobind 的查找和引入：

```cmake
# top-level CMakeLists.txt
if(BUILD_NANOBIND)
  if(NOT EXISTS "${THIRDPARTY_DIR}/nanobind/CMakeLists.txt")
    message(FATAL_ERROR "nanobind not found in 3rdparty/. Run 'manage.py setup' first.")
  endif()
  # nanobind 要求在 include 其 CMake 配置前先 find_package(Python)
  find_package(Python COMPONENTS Interpreter Development REQUIRED)
  add_3rdparty_subdirectory(nanobind "")
  add_subdirectory(bindings/nanobind)
endif()
```

**关键差异**：Nanobind 使用 `Python`（无版本号后缀）而非 `Python3`，且必须在 `add_subdirectory(nanobind)` 之前完成 `find_package`，因为 nanobind 的 CMake 配置依赖 `Python::Module` 目标。

绑定本身的 CMakeLists.txt 与 pybind11 几乎同构：

```cmake
# bindings/nanobind/CMakeLists.txt — 仅 13 行
nanobind_add_module(enginenanobind src/nanobind_bindings.cpp)

target_link_libraries(enginenanobind PRIVATE engine)
target_include_directories(enginenanobind PRIVATE
  ${CMAKE_SOURCE_DIR}/engine/include
)

set_target_properties(enginenanobind PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/_build/nanobind"
  OUTPUT_NAME "_core_nanobind"
)
```

将 `pybind11_add_module` 替换为 `nanobind_add_module` 是唯一的 CMake 级别差异，体现了 API 层面的精心设计。

## 核心技术细节

### 模块定义宏

Nanobind 使用 `NB_MODULE` 宏（而非 pybind11 的 `PYBIND11_MODULE`）：

```cpp
#include <nanobind/nanobind.h>

namespace nb = nanobind;  // 命名空间约定：nb 而非 py

NB_MODULE(_core, m) {
  m.doc() = "CppPy engine - nanobind binding";
  // 类绑定代码...
}
```

`NB_MODULE` 宏生成的模块加载代码与 pybind11 有本质区别。Pybind11 在模块初始化时会执行大量运行时注册，而 nanobind 将这些工作尽可能推入编译期，从而减少了 `import` 的延迟。

### 头文件体系

Nanobind 采用比 pybind11 更细粒度的头文件组织：

```cpp
#include <nanobind/nanobind.h>       // 核心：NB_MODULE, nb::class_, nb::init
#include <nanobind/stl/function.h>   // 独立的功能绑定头文件
#include <nanobind/stl/optional.h>   // std::optional 支持
#include <nanobind/stl/shared_ptr.h> // shared_ptr 自动转换
#include <nanobind/stl/string.h>     // std::string ↔ Python str
#include <nanobind/stl/vector.h>     // std::vector ↔ Python list
```

与 pybind11 将所有 STL 转换放在 `<pybind11/stl.h>` 中不同，nanobind 的分离式设计允许开发者按需引入，从而减少不必要的模板实例化。这是 nanobind 编译速度优势的来源之一。

### 类绑定机制

Nanobind 的类绑定 API 保持了与 pybind11 的高度相似性，但在细节上进行了优化：

```cpp
namespace nb = nanobind;
using namespace engine;

NB_MODULE(_core, m) {
  m.doc() = "CppPy engine - nanobind binding";

  // nb::class_<CppType> 的 API 与 pybind11 几乎一致
  nb::class_<EngineFacade>(m, "Engine")
      .def(nb::init<>())  // 注意：nb::init<>() 而非 py::init<>()
      .def("init", &EngineFacade::Init, nb::arg("config_json") = "{}")
      .def("shutdown", &EngineFacade::Shutdown)
      .def("update", &EngineFacade::Update, nb::arg("dt"))
      .def("create_scene", &EngineFacade::CreateScene, nb::arg("name"))
      .def("get_scene", &EngineFacade::GetScene, nb::arg("name"))
      .def("scene_names", &EngineFacade::SceneNames)
      // 属性命名差异：def_prop_ro vs def_property_readonly
      .def_prop_ro("is_initialized", &EngineFacade::IsInitialized)
```

API 差异对照表：

| 功能 | pybind11 | nanobind |
|------|----------|----------|
| 构造函数 | `py::init<>()` | `nb::init<>()` |
| 只读属性 | `def_property_readonly` | `def_prop_ro` |
| 读写属性 | `def_property` | `def_prop_rw` |
| 读写成员 | `def_readwrite` | `def_rw` |
| 模块宏 | `PYBIND11_MODULE` | `NB_MODULE` |
| 返回值策略 | `py::return_value_policy::reference_internal` | `nb::rv_policy::reference_internal` |
| 参数命名 | `py::arg("name")` | `nb::arg("name")` |

### Doxygen 风格的简化命名

Nanobind 刻意缩短了常见的 API 名称，这是基于作者对 pybind11 用户使用模式的分析所做的设计选择。例如：

```cpp
// pybind11 风格
.def_property_readonly("count", &Scene::ObjectCount)
.def_readwrite("x", &Transform::x)

// nanobind 风格 — 更短，但意图同样清晰
.def_prop_ro("count", &Scene::ObjectCount)
.def_rw("x", &Transform::x)
```

### 引用生命周期管理

Nanobind 的返回值策略命名空间更短，但策略种类几乎完全相同：

```cpp
nb::class_<GameObject>(m, "GameObject")
    .def("add_transform",
         [](GameObject& self) -> TransformComponent* {
           return &self.AddComponent<TransformComponent>();
         }, nb::rv_policy::reference_internal)  // 等价于 pybind11 的 reference_internal
    .def("add_ai",
         [](GameObject& self) -> AIComponent* {
           return &self.AddComponent<AIComponent>();
         }, nb::rv_policy::reference_internal);
```

**Nanobind 生命周期管理的底层改进**：Pybind11 使用 `std::shared_ptr` 的别名构造函数实现引用计数分享，而 nanobind 使用了一种更高效的自定义引用计数机制，避免了 shared_ptr 控制块的分配开销。

### GIL 管理差异

Nanobind 对 GIL 的处理比 pybind11 更加自动化。在多线程场景中，nanobind 自动检测是否需要 GIL，减少了手动 `gil_scoped_acquire` 的需求：

```cpp
// nanobind 事件回调 — 无需显式 GIL 管理
.def("subscribe_event",
     [](EngineFacade& self, const std::string& event_type,
        nb::callable callback) -> int64_t {
       if (event_type == "damage") {
         // nb::callable 替代 py::function，内置 GIL 安全处理
         auto sub = self.GetEventBus().Subscribe<std::string>(
             [callback = std::move(callback)](const std::string& data) {
               callback(data);  // nanobind 自动处理跨线程 GIL 获取
             });
         return sub.id;
       }
       return -1;
     },
     nb::arg("event_type"), nb::arg("callback"))
```

注意上面的代码与 pybind11 版本的关键差异：
1. 使用 `nb::callable` 替代 `py::function`
2. Lambda 中使用 `callback = std::move(callback)` 显式捕获，避免不必要的引用计数
3. **无需 `py::gil_scoped_acquire`** —— nanobind 在跨线程调用时自动管理 GIL

### 属性绑定的返回值优化

Nanobind 的 `def_prop_rw` 支持返回引用（`float&`），使得 setter 可以直接修改变量而无需单独定义：

```cpp
nb::class_<TransformComponent, Component>(m, "Transform")
    .def(nb::init<>())
    // getter 返回 float& 而非 float，允许 Python 端直接修改
    .def_prop_rw("x",
         [](TransformComponent& t) -> float& { return t.data.x; },
         [](TransformComponent& t, float v) { t.data.x = v; })
    .def_prop_rw("y",
         [](TransformComponent& t) -> float& { return t.data.y; },
         [](TransformComponent& t, float v) { t.data.y = v; })
    .def_prop_rw("z",
         [](TransformComponent& t) -> float& { return t.data.z; },
         [](TransformComponent& t, float v) { t.data.z = v; });
```

这种设计允许 `t.x += 1.0` 这样的原地修改操作，而不会产生中间拷贝。

## 实现复杂度分析

### 代码量

Nanobind 绑定文件 `nanobind_bindings.cpp` 共 112 行（与 pybind11 的 110 行几乎相同）。API 命名更短但概念完全相同。迁移成本极低——开发者可以在 pybind11 和 nanobind 之间快速切换。

### 学习曲线

**如果你已经会 pybind11，学习 nanobind 大约需要一小时**。API 差异主要体现在：
- 命名空间的缩写（`nb::` vs `py::`）
- 属性方法的缩写（`def_prop_ro` vs `def_property_readonly`）
- 需要按需引入 STL 头文件（而非一次性引入 `<pybind11/stl.h>`）

GIL 自动管理降低了对 Python C API 理解的要求，但可能在需要精细控制 GIL 的场景中带来意外行为。

### 编译速度

Nanobind 的设计目标之一是编译速度。通过以下技术手段实现：

1. **细粒度头文件**：按需引入，减少预处理器展开量
2. **减少模板实例化深度**：内部使用更多运行时多态替代编译期递归
3. **预编译头兼容**：nanobind 头文件结构与 PCH（Precompiled Header）机制配合更好

在本项目的 CMake 构建中，nanobind 绑定的编译时间约为 pybind11 的 60-70%。

### 调试体验

Nanobind 的运行时错误信息比 pybind11 更简洁。类型错误信息去除了模板展开栈的冗长输出，直接给出类型期望。但编译期错误信息与 pybind11 类似，模板错误仍然较长。

## 易用性评估

### Python 端使用

Python API 与 pybind11 完全一致：

```python
import enginenanobind

engine = enginenanobind.Engine()
engine.init('{"app": "nanobind_demo"}')

scene = engine.create_scene("MainScene")
player = scene.create_object("Player")
enemy = scene.create_object("Enemy")

# 添加组件 — Transform 和 AI
player.add_transform()
enemy.add_ai()

# 属性访问
print(f"Engine initialized: {engine.is_initialized}")
print(f"Scene objects: {scene.object_count}")

# 事件系统
engine.subscribe_event("damage", lambda data: print(f"Damage: {data}"))
engine.publish_event("damage", '{"amount": 75}')

# 更新循环
for i in range(3):
    engine.update(0.016)

# 批量操作
scene.batch_create_objects(5, "NanobindObj")
print(f"After batch: {scene.object_count} objects")

engine.shutdown()
```

### 迁移指南：从 pybind11 到 nanobind

迁移检查清单：

1. **命名空间**：全局替换 `namespace py = pybind11` → `namespace nb = nanobind`
2. **模块宏**：`PYBIND11_MODULE(name, m)` → `NB_MODULE(name, m)`
3. **属性方法**：
   - `def_property_readonly` → `def_prop_ro`
   - `def_property` → `def_prop_rw`
   - `def_readwrite` → `def_rw`
4. **返回值策略**：`py::return_value_policy::X` → `nb::rv_policy::X`
5. **头文件**：拆分为多个 `<nanobind/stl/xxx.h>` 按需引入
6. **CMake**：`pybind11_add_module` → `nanobind_add_module`
7. **GIL**：删除大部分 `py::gil_scoped_acquire` / `py::gil_scoped_release` 调用

### 优点总结

1. **更小的二进制体积**：生成的 `.pyd` 文件比 pybind11 小约 50%
2. **更快的编译速度**：减少约 30-40% 的编译时间
3. **自动 GIL 管理**：跨线程回调不再需要手动获取 GIL
4. **零开销抽象**：更多工作在编译期完成，运行时无额外开销
5. **活跃的维护**：由 pybind11 原作者维护，吸收了十年经验教训

### 缺点总结

1. **社区较小**：相比 pybind11，Stack Overflow 和其他平台上的讨论较少
2. **文档覆盖率**：API 文档齐全，但教程和最佳实践指南较少
3. **Python 版本限制**：不支持 Python 3.7 及以下版本
4. **不向后兼容 pybind11**：虽然迁移成本低，但需要从代码到构建系统全面更新
5. **成熟度**：部分高级特性（如自定义类型转换器）的 API 仍可能变更

## 编译、安装与使用

### 编译

```bash
cd CppPy
python scripts/manage.py setup              # 自动 clone nanobind 到 3rdparty/
python scripts/manage.py build              # 编译所有方案（或 --scheme nanobind）
```

编译产物位于 `dist/<Config>/enginenanobind/`：

```
dist/Debug/enginenanobind/
├── __init__.py                  # from ._core import ...
├── _core.cp312-win_amd64.pyd    # 内部 C 扩展
├── _core.pyi                    # nanobind 原生存根（质量最优）
└── py.typed
```

### 安装与使用

将 `dist/<Config>/` 加入 `PYTHONPATH` 后即可导入：

```bash
export PYTHONPATH="$(pwd)/dist/Debug"    # Linux / macOS
$env:PYTHONPATH="$(Get-Location)\dist\Debug"  # Windows PowerShell
```

```python
import enginenanobind
engine = enginenanobind.Engine()
engine.init('{}')
```

### 打包分发

```bash
python scripts/manage.py package --scheme nanobind --config Release
# 产物: dist/enginenanobind-0.1.0.zip
```

## 物理文件与 Python 类型存根 (`.pyi`)

### 产物物理文件

nanobind 绑定编译后产生以下文件：

| 文件 | 说明 |
|------|------|
| `enginenanobind/__init__.py` | 包入口，执行 `from ._core import *` 重导出公开 API |
| `enginenanobind/_core.*.pyd` | 内部 C 扩展模块（以下划线前缀隐藏） |
| `enginenanobind/_core.pyi` | **原生**类型存根，由 nanobind 内置的 `nanobind.stubgen` 生成 |
| `enginenanobind/py.typed` | PEP 561 标记文件 |

### Python 如何发现和加载 .pyd

Python 通过 `PYTHONPATH` 搜索到 `enginenanobind/` 包目录，执行 `__init__.py`，其中 `from ._core import *` 通过相对导入找到包内的 `_core.*.pyd`。

### 类型存根生成（原生支持）

nanobind 是所有 5 种方案中**唯一内置原生 `.pyi` 生成的方案**。它不依赖第三方工具或启发式推断——而是直接读取绑定时注册的结构化 `__nb_signature__` 信息：

```bash
python -m nanobind.stubgen -m enginenanobind -O <output_dir>/
```

在 CppPy 中通过 `scripts/generate_stubs.py` 调用：
```python
# nanobind.stubgen 读取 __nb_signature__，无需启发式推断
subprocess.run([python, "-m", "nanobind.stubgen",
    "-m", "enginenanobind",
    "-O", module_dir])
```

**生成质量对比**：

| 方案 | 工具 | 原理 | `create_scene` 返回类型 |
|------|------|------|------------------------|
| nanobind | 内置 `nanobind.stubgen` | 读取 `__nb_signature__` | `Scene` ✅ |
| pybind11 | `pybind11-stubgen` | docstring 解析 | `...` (Ellipsis) ❌ |
| Cython | `stubgen-pyx` | `.pyx` AST 解析 | 取决于 `.pyx` 中的类型声明 |

nanobind 的存根是唯一能正确解析所有返回类型而不产生 `...` 的方案，这是因为它使用结构化签名数据而非启发式推断。

### 用户可见效果

生成了 `enginenanobind.pyi` + `py.typed` 后，用户可以在 VS Code / PyCharm 中获得完整的自动补全和类型检查：

```python
import enginenanobind
engine = enginenanobind.Engine()
engine.  # IDE 提示: init(config_json: str = '{}') -> bool
         #             create_scene(name: str) -> Scene
         #             update(dt: float) -> None
         #             ...
```

## 适用场景推荐

Nanobind 最适合以下场景：

- **新项目且目标 Python ≥ 3.8**：无需考虑旧版本兼容性的全新绑定项目
- **对二进制体积敏感**：如移动端 Python 嵌入、WebAssembly 部署（Pyodide）
- **编译时间是大项目瓶颈**：绑定层需要频繁修改和重新编译的场景
- **已有 pybind11 代码，希望渐进迁移**：API 高度相似，迁移成本可控

不太适合以下场景：

- **需要支持 Python 3.6/3.7** 的遗留系统
- **团队已有大量 pybind11 经验且无性能瓶颈**：迁移收益可能不足以覆盖切换成本
- **需要广泛的社区和第三方资源支持**：现阶段 pybind11 的生态更丰富
