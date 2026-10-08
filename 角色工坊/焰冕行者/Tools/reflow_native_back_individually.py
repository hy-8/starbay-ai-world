"""Own-root/end posterior fall with root-correlated loose wave controls."""
import bpy, sys, re, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
ROOT = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--')+1:]
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
def flag(n):
    v = np.empty(len(raw), bool)
    cu.attributes[n].data.foreach_get('value', v)
    return v
fringe, upper = flag('native_resculpted_fringe_sweeps'), flag('native_descending_fine_locks')
mask = (~(fringe|upper)) & (raw[:, 0, 1] > -.008) & (raw[:, 32, 1] > .025)
if pilot: mask &= raw[:, 0, 0] < -.005
ids = np.flatnonzero(mask)
assert len(ids) > 200
body = bpy.data.objects['CC0 male body • retained topology']
assert np.array_equal(np.array(body.matrix_world), np.eye(4))
bv = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
t = np.linspace(0, 1, 65)
u = t[:, None]
bulge = np.sin(np.pi*t)**1.5
repairs = end_moves = 0
def unit(v): return v/max(np.linalg.norm(v), 1e-10)
for index in ids:
    old = raw[index]
    root, end = old[0].copy(), old[-1].copy()
    hit, nn, _, distance = bv.find_nearest(Vector(end))
    gap = (Vector(end)-hit).dot(nn)
    if distance < .025 and gap < .0018:
        end += np.array(nn)*(.0022-gap)
        end_moves += 1
    hit, normal, _, _ = bv.find_nearest(Vector(root))
    normal = np.array(normal)
    chord = end-root
    tangent = chord-normal*chord.dot(normal)
    if np.linalg.norm(tangent) < .003: tangent = old[10]-root
    tangent = unit(tangent)
    lateral = unit(np.cross(tangent, normal))
    phase = root[0]*130+root[1]*95+root[2]*75
    lead = float(np.clip(np.linalg.norm(chord)*.35, .018, .045))
    relief = .009+.006*(.5+.5*np.sin(phase))
    p1 = root+tangent*lead+normal*relief
    p2 = end-.30*chord+normal*.008+lateral*(.008*np.sin(phase+.8))
    values = (1-u)**3*root+3*(1-u)**2*u*p1+3*(1-u)*u*u*p2+u**3*end
    values += normal[None, :]*(bulge*(.005+.004*(.5+.5*np.cos(phase))))[:, None]
    values += lateral[None, :]*(bulge*.009*np.sin(2.4*np.pi*t+phase))[:, None]
    correction = np.zeros_like(values)
    for j in range(1, 64):
        hit, nn, _, distance = bv.find_nearest(Vector(values[j]))
        gap = (Vector(values[j])-hit).dot(nn)
        if distance < .025 and gap < .001:
            correction[j] = np.array(nn)*(.0014-gap)
            repairs += 1
    magnitudes = np.linalg.norm(correction, axis=1)
    expanded = correction.copy()
    for j in range(1, 64):
        lo, hi = max(1, j-4), min(64, j+5)
        weight = np.maximum(0, 1-np.abs(np.arange(lo, hi)-j)/5)
        scores = magnitudes[lo:hi]*weight
        winner = int(np.argmax(scores))
        if scores[winner] > np.linalg.norm(expanded[j]):
            expanded[j] = correction[lo+winner]*weight[winner]
    values += expanded
    values[0], values[-1] = root, end
    q[index] = values
assert np.isfinite(q).all() and np.array_equal(q[:, 0], raw[:, 0])
assert np.array_equal(q[~mask], raw[~mask]) and np.array_equal(q[fringe|upper], raw[fringe|upper])
ob.data = cu.copy()
ob.data.attributes['position'].data.foreach_set('vector', q.astype(np.float32).ravel())
attr = 'native_individual_back_pilot' if pilot else 'native_individual_back_fall'
assert not ob.data.attributes.get(attr)
ob.data.attributes.new(attr, 'BOOLEAN', 'CURVE').data.foreach_set('value', mask)
ob.data.update_tag()
out.mkdir(parents=True)
rd.mkdir(parents=True)
s = bpy.context.scene
pref = bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type = 'OPTIX'
pref.get_devices()
for device in pref.devices: device.use = device.type == 'OPTIX'
s.cycles.device = 'GPU'
s.cycles.samples = 96
s.cycles.use_denoising = False
s.render.resolution_x, s.render.resolution_y = 1200, 1400
s.render.resolution_percentage = 80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
(out/'individual_back_manifest.json').write_text(json.dumps(dict(
    source=base, source_sha256=digest, pilot=pilot, selection_attribute=attr,
    changed_fibers=len(ids), designed_endpoint_relocations=end_moves,
    intermediate_discrete_body_repairs=repairs,
    method='Nonfringe/non133-upper primary rootsY>-8mm andmidpointY>25mm; pilot restricts rootsX<-5mm. Each own-root/end cubic:18-45mm projected tangent lead,9-15mm normal lead lift,8mm endpoint control normal/lateral phase. Midpath5-9mm normal bow and9mm root-correlated loose lateral wave. Endpoints only2.2mm body relocation allowed; current roots/radii/topology/fringe/upper/otherhair/materials/lighting retained. Discrete1/1.4mm sampled body guard with4-point envelope, not continuous collision or art acceptance.',
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
print('NATIVE_INDIVIDUAL_BACK_RENDERED', version, len(ids), flush=True)
