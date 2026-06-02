# C++ 扩展封装为 Python 模块后的放置、使用与 Wheel 打包指南

## 1. 文档目标

当 C++ 代码通过 `pybind11`、Python/C API、Cython、SWIG 等方式封装成 Python 扩展模块后，推荐使用标准 Python 包结构进行组织、安装和发布，而不是长期依赖手动复制 `.so` / `.pyd` / `.dll` 文件。

推荐目标：

```text
开发期：pip install -e .
发布期：构建 wheel 后 pip install
使用期：import package 或 from package import module
```

这样可以保证 Python 项目中使用方便、路径稳定、依赖可控，并且适合团队协作、CI/CD 和跨平台发布。

---

## 2. 核心原则

### 2.1 把 C++ 扩展模块放进 Python package

不推荐把编译出来的扩展模块随意放到项目根目录，也不推荐长期依赖 `PYTHONPATH`。

推荐结构：

```text
my_project/
├── pyproject.toml
├── CMakeLists.txt
├── cpp/
│   ├── bindings.cpp
│   └── engine.cpp
├── src/
│   └── myengine/
│       ├── __init__.py
│       ├── gameplay.py
│       └── _core.*.so / _core.*.pyd
└── tests/
    └── test_myengine.py
```

Python 使用方式：

```python
import myengine
```

或：

```python
from myengine import _core
```

更推荐对外隐藏底层 C++ 模块：

```python
# src/myengine/__init__.py
from ._core import init, shutdown, tick
```

用户侧：

```python
import myengine

myengine.init()
myengine.tick()
myengine.shutdown()
```

这种方式让 `_core` 作为底层 native 扩展，`myengine` 作为稳定 Python API 门面。

---

## 3. 推荐命名方式

### 3.1 Python 包名

使用业务语义清晰的名字，例如：

```text
myengine
game_tools
asset_pipeline
physics_runtime
```

### 3.2 C++ 扩展模块名

推荐使用内部模块名：

```text
_core
_native
_runtime
_bindings
```

示例：

```cpp
#include <pybind11/pybind11.h>

namespace py = pybind11;

PYBIND11_MODULE(_core, m) {
    m.def("init", []() {
        // initialize engine
    });
}
```

对应 Python 导入：

```python
from myengine import _core
```

注意：`PYBIND11_MODULE` 中的模块名必须和 Python 实际导入名一致。

如果 C++ 中写：

```cpp
PYBIND11_MODULE(_core, m)
```

那么导入名应为：

```python
from myengine import _core
```

如果写成：

```cpp
PYBIND11_MODULE(engine_core, m)
```

但 Python 中导入：

```python
from myengine import _core
```

会导致导入失败。

---

## 4. 推荐构建方案

推荐使用：

```text
pyproject.toml + scikit-build-core + CMake + pybind11
```

这是 C++ / Python 混合项目目前非常实用的工程化方案。

---

## 5. 最小工程结构

```text
my_project/
├── pyproject.toml
├── CMakeLists.txt
├── cpp/
│   ├── bindings.cpp
│   └── engine.cpp
├── src/
│   └── myengine/
│       ├── __init__.py
│       └── runtime.py
└── tests/
    └── test_import.py
```

构建后，wheel 中应该包含：

Linux / macOS：

```text
myengine/
├── __init__.py
├── runtime.py
└── _core.cpython-311-x86_64-linux-gnu.so
```

Windows：

```text
myengine/
├── __init__.py
├── runtime.py
└── _core.cp311-win_amd64.pyd
```

---

## 6. pyproject.toml 示例

```toml
[build-system]
requires = [
    "scikit-build-core",
    "pybind11"
]
build-backend = "scikit_build_core.build"

[project]
name = "myengine"
version = "0.1.0"
description = "Python bindings for MyEngine"
requires-python = ">=3.9"

[tool.scikit-build]
wheel.packages = ["src/myengine"]
```

如果有额外 Python 依赖，可以写：

```toml
[project]
name = "myengine"
version = "0.1.0"
description = "Python bindings for MyEngine"
requires-python = ">=3.9"
dependencies = [
    "numpy>=1.24",
    "pydantic>=2.0"
]
```

安装 wheel 时，pip 会自动安装这些 Python 依赖。

---

## 7. CMakeLists.txt 示例

```cmake
cmake_minimum_required(VERSION 3.20)

project(myengine LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(_core
    cpp/bindings.cpp
    cpp/engine.cpp
)

install(TARGETS _core
    LIBRARY DESTINATION myengine
    RUNTIME DESTINATION myengine
)
```

这里的关键点：

```cmake
pybind11_add_module(_core ...)
```

要和 C++ 绑定代码一致：

```cpp
PYBIND11_MODULE(_core, m) {
    // bindings
}
```

最终 Python 导入：

```python
from myengine import _core
```

---

## 8. 开发期使用方式

在项目根目录执行：

```bash
pip install -e .
```

然后在任意 Python 代码中使用：

```python
import myengine
```

或：

```python
from myengine import _core
```

开发期推荐使用 editable install，而不是修改 `sys.path` 或手动复制扩展模块。

优点：

```text
Python 包路径稳定
方便 IDE / 测试工具识别
适合 pytest / CI
不需要手动维护 PYTHONPATH
```

---

## 9. Wheel 打包流程

### 9.1 安装构建工具

在项目根目录所在的 Python 虚拟环境中安装：

```bash
pip install build wheel
```

如果项目使用 `pybind11 + scikit-build-core + CMake`，也可以安装：

```bash
pip install scikit-build-core pybind11
```

如果 `pyproject.toml` 的 `[build-system]` 已经声明了这些依赖，构建时也会自动安装到隔离构建环境中。

---

### 9.2 构建 wheel

在项目根目录执行：

```bash
python -m build --wheel
```

构建成功后，会在 `dist/` 目录生成 wheel 文件。

例如：

Linux：

```text
dist/myengine-0.1.0-cp311-cp311-linux_x86_64.whl
```

Windows：

```text
dist/myengine-0.1.0-cp311-cp311-win_amd64.whl
```

macOS：

```text
dist/myengine-0.1.0-cp311-cp311-macosx_14_0_arm64.whl
```

wheel 文件名含义：

```text
myengine        包名
0.1.0           版本号
cp311           Python 3.11
win_amd64       Windows 64 位平台
linux_x86_64    Linux x86_64 平台
macosx_*        macOS 平台
```

---

### 9.3 构建源码包和 wheel

如果既想打源码包，也想打 wheel，可以执行：

```bash
python -m build
```

它会同时生成：

```text
dist/myengine-0.1.0.tar.gz
dist/myengine-0.1.0-cp311-cp311-win_amd64.whl
```

通常 C++ 扩展项目发布给用户时，wheel 更重要，因为用户安装 wheel 时不需要本地有完整 C++ 编译环境。

源码包适合：

```text
开发者二次构建
Linux 发行版打包
特殊平台自行编译
```

---

## 10. 安装 wheel 测试

构建完成后，建议新建一个干净虚拟环境测试安装。

Linux / macOS：

```bash
python -m venv .venv-test
source .venv-test/bin/activate
pip install dist/myengine-0.1.0-*.whl
python -c "import myengine; print(myengine)"
```

Windows PowerShell：

```powershell
python -m venv .venv-test
.venv-test\Scripts\Activate.ps1
pip install dist\myengine-0.1.0-*.whl
python -c "import myengine; print(myengine)"
```

如果你的 C++ 扩展模块是 `_core`，可以进一步测试：

```bash
python -c "from myengine import _core; print(_core)"
```

如果对外 API 是：

```python
import myengine
myengine.init()
```

则测试：

```bash
python -c "import myengine; myengine.init()"
```

---

## 11. 动态库依赖处理

C++ 扩展模块通常不只是一个 `.so` 或 `.pyd`，它可能依赖其他动态库。

例如：

### 11.1 Linux

```text
myengine/
├── __init__.py
├── _core.cpython-311-x86_64-linux-gnu.so
├── libengine.so
└── libphysics.so
```

### 11.2 Windows

```text
myengine/
├── __init__.py
├── _core.cp311-win_amd64.pyd
├── engine.dll
└── physics.dll
```

### 11.3 macOS

```text
myengine/
├── __init__.py
├── _core.cpython-311-darwin.so
├── libengine.dylib
└── libphysics.dylib
```

重点是：Python 找到 `_core` 不代表系统能加载 `_core` 依赖的 native 动态库。

---

## 12. 把额外动态库打进 wheel

如果 `_core` 依赖其他 C++ 动态库，例如：

```text
libengine.so
engine.dll
libengine.dylib
```

需要把它们一起打进 wheel。

推荐放置结构：

```text
myengine/
├── __init__.py
├── _core.*.so / _core.*.pyd
├── libengine.so
└── libphysics.so
```

CMake 中安装这些库：

```cmake
install(TARGETS _core
    LIBRARY DESTINATION myengine
    RUNTIME DESTINATION myengine
)
```

如果是额外动态库，可以用：

```cmake
install(FILES
    ${CMAKE_BINARY_DIR}/libengine.so
    DESTINATION myengine
)
```

Windows 示例：

```cmake
install(FILES
    ${CMAKE_BINARY_DIR}/Release/engine.dll
    DESTINATION myengine
)
```

实际路径要根据构建目录、生成器类型和目标名调整。

如果动态库本身也是 CMake target，更推荐：

```cmake
install(TARGETS engine
    LIBRARY DESTINATION myengine
    RUNTIME DESTINATION myengine
    ARCHIVE DESTINATION myengine
)
```

---

## 13. Linux / macOS RPATH 设置

为了让 `_core` 能找到同目录下的动态库，Linux 推荐设置：

```cmake
set_target_properties(_core PROPERTIES
    BUILD_WITH_INSTALL_RPATH TRUE
    INSTALL_RPATH "$ORIGIN"
)
```

macOS 推荐：

```cmake
set_target_properties(_core PROPERTIES
    BUILD_WITH_INSTALL_RPATH TRUE
    INSTALL_RPATH "@loader_path"
)
```

这样 `_core` 会优先从自身所在目录查找依赖库。

如果 `_core` 依赖的是另一个 CMake target，比如 `engine`：

```cmake
target_link_libraries(_core PRIVATE engine)
```

仍然需要确保 `engine` 的动态库被安装进 wheel，并且 `_core` 的 rpath 能找到它。

---

## 14. Windows DLL 搜索路径

Windows 下，如果 `_core.pyd` 依赖 `engine.dll`，可以在 `src/myengine/__init__.py` 中添加：

```python
import os
import sys

if sys.platform == "win32":
    os.add_dll_directory(os.path.dirname(__file__))
```

然后再导入 native 模块：

```python
from ._core import *
```

完整示例：

```python
import os
import sys

if sys.platform == "win32":
    os.add_dll_directory(os.path.dirname(__file__))

from ._core import init, shutdown, tick
```

Python 3.8+ 的 Windows DLL 搜索策略比较严格，这一步经常是解决 `DLL load failed while importing _core` 的关键。

---

## 15. 推荐 API 分层

不要把 C++ 绑定模块直接作为最终用户 API 暴露。

推荐分层：

```text
myengine
├── __init__.py      # 对外 API
├── runtime.py       # Python 逻辑封装
├── pipeline.py      # 工具链逻辑
└── _core.*.so       # C++ native 扩展
```

`_core` 负责：

```text
性能敏感逻辑
底层引擎对象
资源加载
物理/动画/渲染桥接
大规模数据处理
```

Python 层负责：

```text
API 包装
默认参数
异常转换
日志系统
配置解析
工具链流程编排
编辑器扩展
测试胶水
```

示例：

```python
# src/myengine/runtime.py
from . import _core


class Engine:
    def __init__(self, config_path: str):
        self._handle = _core.create_engine(config_path)

    def tick(self, delta_time: float) -> None:
        _core.tick(self._handle, delta_time)

    def shutdown(self) -> None:
        _core.destroy_engine(self._handle)
```

对外：

```python
# src/myengine/__init__.py
from .runtime import Engine
```

用户使用：

```python
from myengine import Engine

engine = Engine("config.json")
engine.tick(1.0 / 60.0)
engine.shutdown()
```

这样可以避免用户直接依赖 C++ 绑定细节，后续即使 `_core` 的实现方式调整，也可以保持 Python API 稳定。

---

## 16. 多平台 wheel

C++ 扩展模块的 wheel 是平台相关的。

也就是说：

```text
Windows 构建出来的 wheel 只能给 Windows 用
Linux 构建出来的 wheel 只能给 Linux 用
macOS 构建出来的 wheel 只能给 macOS 用
```

不同 Python 版本通常也要分别构建：

```text
cp39
cp310
cp311
cp312
```

如果团队需要正式分发，建议 CI 分别构建：

```text
Windows x64 + Python 3.9/3.10/3.11/3.12
Linux x86_64 + Python 3.9/3.10/3.11/3.12
macOS arm64/x86_64 + Python 3.9/3.10/3.11/3.12
```

---

## 17. 使用 cibuildwheel 批量构建

如果需要给多个 Python 版本和多个平台构建 wheel，推荐使用 `cibuildwheel`。

安装：

```bash
pip install cibuildwheel
```

本地构建当前平台 wheel：

```bash
python -m cibuildwheel --output-dir wheelhouse
```

也可以在 `pyproject.toml` 中配置：

```toml
[tool.cibuildwheel]
build = "cp39-* cp310-* cp311-* cp312-*"
test-command = "python -c \"import myengine; print(myengine)\""
```

如果要测试 C++ 扩展导入：

```toml
[tool.cibuildwheel]
build = "cp39-* cp310-* cp311-* cp312-*"
test-command = "python -c \"from myengine import _core; print(_core)\""
```

构建结果会放在：

```text
wheelhouse/
```

适合团队 CI/CD 使用。

---

## 18. Linux manylinux 注意事项

在 Linux 上直接执行：

```bash
python -m build --wheel
```

生成的可能是：

```text
linux_x86_64.whl
```

这种 wheel 不一定适合在其他 Linux 发行版上安装。

正式发布到 PyPI 或团队制品库时，通常需要 manylinux wheel，例如：

```text
manylinux_2_28_x86_64.whl
```

推荐使用 `cibuildwheel`，它会在 manylinux Docker 镜像中构建，生成兼容性更好的 wheel：

```bash
python -m cibuildwheel --platform linux --output-dir wheelhouse
```

对于 Linux native 依赖，构建 wheel 后还要关注动态库是否被正确修复和打包。`cibuildwheel` 通常会结合 `auditwheel` 处理 manylinux wheel 的依赖修复。

---

## 19. 检查 wheel 内容

可以用 `wheel` 工具查看 wheel 里到底打进了哪些文件。

安装：

```bash
pip install wheel
```

解包检查：

```bash
wheel unpack dist/myengine-0.1.0-*.whl
```

或者直接列出内容：

```bash
python -m zipfile -l dist/myengine-0.1.0-*.whl
```

确认里面包含：

```text
myengine/__init__.py
myengine/_core.*.so / _core.*.pyd
myengine/libengine.so / engine.dll / libengine.dylib
```

如果 native 模块或依赖动态库没有被打进去，需要检查：

```text
CMake install 规则
pyproject.toml 的 package 配置
scikit-build-core 配置
动态库路径是否正确
```

---

## 20. 临时调试方式

如果只是快速验证，可以把扩展模块放到脚本同级目录：

```text
test.py
_core.cpython-311-x86_64-linux-gnu.so
```

然后：

```python
import _core
```

也可以设置 `PYTHONPATH`。

Linux / macOS：

```bash
export PYTHONPATH=/path/to/module:$PYTHONPATH
```

Windows PowerShell：

```powershell
$env:PYTHONPATH="C:\path\to\module;$env:PYTHONPATH"
```

但这只适合临时调试，不推荐作为正式项目使用方式。

---

## 21. 常见错误与排查

### 21.1 Python 找不到模块

错误：

```text
ModuleNotFoundError: No module named 'myengine'
```

检查：

```text
是否执行了 pip install -e . 或 pip install xxx.whl
包目录是否有 __init__.py
pyproject.toml 中包路径是否正确
是否在正确的虚拟环境中运行 Python
```

---

### 21.2 扩展模块初始化函数不匹配

错误：

```text
ImportError: dynamic module does not define module export function
```

通常原因是 `PYBIND11_MODULE` 名字和实际导入名不一致。

错误示例：

```cpp
PYBIND11_MODULE(engine_core, m)
```

但 Python 中：

```python
import _core
```

修复：

```cpp
PYBIND11_MODULE(_core, m)
```

---

### 21.3 找不到底层动态库

错误可能类似：

Linux：

```text
ImportError: libengine.so: cannot open shared object file
```

Windows：

```text
ImportError: DLL load failed while importing _core
```

检查：

```text
依赖动态库是否和 _core 放在一起
Windows 是否设置 os.add_dll_directory
Linux 是否设置 $ORIGIN rpath
macOS 是否设置 @loader_path
```

---

### 21.4 Python 版本或 ABI 不匹配

例如把 Python 3.10 编译的模块拿到 Python 3.11 使用：

```text
_core.cpython-310-x86_64-linux-gnu.so
```

在 Python 3.11 下可能无法导入。

解决：

```text
为目标 Python 版本重新构建
使用 wheel 标签区分版本
CI 中分别构建不同 Python 版本产物
```

---

### 21.5 wheel 安装成功但 import 失败

可能原因：

```text
native 扩展没有被安装进 package
依赖动态库没有被打进 wheel
rpath / DLL 搜索路径不正确
PYBIND11_MODULE 名称不匹配
当前 Python 版本和 wheel 标签不匹配
```

建议排查：

```bash
python -m zipfile -l dist/myengine-0.1.0-*.whl
```

确认 `_core` 和依赖库是否真的在 wheel 中。

---

## 22. 最佳实践清单

```text
使用标准 Python package 承载 C++ 扩展模块
C++ 扩展模块使用 _core / _native 这类内部命名
Python 层提供稳定、友好的对外 API
开发期使用 pip install -e .
发布期使用 python -m build --wheel
团队多平台发布使用 cibuildwheel
不要长期手动复制 .so / .pyd
不要长期依赖 PYTHONPATH
处理好动态库依赖路径
保证 PYBIND11_MODULE 名称与导入名一致
为不同平台和 Python 版本分别构建 wheel
用 pytest 覆盖基本 import 和核心 API 调用
检查 wheel 内容，确认 native 模块和动态库被打包
```

---

## 23. 完整流程总结

### 23.1 开发期

```bash
pip install -e .
python -c "import myengine; print(myengine)"
```

### 23.2 构建 wheel

```bash
python -m build --wheel
```

### 23.3 测试 wheel

Linux / macOS：

```bash
python -m venv .venv-test
source .venv-test/bin/activate
pip install dist/myengine-0.1.0-*.whl
python -c "import myengine; print(myengine)"
python -c "from myengine import _core; print(_core)"
```

Windows PowerShell：

```powershell
python -m venv .venv-test
.venv-test\Scripts\Activate.ps1
pip install dist\myengine-0.1.0-*.whl
python -c "import myengine; print(myengine)"
python -c "from myengine import _core; print(_core)"
```

### 23.4 团队多平台发布

```bash
python -m cibuildwheel --output-dir wheelhouse
```

最终产物示例：

```text
wheelhouse/
├── myengine-0.1.0-cp39-cp39-win_amd64.whl
├── myengine-0.1.0-cp310-cp310-win_amd64.whl
├── myengine-0.1.0-cp311-cp311-manylinux_x86_64.whl
├── myengine-0.1.0-cp312-cp312-macosx_14_0_arm64.whl
└── ...
```

---

## 24. 推荐决策

如果只是本地实验：

```text
可以临时把 .so / .pyd 放到脚本同级目录
```

如果是个人项目或工具：

```text
使用 pyproject.toml + pip install -e .
```

如果是团队项目、游戏引擎工具链、编辑器插件或生产环境：

```text
使用 pyproject.toml + CMake + scikit-build-core
开发期 editable install
发布期 wheel 分发
多平台发布使用 cibuildwheel
C++ 模块放在 Python package 内
Python 层封装对外 API
处理好动态库依赖和 rpath / DLL 搜索路径
```

最终推荐形态：

```text
myengine/
├── __init__.py
├── runtime.py
├── pipeline.py
└── _core.*.so / _core.*.pyd
```

对外使用：

```python
import myengine
```

内部实现：

```python
from . import _core
```

一句话总结：

```text
不要分发裸 .so / .pyd，应该把 C++ 扩展模块作为 Python package 的一部分打进 wheel。
```

这样 Python 项目只需要：

```bash
pip install myengine-0.1.0-*.whl
```

然后：

```python
import myengine
```

即可正常使用。