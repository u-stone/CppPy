#!/usr/bin/env python3
"""Package pre-compiled Python packages from dist/ into distributable archives.

Two output formats:
  1. zip archives — simplest, unzip anywhere and add to PYTHONPATH
  2. Directory copy  — copy to any location on PYTHONPATH

Usage:
  python scripts/package_wheel.py --scheme pybind11 [--config Release]
  python scripts/package_wheel.py --all --config Debug
"""

import argparse
import os
import shutil
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")

PACKAGE_META = {
    "pybind11": "enginepybind",
    "nanobind": "enginenanobind",
    "swig":     "engineswig",
    "cython":   "enginecython",
    "cffi":     "enginecffi",
}

VERSION = "0.1.0"


def package_scheme(scheme, config, fmt="zip"):
    """Package one scheme."""
    pkg_name = PACKAGE_META[scheme]
    src = os.path.join(DIST_DIR, config, pkg_name) if config else os.path.join(DIST_DIR, pkg_name)

    if not os.path.isdir(src):
        print(f"  SKIP {pkg_name}: not found at {src}")
        return None

    if fmt == "zip":
        out = os.path.join(DIST_DIR, f"{pkg_name}-{VERSION}.zip")

        # Use make_archive for reliable zip creation
        import tempfile
        tmp = tempfile.mkdtemp()
        try:
            tmp_pkg = os.path.join(tmp, pkg_name)
            shutil.copytree(src, tmp_pkg)
            archive_base = os.path.join(DIST_DIR, f"{pkg_name}-{VERSION}")
            shutil.make_archive(archive_base, "zip", tmp)
            print(f"  => {archive_base}.zip")
            return f"{archive_base}.zip"
        finally:
            shutil.rmtree(tmp)

    elif fmt == "copy":
        out = os.path.join(DIST_DIR, "packages", pkg_name)
        if os.path.isdir(out):
            shutil.rmtree(out)
        shutil.copytree(src, out)
        print(f"  => {out}/")
        return out

    return None


def main():
    parser = argparse.ArgumentParser(description="Package dist/ into distributable archives")
    parser.add_argument("--scheme", choices=list(PACKAGE_META))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--config", default="Release")
    parser.add_argument("--format", choices=["zip", "copy"], default="zip")
    args = parser.parse_args()

    if args.all:
        schemes = list(PACKAGE_META)
    elif args.scheme:
        schemes = [args.scheme]
    else:
        parser.error("Specify --scheme or --all")

    for s in schemes:
        name = PACKAGE_META[s]
        print(f"\n=== {name} ({s}) ===")
        package_scheme(s, args.config, args.format)


if __name__ == "__main__":
    main()
