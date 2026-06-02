find_package(Python3 REQUIRED COMPONENTS Development)

set(CYTHON_OUTPUT_DIR "${CMAKE_CURRENT_BINARY_DIR}/cython_gen")
file(MAKE_DIRECTORY ${CYTHON_OUTPUT_DIR})

add_custom_command(
  OUTPUT ${CYTHON_OUTPUT_DIR}/_core.cxx
  COMMAND ${CYTHON_EXECUTABLE}
    --cplus -3
    -o ${CYTHON_OUTPUT_DIR}/_core.cxx
    ${CMAKE_CURRENT_SOURCE_DIR}/src/_core.pyx
  COMMAND ${CMAKE_COMMAND}
    "-DGENERATED_FILE=${CYTHON_OUTPUT_DIR}/_core.cxx"
    -P ${CMAKE_CURRENT_SOURCE_DIR}/cmake/patch_cython_debug.cmake
  DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/src/_core.pyx
          ${CMAKE_CURRENT_SOURCE_DIR}/src/_core.pxd
          ${CMAKE_CURRENT_SOURCE_DIR}/cmake/patch_cython_debug.cmake
  COMMENT "Cython compiling _core.pyx -> _core.cxx"
)

add_library(_core_cython MODULE
  ${CYTHON_OUTPUT_DIR}/_core.cxx
  src/cython_cpp_wrap.cpp
)

target_sources(_core_cython PRIVATE
  ${CMAKE_SOURCE_DIR}/engine/include/engine/c_api.h
  ${CMAKE_CURRENT_SOURCE_DIR}/src/_core.pxd
  ${CMAKE_CURRENT_SOURCE_DIR}/src/_core.pyx
)

target_include_directories(_core_cython PRIVATE
  ${CMAKE_SOURCE_DIR}/engine/include
  ${Python3_INCLUDE_DIRS}
)

if(WIN32)
  set_target_properties(_core_cython PROPERTIES SUFFIX ".pyd")
endif()

target_link_libraries(_core_cython PRIVATE engine)

if(WIN32)
  set(_py_lib "${Python3_ROOT_DIR}/libs/python${Python3_VERSION_MAJOR}${Python3_VERSION_MINOR}.lib")
  target_link_libraries(_core_cython PRIVATE "${_py_lib}")
  target_link_options(_core_cython PRIVATE
    $<$<CONFIG:Debug>:/NODEFAULTLIB:python${Python3_VERSION_MAJOR}${Python3_VERSION_MINOR}_d.lib>
  )
else()
  target_link_libraries(_core_cython PRIVATE ${Python3_LIBRARIES})
endif()

set_target_properties(_core_cython PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/_build/cython"
  OUTPUT_NAME "_core_cython"
)

set(_pkg "${CMAKE_SOURCE_DIR}/dist/$<CONFIG>/enginecython")

add_custom_command(TARGET _core_cython POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E make_directory "${_pkg}"
  COMMAND ${CMAKE_COMMAND} -E rename
    "$<TARGET_FILE:_core_cython>"
    "${_pkg}/_core$<TARGET_FILE_SUFFIX:_core_cython>"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${CMAKE_CURRENT_SOURCE_DIR}/python/__init__.py"
    "${_pkg}/"
  COMMENT "Cython: assembling package enginecython/"
)

add_custom_command(TARGET _core_cython POST_BUILD
  COMMAND ${Python3_EXECUTABLE}
    ${CMAKE_SOURCE_DIR}/scripts/generate_stubs.py
    --scheme cython
    --module-dir "${_pkg}"
  COMMENT "Cython: generating .pyi stubs"
)
