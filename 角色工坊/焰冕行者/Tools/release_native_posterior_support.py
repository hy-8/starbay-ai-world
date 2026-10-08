"""Re-style existing middle posterior support into free-tip covering layers."""
import bpy, sys, re, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--')+1:]
version, base = a[:2]
pilot = '--pilot' in a
outer_layer = '--outer-layer' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+', v) for v in a[:2])
out, rd = ROOT/'Exports'/version, ROOT/'Renders'/version
assert not out.exists() and not rd.exists()
source = ROOT/'Exports'/base/'Ember_Regent.blend'
digest = hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
ob = bpy.data.objects['Original posterior coverage • surface-grown short fibers']
assert np.array_equal(np.array(ob.matrix_world), np.eye(4))
cu = ob.data
counts = np.array([c.points_length for c in cu.curves])
assert (counts == counts[0]).all()
N = int(counts[0])
p = np.empty((len(cu.points), 3), np.float32)
cu.attributes['position'].data.foreach_get('vector', p.ravel())
raw = p.reshape(-1, N, 3).astype(float)
q = raw.copy()
r = raw[:, 0]
mask = (r[:, 1] > .015) & (r[:, 2] > 1.800) & (r[:, 2] < 1.855) & (np.abs(r[:, 0]) < .070)
if pilot: mask &= r[:, 0] < -.005
ids = np.flatnonzero(mask)
assert len(ids) > 200
body = bpy.data.objects['CC0 male body • retained topology']
bv = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
t = np.linspace(0, 1, N)
u = t[:, None]

def unit(v): return v/max(np.linalg.norm(v), 1e-10)
def smooth(v):
    v = np.clip(v, 0, 1)
    return v*v*(3-2*v)

blend = smooth((t-3/(N-1))/.20)[:, None]
repairs = end_moves = 0
lengths = []
for index in ids:
    old = raw[index]
    root = old[0]
    hit, normal, _, _ = bv.find_nearest(Vector(root))
    normal = np.array(normal)
    phase = root[0]*145+root[1]*100
    heading = unit(np.array([.28*np.sin(phase)+.14, .22, -.96]))
    tangent = heading-normal*np.dot(heading, normal)
    tangent = unit(tangent)
    length = .075+.035*float(smooth((root[2]-1.800)/.055))+.009*np.sin(phase+.7)
    end = root+heading*length
    hit, nn, _, distance = bv.find_nearest(Vector(end))
    gap = (Vector(end)-hit).dot(nn)
    end_threshold, end_clearance = (.018, .022) if outer_layer else (.006, .008)
    if distance < .045 and gap < end_threshold:
        end += np.array(nn)*(end_clearance-gap)
        end_moves += 1
    chord = end-root
    lead = .026+.012*float(smooth((root[2]-1.800)/.055))
    lift = (.016+.010*(.5+.5*np.sin(phase))) if outer_layer else (.006+.004*(.5+.5*np.sin(phase)))
    p1 = root+tangent*lead+normal*lift
    p2 = end-.27*chord+normal*(.014 if outer_layer else .005)
    new = (1-u)**3*root+3*(1-u)**2*u*p1+3*(1-u)*u*u*p2+u**3*end
    if outer_layer:
        lateral = unit(np.cross(tangent, normal))
        new += lateral[None, :]*(.010*np.sin(2.4*np.pi*t+phase)*np.sin(np.pi*t)**1.5)[:, None]
    # Each own true root, spatially correlated heading/end length, no group
    # averaging or new root sampling. Current roots and first4 points survive.
    values = old*(1-blend)+new*blend
    correction = np.zeros_like(values)
    for j in range(4, N):
        hit, nn, _, distance = bv.find_nearest(Vector(values[j]))
        gap = (Vector(values[j])-hit).dot(nn)
        if distance < .035 and gap < .001:
            correction[j] = np.array(nn)*(.0014-gap)
            repairs += 1
    magnitudes = np.linalg.norm(correction, axis=1)
    expanded = correction.copy()
    for j in range(4, N):
        lo, hi = max(4, j-2), min(N, j+3)
        weight = np.maximum(0, 1-np.abs(np.arange(lo, hi)-j)/3)
        scores = magnitudes[lo:hi]*weight
        winner = int(np.argmax(scores))
        if scores[winner] > np.linalg.norm(expanded[j]):
            expanded[j] = correction[lo+winner]*weight[winner]
    values += expanded
    values[:4] = old[:4]
    q[index] = values
    lengths.append(float(np.linalg.norm(np.diff(values, axis=0), axis=1).sum()))
assert np.isfinite(q).all() and np.array_equal(q[:, :4], raw[:, :4])
assert np.array_equal(q[~mask], raw[~mask])
ob.data = cu.copy()
ob.data.attributes['position'].data.foreach_set('vector', q.astype(np.float32).ravel())
attr = ('native_posterior_outer_pilot' if pilot else 'native_posterior_outer_layers') if outer_layer else ('native_posterior_support_pilot' if pilot else 'native_posterior_free_support')
assert not ob.data.attributes.get(attr)
ob.data.attributes.new(attr, 'BOOLEAN', 'CURVE').data.foreach_set('value', mask)
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
(out/'posterior_support_manifest.json').write_text(json.dumps(dict(
    source=base, source_sha256=digest, changed_object=ob.name, pilot=pilot, outer_layer=outer_layer,
    selection_attribute=attr, changed_fibers=len(ids), points_per_curve=N,
    relocated_designed_endpoints=end_moves, intermediate_discrete_body_repairs=repairs,
    actual_length_quantiles_m=np.quantile(lengths, [0, .5, .9, 1]).tolist(),
    method='Existing original support rootsY>15mm, Z(1.800,1.855)m, absoluteX<70mm; pilot limits rootsX<-5mm. Each own true-root cubic has spatially correlated sideways/downward heading,75-110mm plus+-9mm design chord before endpoint body relocation and26-38mm tangent lead. First4 points exact;20% transition blend. Same fiber count/radii/materials and all other objects retained. Interior1/1.4mm sampled body guard; not continuous collision or artistic approval.',
    design_controls=dict(lead_lift_range_m=[.016,.026] if outer_layer else [.006,.010], terminal_control_normal_lift_m=.014 if outer_layer else .005, added_lateral_wave_m=.010 if outer_layer else 0., endpoint_threshold_m=end_threshold, endpoint_clearance_m=end_clearance),
    status='Actual drafts pending aesthetic inspection'), indent=2), encoding='utf-8')
cam = bpy.data.objects['03_Side'].copy()
cam.data = cam.data.copy()
s.collection.objects.link(cam)
cam.name = '05_OppositeSide'
reflect = Matrix.Diagonal((-1., 1., 1., 1.))
cam.matrix_world = reflect@cam.matrix_world@reflect
for shot in (['04_Back', '05_OppositeSide'] if pilot else ['04_Back', '03_Side', '05_OppositeSide', '02_ThreeQuarter']):
    s.camera = bpy.data.objects[shot]
    s.render.filepath = str(rd/(shot+'.png'))
    bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
print('NATIVE_POSTERIOR_SUPPORT_RELEASED', version, len(ids), flush=True)
