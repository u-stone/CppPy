#!/usr/bin/env python3
# scripts/manage.py
# Single entry point: manage.py {setup|build|run|lint|tidy} [--scheme SCHEME]

import argparse
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
import venv
import zipfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR = os.path.join(PROJECT_ROOT, "build")
VENV_DIR = os.path.join(BUILD_DIR, "venv")
BINDINGS_OUTPUT = os.path.join(BUILD_DIR, "bindings_output")

ALL_SCHEMES = ["pybind11", "nanobind", "swig", "cython", "cffi"]

EXAMPLES = {
    "pybind11": os.path.join(PROJECT_ROOT, "examples", "pybind11", "demo.py"),
    "nanobind": os.path.join(PROJECT_ROOT, "examples", "nanobind", "demo.py"),
    "swig": os.path.join(PROJECT_ROOT, "examples", "swig", "demo.py"),
    "cython": os.path.join(PROJECT_ROOT, "examples", "cython", "demo.py"),
    "cffi": os.path.join(PROJECT_ROOT, "examples", "cffi", "demo.py"),
}

PYTHON_REQUIREMENTS = [
    "pybind11>=2.12.0",
    "nanobind>=2.0.0",
    "cffi>=1.16.0",
    "cython>=3.0.0",
    "black>=24.0.0",
    "flake8>=7.0.0",
]


def _get_venv_python():
    if platform.system() == "Windows":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    return os.path.join(VENV_DIR, "bin", "python")


def _run(cmd, **kwargs):
    """Run a command, print it, and return CompletedProcess."""
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=False, **kwargs)


def cmd_setup(args):
    """Create virtualenv, run cmake configure, install Python deps."""
    print("[setup] Creating virtualenv...")
    if not os.path.exists(VENV_DIR):
        venv.create(VENV_DIR, with_pip=True)
    print(f"[setup] Virtualenv at {VENV_DIR}")

    python = _get_venv_python()

    # Install Python dependencies
    print("[setup] Installing Python dependencies...")
    _run([python, "-m", "pip", "install", "--upgrade", "pip"])
    for req in PYTHON_REQUIREMENTS:
        _run([python, "-m", "pip", "install", req])

    # Clone/download 3rdparty C++ dependencies (skipped if already present)
    print("[setup] Checking 3rdparty dependencies...")
    _setup_3rdparty(args.scheme)

    # CMake configure
    print("[setup] Running cmake configure...")
    os.makedirs(BUILD_DIR, exist_ok=True)

    cmake_args = [
        "cmake", "-B", BUILD_DIR, "-S", PROJECT_ROOT,
        "-G", "Ninja",
        "-DCMAKE_C_COMPILER=clang",
        "-DCMAKE_CXX_COMPILER=clang++",
        "-DCMAKE_BUILD_TYPE=Release",
        f"-DPython3_EXECUTABLE={python}",
        f"-DPython_EXECUTABLE={python}",
    ]
    # Toggle individual schemes
    scheme_flags = {
        "pybind11": "BUILD_PYBIND11",
        "nanobind": "BUILD_NANOBIND",
        "swig": "BUILD_SWIG",
        "cython": "BUILD_CYTHON",
        "cffi": "BUILD_CFFI",
    }
    for scheme, flag in scheme_flags.items():
        if args.scheme:
            cmake_args.append(f"-D{flag}={'ON' if scheme == args.scheme else 'OFF'}")
        else:
            cmake_args.append(f"-D{flag}=ON")

    result = _run(cmake_args)
    if result.returncode != 0:
        print("[setup] CMake configure FAILED", file=sys.stderr)
        sys.exit(1)
    print("[setup] CMake configure OK")


def cmd_build(args):
    """Build all or a specific scheme."""
    if not os.path.exists(os.path.join(BUILD_DIR, "CMakeCache.txt")):
        print("[build] Build tree not configured. Run 'setup' first.",
              file=sys.stderr)
        sys.exit(1)

    print("[build] Building...")
    build_args = ["cmake", "--build", BUILD_DIR]
    if args.parallel:
        build_args += ["--parallel", str(args.parallel)]

    result = _run(build_args)
    if result.returncode != 0:
        print("[build] Build FAILED", file=sys.stderr)
        sys.exit(1)
    print("[build] Build OK")


def cmd_run(args):
    """Run example scripts for all or a specific scheme."""
    schemes = [args.scheme] if args.scheme else ALL_SCHEMES
    python = _get_venv_python() if os.path.exists(_get_venv_python()) else sys.executable

    results = {}
    for scheme in schemes:
        example = EXAMPLES.get(scheme)
        if not example or not os.path.exists(example):
            results[scheme] = "SKIP (no example)"
            continue

        print(f"\n[run] === {scheme} ===")
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.join(BINDINGS_OUTPUT, scheme)

        result = _run([python, example], env=env)
        if result.returncode == 0:
            results[scheme] = "PASS"
        else:
            results[scheme] = f"FAIL (exit {result.returncode})"

    # Summary
    print("\n" + "=" * 50)
    print("  Results Summary")
    print("=" * 50)
    for scheme, status in results.items():
        print(f"  {scheme:12s} : {status}")
    print("=" * 50)

    if any("FAIL" in s for s in results.values()):
        sys.exit(1)


def cmd_lint(args):
    """Run clang-format and flake8 checks."""
    print("[lint] Running clang-format check...")
    cpp_files = _find_files(PROJECT_ROOT, [".cpp", ".h", ".hpp"],
                            exclude=["build", ".git"])
    if cpp_files:
        result = _run(["clang-format", "--dry-run", "-Werror"] + cpp_files)
        if result.returncode != 0:
            print("[lint] clang-format found style violations", file=sys.stderr)
        else:
            print("[lint] clang-format OK")
    else:
        print("[lint] No C++ files found")

    print("[lint] Running flake8...")
    py_files = _find_files(PROJECT_ROOT, [".py"], exclude=["build", ".git"])
    if py_files:
        result = _run(["flake8", "--max-line-length=100"] + py_files)
        if result.returncode != 0:
            print("[lint] flake8 found issues", file=sys.stderr)
        else:
            print("[lint] flake8 OK")
    else:
        print("[lint] No Python files found")

    print("[lint] Running black check...")
    if py_files:
        result = _run(["black", "--check", "--line-length=100"] + py_files)
        if result.returncode != 0:
            print("[lint] black found formatting issues", file=sys.stderr)
        else:
            print("[lint] black OK")


def cmd_tidy(args):
    """Run clang-tidy on engine and binding sources."""
    print("[tidy] Running clang-tidy...")
    compile_db = os.path.join(BUILD_DIR, "compile_commands.json")
    if not os.path.exists(compile_db):
        print("[tidy] No compile_commands.json — run build first",
              file=sys.stderr)
        sys.exit(1)

    source_dirs = [
        os.path.join(PROJECT_ROOT, "engine", "src"),
        os.path.join(PROJECT_ROOT, "bindings"),
    ]
    cpp_files = []
    for d in source_dirs:
        if os.path.isdir(d):
            cpp_files.extend(_find_files(d, [".cpp"]))

    if not cpp_files:
        print("[tidy] No source files found")
        return

    result = _run(["run-clang-tidy", "-p", BUILD_DIR] + cpp_files)
    if result.returncode != 0:
        print("[tidy] clang-tidy found issues", file=sys.stderr)
    else:
        print("[tidy] clang-tidy OK")


THIRDPARTY_DIR = os.path.join(PROJECT_ROOT, "3rdparty")

THIRDPARTY_DEPS = {
    "pybind11": {
        "url": "https://github.com/pybind/pybind11.git",
        "tag": "v2.12.0",
        "recursive": False,
    },
    "nanobind": {
        "url": "https://github.com/wjakob/nanobind.git",
        "tag": "v2.6.0",
        "recursive": True,
    },
}

# SWIG pre-built binary (swigwin) for Windows.
# On Linux/macOS, SWIG is expected to be installed via the system package manager.
SWIG_WIN_URL = (
    "https://sourceforge.net/projects/swig/files/swigwin/swigwin-4.4.0/"
    "swigwin-4.4.0.zip/download"
)
SWIG_INSTALL_DIR = os.path.join(THIRDPARTY_DIR, "swig-install")


def _setup_swig():
    """Download and extract the swigwin pre-built binary (Windows only).

    On other platforms, SWIG is expected to be available on PATH via the
    system package manager (apt, brew, dnf, pacman, etc.).
    """
    swig_exe = os.path.join(SWIG_INSTALL_DIR, "swig.exe")
    if os.path.isfile(swig_exe):
        print("  [3rdparty] swig: already present, skipping")
        return

    if platform.system() != "Windows":
        print("  [3rdparty] swig: not Windows — install SWIG via your "
              "system package manager (apt install swig / brew install swig)")
        return

    zip_path = os.path.join(THIRDPARTY_DIR, "swigwin.zip")

    # Download
    print(f"  [3rdparty] swig: downloading swigwin-4.4.0.zip (~12 MB) ...")
    try:
        urllib.request.urlretrieve(SWIG_WIN_URL, zip_path)
    except Exception as e:
        print(f"  [3rdparty] swig: download FAILED — {e}", file=sys.stderr)
        print("  [3rdparty] swig: install SWIG manually to "
              f"{SWIG_INSTALL_DIR}", file=sys.stderr)
        return
    print("  [3rdparty] swig: download OK")

    # Extract — the zip contains a top-level swigwin-4.4.0/ directory
    print(f"  [3rdparty] swig: extracting to {SWIG_INSTALL_DIR} ...")
    os.makedirs(SWIG_INSTALL_DIR, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Strip the top-level directory prefix from paths
            for member in zf.infolist():
                # e.g. "swigwin-4.4.0/swig.exe" → "swig.exe"
                rel = member.filename.split("/", 1)
                target_name = rel[1] if len(rel) > 1 else rel[0]
                if not target_name:
                    continue
                target_path = os.path.join(SWIG_INSTALL_DIR, target_name)
                if member.is_dir():
                    os.makedirs(target_path, exist_ok=True)
                else:
                    with zf.open(member) as src, open(target_path, "wb") as dst:
                        shutil.copyfileobj(src, dst)
    except Exception as e:
        print(f"  [3rdparty] swig: extraction FAILED — {e}", file=sys.stderr)
        return

    # Clean up zip and any leftover source directory
    os.remove(zip_path)
    old_src = os.path.join(THIRDPARTY_DIR, "swig-4.4.1")
    if os.path.isdir(old_src):
        shutil.rmtree(old_src, ignore_errors=True)

    if os.path.isfile(swig_exe):
        print("  [3rdparty] swig: setup OK")
    else:
        print("  [3rdparty] swig: extraction completed but swig.exe not "
              "found — check the archive layout", file=sys.stderr)


def _setup_3rdparty(scheme=None):
    """Clone/download third-party libraries into 3rdparty/ (skip if exists).

    Args:
        scheme: If set, only prepare dependencies for the given binding scheme.
                If None, prepare everything.
    """
    os.makedirs(THIRDPARTY_DIR, exist_ok=True)

    # Git-cloned dependencies (pybind11, nanobind)
    need_all = scheme is None
    for name, info in THIRDPARTY_DEPS.items():
        if not need_all and name != scheme:
            continue
        dest = os.path.join(THIRDPARTY_DIR, name)
        if os.path.exists(os.path.join(dest, "CMakeLists.txt")):
            print(f"  [3rdparty] {name}: already present, skipping")
            continue
        print(f"  [3rdparty] {name}: cloning {info['url']} @ {info['tag']} ...")
        clone_args = ["git", "clone", "--depth", "1", "--branch", info["tag"]]
        if info.get("recursive"):
            clone_args.append("--recurse-submodules")
        clone_args += [info["url"], dest]
        result = _run(clone_args)
        if result.returncode != 0:
            print(f"  [3rdparty] {name}: clone FAILED", file=sys.stderr)
        else:
            print(f"  [3rdparty] {name}: clone OK")

    # SWIG pre-built binary (Windows only)
    if need_all or scheme == "swig":
        _setup_swig()


def _find_files(root, extensions, exclude=None):
    """Recursively find files with given extensions."""
    exclude = set(exclude or [])
    result = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude]
        for fn in filenames:
            if any(fn.endswith(ext) for ext in extensions):
                result.append(os.path.join(dirpath, fn))
    return result


def main():
    parser = argparse.ArgumentParser(
        description="CppPy project manager"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_setup = sub.add_parser("setup", help="Configure CMake and install deps")
    p_setup.add_argument("--scheme", choices=ALL_SCHEMES,
                         help="Only setup for a specific scheme")

    p_build = sub.add_parser("build", help="Build the project")
    p_build.add_argument("--scheme", choices=ALL_SCHEMES,
                         help="Only build a specific scheme")
    p_build.add_argument("--parallel", type=int, default=0,
                         help="Number of parallel build jobs")

    p_run = sub.add_parser("run", help="Run example scripts")
    p_run.add_argument("--scheme", choices=ALL_SCHEMES,
                       help="Only run a specific scheme")

    sub.add_parser("lint", help="Run clang-format and flake8 checks")

    sub.add_parser("tidy", help="Run clang-tidy")

    # Also accept command as first positional for convenience
    args = parser.parse_args()

    commands = {
        "setup": cmd_setup,
        "build": cmd_build,
        "run": cmd_run,
        "lint": cmd_lint,
        "tidy": cmd_tidy,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
