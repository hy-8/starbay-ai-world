"""Split broad existing native frontal locks into shallow coherent sublayers.

No new whole-head template or added strands. Bystedt CC BY-SA derivative stays
local. Preserves actual roots and primary flow; representative samples first.
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
if out.exists() or render.exists():raise RuntimeError('Fresh separation sample required')
source=ROOT/'Exports/nativecoverage05/Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
assert all(c.points_length==65 for c in cu.curves)
q=p.reshape(-1,65,3).astype(float);original=q.copy();root=q[:,0];tip=q[:,-1]
eligible=(tip[:,1]<-.145)&(tip[:,2]<1.81)&(root[:,2]>1.81)&(root[:,1]<-.055)
ids=np.flatnonzero(eligible)
labels,inverse=np.unique(np.round(tip[ids]/.003).astype(int),axis=0,return_inverse=True)
counts=np.bincount(inverse);groups=[]
for label,count in enumerate(counts):
 if count<100:continue
 members=ids[inverse==label]
 groups.append((label,members))
sample='--two-groups' in a
if sample:
 groups=sorted([row for row in groups if q[row[1],-1,0].mean()>.0],key=lambda row:len(row[1]),reverse=True)[:2]
assert groups,'No broad frontal native locks detected'
body=bpy.data.objects['CC0 male body • retained topology'];assert np.allclose(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
t=np.linspace(0,1,65);rise=np.clip((t-.16)/.84,0,1);rise=rise*rise*(3-2*rise);rows=[];guards=0
for label,members in groups:
 center=q[members].mean(axis=0);tangent=np.gradient(center,axis=0)
 tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-10)
 radial=center-np.array([0,-.045,1.771]);normal=radial-tangent*np.sum(radial*tangent,axis=1)[:,None]
 normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-10)
 across=np.cross(tangent,normal);across/=np.maximum(np.linalg.norm(across,axis=1)[:,None],1e-10)
 # True roots determine subordinate layers, so nearby fibers move together.
 coordinate=q[members,0]@across[0]
 lo,hi=np.quantile(coordinate,[.02,.98]);v=np.clip((coordinate-lo)/max(hi-lo,1e-8),0,.99999)
 layer=np.floor(v*3).astype(int)-1
 phase=float(center[0,0]*37+center[0,1]*23)
 for k,index in enumerate(members):
  level=layer[k];fine=(v[k]*3-np.floor(v[k]*3))-.5
  lateral=(.0023*level*np.sin(t*np.pi*1.15)+.0010*level*t**2)*rise
  depth=(.0025*level*np.sin(t*np.pi*.85+phase)+.0012*fine)*rise
  q[index]+=across*lateral[:,None]+normal*depth[:,None]
  for j in range(1,65):
   if q[index,j,2]<1.795:continue
   hit,n,_,dist=bv.find_nearest(Vector(q[index,j]));gap=(Vector(q[index,j])-hit).dot(n)
   if dist<.02 and gap<.0004:q[index,j]=np.array(hit+n*.0005);guards+=1
 rows.append(dict(fibers=len(members),sub_layer_counts=np.bincount(layer+1,minlength=3).tolist(),
  root_width_quantile_m=float(hi-lo),max_displacement_m=float(np.linalg.norm(q[members]-original[members],axis=2).max())))
assert np.array_equal(q[:,0],original[:,0])
assert np.isfinite(q).all()
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
out.mkdir(parents=True);render.mkdir(parents=True)
(out/'sublayer_manifest.json').write_text(json.dumps(dict(source='nativecoverage05',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
 author='Daniel Bystedt',license='CC BY-SA; version unspecified',two_group_sample=sample,groups=rows,
 method='Existing full native shafts grouped by free endpoint proximity, subordinate coherent depth layers from actual root coordinate; no strands added',
 original_roots_unchanged=True,discrete_body_guard_events=guards,geometry_finite=True,
 status='Unreviewed actual shape study',scope='Root unchanged and discrete body points only; not complete segment/clothing/animation proof'),indent=2),encoding='utf-8')
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in (['02_ThreeQuarter'] if sample else ['01_Front','02_ThreeQuarter','03_Side','04_Back']):
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('NATIVE_FRINGE_SUBLAYERS_SAVED',version,len(groups),flush=True)
