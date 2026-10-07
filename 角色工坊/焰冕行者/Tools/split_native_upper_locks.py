"""Sculpt nested, asymmetric subdivisions within existing upper locks.

Deterministic native-curve editing only; no source geometry is sent to AI.
"""
import bpy, sys, re, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--') + 1:]
version, base, donor = a[:3]
assert all(re.fullmatch('[A-Za-z0-9_-]+', v) for v in a[:3])
out, renders = ROOT/'Exports'/version, ROOT/'Renders'/version
assert not out.exists() and not renders.exists()
name = 'Bystedt layercut derivative • native root reflow'

def read(v):
    p = ROOT/'Exports'/v/'Ember_Regent.blend'
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(p), use_scripts=False)
    cu = bpy.data.objects[name].data
    xyz = np.empty((len(cu.points), 3), np.float32)
    cu.attributes['position'].data.foreach_get('vector', xyz.ravel())
    return p, h, xyz.reshape(-1, 65, 3).astype(float)

donorpath, donorhash, old = read(donor)
source, digest, raw = read(base)
ob = bpy.data.objects[name]; cu = ob.data
frame = np.empty(len(raw), bool)
cu.attributes['native_front_frame_sculpture'].data.foreach_get('value', frame)
eligible = np.flatnonzero((~frame) & (old[:, 0, 2] > 1.830) & (old[:, 0, 1] < .065))
features = (old[eligible][:, [0, 8, 16, 24, 40]] * np.array([.7, .9, 1, 1, .4])[None, :, None]).reshape(len(eligible), -1)
centers = [features[len(features)//2]]; best = np.full(len(features), np.inf)
for _ in range(1, 150):
    best = np.minimum(best, np.sum((features-centers[-1])**2, axis=1))
    centers.append(features[np.argmax(best)])
centers = np.array(centers)
def assign():
    return np.argmin(np.maximum(0, (features*features).sum(1)[:, None] + (centers*centers).sum(1)[None] - 2*features@centers.T), axis=1)
for _ in range(24):
    labels = assign()
    for k in range(150):
        if (labels == k).any(): centers[k] = features[labels == k].mean(0)
labels = assign()
body = bpy.data.objects['CC0 male body • retained topology']
assert np.array_equal(np.array(body.matrix_world), np.eye(4))
bv = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
t = np.linspace(0, 1, 65)
def smooth(x):
    x = np.clip(x, 0, 1); return x*x*(3-2*x)
env = smooth(t/.13)*(1-smooth((t-.36)/.32)); env[44:] = 0
q = raw.copy(); mask = np.zeros(len(raw), bool); rows = []; repairs = 0
for k in range(150):
    ids = eligible[labels == k]
    if len(ids) < 80: continue
    c = raw[ids].mean(0)
    # Restrict this study to the front upper sweep, leaving rear waves alone.
    if c[0, 1] > -.010: continue
    tangent = np.gradient(c, axis=0)
    tangent /= np.maximum(np.linalg.norm(tangent, axis=1)[:, None], 1e-9)
    _, n, _, _ = bv.find_nearest(Vector(c[0]))
    across = np.zeros_like(tangent); prev = np.cross(np.array(n), tangent[0])
    prev /= max(np.linalg.norm(prev), 1e-9)
    for j in range(65):
        prev -= tangent[j]*np.dot(prev, tangent[j])
        prev /= max(np.linalg.norm(prev), 1e-9); across[j] = prev
    normal = np.cross(tangent, across)
    if np.dot(normal[0], np.array(n)) < 0: normal = -normal
    delta = raw[ids]-c[None]
    wide = np.sum(delta*across[None], axis=2)
    # Follow each fiber's existing section position to form coherent sublocks.
    coordinate = np.mean(wide[:, 8:25], axis=1)
    cut = np.quantile(coordinate, [.29, .68])
    bands = np.searchsorted(cut, coordinate)
    for b in range(3):
        members = ids[bands == b]
        if len(members) < 20: continue
        values = raw[members].copy(); center = values.mean(0)
        d = values-center[None]
        width = np.sum(d*across[None], axis=2)
        phase = (k*2.399963 + b*1.73)
        # Subtle broad lateral separation and unequal height, no periodic curl.
        lateral = (b-1)*.0018 + .0007*np.sin(phase)
        loft = .0005 + .0018*(.5+.5*np.sin(phase+1))
        asymmetric = env*(.8+.2*np.sin(t*3+phase))
        values -= across[None]*(width*.38*env[None])[:, :, None]
        values += across[None]*(lateral*asymmetric)[None, :, None]
        values += normal[None]*(loft*asymmetric)[None, :, None]
        for i in range(len(members)):
            for j in range(1, 44):
                if env[j] < .001: continue
                hit, nn, _, dist = bv.find_nearest(Vector(values[i, j]))
                gap = (Vector(values[i, j])-hit).dot(nn)
                if dist < .03 and gap < .0005:
                    values[i, j] += np.array(nn)*(.0007-gap); repairs += 1
        values[:, 0] = raw[members, 0]; values[:, 44:] = raw[members, 44:]
        q[members] = values; mask[members] = True
        rows.append(dict(group=k, band=b, fibers=len(members), maximum_displacement_m=float(np.linalg.norm(values-raw[members], axis=2).max())))
assert mask.sum() > 100 and np.isfinite(q).all()
assert np.array_equal(q[frame], raw[frame]) and np.array_equal(q[~mask], raw[~mask])
assert np.array_equal(q[:, 0], raw[:, 0]) and np.array_equal(q[:, 44:], raw[:, 44:])
ob.data = cu.copy(); ob.data.attributes['position'].data.foreach_set('vector', q.astype(np.float32).ravel())
attr = 'native_upper_nested_locks'
ob.data.attributes.new(attr, 'BOOLEAN', 'CURVE').data.foreach_set('value', mask)
ob.data.update_tag(); out.mkdir(parents=True); renders.mkdir(parents=True)
s = bpy.context.scene
pref = bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type = 'OPTIX'; pref.get_devices()
for d in pref.devices: d.use = d.type == 'OPTIX'
s.cycles.device = 'GPU'; s.cycles.samples = 96; s.cycles.use_denoising = False
s.render.resolution_x, s.render.resolution_y = 1200, 1400; s.render.resolution_percentage = 80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam = bpy.data.objects['03_Side'].copy(); cam.data = cam.data.copy()
s.collection.objects.link(cam); cam.name = '05_OppositeSide'
ref = Matrix.Diagonal((-1., 1., 1., 1.)); cam.matrix_world = ref@cam.matrix_world@ref
for shot in ['02_ThreeQuarter', '01_Front', '05_OppositeSide']:
    s.camera = bpy.data.objects[shot]; s.render.filepath = str(renders/(shot+'.png'))
    bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
assert hashlib.sha256(donorpath.read_bytes()).hexdigest() == donorhash
(out/'nested_lock_manifest.json').write_text(json.dumps(dict(source=base, source_sha256=digest, donor=donor, donor_sha256=donorhash,
    changed_fibers=int(mask.sum()), sublocks=len(rows), groups=rows, selection_attribute=attr, discrete_body_repairs=repairs,
    method='Reproduce donor86 150 whole-path groups. Upper-front groups with at least80 fibers split by transverse coordinate at29/68 percentiles;38% within-sublock width contraction, asymmetric1.8mm lateral separation and0.5-2.3mm broad normal loft. Roots/points44-64/foreground/materials/other objects preserved.',
    status='Actual drafts pending artistic review; discrete corrections are not continuous collision validation.'), indent=2), encoding='utf-8')
print('NESTED_LOCKS_SAVED', version, int(mask.sum()), flush=True)
