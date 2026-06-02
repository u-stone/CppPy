# bindings/cython/src/_core.pyx
# Cython wrapper — provides Pythonic classes around the C API opaque handles.

from libc.stdlib cimport free
from libc.string cimport const_char
cimport _core


cdef class Engine:
    cdef _core.EngineHandle _handle

    def __cinit__(self):
        self._handle = _core.engine_create()

    def __dealloc__(self):
        if self._handle != NULL:
            _core.engine_destroy(self._handle)

    def init(self, config_json="{}"):
        cdef bytes cfg = config_json.encode('utf-8')
        return bool(_core.engine_init(self._handle, cfg))

    def shutdown(self):
        _core.engine_shutdown(self._handle)

    @property
    def is_initialized(self):
        return bool(_core.engine_is_initialized(self._handle))

    def update(self, float dt):
        _core.engine_update(self._handle, dt)

    def create_scene(self, name):
        cdef bytes n = name.encode('utf-8')
        cdef _core.SceneHandle sh = _core.scene_create(self._handle, n)
        if sh == NULL:
            return None
        return Scene._create(sh, self)

    def get_scene(self, name):
        cdef bytes n = name.encode('utf-8')
        cdef _core.SceneHandle sh = _core.scene_get_by_name(self._handle, n)
        if sh == NULL:
            return None
        return Scene._create(sh, self)

    def publish_event(self, event_type, data):
        cdef bytes et = event_type.encode('utf-8')
        cdef bytes d = data.encode('utf-8')
        _core.engine_publish_event(self._handle, et, d)

    def mass_spawn(self, scene_name, int count, prefix="obj"):
        cdef bytes sn = scene_name.encode('utf-8')
        cdef bytes p = prefix.encode('utf-8')
        _core.engine_mass_spawn(self._handle, sn, count, p)


cdef class Scene:
    cdef _core.SceneHandle _handle
    cdef Engine _engine

    @staticmethod
    cdef Scene _create(_core.SceneHandle handle, Engine engine):
        cdef Scene s = Scene.__new__(Scene)
        s._handle = handle
        s._engine = engine
        return s

    def create_object(self, name):
        cdef bytes n = name.encode('utf-8')
        cdef _core.GameObjectHandle gh = _core.go_create(self._handle, n)
        if gh == NULL:
            return None
        return GameObject._create(gh, self._engine)

    def object_count(self):
        return _core.scene_object_count(self._handle)


cdef class GameObject:
    cdef _core.GameObjectHandle _handle
    cdef Engine _engine

    @staticmethod
    cdef GameObject _create(_core.GameObjectHandle handle, Engine engine):
        cdef GameObject g = GameObject.__new__(GameObject)
        g._handle = handle
        g._engine = engine
        return g

    @property
    def name(self):
        if self._handle == NULL:
            return ""
        cdef const char* n = _core.go_name(self._handle)
        return n.decode('utf-8') if n else ""

    @property
    def id(self):
        return _core.go_id(self._handle)

    def add_component(self, type_name):
        cdef bytes tn = type_name.encode('utf-8')
        cdef _core.ComponentHandle ch = _core.go_add_component(self._handle, tn)
        if ch == NULL:
            return None
        return Component._create(ch)

    def get_component(self, type_name):
        cdef bytes tn = type_name.encode('utf-8')
        cdef _core.ComponentHandle ch = _core.go_get_component(self._handle, tn)
        if ch == NULL:
            return None
        return Component._create(ch)


cdef class Component:
    cdef _core.ComponentHandle _handle

    @staticmethod
    cdef Component _create(_core.ComponentHandle handle):
        cdef Component c = Component.__new__(Component)
        c._handle = handle
        return c

    @property
    def type_name(self):
        cdef const char* n = _core.component_type_name(self._handle)
        return n.decode('utf-8') if n else ""
