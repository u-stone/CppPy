"""CppPy engine — SWIG binding.

At build time this file is replaced by the SWIG-generated engineswig.py
(which provides the full Python API surface).  The compiled _engineswig.pyd
sits alongside this package directory so that the wrapper's
'import _engineswig' can find it.
"""

# This placeholder is overwritten by CMake POST_BUILD.
# See bindings/swig/CMakeLists.txt.
