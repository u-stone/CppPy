#!/usr/bin/env python3
# scripts/generate_stubs.py
# Generate .pyi type-stub files and/or API docs for all 5 binding schemes.
#
# Called from CMake POST_BUILD custom commands, or standalone:
#   python scripts/generate_stubs.py --scheme pybind11 --module-dir <dir>

import argparse
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)


def _python():
    return sys.executable


def _run(cmd, **kwargs):
    print(f"  [stubs] {' '.join(cmd)}")
    return subprocess.run(cmd, check=False, **kwargs)


# ── nanobind ──────────────────────────────────────────────────────────────
def gen_nanobind(module_dir):
    """Use nanobind's native stub generator (reads __nb_signature__)."""
    # nanobind.stubgen -O expects a directory, not a filename
    # PYTHONPATH must include module_dir so _core.pyd can be imported.
    result = _run(
        [
            _python(),
            "-m",
            "nanobind.stubgen",
            "-m",
            "_core",
            "-O",
            module_dir,
        ],
        env={**os.environ, "PYTHONPATH": module_dir},
    )
    if result.returncode == 0:
        marker = os.path.join(module_dir, "py.typed")
        open(marker, "w").close()
        print(f"  [stubs] wrote {marker}")
    else:
        print("  [stubs] nanobind stubgen FAILED — continuing", file=sys.stderr)


# ── pybind11 ──────────────────────────────────────────────────────────────
def gen_pybind11(module_dir):
    """Generate stubs via pybind11-stubgen (runtime introspection)."""
    _run(
        [
            _python(),
            "-m",
            "pybind11_stubgen",
            "_core",
            "-o",
            module_dir,
        ],
        env={**os.environ, "PYTHONPATH": module_dir},
    )
    marker = os.path.join(module_dir, "py.typed")
    open(marker, "w").close()


# ── Cython ────────────────────────────────────────────────────────────────
def gen_cython(module_dir):
    """Generate stubs from .pyx / .pxd source via stubgen-pyx (AST-based)."""
    cython_src = os.path.join(PROJECT_ROOT, "bindings", "cython", "src")
    _run(
        [
            _python(),
            "-m",
            "stubgen_pyx",
            cython_src,
            "--output-dir",
            module_dir,
        ]
    )
    marker = os.path.join(module_dir, "py.typed")
    open(marker, "w").close()


# ── SWIG ──────────────────────────────────────────────────────────────────
def gen_swig(module_dir):
    """SWIG has no dedicated .pyi tool.

    The SWIG-generated wrapper is installed as engineswig/__init__.py.
    _engineswig.pyd sits alongside the package directory (at the PYTHONPATH
    root) so the wrapper's absolute 'import _engineswig' resolves.

    We attempt mypy stubgen with PYTHONPATH set to the packages root
    (one level above the package) so both the package and _engineswig.pyd
    are importable.
    """
    packages_root = os.path.dirname(module_dir)
    stubgen_exe = os.path.join(os.path.dirname(_python()), "stubgen.exe")
    if not os.path.exists(stubgen_exe):
        stubgen_exe = os.path.join(os.path.dirname(_python()), "stubgen")

    result = _run(
        [
            stubgen_exe,
            "-m",
            "engineswig",
            "-o",
            packages_root,
        ],
        env={**os.environ, "PYTHONPATH": packages_root},
    )

    if result.returncode != 0:
        print(
            "  [stubs] mypy stubgen failed for SWIG "
            "(expected — SWIG wrapper uses absolute import)"
        )
        print("  [stubs] Instead, read engineswig/__init__.py or use help(engineswig).")

    marker = os.path.join(module_dir, "py.typed")
    open(marker, "w").close()
    print(f"  [stubs] wrote {marker}")


# ── CFFI ──────────────────────────────────────────────────────────────────
def gen_cffi(module_dir):
    """CFFI/ctypes has no auto-stub tool.

    We ship a hand-written .pyi file alongside the DLL.
    The stub is maintained at bindings/cffi/python/cffi_bridge.pyi.
    """
    src = os.path.join(PROJECT_ROOT, "bindings", "cffi", "python", "cffi_bridge.pyi")
    import shutil

    dst = os.path.join(module_dir, "cffi_bridge.pyi")
    shutil.copyfile(src, dst)
    marker = os.path.join(module_dir, "py.typed")
    open(marker, "w").close()
    print(f"  [stubs] {src} -> {dst}")


# ── dispatch ──────────────────────────────────────────────────────────────
GENERATORS = {
    "nanobind": gen_nanobind,
    "pybind11": gen_pybind11,
    "cython": gen_cython,
    "swig": gen_swig,
    "cffi": gen_cffi,
}


def main():
    parser = argparse.ArgumentParser(description="Generate .pyi stubs for CppPy bindings")
    parser.add_argument("--scheme", required=True, choices=list(GENERATORS) + ["all"])
    parser.add_argument(
        "--module-dir", required=True, help="Directory containing the built .pyd/.so/.dll"
    )
    args = parser.parse_args()

    module_dir = os.path.abspath(args.module_dir)

    if args.scheme == "all":
        for scheme, gen in GENERATORS.items():
            print(f"\n[stubs] === {scheme} ===")
            gen(module_dir)
    else:
        GENERATORS[args.scheme](module_dir)


if __name__ == "__main__":
    main()
