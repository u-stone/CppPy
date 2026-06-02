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

# Generate .pyi type stubs (nanobind built-in, reads __nb_signature__).
add_custom_command(TARGET engine_nanobind POST_BUILD
  COMMAND ${Python3_EXECUTABLE}
    ${CMAKE_SOURCE_DIR}/scripts/generate_stubs.py
    --scheme nanobind
    --module-dir "$<TARGET_FILE_DIR:engine_nanobind>"
  COMMENT "nanobind: generating .pyi stubs"
)
