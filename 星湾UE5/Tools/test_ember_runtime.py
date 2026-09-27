"""Bounded real PIE locomotion/animation/spell test; leaves results and screenshots.

Uses native CharacterMovement and Montage APIs; physical keyboard tests are separate.
"""
import unreal,time,json,traceback,builtins,math
from pathlib import Path
P=Path(unreal.Paths.project_dir());D='/Game/Starbay/Ember_v04';R={'status':'running','samples':[]};OUT=P/'Saved/ember_runtime.json'
L=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);U=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if L.is_in_play_in_editor():raise RuntimeError('Existing PIE protected')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
evidence=next((a for a in actors.get_all_level_actors() if 'EmberEvidenceCamera' in a.tags),None)
if not evidence:
    evidence=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(350,320,180));evidence.tags=['EmberEvidenceCamera']
def write():OUT.write_text(json.dumps(R,indent=2),encoding='utf-8')
def xyz(v):return [v.x,v.y,v.z]
state={'phase':'start','wall':time.monotonic(),'start':0,'spell':False,'shots':set()}
def tick(dt):
    try:
        if time.monotonic()-state['wall']>95:raise RuntimeError('Runtime test exceeded 95 seconds')
        w=U.get_game_world()
        if not w:return
        c=unreal.GameplayStatics.get_player_character(w,0)
        if not c:return
        t=unreal.GameplayStatics.get_time_seconds(w);mesh=c.get_component_by_class(unreal.SkeletalMeshComponent);movement=c.get_component_by_class(unreal.CharacterMovementComponent);anim=mesh.get_anim_instance()
        if state['phase']=='start':
            R['pawn']=c.get_class().get_path_name();R['mesh']=mesh.get_editor_property('skeletal_mesh_asset').get_path_name();R['anim_class']=anim.get_class().get_path_name() if anim else None
            assert 'Ember' in R['pawn'] and 'Ember' in R['mesh'] and anim,'Incorrect playable character defaults'
            state['start']=t;state['phase']='test';state['origin']=c.get_actor_location();write()
        age=t-state['start'];pos=c.get_actor_location()
        if age<2:phase='idle'
        elif age<3.5:
            phase='walk';movement.set_editor_property('max_walk_speed',300.0);c.add_movement_input(unreal.Vector(1,0,0),1,False)
        elif age<5:
            phase='run';movement.set_editor_property('max_walk_speed',600.0);c.add_movement_input(unreal.Vector(1,0,0),1,False)
        elif age<7.5:
            phase='jump'
            if not state.get('jumped'):c.jump();state['jumped']=True;state['jumpz']=pos.z
            if age>5.25:c.stop_jumping()
            state['jump_rise']=max(state.get('jump_rise',0),pos.z-state['jumpz'])
        else:
            phase='spell'
            if not state['spell']:
                # Return to the unobstructed stage only for the presentation shot.
                # All locomotion/jump samples above retain their actual world positions.
                c.set_actor_location(state['origin'],False,False);pos=c.get_actor_location()
                montage=unreal.load_asset(D+'/AM_EmberSpell');duration=c.play_anim_montage(montage,1.0,'None');R['montage_return_seconds']=duration
                unreal.MaterialLibrary.set_scalar_parameter_value(w,unreal.load_asset(D+'/MPC_EmberSpell'),'SpellStart',t)
                state['spell']=True;state['spell_start']=t
                loc=pos+unreal.Vector(340,320,65);rot=unreal.MathLibrary.find_look_at_rotation(loc,pos+unreal.Vector(0,0,15))
                camera=unreal.GameplayStatics.get_all_actors_with_tag(w,'EmberEvidenceCamera')[0]
                camera.set_actor_location(loc,False,False);camera.set_actor_rotation(rot,False);camera.get_component_by_class(unreal.CameraComponent).set_field_of_view(40.0)
                unreal.GameplayStatics.get_player_controller(w,0).set_view_target_with_blend(camera,0.0)
        if not R['samples'] or age-R['samples'][-1]['seconds']>.15:
            R['samples'].append({'seconds':age,'phase':phase,'location':xyz(pos),'velocity':xyz(c.get_velocity()),'hand_local':xyz(mesh.get_socket_location('hand_r')-pos),'knee_local':xyz(mesh.get_socket_location('calf_l')-pos),'falling':movement.is_falling(),'montage_playing':anim.is_any_montage_playing()})
        if phase=='spell' and age>9 and 'spell' not in state['shots']:
            target=P/'Preview/UE5_Ember_Spell.png';unreal.AutomationLibrary.take_high_res_screenshot(1280,900,str(target));state['shots'].add('spell')
        if age>12.5:
            R['max_jump_rise_cm']=state.get('jump_rise',0);R['final_on_ground']=movement.is_moving_on_ground()
            def speed(phase):
                samples=[math.hypot(s['velocity'][0],s['velocity'][1]) for s in R['samples'] if s['phase']==phase];return max(samples or [0])
            R['walk_peak_cm_s']=speed('walk');R['run_peak_cm_s']=speed('run')
            R['checks']={'walk':speed('walk')>200,'run':speed('run')>500,'jump':state.get('jump_rise',0)>60,'landed':R['final_on_ground'],'montage':sum(s['montage_playing'] for s in R['samples'] if s['phase']=='spell')>6}
            R['status']='passed' if all(R['checks'].values()) else 'failed';write();unreal.unregister_slate_post_tick_callback(builtins._ember_runtime_test);L.editor_request_end_play()
    except Exception:
        R['status']='failed';R['error']=traceback.format_exc();write();unreal.unregister_slate_post_tick_callback(builtins._ember_runtime_test)
        if L.is_in_play_in_editor():L.editor_request_end_play()
write();builtins._ember_runtime_test=unreal.register_slate_post_tick_callback(tick);L.editor_request_begin_play()
