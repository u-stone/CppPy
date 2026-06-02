#include <pybind11/functional.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "engine/cpp_api.h"
#include "engine/facade.h"
#include "engine/game_object.h"
#include "engine/scene.h"

namespace py = pybind11;
using namespace engine;

PYBIND11_MODULE(_core, m) {
  m.doc() = "CppPy engine - pybind11 binding";

  py::class_<EngineFacade>(m, "Engine")
      .def(py::init<>())
      .def("init", &EngineFacade::Init, py::arg("config_json") = "{}")
      .def("shutdown", &EngineFacade::Shutdown)
      .def("update", &EngineFacade::Update, py::arg("dt"))
      .def("create_scene", &EngineFacade::CreateScene, py::arg("name"))
      .def("get_scene", &EngineFacade::GetScene, py::arg("name"))
      .def("scene_names", &EngineFacade::SceneNames)
      .def_property_readonly("is_initialized", &EngineFacade::IsInitialized)
      .def("find_scene", &cpp_api::FindScene, py::arg("name"))
      .def("create_scene_with_object", &cpp_api::CreateSceneWithDefaultObject,
           py::arg("scene_name"), py::arg("object_name"))
      .def("subscribe_event",
           [](EngineFacade& self, const std::string& event_type,
              py::function callback) -> int64_t {
             if (event_type == "damage") {
               auto sub = self.GetEventBus().Subscribe<std::string>(
                   [callback](const std::string& data) {
                     py::gil_scoped_acquire gil;
                     callback(data);
                   });
               return sub.id;
             }
             return -1;
           },
           py::arg("event_type"), py::arg("callback"))
      .def("publish_event",
           [](EngineFacade& self, const std::string& event_type,
              const std::string& data) {
             if (event_type == "damage") {
               self.GetEventBus().Publish(data);
             }
           },
           py::arg("event_type"), py::arg("data"));

  py::class_<Scene, std::shared_ptr<Scene>>(m, "Scene")
      .def("name", &Scene::Name)
      .def("create_object", &Scene::CreateObject, py::arg("name"))
      .def("remove_object", &Scene::RemoveObject, py::arg("id"))
      .def("find_object", &Scene::FindObject, py::arg("id"))
      .def("object_count", &Scene::ObjectCount)
      .def_property_readonly("all_objects", &Scene::AllObjects)
      .def("find_objects_by_name", &cpp_api::FindObjectsByName,
           py::arg("name"))
      .def("batch_create_objects", &cpp_api::BatchCreateObjects,
           py::arg("count"), py::arg("prefix"));

  py::class_<GameObject, std::shared_ptr<GameObject>>(m, "GameObject")
      .def("id", &GameObject::Id)
      .def("name", &GameObject::Name)
      .def("add_transform",
           [](GameObject& self) -> TransformComponent* {
             return &self.AddComponent<TransformComponent>();
           }, py::return_value_policy::reference_internal)
      .def("add_ai",
           [](GameObject& self) -> AIComponent* {
             return &self.AddComponent<AIComponent>();
           }, py::return_value_policy::reference_internal)
      .def("get_transform",
           [](GameObject& self) -> TransformComponent* {
             return self.GetComponent<TransformComponent>();
           }, py::return_value_policy::reference_internal)
      .def("get_ai",
           [](GameObject& self) -> AIComponent* {
             return self.GetComponent<AIComponent>();
           }, py::return_value_policy::reference_internal);

  py::class_<Component>(m, "Component")
      .def(py::init<std::string>(), py::arg("type_name"))
      .def("type_name", &Component::TypeName)
      .def("on_update", &Component::OnUpdate, py::arg("dt"))
      .def("on_enable", &Component::OnEnable)
      .def("on_disable", &Component::OnDisable)
      .def_property("enabled", &Component::IsEnabled, &Component::SetEnabled);

  py::class_<TransformComponent, Component>(m, "Transform")
      .def(py::init<>())
      .def_property("x",
           [](TransformComponent& t) -> float { return t.data.x; },
           [](TransformComponent& t, float v) { t.data.x = v; })
      .def_property("y",
           [](TransformComponent& t) -> float { return t.data.y; },
           [](TransformComponent& t, float v) { t.data.y = v; })
      .def_property("z",
           [](TransformComponent& t) -> float { return t.data.z; },
           [](TransformComponent& t, float v) { t.data.z = v; });

  py::class_<AIComponent, Component>(m, "AIComponent").def(py::init<>());

  py::class_<Transform>(m, "TransformData")
      .def(py::init<>())
      .def_readwrite("x", &Transform::x)
      .def_readwrite("y", &Transform::y)
      .def_readwrite("z", &Transform::z);
}
