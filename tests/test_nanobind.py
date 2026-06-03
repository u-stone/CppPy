"""Smoke tests for enginenanobind (nanobind binding)."""

import pytest


def test_import():
    import enginenanobind
    assert hasattr(enginenanobind, "Engine")
    assert hasattr(enginenanobind, "Scene")


def test_engine_lifecycle():
    import enginenanobind
    e = enginenanobind.Engine()
    e.init("{}")
    assert e.is_initialized
    e.update(0.016)
    e.shutdown()


def test_create_scene():
    import enginenanobind
    e = enginenanobind.Engine()
    e.init("{}")
    scene = e.create_scene("Main")
    assert scene is not None
    e.shutdown()


def test_object_and_components():
    import enginenanobind
    e = enginenanobind.Engine()
    e.init("{}")
    scene = e.create_scene("Main")
    obj = scene.create_object("Hero")
    obj.add_transform()
    obj.add_ai()
    assert scene.object_count() == 1
    e.shutdown()
