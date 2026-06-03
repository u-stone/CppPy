"""Smoke tests for enginecython (Cython binding)."""


def test_import():
    import enginecython

    assert hasattr(enginecython, "Engine")


def test_engine_lifecycle():
    import enginecython

    e = enginecython.Engine()
    e.init("{}")
    assert e.is_initialized
    e.update(0.016)
    e.shutdown()


def test_scene_and_object():
    import enginecython

    e = enginecython.Engine()
    e.init("{}")
    scene = e.create_scene("Main")
    assert scene is not None
    obj = scene.create_object("Hero")
    assert obj is not None
    obj.add_component("Transform")
    c = obj.get_component("Transform")
    assert c is not None
    e.shutdown()


def test_mass_spawn():
    import enginecython

    e = enginecython.Engine()
    e.init("{}")
    scene = e.create_scene("Main")
    e.mass_spawn("Main", 3, "Test")
    assert scene.object_count() == 3
    e.shutdown()
