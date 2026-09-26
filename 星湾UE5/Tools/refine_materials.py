"""UE 5.6 editor-only, reversible leaf/glow correction for saved L_Starbay.

Copies three materials to a fresh Art_v02 namespace and overrides only matching
slots on the two known scene actors. Original materials and meshes are never
edited/saved. Saves a verified map-file backup before the first asset mutation.
No lighting, geometry, collision or gameplay changes. Do not run during PIE.

APIs checked in installed UE 5.6 source: EditorAssetLibrary.h (duplicate/save),
MaterialEditingLibrary.{h,cpp} (graph connections; input lookup needs no open
material editor), Material.h (TwoSided/ShadingModel), EngineTypes.h (foliage),
PrimitiveComponent.h (component SetMaterial), FileHelpers.h (dirty packages),
LevelEditorSubsystem.h (current level/save), PyWrapperObject.cpp (modify).
Run inside the interactive editor. This file does not start or close the editor.
"""
import hashlib
import json
import shutil
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/Starbay/Maps/L_Starbay"
GEOMETRY = "/Game/Starbay/Import_v01/Geometry"
DESTINATION = "/Game/Starbay/Art_v02"
NAMES = ("v6_leaf", "v6_leaflight", "v6_glow")
ACTOR_NAMES = ("SM_District", "SM_CourtyardDetails")
REPORT = PROJECT / "Saved" / "material_refinement_report.json"
assets = unreal.EditorAssetLibrary
graph = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
result = {"schema": 1, "status": "preflight", "started_utc": datetime.now(timezone.utc).isoformat(),
          "map": MAP, "destination": DESTINATION, "created_materials": [], "overrides": [],
          "scope": "material correction only; visual quality and performance require UE inspection",
          "lighting_changed": False, "original_assets_modified": False, "map_save_attempted": False}
components = []
old_overrides = []
map_touched = False


def asset_file(path, extension=".uasset"):
    if not path.startswith("/Game/"):
        raise RuntimeError("Unexpected package outside /Game: " + path)
    return (PROJECT / "Content" / (path[len("/Game/"):] + extension)).resolve()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_clean():
    dirty = list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())
    dirty += list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())
    if dirty:
        raise RuntimeError("Save or resolve existing unsaved packages first: " + ", ".join(x.get_name() for x in dirty))


def check_originals(protected):
    changed = [str(path) for path, before in protected.items() if digest(path) != before]
    if changed:
        result["original_assets_modified"] = True
        result["unexpected_changed_files"] = changed
        raise RuntimeError("An original material/mesh file changed unexpectedly")


def same_map():
    world = editor.get_editor_world()
    return world is not None and world.get_path_name() == MAP + ".L_Starbay"


def connect_property(node, prop):
    if not graph.connect_material_property(node, "", prop):
        raise RuntimeError("Material property connection failed: " + str(prop))


def constant(mat, value, prop, row):
    node = graph.create_material_expression(mat, unreal.MaterialExpressionConstant, -360, row)
    if not node:
        raise RuntimeError("Could not create scalar material expression")
    node.set_editor_property("r", value)
    connect_property(node, prop)


try:
    if (levels.is_in_play_in_editor() or editor.get_game_world() is not None
            or len(unreal.EditorLevelLibrary.get_pie_worlds(True))):
        raise RuntimeError("Existing PIE/SIE detected; no world or asset was modified.")
    if not same_map() or levels.get_current_level().get_path_name() != MAP + ".L_Starbay:PersistentLevel":
        raise RuntimeError("Open L_Starbay with its persistent level current; script never changes maps.")
    check_clean()
    destination_dir = PROJECT / "Content" / DESTINATION[len("/Game/"):]
    if destination_dir.exists() or assets.does_directory_exist(DESTINATION):
        raise RuntimeError("Art_v02 already exists; refusing overwrite or retry into partial results.")
    foliage_model = unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE
    materials = {}
    protected_files = {}
    for name in NAMES:
        source = GEOMETRY + "/" + name
        target = DESTINATION + "/M_" + name
        if assets.does_asset_exist(target):
            raise RuntimeError("Target exists: " + target)
        material = assets.load_asset(source)
        if not isinstance(material, unreal.Material):
            raise RuntimeError("Required original material missing or wrong type: " + source)
        if name != "v6_glow" and graph.get_material_property_input_node(material, unreal.MaterialProperty.MP_BASE_COLOR) is None:
            raise RuntimeError("Leaf BaseColor has no connected node; refusing to invent its original color.")
        materials[name] = material
        source_file = asset_file(source)
        if not source_file.is_file():
            raise RuntimeError("Original material is not saved: " + source)
        protected_files[source_file] = digest(source_file)
    scene_actors = actor_system.get_all_level_actors()
    planned = []
    matches = {name: 0 for name in NAMES}
    for label in ACTOR_NAMES:
        found = [actor for actor in scene_actors if actor.get_actor_label() == label]
        if len(found) != 1 or not isinstance(found[0], unreal.StaticMeshActor):
            raise RuntimeError("Expected exactly one StaticMeshActor named " + label)
        actor = found[0]
        if not actor.get_path_name().startswith(MAP + ".L_Starbay:PersistentLevel."):
            raise RuntimeError("Actor does not belong to the target persistent level: " + label)
        component = actor.static_mesh_component
        mesh = component.get_editor_property("static_mesh")
        if mesh is None or mesh.get_path_name() != GEOMETRY + "/" + label + "." + label:
            raise RuntimeError("Geometry actor references an unexpected mesh: " + label)
        mesh_file = asset_file(GEOMETRY + "/" + label)
        protected_files[mesh_file] = digest(mesh_file)
        components.append((actor, component))
        old_overrides.append(list(component.get_editor_property("override_materials")))
        for index, slot in enumerate(mesh.static_materials):
            original = slot.material_interface
            for name, material in materials.items():
                if original == material:
                    if component.get_material(index) != material:
                        raise RuntimeError("Existing actor material override would be replaced: " + label + "/" + str(index))
                    planned.append((actor, component, index, name, str(slot.material_slot_name)))
                    matches[name] += 1
    if any(count != 1 for count in matches.values()):
        raise RuntimeError("Expected one scene slot for each target material: " + str(matches))
    map_file = asset_file(MAP, ".umap")
    if not map_file.is_file():
        raise RuntimeError("Saved map file missing")
    for folder in ("__ExternalActors__", "__ExternalObjects__"):
        external = PROJECT / "Content" / folder / "Starbay" / "Maps" / "L_Starbay"
        if external.exists() and any(external.rglob("*.uasset")):
            raise RuntimeError("External actor/object packages need a broader backup; refusing this umap-only workflow.")
    # Asset loads can trigger compilation; recheck unsaved state before the backup.
    check_clean()
    if not same_map():
        raise RuntimeError("Current map changed during preflight")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ") + "_" + uuid.uuid4().hex[:8]
    backup_dir = PROJECT / "Saved" / "backups" / ("materials_v02_" + stamp)
    backup_dir.mkdir(parents=True, exist_ok=False)
    backups = []
    for extension in (".umap", ".uexp", ".ubulk", ".uptnl"):
        source_file = map_file.with_suffix(extension)
        if source_file.is_file():
            backup = backup_dir / source_file.name
            before = digest(source_file)
            shutil.copy2(source_file, backup)
            if digest(backup) != before or digest(source_file) != before:
                raise RuntimeError("Map backup checksum mismatch")
            backups.append({"source": str(source_file), "backup": str(backup), "sha256": before})
    result["backups"] = backups
    result["original_component_overrides"] = [
        {"actor": actor.get_path_name(), "materials": [x.get_path_name() if x else None for x in previous]}
        for (actor, _component), previous in zip(components, old_overrides)]
    result["status"] = "applying"
    revised = {}
    for name in NAMES:
        target = DESTINATION + "/M_" + name
        material = assets.duplicate_asset(GEOMETRY + "/" + name, target)
        if not isinstance(material, unreal.Material):
            raise RuntimeError("Material duplication failed: " + name)
        result["created_materials"].append(target)
        if name == "v6_glow":
            node = graph.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -360, 420)
            node.set_editor_property("constant", unreal.LinearColor(3.0, 1.89, 0.72, 1.0))
            connect_property(node, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        else:
            material.set_editor_property("two_sided", True)
            material.set_editor_property("shading_model", foliage_model)
            base = graph.get_material_property_input_node(material, unreal.MaterialProperty.MP_BASE_COLOR)
            output = graph.get_material_property_input_node_output_name(material, unreal.MaterialProperty.MP_BASE_COLOR)
            multiply = graph.create_material_expression(material, unreal.MaterialExpressionMultiply, -360, 420)
            multiply.set_editor_property("const_b", 0.5)
            if not graph.connect_material_expressions(base, output, multiply, "A"):
                raise RuntimeError("Could not connect preserved BaseColor to foliage SSS")
            connect_property(multiply, unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
            constant(material, 0.8, unreal.MaterialProperty.MP_ROUGHNESS, 600)
            constant(material, 0.0, unreal.MaterialProperty.MP_METALLIC, 760)
        graph.recompile_material(material)
        if not assets.save_loaded_asset(material, False):
            raise RuntimeError("Could not save new material: " + target)
        revised[name] = material
    if not same_map() or levels.is_in_play_in_editor():
        raise RuntimeError("Editor world changed before component overrides")
    for actor, component, index, name, slot_name in planned:
        actor.modify()
        component.modify()
        map_touched = True
        component.set_material(index, revised[name])
        if component.get_material(index) != revised[name]:
            raise RuntimeError("Component override did not take effect")
        result["overrides"].append({"actor": actor.get_path_name(), "slot_index": index, "slot_name": slot_name,
                                    "before": materials[name].get_path_name(), "after": revised[name].get_path_name()})
    check_originals(protected_files)
    result["map_save_attempted"] = True
    if not levels.save_current_level():
        raise RuntimeError("Could not save material overrides in current map")
    check_originals(protected_files)
    result["map_sha256_after"] = digest(map_file)
    result["protected_original_files"] = [{"file": str(path), "sha256": value} for path, value in protected_files.items()]
    result["status"] = "material_overrides_saved"
    result["visual_validation_passed"] = False
    result["changes"] = {"leaves": "two-sided foliage; preserved BaseColor; Subsurface=BaseColor*0.5; roughness=0.8; metallic=0",
                         "glow": "emissive linear RGB=(3.0,1.89,0.72), matching source color*3"}
except Exception:
    result["status"] = "failed"
    result["error"] = traceback.format_exc()
    # Restore only our in-memory component overrides; do not replace open map files
    # from disk or delete partial new assets. Backup/report support explicit recovery.
    if map_touched and same_map() and not levels.is_in_play_in_editor():
        try:
            for (_actor, component), previous in zip(components, old_overrides):
                component.set_editor_property("override_materials", previous)
            result["rollback"] = "Original overrides restored in memory; map is unsaved. Inspect before saving."
        except Exception:
            result["rollback_error"] = traceback.format_exc()
    result["recovery"] = ("Partial Art_v02 assets are preserved and block reruns. If the map was saved/partly saved, "
                          "close its editor before restoring the verified umap backup; do not overwrite a loaded map file.")
    raise
finally:
    result["finished_utc"] = datetime.now(timezone.utc).isoformat()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    unreal.log("Starbay material refinement: " + result["status"] + "; " + str(REPORT))
