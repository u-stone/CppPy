# bindings/nanobind/CMakeLists.txt
nanobind_add_module(engine_nanobind src/nanobind_bindings.cpp)

target_link_libraries(engine_nanobind PRIVATE engine)

target_include_directories(engine_nanobind PRIVATE
  ${CMAKE_SOURCE_DIR}/engine/include
)

set_target_properties(engine_nanobind PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/nanobind"
  RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/nanobind"
)
