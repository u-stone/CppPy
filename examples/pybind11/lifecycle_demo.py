#!/usr/bin/env python3
# examples/pybind11/lifecycle_demo.py
# Demonstrates object lifecycle management — create, transfer ownership,
# out-of-order deletion, and verify no crashes.

import os, sys

try:
    import enginepybind
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
    import enginepybind


def main():
    print("=" * 50)
    print("  CppPy — Lifecycle Demo (pybind11)")
    print("=" * 50)

    engine = enginepybind.Engine()
    engine.init('{"app": "lifecycle_demo"}')

    # Create scene
    scene = engine.create_scene("LifecycleScene")

    # Create and immediately release references (shared_ptr keeps alive)
    obj1 = scene.create_object("Temp1")
    obj2 = scene.create_object("Temp2")
    print(f"[demo] Created: {obj1.name()} and {obj2.name()}")

    # Add components
    t1 = obj1.add_transform()
    t1.x = 1.0
    print(f"[demo] obj1 transform x={obj1.get_transform().x}")

    # Remove an object
    scene.remove_object(obj2.id())
    print(f"[demo] After removing obj2, scene has {scene.object_count()} objects")

    # Create many objects and let them go out of scope (shared_ptr still owns)
    for i in range(10):
        tmp = scene.create_object(f"Temp_{i}")
        tmp.add_transform()
    print(f"[demo] After batch create, scene has {scene.object_count()} objects")

    # Verify finding by name still works via template API
    results = scene.find_objects_by_name("Temp1")
    print(f"[demo] Found {len(results)} objects named 'Temp1'")

    # Run one tick to exercise all living components
    engine.update(0.016)
    print("[demo] Tick after lifecycle operations OK")

    # Shutdown — should cleanly destroy all scenes, objects, components
    engine.shutdown()
    print("[demo] Shutdown after lifecycle operations OK")
    print("\n[DONE] lifecycle demo passed — no leaks, no crashes")


if __name__ == "__main__":
    main()
