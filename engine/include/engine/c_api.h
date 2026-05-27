#ifndef ENGINE_C_API_H_
#define ENGINE_C_API_H_

// Pure-C ABI for the engine. All types are opaque handles (void*).
// Designed for cffi/ctypes consumption. No STL types in signatures.

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

typedef void* EngineHandle;
typedef void* SceneHandle;
typedef void* GameObjectHandle;
typedef void* ComponentHandle;

typedef void (*EventCallback)(const char* event_type, const char* json_data,
                              void* user_data);

// --- Engine lifecycle ---
EngineHandle engine_create(void);
void engine_destroy(EngineHandle engine);
int engine_init(EngineHandle engine, const char* config_json);
void engine_shutdown(EngineHandle engine);
int engine_is_initialized(EngineHandle engine);

// --- Update loop ---
void engine_update(EngineHandle engine, float dt);

// --- Scene management ---
SceneHandle scene_create(EngineHandle engine, const char* name);
void scene_destroy(EngineHandle engine, SceneHandle scene);
SceneHandle scene_get_by_name(EngineHandle engine, const char* name);
int scene_object_count(SceneHandle scene);

// --- GameObject management ---
GameObjectHandle go_create(SceneHandle scene, const char* name);
void go_destroy(SceneHandle scene, GameObjectHandle go);
const char* go_name(GameObjectHandle go);
int64_t go_id(GameObjectHandle go);

// --- Component management ---
ComponentHandle go_add_component(GameObjectHandle go, const char* type_name);
void go_remove_component(GameObjectHandle go, ComponentHandle comp);
ComponentHandle go_get_component(GameObjectHandle go, const char* type_name);
const char* component_type_name(ComponentHandle comp);

// --- Batch operations ---
void engine_mass_spawn(EngineHandle engine, const char* scene_name, int count,
                       const char* prefix);

// --- Event system ---
int engine_subscribe(EngineHandle engine, const char* event_type,
                     EventCallback callback, void* user_data);
void engine_unsubscribe(EngineHandle engine, int subscription_id);
void engine_publish_event(EngineHandle engine, const char* event_type,
                          const char* json_data);

#ifdef __cplusplus
}
#endif

#endif  // ENGINE_C_API_H_
