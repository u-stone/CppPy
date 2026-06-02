"""CppPy engine — CFFI/ctypes binding.

This package exposes the C++ game engine kernel via ctypes (pure-C ABI).
The engine is loaded as engine_c.dll via ctypes.CDLL, wrapped by cffi_bridge.py.

Usage:
    import enginecffi
    engine = enginecffi.Engine('{"app":"demo"}')
    engine.init()
    scene = engine.create_scene("Main")
    ...
"""

import os as _os, sys as _sys

# Python 3.8+ on Windows requires explicit DLL search path for ctypes.
if _sys.platform == "win32":
    _os.add_dll_directory(_os.path.dirname(__file__))

from .cffi_bridge import Component, Engine, GameObject, Scene
