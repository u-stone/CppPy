#include "engine/c_api.h"

#include <cstring>
#include <iostream>
#include <mutex>
#include <string>
#include <unordered_map>

#include "engine/facade.h"
#include "engine/game_object.h"
#include "engine/scene.h"

namespace {

struct CEngineState {
  engine::EngineFacade facade;
  std::unordered_map<int, EventCallback> callbacks;
  std::unordered_map<int, void*> callback_user_data;
  std::mutex callback_mutex;
  int next_sub_id = 1;
};

CEngineState* ToState(EngineHandle h) {
  return static_cast<CEngineState*>(h);
}

engine::Scene* ToScene(SceneHandle h) {
  return static_cast<engine::Scene*>(h);
}

engine::GameObject* ToGO(GameObjectHandle h) {
  return static_cast<engine::GameObject*>(h);
}

engine::Component* ToComp(ComponentHandle h) {
  return static_cast<engine::Component*>(h);
}

}  // namespace

extern "C" {

EngineHandle engine_create(void) {
  auto* state = new CEngineState();
  std::cout << "[C API] engine_create" << std::endl;
  return static_cast<EngineHandle>(state);
}

void engine_destroy(EngineHandle engine) {
  std::cout << "[C API] engine_destroy" << std::endl;
  delete ToState(engine);
}

int engine_init(EngineHandle engine, const char* config_json) {
  return ToState(engine)->facade.Init(config_json ? config_json : "{}") ? 1 : 0;
}

void engine_shutdown(EngineHandle engine) {
  ToState(engine)->facade.Shutdown();
}

int engine_is_initialized(EngineHandle engine) {
  return ToState(engine)->facade.IsInitialized() ? 1 : 0;
}

void engine_update(EngineHandle engine, float dt) {
  ToState(engine)->facade.Update(dt);
}

// --- Scene ---

SceneHandle scene_create(EngineHandle engine, const char* name) {
  auto scene = ToState(engine)->facade.CreateScene(name ? name : "Untitled");
  return static_cast<SceneHandle>(scene.get());
}

void scene_destroy(EngineHandle engine, SceneHandle scene) {
  // Scene is owned by EngineFacade via shared_ptr; no explicit deletion needed.
  // The C API hands out raw pointers; the engine's shutdown clears scenes.
  (void)engine;
  (void)scene;
}

SceneHandle scene_get_by_name(EngineHandle engine, const char* name) {
  auto scene = ToState(engine)->facade.GetScene(name ? name : "");
  return static_cast<SceneHandle>(scene.get());
}

int scene_object_count(SceneHandle scene) {
  return static_cast<int>(ToScene(scene)->ObjectCount());
}

// --- GameObject ---

GameObjectHandle go_create(SceneHandle scene, const char* name) {
  auto obj = ToScene(scene)->CreateObject(name ? name : "Unnamed");
  return static_cast<GameObjectHandle>(obj.get());
}

void go_destroy(SceneHandle scene, GameObjectHandle go) {
  ToScene(scene)->RemoveObject(ToGO(go)->Id());
}

const char* go_name(GameObjectHandle go) {
  // Returns pointer to internal string; valid as long as the GameObject lives.
  return ToGO(go)->Name().c_str();
}

int64_t go_id(GameObjectHandle go) { return ToGO(go)->Id(); }

// --- Component ---

ComponentHandle go_add_component(GameObjectHandle go, const char* type_name) {
  if (!type_name) return nullptr;
  auto* obj = ToGO(go);
  if (std::strcmp(type_name, "Transform") == 0) {
    return static_cast<ComponentHandle>(&obj->AddComponent<engine::TransformComponent>());
  } else if (std::strcmp(type_name, "AI") == 0) {
    return static_cast<ComponentHandle>(&obj->AddComponent<engine::AIComponent>());
  }
  return nullptr;
}

void go_remove_component(GameObjectHandle go, ComponentHandle comp) {
  if (!comp) return;
  auto* obj = ToGO(go);
  obj->RemoveComponent(std::type_index(typeid(*ToComp(comp))));
}

ComponentHandle go_get_component(GameObjectHandle go, const char* type_name) {
  if (!type_name) return nullptr;
  auto* obj = ToGO(go);
  if (std::strcmp(type_name, "Transform") == 0) {
    return static_cast<ComponentHandle>(
        obj->GetComponent<engine::TransformComponent>());
  } else if (std::strcmp(type_name, "AI") == 0) {
    return static_cast<ComponentHandle>(
        obj->GetComponent<engine::AIComponent>());
  }
  return nullptr;
}

const char* component_type_name(ComponentHandle comp) {
  return ToComp(comp)->TypeName().c_str();
}

// --- Batch ---

void engine_mass_spawn(EngineHandle engine, const char* scene_name, int count,
                       const char* prefix) {
  auto& f = ToState(engine)->facade;
  auto scene = f.GetScene(scene_name ? scene_name : "");
  if (!scene) {
    scene = f.CreateScene(scene_name ? scene_name : "BatchScene");
  }
  for (int i = 0; i < count; ++i) {
    std::string name = std::string(prefix ? prefix : "obj") + "_" +
                       std::to_string(i);
    auto obj = scene->CreateObject(name);
    obj->AddComponent<engine::TransformComponent>();
  }
}

// --- Events ---

int engine_subscribe(EngineHandle engine, const char* event_type,
                     EventCallback callback, void* user_data) {
  if (!event_type || !callback) return -1;
  auto& state = *ToState(engine);
  std::lock_guard<std::mutex> lock(state.callback_mutex);
  int id = state.next_sub_id++;
  state.callbacks[id] = callback;
  state.callback_user_data[id] = user_data;

  // Wire to the C++ event bus via a simple string-based event.
  if (std::strcmp(event_type, "damage") == 0) {
    state.facade.GetEventBus().Subscribe<std::string>(
        [&state, id](const std::string& data) {
          std::lock_guard<std::mutex> lock(state.callback_mutex);
          auto it = state.callbacks.find(id);
          if (it != state.callbacks.end()) {
            auto ud_it = state.callback_user_data.find(id);
            void* ud =
                (ud_it != state.callback_user_data.end()) ? ud_it->second
                                                          : nullptr;
            it->second("damage", data.c_str(), ud);
          }
        });
  }
  return id;
}

void engine_unsubscribe(EngineHandle engine, int subscription_id) {
  auto& state = *ToState(engine);
  std::lock_guard<std::mutex> lock(state.callback_mutex);
  state.callbacks.erase(subscription_id);
  state.callback_user_data.erase(subscription_id);
}

void engine_publish_event(EngineHandle engine, const char* event_type,
                          const char* json_data) {
  if (!event_type || !json_data) return;
  auto& bus = ToState(engine)->facade.GetEventBus();
  if (std::strcmp(event_type, "damage") == 0) {
    bus.Publish(std::string(json_data));
  }
}

}  // extern "C"
