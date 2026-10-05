"""Fit only licensed original Sintel particle paths to the concert hero.
Local evaluation, original/derived geometry retained locally. No bundle rig,
body, texture, hair-card or shader is adopted. Always use a fresh candidate.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version=a[0]
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh candidate required')
source=ROOT/'Exports/napeunderlay02/Ember_Regent.blend';cache=ROOT/'Source/SintelFilm/sintelcontrol02/original_particle_paths.npz'
raw=np.load(cache)['positions'];p=raw*np.array([1.0,1.0,1.0])+np.array([0,-.035,.215])
hybrid='--hybrid' in a
if hybrid:
 mask=p[:,0,1]>-.040
 raw=raw[mask];p=p[mask]
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
body=bpy.data.objects['CC0 male body • retained topology'];bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
mat=next(o for o in bpy.data.objects if not o.hide_render and o.type=='CURVES' and o.name.startswith('Authored')).data.materials[0]
hidden=[]
for ob in bpy.data.objects:
 if not ob.hide_render and (ob.type=='CURVES' or ob.name.startswith('Original nape underlay')) and not (hybrid and ob.name.startswith('Authored frontal revision')):
  ob.hide_render=True;ob.hide_set(True);hidden.append(ob.name)
corrections=[]
for i in range(len(p)):
 hit,normal,_,dist=bv.find_nearest(Vector(p[i,0]));delta=np.array(hit+normal*.0004)-p[i,0]
 p[i]+=delta[None];corrections.append(float(np.linalg.norm(delta)))
N=p.shape[1];t=np.linspace(0,1,N)
if '--layered' in a:
 original_parents=np.load(cache)['positions'][:228]
 kd=KDTree(228)
 for k,q in enumerate(original_parents):kd.insert(Vector(q[0]),k)
 kd.balance()
 # Cut the source's long facial curtain to eyebrow height; preserve root and
 # physical source flow, use smooth regional blend rather than new clumps.
 for i,q in enumerate(p):
  root=q[0];end=q[-1];f=1.
  _,group,_=kd.find(Vector(raw[i,0]));variation=(np.sin(group*12.9898)*43758.5453)%1
  if root[1]<-.052 and end[1]<-.09 and end[2]<1.788:
   j=np.flatnonzero(q[:,2]<1.785)
   if len(j):f=max(.42,(j[0]-1)/(N-1))
  rear=root[1]>-.045
  if rear and root[2]>1.79:f=min(f,.58+.28*variation)
  if hybrid and root[2]>1.805:
   tipheight=(1.786 if root[2]>1.83 else 1.741)+.020*variation
   j=np.flatnonzero(q[:,2]<tipheight)
   if len(j):f=min(f,max(.34,(j[0]-1)/(N-1)))
  if f<1:q=np.stack([np.interp(t*f,t,q[:,k]) for k in range(3)],axis=1)
  if rear:
   radial=np.array([root[0],max(.018,root[1]+.045),0.]);radial/=np.linalg.norm(radial)
   exit=np.clip((t-.55)/.45,0,1);exit=exit*exit*(3-2*exit)
   q+=radial[None]*exit[:,None]*(.006+.008*variation)
   # Source locks retain their own shape; lower roots get longer neck tails.
   if root[2]<1.77:q[:,2]-=(.045 if hybrid else .028)*t**1.7
  p[i]=q
# Guard actual sampled head/body points, excluding new follicle origins.
repairs=0;maxrepair=0.
for i in range(len(p)):
 for j in range(1,N):
  hit,normal,_,dist=bv.find_nearest(Vector(p[i,j]));gap=(Vector(p[i,j])-hit).dot(normal)
  if dist<.018 and gap<.00025:
   amount=.00035-gap;p[i,j]+=np.array(normal)*amount;repairs+=1;maxrepair=max(maxrepair,amount)
p=p.astype(np.float32)
cu=bpy.data.hair_curves.new('Sintel original film hair • fitted local study');cu.add_curves([N]*len(p));cu.attributes['position'].data.foreach_set('vector',p.ravel())
r=np.broadcast_to(.000045*(1-.997*t**2.5)**.7,(len(p),N)).astype(np.float32);cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',r.ravel());cu.materials.append(mat)
ob=bpy.data.objects.new('Sintel CC BY3.0 • original particle-derived fitted groom',cu);bpy.context.scene.collection.objects.link(ob)
ob['attribution']='Sintel Blender Foundation/Durian, Sintel Lite BenDansie CC BY3.0; source container Scthe unity-hair. Modified head fit, red material and optional facial cut.'
out.mkdir(parents=True);render.mkdir(parents=True)
report=dict(source='napeunderlay02',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),cache_sha256=hashlib.sha256(cache.read_bytes()).hexdigest(),method='Original source particle flow translated, each actual follicle projected to target body and complete strand moved with its root; discrete head guard',translation_m=[0,-.035,.215],curves=len(p),points_per_curve=N,hidden_old_objects=hidden,root_correction_quantiles_m=np.quantile(corrections,[0,.5,.9,1]).tolist(),guard_repairs=repairs,maximum_guard_repair_m=maxrepair,layered_cut='--layered' in a,original_front_retained=hybrid,status='Unreviewed local native 3D study; not acceptance',guard_scope='Discrete fiber point nearest-body checks only; not segment, garment or motion validation')
(out/'sintel_fit_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=64;s.cycles.use_denoising=False;s.render.resolution_x=1200;s.render.resolution_y=1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['02_ThreeQuarter','03_Side','04_Back']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('SINTEL_FIT_RENDERED',version,flush=True)
