"""Measure actual surface distance for the crown roots, without changing the model."""
import bpy, sys, json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1]
base=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.open_mainfile(filepath=str(root/'Exports'/base/'Ember_Regent.blend'),use_scripts=False)
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
report=[]
for ob in bpy.data.objects:
 if ob.type!='CURVES' or ob.hide_render: continue
 cu=ob.data
 p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
 sizes=np.array([c.points_length for c in cu.curves]);starts=np.r_[0,np.cumsum(sizes)[:-1]]
 roots=p[starts];upper=roots[:,2]>1.835
 gaps=[]
 for v in roots[upper]:
  pos=ob.matrix_world@Vector(v);h,n,_,_=bv.find_nearest(pos);gaps.append((pos-h).dot(n))
 report.append(dict(name=ob.name,curves=len(sizes),bounds=[p.min(0).tolist(),p.max(0).tolist()],upper_roots=int(upper.sum()),upper_root_gap_quantiles=np.quantile(gaps,[0,.1,.5,.9,1]).tolist() if gaps else None))
print('ROOT_CLEARANCE',json.dumps(report),flush=True)
