# bindings/cffi/python/cffi_bridge.py
# Pythonic OOP wrapper around the raw CFFI/ctypes handles.
# Provides the same API surface as the other binding schemes.

import os
import ctypes
import platform

# --- Load the shared library ---
_lib_dir = os.path.dirname(__file__)
if platform.system() == "Windows":
    _lib = ctypes.CDLL(os.path.join(_lib_dir, "engine_c.dll"))
else:
    _lib = ctypes.CDLL(os.path.join(_lib_dir, "libengine_c.so"))

# --- ctypes function signatures ---

_lib.engine_create.argtypes = []
_lib.engine_create.restype = ctypes.c_void_p

_lib.engine_destroy.argtypes = [ctypes.c_void_p]
_lib.engine_destroy.restype = None

_lib.engine_init.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
_lib.engine_init.restype = ctypes.c_int

_lib.engine_shutdown.argtypes = [ctypes.c_void_p]
_lib.engine_shutdown.restype = None

_lib.engine_is_initialized.argtypes = [ctypes.c_void_p]
_lib.engine_is_initialized.restype = ctypes.c_int

_lib.engine_update.argtypes = [ctypes.c_void_p, ctypes.c_float]
_lib.engine_update.restype = None

_lib.scene_create.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
_lib.scene_create.restype = ctypes.c_void_p

_lib.scene_destroy.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
_lib.scene_destroy.restype = None

_lib.scene_get_by_name.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
_lib.scene_get_by_name.restype = ctypes.c_void_p

_lib.scene_object_count.argtypes = [ctypes.c_void_p]
_lib.scene_object_count.restype = ctypes.c_int

_lib.go_create.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
_lib.go_create.restype = ctypes.c_void_p

_lib.go_destroy.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
_lib.go_destroy.restype = None

_lib.go_name.argtypes = [ctypes.c_void_p]
_lib.go_name.restype = ctypes.c_char_p

_lib.go_id.argtypes = [ctypes.c_void_p]
_lib.go_id.restype = ctypes.c_int64

_lib.go_add_component.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
_lib.go_add_component.restype = ctypes.c_void_p

_lib.go_remove_component.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
_lib.go_remove_component.restype = None

_lib.go_get_component.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
_lib.go_get_component.restype = ctypes.c_void_p

_lib.component_type_name.argtypes = [ctypes.c_void_p]
_lib.component_type_name.restype = ctypes.c_char_p

_lib.engine_mass_spawn.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p]
_lib.engine_mass_spawn.restype = None

EventCallback = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p)
_lib.engine_subscribe.argtypes = [ctypes.c_void_p, ctypes.c_char_p, EventCallback, ctypes.c_void_p]
_lib.engine_subscribe.restype = ctypes.c_int

_lib.engine_unsubscribe.argtypes = [ctypes.c_void_p, ctypes.c_int]
_lib.engine_unsubscribe.restype = None

_lib.engine_publish_event.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
_lib.engine_publish_event.restype = None


# --- Pythonic wrappers ---


class Component:
    """Wrapper around a C ComponentHandle."""

    def __init__(self, handle):
        self._handle = handle

    @property
    def type_name(self):
        result = _lib.component_type_name(self._handle)
        return result.decode("utf-8") if result else ""


class GameObject:
    """Wrapper around a C GameObjectHandle."""

    def __init__(self, handle, engine_handle):
        self._handle = handle
        self._engine_handle = engine_handle

    @property
    def name(self):
        result = _lib.go_name(self._handle)
        return result.decode("utf-8") if result else ""

    @property
    def id(self):
        return _lib.go_id(self._handle)

    def add_component(self, type_name):
        h = _lib.go_add_component(self._handle, type_name.encode("utf-8"))
        return Component(h) if h else None

    def get_component(self, type_name):
        h = _lib.go_get_component(self._handle, type_name.encode("utf-8"))
        return Component(h) if h else None


class Scene:
    """Wrapper around a C SceneHandle."""

    def __init__(self, handle, engine_handle):
        self._handle = handle
        self._engine_handle = engine_handle

    def create_object(self, name):
        h = _lib.go_create(self._handle, name.encode("utf-8"))
        return GameObject(h, self._engine_handle) if h else None

    @property
    def object_count(self):
        return _lib.scene_object_count(self._handle)


class Engine:
    """Wrapper around C EngineHandle — ctypes-based."""

    def __init__(self, config_json="{}"):
        self._handle = _lib.engine_create()
        self._callbacks = {}
        self._callback_refs = {}  # Prevent GC of ctypes callbacks

    def init(self, config_json="{}"):
        return bool(_lib.engine_init(self._handle, config_json.encode("utf-8")))

    def shutdown(self):
        _lib.engine_shutdown(self._handle)

    @property
    def is_initialized(self):
        return bool(_lib.engine_is_initialized(self._handle))

    def update(self, dt):
        _lib.engine_update(self._handle, dt)

    def create_scene(self, name):
        h = _lib.scene_create(self._handle, name.encode("utf-8"))
        return Scene(h, self._handle) if h else None

    def get_scene(self, name):
        h = _lib.scene_get_by_name(self._handle, name.encode("utf-8"))
        return Scene(h, self._handle) if h else None

    def subscribe(self, event_type, callback):
        def _bridge(evt_type, json_data, user_data):
            et = evt_type.decode("utf-8") if evt_type else ""
            jd = json_data.decode("utf-8") if json_data else ""
            callback(jd)

        cb = EventCallback(_bridge)
        self._callback_refs[id(callback)] = cb
        return _lib.engine_subscribe(self._handle, event_type.encode("utf-8"), cb, None)

    def publish_event(self, event_type, data):
        _lib.engine_publish_event(self._handle, event_type.encode("utf-8"), data.encode("utf-8"))

    def mass_spawn(self, scene_name, count, prefix="obj"):
        _lib.engine_mass_spawn(
            self._handle, scene_name.encode("utf-8"), count, prefix.encode("utf-8")
        )

    def __del__(self):
        if self._handle:
            _lib.engine_destroy(self._handle)
