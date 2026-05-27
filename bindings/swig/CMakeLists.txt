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

target_link_libraries(engine_swig PRIVATE engine)

# SWIG 4.4+ has built-in support for building against release Python even
# in Debug mode (it undefs _DEBUG before including Python.h).  The feature
# is gated behind this define.
target_compile_definitions(engine_swig PRIVATE
  $<$<AND:$<CONFIG:Debug>,$<PLATFORM_ID:Windows>>:SWIG_PYTHON_INTERPRETER_NO_DEBUG>
)

# On Windows, pyconfig.h uses #pragma comment(lib, "python3xx.lib") to
# auto-link the Python import library.  In Debug builds it requests the
# _d variant which the standard Python distribution does not ship.
#
# Strategy: do NOT use ${Python3_LIBRARIES} (which may resolve to the
# debug lib under multi-config generators).  Instead, always link the
# release import library directly, and in Debug mode additionally
# suppress the unwanted _d.lib from the pragma.
if(WIN32)
  set(_py_lib "${Python3_ROOT_DIR}/libs/python${Python3_VERSION_MAJOR}${Python3_VERSION_MINOR}.lib")
  target_link_libraries(engine_swig PRIVATE "${_py_lib}")
  target_link_options(engine_swig PRIVATE
    $<$<CONFIG:Debug>:/NODEFAULTLIB:python${Python3_VERSION_MAJOR}${Python3_VERSION_MINOR}_d.lib>
  )
else()
  target_link_libraries(engine_swig PRIVATE ${Python3_LIBRARIES})
endif()

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
    "$<TARGET_FILE_DIR:engine_swig>/"
)
