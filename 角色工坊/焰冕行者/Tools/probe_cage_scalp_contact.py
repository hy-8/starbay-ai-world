"""Source-paired sampling of modified native fibers against evaluated head skin.

This is a finite regional nearest-face diagnostic, not exhaustive collisions.
"""
import bpy, sys, json, re, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
version=sys.argv[sys.argv.index('--')+1]
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
folder=ROOT/'Exports'/version
output=folder/'sampled_cage_scalp_contact.json'
if output.exists():raise RuntimeError('Prior diagnostic preserved')
manifest=json.loads((folder/'shag_cut_manifest.json').read_text(encoding='utf-8'))
source=ROOT/'Exports'/manifest['source']/'Ember_Regent.blend'
candidate=folder/'Ember_Regent.blend'
source_sha=hashlib.sha256(source.read_bytes()).hexdigest()
candidate_sha=hashlib.sha256(candidate.read_bytes()).hexdigest()
assert source_sha==manifest['source_sha256']
def read(name):
    ob=bpy.data.objects[name];count=len(ob.data.curves[0].points)
    p=np.empty(len(ob.data.points)*3,np.float32)
    ob.data.attributes['position'].data.foreach_get('vector',p)
    return p.reshape(-1,count,3)
names=[row['object'] for row in manifest['components']]
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
old={name:read(name) for name in names}
bpy.ops.wm.open_mainfile(filepath=str(candidate),use_scripts=False)
bpy.context.view_layer.update()
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
rows=[]
for name in names:
    p=read(name);changed=np.any(p!=old[name],axis=2)
    changed[:,0]=False
    changed &= p[:,:,2]>1.745
    ids=np.flatnonzero(changed.ravel())
    rng=np.random.default_rng(100505)
    ids=rng.choice(ids,min(20000,len(ids)),replace=False)
    paired={}
    for label,points in [('source',old[name]),('candidate',p)]:
        gaps=[];distances=[]
        for index in ids:
            q=Vector(points.reshape(-1,3)[index])
            hit,normal,_,distance=bv.find_nearest(q)
            gaps.append((q-hit).dot(normal));distances.append(distance)
        gaps=np.array(gaps);distances=np.array(distances)
        flags=(gaps<-.0005)&(distances<.02)
        paired[label]=dict(potential_contact_flags=int(flags.sum()),
            signed_gaps_quantiles_m=np.quantile(gaps,[0,.01,.5,1]).tolist(),
            flagged_point_indices=ids[flags][:20].tolist())
    rows.append(dict(object=name,sampled_points=len(ids),paired=paired))
report=dict(source=manifest['source'],candidate=version,source_sha256=source_sha,candidate_sha256=candidate_sha,
    source_and_candidate_unchanged=True,components=rows,
    scope='At most20000 seeded samples per modified object, changed interior points z>1.745m, evaluated body nearest-face gap <-0.5mm and distance<20mm; source and candidate compared at identical indices',
    boundary='Finite sampled proximity on head skin. Does not prove all-fiber, strand-strand, eye, garment, scalp surface-crossing or animated collision safety.')
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_sha
assert hashlib.sha256(candidate.read_bytes()).hexdigest()==candidate_sha
output.write_text(json.dumps(report,indent=2),encoding='utf-8')
print('CAGE_SCALP_CONTACT',rows,flush=True)
