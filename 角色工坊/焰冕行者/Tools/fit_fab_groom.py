"""Local non-generative scalp fitting of licensed Fab groom to the real hero.

Each existing strand retains its source flow; fresh candidate, original intact.
Licensed source/derived geometry must not be published as standalone assets.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version=a[0]
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh candidate required')
source=ROOT/'Exports/napeunderlay02/Ember_Regent.blend'
folder=ROOT/'Source/FabMediumLayered/fabcontrol01';cache=folder/'licensed_particle_paths.npz'
raw=np.load(cache)['positions'];groups=json.loads((folder/'bake_manifest.json').read_text())['groups']
scale=np.array([1.05,1.20,1.0]) if '--measured-affine' in a else np.ones(3)
translation=np.array([0,-.054,1.797]) if '--measured-affine' in a else np.array([0,-.025,1.785])
p=raw*scale+translation;N=p.shape[1];t=np.linspace(0,1,N)
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
body=bpy.data.objects['CC0 male body • retained topology'];bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
mat=next(o for o in bpy.data.objects if not o.hide_render and o.type=='CURVES' and o.name.startswith('Authored')).data.materials[0]
if '--source-response' in a:
 with bpy.data.libraries.load(str(ROOT/'Source/FabMediumLayered/hairstyle.blend'),link=False) as (src,dst):
  dst.materials=['Hair']
 mat=dst.materials[0].copy();mat.name='Fab original directional hair shader • burgundy tint'
 ramp=mat.node_tree.nodes['Color Ramp'].color_ramp
 ramp.elements[0].color=(.040,.0018,.003,1);ramp.elements[1].color=(.120,.008,.015,1)
hybrid='--hybrid' in a;hidden=[]
for ob in bpy.data.objects:
 retain=hybrid and ob.name.startswith('Authored frontal revision')
 if '--retain-support' in a and ob.name.startswith(('Abhay flow derivative','Bystedt derivative','Original posterior coverage')):retain=True
 if not ob.hide_render and (ob.type=='CURVES' or ob.name.startswith('Original nape underlay')) and not retain:
  ob.hide_render=True;ob.hide_set(True);hidden.append(ob.name)
corrections=[]
for i in range(len(p)):
 hit,normal,_,dist=bv.find_nearest(Vector(p[i,0]));delta=np.array(hit+normal*.0004)-p[i,0]
 p[i]+=delta[None];corrections.append(float(np.linalg.norm(delta)))
if '--longback' in a:
 for group in groups:
  factor={'Curves-Back':3.0,'Curves-Sides':2.6,'Curves-Front':1.0}[group['name']]
  # Extend the actual short existing strand's own curved trajectory. Roots
  # remain attached; no unrelated authored template is substituted.
  indices=np.arange(*group['range']);roots=p[indices,0].copy()
  p[indices]=roots[:,None]+(p[indices]-roots[:,None])*factor
# Retain complete authored source shape in the first study. Later regional
# edits change only existing strands, never synthesize from a generative model.
if '--layered' in a:
 for i,q in enumerate(p):
  root=q[0];tip=q[-1]
  # Small length variance is tied to neighboring source roots, not every fiber.
  groupkey=np.floor(raw[i,0]/.009)
  variation=(np.sin(np.dot(groupkey,[12.9898,78.233,19.131]))*43758.5453)%1
  back=root[1]>-.015
  if back and root[2]>1.795:
   factor=.74+.23*variation
   q=np.stack([np.interp(t*factor,t,q[:,k]) for k in range(3)],axis=1)
  # Existing lower-back hairs extend to collar depth; higher tiers stay shorter.
  if back and root[2]<1.78:
   weight=np.clip((1.78-root[2])/.05,0,1)
   q[:,2]-=.035*weight*t**1.7
   q[:,1]+=.006*weight*t**2
  p[i]=q
repairs=0;maxrepair=0.
for i in range(len(p)):
 for j in range(1,N):
  hit,normal,_,dist=bv.find_nearest(Vector(p[i,j]));gap=(Vector(p[i,j])-hit).dot(normal)
  if dist<.020 and gap<.00025:
   amount=.00035-gap;p[i,j]+=np.array(normal)*amount;repairs+=1;maxrepair=max(maxrepair,amount)
p=p.astype(np.float32);out.mkdir(parents=True);render.mkdir(parents=True)
kept=[]
for group in groups:
 indices=np.arange(*group['range'])
 if hybrid:
  threshold=-.065 if '--retain-support' in a and group['name']=='Curves-Sides' else -.035
  indices=indices[p[indices,0,1]>threshold]
 q=p[indices]
 if not len(q):continue
 cu=bpy.data.hair_curves.new('Fab licensed '+group['name']);cu.add_curves([N]*len(q));cu.attributes['position'].data.foreach_set('vector',q.ravel())
 radius=.000055 if '--longback' in a else .000045
 r=np.broadcast_to(radius*(1-.996*t**2.4)**.75,(len(q),N)).astype(np.float32)
 cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',r.ravel());cu.materials.append(mat)
 ob=bpy.data.objects.new('Muzammil Fab Standard • '+group['name'],cu);bpy.context.scene.collection.objects.link(ob)
 ob['license']='Fab Standard, NoAI. Muzammil Free Medium Layered HairStyle. Existing content transformed locally; no generative input. Standalone redistribution prohibited.'
 kept.append(dict(object=ob.name,curves=len(q)))
report=dict(source='napeunderlay02',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),cache_sha256=hashlib.sha256(cache.read_bytes()).hexdigest(),
 method='Existing licensed particle paths, original flow retained. Each root projected to evaluated target body; full strand translated; discrete point guard.',
 affine_translation_m=translation.tolist(),affine_scale=scale.tolist(),root_correction_quantiles_m=np.quantile(corrections,[0,.5,.9,.99,1]).tolist(),
 point_guard_repairs=repairs,maximum_guard_repair_m=maxrepair,components=kept,old_hidden_objects=hidden,
 layered_cut='--layered' in a,retained_original_front=hybrid,retained_existing_short_support='--retain-support' in a,
 existing_side_back_length_scale=[3.0,2.6] if '--longback' in a else [1.0,1.0],
 source_directional_shader_red_tint='--source-response' in a,
 collision_scope='Discrete hair points nearest body only; not complete segments, clothes, eyes or animation',status='Unreviewed real 3D candidate')
(out/'fab_fit_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=64;s.cycles.use_denoising=False;s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in (['02_ThreeQuarter'] if '--single-view' in a else ['02_ThreeQuarter','03_Side','04_Back']):
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('FAB_FITTED_RENDERED',version,flush=True)
