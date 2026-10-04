"""Read-only paired geometry/UV checks and eye-opening ray samples.

Tests the sculpture invariants against its declared neutral source. The ray
grid measures actual eye visibility from the front, not full collision safety.
"""
import bpy, sys, re, hashlib, json
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
version = sys.argv[sys.argv.index('--')+1]
if not re.fullmatch('[A-Za-z0-9_-]+', version):
    raise ValueError(version)
folder = ROOT/'Exports'/version
output = folder/'paired_sculpt_audit.json'
if output.exists():
    raise RuntimeError('Preserve existing audit')
manifest = json.loads((folder/'portrait_sculpt_manifest.json').read_text())
source = ROOT/'Exports'/manifest['source']/'Ember_Regent.blend'
candidate = folder/'Ember_Regent.blend'

def mesh_digest(ob):
    p = np.array([v.co[:] for v in ob.data.vertices], np.float32)
    topology = [tuple(f.vertices) for f in ob.data.polygons]
    uv = [np.array([v.uv[:] for v in layer.data], np.float32).tobytes() for layer in ob.data.uv_layers]
    return p, hashlib.sha256(repr(topology).encode()).hexdigest(), hashlib.sha256(b''.join(uv)).hexdigest()

def visible_grooms():
    records = {}
    for ob in bpy.data.objects:
        if ob.type!='CURVES' or ob.hide_render:
            continue
        a = np.empty(len(ob.data.points)*3, np.float32)
        ob.data.attributes['position'].data.foreach_get('vector', a)
        r = np.empty(len(ob.data.points), np.float32)
        ob.data.attributes['radius'].data.foreach_get('value', r)
        records[ob.name] = hashlib.sha256(a.tobytes()+r.tobytes()+np.array(ob.matrix_world, np.float32).tobytes()).hexdigest()
    return records

def measure(path):
    bpy.ops.wm.open_mainfile(filepath=str(path), use_scripts=False)
    bpy.context.view_layer.update()
    body = bpy.data.objects['CC0 male body • retained topology']
    eyes = bpy.data.objects['Fitted CC0 high-poly']
    dg = bpy.context.evaluated_depsgraph_get()
    bvh, evh = BVHTree.FromObject(body, dg), BVHTree.FromObject(eyes, dg)
    p, topology, uv = mesh_digest(body)
    eye_xyz, eye_topology, eye_uv = mesh_digest(eyes)
    samples = []
    for side in [-1, 1]:
        xs = side*np.linspace(.018, .052, 101)
        zs = np.linspace(1.734, 1.766, 97)
        visible = []
        for x in xs:
            for z in zs:
                origin, direction = Vector((x, -.5, z)), Vector((0, 1, 0))
                eye_hit = evh.ray_cast(origin, direction, .6)[0]
                if eye_hit is None:
                    continue
                body_hit = bvh.ray_cast(origin, direction, .6)[0]
                if body_hit is None or eye_hit.y<body_hit.y-.00001:
                    visible.append((float(x),float(z)))
        a = np.array(visible)
        samples.append(dict(side=side, grid=[101,97], visible_ray_count=len(visible),
            approximate_projected_eye_area_m2=len(visible)*abs(xs[1]-xs[0])*(zs[1]-zs[0]),
            visible_xz_bounds=[a.min(axis=0).tolist(), a.max(axis=0).tolist()] if len(a) else [],
            scope='Front orthographic ray grid through retained eye mesh and actual evaluated body, excludes hair/brows/lashes; not exhaustive eyelid/motion contact validation'))
    return dict(body_base=p, topology=topology, uv=uv,
        eyeball_sha256=hashlib.sha256(eye_xyz.tobytes()+eye_topology.encode()+eye_uv.encode()).hexdigest(),
        grooms=visible_grooms(), eye_opening_samples=samples)

old = measure(source)
new = measure(candidate)
checks = dict(body_basis_exactly_preserved=np.array_equal(old['body_base'],new['body_base']),
              body_topology_preserved=old['topology']==new['topology'],
              body_uvs_preserved=old['uv']==new['uv'],
              eyeball_mesh_and_uv_preserved=old['eyeball_sha256']==new['eyeball_sha256'],
              all_visible_native_grooms_exactly_preserved=old['grooms']==new['grooms'])
assert all(checks.values()), checks
report = dict(version=version, source=manifest['source'],
    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
    invariant_checks=checks, checks_passed=True,
    before_eye_opening_samples=old['eye_opening_samples'], after_eye_opening_samples=new['eye_opening_samples'],
    scope='Paired static invariants and sampled front eye visibility; not art acceptance, full collision or animation validation')
output.write_text(json.dumps(report, indent=2), encoding='utf-8')
print('PAIRED_PORTRAIT_AUDIT',checks,flush=True)
