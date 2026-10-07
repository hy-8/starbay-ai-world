"""Explicit full-length side locks instead of keeping the source's flat entry fan."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
tiered='--tiered' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:2])
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version;assert not out.exists() and not render.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());raw=p.reshape(-1,65,3).astype(float);q=raw.copy();r=raw[:,0]
frame=np.empty(len(raw),bool);cu.attributes['native_front_frame_sculpture'].data.foreach_get('value',frame)
eligible=np.flatnonzero((~frame)&(r[:,0]>.003)&(r[:,0]<.105)&(r[:,2]>1.805)&(r[:,1]<.060))
root=r[eligible];K=80;centers=[root[len(root)//2]];best=np.full(len(root),np.inf)
for _ in range(1,K):best=np.minimum(best,np.sum((root-centers[-1])**2,axis=1));centers.append(root[np.argmax(best)])
centers=np.array(centers)
def assign():return np.argmin(np.maximum(0,(root*root).sum(axis=1)[:,None]+(centers*centers).sum(axis=1)[None]-2*root@centers.T),axis=1)
for _ in range(24):
 labels=assign()
 for k in range(K):
  if (labels==k).any():centers[k]=root[labels==k].mean(axis=0)
labels=assign();body=bpy.data.objects['CC0 male body • retained topology'];assert np.array_equal(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get());t=np.linspace(0,1,65);u=t[:,None];mask=np.zeros(len(raw),bool);rows=[];repairs=0
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
for k in range(K):
 ids=eligible[labels==k]
 if len(ids)<30:continue
 roots=r[ids];center=roots.mean(axis=0);phase=float(k*2.399963)
 _,n,_,_=bv.find_nearest(Vector(center));normal=np.array(n)
 # Root position influences target depth so neighboring forward/back regions
 # stay ordered. Independent phases vary the curl and terminal height.
 end=np.array([.092+.012*np.sin(phase),center[1]+.024+.016*np.sin(phase*.71),1.748+.035*(.5+.5*np.cos(phase*.71))])
 heading=np.array([.4,-.4,-.65]);heading-=normal*np.dot(heading,normal);heading/=max(np.linalg.norm(heading),1e-9)
 c1=center+heading*.022+normal*(.005+.003*np.sin(phase)**2)
 c2=np.array([.111+.008*np.cos(phase),center[1]-.027-.016*np.cos(phase),1.821+.016*np.sin(phase*.71)])
 if tiered:
  height=float(np.clip((center[2]-1.815)/.060,0,1))
  # Shorter high-root canopy locks terminate on the upper side; lower locks
  # fall farther. This separates tiers instead of80 parallel same-length ribs.
  end=np.array([.100-.024*height+.012*np.sin(phase),center[1]+.012+.024*np.cos(phase*.71),1.740+.065*height+.018*np.sin(phase*.71)])
  c2=np.array([max(center[0]+.026,end[0]+.025+.008*np.cos(phase)),center[1]-.023-.016*np.cos(phase),max(end[2]+.020,center[2]-.026+.012*np.sin(phase))])
 guide=(1-u)**3*center+3*(1-u)**2*u*c1+3*(1-u)*u*u*c2+u**3*end
 guide[:,0]+=.004*np.sin(2*np.pi*t+phase)*np.sin(np.pi*t)
 guide[:,1]+=.005*np.sin(2*np.pi*t+phase*.7)*np.sin(np.pi*t)
 values=guide[None]+(roots-center)[:,None]*(1-.84*smooth((t-.06)/.84))[None,:,None]
 for local,i in enumerate(ids):
  phi=float(i*2.399963)
  values[local,:,2]+=.006*np.sin(phi)*smooth((t-.55)/.45)
  values[local,:,0]+=.0006*np.sin(2*np.pi*t+phi)*np.sin(np.pi*t)
  for j in range(1,65):
   hit,n,_,dist=bv.find_nearest(Vector(values[local,j]));gap=(Vector(values[local,j])-hit).dot(n)
   if dist<.030 and gap<.0005:values[local,j]+=np.array(n)*(.0007-gap);repairs+=1
 values[:,0]=roots;q[ids]=values;mask[ids]=True
 rows.append(dict(patch=int(k),fibers=len(ids),end_m=end.tolist(),max_displacement_m=float(np.linalg.norm(values-raw[ids],axis=2).max())))
assert mask.sum()>100 and np.isfinite(q).all() and np.array_equal(q[:,0],raw[:,0]) and np.array_equal(q[frame],raw[frame]) and np.array_equal(q[~mask],raw[~mask])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel());ob.data.update_tag()
attr='native_relaxed_side_locks';ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask)
out.mkdir(parents=True);render.mkdir(parents=True);s=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for name in ['02_ThreeQuarter','05_OppositeSide','01_Front']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'side_lock_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,eligible_fibers=len(eligible),target_patches=K,edited_patches=len(rows),changed_fibers=int(mask.sum()),selection_attribute=attr,patches=rows,tiered=tiered,all_roots_exact=True,explicit_foreground_exact=True,unselected_primary_exact=True,other_hair_exact=True,discrete_body_repairs=repairs,method='Whole positive-X upper primary sides excluding explicit foreground61.80 real follicle patches, minimum30 shafts; new scalp-tangent cubic departure, '+('root-height dependent upper short canopy/lower long sides; height/phase staggered terminals and middle controls' if tiered else 'full-length side curls/end heights1.748-1.783m before individual scatter')+',4/5mm phased bends, tapered root scatter. True follicles retained; old first4 allowed to change. Materials/lights unchanged.',status='Actual drafts pending review; no artistic or continuous collision acceptance'),indent=2),encoding='utf-8')
print('RELAXED_SIDE_LOCKS_SAVED',version,int(mask.sum()),len(rows),flush=True)
