#!/usr/bin/env python3
"""Package pre-compiled dist/ packages into distributable archives.

Formats:
  zip   — simple archive, unzip anywhere and add to PYTHONPATH
  wheel — standard .whl for pip install
  copy  — plain directory copy

Usage:
  python scripts/package_wheel.py --scheme pybind11 --config Debug
  python scripts/package_wheel.py --all --config Release --format wheel
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")

PACKAGE_META = {
    "pybind11": "enginepybind",
    "nanobind": "enginenanobind",
    "swig": "engineswig",
    "cython": "enginecython",
    "cffi": "enginecffi",
}

VERSION = "0.1.0"


def _find_python():
    venv = os.path.join(PROJECT_ROOT, "build", "venv", "Scripts", "python.exe")
    return venv if os.path.exists(venv) else sys.executable


def package_scheme(scheme, config, fmt="zip", python_exe=None):
    """Package one scheme."""
    if python_exe is None:
        python_exe = _find_python()

    pkg_name = PACKAGE_META[scheme]
    src = os.path.join(DIST_DIR, config, pkg_name) if config else os.path.join(DIST_DIR, pkg_name)

    if not os.path.isdir(src):
        print(f"  SKIP {pkg_name}: not found at {src}")
        return None

    if fmt == "wheel":
        return _build_wheel(pkg_name, src, python_exe)
    elif fmt == "zip":
        return _build_zip(pkg_name, src)
    elif fmt == "copy":
        out = os.path.join(DIST_DIR, "packages", pkg_name)
        if os.path.isdir(out):
            shutil.rmtree(out)
        shutil.copytree(src, out)
        print(f"  => {out}/")
        return out

    return None


def _build_zip(pkg_name, src):
    out = os.path.join(DIST_DIR, f"{pkg_name}-{VERSION}.zip")
    tmp = tempfile.mkdtemp()
    try:
        shutil.copytree(src, os.path.join(tmp, pkg_name))
        archive_base = os.path.join(DIST_DIR, f"{pkg_name}-{VERSION}")
        shutil.make_archive(archive_base, "zip", tmp)
        print(f"  => {archive_base}.zip")
        return f"{archive_base}.zip"
    finally:
        shutil.rmtree(tmp)


def _build_wheel(pkg_name, src, python_exe):
    """Build a standard .whl using python -m build."""
    tmp = tempfile.mkdtemp()
    try:
        # Copy package files into temp build dir
        pkg_dest = os.path.join(tmp, pkg_name)
        shutil.copytree(src, pkg_dest)

        # Write pyproject.toml with package-data to include .pyd/.dll
        with open(os.path.join(tmp, "pyproject.toml"), "w") as f:
            f.write(f"""\
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "{pkg_name}"
version = "{VERSION}"
description = "CppPy engine - Python binding"
requires-python = ">=3.8"

[tool.setuptools.package-data]
{pkg_name} = ["*.pyd", "*.dll", "*.so", "*.dylib", "*.pyi", "py.typed"]
""")

        # Build wheel into dist/.  Must run from tmp/ to avoid CppPy's own
        # build/ directory shadowing the 'build' pip package.
        result = subprocess.run(
            [python_exe, "-m", "build", "--wheel", "--outdir", DIST_DIR, "."],
            capture_output=True, text=True, cwd=tmp,
        )
        if result.returncode == 0:
            # Find the generated wheel
            for f in sorted(os.listdir(DIST_DIR), reverse=True):
                full = os.path.join(DIST_DIR, f)
                if f.startswith(pkg_name) and f.endswith(".whl"):
                    size_mb = os.path.getsize(full) / (1024 * 1024)
                    print(f"  => {full}  ({size_mb:.1f} MB)")
                    break
        else:
            print(f"  ERROR building wheel:\n{result.stderr}")
            return None
    finally:
        shutil.rmtree(tmp)


def main():
    parser = argparse.ArgumentParser(description="Package dist/ into distributable archives")
    parser.add_argument("--scheme", choices=list(PACKAGE_META))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--config", default="Release")
    parser.add_argument("--format", choices=["zip", "wheel", "copy"], default="zip")
    args = parser.parse_args()

    if args.all:
        schemes = list(PACKAGE_META)
    elif args.scheme:
        schemes = [args.scheme]
    else:
        parser.error("Specify --scheme or --all")

    python_exe = _find_python()
    for s in schemes:
        name = PACKAGE_META[s]
        print(f"\n=== {name} ({s}) ===")
        package_scheme(s, args.config, args.format, python_exe=python_exe)


if __name__ == "__main__":
    main()
