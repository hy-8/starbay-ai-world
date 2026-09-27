"""Create a separate UE-compatible skinned candidate from the protected v14 sculpt.
Epic mannequin is a local binding reference, not part of the character export.
All output is versioned. Uses nearest surface weights plus semantic rigid/cloth groups.
"""
import bpy,math,json,sys,hashlib,random
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[1]
VERSION=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'rig01'
OUT=ROOT/'Exports'/VERSION
if not bpy.app.background or (OUT/'Ember_Rigged.blend').exists():raise RuntimeError('Use fresh background candidate')
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports/v14/Ember_Regent.blend'))
random.seed(31)
scene=bpy.context.scene
stage=bpy.data.collections['90_Stage']
source_objects=set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'Source/UE_Reference/Manny.fbx'))
imported=set(bpy.data.objects)-source_objects
rig=next(o for o in imported if o.type=='ARMATURE')
rig.name='root'
refs=[o for o in imported if o.type=='MESH']
assert refs
# Store the exact UE bone rest frames and nearest mannequin skin weights in world meters.
refpoints=[];refweights=[]
for ob in refs:
    groups={g.index:g.name for g in ob.vertex_groups}
    for v in ob.data.vertices:
        refpoints.append(ob.matrix_world@v.co)
        refweights.append({groups[g.group]:g.weight for g in v.groups if groups[g.group] in rig.data.bones and g.weight>.0001})
tree=KDTree(len(refpoints))
for i,v in enumerate(refpoints):tree.insert(v,i)
tree.balance()
bones={b.name:rig.matrix_world@b.head_local for b in rig.data.bones}
sys.path.insert(0,str(ROOT/'Tools'))
from hand_binding import HandBinding
hand_binding=HandBinding(ROOT,rig)

gamecol=bpy.data.collections.new('10_GameCharacter');scene.collection.children.link(gamecol)
for c in list(rig.users_collection):c.objects.unlink(rig)
gamecol.objects.link(rig)
rig.show_in_front=True
rig.data.display_type='STICK'

# Add accessory chains while retaining all original mannequin bone names/rest frames.
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
hand_binding.add_bones(rig)
for side,x in [('L',-.19),('C',0),('R',.19)]:
    previous='spine_05'
    for i in range(4):
        b=rig.data.edit_bones.new('cape_'+side+'_'+str(i+1))
        b.head=(x*100,(.14+i*.12)*100,(1.48-i*.33)*100)
        b.tail=(x*100,(.14+(i+1)*.12)*100,(1.48-(i+1)*.33)*100)
        b.parent=rig.data.edit_bones[previous];previous=b.name
for side,x in [('L',-.11),('R',.11),('B',0)]:
    previous='head'
    for i in range(3):
        b=rig.data.edit_bones.new('hair_'+side+'_'+str(i+1))
        yy=.08 if side=='B' else -.06
        b.head=(x*100,yy*100,(1.77-i*.22)*100);b.tail=(x*100,(yy+.02)*100,(1.55-i*.22)*100)
        b.parent=rig.data.edit_bones[previous];previous=b.name
for side,x,y in [('FL',.17,-.13),('FR',-.17,-.13),('BL',.17,.11),('BR',-.17,.11)]:
    previous='pelvis'
    for i in range(3):
        b=rig.data.edit_bones.new('skirt_'+side+'_'+str(i+1))
        b.head=(x*100,y*100,(1.0-i*.29)*100);b.tail=(x*100,y*100,(.71-i*.29)*100)
        b.parent=rig.data.edit_bones[previous];previous=b.name
bpy.ops.object.mode_set(mode='OBJECT')
rig.animation_data_clear()

def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)

def nearest_weights(co):
    hits=tree.find_n(co,4);weights={}
    for _,idx,dist in hits:
        k=1/max(.004,dist)**3
        for name,w in refweights[idx].items():weights[name]=weights.get(name,0)+w*k
    top=sorted(weights.items(),key=lambda x:x[1],reverse=True)[:4]
    total=sum(w for _,w in top)
    return {n:w/total for n,w in top} if total else {'pelvis':1}

def chain_weights(co,prefix,top,step,count):
    f=max(0,min(count-1,(top-co.z)/step));i=int(f);q=f-i
    return {prefix+str(i+1):1-q,prefix+str(min(count,i+2)):q} if q>.0001 else {prefix+str(i+1):1}

materials={}
def simplify_mat(mat):
    name=mat.name
    if name.startswith(('Ivory fiber','Pearl white','Silver hair')):key='Ivory fiber 0'
    elif name.startswith(('Dark limbal','Warm charcoal','Pupil')):key='Pupil'
    elif name in ['Blackened raised gold relief','Platinum woven braid','Antique gold recess']:key='Brushed champagne gold'
    else:key=name
    return bpy.data.materials.get(key,mat)

objects=[];cost_before=0
for original in sorted(source_objects,key=lambda x:x.name):
    if original.type not in {'MESH','CURVE'} or original.hide_render or original.hide_get():continue
    group=original.users_collection[0].name
    if group.startswith(('90_','08_')):continue
    ob=original.copy();ob.data=original.data.copy();gamecol.objects.link(ob);ob.hide_set(False)
    if ob.type=='CURVE':
        ob.data.bevel_resolution=0
        if 'individual fibers' in ob.name or 'flyaway fibers' in ob.name:
            old=ob.data;cu=bpy.data.curves.new(ob.name+' game fibers','CURVE');cu.dimensions='3D';cu.bevel_depth=old.bevel_depth*2.1;cu.bevel_resolution=0
            for idx,spline in enumerate(old.splines):
                if idx%4:continue
                points=list(spline.points)[::3]
                if points[-1]!=spline.points[-1]:points.append(spline.points[-1])
                sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
                for p,q in zip(sp.points,points):p.co=q.co;p.radius=q.radius
            for mat in old.materials:cu.materials.append(mat)
            ob.data=cu
    for mod in list(ob.modifiers):
        if mod.type=='SUBSURF':
            if group=='01_Body':mod.levels=1;mod.render_levels=1
            else:ob.modifiers.remove(mod)
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.object.convert(target='MESH');ob=bpy.context.object
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    # Repose the relaxed showcase arms to the official mannequin bind stance.
    for v in ob.data.vertices:
        c=v.co.copy()
        if group in ['01_Body','03_OuterRobe'] and .80<c.z<1.58:
            s=1 if c.x>=0 else -1
            weight=smooth(.175,.265,abs(c.x));a=s*math.radians(18)*weight
            x=c.x-s*.203;z=c.z-1.478
            c.x=s*.203+math.cos(a)*x-math.sin(a)*z
            c.z=1.478+math.sin(a)*x+math.cos(a)*z
        if group=='02_Innerwear' and c.z<1.05:
            c.x-=math.copysign(.055*(1-smooth(.20,1.05,c.z)),c.x)
        if group=='04_Mantle':
            c.x=c.x*.50-.22*smooth(.05,.9,c.x)
            c.y+=max(0,v.co.x)*.30
        if group=='07_Staff':
            h=hand_binding.staff_center();t=(h.z-.05)/1.85
            c+=Vector((h.x-(.61+.25*t),h.y-(-.03+.045*t),0))
        if group=='01_Body' and abs(c.x)>.37 and c.z<1.23:
            c,_=hand_binding.fit(c)
        v.co=c
    # Reduce dense parametric meshes; preserve more facial topology than cloth.
    if len(ob.data.polygons)>2500 and group!='05_Hair':
        dec=ob.modifiers.new('Game surface reduction','DECIMATE');dec.ratio=.65 if group=='01_Body' else .42
        bpy.ops.object.modifier_apply(modifier=dec.name)
    for i,mat in enumerate(ob.data.materials):ob.data.materials[i]=simplify_mat(mat)
    ob.vertex_groups.clear()
    groups={name:ob.vertex_groups.new(name=name) for name in rig.data.bones.keys()}
    for v in ob.data.vertices:
        c=v.co
        if group=='07_Staff':weights={'hand_l':1}
        elif group=='05_Hair':
            if c.z>1.75:weights={'head':1}
            else:
                side='B' if c.y>.10 else ('L' if c.x<0 else 'R')
                weights=chain_weights(c,'hair_'+side+'_',1.75,.22,3)
        elif group=='01_Body' and c.z>1.63:weights={'head':1}
        elif group=='01_Body' and abs(c.x)>.37 and c.z<1.23:
            weights=hand_binding.skin(c) or nearest_weights(c)
        elif group=='04_Mantle':
            side='L' if c.x<-.08 else ('R' if c.x>.12 else 'C')
            weights=chain_weights(c,'cape_'+side+'_',1.48,.33,4)
        elif group=='06_Regalia' and any(t in ob.name.lower() for t in ['crown','circlet','forehead']):weights={'head':1}
        elif group=='06_Regalia' and 'Shoulder' in ob.name:weights={'clavicle_l' if c.x>0 else 'clavicle_r':1}
        elif c.z<1.05 and (group=='03_OuterRobe' or (group=='02_Innerwear' and not any(t in ob.name.lower() for t in ['trouser','boot']))):
            # Independent skirt chains avoid stretching the hem between opposite legs.
            side=('F' if c.y<0 else 'B')+('L' if c.x>=0 else 'R')
            weights=chain_weights(c,'skirt_'+side+'_',1.0,.29,3)
        else:weights=nearest_weights(c)
        for name,w in weights.items():
            if w>.00001:groups[name].add([v.index],w,'REPLACE')
    mod=ob.modifiers.new('Ember skeleton deformation','ARMATURE');mod.object=rig
    ob.parent=rig;ob.matrix_parent_inverse=rig.matrix_world.inverted()
    objects.append(ob)
    original.hide_render=True;original.hide_set(True)
    print('SKINNED',ob.name,len(ob.data.vertices),flush=True)
for ob in refs:ob.hide_render=True;ob.hide_set(True)
for ob in source_objects:
    if ob.users_collection and ob.users_collection[0].name=='08_EmberFX':ob.hide_render=True;ob.hide_set(True)

# Join skinned pieces into one mesh while retaining material slots and deformation groups.
bpy.ops.object.select_all(action='DESELECT')
for ob in objects:ob.select_set(True)
bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();character=bpy.context.object;character.name='SK_EmberRegent'
used={g.group for v in character.data.vertices for g in v.groups}
for g in reversed(list(character.vertex_groups)):
    if g.index not in used:character.vertex_groups.remove(g)
triangles=sum(len(p.vertices)-2 for p in character.data.polygons)
rig.select_set(True)
# Retain exact parent bind inverse after joining, and disable hidden source collections in renders.
scene.render.fps=30;scene.frame_start=1;scene.frame_end=120
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Ember_Rigged.blend'))
bpy.ops.export_scene.fbx(filepath=str(OUT/'SK_EmberRegent.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',path_mode='COPY',embed_textures=True)
report={'version':VERSION,'source':'v14','status':'bound candidate; requires deformation and UE runtime validation','triangles':triangles,'vertices':len(character.data.vertices),'bones':len(rig.data.bones),'materials':[m.name for m in character.data.materials],'epic_reference':'Source/UE_Reference/sources.json','files':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in OUT.iterdir() if p.suffix in ['.blend','.fbx']}}
(OUT/'rig_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('GAME_RIG_CREATED',json.dumps(report),flush=True)
