"""Actual-camera localized sculpt of the observed upright fringe lock."""
import bpy, sys, re, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--')+1:]
version, base = a[:2]
probe = '--probe' in a
surface_bend = '--surface-bend' in a
amount = float(a[a.index('--amount')+1]) if '--amount' in a else .010
assert abs(amount) <= .018 and all(re.fullmatch('[A-Za-z0-9_-]+', v) for v in a[:2])
source = ROOT/'Exports'/base/'Ember_Regent.blend'
digest = hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
ob = bpy.data.objects['Bystedt layercut derivative • native root reflow']
assert np.array_equal(np.array(ob.matrix_world), np.eye(4))
cu = ob.data
p = np.empty((len(cu.points), 3), np.float32)
cu.attributes['position'].data.foreach_get('vector', p.ravel())
raw = p.reshape(-1, 65, 3).astype(float)
fringe = np.empty(len(raw), bool)
cu.attributes['native_resculpted_fringe_sweeps'].data.foreach_get('value', fringe)
camera = bpy.data.objects['02_ThreeQuarter']
M = np.array(camera.matrix_world.inverted())
P = np.array(camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(), x=1200, y=1400, scale_x=1, scale_y=1))
flat = raw.reshape(-1, 3)
clip = np.c_[flat, np.ones(len(flat))]@M.T@P.T
xy = clip[:, :2]/clip[:, 3, None]
pixel = np.c_[xy[:, 0]*.5+.5, .5-xy[:, 1]*.5].reshape(-1, 65, 2)
center, radii = np.array([.588, .400]), np.array([.022, .115])
inside = np.sum(((pixel-center)/radii)**2, axis=2) < 1
hits = inside[:, 10:62].sum(axis=1)
mask = fringe & (hits >= 12)
ids = np.flatnonzero(mask)
assert len(ids) > 10 and len(ids) < fringe.sum()*.6, len(ids)
record = dict(source=base, source_sha256=digest, source_unchanged=True,
    camera='02_ThreeQuarter', selection='Actual current fringe with>=12 points10:61 in normalized image ellipse center(.588,.400)/radii(.022,.115). Geometric projection only, not depth/visibility proof.',
    fibers=len(ids), root_xyz_quantiles_m=np.quantile(raw[ids, 0], [0,.25,.5,.75,1], axis=0).tolist(),
    tip_xyz_quantiles_m=np.quantile(raw[ids, -1], [0,.25,.5,.75,1], axis=0).tolist(),
    projected_point_count_quantiles=np.quantile(hits[ids], [0,.5,1]).tolist())
if probe:
    out = ROOT/'Exports'/(version+'.json')
    assert not out.exists()
    record['status'] = 'Read-only geometric projection probe, not art acceptance'
    out.write_text(json.dumps(record, indent=2), encoding='utf-8')
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
    print('FRONTAL_PROBE', json.dumps(record), flush=True)
    sys.exit(0)
out, rd = ROOT/'Exports'/version, ROOT/'Renders'/version
assert not out.exists() and not rd.exists()
body = bpy.data.objects['CC0 male body • retained topology']
bv = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
right = np.array(camera.matrix_world)[:3, 0]
t = np.linspace(0, 1, 65)
onset = np.clip((t-t[5])/.22, 0, 1)
onset = onset*onset*(3-2*onset)
envelope = np.sin(np.pi*t)**1.6*onset
q = raw.copy()
repairs = 0
for index in ids:
    old = raw[index]
    # Broad shared bend, independent source paths and exact own endpoints.
    root = old[0]
    phase = root[0]*55 + root[1]*45
    strength = .8 + .2*(.5+.5*np.sin(phase))
    if surface_bend:
        normals = np.array([bv.find_nearest(Vector(v))[1][:] for v in old])
        for axis in range(3):
            normals[:, axis] = np.convolve(np.pad(normals[:, axis], (2, 2), mode='edge'), np.array([1,4,6,4,1])/16, mode='valid')
        normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-9)
        tangents = right[None, :] - normals*(normals@right)[:, None]
        values = old + envelope[:, None]*(tangents*(amount*strength) + normals*.002)
    else:
        values = old + envelope[:, None]*right[None, :]*(amount*strength)
        values[:, 1] -= envelope*.003
    correction = np.zeros_like(values)
    for j in range(6, 64):
        hit, nn, _, distance = bv.find_nearest(Vector(values[j]))
        gap = (Vector(values[j])-hit).dot(nn)
        if distance < .025 and gap < .0008:
            correction[j] = np.array(nn)*(.0011-gap)
            repairs += 1
    magnitude = np.linalg.norm(correction, axis=1)
    expanded = correction.copy()
    for j in range(6, 64):
        lo, hi = max(6, j-4), min(64, j+5)
        weight = np.maximum(0, 1-np.abs(np.arange(lo, hi)-j)/5)
        scores = magnitude[lo:hi]*weight
        winner = int(np.argmax(scores))
        if scores[winner] > np.linalg.norm(expanded[j]):
            expanded[j] = correction[lo+winner]*weight[winner]
    values += expanded
    values[:6], values[-1] = old[:6], old[-1]
    q[index] = values
assert np.isfinite(q).all() and np.array_equal(q[:, :6], raw[:, :6])
assert np.array_equal(q[:, -1], raw[:, -1]) and np.array_equal(q[~mask], raw[~mask])
ob.data = cu.copy()
ob.data.attributes['position'].data.foreach_set('vector', q.astype(np.float32).ravel())
attribute = 'native_projected_front_bend'
assert not ob.data.attributes.get(attribute)
ob.data.attributes.new(attribute, 'BOOLEAN', 'CURVE').data.foreach_set('value', mask)
ob.data.update_tag()
out.mkdir(parents=True)
rd.mkdir(parents=True)
s = bpy.context.scene
pref = bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type = 'OPTIX'
pref.get_devices()
for d in pref.devices: d.use = d.type == 'OPTIX'
s.cycles.device = 'GPU'
s.cycles.samples = 96
s.cycles.use_denoising = False
s.render.resolution_x, s.render.resolution_y = 1200, 1400
s.render.resolution_percentage = 80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
record.update(selection_attribute=attribute, changed_fibers=len(ids), amount_m=amount, surface_bend=surface_bend,
    intermediate_sampled_repairs=repairs, preserved_prefix_points=6, all_endpoints_exact=True,
    method=('Selected current fringe: single broad sin(pi*t)^1.6 bend,80-100% root-field strength. '
            + ('Camera-right vector projected onto smoothed per-point nearest-body tangent planes;2mm normal lift. ' if surface_bend else 'Fixed camera-right vector with3mm forward offset. ')
            + 'Onset afterpoint5, own tips exact.0.8/1.1mm discrete body point guard with4-point envelope. Original radii/topology/otherhair/materials/lamps retained; not continuous collision verification.'),
    status='Unreviewed actual geometry study')
(out/'projected_front_manifest.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
for shot in ['02_ThreeQuarter', '01_Front']:
    s.camera = bpy.data.objects[shot]
    s.render.filepath = str(rd/(shot+'.png'))
    bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
print('PROJECTED_FRONT_RENDERED', version, len(ids), flush=True)
