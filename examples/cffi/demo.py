#!/usr/bin/env python3
# examples/cffi/demo.py
# Demonstrates the CFFI + ctypes binding — pure C ABI with Python wrapper.

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

from engine_cffi import Engine


def main():
    print("=" * 50)
    print("  CppPy — CFFI/ctypes Demo")
    print("=" * 50)

    # Instantiate the ctypes-based wrapper
    engine = Engine()
    print("[demo] Engine created")

    ok = engine.init('{"app": "cffi_demo"}')
    print(f"[demo] Engine initialized: {engine.is_initialized}")

    scene = engine.create_scene("MainScene")
    print(f"[demo] Scene created with {scene.object_count} objects")

    player = scene.create_object("Player")
    enemy = scene.create_object("Enemy")
    print(f"[demo] Objects: {player.name} (id={player.id}), "
          f"{enemy.name} (id={enemy.id})")

    # Add components via ctypes C API
    t = player.add_component("Transform")
    ai = enemy.add_component("AI")
    print(f"[demo] Components: {t.type_name} on Player, {ai.type_name} on Enemy")

    # Event subscription via ctypes callback
    def on_damage(data):
        print(f"[demo] Event received: damage => {data}")

    sub_id = engine.subscribe("damage", on_damage)
    print(f"[demo] Subscribed to 'damage' events (id={sub_id})")

    engine.publish_event("damage", '{"amount": 60}')

    # Update loop
    print()
    for i in range(3):
        engine.update(0.016)
        print(f"[demo] --- tick {i} ---")
    print()

    # Batch operation via C API
    engine.mass_spawn("MainScene", 8, "CffiObj")
    print(f"[demo] After mass spawn, scene has {scene.object_count} objects")

    engine.shutdown()
    print("[demo] Engine shutdown complete")
    print("\n[DONE] CFFI/ctypes demo passed")


if __name__ == "__main__":
    main()
