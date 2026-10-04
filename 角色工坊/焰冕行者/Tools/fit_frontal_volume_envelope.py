"""Fit actual upper frontal lock clearance to the actual retained body.

Preserves verified real roots and fiber offsets; no flat clipping plane. Fresh
neutral render variants are needed to judge whether the volume fit helps art.
"""
import bpy, sys, re, json, hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
args = sys.argv[sys.argv.index('--')+1:]
version, source_version = args[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+', v) for v in args[:2]):
    raise ValueError(args)
limit = float(args[args.index('--limit-mm')+1])*.001 if '--limit-mm' in args else .018
lower_fringe = '--lower-fringe' in args
if not .012<=limit<=.032:
    raise ValueError('Frontal envelope must be 12..32mm')
out, render = ROOT/'Exports'/version, ROOT/'Renders'/version
if out.exists() or render.exists():
    raise RuntimeError('Fresh output required')
source = ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
bpy.context.view_layer.update()
front = next(o for o in bpy.data.objects if o.name.startswith('Authored frontal revision') and not o.hide_render)
if not np.allclose(np.array(front.matrix_world), np.eye(4)):
    raise RuntimeError('Neutral world-aligned frontal groom required')
records = json.loads((ROOT/'Exports/spatialfringe17/authored_fringe_design.json').read_text(encoding='utf-8'))
cu = front.data
sizes = [len(c.points) for c in cu.curves]
if len(set(sizes))!=1 or sum(r['assigned_visible_fibers'] for r in records)!=len(sizes):
    raise RuntimeError('Known authored frontal groups required')
N = sizes[0]
t = np.linspace(0, 1, N)
raw = np.empty(len(cu.points)*3, np.float32)
cu.attributes['position'].data.foreach_get('vector', raw)
raw = raw.reshape(-1, N, 3)
result = raw.copy()
bv = BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'], bpy.context.evaluated_depsgraph_get())

def smooth(x):
    x = np.clip(x, 0, 1)
    return x*x*(3-2*x)

offset = 0
before, after = [], []
modified_locks = 0
for record in records:
    count = record['assigned_visible_fibers']
    group = raw[offset:offset+count].astype(float)
    base = np.median(group, axis=0)
    delta = np.zeros_like(base)
    for j in range(1, N):
        point = base[j]
        lower_z, height_span = (1.710, .030) if lower_fringe else (1.785, .040)
        weight = float(smooth((point[2]-lower_z)/height_span)*smooth(t[j]/.15))
        if weight<1e-6:
            continue
        hit, normal, face, dist = bv.find_nearest(Vector(point))
        gap = (Vector(point)-hit).dot(normal)
        before.append(gap)
        if gap>limit and dist<.090:
            delta[j] = np.array(normal)*(-(gap-limit)*weight)
    # Smooth the normal displacement along each real lock, rather than
    # imposing a hard height boundary or individually kinked nearest points.
    kernel = np.array([1, 2, 3, 2, 1], float)/9
    delta = np.stack([np.convolve(delta[:, k], kernel, mode='same') for k in range(3)], axis=1)
    delta *= smooth(t/.12)[:, None]
    delta[0] = 0
    if np.linalg.norm(delta, axis=1).max()>.0001:
        modified_locks += 1
    new_base = base+delta
    for j in range(1, N):
        if base[j, 2]<=(1.710 if lower_fringe else 1.785):
            continue
        hit, normal, face, dist = bv.find_nearest(Vector(new_base[j]))
        after.append((Vector(new_base[j])-hit).dot(normal))
    result[offset:offset+count] = (group+delta[None]).astype(np.float32)
    result[offset:offset+count, 0] = raw[offset:offset+count, 0]
    offset += count
assert offset==len(raw) and np.array_equal(result[:, 0], raw[:, 0]) and np.isfinite(result).all()
new_data = cu.copy()
new_data.attributes['position'].data.foreach_set('vector', result.ravel())
front.data = new_data
scene = bpy.context.scene
pref = bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type = 'OPTIX'
pref.get_devices()
for device in pref.devices:
    device.use = device.type=='OPTIX'
scene.cycles.device = 'GPU'
scene.cycles.samples = 64 if '--draft' in args else 192
scene.cycles.use_denoising = False
scene.render.resolution_x, scene.render.resolution_y = 1200, 1400
scene.render.resolution_percentage = 80 if '--draft' in args else 100
out.mkdir(parents=True)
render.mkdir(parents=True)
report = dict(version=version, source=source_version,
    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    method='Per-lock selected scalp normal clearance envelope; smooth along-path displacements, exact roots and fiber cross sections retained',
    limit_m=limit, modified_locks=modified_locks, frontal_curves=len(raw),
    lower_fringe_included=lower_fringe,
    all_roots_preserved_exactly=True,
    max_displacement_m=float(np.linalg.norm(result-raw, axis=2).max()),
    selected_base_gap_before_quantiles_m=np.quantile(before, [0, .5, .95, 1]).tolist(),
    selected_base_gap_after_quantiles_m=np.quantile(after, [0, .5, .95, 1]).tolist(),
    samples=scene.cycles.samples, draft='--draft' in args, denoising=False,
    status='Unreviewed actual geometric study; not artistic approval',
    collision_scope='Selected median paths only, with slightly differing before/after endpoint eligibility; not exhaustive scalp/fibers/clothing/motion validation',
    license='Original frontal and posterior geometry; Bystedt CC BY-SA support; Abhay Pratap Royalty Free flow-derived support; hidden donor rear stays local')
(out/'frontal_envelope_manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front', '02_ThreeQuarter', '03_Side', '04_Back']:
    scene.camera = bpy.data.objects[name]
    scene.render.filepath = str(render/(name+'.png'))
    bpy.ops.render.render(write_still=True)
print('FRONTAL_VOLUME_ENVELOPE_RENDERED', version, flush=True)
