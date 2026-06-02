"""CppPy engine — pybind11 binding.

This package exposes the C++ game engine kernel to Python via pybind11.
The compiled C extension is _core.pyd; this __init__.py re-exports the
public API so users get a clean package interface.

Usage:
    import enginepybind
    engine = enginepybind.Engine()
    engine.init('{"app":"demo"}')
    scene = engine.create_scene("Main")
    ...
    engine.shutdown()
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

# Ensure pybind11-stubgen can still find the module under its original name.
# The .pyi stub covers _core, so type checkers follow __init__.py re-exports.
