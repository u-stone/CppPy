# bindings/pybind11/CMakeLists.txt
pybind11_add_module(engine_pybind src/pybind11_bindings.cpp)

target_sources(engine_pybind PRIVATE
  ${CMAKE_SOURCE_DIR}/engine/include/engine/cpp_api.h
  ${CMAKE_SOURCE_DIR}/engine/include/engine/facade.h
  ${CMAKE_SOURCE_DIR}/engine/include/engine/game_object.h
  ${CMAKE_SOURCE_DIR}/engine/include/engine/scene.h
)

target_link_libraries(engine_pybind PRIVATE engine)

target_include_directories(engine_pybind PRIVATE
  ${CMAKE_SOURCE_DIR}/engine/include
)

# Output to a consistent location for manage.py to find
set_target_properties(engine_pybind PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/pybind11"
  RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bindings_output/pybind11"
)
