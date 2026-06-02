add_library(engine_c SHARED src/cffi_c_impl.cpp)

target_sources(engine_c PRIVATE
  ${CMAKE_SOURCE_DIR}/engine/include/engine/c_api.h
)

target_include_directories(engine_c PRIVATE ${CMAKE_SOURCE_DIR}/engine/include)

target_link_libraries(engine_c PRIVATE engine Threads::Threads)

# On Windows, symbols from the static library must be explicitly exported.
# Use a .def file to list all C API exports for LoadLibrary/ctypes.
if(WIN32)
  target_sources(engine_c PRIVATE src/engine_c.def)
endif()

set_target_properties(engine_c PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/cffi"
  RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/cffi"
)

add_custom_command(TARGET engine_c POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${CMAKE_CURRENT_SOURCE_DIR}/python/cffi_build.py"
    "$<TARGET_FILE_DIR:engine_c>/"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${CMAKE_CURRENT_SOURCE_DIR}/python/cffi_bridge.py"
    "$<TARGET_FILE_DIR:engine_c>/"
  COMMAND ${Python3_EXECUTABLE}
    ${CMAKE_SOURCE_DIR}/scripts/generate_stubs.py
    --scheme cffi
    --module-dir "$<TARGET_FILE_DIR:engine_c>"
  COMMENT "CFFI: installing hand-written .pyi stubs"
)
