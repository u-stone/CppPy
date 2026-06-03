// cpp_api.h is a header-only template library.
// This compilation unit exists to verify the header compiles and to house
// any non-template helpers or explicit template instantiations if needed.

#include "engine/cpp_api.h"

// Force instantiation of common templates for linker visibility.
namespace engine::cpp_api {

// Verify the header compiles.
void __cpp_api_anchor() {
  (void)&AddComponent<TransformComponent>;
  (void)&AddComponent<AIComponent>;
  (void)&GetComponent<TransformComponent>;
  (void)&GetComponent<AIComponent>;
}

} // namespace engine::cpp_api
