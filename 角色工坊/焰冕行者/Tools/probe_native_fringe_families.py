"""Aggregate existing frontal family flow and free-tip widths."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base,probe=a
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a):raise ValueError(a)
out=ROOT/'Exports'/version
if out.exists():raise RuntimeError('Fresh aggregate required')
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
cu=bpy.data.objects['Bystedt layercut derivative • native root reflow'].data;p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());p=p.reshape(-1,65,3).astype(float)
frontal=np.empty(len(cu.curves),np.int32);cu.attributes['native_front_guide_index'].data.foreach_get('value',frontal)
data=np.load(ROOT/'Exports'/probe/'local_flow_groups.npz');ids=data['ids'];labels=data['labels'];assert np.array_equal(ids,np.flatnonzero(frontal>=0))
rows=[]
for g in np.unique(labels):
 members=ids[labels==g];q=p[members];center=q.mean(axis=0);tangent=np.gradient(center,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
 cross=np.cross(tangent,[0,0,1]);cross/=np.maximum(np.linalg.norm(cross,axis=1)[:,None],1e-9);delta=q-center[None];width=np.diff(np.quantile(np.sum(delta*cross[None],axis=2),[.05,.95],axis=0),axis=0)[0]
 rows.append(dict(group=int(g),shafts=len(q),root_mean_m=center[0].tolist(),tip_mean_m=center[-1].tolist(),middle_90pct_width_m=float(np.median(width[16:49])),free_90pct_width_m=float(np.median(width[49:])),tip_z_quantiles_m=np.quantile(q[:,-1,2],[0,.1,.5,.9,1]).tolist(),arc_length_quantiles_m=np.quantile(np.linalg.norm(np.diff(q,axis=1),axis=2).sum(axis=1),[0,.5,1]).tolist()))
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
summary=dict(source=base,source_sha256=digest,source_unchanged=True,records=rows,scope='Geometric family aggregates only, not projected-camera visibility, artistic or collision approval; indices stay local')
out.mkdir(parents=True);(out/'fringe_probe.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print('FRINGE_FAMILY_PROBE',json.dumps(summary),flush=True)
