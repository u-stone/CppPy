#!/usr/bin/env python3
# examples/cython/demo.py — Cython binding demo.
# VS Code users: .vscode/settings.json already configures PYTHONPATH.

import os, sys

try:
    import enginecython
except ImportError:
    _d = os.path.join(os.path.dirname(__file__), "..", "..", "dist")
    for _cfg in ("Debug", "Release", ""):
        _p = os.path.join(_d, _cfg) if _cfg else _d
        if os.path.isdir(_p) and any(
            e.startswith("engine_") and os.path.isdir(os.path.join(_p, e))
            for e in os.listdir(_p)
        ):
            sys.path.insert(0, _p)
            break
    import enginecython


def main():
    print("=" * 50)
    print("  CppPy — Cython Demo")
    print("=" * 50)

    # Use the Cython-wrapped Pythonic API
    engine = enginecython.Engine()
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
