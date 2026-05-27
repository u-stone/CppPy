# engine/CMakeLists.txt — shared static library
add_library(engine STATIC
  src/thread_pool.cpp
  src/event_bus.cpp
  src/game_object.cpp
  src/scene.cpp
  src/facade.cpp
  src/c_api.cpp
  src/cpp_api.cpp
)

target_include_directories(engine
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/engine/include>
    $<INSTALL_INTERFACE:include>
)

target_link_libraries(engine PUBLIC Threads::Threads)
engine_set_warnings(engine)
