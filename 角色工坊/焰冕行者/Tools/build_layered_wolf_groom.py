"""Actual scalp-derived, asymmetrically combed medium wolf-cut native groom.

Usage: blender --background --python this.py -- hairdesign01 [--draft]
Every candidate has fresh folders. Original reference pixels are not projected.
"""
import bpy,sys,json,re,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];VERSION=args[0];DRAFT='--draft' in args
if not re.fullmatch('[A-Za-z0-9_-]+',VERSION):raise ValueError(VERSION)
OUT=ROOT/'Exports'/VERSION;RENDER=ROOT/'Renders'/VERSION
if OUT.exists() or RENDER.exists():raise RuntimeError('Fresh candidate required')
OUT.mkdir(parents=True);RENDER.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports/atelier09/Ember_Regent.blend'))
col=bpy.data.collections['05_Hair']
for ob in list(col.objects):bpy.data.objects.remove(ob,do_unlink=True)
body=max((o for o in bpy.data.collections['01_Body'].objects if o.type=='MESH' and not o.hide_render and 'high-poly' not in o.name),key=lambda o:len(o.data.vertices))
bpy.context.view_layer.update();bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
C=Vector((0,-.044,1.771));rng=np.random.default_rng(617);N=72;t=np.linspace(0,1,N)

def scalp(theta,a):
 d=Vector((math.sin(theta)*math.sin(a),-math.sin(theta)*math.cos(a),math.cos(theta)))
 hit,n,_,_=bv.ray_cast(C,d,.35)
 if hit is None:return C+d*.103,d
 return hit,n

guides=[];types=[];widths=[]
# Fully covered underlying comb, with varied parent lengths. Roots and paths are
# measured on actual head geometry, not an assumed spherical skull.
for k in range(870):
 a=rng.uniform(-math.pi,math.pi);front=max(0,math.cos(a));back=max(0,-math.cos(a))
 maxth=1.06+.64*(1-front)+.10*back
 th=math.acos(1-rng.uniform(0,1)*(1-math.cos(maxth)))
 root,_=scalp(th,a);side=1 if root.x>-.023 else -1
 # Crown/cowl angles avoid a flat semicircular shared endpoint.
 end=max(th+.28,1.70+.13*(1-front)+rng.normal(0,.21))
 layer=rng.uniform(.60,1.15);phase=rng.uniform(0,2*math.pi)
 path=[]
 for s in t:
  theta=th+(end-th)*(s*.92+.08*s*s)
  sweep=side*(.38*front+.12)*math.sin(math.pi*s*.72)
  az=a+sweep+.075*math.sin(s*7+phase)*math.sin(math.pi*s)**2
  p,n=scalp(theta,az)
  lift=(.006+.013*layer)*math.sin(math.pi*s)**.85
  lift+=.0035*math.sin(s*8+phase)*math.sin(math.pi*s)**2
  p+=n*(.0005+lift)
  free=max(0,(s-.61)/.39)**1.3
  p.z-=free*(.025+.078*back+.025*(1-front))*layer
  p.x+=side*free*(.005+.010*math.sin(s*8+phase))
  p.y+=free*(.010*back-.009*front)
  path.append(p)
 guides.append(np.array(path));types.append('under');widths.append(.0034)

# Selected top/fringe locks with independent S-curves and unequal lengths.
# The heavier section sweeps to the model's right; the left ear has more space.
for side,count in [(1,46),(-1,30)]:
 for k in range(count):
  f=k/(count-1);rx=-.021+rng.normal(0,.007);ry=-.094+f*.143
  h,n,_,_=bv.ray_cast(Vector((rx,ry,2.05)),Vector((0,0,-1)),.45)
  if h is None:continue
  h+=n*.00045
  bend=rng.uniform(-.005,.005);z_end=rng.uniform(1.724,1.786)
  # No large common crown arch: lifts stay between 8 and 20 millimetres.
  p=np.array([h,(side*(.042+.025*f),-.123+.095*f,1.879+.008*(1-f)),
              (side*(.085+.016*f),-.158+.100*f,1.815-.017*f),
              (side*(.035+.069*f)+bend,-.165+.098*f,z_end)])
  s=t[:,None];path=p[0]*(1-s)**3+3*p[1]*(1-s)**2*s+3*p[2]*(1-s)*s*s+p[3]*s**3
  phase=rng.uniform(0,6.28)
  path[:,0]+=.007*np.sin(t*8+phase)*np.sin(math.pi*t)**2
  path[:,1]+=.003*np.sin(t*7+phase)*np.sin(math.pi*t)**2
  guides.append(path);types.append('fringe');widths.append(.0024)

# Back layers use actual posterior roots and curved tapered tips. Lengths stop
# above the coat rather than forming one rectangular hair curtain.
for k in range(115):
 a=math.pi*.58+math.pi*.84*k/114;th=rng.uniform(.45,1.72);root,n=scalp(th,a)
 side=1 if root.x>0 else -1;endz=rng.uniform(1.602,1.701);phase=rng.uniform(0,6.28)
 p=np.array([root,root+n*.016+Vector((0,.010,.002)),
             (root.x*1.15+.009*math.sin(phase),.104+abs(root.x)*.15,1.725),
             (root.x*1.05+side*.005,.112+.014*math.sin(phase),endz)])
 s=t[:,None];path=p[0]*(1-s)**3+3*p[1]*(1-s)**2*s+3*p[2]*(1-s)*s*s+p[3]*s**3
 path[:,0]+=.006*np.sin(t*10+phase)*np.sin(math.pi*t)
 guides.append(path);types.append('nape');widths.append(.003)

# Native strand interpolation around local parallel-transport-like frames.
# Fine phase variation prevents a shiny undivided ribbon through each bundle.
paths=[];rads=[];strand_types=[]
for gi,(guide,kind,width) in enumerate(zip(guides,types,widths)):
 count={'under':58,'fringe':150,'nape':120}[kind]
 tangent=np.gradient(guide,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-8)
 basis=np.cross(tangent,np.array([0,1,0]));basis/=np.maximum(np.linalg.norm(basis,axis=1,keepdims=True),1e-8);normal=np.cross(tangent,basis)
 phase=rng.uniform(0,6.28,(count,1));scatter=(.72+.28*np.sin(math.pi*t))*(1-.77*t**4)
 ox=rng.normal(0,width,(count,1))*scatter+.00065*np.sin(t*18+phase)*np.sin(math.pi*t)
 oy=rng.normal(0,width*.55,(count,1))*scatter+.00035*np.sin(t*23+phase)*np.sin(math.pi*t)
 xyz=guide[None,:,:]+basis[None,:,:]*ox[:,:,None]+normal[None,:,:]*oy[:,:,None]
 # Spread parent roots over the real scalp so the independent locks do not
 # require a visible opaque support cap or a sparse stubble underlayer.
 for j in range(count):
  hit,n,_,_=bv.find_nearest(Vector(xyz[j,0]))
  if hit is not None:
   delta=np.array(hit+n*.00035)-xyz[j,0];xyz[j]+=delta[None,:]*(1-t[:,None])**2
 # Individual trimming makes lock tips less regular without changing the roots.
 if kind!='under':
  stop=rng.uniform(.84,1,(count,1));idx=t[None,:]*stop*(N-1);lo=np.floor(idx).astype(int);hi=np.minimum(N-1,lo+1);fraction=(idx-lo)[:,:,None]
  xyz=xyz[np.arange(count)[:,None],lo]*(1-fraction)+xyz[np.arange(count)[:,None],hi]*fraction
 paths.append(xyz.astype(np.float32));rads.append((rng.uniform(.000029,.000044,(count,1))*(1-.96*t)**.65).astype(np.float32));strand_types.extend([kind]*count)
xyz=np.concatenate(paths);rad=np.concatenate(rads)
cu=bpy.data.hair_curves.new('Layered wolf cut real native fibers');cu.add_curves([N]*len(xyz));cu.attributes['position'].data.foreach_set('vector',xyz.ravel());cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',rad.ravel())
ob=bpy.data.objects.new('Asymmetric layered wolf cut groom',cu);col.objects.link(ob)
mat=bpy.data.materials.new('Dark cherry layered physical hair');mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear();bs=nt.nodes.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='COLOR';bs.inputs['Roughness'].default_value=.32;bs.inputs['Radial Roughness'].default_value=.48
hi=nt.nodes.new('ShaderNodeHairInfo');r=nt.nodes.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(.008,.001,.0013,1);r.color_ramp.elements[1].color=(.045,.005,.006,1);nt.links.new(hi.outputs['Random'],r.inputs[0]);nt.links.new(r.outputs[0],bs.inputs['Color']);out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(bs.outputs[0],out.inputs[0]);cu.materials.append(mat)

stage=bpy.data.collections['90_Stage'];scene=bpy.context.scene
for ob in list(stage.objects):
 if ob.type in ['LIGHT','CAMERA']:bpy.data.objects.remove(ob,do_unlink=True)
def area(name,loc,power,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=size;o=bpy.data.objects.new(name,d);stage.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,-.025,1.74))-o.location).to_track_quat('-Z','Y').to_euler()
area('Neutral key',(-1.5,-2,2.7),115,1.5);area('Neutral fill',(1.5,-1.5,1.9),48,1.5);area('Neutral rim',(1,1.7,2.5),90,1.2)
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.055,.055,.055,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.3
scene.render.engine='CYCLES';scene.cycles.samples=48 if DRAFT else 128;scene.cycles.use_denoising=True
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-.25
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=70 if DRAFT else 100
shots=[('01_Front',(0,-4,1.76)),('02_ThreeQuarter',(.95,-3,1.79)),('03_Side',(4,-.025,1.76)),('04_Back',(0,4,1.76))]
for name,loc in shots:
 d=bpy.data.cameras.new(name);cam=bpy.data.objects.new(name,d);stage.objects.link(cam);cam.location=loc;cam.rotation_euler=(Vector((0,-.025,1.745))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=.54;scene.camera=cam;scene.render.filepath=str(RENDER/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Ember_Regent.blend'))
report={'version':VERSION,'source':'atelier09','seed':617,'guide_count':len(guides),'strand_count':len(xyz),'point_count':int(xyz.size//3),'method':'actual scalp rays, independent layered comb and diagonal crown/fringe, native fibers','style':'asymmetrical medium layered wolf cut','renderer':'Cycles OptiX','samples':scene.cycles.samples,'draft':DRAFT,'status':'candidate requires visual review, no artistic approval implied'}
(OUT/'groom_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'guide_design.json').write_text(json.dumps({'kinds':types,'widths_m':widths,'positions_m':[g.tolist() for g in guides]},ensure_ascii=False),encoding='utf-8')
print('WOLF_GROOM_SAVED',VERSION,report,flush=True)
