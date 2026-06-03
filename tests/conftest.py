# tests/conftest.py — shared fixtures for CppPy import smoke tests.
import os, sys

# Ensure dist/ packages are importable (for bare pytest runs without editable install).
_dist = os.path.join(os.path.dirname(__file__), "..", "dist")
for _cfg in ("Debug", "Release", ""):
    _p = os.path.join(_dist, _cfg) if _cfg else _dist
    if os.path.isdir(_p) and any(
        d.startswith("engine") and os.path.isdir(os.path.join(_p, d)) for d in os.listdir(_p)
    ):
        sys.path.insert(0, _p)
        break
