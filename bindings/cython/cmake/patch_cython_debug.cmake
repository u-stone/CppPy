# Patches the Cython-generated .cxx to prevent the _DEBUG -> Py_DEBUG ->
# Py_REF_DEBUG chain on Windows.  Uses the same #undef / #define guard that
# SWIG 4.4+ and pybind11 apply around Python.h.
#
# Invoked by the custom_command in bindings/cython/CMakeLists.txt right
# after Cython produces the .cxx file.

file(READ "${GENERATED_FILE}" CONTENT)
string(FIND "${CONTENT}" "#include \"Python.h\"" PYTHON_H_POS)

if(PYTHON_H_POS EQUAL -1)
  message(FATAL_ERROR "patch_cython_debug: could not find #include \"Python.h\" in ${GENERATED_FILE}")
endif()

string(SUBSTRING "${CONTENT}" 0 ${PYTHON_H_POS} BEFORE)
math(EXPR REST_START "${PYTHON_H_POS}")
string(SUBSTRING "${CONTENT}" ${REST_START} -1 REST)

string(FIND "${REST}" "\n" EOL_POS)
math(EXPR INCLUDE_LEN "${EOL_POS} + 1")
string(SUBSTRING "${REST}" 0 ${INCLUDE_LEN} INCLUDE_LINE)

math(EXPR AFTER_START "${EOL_POS} + 1")
string(SUBSTRING "${REST}" ${AFTER_START} -1 AFTER)

set(PATCHED "${BEFORE}#undef _DEBUG\n${INCLUDE_LINE}#define _DEBUG 1\n${AFTER}")
file(WRITE "${GENERATED_FILE}" "${PATCHED}")
message(STATUS "Cython: wrapped Python.h with _DEBUG guard in ${GENERATED_FILE}")
