"""Inspect the real gameplay camera rather than the evidence camera."""
import unreal,time,builtins,json,traceback
from pathlib import Path
P=Path(unreal.Paths.project_dir());L=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);U=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
assert not L.is_in_play_in_editor()
start=time.monotonic();state={}
def tick(dt):
    if time.monotonic()-start<6:return
    if state.get('captured'):
        if time.monotonic()-state['captured']>2:
            unreal.unregister_slate_post_tick_callback(builtins._ember_camera);L.editor_request_end_play()
        return
    try:
        w=U.get_game_world();c=unreal.GameplayStatics.get_player_character(w,0)
        if not c:return
        pcm=unreal.GameplayStatics.get_player_camera_manager(w,0)
        r={'pawn':str(c.get_actor_location()),'view':str(pcm.get_camera_location()),'rotation':str(pcm.get_camera_rotation()),'components':[]}
        for cl in [unreal.CameraComponent,unreal.SpringArmComponent,unreal.SkeletalMeshComponent]:
            for comp in c.get_components_by_class(cl):
                item={'name':comp.get_name(),'active':comp.is_active(),'world':str(comp.get_world_location()),'relative':str(comp.get_editor_property('relative_location')),'parent':str(comp.get_attach_parent())}
                if isinstance(comp,unreal.SpringArmComponent):item.update(length=comp.get_editor_property('target_arm_length'),offset=str(comp.get_editor_property('socket_offset')))
                r['components'].append(item)
        (P/'Saved/ember_camera.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
        unreal.AutomationLibrary.take_high_res_screenshot(1280,720,str(P/'Preview/UE5_Ember_PlayerCamera.png'))
        state['captured']=time.monotonic()
    except Exception:
        (P/'Saved/ember_camera.json').write_text(json.dumps({'error':traceback.format_exc()}),encoding='utf-8');unreal.unregister_slate_post_tick_callback(builtins._ember_camera);L.editor_request_end_play()
builtins._ember_camera=unreal.register_slate_post_tick_callback(tick);L.editor_request_begin_play()
