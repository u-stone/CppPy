#include "engine/scene.h"

#include <algorithm>
#include <iostream>

namespace engine {

Scene::Scene(std::string name) : name_(std::move(name)) {}

std::shared_ptr<GameObject> Scene::CreateObject(const std::string &name) {
  std::lock_guard<std::mutex> lock(mutex_);
  auto obj = std::make_shared<GameObject>(name);
  objects_.push_back(obj);
  std::cout << "  [Scene] Created object '" << name
            << "' (total: " << objects_.size() << ")" << std::endl;
  return obj;
}

void Scene::RemoveObject(GameObjectId id) {
  std::lock_guard<std::mutex> lock(mutex_);
  objects_.erase(std::remove_if(objects_.begin(), objects_.end(),
                                [id](const std::shared_ptr<GameObject> &obj) {
                                  return obj->Id() == id;
                                }),
                 objects_.end());
  std::cout << "  [Scene] Removed object id=" << id << std::endl;
}

std::shared_ptr<GameObject> Scene::FindObject(GameObjectId id) const {
  std::lock_guard<std::mutex> lock(mutex_);
  for (auto &obj : objects_) {
    if (obj->Id() == id)
      return obj;
  }
  return nullptr;
}

void Scene::Update(float dt) {
  std::vector<std::shared_ptr<GameObject>> snapshot;
  {
    std::lock_guard<std::mutex> lock(mutex_);
    snapshot = objects_;
  }
  std::cout << " [Scene] Update '" << name_ << "' dt=" << dt
            << ", objects=" << snapshot.size() << std::endl;
  for (auto &obj : snapshot) {
    if (obj) {
      obj->Update(dt);
    }
  }
}

size_t Scene::ObjectCount() const {
  std::lock_guard<std::mutex> lock(mutex_);
  return objects_.size();
}

std::vector<std::shared_ptr<GameObject>> Scene::AllObjects() const {
  std::lock_guard<std::mutex> lock(mutex_);
  return objects_;
}

} // namespace engine
