// bindings/cython/src/cython_cpp_wrap.cpp
// C++ helper functions invoked by the Cython module for operations
// that require direct C++ API access (STL types, templates, etc.).

#include "engine/c_api.h"
#include "engine/cpp_api.h"
#include "engine/facade.h"
#include "engine/game_object.h"
#include "engine/scene.h"

// Expose via extern "C" for Cython to cimport
extern "C" {

void *engine_cpp_create_from_facade() {
  auto *engine = new engine::EngineFacade();
  return static_cast<void *>(engine);
}

void engine_cpp_destroy_facade(void *ptr) {
  delete static_cast<engine::EngineFacade *>(ptr);
}

int engine_cpp_batch_create(void *engine_ptr, const char *scene_name, int count,
                            const char *prefix) {
  auto &f = *static_cast<engine::EngineFacade *>(engine_ptr);
  auto scene = f.CreateScene(scene_name ? scene_name : "Batch");
  auto objects = engine::cpp_api::BatchCreateObjects(scene, count,
                                                     prefix ? prefix : "obj");
  return static_cast<int>(objects.size());
}

} // extern "C"
