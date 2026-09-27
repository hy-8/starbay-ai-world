"""Assign native material interfaces explicitly after skeletal LOD generation."""
import unreal,json
from pathlib import Path
D='/Game/Starbay/Ember_v04';E=unreal.EditorAssetLibrary;mesh=E.load_asset(D+'/SK_EmberRegent');slots=list(mesh.get_editor_property('materials'))
for i,slot in enumerate(slots):
    path=D+'/M_Ember_%02d'%i
    material=E.load_asset(path) if E.does_asset_exist(path) else E.duplicate_asset('/Game/Starbay/Ember_v02/M_Ember_%02d'%i,path)
    assert material;E.save_loaded_asset(material)
    slot.set_editor_property('material_interface',material);slots[i]=slot
mesh.set_editor_property('materials',slots);E.save_loaded_asset(mesh)
for name in ['BP_EmberCharacter','BP_EmberCombat']:
    bp=E.load_asset(D+'/'+name);c=unreal.get_default_object(bp.generated_class()).get_component_by_class(unreal.SkeletalMeshComponent)
    for i in range(len(slots)):c.set_material(i,E.load_asset(D+'/M_Ember_%02d'%i))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp);E.save_loaded_asset(bp)
r={'mesh_materials':[str(s.get_editor_property('material_interface')) for s in mesh.get_editor_property('materials')]}
(Path(unreal.Paths.project_dir())/'Saved/ember_material_assignment.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
