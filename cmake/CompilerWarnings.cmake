# cmake/CompilerWarnings.cmake — Google-style warning flags
function(engine_set_warnings target)
  if(MSVC)
    target_compile_options(${target} PRIVATE /W4 /permissive-)
  else()
    target_compile_options(${target} PRIVATE
      -Wall -Wextra -Wpedantic
      -Wno-unused-parameter
      -Wno-missing-field-initializers
    )
  endif()
endfunction()
