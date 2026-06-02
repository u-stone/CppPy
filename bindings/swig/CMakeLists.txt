find_package(Python3 REQUIRED COMPONENTS Development)

set(SWIG_MODULE_engineswig_name engineswig)

set_property(SOURCE src/engine.i PROPERTY CPLUSPLUS ON)
set_property(SOURCE src/engine.i PROPERTY SWIG_MODULE_NAME engineswig)
set_property(SOURCE src/engine.i PROPERTY SWIG_FLAGS
  "-I${CMAKE_SOURCE_DIR}/engine/include")

swig_add_library(engineswig
  LANGUAGE python
  SOURCES src/engine.i
)

target_sources(${SWIG_MODULE_engineswig_name} PRIVATE
  ${CMAKE_SOURCE_DIR}/engine/include/engine/c_api.h
)

target_link_libraries(engineswig PRIVATE engine)

target_compile_definitions(engineswig PRIVATE
  $<$<AND:$<CONFIG:Debug>,$<PLATFORM_ID:Windows>>:SWIG_PYTHON_INTERPRETER_NO_DEBUG>
)

if(WIN32)
  set(_py_lib "${Python3_ROOT_DIR}/libs/python${Python3_VERSION_MAJOR}${Python3_VERSION_MINOR}.lib")
  target_link_libraries(engineswig PRIVATE "${_py_lib}")
  target_link_options(engineswig PRIVATE
    $<$<CONFIG:Debug>:/NODEFAULTLIB:python${Python3_VERSION_MAJOR}${Python3_VERSION_MINOR}_d.lib>
  )
else()
  target_link_libraries(engineswig PRIVATE ${Python3_LIBRARIES})
endif()

target_include_directories(engineswig PRIVATE
  ${CMAKE_SOURCE_DIR}/engine/include
  ${Python3_INCLUDE_DIRS}
)

set_target_properties(${SWIG_MODULE_engineswig_name} PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/_build/swig"
)

# SWIG generates engineswig.py (wrapper) + _engineswig.pyd (binary).
# The wrapper does 'import _engineswig', so the .pyd must live at the
# same level as the package directory (both under $<CONFIG>/).
set(_pkg "${CMAKE_SOURCE_DIR}/dist/$<CONFIG>/engineswig")

add_custom_command(TARGET engineswig POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E make_directory "${_pkg}"
  COMMAND ${CMAKE_COMMAND} -E rename
    "$<TARGET_FILE:engineswig>"
    "${_pkg}/_engineswig$<TARGET_FILE_SUFFIX:engineswig>"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${CMAKE_CURRENT_BINARY_DIR}/engineswig.py"
    "${_pkg}/__init__.py"
  COMMENT "SWIG: assembling package engineswig/"
)

add_custom_command(TARGET engineswig POST_BUILD
  COMMAND ${Python3_EXECUTABLE}
    ${CMAKE_SOURCE_DIR}/scripts/generate_stubs.py
    --scheme swig
    --module-dir "${_pkg}"
  COMMENT "SWIG: generating .pyi stubs"
)
