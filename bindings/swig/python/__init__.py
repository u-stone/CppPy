"""CppPy engine — SWIG binding.

At build time this file is replaced by the SWIG-generated engine_swig.py
(which provides the full Python API surface).  The compiled _engine_swig.pyd
sits alongside this package directory so that the wrapper's
'import _engine_swig' can find it.
"""
# This placeholder is overwritten by CMake POST_BUILD.
# See bindings/swig/CMakeLists.txt.
