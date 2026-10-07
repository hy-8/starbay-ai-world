"""Sculpt the previously missed crown family into continuous small locks."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base,probe=a[:3]
all_crown='--all-crown' in a
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:3]):raise ValueError(a)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh crown sculpture required')
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());raw=p.reshape(-1,65,3).astype(float);q=raw.copy()
partition=ROOT/'Exports'/probe/'local_flow_groups.npz';data=np.load(partition);ids=data['ids'];labels=data['labels']
front=np.empty(len(cu.curves),np.int32);cu.attributes['native_front_guide_index'].data.foreach_get('value',front);assert np.array_equal(ids,np.flatnonzero(front<0))
body=bpy.data.objects['CC0 male body • retained topology'];assert np.array_equal(np.array(body.matrix_world),np.eye(4));bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
mask=np.zeros(len(raw),bool);rows=[];repairs=0;t=np.linspace(0,1,65)
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
for family in ([5,20,33,62] if all_crown else [5]):
 members=ids[labels==family];old=raw[members]
 # Only this already measured high family is partitioned further; all others
 # and the previous posterior sculpture remain exactly untouched.
 features=old[:,[0,16,32,48,64]].copy();features[:,0]*=.45;features=features.reshape(len(members),-1)
 K=min(8,max(2,len(members)//180));fit=features[::3];centers=[fit[len(fit)//2]];best=np.full(len(fit),np.inf)
 for _ in range(1,K):best=np.minimum(best,np.sum((fit-centers[-1])**2,axis=1));centers.append(fit[np.argmax(best)])
 centers=np.array(centers)
 def assign(x):return np.argmin(np.maximum(0,(x*x).sum(axis=1)[:,None]+(centers*centers).sum(axis=1)[None]-2*x@centers.T),axis=1)
 for _ in range(16):
  lab=assign(fit)
  for g in range(K):
   if (lab==g).any():centers[g]=fit[lab==g].mean(axis=0)
 sublabels=assign(features)
 for g in np.unique(sublabels):
  selected=members[sublabels==g];old=raw[selected];center=old.mean(axis=0)
  tangent=np.gradient(center,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
  across=np.zeros_like(tangent);prev=np.cross(tangent[0],[0,0,1]);prev/=max(np.linalg.norm(prev),1e-9)
  for j in range(65):prev-=tangent[j]*np.dot(prev,tangent[j]);prev/=max(np.linalg.norm(prev),1e-9);across[j]=prev
  normal=np.cross(across,tangent);delta=old-center[None];wide=np.sum(delta*across[None],axis=2);deep=np.sum(delta*normal[None],axis=2);along=np.sum(delta*tangent[None],axis=2)
  fade=smooth((t-.06)/.20)*(1-smooth((t-.85)/.15));phase=(family*8+int(g))*2.399963
  # Different gently descending crowns, retaining the measured path and
  # its longitudinal scatter. No replacement with scalp arcs or point snap.
  elevated=smooth((center[:,2]-1.861)/.012)
  shape=fade*elevated
  values=center[None]+tangent[None]*along[:,:,None]+across[None]*(wide*(1-.32*fade[None]))[:,:,None]+normal[None]*(deep*(1-.30*fade[None]))[:,:,None]
  values[:,:,2]-=(.0035+.0015*(.5+.5*np.cos(phase)))*shape[None]
  arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(center,axis=0),axis=1))];theta=2*np.pi*arc/.060+phase
  values+=across[None]*(.0018*(np.sin(theta)-np.sin(phase))*shape)[None,:,None]
  values[:,:,2]+=(.0010*(np.cos(theta)-np.cos(phase))*shape)[None]
  for i in range(len(selected)):
   for j in range(4,62):
    if shape[j]<.001:continue
    hit,n,_,dist=bv.find_nearest(Vector(values[i,j]));gap=(Vector(values[i,j])-hit).dot(n)
    if dist<.020 and gap<.0005:values[i,j]+=np.array(n)*(.0007-gap);repairs+=1
  values[:,:4]=old[:,:4];values[:,62:]=old[:,62:];q[selected]=values;mask[selected]=True
  rows.append(dict(family=family,sublock=int(g),fibers=len(selected),max_displacement_m=float(np.linalg.norm(values-old,axis=2).max()),before_max_z_m=float(old[:,:,2].max()),after_max_z_m=float(values[:,:,2].max())))
assert mask.sum()>100 and np.isfinite(q).all() and np.array_equal(q[:,:4],raw[:,:4]) and np.array_equal(q[:,62:],raw[:,62:]) and np.array_equal(q[~mask],raw[~mask])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel());attribute='native_crown_sculpture'
prior=ob.data.attributes.get(attribute)
if prior:ob.data.attributes.remove(prior)
ob.data.attributes.new(attribute,'BOOLEAN','CURVE').data.foreach_set('value',mask)
out.mkdir(parents=True);render.mkdir(parents=True);s=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False;s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for name in ['02_ThreeQuarter','05_OppositeSide','01_Front']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'crown_sculpture_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,partition_sha256=hashlib.sha256(partition.read_bytes()).hexdigest(),changed_fibers=int(mask.sum()),sublocks=rows,selection_attribute=attribute,first_four_last_three_exact=True,unselected_primary_exact=True,discrete_body_repairs=repairs,method='Measured high family5 only' if not all_crown else 'Measured four high families5/20/33/62',sculpture='Whole-path sublocks (2-8 kmeans); parallel transported cross sections;32% width/30% depth contraction;3.5-5mm crown lowering;60mm wavelength1.8mm cross/1mm vertical bends;local elevation/root/tip fade',status='Actual drafts pending review',scope='Static local sculpture; no continuous collision/animation or artistic acceptance'),indent=2),encoding='utf-8');print('CROWN_SCULPTURE_SAVED',version,int(mask.sum()),flush=True)
