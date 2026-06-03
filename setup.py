# CppPy — editable install support
#
#   pip install -e .       # development mode (no PYTHONPATH needed)
#   python setup.py develop  # same, via setuptools directly
#
# During editable install, setuptools links the packages in dist/<Config>/
# into site-packages so 'import enginepybind' etc. work from anywhere.
# The .pyd files must already be compiled (run manage.py build first).

from setuptools import setup, find_packages
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(PROJECT_ROOT, "dist")

# Auto-detect the build configuration directory
def _find_config():
    try:
        for entry in os.listdir(DIST):
            p = os.path.join(DIST, entry)
            if os.path.isdir(p) and any(
                f.startswith("engine") for f in os.listdir(p)
                if os.path.isdir(os.path.join(p, f))
            ):
                return p
    except OSError:
        pass
    raise RuntimeError(
        "No compiled packages found in dist/. Run 'manage.py build' first."
    )

pkg_root = _find_config()

# setuptools requires package_dir to be relative to setup.py.
# Convert the absolute path to a relative one.
rel_pkg_root = os.path.relpath(pkg_root, PROJECT_ROOT)

setup(
    name="cpppy-engine",
    version="0.1.0",
    description="C++17 game engine kernel with 5 Python binding schemes",
    license="MIT",
    python_requires=">=3.8",
    packages=find_packages(where=pkg_root),
    package_dir={"": rel_pkg_root},
)
