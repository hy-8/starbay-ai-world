"""Explicitly author front-facing locks in the measured positive-X root area."""
import bpy, sys, re, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
fine_locks='--fine-locks' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
assert not out.exists() and not render.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
assert all(c.points_length==65 for c in cu.curves)
raw=p.reshape(-1,65,3).astype(float);q=raw.copy();r=raw[:,0]
eligible=np.flatnonzero((r[:,0]>.025)&(r[:,0]<.073)&(r[:,1]<-.065)&(r[:,1]>-.125)&(r[:,2]>1.830))
assert len(eligible)>200
root=r[eligible];K=30 if fine_locks else 10;centers=[root[len(root)//2]];best=np.full(len(root),np.inf)
for _ in range(1,K):
 best=np.minimum(best,np.sum((root-centers[-1])**2,axis=1));centers.append(root[np.argmax(best)])
centers=np.array(centers)
def assign():return np.argmin(np.maximum(0,(root*root).sum(axis=1)[:,None]+(centers*centers).sum(axis=1)[None]-2*root@centers.T),axis=1)
for _ in range(20):
 labels=assign()
 for k in range(K):
  if (labels==k).any():centers[k]=root[labels==k].mean(axis=0)
labels=assign();body=bpy.data.objects['CC0 male body • retained topology']
assert np.array_equal(np.array(body.matrix_world),np.eye(4));bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
t=np.linspace(0,1,65);u=t[:,None];mask=np.zeros(len(raw),bool);rows=[];repairs=0
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
for k in range(K):
 members=eligible[labels==k]
 if len(members)<30:continue
 roots=r[members];center=roots.mean(axis=0);phase=k*2.399963
 end=np.array([.031+.043*(.5+.5*np.sin(phase)),-.155-.012*np.cos(phase),1.774+.017*np.sin(phase*.71)])
 c1=center+np.array([.003,-.015,.008])
 c2=np.array([end[0]+.021,-.175,1.812+.014*np.cos(phase*.71)])
 guide=(1-u)**3*center+3*(1-u)**2*u*c1+3*(1-u)*u*u*c2+u**3*end
 guide[:,0]+=.0025*np.sin(2*np.pi*t+phase)*np.sin(np.pi*t)
 if fine_locks:
  end=np.array([.023+.061*(.5+.5*np.sin(phase)),-.153-.019*np.cos(phase),1.768+.023*np.sin(phase*.71)])
  c1=center+np.array([.001+.004*np.sin(phase),-.016,.005+.004*np.cos(phase)])
  c2=np.array([end[0]+.012*np.cos(phase),-.171,1.813+.020*np.cos(phase*.71)])
  guide=(1-u)**3*center+3*(1-u)**2*u*c1+3*(1-u)*u*u*c2+u**3*end
  guide[:,0]+=.005*np.sin(2*np.pi*t+phase)*np.sin(np.pi*t)
  guide[:,1]+=.002*np.cos(2*np.pi*t+phase)*np.sin(np.pi*t)
 values=guide[None]+(roots-center)[:,None]*(1-.86*smooth((t-.08)/.82))[None,:,None]
 # Distributed, tapered tips instead of every member ending on one line.
 for local,i in enumerate(members):
  fiberphase=i*2.399963
  values[local,:,2]+=.007*np.sin(fiberphase)*smooth((t-.45)/.55)
  values[local,:,0]+=.0008*np.sin(np.pi*t)*np.sin(2*np.pi*t+fiberphase)
  for j in range(1,65):
   hit,n,_,dist=bv.find_nearest(Vector(values[local,j]));gap=(Vector(values[local,j])-hit).dot(n)
   if dist<.025 and gap<.0005:values[local,j]+=np.array(n)*(.0007-gap);repairs+=1
 values[:,0]=roots;q[members]=values;mask[members]=True
 rows.append(dict(patch=k,fibers=len(members),guide_end_m=end.tolist(),max_displacement_m=float(np.linalg.norm(values-raw[members],axis=2).max())))
assert np.isfinite(q).all() and np.array_equal(q[:,0],raw[:,0]) and np.array_equal(q[~mask],raw[~mask])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_front_frame_sculpture';ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask)
out.mkdir(parents=True);render.mkdir(parents=True);s=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['02_ThreeQuarter','01_Front','03_Side']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'front_frame_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,changed_fibers=int(mask.sum()),eligible_fibers=len(eligible),target_patches=K,selection_attribute=attr,patches=rows,fine_locks=fine_locks,all_roots_exact=True,unselected_primary_exact=True,other_hair_unchanged=True,discrete_body_repairs=repairs,method=f'Camera-attributed positive-X/front root zone;{len(rows)} edited source-follicle patches from{K} target patches (groups below30 fibers remain unchanged), explicitly authored cubic foreground locks with varied tapered tip positions'+(';5mm lateral and2mm depth phase-staggered wave; broader length scatter' if fine_locks else '')+'. Existing hair topology/radii retained.',status='Actual drafts pending review',scope='Discrete real-body point checks only, not full segment/eye/clothing/animation collision or art acceptance'),indent=2),encoding='utf-8')
print('VISIBLE_FRONT_LOCKS_SAVED',version,int(mask.sum()),flush=True)
