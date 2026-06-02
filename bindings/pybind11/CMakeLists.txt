# bindings/pybind11/CMakeLists.txt
pybind11_add_module(_core_pybind11 src/pybind11_bindings.cpp)

target_sources(_core_pybind11 PRIVATE
  ${CMAKE_SOURCE_DIR}/engine/include/engine/cpp_api.h
  ${CMAKE_SOURCE_DIR}/engine/include/engine/facade.h
  ${CMAKE_SOURCE_DIR}/engine/include/engine/game_object.h
  ${CMAKE_SOURCE_DIR}/engine/include/engine/scene.h
)

target_link_libraries(_core_pybind11 PRIVATE engine)

target_include_directories(_core_pybind11 PRIVATE
  ${CMAKE_SOURCE_DIR}/engine/include
)

# Output to a scheme-private temp directory to avoid _core filename conflicts.
set_target_properties(_core_pybind11 PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/_build/pybind11"
  OUTPUT_NAME "_core_pybind11"
)

# Final package location: build/bindings_output/<Config>/engine_pybind/
set(_pkg "${CMAKE_BINARY_DIR}/bindings_output/$<CONFIG>/engine_pybind")

add_custom_command(TARGET _core_pybind11 POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E make_directory "${_pkg}"
  COMMAND ${CMAKE_COMMAND} -E rename
    "$<TARGET_FILE:_core_pybind11>"
    "${_pkg}/_core$<TARGET_FILE_SUFFIX:_core_pybind11>"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${CMAKE_CURRENT_SOURCE_DIR}/python/__init__.py"
    "${_pkg}/"
  COMMENT "pybind11: assembling package engine_pybind/"
)

add_custom_command(TARGET _core_pybind11 POST_BUILD
  COMMAND ${Python3_EXECUTABLE}
    ${CMAKE_SOURCE_DIR}/scripts/generate_stubs.py
    --scheme pybind11
    --module-dir "${_pkg}"
  COMMENT "pybind11: generating .pyi stubs"
)
