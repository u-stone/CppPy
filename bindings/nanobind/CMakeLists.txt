# bindings/nanobind/CMakeLists.txt
nanobind_add_module(engine_nanobind src/nanobind_bindings.cpp)

target_sources(engine_nanobind PRIVATE
  ${CMAKE_SOURCE_DIR}/engine/include/engine/cpp_api.h
  ${CMAKE_SOURCE_DIR}/engine/include/engine/facade.h
  ${CMAKE_SOURCE_DIR}/engine/include/engine/game_object.h
  ${CMAKE_SOURCE_DIR}/engine/include/engine/scene.h
)

target_link_libraries(engine_nanobind PRIVATE engine)

target_include_directories(engine_nanobind PRIVATE
  ${CMAKE_SOURCE_DIR}/engine/include
)

set_target_properties(engine_nanobind PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/nanobind"
  RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/nanobind"
)
