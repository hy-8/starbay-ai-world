"""Combine the template's jumping controller with native combat inheritance."""
import unreal,json,traceback
from pathlib import Path
P=Path(unreal.Paths.project_dir());D='/Game/Starbay/Ember_v04';E=unreal.EditorAssetLibrary;R={}
try:
    dest=D+'/BP_EmberHero'
    bp=E.load_asset(dest) if E.does_asset_exist(dest) else E.duplicate_asset(D+'/BP_EmberCharacter',dest)
    for old,new in [('Move','EmberMove'),('Aim','EmberAim')]:
        graph=unreal.BlueprintEditorLibrary.find_graph(bp,old)
        if graph:unreal.BlueprintEditorLibrary.rename_graph(graph,new)
    unreal.BlueprintEditorLibrary.reparent_blueprint(bp,E.load_blueprint_class(D+'/BP_EmberCombat'))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp);R['generated_class']=bp.generated_class().get_path_name()
    c=unreal.get_default_object(bp.generated_class());m=c.get_component_by_class(unreal.SkeletalMeshComponent)
    m.set_skeletal_mesh_asset(E.load_asset(D+'/SK_EmberRegent'));m.set_anim_instance_class(E.load_blueprint_class(D+'/ABP_Ember'))
    for i in range(16):m.set_material(i,E.load_asset(D+'/M_Ember_%02d'%i))
    c.get_component_by_class(unreal.CharacterMovementComponent).set_editor_property('max_walk_speed',600.0)
    E.save_loaded_asset(bp)
    imc=E.load_asset('/Game/Variant_Combat/Input/IMC_Combat')
    if not any(str(x.key.get_editor_property('key_name'))=='SpaceBar' for x in imc.get_editor_property('mappings')):
        key=unreal.Key();key.set_editor_property('key_name','SpaceBar');imc.map_key(E.load_asset('/Game/Input/Actions/IA_Jump'),key);E.save_loaded_asset(imc)
    gm=E.load_asset(D+'/BP_EmberGameMode');unreal.get_default_object(gm.generated_class()).set_editor_property('default_pawn_class',bp.generated_class());unreal.BlueprintEditorLibrary.compile_blueprint(gm);E.save_loaded_asset(gm)
    R['status']='composed; native key verification pending'
except Exception:R['status']='failed';R['error']=traceback.format_exc();raise
finally:(P/'Saved/ember_playable.json').write_text(json.dumps(R,indent=2),encoding='utf-8')
