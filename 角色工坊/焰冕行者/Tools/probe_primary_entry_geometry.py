"""Read-only statistics of the now attributed primary entry sections."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:2])
out=ROOT/'Exports'/version;assert not out.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());p=p.reshape(-1,65,3).astype(float)
r=np.empty(len(cu.points),np.float32);cu.attributes['radius'].data.foreach_get('value',r);r=r.reshape(-1,65)
body=bpy.data.objects['CC0 male body • retained topology'];assert np.array_equal(np.array(body.matrix_world),np.eye(4)) and np.array_equal(np.array(ob.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get());root=p[:,0]
ids=np.flatnonzero((root[:,0]>.003)&(root[:,0]<.105)&(root[:,2]>1.805)&(root[:,1]<.060))
gaps=[];lengths=[];directions=[];stats=[]
for j in [0,1,3,7,12,16]:
 values=[]
 for i in ids:
  hit,n,_,dist=bv.find_nearest(Vector(p[i,j]));values.append(float((Vector(p[i,j])-hit).dot(n)))
 stats.append(dict(point_index_zero_based=j,nearest_body_signed_point_gap_quantiles_m=np.quantile(values,[0,.1,.5,.9,1]).tolist(),radius_quantiles_m=np.quantile(r[ids,j],[0,.1,.5,.9,1]).tolist()))
for i in ids:
 _,normal,_,_=bv.find_nearest(Vector(root[i]));direction=p[i,1]-root[i];direction/=max(np.linalg.norm(direction),1e-9);directions.append(float(np.dot(direction,normal)))
out.mkdir(parents=True)
report=dict(source=base,source_sha256=digest,eligible_primary_shafts=len(ids),region='positive-X upper scalp roots .003<X<.105, Z>1.805, Y<.060',point_stats=stats,entry_normal_cosine_quantiles=np.quantile(directions,[0,.1,.5,.9,1]).tolist(),first_eight_point_arc_quantiles_m=np.quantile(np.linalg.norm(np.diff(p[ids,:8],axis=1),axis=2).sum(axis=1),[0,.1,.5,.9,1]).tolist(),source_unchanged=hashlib.sha256(source.read_bytes()).hexdigest()==digest,scope='Aggregate geometry in root region; view ownership from real emission section IDs. Signed nearest-point distances, not continuous body/animation collision.')
(out/'entry_geometry_probe.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report),flush=True)
