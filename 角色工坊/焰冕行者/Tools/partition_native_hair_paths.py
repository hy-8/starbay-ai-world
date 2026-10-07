"""Read-only whole-path families. Local indices never belong in Git uploads."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2]):raise ValueError(a)
out=ROOT/'Exports'/version
if out.exists():raise RuntimeError('Fresh partition probe required')
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());raw=p.reshape(-1,65,3)
front=np.empty(len(cu.curves),np.int32);cu.attributes['native_front_guide_index'].data.foreach_get('value',front)
ids=np.flatnonzero(front<0);features=raw[ids][:,[0,16,32,48,64]].copy();features[:,0]*=.45;features=features.reshape(len(ids),-1)
fit=features[::3].astype(float);K=96;centers=[fit[len(fit)//2]];best=np.full(len(fit),np.inf)
for i in range(1,K):
 best=np.minimum(best,np.sum((fit-centers[-1])**2,axis=1));centers.append(fit[np.argmax(best)])
centers=np.array(centers)
def assign(x):return np.argmin(np.maximum(0,(x*x).sum(axis=1)[:,None]+(centers*centers).sum(axis=1)[None]-2*x@centers.T),axis=1)
for _ in range(18):
 labels=assign(fit)
 for i in range(K):
  if (labels==i).any():centers[i]=fit[labels==i].mean(axis=0)
labels=assign(features.astype(float));counts=[];widths=[];depths=[]
for i in range(K):
 pp=raw[ids[labels==i]];mean=pp.mean(axis=0);tangent=np.gradient(mean,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
 normal=mean-np.array([0,-.035,1.776]);normal-=tangent*np.sum(normal*tangent,axis=1)[:,None];normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-9)
 across=np.cross(tangent,normal);delta=pp-mean
 w=np.quantile(np.sum(delta*across[None],axis=2),[.05,.95],axis=0);d=np.quantile(np.sum(delta*normal[None],axis=2),[.05,.95],axis=0)
 counts.append(len(pp));widths.append(float(np.median((w[1]-w[0])[16:49])));depths.append(float(np.median((d[1]-d[0])[16:49])))
out.mkdir(parents=True);np.savez_compressed(out/'local_flow_groups.npz',ids=ids,labels=labels)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
summary=dict(source=base,source_sha256=digest,source_unchanged=True,method='96 deterministic farthest-seeded whole-path kmeans,5 position samples/root weight.45,18 iterations on1/3 sample, all non-frontal curves assigned',fiber_count=len(ids),groups=K,count_quantiles=np.quantile(counts,[0,.5,.9,1]).tolist(),middle_90pct_width_quantiles_m=np.quantile(widths,[0,.5,.9,1]).tolist(),middle_90pct_depth_quantiles_m=np.quantile(depths,[0,.5,.9,1]).tolist(),local_partition_sha256=hashlib.sha256((out/'local_flow_groups.npz').read_bytes()).hexdigest(),scope='Geometric aggregate only. Indices remain local. No art, continuous occlusion or collision assurance.')
(out/'partition_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print('WHOLE_PATH_PARTITION',version,len(ids),K,flush=True)
