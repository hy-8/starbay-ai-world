"""Bind a CC0 authored groom using identical MakeHuman vertex correspondence.

Each strand follows a source/target scalp triangle frame, rather than guessed
global scale and per-point surface clamping. Fresh candidate and QC views only.
"""
import bpy,sys,json,re,math,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];VERSION,STYLE=args[:2]
if not re.fullmatch('[A-Za-z0-9_-]+',VERSION):raise ValueError(VERSION)
if STYLE not in ['basic_short_hair','straight_hair_to_shoulder']:raise ValueError(STYLE)
OUT=ROOT/'Exports'/VERSION;RENDER=ROOT/'Renders'/VERSION
if OUT.exists() or RENDER.exists():raise RuntimeError('Fresh directories required')
OUT.mkdir(parents=True);RENDER.mkdir(parents=True)
lib=ROOT/'Source/HairEditorCC0/hair/haireditor/hair.blend'
bpy.ops.wm.open_mainfile(filepath=str(lib))
surface=bpy.data.objects[STYLE].data.surface
source_vertices=np.array([surface.matrix_world@v.co for v in surface.data.vertices],dtype=float)
surface.data.calc_loop_triangles();triangles=np.array([list(t.vertices) for t in surface.data.loop_triangles],dtype=int)
source_bvh=BVHTree.FromPolygons([Vector(p) for p in source_vertices],triangles.tolist(),all_triangles=True)

target=[]
for line in (ROOT/'Source/base.obj').read_text().splitlines():
 q=line.split()
 if q and q[0]=='v':target.append(tuple(map(float,q[1:4])))
target=np.array(target,dtype=float)
for line in (ROOT/'Source/male_young.target').read_text().splitlines():
 q=line.split()
 if len(q)==4 and q[0].isdigit():target[int(q[0])]+=np.array(list(map(float,q[1:4])))
target=np.stack([target[:,0]*.115,-target[:,2]*.115,(target[:,1]+8.188)*.115],axis=1)
for record in json.loads((ROOT/'Source/couture_sources.json').read_text(encoding='utf-8')):
 for line in (ROOT/'Source'/record['file']).read_text().splitlines():
  q=line.split()
  if len(q)==4 and q[0].isdigit():
   dx,dy,dz=map(float,q[1:]);target[int(q[0])]+=np.array([dx,-dz,dy])*(.115*record['weight'])
if len(target)!=len(source_vertices):raise RuntimeError('Source topology correspondence absent')

pack=ROOT/'Source/HairEditorCC0'/('baked2_'+STYLE+'.npz');data=np.load(pack)
xyz=data['positions'].astype(float);sizes=data['sizes'];radii=data['radii'].astype(float)*.75
matrix=data['matrix'];xyz=xyz@matrix[:3,:3].T+matrix[:3,3]
base='hairrecongroom05' if '--neutral' in args else 'atelier09'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports'/base/'Ember_Regent.blend'))
body=max((o for o in bpy.data.collections['01_Body'].objects if o.type=='MESH' and not o.hide_render and 'high-poly' not in o.name),key=lambda o:len(o.data.vertices))
bpy.context.view_layer.update();target_bvh=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
# Match the sculpted scalp surface while retaining known source vertex IDs.
for i in np.flatnonzero(target[:,2]>1.715):
 p=Vector(target[i]);hit,n,_,_=target_bvh.find_nearest(p)
 if hit is not None and (hit-p).length<.020:target[i]=np.array(hit)

def frame(a,b,c):
 u=b-a;v=c-a;n=np.cross(u,v);n/=max(np.linalg.norm(n),1e-10)
 scale=math.sqrt(max(np.linalg.norm(u)*np.linalg.norm(v),1e-10))
 return np.stack([u,v,n*scale],axis=1),n

# Triangle transforms are shared by many nearby strand roots; cache once.
frames={};offset=0;bound=0;root_errors=[];fallback=0
head=source_vertices[:,2]>1.38
affine=np.linalg.lstsq(np.column_stack([source_vertices[head],np.ones(head.sum())]),target[head],rcond=None)[0]
for size in sizes:
 size=int(size);strand=xyz[offset:offset+size].copy();root=strand[0]
 hit,n,ti,d=source_bvh.find_nearest(Vector(root))
 if hit is None or d>.040:
  xyz[offset:offset+size]=np.column_stack([strand,np.ones(size)])@affine;fallback+=1;offset+=size;continue
 if ti not in frames:
  ids=triangles[ti];a,b,c=source_vertices[ids];aa,bb,cc=target[ids]
  sf,sn=frame(a,b,c);tf,tn=frame(aa,bb,cc)
  transfer=tf@np.linalg.pinv(sf)
  frames[ti]=(a,aa,transfer,tn)
 a,aa,transfer,tn=frames[ti]
 mapped=(strand-a)@transfer.T+aa
 # Keep the whole curve's groom shape after a small root clearance correction.
 p=Vector(mapped[0]);thit,normal,_,_=target_bvh.find_nearest(p)
 if thit is not None and (thit-p).length<.025:
  correction=np.array(thit+normal*.00045)-mapped[0]
  mapped+=correction;root_errors.append(float(np.linalg.norm(correction)))
 xyz[offset:offset+size]=mapped;bound+=1;offset+=size
 if bound%15000==0:print('STRANDS_BOUND',bound,flush=True)

haircol=bpy.data.collections['05_Hair']
for ob in list(haircol.objects):bpy.data.objects.remove(ob,do_unlink=True)
cu=bpy.data.hair_curves.new('Topology bound CC0 guide groom');cu.add_curves(sizes.tolist());cu.attributes['position'].data.foreach_set('vector',xyz.astype(np.float32).ravel());cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',radii.astype(np.float32))
mat=bpy.data.materials.new('Deep auburn physical hair');mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear();bs=nt.nodes.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='COLOR';bs.inputs['Roughness'].default_value=.40;bs.inputs['Radial Roughness'].default_value=.55
hi=nt.nodes.new('ShaderNodeHairInfo');r=nt.nodes.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(.007,.0011,.0013,1);r.color_ramp.elements[1].color=(.035,.005,.005,1);nt.links.new(hi.outputs['Random'],r.inputs[0]);nt.links.new(r.outputs[0],bs.inputs['Color']);out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(bs.outputs[0],out.inputs[0]);cu.materials.append(mat)
ob=bpy.data.objects.new('Triangle-frame fitted authored '+STYLE,cu);haircol.objects.link(ob)
scene=bpy.context.scene;scene.cycles.samples=96;scene.cycles.use_denoising=True
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles_curves.shape='THICK'
# Reuse protected source lights, with explicit front/side/back inspection cameras.
cam=scene.camera;cam.data.type='ORTHO'
for name,loc,target,scale in [('01_Front',(0,-4,1.76),(0,-.025,1.744),.51),('02_ThreeQuarter',(.8,-3,1.80),(0,-.025,1.744),.51),('03_Side',(4,-.025,1.76),(0,-.025,1.744),.51),('04_Back',(0,4,1.76),(0,-.025,1.744),.51)]:
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;scene.render.resolution_x=1050;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.filepath=str(RENDER/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Ember_Regent.blend'))
report={'version':VERSION,'source_scene':base,'groom_source':'https://files2.makehumancommunity.org/functional/haireditor.zip','groom_author':'Tomas Klecer','license':'CC0','style':STYLE,'groom_npz_sha256':hashlib.sha256(pack.read_bytes()).hexdigest(),'method':'identical scalp vertex correspondence and per triangle affine frame binding','bound_strands':bound,'fallback_strands':fallback,'median_root_correction_m':float(np.median(root_errors)),'status':'experimental method; prior candidates failed artistic review'}
(OUT/'groom_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('CORRESPONDENCE_GROOM_SAVED',VERSION,flush=True)
