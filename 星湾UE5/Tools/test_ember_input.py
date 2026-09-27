"""Exercise real Enhanced Input key mappings in PIE via development key injection.

No CharacterMovement speed overrides or direct animation calls. This verifies
the game's key mappings and Blueprint dispatch, not physical keyboard hardware.
"""
import unreal,json,time,traceback,builtins,math
from pathlib import Path
P=Path(unreal.Paths.project_dir());D='/Game/Starbay/Ember_v04';L=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);U=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if L.is_in_play_in_editor():raise RuntimeError('Existing PIE protected')
performance=unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle=performance.get_editor_property('bThrottleCPUWhenNotForeground')
performance.set_editor_property('bThrottleCPUWhenNotForeground',False)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not any('EmberEvidenceCamera' in a.tags for a in actors.get_all_level_actors()):
    a=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(350,320,180));a.tags=['EmberEvidenceCamera']
R={'status':'running','method':'Enhanced Input development Input.+key / Input.-key, not OS keyboard injection','samples':[]};state={'wall':time.monotonic(),'fired':set()};out=P/'Saved/ember_input_runtime.json'
def write():out.write_text(json.dumps(R,indent=2),encoding='utf-8')
def once(name,fn):
    if name not in state['fired']:state['fired'].add(name);fn()
def tick(dt):
    try:
        if time.monotonic()-state['wall']>100:raise RuntimeError('Input test timeout')
        w=U.get_game_world()
        if not w:return
        c=unreal.GameplayStatics.get_player_character(w,0)
        if not c:return
        pc=unreal.GameplayStatics.get_player_controller(w,0);t=unreal.GameplayStatics.get_time_seconds(w)
        if 'start' not in state:
            state['start']=t;state['origin']=c.get_actor_location();R['pawn']=c.get_class().get_path_name();R['controller']=pc.get_class().get_path_name()
            assert 'EmberHero' in R['pawn'],'New native playable pawn not active'

        age=t-state['start'];cmd=lambda text:unreal.SystemLibrary.execute_console_command(w,text,pc)
        if age>1:once('walk',lambda:cmd('Input.+key W 1'))
        if age>2.6:once('sprint',lambda:cmd('Input.+key LeftShift 1'))
        if age>4:
            once('stop',lambda:cmd('Input.-key W'));once('stopshift',lambda:cmd('Input.-key LeftShift'))
        if age>4.5:once('jump',lambda:cmd('Input.+key SpaceBar 1'))
        if age>5.4:once('releasejump',lambda:cmd('Input.-key SpaceBar'))
        if age>7 and 'cast' not in state['fired']:
            c.set_actor_location(state['origin'],False,False)
            camera=unreal.GameplayStatics.get_all_actors_with_tag(w,'EmberEvidenceCamera')[0];loc=c.get_actor_location()+unreal.Vector(500,350,80)
            camera.set_actor_location(loc,False,False);camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(loc,c.get_actor_location()+unreal.Vector(0,0,10)),False)
            camera.get_component_by_class(unreal.CameraComponent).set_field_of_view(36);pc.set_view_target_with_blend(camera,0)
            once('cast',lambda:cmd('Input.+key Q 1'))
        if age>7.9:once('releasecast',lambda:cmd('Input.-key Q'))
        if age>12.5:once('castagain',lambda:cmd('Input.+key Q 1'))
        if age>12.8:once('releaseagain',lambda:cmd('Input.-key Q'))
        mesh=c.get_component_by_class(unreal.SkeletalMeshComponent);anim=mesh.get_anim_instance();vel=c.get_velocity();pos=c.get_actor_location()
        phase='idle' if age<1 else 'walk' if age<2.6 else 'sprint' if age<4 else 'jump' if age<7 else 'cast' if age<12.5 else 'castagain'
        if not R['samples'] or age-R['samples'][-1]['seconds']>.10:
            R['samples'].append({'seconds':age,'phase':phase,'speed':math.hypot(vel.x,vel.y),'input':str(c.get_last_movement_input_vector()),'z':pos.z,'hand_local':[float(x) for x in (mesh.get_socket_location('hand_r')-pos).to_tuple()],'montage_playing':anim.is_any_montage_playing(),'attacking':c.get_editor_property('Is Attacking')})
        if age>8.7:once('screenshot',lambda:unreal.AutomationLibrary.take_high_res_screenshot(1280,900,str(P/'Preview/UE5_Ember_NativeCast.png')))
        if age>18:
            peak=lambda phase:max([s['speed'] for s in R['samples'] if s['phase']==phase] or [0])
            R['walk_speed']=peak('walk');R['sprint_speed']=peak('sprint');R['jump_rise']=max(s['z'] for s in R['samples'])-state['origin'].z
            R['checks']={'walk_mapping':220<R['walk_speed']<380,'shift_sprint_mapping':R['sprint_speed']>500,'space_jump_mapping':R['jump_rise']>60,'q_cast_mapping':sum(s['montage_playing'] for s in R['samples'] if s['phase']=='cast')>3}
            recovery=[s for s in R['samples'] if 11.5<s['seconds']<12.4]
            R['checks']['cast_recovers']=bool(recovery) and all(not s['montage_playing'] and not s['attacking'] for s in recovery)
            R['checks']['repeat_cast']=sum(s['montage_playing'] for s in R['samples'] if s['phase']=='castagain')>3
            R['status']='passed' if all(R['checks'].values()) else 'failed';write();unreal.unregister_slate_post_tick_callback(builtins._ember_input_test);L.editor_request_end_play();performance.set_editor_property('bThrottleCPUWhenNotForeground',old_throttle)
    except Exception:
        R['status']='failed';R['error']=traceback.format_exc();write();unreal.unregister_slate_post_tick_callback(builtins._ember_input_test)
        if L.is_in_play_in_editor():L.editor_request_end_play()
        performance.set_editor_property('bThrottleCPUWhenNotForeground',old_throttle)
write();builtins._ember_input_test=unreal.register_slate_post_tick_callback(tick);L.editor_request_begin_play()
