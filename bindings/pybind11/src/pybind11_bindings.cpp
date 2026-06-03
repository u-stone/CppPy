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

  // Disable auto-generated C++ signatures in docstrings so
  // pybind11-stubgen uses our clean Python-type signatures instead.
  py::options options;
  options.disable_function_signatures();

  py::class_<EngineFacade>(m, "Engine")
      .def(py::init<>())
      .def("init", &EngineFacade::Init, py::arg("config_json") = "{}",
           py::doc("init(config_json: str = '{}') -> bool"))
      .def("shutdown", &EngineFacade::Shutdown,
           py::doc("shutdown() -> None"))
      .def("update", &EngineFacade::Update, py::arg("dt"),
           py::doc("update(dt: float) -> None"))
      .def("create_scene", &EngineFacade::CreateScene, py::arg("name"),
           py::doc("create_scene(name: str) -> Scene"))
      .def("get_scene", &EngineFacade::GetScene, py::arg("name"),
           py::doc("get_scene(name: str) -> Scene | None"))
      .def("scene_names", &EngineFacade::SceneNames,
           py::doc("scene_names() -> list[str]"))
      .def_property_readonly("is_initialized", &EngineFacade::IsInitialized)
      .def("find_scene", &cpp_api::FindScene, py::arg("name"),
           py::doc("find_scene(name: str) -> Scene | None"))
      .def("create_scene_with_object", &cpp_api::CreateSceneWithDefaultObject,
           py::arg("scene_name"), py::arg("object_name"),
           py::doc("create_scene_with_object(scene_name: str, object_name: str) -> tuple[Scene, GameObject]"))
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
           py::arg("event_type"), py::arg("callback"),
           py::doc("subscribe_event(event_type: str, callback: Callable) -> int"))
      .def("publish_event",
           [](EngineFacade& self, const std::string& event_type,
              const std::string& data) {
             if (event_type == "damage") {
               self.GetEventBus().Publish(data);
             }
           },
           py::arg("event_type"), py::arg("data"),
           py::doc("publish_event(event_type: str, data: str) -> None"));

  py::class_<Scene, std::shared_ptr<Scene>>(m, "Scene")
      .def("name", &Scene::Name, py::doc("name() -> str"))
      .def("create_object", &Scene::CreateObject, py::arg("name"),
           py::doc("create_object(name: str) -> GameObject"))
      .def("remove_object", &Scene::RemoveObject, py::arg("id"),
           py::doc("remove_object(id: int) -> None"))
      .def("find_object", &Scene::FindObject, py::arg("id"),
           py::doc("find_object(id: int) -> GameObject | None"))
      .def("object_count", &Scene::ObjectCount,
           py::doc("object_count() -> int"))
      .def_property_readonly("all_objects", &Scene::AllObjects)
      .def("find_objects_by_name", &cpp_api::FindObjectsByName,
           py::arg("name"),
           py::doc("find_objects_by_name(name: str) -> list[GameObject]"))
      .def("batch_create_objects", &cpp_api::BatchCreateObjects,
           py::arg("count"), py::arg("prefix"),
           py::doc("batch_create_objects(count: int, prefix: str) -> list[GameObject]"));

  py::class_<GameObject, std::shared_ptr<GameObject>>(m, "GameObject")
      .def("id", &GameObject::Id, py::doc("id() -> int"))
      .def("name", &GameObject::Name, py::doc("name() -> str"))
      .def("add_transform",
           [](GameObject& self) -> TransformComponent* {
             return &self.AddComponent<TransformComponent>();
           }, py::return_value_policy::reference_internal,
           py::doc("add_transform() -> Transform"))
      .def("add_ai",
           [](GameObject& self) -> AIComponent* {
             return &self.AddComponent<AIComponent>();
           }, py::return_value_policy::reference_internal,
           py::doc("add_ai() -> AIComponent"))
      .def("get_transform",
           [](GameObject& self) -> TransformComponent* {
             return self.GetComponent<TransformComponent>();
           }, py::return_value_policy::reference_internal,
           py::doc("get_transform() -> Transform | None"))
      .def("get_ai",
           [](GameObject& self) -> AIComponent* {
             return self.GetComponent<AIComponent>();
           }, py::return_value_policy::reference_internal,
           py::doc("get_ai() -> AIComponent | None"));

  py::class_<Component>(m, "Component")
      .def(py::init<std::string>(), py::arg("type_name"),
           py::doc("Component(type_name: str)"))
      .def("type_name", &Component::TypeName, py::doc("type_name() -> str"))
      .def("on_update", &Component::OnUpdate, py::arg("dt"),
           py::doc("on_update(dt: float) -> None"))
      .def("on_enable", &Component::OnEnable, py::doc("on_enable() -> None"))
      .def("on_disable", &Component::OnDisable, py::doc("on_disable() -> None"))
      .def_property("enabled", &Component::IsEnabled, &Component::SetEnabled);

  py::class_<TransformComponent, Component>(m, "Transform")
      .def(py::init<>(), py::doc("Transform()"))
      .def_property("x",
           [](TransformComponent& t) -> float { return t.data.x; },
           [](TransformComponent& t, float v) { t.data.x = v; })
      .def_property("y",
           [](TransformComponent& t) -> float { return t.data.y; },
           [](TransformComponent& t, float v) { t.data.y = v; })
      .def_property("z",
           [](TransformComponent& t) -> float { return t.data.z; },
           [](TransformComponent& t, float v) { t.data.z = v; });

  py::class_<AIComponent, Component>(m, "AIComponent")
      .def(py::init<>(), py::doc("AIComponent()"));

  py::class_<Transform>(m, "TransformData")
      .def(py::init<>(), py::doc("TransformData()"))
      .def_readwrite("x", &Transform::x)
      .def_readwrite("y", &Transform::y)
      .def_readwrite("z", &Transform::z);
}
