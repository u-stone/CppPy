# bindings/cffi/python/cffi_build.py
# Builds the CFFI bindings from engine/c_api.h.
# Usage: python cffi_build.py

import os
import sys
from cffi import FFI

ffi = FFI()

# Read the C API header
header_path = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "engine", "include", "engine", "c_api.h"
)
with open(header_path) as f:
    header_content = f.read()

# Filter out #include and extern "C" since cffi processes pure C declarations.
lines = []
in_cxx_guard = False
for line in header_content.splitlines():
    if "#ifdef __cplusplus" in line:
        in_cxx_guard = True
        continue
    if "#endif" in line and in_cxx_guard:
        in_cxx_guard = False
        continue
    if 'extern "C"' in line:
        continue
    if line.startswith("#include"):
        continue
    lines.append(line)

clean_header = "\n".join(lines)

ffi.cdef(clean_header)

if __name__ == "__main__":
    # Compile and link against the engine_c shared library
    lib_path = os.path.join(os.path.dirname(__file__), "..")

    ffi.set_source(
        "_engine_cffi",
        None,  # No extra C source — all symbols come from engine_c.so
        libraries=[],
        extra_link_args=[],
    )

    ffi.compile(tmpdir=os.path.join(lib_path, "build_cffi"))
    print("[CFFI] Bindings compiled successfully.")
