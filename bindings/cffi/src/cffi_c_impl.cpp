// bindings/cffi/src/cffi_c_impl.cpp
// Re-exports the C API functions as a standalone shared library (engine_c).
// The C API functions are already defined in engine/src/c_api.cpp and
// linked via the engine static library. This file just provides the
// compilation unit and any additional cffi-specific C thunks.

#include "engine/c_api.h"

// No additional code needed — the engine static library provides all
// extern "C" symbols, and linking them into this shared library makes
// them available via dlopen / LoadLibrary for cffi/ctypes.
