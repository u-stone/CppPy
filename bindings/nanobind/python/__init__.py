"""CppPy engine — nanobind binding.

This package exposes the C++ game engine kernel to Python via nanobind.
The compiled C extension is _core.pyd; this __init__.py re-exports the
public API so users get a clean package interface.

Usage:
    import engine_nanobind
    engine = engine_nanobind.Engine()
    engine.init('{"app":"demo"}')
    ...
"""

from ._core import (
    AIComponent,
    Component,
    Engine,
    GameObject,
    Scene,
    Transform,
    TransformData,
)
