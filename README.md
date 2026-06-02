# CppPy — C++ Game Engine to Python Binding Verification

A technical verification project comparing 5 approaches for bridging a C++17 game engine kernel into Python 3.x.

## Binding Schemes

| Scheme | Approach | Module Name |
|--------|----------|-------------|
| **pybind11** | Header-only binding via `PYBIND11_MODULE` | `enginepybind` |
| **nanobind** | Next-gen pybind11 rewrite | `enginenanobind` |
| **SWIG** | `.i` interface file auto-generation | `engineswig` |
| **Cython** | `.pyx` → compiled C extension | `enginecython` |
| **CFFI + ctypes** | Pure-C `extern "C"` ABI | `cffi_bridge` |

## Quick Start

```bash
# 1. Setup (create venv, install deps, configure CMake)
python scripts/manage.py setup

# 2. Build all bindings (compiles C++ engine + 5 Python packages to dist/)
python scripts/manage.py build

# 3. Run all demos (automatically sets PYTHONPATH to dist/)
python scripts/manage.py run

# 4. Lint & tidy
python scripts/manage.py lint
python scripts/manage.py tidy
```

After building, `dist/Debug/` (or `dist/Release/`) contains 5 self-contained Python packages:

```
dist/Debug/
├── enginepybind/      # import enginepybind
├── enginenanobind/    # import enginenanobind
├── engineswig/        # import engineswig
├── enginecython/      # import enginecython
└── enginecffi/        # import enginecffi
```

Each package is a native Python module — `__init__.py` + internal `_core` C extension + `.pyi` stubs.

## Using as a Library

```bash
# Without manage.py — just set PYTHONPATH to dist/<Config>/
PYTHONPATH=dist/Debug python       # Linux / macOS
$env:PYTHONPATH="dist\Debug"; python  # Windows PowerShell
```

```python
>>> import enginepybind
>>> engine = enginepybind.Engine()
>>> engine.init('{"app":"demo"}')
>>> engine.update(0.016)
>>> engine.shutdown()
```

## Packaging for Distribution

```bash
# Package all or a single scheme as .zip archives
python scripts/manage.py package --config Release
python scripts/manage.py package --scheme pybind11 --config Release

# Output: dist/enginepybind-0.1.0.zip, dist/enginenanobind-0.1.0.zip, ...
```

## Build a Single Scheme

```bash
python scripts/manage.py setup --scheme pybind11
python scripts/manage.py build --scheme pybind11
python scripts/manage.py run --scheme pybind11
```

## Requirements

- CMake >= 3.20
- Ninja (or Make)
- Python >= 3.9
- C++17 compiler (GCC 9+, Clang 10+, MSVC 2019+)
- SWIG (optional, for SWIG bindings)
- Cython (installed via pip)

## Project Structure

```
CppPy/
├── engine/          # Shared C++17 game engine (static library)
│   ├── include/     # Headers: facade, scene, game_object, event_bus, etc.
│   └── src/         # Implementations
├── bindings/        # One subdirectory per binding scheme
│   ├── pybind11/
│   ├── nanobind/
│   ├── swig/
│   ├── cython/
│   └── cffi/
├── examples/        # Demo scripts for each scheme
├── scripts/         # manage.py orchestration
├── cmake/           # CMake helper modules
└── tools/           # .clang-format, .clang-tidy
```

## Engine API Layers

- **C API** (`c_api.h`): Pure `extern "C"` functions with opaque `void*` handles. ABI-stable. Used by cffi/ctypes and SWIG.
- **C++ Template API** (`cpp_api.h`): Templates, `std::vector`, `std::optional`, `std::shared_ptr`. Used by pybind11 and nanobind.

## Documentation

Each binding scheme has a detailed technical document in `docs/`:

| Scheme | Document | Topics Covered |
|--------|----------|----------------|
| pybind11 | [docs/pybind11.md](docs/pybind11.md) | STL auto-conversion, GIL management, return value policies |
| nanobind | [docs/nanobind.md](docs/nanobind.md) | Smaller binaries, faster compilation, auto GIL, migration from pybind11 |
| SWIG | [docs/swig.md](docs/swig.md) | `.i` interface files, typemaps, multi-language support, bytes/str handling |
| Cython | [docs/cython.md](docs/cython.md) | `.pxd`/`.pyx` workflow, `cdef class`, manual lifecycle, near-native performance |
| CFFI + C API | [docs/cffi.md](docs/cffi.md) | Pure C ABI, ctypes/CDLL, shared library distribution, cross-scheme comparison |

Each document covers: underlying mechanism, dependency setup, code walkthrough with annotations, implementation complexity analysis, ease-of-use evaluation, and use case recommendations.

**[docs/troubleshooting.md](docs/troubleshooting.md)** — 踩坑记录与解决方案：Debug 构建链接错误、多配置生成器路径问题、VS IDE 头文件显示等常见问题及解决办法。

中文文档请参阅 [README.zh.md](README.zh.md)。

## License

MIT
