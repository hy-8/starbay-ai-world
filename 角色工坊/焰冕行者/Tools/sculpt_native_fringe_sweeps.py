"""Resculpt the visible fringe, including the old61 foreground, in native3D."""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
keep_terminal_heights='--keep-terminal-heights' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
out,renders=ROOT/'Exports'/version,ROOT/'Renders'/version
assert not out.exists() and not renders.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float);q=raw.copy();r=raw[:,0]
frame=np.empty(len(raw),bool);cu.attributes['native_front_frame_sculpture'].data.foreach_get('value',frame)
other=(~frame)&(r[:,0]<-.004)&(r[:,1]<-.065)&(r[:,2]>1.830)&(raw[:,-1,1]<-.13)&(raw[:,-1,2]>1.730)
eligible=np.flatnonzero(frame|other)
features=(raw[eligible][:,[0,8,24,40,64]]*np.array([.5,.6,.8,1,1])[None,:,None]).reshape(len(eligible),-1)
K=54;centers=[features[len(features)//2]];best=np.full(len(features),np.inf)
for _ in range(1,K):
 best=np.minimum(best,np.sum((features-centers[-1])**2,axis=1));centers.append(features[np.argmax(best)])
centers=np.array(centers)
def assign():return np.argmin(np.maximum(0,(features*features).sum(1)[:,None]+(centers*centers).sum(1)[None]-2*features@centers.T),axis=1)
for _ in range(24):
 labels=assign()
 for k in range(K):
  if (labels==k).any():centers[k]=features[labels==k].mean(0)
labels=assign()
body=bpy.data.objects['CC0 male body • retained topology'];assert np.array_equal(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
t=np.linspace(0,1,65);mask=np.zeros(len(raw),bool);rows=[];repairs=0
def smooth(x):
 x=np.clip(x,0,1);return x*x*(3-2*x)
env=smooth((t-.04)/.16)*(1-smooth((t-.80)/.20))
for k in range(K):
 ids=eligible[labels==k]
 if len(ids)<30:continue
 old=raw[ids];c=old.mean(0);tangent=np.gradient(c,axis=0)
 tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
 _,nn,_,_=bv.find_nearest(Vector(c[0]));normal=np.array(nn)
 across=np.zeros_like(tangent);prev=np.cross(normal,tangent[0]);prev/=max(np.linalg.norm(prev),1e-9)
 for j in range(65):
  prev-=tangent[j]*np.dot(prev,tangent[j]);prev/=max(np.linalg.norm(prev),1e-9);across[j]=prev
 phase=k*2.399963;direction=-1. if c[0,0]>.002 else .65
 # A broad crossing bend, then a gentle reverse before the tapered tip.
 sweep=(.009+.005*(.5+.5*np.sin(phase)))*direction
 lateral=sweep*np.sin(np.pi*t)*env
 lateral+=.004*np.cos(phase)*smooth((t-.58)/.42)
 terminal_raise=.005+.018*(.5+.5*np.cos(phase*.71))
 if keep_terminal_heights:terminal_raise=0.
 vertical=.004*np.sin(np.pi*t)*env+terminal_raise*smooth((t-.38)/.62)
 guide=c.copy();guide[:,0]+=lateral;guide[:,1]-=.0025*np.sin(np.pi*t)*env;guide[:,2]+=vertical
 delta=old-c[None];width=np.sum(delta*across[None],axis=2)
 values=old-across[None]*(width*.40*env[None])[:,:,None]+(guide-c)[None]
 for i in range(len(ids)):
  for j in range(1,65):
   hit,n,_,dist=bv.find_nearest(Vector(values[i,j]));gap=(Vector(values[i,j])-hit).dot(n)
   if dist<.025 and gap<.0005:
    values[i,j]+=np.array(n)*(.0007-gap);repairs+=1
 values[:,0]=old[:,0];q[ids]=values;mask[ids]=True
 rows.append(dict(group=k,fibers=len(ids),old61_fibers=int(frame[ids].sum()),sweep_m=sweep,terminal_raise_m=terminal_raise,
  maximum_displacement_m=float(np.linalg.norm(values-old,axis=2).max())))
assert mask.sum()>100 and np.isfinite(q).all()
assert np.array_equal(q[:,0],raw[:,0]) and np.array_equal(q[~mask],raw[~mask])
assert (q[:,-1,2]<1.640).sum()==0
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_resculpted_fringe_sweeps';ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
out.mkdir(parents=True);renders.mkdir(parents=True);s=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for shot in ['02_ThreeQuarter','01_Front','05_OppositeSide']:
 s.camera=bpy.data.objects[shot];s.render.filepath=str(renders/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'fringe_sweep_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,selection_attribute=attr,
 eligible_fibers=len(eligible),changed_fibers=int(mask.sum()),changed_old61_fibers=int((mask&frame).sum()),groups=rows,
 unchanged_old61_fibers=int((~mask&frame).sum()),discrete_body_repairs=repairs,minimum_primary_tip_z_m=float(q[:,-1,2].min()),primary_tips_below_1_640m=0,
 keep_terminal_heights=keep_terminal_heights,
 method='Explicitly permit resculpting old61 foreground.54 current whole-path groups usingpoints0/8/24/40/64 weights.5/.6/.8/1/1; select old61 plus real negativeX/frontward-ended fringe, minimum30 fibers. Cross-face9-14mm broad bend with4mm phase-varied terminal reversal,'+('zero terminal lift (discrete body correction may still move a tip)' if keep_terminal_heights else '5-23mm terminal lift')+' and40% transverse contraction. True roots/topology/radii/unselected hair/materials unchanged.',
 status='Actual drafts pending artistic review, no eye/body continuous collision or artistic acceptance.'),indent=2),encoding='utf-8')
print('FRINGE_SWEEPS_SCULPTED',version,int(mask.sum()),int((mask&frame).sum()),flush=True)
