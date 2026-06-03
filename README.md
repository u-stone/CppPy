# CppPy — C++ Game Engine to Python Binding Verification

A technical verification project comparing 5 approaches for bridging a C++17 game engine kernel into Python 3.x.

## Binding Schemes

| Scheme | Approach | Module |
|--------|----------|--------|
| **pybind11** | Header-only binding via `PYBIND11_MODULE` | `enginepybind` |
| **nanobind** | Next-gen pybind11 rewrite | `enginenanobind` |
| **SWIG** | `.i` interface file auto-generation | `engineswig` |
| **Cython** | `.pyx` → compiled C extension | `enginecython` |
| **CFFI + ctypes** | Pure-C `extern "C"` ABI | `enginecffi` |

## Quick Start

```bash
# 1. Setup (create venv, install deps, configure CMake)
python scripts/manage.py setup

# 2. Build (compile C++ engine + 5 Python packages → dist/)
python scripts/manage.py build

# 3. Install (editable mode — now import from anywhere)
python scripts/manage.py develop
```

```python
>>> import enginepybind
>>> engine = enginepybind.Engine()
>>> engine.init('{"app":"demo"}')
>>> engine.update(0.016)
>>> engine.shutdown()
```

Verify everything works:

```bash
python scripts/manage.py run     # all demos
python scripts/manage.py test    # 22 pytest smoke tests
python scripts/manage.py lint    # clang-format + flake8 + black
```

## All Commands

| Command | Description |
|---------|-------------|
| `setup` | Create venv, install deps, cmake configure |
| `build` | Compile C++ engine + all bindings → `dist/` |
| `develop` | `pip install -e .` — import from any directory |
| `run` | Execute all demo scripts |
| `test` | Run 22 pytest smoke tests |
| `format` | Auto-format C++ (clang-format) + Python (black) |
| `lint` | Check formatting (clang-format, flake8, black) |
| `tidy` | Static analysis on engine sources (clang-tidy) |
| `wheel` | Build standard `.whl` for `pip install` |
| `package` | Create `.zip` archives from `dist/` |

All commands use the venv Python automatically — no activation needed.

## Distribution

### Wheel — standard Python packaging (`pip install`)

```bash
python scripts/manage.py wheel --config Release
pip install dist/enginepybind-0.1.0-*.whl
```

The `.whl` contains `__init__.py`, `_core.pyd`, `_core.pyi`, and `py.typed`. This is the same format used by NumPy, PyTorch, etc.

### Editable install — for development

```bash
python scripts/manage.py develop      # = pip install -e .
```

Creates an egg-link in `venv/site-packages/` → `dist/Debug/`. Rebuild updates automatically.

### PYTHONPATH — zero install

```bash
PYTHONPATH=dist/Debug python                  # Linux / macOS
$env:PYTHONPATH="dist\Debug"; python           # Windows PowerShell
```

### Zip archive — quick distribution

```bash
python scripts/manage.py package --config Release
# → dist/enginepybind-0.1.0.zip
```

## VS Code

**One setting is all it takes** (already in `.vscode/settings.json`):

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/build/venv/Scripts/python.exe"
}
```

Why this is enough: `pip install -e .` registers packages in `venv/site-packages/`. Pylance finds them automatically through the interpreter — no `extraPaths`, no terminal `PYTHONPATH`.

**Debugging** (`.vscode/launch.json`, press `F5`):
- `Python: Current File` — debug the active editor file
- `pytest: Current Test` — debug a single test
- `pytest: All Tests` — debug the full suite

## Build a Single Scheme

```bash
python scripts/manage.py setup --scheme pybind11
python scripts/manage.py build --scheme pybind11
python scripts/manage.py run --scheme pybind11
```

## Requirements

- CMake >= 3.20
- Python >= 3.9
- C++17 compiler (GCC 9+, Clang 10+, MSVC 2019+)
- SWIG (optional, auto-downloaded by setup)
- Cython, pybind11, nanobind (installed via pip by setup)

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
├── dist/            # Build output — self-contained Python packages + .whl
├── docs/            # Technical documentation per scheme
└── tools/           # .clang-format, .clang-tidy, cpp-python-bindings.skill
```

## Engine API Layers

- **C API** (`c_api.h`): Pure `extern "C"` functions with opaque `void*` handles. ABI-stable. Used by cffi/ctypes and SWIG.
- **C++ Template API** (`cpp_api.h`): Templates, `std::vector`, `std::optional`, `std::shared_ptr`. Used by pybind11 and nanobind.

## Documentation

Start with the **[comparison](docs/comparison.md)** for a focused side-by-side of how each scheme bridges C++ to Python, then dive into the detailed technical docs:

| Scheme | Document | Topics Covered |
|--------|----------|----------------|
| pybind11 | [docs/pybind11.md](docs/pybind11.md) | STL auto-conversion, GIL management, return value policies |
| nanobind | [docs/nanobind.md](docs/nanobind.md) | Smaller binaries, faster compilation, auto GIL |
| SWIG | [docs/swig.md](docs/swig.md) | `.i` interface files, typemaps, multi-language support |
| Cython | [docs/cython.md](docs/cython.md) | `.pxd`/`.pyx` workflow, `cdef class`, near-native performance |
| CFFI + C API | [docs/cffi.md](docs/cffi.md) | Pure C ABI, ctypes/CDLL, shared library distribution |

**[docs/troubleshooting.md](docs/troubleshooting.md)** — 踩坑记录与解决方案 (Chinese).

中文文档：[README.zh.md](README.zh.md)

## License

MIT
