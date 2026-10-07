"""Small continuous lifted crown locks on the existing saved groom.

Root attachment, explicit foreground61, nape68 endpoints and body are retained.
This is actual local geometry design; static body-point guards are not dynamics.
"""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version;assert not out.exists() and not render.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());raw=p.reshape(-1,65,3).astype(float);q=raw.copy()
frame=np.empty(len(raw),bool);cu.attributes['native_front_frame_sculpture'].data.foreach_get('value',frame)
r=raw[:,0];eligible=np.flatnonzero((~frame)&(r[:,0]<-.004)&(r[:,0]>-.080)&(r[:,1]>-.085)&(r[:,1]<.045)&(r[:,2]>1.840)&(raw[:,:,2].max(axis=1)>1.862))
assert len(eligible)>200
features=raw[eligible][:,[0,12,25,40,64]].copy();features[:,0]*=.40;features=features.reshape(len(eligible),-1)
K=min(48,max(8,len(eligible)//90));fit=features[::2];centers=[fit[len(fit)//2]];best=np.full(len(fit),np.inf)
for _ in range(1,K):best=np.minimum(best,np.sum((fit-centers[-1])**2,axis=1));centers.append(fit[np.argmax(best)])
centers=np.array(centers)
def assign(x):return np.argmin(np.maximum(0,(x*x).sum(axis=1)[:,None]+(centers*centers).sum(axis=1)[None]-2*x@centers.T),axis=1)
for _ in range(20):
 labels=assign(fit)
 for k in range(K):
  if (labels==k).any():centers[k]=fit[labels==k].mean(axis=0)
labels=assign(features);body=bpy.data.objects['CC0 male body • retained topology']
assert np.array_equal(np.array(body.matrix_world),np.eye(4));bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
t=np.linspace(0,1,65);mask=np.zeros(len(raw),bool);rows=[];repairs=0
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
for k in np.unique(labels):
 members=eligible[labels==k]
 if len(members)<25:continue
 old=raw[members];center=old.mean(axis=0);tangent=np.gradient(center,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
 outward=np.array([bv.find_nearest(Vector(v))[1][:] for v in center])
 for _ in range(2):outward=np.vstack([outward[0],(outward[:-2]+outward[1:-1]+outward[2:])/3,outward[-1]])
 outward/=np.maximum(np.linalg.norm(outward,axis=1)[:,None],1e-9)
 previous=np.cross(tangent[0],outward[0]);previous/=max(np.linalg.norm(previous),1e-9);across=np.zeros_like(tangent)
 for j in range(65):
  previous-=tangent[j]*np.dot(previous,tangent[j]);length=np.linalg.norm(previous)
  if length<1e-8:
   axis=np.eye(3)[np.argmin(abs(tangent[j]))];previous=np.cross(tangent[j],axis);length=np.linalg.norm(previous)
  previous/=max(length,1e-9);across[j]=previous
 normal=np.cross(across,tangent);delta=old-center[None]
 along=np.sum(delta*tangent[None],axis=2);wide=np.sum(delta*across[None],axis=2);deep=np.sum(delta*normal[None],axis=2)
 width=np.diff(np.quantile(wide,[.05,.95],axis=0),axis=0)[0];depth=np.diff(np.quantile(deep,[.05,.95],axis=0),axis=0)[0]
 weight=smooth((t-.06)/.24)*(1-smooth((t-.76)/.21))*smooth((center[:,2]-1.825)/.030)
 ws=np.minimum(1,.0038/np.maximum(width,1e-7));ds=np.minimum(1,.0026/np.maximum(depth,1e-7))
 values=center[None]+tangent[None]*along[:,:,None]+across[None]*(wide*(1-weight[None]+ws[None]*weight[None]))[:,:,None]+normal[None]*(deep*(1-weight[None]+ds[None]*weight[None]))[:,:,None]
 phase=float(k*2.399963);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(center,axis=0),axis=1))];theta=2*np.pi*arc/.070+phase
 lift=.006+.004*(.5+.5*np.sin(phase))
 values+=outward[None]*((lift+.002*np.cos(theta))*weight)[None,:,None]
 values+=across[None]*(.003*np.sin(theta)*weight)[None,:,None]
 for i in range(len(members)):
  for j in range(4,62):
   if weight[j]<.001:continue
   hit,n,_,dist=bv.find_nearest(Vector(values[i,j]));gap=(Vector(values[i,j])-hit).dot(n)
   if dist<.020 and gap<.0005:values[i,j]+=np.array(n)*(.0007-gap);repairs+=1
 values[:,:4]=old[:,:4];values[:,62:]=old[:,62:];q[members]=values;mask[members]=True
 rows.append(dict(lock=int(k),fibers=len(members),lift_m=lift,median_before_width_m=float(np.median(width[16:49])),median_before_depth_m=float(np.median(depth[16:49])),max_displacement_m=float(np.linalg.norm(values-old,axis=2).max())))
assert mask.sum()>100 and np.isfinite(q).all() and np.array_equal(q[:,:4],raw[:,:4]) and np.array_equal(q[:,62:],raw[:,62:]) and np.array_equal(q[frame],raw[frame]) and np.array_equal(q[~mask],raw[~mask])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_lifted_crown_locks';ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask)
out.mkdir(parents=True);render.mkdir(parents=True);s=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False;s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for name in ['02_ThreeQuarter','01_Front','05_OppositeSide']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'lifted_crown_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,eligible_fibers=len(eligible),target_locks=K,edited_locks=len(rows),changed_fibers=int(mask.sum()),selection_attribute=attr,locks=rows,first_four_last_three_exact=True,explicit_front_frame_exact=True,unselected_primary_exact=True,other_hair_unchanged=True,discrete_body_repairs=repairs,method='Negative-X upper crown root region; whole-path small clusters, continuous transported sections target3.8mm width/2.6mm depth; 6-10mm actual smoothed scalp-normal lift with70mm wavelength/3mm lateral phase-staggered bends. Root/low-tip fade; existing foreground and nape endpoints retained.',status='Actual drafts pending review',scope='Local actual geometry/discrete body checks, not continuous collision or artistic acceptance'),indent=2),encoding='utf-8')
print('LIFTED_CROWN_SAVED',version,int(mask.sum()),len(rows),flush=True)
