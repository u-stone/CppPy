#ifndef ENGINE_EVENT_BUS_H_
#define ENGINE_EVENT_BUS_H_

#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <typeindex>
#include <unordered_map>
#include <vector>

namespace engine {

using SubscriptionId = int64_t;

// Type-erased subscriber handle. Copyable, moveable.
struct Subscription {
  SubscriptionId id = -1;
  std::type_index event_type = std::type_index(typeid(void));

  bool IsValid() const { return id >= 0; }
};

class EventBus {
public:
  EventBus() = default;
  ~EventBus() = default;

  EventBus(const EventBus &) = delete;
  EventBus &operator=(const EventBus &) = delete;

  // Subscribe to events of type T. Returns a subscription handle.
  // T must be copyable.
  template <typename T>
  Subscription Subscribe(std::function<void(const T &)> handler) {
    static_assert(std::is_copy_constructible_v<T>,
                  "Event type must be copyable");
    std::lock_guard<std::mutex> lock(mutex_);
    SubscriptionId id = next_id_++;
    auto &entry = handlers_[std::type_index(typeid(T))];
    entry.push_back(std::make_shared<TypedHandler<T>>(id, std::move(handler)));
    return Subscription{id, std::type_index(typeid(T))};
  }

  // Convenience overload for lambdas / function objects.
  template <typename T, typename Callable>
  Subscription Subscribe(Callable &&callable) {
    return Subscribe<T>(
        std::function<void(const T &)>(std::forward<Callable>(callable)));
  }

  // Publish an event. All matching subscribers are invoked synchronously.
  template <typename T> void Publish(const T &event) {
    std::vector<std::shared_ptr<HandlerBase>> snapshot;
    {
      std::lock_guard<std::mutex> lock(mutex_);
      auto it = handlers_.find(std::type_index(typeid(T)));
      if (it != handlers_.end()) {
        snapshot = it->second;
      }
    }
    for (auto &h : snapshot) {
      auto *typed = static_cast<TypedHandler<T> *>(h.get());
      typed->callback(event);
    }
  }

  // Unsubscribe a previously registered handler.
  void Unsubscribe(const Subscription &sub);

  // Remove all subscribers.
  void Clear();

private:
  struct HandlerBase {
    SubscriptionId id;
    explicit HandlerBase(SubscriptionId i) : id(i) {}
    virtual ~HandlerBase() = default;
  };

  template <typename T> struct TypedHandler : HandlerBase {
    std::function<void(const T &)> callback;
    TypedHandler(SubscriptionId i, std::function<void(const T &)> cb)
        : HandlerBase(i), callback(std::move(cb)) {}
  };

  std::mutex mutex_;
  SubscriptionId next_id_ = 0;
  std::unordered_map<std::type_index, std::vector<std::shared_ptr<HandlerBase>>>
      handlers_;
};

} // namespace engine

#endif // ENGINE_EVENT_BUS_H_
