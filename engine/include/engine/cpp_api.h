#ifndef ENGINE_CPP_API_H_
#define ENGINE_CPP_API_H_

// C++ template API layer. Uses STL containers, templates, optional, etc.
// This is the API that pybind11/nanobind excel at — automatic conversions.
// cffi/ctypes cannot handle these signatures directly.

#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <tuple>
#include <typeindex>
#include <type_traits>
#include <vector>

#include "engine/facade.h"
#include "engine/game_object.h"
#include "engine/scene.h"

namespace engine::cpp_api {

// --- GameObject template helpers ---

template <typename T, typename... Args>
std::shared_ptr<T> AddComponent(GameObject& go, Args&&... args) {
  static_assert(std::is_base_of_v<Component, T>, "T must derive from Component");
  T& comp = go.AddComponent<T>(std::forward<Args>(args)...);
  // Return a shared_ptr aliasing the component. The GameObject owns it.
  return std::shared_ptr<T>(std::shared_ptr<GameObject>{}, &comp);
}

template <typename T>
T* GetComponent(GameObject& go) {
  return go.template GetComponent<T>();
}

// --- Scene helpers ---

template <typename Predicate>
std::vector<std::shared_ptr<GameObject>> FindObjects(const Scene& scene,
                                                     Predicate&& pred) {
  std::vector<std::shared_ptr<GameObject>> result;
  for (auto& obj : scene.AllObjects()) {
    if (pred(obj)) {
      result.push_back(obj);
    }
  }
  return result;
}

inline std::vector<std::shared_ptr<GameObject>> FindObjectsByName(
    const Scene& scene, std::string_view name) {
  return FindObjects(scene, [&](const std::shared_ptr<GameObject>& obj) {
    return obj->Name() == name;
  });
}

// --- Event system helpers ---

template <typename EventT>
Subscription Subscribe(EventBus& bus,
                       std::function<void(const EventT&)> handler) {
  return bus.Subscribe<EventT>(std::move(handler));
}

template <typename EventT, typename Callable>
Subscription Subscribe(EventBus& bus, Callable&& callable) {
  return bus.Subscribe<EventT>(std::forward<Callable>(callable));
}

template <typename EventT>
void Publish(EventBus& bus, const EventT& event) {
  bus.Publish(event);
}

// --- Factory helpers returning tuples ---

inline std::tuple<std::shared_ptr<Scene>, std::shared_ptr<GameObject>>
CreateSceneWithDefaultObject(EngineFacade& engine, const std::string& scene_name,
                             const std::string& object_name) {
  auto scene = engine.CreateScene(scene_name);
  auto obj = scene->CreateObject(object_name);
  obj->AddComponent<TransformComponent>();
  return {scene, obj};
}

// --- STL-heavy utility: batch create, returns vector ---

inline std::vector<std::shared_ptr<GameObject>> BatchCreateObjects(
    std::shared_ptr<Scene> scene, int count, const std::string& prefix) {
  std::vector<std::shared_ptr<GameObject>> result;
  result.reserve(count);
  for (int i = 0; i < count; ++i) {
    auto obj =
        scene->CreateObject(prefix + "_" + std::to_string(i));
    obj->AddComponent<TransformComponent>();
    result.push_back(obj);
  }
  return result;
}

// --- Optional-return helper ---

inline std::optional<std::shared_ptr<Scene>> FindScene(
    EngineFacade& engine, const std::string& name) {
  auto scene = engine.GetScene(name);
  if (scene) {
    return scene;
  }
  return std::nullopt;
}

}  // namespace engine::cpp_api

#endif  // ENGINE_CPP_API_H_
