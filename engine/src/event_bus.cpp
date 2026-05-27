#include "engine/event_bus.h"

#include <algorithm>

namespace engine {

void EventBus::Unsubscribe(const Subscription& sub) {
  if (!sub.IsValid()) return;
  std::lock_guard<std::mutex> lock(mutex_);
  auto it = handlers_.find(sub.event_type);
  if (it == handlers_.end()) return;
  auto& vec = it->second;
  vec.erase(std::remove_if(vec.begin(), vec.end(),
                           [&](const std::shared_ptr<HandlerBase>& h) {
                             return h->id == sub.id;
                           }),
            vec.end());
}

void EventBus::Clear() {
  std::lock_guard<std::mutex> lock(mutex_);
  handlers_.clear();
}

}  // namespace engine
