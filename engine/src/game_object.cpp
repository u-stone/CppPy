#include "engine/game_object.h"

#include <iostream>

namespace engine {

std::atomic<GameObjectId> GameObject::next_id_{1};

void TransformComponent::OnUpdate(float dt) {
  std::cout << "  [TransformComponent] OnUpdate dt=" << dt << std::endl;
}

void AIComponent::OnUpdate(float dt) {
  std::cout << "  [AIComponent] OnUpdate dt=" << dt << std::endl;
}

GameObject::GameObject(std::string name)
    : id_(next_id_.fetch_add(1, std::memory_order_relaxed)),
      name_(std::move(name)) {}

GameObject::~GameObject() {
  components_.clear();
  components_by_type_.clear();
}

void GameObject::RemoveComponent(std::type_index type) {
  std::lock_guard<std::mutex> lock(component_mutex_);
  components_by_type_.erase(type);
  components_.erase(
      std::remove_if(components_.begin(), components_.end(),
                     [&](const std::unique_ptr<Component>& c) {
                       return std::type_index(typeid(*c)) == type;
                     }),
      components_.end());
}

void GameObject::Update(float dt) {
  std::lock_guard<std::mutex> lock(component_mutex_);
  std::cout << "  [GameObject] Update '" << name_ << "' (id=" << id_ << ") dt="
            << dt << std::endl;
  for (auto& comp : components_) {
    if (comp->IsEnabled()) {
      comp->OnUpdate(dt);
    }
  }
}

size_t GameObject::ComponentCount() const {
  std::lock_guard<std::mutex> lock(component_mutex_);
  return components_.size();
}

}  // namespace engine
