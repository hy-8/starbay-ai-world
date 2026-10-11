"""Separate the broad positive-X sweep into unequal coherent sections."""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
bounded='--bounded' in a
projected=a[a.index('--projected')+1] if '--projected' in a else None
save='--save-archive' in a;save_only='--save-only' in a;assert not save_only or save
md=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者\Exports')/version
if save:assert not md.exists() and not (ROOT/'Exports'/version).exists()
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=ROOT/'Renders'/version;assert not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());original=p.copy()
sizes=np.array([c.points_length for c in cu.curves]);starts=np.r_[0,np.cumsum(sizes)[:-1]];roots=p[starts]
restored=np.empty(len(sizes),bool);cu.attributes['native_restored_raw_controls'].data.foreach_get('value',restored)
accepted=np.empty(len(sizes),bool);cu.attributes['native_inner_curtain_shift'].data.foreach_get('value',accepted)
mask=(~restored)&(~accepted)&(roots[:,0]>.003)&(roots[:,2]>1.820)
if projected:
 idroot=ROOT/'Renders'/projected;idm=json.loads((idroot/'edit_id_manifest.json').read_text());assert idm['source_sha256']==digest
 selected=np.load(idroot/'local_projected_indices.npz')['selected'];mask[:]=False;mask[selected]=True;mask&=(~restored)&(~accepted)&(sizes==65)
ids=np.flatnonzero(mask);assert len(ids)>300 and np.all(sizes[ids]==65)
indices=starts[ids,None]+np.arange(65)[None,:];paths=p[indices].astype(float)
features=paths[:,[0,16,32,48],:].reshape(len(paths),-1)
K=14 if projected else 7;centers=[features[len(features)//2]];distance=np.full(len(features),np.inf)
for i in range(1,K):
 distance=np.minimum(distance,np.sum((features-centers[-1])**2,axis=1));centers.append(features[np.argmax(distance)])
centers=np.array(centers)
for i in range(20):
 labels=np.argmin(((features[:,None,:]-centers[None,:,:])**2).sum(2),axis=1)
 for k in range(K):
  if np.any(labels==k):centers[k]=features[labels==k].mean(0)
t=np.linspace(0,1,65)
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
envelope=smooth((t-.12)/.19)*(1-smooth((t-.65)/.20));envelope[:8]=0;envelope[56:]=0
body=bpy.data.objects['CC0 male body • retained topology'];bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
result=paths.copy();repairs=0;groups=[]
for k in range(K):
 rows=np.flatnonzero(labels==k);src=paths[rows];center=src.mean(0)
 tangent=np.gradient(center,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-10)
 normal=center-np.array([0,-.035,1.776]);normal-=tangent*np.sum(normal*tangent,axis=1)[:,None];normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-10)
 across=np.cross(tangent,normal)
 width=np.sum((src-center)*across,axis=2)
 contraction=.28+.12*(.5+.5*np.sin(k*2.39));lift=.0004+.0015*(.5+.5*np.sin(k*1.73))
 if projected:contraction=.65;lift=0
 lateral=width*contraction
 if bounded:
  limit=.004 if projected else .0018;lateral=limit*np.tanh(lateral/limit);lift*=.20
 vals=src-across[None]*(lateral*envelope)[:,:,None]+normal[None]*(lift*envelope)[None,:,None]
 for i in range(len(rows)):
  for j in range(8,56):
   if envelope[j]<.001:continue
   h,n,_,dist=bv.find_nearest(Vector(vals[i,j]));gap=(Vector(vals[i,j])-h).dot(n)
   if bounded:
    oh,on,_,od=bv.find_nearest(Vector(src[i,j]));oldgap=(Vector(src[i,j])-oh).dot(on)
    if dist<.03 and gap<min(.0003,oldgap):vals[i,j]=src[i,j];repairs+=1
   elif dist<.03 and gap<.0005:
    vals[i,j]+=np.array(n)*(.0005-gap);repairs+=1
 vals[:,:8]=src[:,:8];vals[:,56:]=src[:,56:];result[rows]=vals
 groups.append(dict(group=k,fibers=len(rows),width_contraction=contraction,lift_m=lift))
p[indices]=result.astype(np.float32);assert np.isfinite(p).all()
cu.attributes['position'].data.foreach_set('vector',p.ravel());cu.update_tag()
modelhash=None
if save:
 cu.attributes.new('native_sweep_channels','BOOLEAN','CURVE').data.foreach_set('value',mask)
 md.mkdir(parents=True);bpy.ops.wm.save_as_mainfile(filepath=str(md/'Ember_Regent.blend'),compress=True);modelhash=hashlib.sha256((md/'Ember_Regent.blend').read_bytes()).hexdigest()
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE';s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
out.mkdir(parents=True);images={}
for shot in ([] if save_only else ['02_ThreeQuarter','03_Side']):
 s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=hashlib.sha256(dest.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
method='Read-only geometry pilot. Non-restored primary curves,rootX>3mm,rootZ>1.820m,exclude accepted inner curtain. Seven deterministic whole-path families;28-40percent middle transverse width contraction and0.4-1.9mm outward loft. First8 and last9 controls preserved, radii unchanged. Discrete body guard not continuous collision proof. Preserve side-part direction; right-sweep geometry intentionally changes.'
if bounded:method+=' Bounded mode: transverse contraction smoothly saturates at1.8mm; loft reduced to20percent. If a new point falls below min(original signed nearest gap,0.3mm), revert that point to its original source instead of projecting buried controls outward.'
if projected:method='Actual inspected projected ellipse selection, excluding restored/accepted/mixed-short curves.14 deterministic whole-path families;65percent middle transverse contraction bounded4mm,zero loft. First8 and last9controls preserved,radii unchanged. If a new point falls below min(original signed nearest gap,0.3mm),revert that point to source. Local body guard is not continuous collision proof. Preserves side-part direction;right-sweep geometry intentionally changes.'
manifest=dict(source=base,source_sha256=digest,model_saved=save,model_sha256=modelhash,archive_model_path=str(md/'Ember_Regent.blend') if save else None,source_unchanged=True,bounded=bounded,projected_selection=projected,selected_fibers=len(ids),groups=groups,max_same_index_displacement_m=float(np.linalg.norm(p-original,axis=1).max()),discrete_body_repairs=repairs,images_sha256=images,method=method)
(out/'sweep_channels_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
if save:(md/'sweep_channels_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('FRONTAL_CHANNELS_RESULT',version,flush=True)
