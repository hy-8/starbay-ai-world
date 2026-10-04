"""Sample actual scalp-normal gaps at real frontal roots; no model mutation."""
import bpy, sys, re, json, hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT = Path(__file__).resolve().parents[1]
version = sys.argv[sys.argv.index('--')+1]
if not re.fullmatch('[A-Za-z0-9_-]+', version):
    raise ValueError(version)
source = ROOT/'Exports'/version/'Ember_Regent.blend'
output = ROOT/'Exports'/version/'frontal_root_sample_probe.json'
if output.exists():
    raise RuntimeError('Preserve earlier probe')
before = hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
bpy.context.view_layer.update()
front = next(o for o in bpy.data.objects if o.name.startswith('Authored frontal revision') and not o.hide_render)
sizes = [len(c.points) for c in front.data.curves]
assert len(set(sizes))==1 and len(sizes)==27760
a = np.empty(len(front.data.points)*3, np.float32)
front.data.attributes['position'].data.foreach_get('vector', a)
roots = a.reshape(-1,sizes[0],3)[:,0]
bv = BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
rows = []
for name, start, end in [('Crown',0,6160),('Fringe',6160,27760)]:
    gaps = []
    for root in roots[start:end:24]:
        p = front.matrix_world@Vector(root)
        hit, normal, index, distance = bv.find_nearest(p)
        gaps.append((p-hit).dot(normal))
    rows.append(dict(region=name, stride=24, sampled_roots=len(gaps),
        signed_gap_quantiles_m=np.quantile(gaps,[0,.5,.95,1]).tolist()))
report = dict(source=version, source_sha256=before, source_unchanged=hashlib.sha256(source.read_bytes()).hexdigest()==before,
    method='Every 24th real root in known authored crown/fringe groups against actual evaluated body BVH',regions=rows,
    scope='Sampled roots only; does not prove all-root/all-strand attachment or collisions')
output.write_text(json.dumps(report,indent=2),encoding='utf-8')
print('FRONTAL_ROOT_SAMPLE_PROBE',rows,flush=True)
