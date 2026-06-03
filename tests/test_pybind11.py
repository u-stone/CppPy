"""Smoke tests for enginepybind (pybind11 binding)."""

import pytest


@pytest.fixture
def engine():
    import enginepybind
    e = enginepybind.Engine()
    e.init("{}")
    yield e
    e.shutdown()


def test_import():
    import enginepybind
    assert hasattr(enginepybind, "Engine")
    assert hasattr(enginepybind, "Scene")
    assert hasattr(enginepybind, "GameObject")


def test_engine_lifecycle():
    import enginepybind
    e = enginepybind.Engine()
    e.init("{}")
    assert e.is_initialized
    e.update(0.016)
    e.shutdown()


def test_scene_create(engine):
    scene = engine.create_scene("TestScene")
    assert scene is not None
    assert scene.name() == "TestScene"


def test_object_creation(engine):
    scene = engine.create_scene("TestScene")
    obj = scene.create_object("Player")
    assert obj is not None
    assert obj.name() == "Player"
    assert isinstance(obj.id(), int)


def test_components(engine):
    scene = engine.create_scene("TestScene")
    obj = scene.create_object("Player")
    t = obj.add_transform()
    assert t is not None
    ai = obj.add_ai()
    assert ai is not None
    assert t.type_name() == "Transform"
    assert ai.type_name() == "AI"


def test_batch_objects(engine):
    scene = engine.create_scene("TestScene")
    objs = scene.batch_create_objects(5, "Batch")
    assert len(objs) == 5
    assert scene.object_count() == 5


def test_event_subscription(engine):
    received = []

    def handler(data):
        received.append(data)

    sub_id = engine.subscribe_event("damage", handler)
    assert sub_id >= 0
    engine.publish_event("damage", '{"amount": 10}')
    assert len(received) == 1
