#!/usr/bin/env python3
# examples/cython/demo.py
# Demonstrates the Cython binding — uses compiled .pyx module wrapping C API.

import os
import sys

_bindings_dir = os.path.join(
    os.path.dirname(__file__), "..", "..", "build", "bindings_output", "cython"
)
sys.path.insert(0, _bindings_dir)

# When built via setup_cython.py, the module is importable directly.
# When built via CMake, we need to find the .pyd/.so
try:
    import engine_cython
except ImportError:
    # CMake build may produce a differently named artifact
    import glob

    _pattern = os.path.join(_bindings_dir, "engine_cython*")
    _matches = glob.glob(_pattern)
    if _matches:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "engine_cython", _matches[0]
        )
        engine_cython = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(engine_cython)
    else:
        raise


def main():
    print("=" * 50)
    print("  CppPy — Cython Demo")
    print("=" * 50)

    # Use the Cython-wrapped Pythonic API
    engine = engine_cython.Engine()
    print("[demo] Engine created")

    ok = engine.init('{"app": "cython_demo"}')
    print(f"[demo] Engine initialized: {engine.is_initialized}")

    scene = engine.create_scene("MainScene")
    print(f"[demo] Scene created with {scene.object_count()} objects")

    player = scene.create_object("Player")
    enemy = scene.create_object("Enemy")
    print(f"[demo] Objects: {player.name} (id={player.id}), "
          f"{enemy.name} (id={enemy.id})")

    # Add components
    t = player.add_component("Transform")
    ai = enemy.add_component("AI")
    print(f"[demo] Components: {t.type_name} on Player, {ai.type_name} on Enemy")

    # Event subscription (not yet implemented in Cython wrapper)
    # def on_damage(evt_type, data):
    #     print(f"[demo] Event: {evt_type} => {data}")
    # sub_id = engine.subscribe("damage", on_damage)
    # print(f"[demo] Subscribed to 'damage' (id={sub_id})")
    # engine.publish_event("damage", '{"amount": 100}')

    # Update loop
    print()
    for i in range(3):
        engine.update(0.016)
        print(f"[demo] --- tick {i} ---")
    print()

    # Mass spawn
    engine.mass_spawn("MainScene", 5, "CythonObj")
    print(f"[demo] After mass spawn, scene has {scene.object_count()} objects")

    engine.shutdown()
    print("[demo] Engine shutdown complete")
    print("\n[DONE] Cython demo passed")


if __name__ == "__main__":
    main()
