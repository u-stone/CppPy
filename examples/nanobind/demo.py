#!/usr/bin/env python3
"""examples/nanobind/demo.py — nanobind binding demo."""

import os
import sys

_bindings_dir = os.path.join(
    os.path.dirname(__file__), "..", "..", "build", "bindings_output", "nanobind"
)
sys.path.insert(0, _bindings_dir)

import engine_nanobind


def main():
    print("=" * 50)
    print("  CppPy — nanobind Demo")
    print("=" * 50)

    engine = engine_nanobind.Engine()
    print("[demo] Engine created")

    engine.init('{"app": "nanobind_demo"}')
    print(f"[demo] Engine initialized: {engine.is_initialized}")

    scene = engine.create_scene("MainScene")
    print(f"[demo] Scene created: {scene.name()}")

    player = scene.create_object("Player")
    enemy = scene.create_object("Enemy")
    print(f"[demo] Objects: {player.name()} (id={player.id()}), "
          f"{enemy.name()} (id={enemy.id()})")

    player.add_transform()
    enemy.add_ai()
    print("[demo] Components added: Transform to Player, AI to Enemy")

    def on_damage(data):
        print(f"[demo] Event received: damage => {data}")

    sub_id = engine.subscribe_event("damage", on_damage)
    print(f"[demo] Subscribed to 'damage' events (id={sub_id})")
    engine.publish_event("damage", '{"amount": 75}')

    print()
    for i in range(3):
        engine.update(0.016)
        print(f"[demo] --- tick {i} ---")
    print()

    objs = scene.batch_create_objects(5, "NanobindObj")
    print(f"[demo] Batch created {len(objs)} objects")

    engine.shutdown()
    print("[demo] Engine shutdown complete")
    print("\n[DONE] nanobind demo passed")


if __name__ == "__main__":
    main()
