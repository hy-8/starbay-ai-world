"""Read persisted character defaults, build distance LODs, and assert critical references."""
import unreal,json,traceback
from pathlib import Path
P=Path(unreal.Paths.project_dir());D='/Game/Starbay/Ember_v04';E=unreal.EditorAssetLibrary
R={'status':'started'}
try:
    bp=E.load_asset(D+'/BP_EmberHero');cdo=unreal.get_default_object(bp.generated_class());mesh_comp=cdo.get_component_by_class(unreal.SkeletalMeshComponent)
    mesh=mesh_comp.get_editor_property('skeletal_mesh_asset');animclass=mesh_comp.get_editor_property('anim_class')
    R['mesh']=mesh.get_path_name();R['anim_class']=animclass.get_path_name();R['walk_speed']=cdo.get_component_by_class(unreal.CharacterMovementComponent).get_editor_property('max_walk_speed')
    assert R['mesh'].startswith(D) and R['anim_class'].startswith(D),'Character defaults did not persist'
    subs=unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
    if subs.get_lod_count(mesh)<3:assert subs.regenerate_lod(mesh,3,False,False),'LOD generation failed'
    E.save_loaded_asset(mesh)
    R['lods']=[{'index':i,'vertices':subs.get_num_verts(mesh,i),'sections':subs.get_num_sections(mesh,i)} for i in range(subs.get_lod_count(mesh))]
    R['animations']={key:unreal.load_asset(D+'/A_Ember_'+key).get_play_length() for key in ['Idle','Walk','Run','Jump','Fall','Land','Spell']}
    R['material_slots']=[str(s.material_slot_name) for s in mesh.get_editor_property('materials')]
    assert all(s.material_interface for s in mesh.get_editor_property('materials')),'Missing persisted material'
    assert cdo.get_editor_property('Combo Attack Montage').get_path_name().startswith(D)
    R['status']='asset_checks_passed; runtime and visual checks remain separate'
except Exception:R['status']='failed';R['error']=traceback.format_exc();raise
finally:(P/'Saved/ember_asset_validation.json').write_text(json.dumps(R,indent=2),encoding='utf-8')
