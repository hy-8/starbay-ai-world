"""Bake template locomotion, original spell choreography and accessory lag to a new candidate.
Blender render frames are pose checks, not proof of UE playability.
"""
import bpy,math,json,sys,hashlib
from mathutils import Quaternion,Vector,Matrix
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:]
src=args[0] if args else 'rig01';version=args[1] if len(args)>1 else 'motion01'
OUT=ROOT/'Exports'/version;RENDER=ROOT/'Renders'/version
if not bpy.app.background or (OUT/'Ember_Animated.blend').exists():raise RuntimeError('Fresh background candidate required')
OUT.mkdir(parents=True,exist_ok=True);RENDER.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports'/src/'Ember_Rigged.blend'))
rig=bpy.data.objects['root'];character=bpy.data.objects['SK_EmberRegent'];scene=bpy.context.scene
# Keep the source sculpt in its own v14 file; remove hidden scratch copies from this animated derivative.
for ob in list(bpy.data.objects):
    if ob not in [rig,character] and not any(c.name=='90_Stage' for c in ob.users_collection):bpy.data.objects.remove(ob,do_unlink=True)
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
rig.animation_data_create();scene.render.fps=30
actions={};reports=[]
def world_rotation(pb,axis,angle):
    local=pb.bone.matrix_local.to_quaternion().inverted()@Vector(axis)
    return Quaternion(local,angle)
for name in ['Idle','Walk','Run','Jump','Fall','Land']:
    before=set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(ROOT/'Source/UE_Reference'/(name+'.fbx')))
    imported=set(bpy.data.objects)-before;source=next(o for o in imported if o.type=='ARMATURE')
    sa=source.animation_data.action
    end=int(sa.frame_range[1]);scene.frame_start=1;scene.frame_end=end
    act=bpy.data.actions.new('Ember_'+name);rig.animation_data.action=act
    for frame in range(1,end+1):
        scene.frame_set(frame);phase=(frame-1)/max(1,end-1)*math.tau
        rig.scale=(.01,.01,.01);rig.location=(0,0,0);rig.rotation_euler=(0,0,0)
        rig.keyframe_insert('scale',frame=frame);rig.keyframe_insert('location',frame=frame);rig.keyframe_insert('rotation_euler',frame=frame)
        for pb in rig.pose.bones:
            pb.rotation_mode='QUATERNION'
            if pb.name in source.pose.bones:
                sp=source.pose.bones[pb.name];pb.location=sp.location;pb.rotation_quaternion=sp.rotation_quaternion;pb.scale=sp.scale
            else:
                pb.location=(0,0,0);pb.scale=(1,1,1)
                idx=int(pb.name[-1]);amp={'Idle':.035,'Walk':.075,'Run':.13,'Jump':.16,'Fall':.12,'Land':.09}[name]
                if pb.name.startswith('grip'):
                    direction=(pb.bone.tail_local-pb.bone.head_local).normalized()
                    normal=Vector((0,-1,0));axis=direction.cross(normal).normalized()
                    angle=([0,.58,1.10,.66][idx] if '_L_' in pb.name else [0,.08,.16,.10][idx])
                    if 'thumb' in pb.name:angle*=.50
                    pb.rotation_quaternion=world_rotation(pb,axis,angle)
                elif pb.name.startswith('cape'):
                    pb.rotation_quaternion=world_rotation(pb,(1,0,0),amp*math.sin(phase-idx*.62)) @ world_rotation(pb,(0,0,1),amp*.5*math.sin(phase-idx*.9+.7))
                elif pb.name.startswith('skirt'):
                    side=1 if '_FL_' in pb.name or '_BL_' in pb.name else -1
                    swing={'Idle':.015,'Walk':.14,'Run':.29,'Jump':.23,'Fall':.13,'Land':.12}[name]
                    pb.rotation_quaternion=world_rotation(pb,(1,0,0),side*swing*math.sin(phase-idx*.38)/idx) @ world_rotation(pb,(0,1,0),side*.04)
                else:pb.rotation_quaternion=world_rotation(pb,(1,0,0),amp*.45*math.sin(phase-idx*.83))
            # A relaxed, quieter staff arm reduces the long staff's swing during locomotion.
            if pb.name in ['upperarm_l','lowerarm_l'] and name in ['Idle','Walk','Run']:
                pb.rotation_quaternion=Quaternion().slerp(pb.rotation_quaternion,.35)
            if pb.name.endswith('_l') and any(pb.name.startswith(t+'_0') for t in ['index','middle','ring','pinky']):
                joint=int(pb.name.split('_')[1]);pb.rotation_quaternion=world_rotation(pb,(0,.84,-.55),[0,.90,1.05,.60][joint])
            elif pb.name.startswith('thumb_0') and pb.name.endswith('_l'):
                pb.rotation_quaternion=world_rotation(pb,(0,-.65,.76),.40)
            pb.keyframe_insert('location',frame=frame,group=pb.name);pb.keyframe_insert('rotation_quaternion',frame=frame,group=pb.name);pb.keyframe_insert('scale',frame=frame,group=pb.name)
    act.use_fake_user=True;actions[name]=act
    for ob in imported:bpy.data.objects.remove(ob,do_unlink=True)
    bpy.data.actions.remove(sa)
    reports.append({'action':name,'frames':end,'duration_seconds':(end-1)/30,'source':'Epic UE5.6 template, with baked accessory lag and reduced staff-arm swing'})

# Authored four-second summon/release/settle, based on the idle stance.
rig.animation_data.action=actions['Idle'];scene.frame_set(1)
baseline={p.name:(p.location.copy(),p.rotation_quaternion.copy(),p.scale.copy()) for p in rig.pose.bones}
spell=bpy.data.actions.new('Ember_Spell');rig.animation_data.action=spell;end=121
def envelope(f,a,b,c,d):
    if f<a or f>d:return 0
    if f<b:t=(f-a)/(b-a);return t*t*(3-2*t)
    if f<=c:return 1
    t=(d-f)/(d-c);return t*t*(3-2*t)
for frame in range(1,end+1):
    scene.frame_set(frame);raise0=envelope(frame,1,38,70,115);cast=envelope(frame,45,65,78,106)
    rig.scale=(.01,.01,.01);rig.location=(0,0,0);rig.rotation_euler=(0,0,0)
    rig.keyframe_insert('scale',frame=frame);rig.keyframe_insert('location',frame=frame);rig.keyframe_insert('rotation_euler',frame=frame)
    for pb in rig.pose.bones:
        loc,q,scale=baseline[pb.name];pb.location=loc;pb.rotation_quaternion=q;pb.scale=scale
        if pb.name=='upperarm_r':pb.rotation_quaternion=world_rotation(pb,(1,0,0),-1.02*raise0)@world_rotation(pb,(0,1,0),-.30*raise0)@q
        elif pb.name=='lowerarm_r':pb.rotation_quaternion=world_rotation(pb,(1,0,0),-.55*raise0+.38*cast)@q
        elif pb.name=='hand_r':pb.rotation_quaternion=world_rotation(pb,(0,0,1),-.30*cast)@q
        elif pb.name=='upperarm_l':pb.rotation_quaternion=world_rotation(pb,(1,0,0),-.24*raise0)@q
        elif pb.name=='spine_03':pb.rotation_quaternion=world_rotation(pb,(0,0,1),-.16*raise0+.24*cast)@q
        elif pb.name=='head':pb.rotation_quaternion=world_rotation(pb,(0,0,1),.16*raise0)@q
        elif pb.name.startswith(('cape_','hair_','skirt_')):
            idx=int(pb.name[-1]);amp=.05+.15*cast
            pb.rotation_quaternion=world_rotation(pb,(1,0,0),amp*math.sin(frame/18-idx*.6))@q
        pb.keyframe_insert('location',frame=frame,group=pb.name);pb.keyframe_insert('rotation_quaternion',frame=frame,group=pb.name);pb.keyframe_insert('scale',frame=frame,group=pb.name)
spell.use_fake_user=True;actions['Spell']=spell
reports.append({'action':'Spell','frames':end,'duration_seconds':4,'source':'Original keyframed summon/release/settle; not motion capture'})

# Export each clip separately so UE imports named sequences without an action-name ambiguity.
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
for name,act in actions.items():
    rig.animation_data.action=act;scene.frame_start=1;scene.frame_end=int(act.frame_range[1]);scene.frame_set(1)
    bpy.ops.export_scene.fbx(filepath=str(OUT/('A_Ember_'+name+'.fbx')),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z')
rig.animation_data.action=actions['Idle'];scene.frame_start=1;scene.frame_end=int(actions['Idle'].frame_range[1]);scene.frame_set(1)
scene.render.engine='CYCLES';scene.cycles.samples=40;scene.render.resolution_x=1280;scene.render.resolution_y=1280
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:pass
camera=scene.camera;camera.location=(3,-7,2.7);target=Vector((.05,.10,1.1));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=2.55
for name,frame in [('Idle',1),('Walk',12),('Run',10),('Jump',10),('Spell',65)]:
    rig.animation_data.action=actions[name];scene.frame_set(frame);scene.render.filepath=str(RENDER/(name+'.png'));bpy.ops.render.render(write_still=True)
rig.animation_data.action=actions['Idle'];scene.frame_set(1)
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Ember_Animated.blend'))
(OUT/'animation_manifest.json').write_text(json.dumps({'version':version,'rig_source':src,'actions':reports,'status':'baked skeletal animation; UE and deformation validation pending','files':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in OUT.iterdir() if p.suffix in ['.fbx','.blend']}},indent=2),encoding='utf-8')
print('ANIMATED_CANDIDATE_CREATED',version,flush=True)
