add_library(engine_c SHARED src/cffi_c_impl.cpp)

target_sources(engine_c PRIVATE
  ${CMAKE_SOURCE_DIR}/engine/include/engine/c_api.h
)

target_include_directories(engine_c PRIVATE ${CMAKE_SOURCE_DIR}/engine/include)

target_link_libraries(engine_c PRIVATE engine Threads::Threads)

if(WIN32)
  target_sources(engine_c PRIVATE src/engine_c.def)
endif()

set_target_properties(engine_c PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/_build/cffi"
)

set(_pkg "${CMAKE_SOURCE_DIR}/dist/$<CONFIG>/engine_cffi")

add_custom_command(TARGET engine_c POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E make_directory "${_pkg}"
  COMMAND ${CMAKE_COMMAND} -E rename
    "$<TARGET_FILE:engine_c>"
    "${_pkg}/engine_c$<TARGET_FILE_SUFFIX:engine_c>"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${CMAKE_CURRENT_SOURCE_DIR}/python/cffi_bridge.py"
    "${_pkg}/"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${CMAKE_CURRENT_SOURCE_DIR}/python/cffi_build.py"
    "${_pkg}/"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${CMAKE_CURRENT_SOURCE_DIR}/python/__init__.py"
    "${_pkg}/"
  COMMENT "CFFI: assembling package engine_cffi/"
)

add_custom_command(TARGET engine_c POST_BUILD
  COMMAND ${Python3_EXECUTABLE}
    ${CMAKE_SOURCE_DIR}/scripts/generate_stubs.py
    --scheme cffi
    --module-dir "${_pkg}"
  COMMENT "CFFI: installing .pyi stubs"
)
