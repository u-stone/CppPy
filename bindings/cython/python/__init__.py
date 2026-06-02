"""CppPy engine — Cython binding.

This package exposes the C++ game engine kernel to Python via Cython.
The compiled C extension is _core.pyd; this __init__.py re-exports the
public API so users get a clean package interface.

Usage:
    import engine_cython
    engine = engine_cython.Engine()
    engine.init('{"app":"demo"}')
    ...
"""

from ._core import Component, Engine, GameObject, Scene
