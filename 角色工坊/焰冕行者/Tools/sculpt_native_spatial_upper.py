"""Loosen existing upper fall with a smooth root-correlated S-wave field.

Fresh local study only. No new geometry assets, texture or lighting changes.
"""
import bpy, sys, re, json, hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--') + 1:]
version, base = a[:2]
pilot = '--pilot' in a
descending = '--descending' in a
layer_map = '--layer-map' in a
blend = float(a[a.index('--blend') + 1]) if '--blend' in a else 1.
sides_only = '--sides-only' in a
assert 0 < blend <= 1
if layer_map:
    descending = True
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
mask = np.empty(len(raw), bool)
cu.attributes['native_descending_fine_locks'].data.foreach_get('value', mask)
if pilot:
    mask &= (raw[:, 0, 0] > .018) & (raw[:, 0, 2] > 1.800)
if sides_only:
    # Preserve the frontal fall as its own design region: remapped short
    # endings there introduced a visible knot in the inspected full study.
    mask &= (raw[:, 0, 1] > -.035) & (raw[:, -1, 1] > -.015)
    mask &= (np.abs(raw[:, 0, 0]) > .025)
ids = np.flatnonzero(mask)
assert len(ids) > 500
body = bpy.data.objects['CC0 male body • retained topology']
assert np.array_equal(np.array(body.matrix_world), np.eye(4))
bv = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
t = np.linspace(0, 1, 65)
# Smooth onset keeps the existing follicle emergence and first six points.
onset = np.clip((t - t[5])/.20, 0, 1)
onset = onset*onset*(3 - 2*onset)
arch = np.sin(np.pi*t)**2
repairs = 0

def unit(v):
    return v/max(np.linalg.norm(v), 1e-10)

for index in ids:
    old = raw[index]
    root = old[0]
    _, nn, _, _ = bv.find_nearest(Vector(root))
    normal = np.array(nn)
    chord = old[-1] - root
    tangent = chord - normal*chord.dot(normal)
    tangent = unit(tangent)
    lateral = unit(np.cross(tangent, normal))
    # Nearby follicles share broad organic movement, rather than random
    # individual noise or identical mean guide paths.
    phase = root[0]*63 + root[1]*47 + (root[2] - 1.8)*31
    side_amp = .010 + .006*(.5 + .5*np.sin(phase + .9))
    lift = .006 + .007*(.5 + .5*np.cos(phase*.83))
    offset = normal[None, :]*(arch*lift)[:, None]
    offset += lateral[None, :]*(arch*side_amp*np.sin(2*np.pi*t + phase))[:, None]
    # Stagger the ends across a broad root field; avoid outward straight tails.
    offset += lateral[None, :]*(t**4*.008*np.sin(phase*.7))[:, None]
    if descending:
        end = old[-1].copy()
        if layer_map:
            height = np.clip((root[2] - 1.800)/.100, 0, 1)
            side = 1. if root[0] >= 0 else -1.
            end[0] = side*(.078 + .016*height + .006*np.sin(phase*.83))
            end[1] = root[1]*.55 + .022 + .008*np.cos(phase*.71)
            end[2] = root[2] - (.050 + .120*height) + .008*np.sin(phase*.91)
        else:
            end += lateral*(.007*np.sin(phase*.73))
            end[2] += .009*np.sin(phase*.91)
        _, en, _, _ = bv.find_nearest(Vector(end))
        en = np.array(en)
        chord = end - root
        tangent = unit(chord - normal*chord.dot(normal))
        p1 = root + tangent*np.clip(np.linalg.norm(chord)*.48, .035, .075)
        p1 += normal*(.010 + .006*(.5 + .5*np.cos(phase)))
        # Tip tangent is explicitly down, so the body of the lock sweeps
        # over the side and settles vertically rather than arching out.
        p2 = end + np.array([0., 0., .032]) + en*.004
        u = t[:, None]
        shaped = ((1-u)**3*root + 3*(1-u)**2*u*p1
                  + 3*(1-u)*u*u*p2 + u**3*end)
        values = old*(1-onset[:, None]) + shaped*onset[:, None]
    else:
        values = old + onset[:, None]*offset
    values = old + blend*(values - old)
    correction = np.zeros_like(values)
    for j in range(6, 65):
        hit, nn, _, distance = bv.find_nearest(Vector(values[j]))
        gap = (Vector(values[j]) - hit).dot(nn)
        if distance < .025 and gap < .001:
            correction[j] = np.array(nn)*(.0014 - gap)
            repairs += 1
    magnitude = np.linalg.norm(correction, axis=1)
    expanded = correction.copy()
    for j in range(6, 65):
        lo, hi = max(6, j - 4), min(65, j + 5)
        weight = np.maximum(0, 1 - np.abs(np.arange(lo, hi) - j)/5)
        score = magnitude[lo:hi]*weight
        winner = int(np.argmax(score))
        if score[winner] > np.linalg.norm(expanded[j]):
            expanded[j] = correction[lo + winner]*weight[winner]
    values += expanded
    values[:6] = old[:6]
    q[index] = values
assert np.isfinite(q).all() and np.array_equal(q[:, :6], raw[:, :6])
assert np.array_equal(q[~mask], raw[~mask])
ob.data = cu.copy()
ob.data.attributes['position'].data.foreach_set('vector', q.astype(np.float32).ravel())
attr = (('native_remapped_upper_pilot' if pilot else 'native_remapped_upper_layers') if layer_map else ('native_settled_upper_pilot' if pilot else 'native_settled_upper_fall')) if descending else ('native_spatial_upper_pilot' if pilot else 'native_spatial_upper_wave')
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
manifest = dict(source=base, source_sha256=digest, pilot=pilot, sides_only=sides_only, descending=descending, layer_map=layer_map, design_blend=blend,
    selection_attribute=attr, changed_fibers=len(ids), preserved_prefix_points=6,
    intermediate_discrete_body_repairs=repairs,
    maximum_displacement_m=float(np.linalg.norm(q - raw, axis=2).max()),
    method=('Actual133 upper selection. '
            + ('Pilot positive-X roots>18mm/Z>1.800m. ' if pilot else 'Both sides. ')
            + ('Side/rear region limited torootY>-35mm/endY>-15mm/|rootX|>25mm; frontal region retained. ' if sides_only else '')
            + (('Own-root cubic, free layer endpoints from root field:height=clamp((rootZ-1.800)/.100), X=side*(78+16height+6sinphase)mm,Y=.55rootY+22mm+8cosphase,Z=rootZ-(50+120height)mm+8sinphase. '
                if layer_map else 'Own-root cubic, old endpoints staggered7mm laterally/9mm vertically by smooth root field. ')
               + '35-75mm projected root tangent with10-16mm normal lift; terminal control32mm above tip plus4mm local body normal for downward fall. '
               if descending else 'Existing per-fiber paths receive smooth root-correlated broad S field:10-16mm lateral middle amplitude,6-13mm normal lift,8mm lateral end stagger. ')
            + f'Design delta blended{blend:.3f} toward source before sampled body guards. Smooth onset preserves first6 points; no new mean-guide or cross-section transport. Original radii/topology/otherhair/materials/lights unchanged. Discrete1/1.4mm body-point protection with4-point envelope is not continuous collision acceptance.'),
    status='Unreviewed actual geometry study; no aesthetic completion claim')
(out/'spatial_upper_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
cam = bpy.data.objects['03_Side'].copy()
cam.data = cam.data.copy()
s.collection.objects.link(cam)
cam.name = '05_OppositeSide'
reflect = Matrix.Diagonal((-1., 1., 1., 1.))
cam.matrix_world = reflect@cam.matrix_world@reflect
for shot in (['02_ThreeQuarter', '03_Side'] if pilot else
             ['02_ThreeQuarter', '01_Front', '03_Side', '05_OppositeSide']):
    s.camera = bpy.data.objects[shot]
    s.render.filepath = str(rd/(shot + '.png'))
    bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
print('NATIVE_SPATIAL_UPPER_RENDERED', version, len(ids), flush=True)
