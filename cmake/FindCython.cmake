# cmake/FindCython.cmake — locate Cython executable

# Search near Python interpreter first (covers venv on all platforms)
get_filename_component(_python_dir "${Python3_EXECUTABLE}" DIRECTORY)

find_program(CYTHON_EXECUTABLE
  NAMES cython cython3 cython.exe
  HINTS "${_python_dir}"
  PATHS "${Python3_SITELIB}/Cython"
  DOC "Cython executable"
)

if(CYTHON_EXECUTABLE)
  execute_process(
    COMMAND ${CYTHON_EXECUTABLE} --version
    OUTPUT_VARIABLE CYTHON_VERSION_OUTPUT
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET
  )
  string(REGEX MATCH "[0-9]+\\.[0-9]+\\.[0-9]+" CYTHON_VERSION
         "${CYTHON_VERSION_OUTPUT}")
  message(STATUS "Found Cython: ${CYTHON_EXECUTABLE} (version ${CYTHON_VERSION})")
  set(CYTHON_FOUND TRUE)
else()
  set(CYTHON_FOUND FALSE)
  message(WARNING "Cython executable not found")
endif()

mark_as_advanced(CYTHON_EXECUTABLE)
