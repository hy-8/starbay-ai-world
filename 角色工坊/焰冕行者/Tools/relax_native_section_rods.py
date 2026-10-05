"""Quasi-static discrete rod study on measured native lock centerlines.

This is a still groom shaping solver, not rigging or runtime hair simulation.
Retains actual fibers/roots and transfers continuous centerline displacements.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version=a[0];sample='--sample' in a
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh rod study required')
source=ROOT/'Exports/nativecoverage05/Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
assert all(c.points_length==65 for c in cu.curves)
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float);q=raw.copy();root=raw[:,0];tip=raw[:,-1]
ids=np.flatnonzero((tip[:,1]<-.14)&(tip[:,2]<1.81)&(root[:,2]>1.81)&(root[:,1]<-.035))
labels,inv=np.unique(np.round(tip[ids]/.007).astype(int),axis=0,return_inverse=True)
counts=np.bincount(inv);groups=[ids[inv==k] for k in np.argsort(counts)[::-1] if counts[k]>=100]
if sample:groups=groups[:6]
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
t=np.linspace(0,1,65);rows=[];total_contacts=0
for members in groups:
 old=raw[members];center=np.mean(old,axis=0);v=center.copy()
 rest=np.linalg.norm(np.diff(center,axis=0),axis=1)
 # Residual native curl is carried as a bending rest shape, with reduced arch.
 curvature=(center[:-2]-2*center[1:-1]+center[2:])*.35
 contacts=0
 for iteration in range(360):
  # Modest gravity load, reduced near follicles. Length projection follows.
  v[1:,2]-=.000028*(t[1:]**.65)
  for k in range(8):
   d=v[1:]-v[:-1];l=np.maximum(np.linalg.norm(d,axis=1),1e-9)
   correction=d*((l-rest)/l*.49)[:,None]
   v[:-1]+=correction;v[1:]-=correction;v[0]=center[0]
   bend=v[:-2]-2*v[1:-1]+v[2:]-curvature
   v[1:-1]+=bend*.18
   v[0]=center[0]
  if iteration%4==0:
   for j in range(1,65):
    if v[j,2]<1.80:continue
    hit,n,_,dist=bv.find_nearest(Vector(v[j]));gap=(Vector(v[j])-hit).dot(n)
    if dist<.025 and gap<.002:
     delta=np.array(n)*(.002-gap);contacts+=1
     for k in range(max(1,j-2),min(65,j+3)):v[k]+=delta*np.exp(-.5*((k-j)/1.3)**2)
   v[0]=center[0]
 # Preserve the original microscale variation and original scalp follicles.
 shift=v-center;shift[0]=0
 q[members]=old+shift[None]
 # Correct individual surface contact smoothly after centerline transfer.
 for index in members:
  for _ in range(2):
   correction=np.zeros((65,3))
   for j in range(1,64):
    if q[index,j,2]<1.80:continue
    hit,n,_,dist=bv.find_nearest(Vector(q[index,j]));gap=(Vector(q[index,j])-hit).dot(n)
    if dist<.02 and gap<.0005:
     delta=np.array(n)*(.0007-gap);contacts+=1
     for k in range(max(1,j-2),min(65,j+3)):correction[k]+=delta*np.exp(-.5*((k-j)/1.3)**2)
   q[index]+=correction
  q[index,0]=raw[index,0]
 original_length=np.linalg.norm(np.diff(old,axis=1),axis=2).sum(1)
 final_length=np.linalg.norm(np.diff(q[members],axis=1),axis=2).sum(1)
 rows.append(dict(fibers=len(members),max_displacement_m=float(np.linalg.norm(q[members]-old,axis=2).max()),
  original_center_arc_m=float(rest.sum()),relaxed_center_arc_m=float(np.linalg.norm(np.diff(v,axis=0),axis=1).sum()),
  final_fiber_length_ratio_quantiles=np.quantile(final_length/original_length,[0,.5,.9,1]).tolist(),
  discrete_contact_events=contacts));total_contacts+=contacts
assert np.array_equal(q[:,0],raw[:,0]) and np.isfinite(q).all()
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
out.mkdir(parents=True);render.mkdir(parents=True)
report=dict(source='nativecoverage05',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
 author='Daniel Bystedt',license='CC BY-SA; version unspecified',representative_sample=sample,
 sections=rows,all_original_roots_unchanged=True,support_geometry_unchanged=True,
 method='360-step quasi-static centerline rod study, segment-length and reduced-rest-curvature projection with scalp contact; transfer displacements onto original native shafts',
 approximate_solver=True,runtime_simulation=False,status='Unreviewed actual shape study',
 scope='Centerline segment lengths approximate, individual native lengths not constrained; discrete body points only, not full collision/art acceptance')
(out/'rod_relax_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in (['02_ThreeQuarter'] if sample else ['01_Front','02_ThreeQuarter','03_Side','04_Back']):
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('NATIVE_SECTION_RODS_SAVED',version,len(groups),flush=True)
