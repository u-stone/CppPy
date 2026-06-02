#!/usr/bin/env python3
# examples/swig/demo.py
# Demonstrates the SWIG binding — uses auto-generated C API wrappers.
# SWIG 4.x maps char* ↔ Python bytes, so strings are encoded/decoded.

import os
import sys

_dist_root = os.path.join(
    os.path.dirname(__file__), "..", "..", "dist"
)
for _cfg in ("Debug", "Release", ""):
    _path = os.path.join(_dist_root, _cfg) if _cfg else _dist_root
    if os.path.isdir(_path) and any(
        d.startswith("engine_") and os.path.isdir(os.path.join(_path, d))
        for d in os.listdir(_path)
    ):
        sys.path.insert(0, _path)
        break

import engine_swig


def _enc(s):
    """Encode a Python str to UTF-8 bytes for SWIG const char* params."""
    return s.encode("utf-8")


def _dec(b):
    """Decode UTF-8 bytes returned by SWIG const char* outputs."""
    return b.decode("utf-8") if b else None


def main():
    print("=" * 50)
    print("  CppPy — SWIG Demo")
    print("=" * 50)

    # engine_create_and_init is a %inline helper from the .i file
    engine = engine_swig.engine_create_and_init(_enc('{"app": "swig_demo"}'))
    print(f"[demo] Engine created: {engine}")

    initialized = engine_swig.engine_is_initialized(engine)
    print(f"[demo] Engine initialized: {bool(initialized)}")

    # Create scene
    scene = engine_swig.scene_create(engine, _enc("MainScene"))
    print(f"[demo] Scene created: {scene}")

    # Create game objects
    player = engine_swig.go_create(scene, _enc("Player"))
    enemy = engine_swig.go_create(scene, _enc("Enemy"))
    pname = _dec(engine_swig.go_name(player))
    pid = engine_swig.go_id(player)
    ename = _dec(engine_swig.go_name(enemy))
    print(f"[demo] Objects: {pname} (id={pid}), {ename}")

    # Add components
    t_comp = engine_swig.go_add_component(player, _enc("Transform"))
    ai_comp = engine_swig.go_add_component(enemy, _enc("AI"))
    t_name = _dec(engine_swig.component_type_name(t_comp))
    ai_name = _dec(engine_swig.component_type_name(ai_comp))
    print(f"[demo] Components: {t_name} on Player, {ai_name} on Enemy")

    # Mass spawn (batch operation)
    engine_swig.engine_mass_spawn(engine, _enc("MainScene"), 10, _enc("SwarmUnit"))
    count = engine_swig.scene_object_count(scene)
    print(f"[demo] After mass spawn, scene has {count} objects")

    # Update loop
    print()
    for i in range(3):
        engine_swig.engine_update(engine, 0.016)
        print(f"[demo] --- tick {i} ---")
    print()

    # Shutdown
    engine_swig.engine_shutdown(engine)
    engine_swig.engine_destroy(engine)
    print("[demo] Engine shutdown complete")
    print("\n[DONE] SWIG demo passed")


if __name__ == "__main__":
    main()
