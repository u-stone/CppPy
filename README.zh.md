# CppPy — C++ 游戏引擎与 Python 绑定方案验证项目

一个技术验证项目，对比 5 种将 C++17 游戏引擎内核桥接到 Python 3.x 的方案。

## 绑定方案

| 方案 | 方式 | 模块名 |
|------|------|--------|
| **pybind11** | 头文件绑定，通过 `PYBIND11_MODULE` 宏 | `engine_pybind` |
| **nanobind** | pybind11 作者的下一代重写 | `engine_nanobind` |
| **SWIG** | `.i` 接口文件自动生成粘合代码 | `engine_swig` |
| **Cython** | `.pyx` → 编译为 C 扩展 | `engine_cython` |
| **CFFI + ctypes** | 纯 C `extern "C"` ABI | `cffi_bridge` |

## 快速开始

```bash
# 1. 初始化（创建虚拟环境，运行 cmake）
python scripts/manage.py setup

# 2. 构建所有绑定方案
python scripts/manage.py build

# 3. 运行所有示例
python scripts/manage.py run

# 4. 代码检查
python scripts/manage.py lint
python scripts/manage.py tidy
```

## 构建单个方案

```bash
python scripts/manage.py setup --scheme pybind11
python scripts/manage.py build --scheme pybind11
python scripts/manage.py run --scheme pybind11
```

## 环境要求

- CMake >= 3.20
- Ninja（或 Make）
- Python >= 3.9
- C++17 编译器（GCC 9+, Clang 10+, MSVC 2019+）
- SWIG（可选，仅用于 SWIG 绑定方案）
- Cython（通过 pip 安装）

## 项目结构

```
CppPy/
├── engine/          # 共享 C++17 游戏引擎（静态库）
│   ├── include/     # 头文件：facade, scene, game_object, event_bus 等
│   └── src/         # 实现文件
├── bindings/        # 每种绑定方案一个子目录
│   ├── pybind11/
│   ├── nanobind/
│   ├── swig/
│   ├── cython/
│   └── cffi/
├── examples/        # 每种方案的示例脚本
├── docs/            # 每种方案的技术文档
├── scripts/         # manage.py 编排脚本
├── cmake/           # CMake 辅助模块
└── tools/           # .clang-format, .clang-tidy
```

## 引擎 API 层次

- **C API**（`c_api.h`）：纯 `extern "C"` 函数，使用不透明的 `void*` 句柄。ABI 稳定，供 cffi/ctypes 和 SWIG 使用。
- **C++ 模板 API**（`cpp_api.h`）：模板、`std::vector`、`std::optional`、`std::shared_ptr`。供 pybind11 和 nanobind 使用。

## 技术文档

每种绑定方案在 `docs/` 目录下都有详细的技术文档：

| 方案 | 文档 | 涵盖主题 |
|------|------|----------|
| pybind11 | [docs/pybind11.md](docs/pybind11.md) | STL 自动转换、GIL 管理、返回值策略 |
| nanobind | [docs/nanobind.md](docs/nanobind.md) | 更小二进制体积、更快编译、自动 GIL、从 pybind11 迁移 |
| SWIG | [docs/swig.md](docs/swig.md) | `.i` 接口文件、typemap 系统、多语言支持、bytes/str 处理 |
| Cython | [docs/cython.md](docs/cython.md) | `.pxd`/`.pyx` 工作流、`cdef class`、手动生命周期、接近原生性能 |
| CFFI + C API | [docs/cffi.md](docs/cffi.md) | 纯 C ABI、ctypes/CDLL、共享库分发、五种方案横向对比 |

每篇文档均包含：底层机制解析、依赖环境搭建、带注释的代码走读、实现复杂度分析、易用性评估及适用场景推荐。

## 引擎核心设计

### EngineFacade（门面类）
- `Init(config_json)` — 初始化引擎子系统
- `Shutdown()` — 有序关闭，等待所有线程完成
- `CreateScene(name)` — 创建场景
- `Update(dt)` — 驱动所有活跃场景的更新循环
- `GetEventBus()` — 获取事件总线访问接口
- PIMPL 内部实现，Init/Shutdown 使用互斥锁保护

### Scene（场景）
- 维护名称和 GameObject 列表
- `AddObject` / `RemoveObject` 支持互斥锁保护
- 每帧 Update 遍历所有对象

### GameObject + Component（游戏对象与组件）
- ID + 名称，内部持有 `unique_ptr<Component>` 列表
- `AddComponent<T>(args...)` — 工厂模板方法
- Component 提供虚方法：`OnUpdate(dt)`, `OnEnable`, `OnDisable`
- 组件可通过 EventBus 发送事件

### EventBus（事件总线）
- 线程安全的订阅者注册表
- `Publish<T>(event)` 派发到匹配的处理器
- `Subscribe<T>(callback)` 返回订阅句柄
- 每种事件类型使用独立的内部锁

### ThreadPool（线程池）
- 可配置线程数量
- `Enqueue(callable)` 返回 `std::future<R>`
- 停止时排空队列，join 所有工作线程

## 设计目标

1. **公平对比** — 所有方案共享同一个引擎核心，暴露相同的功能集
2. **真实场景** — 场景管理、组件系统、事件系统、多线程支持
3. **可验证** — 每种方案都有对应的 demo 脚本，运行结果一致
4. **可扩展** — 清晰的目录结构，易于添加新的绑定方案或功能

## 许可协议

MIT
