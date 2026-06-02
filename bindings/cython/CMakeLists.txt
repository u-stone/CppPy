find_package(Python3 REQUIRED COMPONENTS Development)

set(CYTHON_OUTPUT_DIR "${CMAKE_CURRENT_BINARY_DIR}/cython_gen")
file(MAKE_DIRECTORY ${CYTHON_OUTPUT_DIR})

add_custom_command(
  OUTPUT ${CYTHON_OUTPUT_DIR}/engine_cython.cxx
  COMMAND ${CYTHON_EXECUTABLE}
    --cplus -3
    -o ${CYTHON_OUTPUT_DIR}/engine_cython.cxx
    ${CMAKE_CURRENT_SOURCE_DIR}/src/engine_cython.pyx
  COMMAND ${CMAKE_COMMAND}
    "-DGENERATED_FILE=${CYTHON_OUTPUT_DIR}/engine_cython.cxx"
    -P ${CMAKE_CURRENT_SOURCE_DIR}/cmake/patch_cython_debug.cmake
  DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/src/engine_cython.pyx
          ${CMAKE_CURRENT_SOURCE_DIR}/src/engine_cython.pxd
          ${CMAKE_CURRENT_SOURCE_DIR}/cmake/patch_cython_debug.cmake
  COMMENT "Cython compiling engine_cython.pyx -> engine_cython.cxx"
)

add_library(engine_cython MODULE
  ${CYTHON_OUTPUT_DIR}/engine_cython.cxx
  src/cython_cpp_wrap.cpp
)

target_sources(engine_cython PRIVATE
  ${CMAKE_SOURCE_DIR}/engine/include/engine/c_api.h
  ${CMAKE_CURRENT_SOURCE_DIR}/src/engine_cython.pxd
  ${CMAKE_CURRENT_SOURCE_DIR}/src/engine_cython.pyx
)

target_include_directories(engine_cython PRIVATE
  ${CMAKE_SOURCE_DIR}/engine/include
  ${Python3_INCLUDE_DIRS}
)

if(WIN32)
  set_target_properties(engine_cython PROPERTIES SUFFIX ".pyd")
endif()

target_link_libraries(engine_cython PRIVATE engine)

# On Windows, pyconfig.h uses #pragma comment(lib, "python3xx.lib") to
# auto-link the Python import library.  In Debug builds it requests the
# _d variant which the standard Python distribution does not ship.
if(WIN32)
  set(_py_lib "${Python3_ROOT_DIR}/libs/python${Python3_VERSION_MAJOR}${Python3_VERSION_MINOR}.lib")
  target_link_libraries(engine_cython PRIVATE "${_py_lib}")
  target_link_options(engine_cython PRIVATE
    $<$<CONFIG:Debug>:/NODEFAULTLIB:python${Python3_VERSION_MAJOR}${Python3_VERSION_MINOR}_d.lib>
  )
else()
  target_link_libraries(engine_cython PRIVATE ${Python3_LIBRARIES})
endif()

set_target_properties(engine_cython PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/cython"
  RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/cython"
)

# Generate .pyi type stubs via stubgen-pyx (Cython AST-based).
add_custom_command(TARGET engine_cython POST_BUILD
  COMMAND ${Python3_EXECUTABLE}
    ${CMAKE_SOURCE_DIR}/scripts/generate_stubs.py
    --scheme cython
    --module-dir "$<TARGET_FILE_DIR:engine_cython>"
  COMMENT "Cython: generating .pyi stubs"
)
