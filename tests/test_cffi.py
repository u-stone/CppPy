"""Smoke tests for enginecffi (CFFI/ctypes binding)."""


def test_import():
    import enginecffi
    assert hasattr(enginecffi, "Engine")


def test_engine_lifecycle():
    import enginecffi
    e = enginecffi.Engine()
    e.init("{}")
    assert e.is_initialized
    e.update(0.016)
    e.shutdown()


def test_scene_and_object():
    import enginecffi
    e = enginecffi.Engine("{}")
    e.init()
    scene = e.create_scene("Main")
    assert scene is not None
    obj = scene.create_object("Hero")
    assert obj is not None
    assert obj.name == "Hero"
    e.shutdown()


def test_components():
    import enginecffi
    e = enginecffi.Engine("{}")
    e.init()
    scene = e.create_scene("Main")
    obj = scene.create_object("Hero")
    t = obj.add_component("Transform")
    assert t is not None
    assert t.type_name == "Transform"
    e.shutdown()
