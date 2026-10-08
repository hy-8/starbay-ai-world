"""Source-path layered posterior with a root-correlated soft wave field.

This is a shape study, not a collision or aesthetic completion certificate.
"""
import bpy, sys, re, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--') + 1:]
version, base = a[:2]
pilot = '--pilot' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+', v) for v in a[:2])
out, rd = ROOT/'Exports'/version, ROOT/'Renders'/version
assert not out.exists() and not rd.exists()
source = ROOT/'Exports'/base/'Ember_Regent.blend'
digest = hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
ob = bpy.data.objects['Bystedt layercut derivative • native root reflow']
cu = ob.data
p = np.empty((len(cu.points), 3), np.float32)
cu.attributes['position'].data.foreach_get('vector', p.ravel())
raw = p.reshape(-1, 65, 3).astype(float)
q = raw.copy()
fringe = np.empty(len(raw), bool)
cu.attributes['native_resculpted_fringe_sweeps'].data.foreach_get('value', fringe)
lengths = np.linalg.norm(np.diff(raw, axis=1), axis=2).sum(1)
mask = (~fringe) & (raw[:, 0, 1] > .015) & (raw[:, 32, 1] > .035) & (lengths > .045)
if pilot:
    mask &= raw[:, 0, 0] < -.010
ids = np.flatnonzero(mask)
assert len(ids) > 500
body = bpy.data.objects['CC0 male body • retained topology']
assert np.array_equal(np.array(body.matrix_world), np.eye(4))
bv = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
t = np.linspace(0, 1, 65)

def smooth(v):
    v = np.clip(v, 0, 1)
    return v*v*(3-2*v)

envelope = smooth((t-11/64)/(1-11/64))
repairs = 0
rates = []
for index in ids:
    old = raw[index]
    root = old[0]
    phase = root[0]*110 + root[1]*80
    high = float(smooth((root[2]-1.748)/.090))
    rate = float(np.clip(.88-.18*high+.065*np.sin(phase), .65, .97))
    rates.append(rate)
    parameter = np.where(t <= 11/64, t, 11/64+(t-11/64)*(rate-11/64)/(1-11/64))
    values = np.stack([np.interp(parameter, t, old[:, axis]) for axis in range(3)], axis=1)
    # Smooth spatial fields vary between neighbouring root territories,
    # retaining each shaft's original trajectory and true root prefix.
    radial = np.array([root[0], root[1]+.035, 0.])
    radial /= max(np.linalg.norm(radial), 1e-9)
    lateral = np.array([-radial[1], radial[0], 0.])
    wave = np.sin(np.pi*envelope)*np.sin(phase+2.6*envelope)
    values += lateral[None, :]*(.008*wave[:, None])
    relief = (.004+.004*(.5+.5*np.cos(phase)))*np.sin(np.pi*envelope)
    values += radial[None, :]*relief[:, None]
    tip = lateral*.005*np.sin(phase+.9)+radial*.005
    tip[2] = .005*np.sin(phase-1.1)
    values += envelope[:, None]*tip[None, :]
    correction = np.zeros_like(values)
    for j in range(12, 65):
        hit, normal, _, distance = bv.find_nearest(Vector(values[j]))
        gap = (Vector(values[j])-hit).dot(normal)
        if distance < .025 and gap < .001:
            correction[j] = np.array(normal)*(.0014-gap)
            repairs += 1
    magnitudes = np.linalg.norm(correction, axis=1)
    expanded = correction.copy()
    for j in range(12, 65):
        lo, hi = max(12, j-3), min(65, j+4)
        weight = np.maximum(0, 1-np.abs(np.arange(lo, hi)-j)/4)
        scores = magnitudes[lo:hi]*weight
        winner = int(np.argmax(scores))
        if scores[winner] > np.linalg.norm(expanded[j]):
            expanded[j] = correction[lo+winner]*weight[winner]
    values += expanded
    values[:12] = old[:12]
    q[index] = values
assert np.isfinite(q).all() and np.array_equal(q[:, :12], raw[:, :12])
assert np.array_equal(q[~mask], raw[~mask]) and np.array_equal(q[fringe], raw[fringe])
ob.data = cu.copy()
ob.data.attributes['position'].data.foreach_set('vector', q.astype(np.float32).ravel())
attr = 'native_posterior_wave_pilot' if pilot else 'native_posterior_soft_wave'
assert not ob.data.attributes.get(attr)
ob.data.attributes.new(attr, 'BOOLEAN', 'CURVE').data.foreach_set('value', mask)
ob.data.update_tag()
out.mkdir(parents=True)
rd.mkdir(parents=True)
s = bpy.context.scene
pref = bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type = 'OPTIX'
pref.get_devices()
for device in pref.devices:
    device.use = device.type == 'OPTIX'
s.cycles.device = 'GPU'
s.cycles.samples = 96
s.cycles.use_denoising = False
s.render.resolution_x, s.render.resolution_y = 1200, 1400
s.render.resolution_percentage = 80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
(out/'posterior_wave_manifest.json').write_text(json.dumps(dict(
    source=base, source_sha256=digest, pilot=pilot, selection_attribute=attr,
    changed_fibers=int(mask.sum()), parameter_rate_range=[min(rates), max(rates)],
    discrete_body_repairs=repairs, maximum_displacement_m=float(np.linalg.norm(q-raw, axis=2).max()),
    method='Nonfringe primary rootsY>15mm, midpointY>35mm, arc length>45mm; pilot restricts rootsX<-10mm. Each own source path resampled with root-correlated .65-.97 parameter cut, first12 points exact. Smooth lateral up to8mm/normal4-8mm midlength wave, up to5mm endpoint lateral/outward/vertical offsets. Roots/radii/topology/current fringe/other components/materials/lighting retained. 1/1.4mm discrete body guard expanded3points, not continuous collision proof. Path parameter cut is not an arc-length guarantee.',
    status='Unreviewed actual shape study; not reference complete'), indent=2), encoding='utf-8')
cam = bpy.data.objects['03_Side'].copy()
cam.data = cam.data.copy()
s.collection.objects.link(cam)
cam.name = '05_OppositeSide'
reflect = Matrix.Diagonal((-1., 1., 1., 1.))
cam.matrix_world = reflect@cam.matrix_world@reflect
for shot in (['04_Back', '02_ThreeQuarter'] if pilot else ['04_Back', '02_ThreeQuarter', '03_Side', '05_OppositeSide']):
    s.camera = bpy.data.objects[shot]
    s.render.filepath = str(rd/(shot+'.png'))
    bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
print('NATIVE_POSTERIOR_WAVE_RENDERED', version, int(mask.sum()), flush=True)
