"""CppPy engine — CFFI/ctypes binding.

This package exposes the C++ game engine kernel via ctypes (pure-C ABI).
The engine is loaded as engine_c.dll via ctypes.CDLL, wrapped by cffi_bridge.py.

Usage:
    import engine_cffi
    engine = engine_cffi.Engine('{"app":"demo"}')
    engine.init()
    scene = engine.create_scene("Main")
    ...
"""

from .cffi_bridge import Component, Engine, GameObject, Scene
