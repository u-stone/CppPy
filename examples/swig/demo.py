#!/usr/bin/env python3
# examples/swig/demo.py — SWIG binding demo.
# VS Code users: .vscode/settings.json already configures PYTHONPATH.

import os, sys

try:
    import engineswig
except ImportError:
    _d = os.path.join(os.path.dirname(__file__), "..", "..", "dist")
    for _cfg in ("Debug", "Release", ""):
        _p = os.path.join(_d, _cfg) if _cfg else _d
        if os.path.isdir(_p) and any(
            e.startswith("engine_") and os.path.isdir(os.path.join(_p, e)) for e in os.listdir(_p)
        ):
            sys.path.insert(0, _p)
            break
    import engineswig


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
    engine = engineswig.engine_create_and_init(_enc('{"app": "swig_demo"}'))
    print(f"[demo] Engine created: {engine}")

    initialized = engineswig.engine_is_initialized(engine)
    print(f"[demo] Engine initialized: {bool(initialized)}")

    # Create scene
    scene = engineswig.scene_create(engine, _enc("MainScene"))
    print(f"[demo] Scene created: {scene}")

    # Create game objects
    player = engineswig.go_create(scene, _enc("Player"))
    enemy = engineswig.go_create(scene, _enc("Enemy"))
    pname = _dec(engineswig.go_name(player))
    pid = engineswig.go_id(player)
    ename = _dec(engineswig.go_name(enemy))
    print(f"[demo] Objects: {pname} (id={pid}), {ename}")

    # Add components
    t_comp = engineswig.go_add_component(player, _enc("Transform"))
    ai_comp = engineswig.go_add_component(enemy, _enc("AI"))
    t_name = _dec(engineswig.component_type_name(t_comp))
    ai_name = _dec(engineswig.component_type_name(ai_comp))
    print(f"[demo] Components: {t_name} on Player, {ai_name} on Enemy")

    # Mass spawn (batch operation)
    engineswig.engine_mass_spawn(engine, _enc("MainScene"), 10, _enc("SwarmUnit"))
    count = engineswig.scene_object_count(scene)
    print(f"[demo] After mass spawn, scene has {count} objects")

    # Update loop
    print()
    for i in range(3):
        engineswig.engine_update(engine, 0.016)
        print(f"[demo] --- tick {i} ---")
    print()

    # Shutdown
    engineswig.engine_shutdown(engine)
    engineswig.engine_destroy(engine)
    print("[demo] Engine shutdown complete")
    print("\n[DONE] SWIG demo passed")


if __name__ == "__main__":
    main()
