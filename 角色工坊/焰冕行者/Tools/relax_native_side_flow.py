"""Replace repetitive side center waves with fitted broad falling cubic guides."""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
whole_side='--whole-side' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
out,renders=ROOT/'Exports'/version,ROOT/'Renders'/version
assert not out.exists() and not renders.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float);q=raw.copy();r=raw[:,0]
frame=np.empty(len(raw),bool);cu.attributes['native_front_frame_sculpture'].data.foreach_get('value',frame)
fringe=np.empty(len(raw),bool);cu.attributes['native_resculpted_fringe_sweeps'].data.foreach_get('value',fringe)
eligible=np.flatnonzero((~frame)&(~fringe)&(r[:,0]>.045)&(r[:,1]>-.065)&(r[:,2]>1.805)&(raw[:,-1,2]>1.700))
if whole_side:
 side=np.empty(len(raw),bool);cu.attributes['native_relaxed_side_locks'].data.foreach_get('value',side)
 eligible=np.flatnonzero(side&(~frame)&(~fringe)&(r[:,2]>1.805)&(raw[:,-1,2]>1.700))
features=(raw[eligible][:,[0,8,24,40,64]]*np.array([.5,.7,1,1,.7])[None,:,None]).reshape(len(eligible),-1)
K=100 if whole_side else 64;centers=[features[len(features)//2]];best=np.full(len(features),np.inf)
for _ in range(1,K):
 best=np.minimum(best,np.sum((features-centers[-1])**2,axis=1));centers.append(features[np.argmax(best)])
centers=np.array(centers)
def assign():return np.argmin(np.maximum(0,(features*features).sum(1)[:,None]+(centers*centers).sum(1)[None]-2*features@centers.T),axis=1)
for _ in range(24):
 labels=assign()
 for k in range(K):
  if (labels==k).any():centers[k]=features[labels==k].mean(0)
labels=assign();body=bpy.data.objects['CC0 male body • retained topology']
assert np.array_equal(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
mask=np.zeros(len(raw),bool);rows=[];repairs=0;t=np.linspace(0,1,65)
def smooth(x):
 x=np.clip(x,0,1);return x*x*(3-2*x)
for k in range(K):
 ids=eligible[labels==k]
 if len(ids)<30:continue
 old=raw[ids];c=old.mean(0)
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(c,axis=0),axis=1))]
 u=arc/max(arc[-1],1e-9);u=u[:,None]
 p0,p3=c[0],c[-1]
 A=np.column_stack([3*(1-u[:,0])**2*u[:,0],3*(1-u[:,0])*u[:,0]**2])
 B=c-(1-u)**3*p0-u**3*p3
 controls=np.linalg.lstsq(A[1:-1],B[1:-1],rcond=None)[0]
 c1,c2=controls
 phi=k*2.399963
 # Preserve distinct source direction; soften inherited repeated oscillation.
 c2=c2.copy();c2[2]-=.006+.007*(.5+.5*np.sin(phi))
 end=p3.copy();end[2]-=.004+.009*(.5+.5*np.cos(phi*.71));end[1]+=.006*np.sin(phi*.53)
 guide=(1-u)**3*p0+3*(1-u)**2*u*c1+3*(1-u)*u*u*c2+u**3*end
 # Root transition is retained; interior/tips relax toward the broad cubic.
 blend=.80*smooth(t/.18)
 values=old+(guide-c)[None]*blend[None,:,None]
 for i in range(len(ids)):
  for j in range(1,65):
   if blend[j]<.001:continue
   hit,n,_,dist=bv.find_nearest(Vector(values[i,j]));gap=(Vector(values[i,j])-hit).dot(n)
   if dist<.03 and gap<.0005:
    values[i,j]+=np.array(n)*(.0007-gap);repairs+=1
 values[:,0]=old[:,0];q[ids]=values;mask[ids]=True
 def turn(path):
  d=np.diff(path,axis=0);d/=np.maximum(np.linalg.norm(d,axis=1)[:,None],1e-9)
  return float(np.degrees(np.arccos(np.clip(np.sum(d[:-1]*d[1:],axis=1),-1,1))).sum())
 rows.append(dict(group=k,fibers=len(ids),source_guide_turn_deg=turn(c),candidate_guide_turn_deg=turn(values.mean(0)),
  guide_rms_fit_m=float(np.sqrt(np.mean(np.sum((guide-c)**2,axis=1)))),
  maximum_displacement_m=float(np.linalg.norm(values-old,axis=2).max())))
assert mask.sum()>100 and np.isfinite(q).all()
assert np.array_equal(q[:,0],raw[:,0]) and np.array_equal(q[~mask],raw[~mask])
assert np.array_equal(q[frame|fringe],raw[frame|fringe]) and (q[:,-1,2]<1.640).sum()==0
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_fitted_side_flow';ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
out.mkdir(parents=True);renders.mkdir(parents=True);s=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for shot in ['02_ThreeQuarter','03_Side','05_OppositeSide']:
 s.camera=bpy.data.objects[shot];s.render.filepath=str(renders/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'side_flow_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,selection_attribute=attr,
 eligible_fibers=len(eligible),changed_fibers=int(mask.sum()),edited_groups=len(rows),groups=rows,discrete_body_repairs=repairs,
 whole_side=whole_side,eligible_root_xyz_quantiles_m=np.quantile(r[eligible],[0,.5,1],axis=0).tolist(),
 method=('100 actual path groups over entire native_relaxed_side_locks source region' if whole_side else '64 actual root-to-tip path groups in positiveX side withrootX>45mm')+', excluding all old61/new106 fringe and tips below1.700m. Arc-parameter least-squares broad cubic source center guides,6-13mm middle-control drop,4-13mm end drop/6mm depth scatter,80% center-flow relaxation with retained roots and within-lock source section. Materials/lights unchanged.',
 status='Actual drafts pending artistic review; curve-turn statistics not completion acceptance.'),indent=2),encoding='utf-8')
print('SIDE_FLOW_RELAXED',version,int(mask.sum()),len(rows),flush=True)
