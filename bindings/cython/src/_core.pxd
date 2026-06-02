# bindings/cython/src/cengine.pxd
# Cython declaration file — tells Cython about the C API functions and types.

cdef extern from "engine/c_api.h" nogil:
    ctypedef void* EngineHandle
    ctypedef void* SceneHandle
    ctypedef void* GameObjectHandle
    ctypedef void* ComponentHandle

    EngineHandle engine_create()
    void engine_destroy(EngineHandle engine)
    int engine_init(EngineHandle engine, const char* config_json)
    void engine_shutdown(EngineHandle engine)
    int engine_is_initialized(EngineHandle engine)
    void engine_update(EngineHandle engine, float dt)

    SceneHandle scene_create(EngineHandle engine, const char* name)
    void scene_destroy(EngineHandle engine, SceneHandle scene)
    SceneHandle scene_get_by_name(EngineHandle engine, const char* name)
    int scene_object_count(SceneHandle scene)

    GameObjectHandle go_create(SceneHandle scene, const char* name)
    void go_destroy(SceneHandle scene, GameObjectHandle go)
    const char* go_name(GameObjectHandle go)
    long long go_id(GameObjectHandle go)

    ComponentHandle go_add_component(GameObjectHandle go, const char* type_name)
    void go_remove_component(GameObjectHandle go, ComponentHandle comp)
    ComponentHandle go_get_component(GameObjectHandle go, const char* type_name)
    const char* component_type_name(ComponentHandle comp)

    void engine_mass_spawn(EngineHandle engine, const char* scene_name,
                           int count, const char* prefix)

    int engine_subscribe(EngineHandle engine, const char* event_type,
                         void (*callback)(const char*, const char*, void*) noexcept,
                         void* user_data)
    void engine_unsubscribe(EngineHandle engine, int subscription_id)
    void engine_publish_event(EngineHandle engine, const char* event_type,
                              const char* json_data)
