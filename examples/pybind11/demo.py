#!/usr/bin/env python3
"""examples/pybind11/demo.py — pybind11 binding reference implementation.

VS Code users: the .vscode/settings.json already configures PYTHONPATH so
'import engine_pybind' works directly without any path manipulation.

Terminal users: run via 'manage.py run' or 'PYTHONPATH=dist/Debug python ...'.
"""

import os, sys

try:
    import engine_pybind  # works when PYTHONPATH is set (VS Code / manage.py)
except ImportError:
    # Fallback: auto-detect dist/ directory for bare terminal runs
    _d = os.path.join(os.path.dirname(__file__), "..", "..", "dist")
    for _cfg in ("Debug", "Release", ""):
        _p = os.path.join(_d, _cfg) if _cfg else _d
        if os.path.isdir(_p) and any(
            e.startswith("engine_") and os.path.isdir(os.path.join(_p, e))
            for e in os.listdir(_p)
        ):
            sys.path.insert(0, _p)
            break
    import engine_pybind


def main():
    print("=" * 50)
    print("  CppPy — pybind11 Demo")
    print("=" * 50)

    engine = engine_pybind.Engine()
    print("[demo] Engine created")

    engine.init('{"app": "pybind11_demo"}')
    print(f"[demo] Engine initialized: {engine.is_initialized}")

    scene = engine.create_scene("MainScene")
    print(f"[demo] Scene created: {scene.name()}")

    player = scene.create_object("Player")
    enemy = scene.create_object("Enemy")
    print(f"[demo] Objects: {player.name()} (id={player.id()}), "
          f"{enemy.name()} (id={enemy.id()})")

    player_transform = player.add_transform()
    player_transform.x = 10.0
    player_transform.y = 5.0
    print(f"[demo] Added Transform to Player (x={player_transform.x})")

    enemy_ai = enemy.add_ai()
    print("[demo] Added AI to Enemy")

    t = player.get_transform()
    print(f"[demo] Retrieved Transform from Player: x={t.x}")

    def on_damage(data):
        print(f"[demo] Event received: damage => {data}")

    sub_id = engine.subscribe_event("damage", on_damage)
    print(f"[demo] Subscribed to 'damage' events (id={sub_id})")

    engine.publish_event("damage", '{"amount": 50}')

    # Update loop — 3 ticks
    print()
    for i in range(3):
        engine.update(0.016)
        print(f"[demo] --- tick {i} ---")
    print()

    found = engine.find_scene("MainScene")
    if found:
        print("[demo] find_scene('MainScene') returned a scene")

    objs = scene.batch_create_objects(3, "Spawn")
    print(f"[demo] Batch created {len(objs)} objects")

    results = scene.find_objects_by_name("Player")
    print(f"[demo] find_objects_by_name('Player') => {len(results)} found")

    engine.shutdown()
    print("[demo] Engine shutdown complete")
    print("\n[DONE] pybind11 demo passed")


if __name__ == "__main__":
    main()
