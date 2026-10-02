"""Static display pose and physical studio renders from an existing real model.

Independent scene copy: no claim of rigging, game runtime, or cloth simulation.
Usage: blender -b --python render_editorial_pose.py -- editorial01 concert13 [--draft]
"""
import bpy,bmesh,sys,math,json,re,hashlib
from pathlib import Path
from mathutils import Vector,Matrix

ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:]
VERSION,SOURCE=args[:2];DRAFT='--draft' in args
if not all(re.fullmatch(r'[A-Za-z0-9_-]+',v) for v in [VERSION,SOURCE]):raise ValueError('Invalid version')
OUT=ROOT/'Exports'/VERSION;RENDER=ROOT/'Renders'/VERSION
if OUT.exists() or RENDER.exists():raise RuntimeError('Fresh output directories required')
OUT.mkdir(parents=True);RENDER.mkdir(parents=True)
source=ROOT/'Exports'/SOURCE/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
scene=bpy.context.scene

# Remove only the inner garment panels completely covered by the outer jacket.
# The source mannequin and fitted suit differ at the pectorals; keeping both
# hidden surfaces caused dark intersections in the new perspective cameras.
inner=bpy.data.objects.get('Anatomically fitted open black shirt')
if inner:
    bm=bmesh.new();bm.from_mesh(inner.data)
    covered=[f for f in bm.faces if abs(f.calc_center_median().x)>.041 or f.calc_center_median().y>-.04]
    bmesh.ops.delete(bm,geom=covered,context='FACES');bm.to_mesh(inner.data);bm.free();inner.data.update()

def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)

def pose_point(p,group):
    c=p.copy();z=c.z;s=1 if c.x>=0 else -1
    # The model remains fully editable, with a modest asymmetric display stance.
    if group in ['01_Body','02_Innerwear','03_OuterRobe','06_Regalia'] and .83<z<1.59:
        w=smooth(.19,.275,abs(c.x))
        angle=math.radians(13 if s>0 else 17)*s*w
        pivot=Vector((s*.203,0,1.478));c=pivot+Matrix.Rotation(angle,3,'Y')@(c-pivot)
        if s<0:
            w=smooth(.27,.36,abs(p.x))*(1-smooth(1.18,1.29,p.z))
            pivot=Vector((-.275,-.005,1.215))
            c=pivot+Matrix.Rotation(math.radians(-12)*w,3,'X')@(c-pivot)
    if group=='02_Innerwear' and z<1.1:
        left=1-smooth(-.06,.03,c.x)
        c.y-=.055*left*(1-smooth(.72,1.07,z))
    # Small contrapposto shared by every garment and accessory.
    c.x+=.009*math.sin(max(0,min(1,z/1.65))*math.pi*1.6)
    if z>1.56:
        w=smooth(1.56,1.64,z);pivot=Vector((0,-.015,1.60))
        rot=Matrix.Rotation(math.radians(7)*w,3,'Z')@Matrix.Rotation(math.radians(-3)*w,3,'Y')
        c=pivot+rot@(c-pivot)
    return c

for ob in list(bpy.data.objects):
    if ob.type=='CURVES' and not ob.hide_render:
        # Native hair is attached rigidly to the head. Moving just the neck mesh
        # while leaving millions of strand points in the rest frame breaks roots.
        pivot=Vector((0,-.015,1.60));shift=Vector((.009*math.sin(math.pi*1.6),0,0))
        rot=Matrix.Rotation(math.radians(7),4,'Z')@Matrix.Rotation(math.radians(-3),4,'Y')
        ob.matrix_world=Matrix.Translation(pivot)@rot@Matrix.Translation(-pivot+shift)@ob.matrix_world
        continue
    if ob.type not in ['MESH','CURVE'] or ob.hide_render:continue
    group=ob.users_collection[0].name if ob.users_collection else ''
    if group.startswith('90_'):continue
    matrix=ob.matrix_world.copy();inv=matrix.inverted()
    if ob.type=='MESH':
        for v in ob.data.vertices:v.co=inv@pose_point(matrix@v.co,group)
        ob.data.update()
    else:
        for sp in ob.data.splines:
            if sp.type=='BEZIER':
                for p in sp.bezier_points:
                    for attr in ['co','handle_left','handle_right']:setattr(p,attr,inv@pose_point(matrix@getattr(p,attr),group))
            else:
                for p in sp.points:p.co=(*(inv@pose_point(matrix@Vector(p.co[:3]),group)),p.co.w)

# More cohesive wine cloth surface; microstructure remains visible in close-ups.
for name in ['Concert oxblood leather','Wine nappa tailored skirt']:
    mat=bpy.data.materials.get(name)
    if mat:
        bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.52;bs.inputs['Specular IOR Level'].default_value=.25
        bs.inputs['Coat Weight'].default_value=.035

stage=bpy.data.collections['90_Stage']
for ob in list(stage.objects):
    if ob.type in ['LIGHT','CAMERA']:bpy.data.objects.remove(ob,do_unlink=True)
# A real curved studio sweep eliminates the visible plane/world horizon.
profile=[(-8,-.008),(2,-.008)]+[(2+3*math.sin(j*math.pi/80),3-3*math.cos(j*math.pi/80)-.008) for j in range(1,41)]+[(5,9)]
verts=[(x,y,z) for x in [-12,12] for y,z in profile];n=len(profile)
faces=[(i,i+1,n+i+1,n+i) for i in range(n-1)]
me=bpy.data.meshes.new('Continuous studio cove');me.from_pydata(verts,[],faces);me.update()
backdrop=bpy.data.objects.new('Continuous studio cove',me);stage.objects.link(backdrop)
me.materials.append(bpy.data.materials['Stage graphite'])
for p in me.polygons:p.use_smooth=True
def area(name,loc,power,color,size,target,ratio=1):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='RECTANGLE';data.size=size;data.size_y=size*ratio
    ob=bpy.data.objects.new(name,data);stage.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    return ob
area('Warm portrait softbox',(-1.6,-2.6,3),185,(1,.87,.78),1.7,(0,0,1.3),1.3)
area('Cool detail fill',(1.8,-2.4,1.9),80,(.77,.85,1),1.6,(0,0,1.25),1.4)
area('Wine edge softbox',(-1.3,1.4,2.2),125,(1,.19,.15),1.2,(0,0,1.3),1.7)
area('Neutral contour',(1.3,1.7,2.7),160,(1,.91,.83),1.4,(0,0,1.3),1.8)
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.04,.048,.068,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.28
scene.render.engine='CYCLES';scene.cycles.samples=32 if DRAFT else 192;scene.cycles.use_denoising=True
if '--hair-detail' in args:
    scene.cycles.samples=384;scene.cycles.use_denoising=False
scene.cycles.transparent_max_bounces=16;scene.cycles.max_bounces=10
try:
    pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
    for d in pref.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:pass
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-.40
scene.render.resolution_percentage=55 if DRAFT else 100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.color_depth='8'
scene.render.film_transparent=False
shots=[
    ('01_Full_Beauty',(1.8,-5.5,1.70),(0,0,1.015),90,(1800,2400)),
    ('02_Half_Body',(.63,-2.75,1.75),(0,-.025,1.465),88,(1800,2100)),
    ('03_Portrait',(.28,-1.92,1.80),(0,-.025,1.736),111,(1800,2100)),
    ('04_Back',(-1.8,5.5,1.85),(0,0,1.015),90,(1500,2000))]
if '--portrait-only' in args:
    shots=[shot for shot in shots if shot[0]=='03_Portrait']
for name,loc,target,lens,res in shots:
    backdrop.rotation_euler.z=math.pi if name=='04_Back' else 0
    data=bpy.data.cameras.new(name);cam=bpy.data.objects.new(name,data);stage.objects.link(cam)
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();data.type='PERSP';data.lens=lens;data.clip_start=.01;data.clip_end=100
    scene.camera=cam;scene.render.resolution_x=res[0];scene.render.resolution_y=res[1];scene.render.filepath=str(RENDER/(name+'.png'))
    bpy.ops.render.render(write_still=True)
scene.camera=bpy.data.objects[shots[0][0]];scene.render.resolution_x=shots[0][4][0];scene.render.resolution_y=shots[0][4][1]
backdrop.rotation_euler.z=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Redline_Editorial.blend'))
report={'version':VERSION,'source':SOURCE,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'renderer':'Blender 4.5.9 Cycles','samples':scene.cycles.samples,'draft':DRAFT,'pose':'static geometric display pose, not a runtime rig','magic_particles':False,'images':[],'status':'visual study, not approved commercial-quality final'}
for p in sorted(RENDER.glob('*.png')):report['images'].append({'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(OUT/'render_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('EDITORIAL_SAVED',str(OUT),flush=True)
