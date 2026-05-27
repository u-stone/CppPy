# bindings/cython/setup_cython.py
# Alternative (non-CMake) build script using setuptools + Cython.
# Usage: python setup_cython.py build_ext --inplace

from setuptools import setup, Extension
from Cython.Build import cythonize
import os

engine_include = os.path.join(
    os.path.dirname(__file__), "..", "..", "engine", "include"
)

ext = Extension(
    name="engine_cython",
    sources=[
        os.path.join(os.path.dirname(__file__), "src", "cengine.pyx"),
        os.path.join(os.path.dirname(__file__), "src", "cython_cpp_wrap.cpp"),
        os.path.join(
            os.path.dirname(__file__), "..", "..", "engine", "src", "facade.cpp"
        ),
        os.path.join(
            os.path.dirname(__file__), "..", "..", "engine", "src", "scene.cpp"
        ),
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "engine",
            "src",
            "game_object.cpp",
        ),
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "engine",
            "src",
            "event_bus.cpp",
        ),
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "engine",
            "src",
            "thread_pool.cpp",
        ),
        os.path.join(
            os.path.dirname(__file__), "..", "..", "engine", "src", "c_api.cpp"
        ),
    ],
    include_dirs=[engine_include],
    language="c++",
    extra_compile_args=["-std=c++17"],
)

setup(
    name="engine_cython",
    ext_modules=cythonize(
        [ext],
        compiler_directives={"language_level": "3"},
    ),
    zip_safe=False,
)
