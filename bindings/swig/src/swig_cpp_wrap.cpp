// bindings/swig/src/swig_cpp_wrap.cpp
// Small C++ helper functions that SWIG cannot auto-generate from the .i file.

#include <iostream>
#include <string>

#include "engine/c_api.h"
#include "engine/cpp_api.h"
#include "engine/facade.h"
#include "engine/game_object.h"
#include "engine/scene.h"

// C++ style helper used by the SWIG-generated Python module.
// SWIG wraps c_api.h but we provide these as additional typed helpers.
namespace engine_swig {

void PrintEngineInfo(engine::EngineFacade &engine) {
  std::cout << "[SWIG] Engine initialized: " << engine.IsInitialized()
            << std::endl;
  auto names = engine.SceneNames();
  std::cout << "[SWIG] Scenes: " << names.size() << std::endl;
  for (const auto &n : names) {
    std::cout << "[SWIG]   - " << n << std::endl;
  }
}

} // namespace engine_swig
