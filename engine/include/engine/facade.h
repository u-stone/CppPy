#ifndef ENGINE_FACADE_H_
#define ENGINE_FACADE_H_

#include <memory>
#include <string>
#include <vector>

#include "engine/event_bus.h"
#include "engine/scene.h"
#include "engine/thread_pool.h"

namespace engine {

class EngineFacade {
 public:
  EngineFacade();
  ~EngineFacade();

  EngineFacade(const EngineFacade&) = delete;
  EngineFacade& operator=(const EngineFacade&) = delete;

  bool Init(const std::string& config_json);
  void Shutdown();

  std::shared_ptr<Scene> CreateScene(const std::string& name);
  std::shared_ptr<Scene> GetScene(const std::string& name) const;
  std::vector<std::string> SceneNames() const;

  void Update(float dt);

  EventBus& GetEventBus() { return event_bus_; }
  ThreadPool& GetThreadPool() { return thread_pool_; }

  bool IsInitialized() const { return initialized_; }

 private:
  bool initialized_ = false;
  bool shutting_down_ = false;

  EventBus event_bus_;
  ThreadPool thread_pool_;

  mutable std::mutex mutex_;
  std::vector<std::shared_ptr<Scene>> scenes_;
};

}  // namespace engine

#endif  // ENGINE_FACADE_H_
