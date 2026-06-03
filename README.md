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

# 2. Build all bindings (C++ engine + 5 Python packages → dist/)
python scripts/manage.py build

# 3. Editable install — then import from anywhere
python scripts/manage.py develop

# 4. Run demos + tests
python scripts/manage.py run
python scripts/manage.py test

# 5. Format, lint, tidy
python scripts/manage.py format    # auto-fix formatting
python scripts/manage.py lint      # check formatting
python scripts/manage.py tidy      # static analysis
```

After building, `dist/Debug/` contains 5 self-contained Python packages. Each is a standard Python package with `__init__.py` + internal `_core` C extension + `.pyi` stubs.

## Editable Install (recommended for development)

```bash
python scripts/manage.py develop           # = pip install -e .
# Now import from any directory:
python -c "import enginepybind; print(enginepybind.Engine())"
```

## Using via PYTHONPATH (alternative, no install needed)

```bash
PYTHONPATH=dist/Debug python               # Linux / macOS
$env:PYTHONPATH="dist\Debug"; python        # Windows PowerShell
```

## Packaging for Distribution

```bash
python scripts/manage.py package --config Release
# Output: dist/enginepybind-0.1.0.zip, dist/enginenanobind-0.1.0.zip, ...
```

## Build a Single Scheme

```bash
python scripts/manage.py setup --scheme pybind11
python scripts/manage.py build --scheme pybind11
python scripts/manage.py run --scheme pybind11
```

## All Commands

| Command | Description |
|---------|-------------|
| `setup` | Create venv, install deps, cmake configure |
| `build` | Compile C++ engine + all bindings → `dist/` |
| `run` | Execute all demo scripts |
| `develop` | `pip install -e .` — editable install |
| `package` | Create `.zip` archives from `dist/` |
| `format` | Auto-format C++ (clang-format) + Python (black) |
| `lint` | Check formatting (clang-format, flake8, black) |
| `tidy` | Static analysis (clang-tidy) |
| `test` | Run pytest smoke tests (22 tests) |

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
│   ├── pybind11/    #   + python/__init__.py  (package facade)
│   ├── nanobind/
│   ├── swig/
│   ├── cython/
│   └── cffi/
├── examples/        # Demo scripts for each scheme
├── tests/           # pytest smoke tests (22 tests across 5 schemes)
├── scripts/         # manage.py orchestration + stubs/wheel helpers
├── dist/            # Build output — self-contained Python packages
├── docs/            # Technical documentation per scheme
└── tools/           # .clang-format, .clang-tidy, cpp-python-bindings.skill
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
