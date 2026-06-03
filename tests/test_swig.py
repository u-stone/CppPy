"""Smoke tests for engineswig (SWIG binding)."""


def test_import():
    import engineswig

    assert hasattr(engineswig, "engine_create_and_init")


def test_engine_create():
    import engineswig

    engine = engineswig.engine_create_and_init(b'{"app":"test"}')
    assert engine is not None
    assert engineswig.engine_is_initialized(engine) == 1
    engineswig.engine_shutdown(engine)
    engineswig.engine_destroy(engine)


def test_scene_and_object():
    import engineswig

    engine = engineswig.engine_create_and_init(b'{"app":"test"}')
    scene = engineswig.scene_create(engine, b"Main")
    assert scene is not None
    go = engineswig.go_create(scene, b"Hero")
    assert go is not None
    engineswig.engine_shutdown(engine)
    engineswig.engine_destroy(engine)
