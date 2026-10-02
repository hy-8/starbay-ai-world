"""Convert fitted CC-BY artist hair-card surfaces into actual native fibers.

Preserves original source cards hidden for edits. Hair lengths and frontal
opening are changed in 3D, then per-island UV paths preserve authored waves.
"""
import bpy,sys,re,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];VERSION=args[0];DRAFT='--draft' in args
if not re.fullmatch('[A-Za-z0-9_-]+',VERSION):raise ValueError(VERSION)
OUT=ROOT/'Exports'/VERSION;RENDER=ROOT/'Renders'/VERSION
if OUT.exists() or RENDER.exists():raise RuntimeError('Fresh output required')
OUT.mkdir(parents=True);RENDER.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports/hairasset02/Ember_Regent.blend'))
ob=next(o for o in bpy.data.collections['05_Hair'].objects if o.type=='MESH')

def components(me):
 adj=[set() for _ in me.vertices]
 for e in me.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
 seen=set();result=[]
 for i in range(len(adj)):
  if i in seen:continue
  todo=[i];seen.add(i);group=[]
  while todo:
   a=todo.pop();group.append(a)
   for b in adj[a]:
    if b not in seen:seen.add(b);todo.append(b)
  result.append(group)
 return result

# Each original island has its own silhouette. The few long central fringe
# cards are shortened more than the side/nape layers, keeping the eyes open.
control_groups=components(ob.data)
for ci,ids in enumerate(control_groups):
 pts=np.array([ob.data.vertices[i].co for i in ids]);minz=pts[:,2].min();front=pts[:,1].min()<-.193
 desired=1.747 if front else 1.647+.043*((ci*7)%11)/10
 ratio=np.clip((1.855-desired)/max(.035,1.855-minz),.25,.88)
 for i in ids:
  v=ob.data.vertices[i];x,y,z=v.co;w=np.clip((1.85-z)/.15,0,1)
  if z<1.855:z=1.855+(z-1.855)*ratio
  x*=1-.25*w;y=-.044+(y+.044)*(1-.27*w)
  if y<-.13 and z<1.795:
   opening=np.clip((1.795-z)/.07,0,1);x=math.copysign(math.sqrt(x*x+.036**2*opening),x if abs(x)>.001 else 1)
  v.co=(x,y,z)
ob.data.update();bpy.context.view_layer.update()
evaluated=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=evaluated.to_mesh(preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get())
groups=components(me);me.calc_loop_triangles();v_to_group={vi:ci for ci,ids in enumerate(groups) for vi in ids}
tri_groups=[[] for _ in groups]
for tr in me.loop_triangles:tri_groups[v_to_group[tr.vertices[0]]].append(tr)
uvlayer=me.uv_layers.active
rng=np.random.default_rng(717);N=88;allpaths=[];allradii=[];guide_count=0

def sample(uv,bv,tri_uv,tri_xyz):
 p,n,idx,dist=bv.find_nearest(Vector((uv[0],uv[1],0)))
 a,b,c=tri_uv[idx];q=np.array(p[:2]);den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
 if abs(den)<1e-12:return tri_xyz[idx,0]
 u=((b[1]-c[1])*(q[0]-c[0])+(c[0]-b[0])*(q[1]-c[1]))/den
 v=((c[1]-a[1])*(q[0]-c[0])+(a[0]-c[0])*(q[1]-c[1]))/den
 return tri_xyz[idx,0]*u+tri_xyz[idx,1]*v+tri_xyz[idx,2]*(1-u-v)

for ci,tri in enumerate(tri_groups):
 if not tri:continue
 tri_uv=np.array([[uvlayer.data[li].uv for li in tr.loops] for tr in tri],dtype=float)
 tri_xyz=np.array([[me.vertices[vi].co for vi in tr.vertices] for tr in tri],dtype=float)
 uvverts=np.column_stack([tri_uv.reshape(-1,2),np.zeros(len(tri_uv)*3)]);faces=np.arange(len(uvverts)).reshape(-1,3)
 bv=BVHTree.FromPolygons([Vector(p) for p in uvverts],faces.tolist(),all_triangles=True)
 umin,vmin=tri_uv.min((0,1));umax,vmax=tri_uv.max((0,1))
 top=sample(((umin+umax)/2,vmax-.0002),bv,tri_uv,tri_xyz);bottom=sample(((umin+umax)/2,vmin+.0002),bv,tri_uv,tri_xyz)
 ascending=bottom[2]>top[2]
 for j in range(72):
  u=umin+(umax-umin)*(j+.5)/72;v=np.linspace(vmin+.0002,vmax-.0002,N) if ascending else np.linspace(vmax-.0002,vmin+.0002,N)
  phase=rng.uniform(0,6.28);us=u+(umax-umin)*.005*np.sin(np.linspace(0,8,N)+phase)
  guide=np.array([sample((uu,vv),bv,tri_uv,tri_xyz) for uu,vv in zip(us,v)])
  tangent=np.gradient(guide,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-8)
  # True card lateral direction from the same UV island, not a fixed billboard.
  across=np.array([sample((min(umax-.0001,uu+.0004),vv),bv,tri_uv,tri_xyz)-sample((max(umin+.0001,uu-.0004),vv),bv,tri_uv,tri_xyz) for uu,vv in zip(us,v)])
  across/=np.maximum(np.linalg.norm(across,axis=1,keepdims=True),1e-8);normal=np.cross(tangent,across);normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-8)
  count=24;t=np.linspace(0,1,N)[None,:];phase=rng.uniform(0,6.28,(count,1))
  lateral=rng.normal(0,.00065,(count,1))*(.7+.3*np.sin(math.pi*t))+.00030*np.sin(t*18+phase)*np.sin(math.pi*t)
  thickness=rng.normal(0,.0010,(count,1))*np.sin(math.pi*t)**.7+.00020*np.sin(t*21+phase)*np.sin(math.pi*t)
  strand=guide[None,:,:]+across[None,:,:]*lateral[:,:,None]+normal[None,:,:]*thickness[:,:,None]
  # Unequal tip lengths create small gaps; root/crown waves remain the artist's.
  stops=rng.uniform(.86,1,(count,1));q=t*stops*(N-1);lo=np.floor(q).astype(int);hi=np.minimum(N-1,lo+1);f=(q-lo)[:,:,None]
  strand=strand[np.arange(count)[:,None],lo]*(1-f)+strand[np.arange(count)[:,None],hi]*f
  allpaths.append(strand.astype(np.float32));allradii.append((rng.uniform(.000027,.000043,(count,1))*(1-.965*t)**.7).astype(np.float32));guide_count+=1
 print('CONVERTED_CARD',ci,len(groups),flush=True)
evaluated.to_mesh_clear()
xyz=np.concatenate(allpaths);radii=np.concatenate(allradii)
cu=bpy.data.hair_curves.new('Artist wave islands converted to real fibers');cu.add_curves([N]*len(xyz));cu.attributes['position'].data.foreach_set('vector',xyz.ravel());cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',radii.ravel())
groom=bpy.data.objects.new('Medium cherry layered groom from Elvaerwyn CC-BY',cu);bpy.data.collections['05_Hair'].objects.link(groom)
ob.name='EDITABLE_SOURCE reshaped authored wave cards';ob.hide_render=True;ob.hide_set(True)
mat=bpy.data.materials.new('Dark cherry native fiber');mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear();bs=nt.nodes.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='COLOR';bs.inputs['Roughness'].default_value=.37;bs.inputs['Radial Roughness'].default_value=.5
hi=nt.nodes.new('ShaderNodeHairInfo');r=nt.nodes.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(.006,.0009,.0013,1);r.color_ramp.elements[1].color=(.038,.0045,.0055,1);nt.links.new(hi.outputs['Random'],r.inputs[0]);nt.links.new(r.outputs[0],bs.inputs['Color']);out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(bs.outputs[0],out.inputs[0]);cu.materials.append(mat)
scene=bpy.context.scene;scene.cycles.samples=48 if DRAFT else 160;scene.render.resolution_percentage=70 if DRAFT else 100
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU'
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(RENDER/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Ember_Regent.blend'))
report=json.loads((ROOT/'Exports/hairasset02/groom_manifest.json').read_text(encoding='utf-8'));report.update({'version':VERSION,'source':'hairasset02','method':'independent artist UV ribbon islands sampled into native strands; cards hidden','changes':'original authored waves reshaped into medium layered length, eye opening and finer strand conversion','cards':len(groups),'guides':guide_count,'strands':len(xyz),'samples':scene.cycles.samples,'draft':DRAFT,'status':'candidate requiring visual review'})
(OUT/'groom_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('CARD_GROOM_SAVED',VERSION,len(xyz),flush=True)
