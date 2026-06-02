// bindings/swig/src/engine.i — SWIG interface file
// Wraps the pure-C API so SWIG can auto-generate Python glue.
//
// SWIG 4.x maps char* ↔ Python bytes by default. To keep things simple we
// stay with that behaviour and let demo.py handle encode/decode.

%module engine_swig

// Generate Python docstrings from C function signatures.
%feature("autodoc", "1");

%begin %{
#define SWIG_PYTHON_STRICT_BYTE_CHAR
%}

%{
#include "engine/c_api.h"
%}

// Ensure stdint types are mapped to Python ints
%include "stdint.i"

// Include the pure-C header for automatic wrapping
%include "engine/c_api.h"

// Additional Python-friendly helpers
%inline %{
  void* engine_create_and_init(const char* config_json) {
    void* engine = engine_create();
    engine_init(engine, config_json);
    return engine;
  }

  void engine_run_ticks(void* engine, int ticks, float dt) {
    for (int i = 0; i < ticks; ++i) {
      engine_update(engine, dt);
    }
  }
%}
