"""Use one active third-person camera after merging two template Blueprints."""
import unreal,json
from pathlib import Path
E=unreal.EditorAssetLibrary;D='/Game/Starbay/Ember_v04';sub=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem);lib=unreal.SubobjectDataBlueprintFunctionLibrary;r=[]
for name in ['BP_EmberCombat','BP_EmberHero']:
    bp=E.load_asset(D+'/'+name)
    for h in sub.k2_gather_subobject_data_for_blueprint(bp):
        data=lib.get_data(h);c=lib.get_object_for_blueprint(data,bp);variable=str(lib.get_variable_name(data))
        if isinstance(c,unreal.CameraComponent):
            active=variable=='FollowCamera';c.set_editor_property('auto_activate',active)
            r.append({'bp':name,'component':c.get_name(),'variable':variable,'auto_activate':active})
        if isinstance(c,unreal.SpringArmComponent) and variable=='CameraBoom':
            c.set_editor_property('target_arm_length',560.0);c.set_editor_property('socket_offset',unreal.Vector(0,45,55));c.set_editor_property('relative_rotation',unreal.Rotator(-10,0,0))
    unreal.get_default_object(bp.generated_class()).set_editor_property('Default Camera Distance',560.0)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp);E.save_loaded_asset(bp,False)
(Path(unreal.Paths.project_dir())/'Saved/ember_camera_repair.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
