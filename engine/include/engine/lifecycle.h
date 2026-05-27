#ifndef ENGINE_LIFECYCLE_H_
#define ENGINE_LIFECYCLE_H_

#include <atomic>
#include <functional>
#include <memory>
#include <mutex>

namespace engine {

// RAII sentinel that detects use-after-free scenarios.
// Wrap a shared_ptr or unique_ptr; when the owned object is destroyed,
// all existing Guards become "expired" and callers can check before use.
class LifecycleGuard {
 public:
  LifecycleGuard() : alive_(std::make_shared<std::atomic<bool>>(true)) {}

  LifecycleGuard(const LifecycleGuard&) = default;
  LifecycleGuard& operator=(const LifecycleGuard&) = default;
  LifecycleGuard(LifecycleGuard&&) = default;
  LifecycleGuard& operator=(LifecycleGuard&&) = default;

  void Invalidate() { *alive_ = false; }

  bool IsAlive() const { return alive_->load(std::memory_order_acquire); }

  explicit operator bool() const { return IsAlive(); }

 private:
  std::shared_ptr<std::atomic<bool>> alive_;
};

// Intrusive reference-counting base for objects exposed through the C API.
// The C API hands out opaque handles (void*) which are pointers to RefCounted
// subclasses. engine_release() calls DecRef() and deletes when count hits zero.
class RefCounted {
 public:
  RefCounted() = default;
  virtual ~RefCounted() = default;

  RefCounted(const RefCounted&) = delete;
  RefCounted& operator=(const RefCounted&) = delete;

  void AddRef() { ref_count_.fetch_add(1, std::memory_order_relaxed); }

  // Returns true if the object should be deleted after this call.
  bool DecRef() {
    if (ref_count_.fetch_sub(1, std::memory_order_acq_rel) == 1) {
      return true;
    }
    return false;
  }

  int RefCount() const { return ref_count_.load(std::memory_order_acquire); }

  LifecycleGuard& Guard() { return guard_; }

 private:
  std::atomic<int> ref_count_{1};
  LifecycleGuard guard_;
};

// Smart handle that holds a RefCounted pointer and manages AddRef/DecRef.
template <typename T>
class RefCountedPtr {
 public:
  RefCountedPtr() : ptr_(nullptr) {}
  explicit RefCountedPtr(T* ptr) : ptr_(ptr) {
    if (ptr_) ptr_->AddRef();
  }
  RefCountedPtr(const RefCountedPtr& other) : ptr_(other.ptr_) {
    if (ptr_) ptr_->AddRef();
  }
  RefCountedPtr(RefCountedPtr&& other) noexcept : ptr_(other.ptr_) {
    other.ptr_ = nullptr;
  }
  ~RefCountedPtr() {
    if (ptr_ && ptr_->DecRef()) {
      delete ptr_;
    }
  }

  RefCountedPtr& operator=(const RefCountedPtr& other) {
    if (this != &other) {
      Reset(other.ptr_);
    }
    return *this;
  }
  RefCountedPtr& operator=(RefCountedPtr&& other) noexcept {
    if (this != &other) {
      Reset(nullptr);
      ptr_ = other.ptr_;
      other.ptr_ = nullptr;
    }
    return *this;
  }

  T* Get() const { return ptr_; }
  T* operator->() const { return ptr_; }
  T& operator*() const { return *ptr_; }
  explicit operator bool() const { return ptr_ != nullptr; }

  void Reset(T* new_ptr = nullptr) {
    T* old = ptr_;
    ptr_ = new_ptr;
    if (new_ptr) new_ptr->AddRef();
    if (old && old->DecRef()) {
      delete old;
    }
  }

 private:
  T* ptr_;
};

}  // namespace engine

#endif  // ENGINE_LIFECYCLE_H_
