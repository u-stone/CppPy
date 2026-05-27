find_package(Python3 REQUIRED COMPONENTS Development)

set(CYTHON_OUTPUT_DIR "${CMAKE_CURRENT_BINARY_DIR}/cython_gen")
file(MAKE_DIRECTORY ${CYTHON_OUTPUT_DIR})

add_custom_command(
  OUTPUT ${CYTHON_OUTPUT_DIR}/engine_cython.cxx
  COMMAND ${CYTHON_EXECUTABLE}
    --cplus -3
    -o ${CYTHON_OUTPUT_DIR}/engine_cython.cxx
    ${CMAKE_CURRENT_SOURCE_DIR}/src/engine_cython.pyx
  DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/src/engine_cython.pyx
          ${CMAKE_CURRENT_SOURCE_DIR}/src/engine_cython.pxd
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

target_link_libraries(engine_cython PRIVATE engine ${Python3_LIBRARIES})

set_target_properties(engine_cython PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/cython"
  RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/cython"
)
