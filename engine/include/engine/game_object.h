#ifndef ENGINE_GAME_OBJECT_H_
#define ENGINE_GAME_OBJECT_H_

#include <cstdint>
#include <memory>
#include <mutex>
#include <string>
#include <typeindex>
#include <type_traits>
#include <unordered_map>
#include <vector>

namespace engine {

class EventBus;

struct Transform {
  float x = 0.0f;
  float y = 0.0f;
  float z = 0.0f;
};

// Base class for all components. Users derive from this.
class Component {
 public:
  explicit Component(std::string type_name) : type_name_(std::move(type_name)) {}
  virtual ~Component() = default;

  Component(const Component&) = delete;
  Component& operator=(const Component&) = delete;

  const std::string& TypeName() const { return type_name_; }

  virtual void OnEnable() {}
  virtual void OnDisable() {}
  virtual void OnUpdate(float dt) {}

  bool IsEnabled() const { return enabled_; }
  void SetEnabled(bool enabled) { enabled_ = enabled; }

 private:
  std::string type_name_;
  bool enabled_ = true;
};

// Example concrete component for demonstration.
class TransformComponent : public Component {
 public:
  TransformComponent() : Component("Transform") {}
  void OnUpdate(float dt) override;
  Transform data;
};

class AIComponent : public Component {
 public:
  AIComponent() : Component("AI") {}
  void OnUpdate(float dt) override;
};

using GameObjectId = int64_t;

class GameObject {
 public:
  explicit GameObject(std::string name);
  ~GameObject();

  // Non-copyable, non-movable (mutex prevents default move).
  GameObject(const GameObject&) = delete;
  GameObject& operator=(const GameObject&) = delete;
  GameObject(GameObject&&) = delete;
  GameObject& operator=(GameObject&&) = delete;

  GameObjectId Id() const { return id_; }
  const std::string& Name() const { return name_; }

  // Thread-safe component management.
  template <typename T, typename... Args>
  T& AddComponent(Args&&... args) {
    static_assert(std::is_base_of_v<Component, T>,
                  "T must derive from Component");
    std::lock_guard<std::mutex> lock(component_mutex_);
    auto component = std::make_unique<T>(std::forward<Args>(args)...);
    T& ref = *component;
    auto idx = std::type_index(typeid(T));
    components_by_type_[idx] = component.get();
    components_.push_back(std::move(component));
    return ref;
  }

  template <typename T>
  T* GetComponent() {
    static_assert(std::is_base_of_v<Component, T>,
                  "T must derive from Component");
    std::lock_guard<std::mutex> lock(component_mutex_);
    auto it = components_by_type_.find(std::type_index(typeid(T)));
    if (it != components_by_type_.end()) {
      return static_cast<T*>(it->second);
    }
    return nullptr;
  }

  void RemoveComponent(std::type_index type);

  void Update(float dt);
  void SetEventBus(EventBus* bus) { event_bus_ = bus; }

  size_t ComponentCount() const;

 private:
  GameObjectId id_;
  std::string name_;
  EventBus* event_bus_ = nullptr;

  mutable std::mutex component_mutex_;
  std::vector<std::unique_ptr<Component>> components_;
  std::unordered_map<std::type_index, Component*> components_by_type_;

  static std::atomic<GameObjectId> next_id_;
};

}  // namespace engine

#endif  // ENGINE_GAME_OBJECT_H_
