#include <nanobind/nanobind.h>
#include <nanobind/stl/function.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>

#include "engine/cpp_api.h"
#include "engine/facade.h"
#include "engine/game_object.h"
#include "engine/scene.h"

namespace nb = nanobind;
using namespace engine;

NB_MODULE(engine_nanobind, m) {
  m.doc() = "CppPy engine - nanobind binding";

  nb::class_<EngineFacade>(m, "Engine")
      .def(nb::init<>())
      .def("init", &EngineFacade::Init, nb::arg("config_json") = "{}")
      .def("shutdown", &EngineFacade::Shutdown)
      .def("update", &EngineFacade::Update, nb::arg("dt"))
      .def("create_scene", &EngineFacade::CreateScene, nb::arg("name"))
      .def("get_scene", &EngineFacade::GetScene, nb::arg("name"))
      .def("scene_names", &EngineFacade::SceneNames)
      .def_prop_ro("is_initialized", &EngineFacade::IsInitialized)
      .def("find_scene", &cpp_api::FindScene, nb::arg("name"))
      .def("create_scene_with_object", &cpp_api::CreateSceneWithDefaultObject,
           nb::arg("scene_name"), nb::arg("object_name"))
      .def("subscribe_event",
           [](EngineFacade& self, const std::string& event_type,
              nb::callable callback) -> int64_t {
             if (event_type == "damage") {
               auto sub = self.GetEventBus().Subscribe<std::string>(
                   [callback = std::move(callback)](const std::string& data) {
                     callback(data);
                   });
               return sub.id;
             }
             return -1;
           },
           nb::arg("event_type"), nb::arg("callback"))
      .def("publish_event",
           [](EngineFacade& self, const std::string& event_type,
              const std::string& data) {
             if (event_type == "damage") {
               self.GetEventBus().Publish(data);
             }
           },
           nb::arg("event_type"), nb::arg("data"));

  nb::class_<Scene>(m, "Scene")
      .def("name", &Scene::Name)
      .def("create_object", &Scene::CreateObject, nb::arg("name"))
      .def("remove_object", &Scene::RemoveObject, nb::arg("id"))
      .def("find_object", &Scene::FindObject, nb::arg("id"))
      .def("object_count", &Scene::ObjectCount)
      .def_prop_ro("all_objects", &Scene::AllObjects)
      .def("find_objects_by_name", &cpp_api::FindObjectsByName,
           nb::arg("name"))
      .def("batch_create_objects", &cpp_api::BatchCreateObjects,
           nb::arg("count"), nb::arg("prefix"));

  nb::class_<GameObject>(m, "GameObject")
      .def("id", &GameObject::Id)
      .def("name", &GameObject::Name)
      .def("add_transform",
           [](GameObject& self) -> TransformComponent* {
             return &self.AddComponent<TransformComponent>();
           }, nb::rv_policy::reference_internal)
      .def("add_ai",
           [](GameObject& self) -> AIComponent* {
             return &self.AddComponent<AIComponent>();
           }, nb::rv_policy::reference_internal)
      .def("get_transform",
           [](GameObject& self) -> TransformComponent* {
             return self.GetComponent<TransformComponent>();
           }, nb::rv_policy::reference_internal)
      .def("get_ai",
           [](GameObject& self) -> AIComponent* {
             return self.GetComponent<AIComponent>();
           }, nb::rv_policy::reference_internal);

  nb::class_<Component>(m, "Component")
      .def(nb::init<std::string>(), nb::arg("type_name"))
      .def("type_name", &Component::TypeName)
      .def("on_update", &Component::OnUpdate, nb::arg("dt"))
      .def("on_enable", &Component::OnEnable)
      .def("on_disable", &Component::OnDisable)
      .def_prop_rw("enabled", &Component::IsEnabled, &Component::SetEnabled);

  nb::class_<TransformComponent, Component>(m, "Transform")
      .def(nb::init<>())
      .def_prop_rw("x",
           [](TransformComponent& t) -> float& { return t.data.x; },
           [](TransformComponent& t, float v) { t.data.x = v; })
      .def_prop_rw("y",
           [](TransformComponent& t) -> float& { return t.data.y; },
           [](TransformComponent& t, float v) { t.data.y = v; })
      .def_prop_rw("z",
           [](TransformComponent& t) -> float& { return t.data.z; },
           [](TransformComponent& t, float v) { t.data.z = v; });

  nb::class_<AIComponent, Component>(m, "AIComponent").def(nb::init<>());

  nb::class_<Transform>(m, "TransformData")
      .def(nb::init<>())
      .def_rw("x", &Transform::x)
      .def_rw("y", &Transform::y)
      .def_rw("z", &Transform::z);
}
