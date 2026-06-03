#include "engine/thread_pool.h"

namespace engine {

ThreadPool::ThreadPool(size_t num_threads) {
  if (num_threads == 0) {
    num_threads = std::thread::hardware_concurrency();
    if (num_threads == 0)
      num_threads = 4;
  }
  workers_.reserve(num_threads);
  for (size_t i = 0; i < num_threads; ++i) {
    workers_.emplace_back([this] {
      for (;;) {
        std::function<void()> task;
        {
          std::unique_lock<std::mutex> lock(mutex_);
          condition_.wait(lock, [this] {
            return stop_.load(std::memory_order_acquire) || !tasks_.empty();
          });
          if (stop_.load(std::memory_order_acquire) && tasks_.empty()) {
            return;
          }
          task = std::move(tasks_.front());
          tasks_.pop();
        }
        task();
      }
    });
  }
}

void ThreadPool::Stop() {
  {
    std::lock_guard<std::mutex> lock(mutex_);
    stop_.store(true, std::memory_order_release);
  }
  condition_.notify_all();
  for (auto &worker : workers_) {
    if (worker.joinable()) {
      worker.join();
    }
  }
  workers_.clear();
}

ThreadPool::~ThreadPool() {
  if (!stop_.load(std::memory_order_acquire)) {
    Stop();
  }
}

} // namespace engine
