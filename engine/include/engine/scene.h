#ifndef ENGINE_SCENE_H_
#define ENGINE_SCENE_H_

#include <memory>
#include <mutex>
#include <string>
#include <vector>

#include "engine/game_object.h"

namespace engine {

class Scene {
public:
  explicit Scene(std::string name);
  ~Scene() = default;

  Scene(const Scene &) = delete;
  Scene &operator=(const Scene &) = delete;

  const std::string &Name() const { return name_; }

  std::shared_ptr<GameObject> CreateObject(const std::string &name);
  void RemoveObject(GameObjectId id);
  std::shared_ptr<GameObject> FindObject(GameObjectId id) const;

  void Update(float dt);

  size_t ObjectCount() const;

  std::vector<std::shared_ptr<GameObject>> AllObjects() const;

private:
  std::string name_;
  mutable std::mutex mutex_;
  std::vector<std::shared_ptr<GameObject>> objects_;
};

} // namespace engine

#endif // ENGINE_SCENE_H_
