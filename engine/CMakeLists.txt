# engine/CMakeLists.txt — shared static library

# Headers exposed to the IDE (VS Solution Explorer). Not needed for
# compilation since target_include_directories handles the include path,
# but VS requires explicit source listing to show them in the project.
set(ENGINE_HEADERS
  include/engine/c_api.h
  include/engine/cpp_api.h
  include/engine/event_bus.h
  include/engine/facade.h
  include/engine/game_object.h
  include/engine/lifecycle.h
  include/engine/scene.h
  include/engine/thread_pool.h
)

add_library(engine STATIC
  src/thread_pool.cpp
  src/event_bus.cpp
  src/game_object.cpp
  src/scene.cpp
  src/facade.cpp
  src/c_api.cpp
  src/cpp_api.cpp
  ${ENGINE_HEADERS}
)

target_include_directories(engine
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/engine/include>
    $<INSTALL_INTERFACE:include>
)

target_link_libraries(engine PUBLIC Threads::Threads)
engine_set_warnings(engine)
