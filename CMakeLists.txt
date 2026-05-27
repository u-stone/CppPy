cmake_minimum_required(VERSION 3.20)
project(CppPy VERSION 1.0.0 LANGUAGES CXX C)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(BUILD_PYBIND11 "Build pybind11 bindings" ON)
option(BUILD_NANOBIND "Build nanobind bindings" ON)
option(BUILD_SWIG "Build SWIG bindings" ON)
option(BUILD_CYTHON "Build Cython bindings" ON)
option(BUILD_CFFI "Build CFFI shared library" ON)

# --- Prerequisites ---
find_package(Threads REQUIRED)

# Only locate the interpreter at top level. Each binding subdirectory
# finds its own Python development libraries to avoid target collisions.
find_package(Python3 REQUIRED COMPONENTS Interpreter)

# Determine the base Python installation from the venv. This ensures
# find_package(Python) / find_package(Python3) in subdirectories resolve
# the correct Python version and its development artifacts.
execute_process(
  COMMAND "${Python3_EXECUTABLE}" -c
    "import sys; print(sys.base_prefix, end='')"
  OUTPUT_VARIABLE PYTHON_BASE_PREFIX
  ERROR_QUIET
  OUTPUT_STRIP_TRAILING_WHITESPACE
)
message(STATUS "Python base install: ${PYTHON_BASE_PREFIX}")

# Pin both Python and Python3 to the same base installation.
# Using CACHE FORCE ensures nanobind/SWIG/Cython subdirectory
# find_package calls resolve to this Python — not a random system one.
set(Python3_ROOT_DIR "${PYTHON_BASE_PREFIX}" CACHE PATH "Python3 root" FORCE)
set(Python_ROOT_DIR "${PYTHON_BASE_PREFIX}" CACHE PATH "Python root" FORCE)
set(Python3_EXECUTABLE "${Python3_EXECUTABLE}" CACHE FILEPATH "Python3 executable" FORCE)
set(Python_EXECUTABLE "${Python3_EXECUTABLE}" CACHE FILEPATH "Python executable" FORCE)

# --- CMake modules ---
list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")
include(CompilerWarnings)

# --- Engine library ---
add_subdirectory(engine)

# --- 3rdparty libraries (pre-downloaded by manage.py setup) ---
set(THIRDPARTY_DIR "${CMAKE_SOURCE_DIR}/3rdparty")
set(THIRDPARTY_BUILD_DIR "${CMAKE_BINARY_DIR}/3rdparty_build")

function(add_3rdparty_subdirectory name subdir)
  if(EXISTS "${THIRDPARTY_DIR}/${name}/${subdir}")
    add_subdirectory("${THIRDPARTY_DIR}/${name}/${subdir}"
                     "${THIRDPARTY_BUILD_DIR}/${name}")
  else()
    add_subdirectory("${THIRDPARTY_DIR}/${name}"
                     "${THIRDPARTY_BUILD_DIR}/${name}")
  endif()
endfunction()

# --- Binding schemes ---
if(BUILD_PYBIND11)
  if(NOT EXISTS "${THIRDPARTY_DIR}/pybind11/CMakeLists.txt")
    message(FATAL_ERROR "pybind11 not found in 3rdparty/. Run 'manage.py setup' first.")
  endif()
  add_3rdparty_subdirectory(pybind11 "")
  add_subdirectory(bindings/pybind11)
endif()

if(BUILD_NANOBIND)
  if(NOT EXISTS "${THIRDPARTY_DIR}/nanobind/CMakeLists.txt")
    message(FATAL_ERROR "nanobind not found in 3rdparty/. Run 'manage.py setup' first.")
  endif()
  # nanobind requires find_package(Python) (no version suffix) to create
  # the Python::Module target before nanobind-config.cmake is included.
  find_package(Python COMPONENTS Interpreter Development REQUIRED)
  add_3rdparty_subdirectory(nanobind "")
  add_subdirectory(bindings/nanobind)
endif()

if(BUILD_SWIG)
  # Point to pre-built swig.exe and its Lib directory in 3rdparty
  get_filename_component(_swig_exe "${THIRDPARTY_DIR}/swig-install/swig.exe"
    ABSOLUTE)
  set(SWIG_EXECUTABLE "${_swig_exe}"
      CACHE FILEPATH "Path to swig executable")
  set(SWIG_DIR "${THIRDPARTY_DIR}/swig-install/Lib"
      CACHE PATH "Path to swig library")
  find_package(SWIG QUIET)
  if(SWIG_FOUND)
    include(UseSWIG)
    add_subdirectory(bindings/swig)
  else()
    message(WARNING "SWIG not found -- skipping SWIG bindings")
  endif()
endif()

if(BUILD_CYTHON)
  include(FindCython)
  if(CYTHON_FOUND)
    add_subdirectory(bindings/cython)
  else()
    message(WARNING "Cython not found -- skipping Cython bindings")
  endif()
endif()

if(BUILD_CFFI)
  add_subdirectory(bindings/cffi)
endif()
