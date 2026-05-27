find_package(Python3 REQUIRED COMPONENTS Development)

set(SWIG_MODULE_engine_swig_name engine_swig)

# SWIG needs to find the C API header for %include
set_property(SOURCE src/engine.i PROPERTY CPLUSPLUS ON)
set_property(SOURCE src/engine.i PROPERTY SWIG_MODULE_NAME engine_swig)
set_property(SOURCE src/engine.i PROPERTY SWIG_FLAGS
  "-I${CMAKE_SOURCE_DIR}/engine/include")

swig_add_library(engine_swig
  LANGUAGE python
  SOURCES src/engine.i
)

target_sources(${SWIG_MODULE_engine_swig_name} PRIVATE
  ${CMAKE_SOURCE_DIR}/engine/include/engine/c_api.h
)

target_link_libraries(engine_swig PRIVATE engine ${Python3_LIBRARIES})

target_include_directories(engine_swig PRIVATE
  ${CMAKE_SOURCE_DIR}/engine/include
  ${Python3_INCLUDE_DIRS}
)

set_target_properties(${SWIG_MODULE_engine_swig_name} PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/swig"
  RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/swig"
)

add_custom_command(TARGET engine_swig POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${CMAKE_CURRENT_BINARY_DIR}/engine_swig.py"
    "${CMAKE_BINARY_DIR}/bindings_output/swig/"
)
