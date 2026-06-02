# bindings/nanobind/CMakeLists.txt
nanobind_add_module(_core_nanobind src/nanobind_bindings.cpp)

target_sources(_core_nanobind PRIVATE
  ${CMAKE_SOURCE_DIR}/engine/include/engine/cpp_api.h
  ${CMAKE_SOURCE_DIR}/engine/include/engine/facade.h
  ${CMAKE_SOURCE_DIR}/engine/include/engine/game_object.h
  ${CMAKE_SOURCE_DIR}/engine/include/engine/scene.h
)

target_link_libraries(_core_nanobind PRIVATE engine)

target_include_directories(_core_nanobind PRIVATE
  ${CMAKE_SOURCE_DIR}/engine/include
)

set_target_properties(_core_nanobind PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/_build/nanobind"
  OUTPUT_NAME "_core_nanobind"
)

set(_pkg "${CMAKE_SOURCE_DIR}/dist/$<CONFIG>/enginenanobind")

add_custom_command(TARGET _core_nanobind POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E make_directory "${_pkg}"
  COMMAND ${CMAKE_COMMAND} -E rename
    "$<TARGET_FILE:_core_nanobind>"
    "${_pkg}/_core$<TARGET_FILE_SUFFIX:_core_nanobind>"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${CMAKE_CURRENT_SOURCE_DIR}/python/__init__.py"
    "${_pkg}/"
  COMMENT "nanobind: assembling package enginenanobind/"
)

add_custom_command(TARGET _core_nanobind POST_BUILD
  COMMAND ${Python3_EXECUTABLE}
    ${CMAKE_SOURCE_DIR}/scripts/generate_stubs.py
    --scheme nanobind
    --module-dir "${_pkg}"
  COMMENT "nanobind: generating .pyi stubs"
)
