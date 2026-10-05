"""Continuous regional cage on existing fibers, not another averaged clump rebuild.

Retains follicles, radii, native editable curves and all unrelated geometry.
Posterior body/coat ray envelopes constrain a nape lay-down study.
"""
import bpy, sys, json, re, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
args = sys.argv[sys.argv.index('--') + 1:]
version, source_version = args[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+', v) for v in args[:2]):
    raise ValueError(args)
out, renders = ROOT/'Exports'/version, ROOT/'Renders'/version
if out.exists() or renders.exists():
    raise RuntimeError('Fresh version required')
source = ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()

def surface(names):
    verts, faces = [], []
    for name in names:
        ob = bpy.data.objects[name]
        ev = ob.evaluated_get(dg)
        mesh = ev.to_mesh(); mesh.calc_loop_triangles()
        offset = len(verts)
        verts.extend(tuple(ob.matrix_world @ v.co) for v in mesh.vertices)
        faces.extend(tuple(offset+i for i in tri.vertices) for tri in mesh.loop_triangles)
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, faces, all_triangles=True), np.array(verts)

body, _ = surface(['CC0 male body • retained topology'])
coat, _ = surface(['Fitted CC0 male_elegantsuit01', 'Tailored standing rear collar'])
collar = bpy.data.objects['Tailored standing rear collar']
collar_top = max((collar.matrix_world @ v.co).z for v in collar.data.vertices)

def smooth(x):
    x = np.clip(x, 0, 1)
    return x*x*(3-2*x)

rear = next(o for o in bpy.data.objects if not o.hide_render and o.name.startswith('Original posterior shag'))
if not np.allclose(np.array(rear.matrix_world), np.eye(4)):
    raise RuntimeError('Neutral world-aligned native groom required')
sizes = [len(c.points) for c in rear.data.curves]
if len(set(sizes)) != 1:
    raise RuntimeError('Uniform fibers required')
N = sizes[0]
raw = np.empty(len(rear.data.points)*3, np.float32)
rear.data.attributes['position'].data.foreach_get('vector', raw)
raw = raw.reshape(-1, N, 3)
result = raw.copy()
t = np.linspace(0, 1, N)
roots = raw[:, 0]
weights = (1-smooth((roots[:, 2]-1.807)/.033))*smooth((roots[:, 1]-.013)/.028)
ids = np.flatnonzero(weights > 0)
hits, shifts = 0, []
for i in ids:
    fiber = raw[i].astype(float)
    weight = weights[i]*smooth(t/.38)*smooth((1.821-fiber[:, 2])/.045)
    # A continuous field on individual existing paths keeps their length and
    # curl diversity. No median path collapses a whole group to a thin tail.
    q = fiber.copy()
    q[:, 0] += fiber[:, 0]*.12*weight*smooth((1.81-fiber[:, 2])/.09)
    envelope = np.full(N, -np.inf)
    for j in range(1, N):
        origin = Vector((q[j, 0], .4, q[j, 2]))
        hit, _, _, _ = body.ray_cast(origin, Vector((0, -1, 0)), .65)
        if hit is None:
            continue
        # Keep a small air layer; long hair rests near the neck, rather than
        # hanging as a detached, uniformly narrow posterior curtain.
        target = hit.y+.015
        envelope[j] = target
        if q[j, 2] < collar_top+.045:
            ch, _, _, _ = coat.ray_cast(origin, Vector((0, -1, 0)), .65)
            if ch is not None:
                envelope[j] = max(envelope[j], ch.y+.004)
        delta = max(-.045, min(0, envelope[j]-q[j, 1]))*.78*weight[j]
        q[j, 1] += delta
        hits += 1
    # Smooth the displacement, not the original fiber. This retains existing
    # strand detail while avoiding a hard bend at the top of the collar.
    dy = q[:, 1]-fiber[:, 1]
    for _ in range(3):
        dy[1:-1] = .25*dy[:-2]+.5*dy[1:-1]+.25*dy[2:]
    q[:, 1] = fiber[:, 1]+dy
    # Final regional back envelope guard. Point/ray sampling is not a complete
    # scalp/strand/garment collision proof and does not cover animation.
    valid = np.isfinite(envelope)
    # A guard must not pull unrelated fibers by unbounded amounts. Only
    # outward correction is permitted here; roots still remain exact.
    q[valid, 1] = np.maximum(q[valid, 1], np.minimum(envelope[valid]-.002, fiber[valid, 1]))
    q[0] = fiber[0]
    result[i] = q
    shifts.extend((fiber[:, 1]-q[:, 1])[weight > .5].tolist())
assert np.array_equal(result[:, 0], raw[:, 0]) and np.isfinite(result).all()
data = rear.data.copy()
data.attributes['position'].data.foreach_set('vector', result.ravel())
rear.data = data
out.mkdir(parents=True); renders.mkdir(parents=True)
report = dict(version=version, source=source_version,
    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    method='Continuous individual-fiber regional cage; move lower posterior hair toward actual neck/coat back-ray envelopes with smoothed displacement and lateral widening; do not average clump centers',
    components=[dict(object=rear.name, curves=len(raw), actually_modified_curves=int(np.any(raw!=result, axis=(1,2)).sum()),
        exact_roots_preserved=True, maximum_displacement_m=float(np.linalg.norm(result-raw, axis=2).max()),
        positions_before_sha256=hashlib.sha256(raw.tobytes()).hexdigest(),
        positions_after_sha256=hashlib.sha256(result.tobytes()).hexdigest())],
    rear_only=True, front_only=False, radii_unchanged=True,
    sampled_body_envelopes=hits, neck_pull_quantiles_m=np.quantile(shifts, [0,.5,.95,1]).tolist(),
    bounded_inward_pull_m=.045*.78, lower_fiber_height_transition_m=[1.776,1.821],
    collision_scope='Modified lower posterior points only, back ray envelopes; no exhaustive strand/scalp/eyes/garment or motion guarantee',
    status='Unreviewed native 3D nape cage study, not artistic acceptance')
(out/'shag_cut_manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
scene = bpy.context.scene
pref = bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX'; pref.get_devices()
for device in pref.devices: device.use = device.type=='OPTIX'
scene.cycles.device='GPU'; scene.cycles.samples=64
scene.cycles.use_denoising=False
scene.render.resolution_x, scene.render.resolution_y = 1200, 1400
scene.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['03_Side','04_Back']:
    scene.camera=bpy.data.objects[name]
    scene.render.filepath=str(renders/(name+'.png'))
    bpy.ops.render.render(write_still=True)
print('GROOM_CAGE_RENDERED', version, flush=True)
