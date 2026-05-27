#include "engine/facade.h"

#include <algorithm>
#include <iostream>

namespace engine {

EngineFacade::EngineFacade() : thread_pool_(4) {}

EngineFacade::~EngineFacade() {
  if (initialized_ && !shutting_down_) {
    Shutdown();
  }
}

bool EngineFacade::Init(const std::string& config_json) {
  std::lock_guard<std::mutex> lock(mutex_);
  if (initialized_) {
    std::cerr << "  [EngineFacade] Already initialized." << std::endl;
    return false;
  }
  std::cout << "  [EngineFacade] Init with config: " << config_json
            << std::endl;
  initialized_ = true;
  return true;
}

void EngineFacade::Shutdown() {
  {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!initialized_ || shutting_down_) return;
    shutting_down_ = true;
  }
  std::cout << "  [EngineFacade] Shutdown — stopping threads, clearing scenes..."
            << std::endl;
  thread_pool_.Stop();
  scenes_.clear();
  event_bus_.Clear();
  initialized_ = false;
  std::cout << "  [EngineFacade] Shutdown complete." << std::endl;
}

std::shared_ptr<Scene> EngineFacade::CreateScene(const std::string& name) {
  std::lock_guard<std::mutex> lock(mutex_);
  if (!initialized_) {
    std::cerr << "  [EngineFacade] Cannot create scene: not initialized."
              << std::endl;
    return nullptr;
  }
  auto scene = std::make_shared<Scene>(name);
  scenes_.push_back(scene);
  std::cout << "  [EngineFacade] Created scene '" << name << "'" << std::endl;
  return scene;
}

std::shared_ptr<Scene> EngineFacade::GetScene(const std::string& name) const {
  std::lock_guard<std::mutex> lock(mutex_);
  for (auto& scene : scenes_) {
    if (scene->Name() == name) return scene;
  }
  return nullptr;
}

std::vector<std::string> EngineFacade::SceneNames() const {
  std::lock_guard<std::mutex> lock(mutex_);
  std::vector<std::string> names;
  names.reserve(scenes_.size());
  for (auto& scene : scenes_) {
    names.push_back(scene->Name());
  }
  return names;
}

void EngineFacade::Update(float dt) {
  std::vector<std::shared_ptr<Scene>> snapshot;
  {
    std::lock_guard<std::mutex> lock(mutex_);
    snapshot = scenes_;
  }
  std::cout << "[EngineFacade] Update dt=" << dt << ", scenes="
            << snapshot.size() << std::endl;
  for (auto& scene : snapshot) {
    scene->Update(dt);
  }
}

}  // namespace engine
