"""Shorten low lateral tails along their own existing trajectories."""
import bpy, sys, re, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--')+1:]
version, base = a[:2]
gentle = '--gentle' in a
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
threshold = 1.640 if gentle else 1.665
target_center = 1.652 if gentle else 1.676
mask = (~fringe) & (raw[:, -1, 2] < threshold) & (np.abs(raw[:, -1, 0]) > .035) & (raw[:, 11, 2] > 1.700)
ids = np.flatnonzero(mask)
assert len(ids) > 0
t = np.linspace(0, 1, 65)
cut_parameters = []
for index in ids:
    old = raw[index]
    root = old[0]
    target = target_center + .008*np.sin(root[0]*125+root[1]*85)
    crossing = np.flatnonzero(old[12:, 2] < target)[0]+12
    low, high = old[crossing, 2], old[crossing-1, 2]
    fraction = (high-target)/max(high-low, 1e-10)
    cut = (crossing-1+fraction)/64
    assert cut > 11/64 and cut < 1
    cut_parameters.append(cut)
    parameter = np.where(t <= 11/64, t, 11/64+(t-11/64)*(cut-11/64)/(1-11/64))
    values = np.stack([np.interp(parameter, t, old[:, axis]) for axis in range(3)], axis=1)
    values[:12] = old[:12]
    q[index] = values
assert np.isfinite(q).all() and np.array_equal(q[:, :12], raw[:, :12])
assert np.array_equal(q[~mask], raw[~mask]) and np.array_equal(q[fringe], raw[fringe])
ob.data = cu.copy()
ob.data.attributes['position'].data.foreach_set('vector', q.astype(np.float32).ravel())
attr = 'native_lateral_longest_trim' if gentle else 'native_lateral_outlier_trim'
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
(out/'side_trim_manifest.json').write_text(json.dumps(dict(
    source=base, source_sha256=digest, selection_attribute=attr, gentle=gentle,
    changed_fibers=int(mask.sum()), cut_parameter_range=[min(cut_parameters), max(cut_parameters)],
    selected_old_tip_z_range_m=[float(raw[mask, -1, 2].min()), float(raw[mask, -1, 2].max())],
    selected_new_tip_z_range_m=[float(q[mask, -1, 2].min()), float(q[mask, -1, 2].max())],
    method=f'Nonfringe primary tipsZ<{threshold:.3f}m, absolute tipX>35mm andpoint11Z>1.700m. Terminate each own source trajectory at first crossing of root-correlated{target_center:.3f}m+-8mm plane; reparameterize point11 through64, all first12 points exact. No replacement guide, new fibers, offsets or body correction. Radii/topology/current fringe/unselected/othercomponents/materials/lighting retained. Source trajectory interpolation is not continuous collision acceptance or guaranteed reference shape.',
    status='Unreviewed actual lateral-tail shape study'), indent=2), encoding='utf-8')
cam = bpy.data.objects['03_Side'].copy()
cam.data = cam.data.copy()
s.collection.objects.link(cam)
cam.name = '05_OppositeSide'
reflect = Matrix.Diagonal((-1., 1., 1., 1.))
cam.matrix_world = reflect@cam.matrix_world@reflect
for shot in ['02_ThreeQuarter', '04_Back', '03_Side', '05_OppositeSide']:
    s.camera = bpy.data.objects[shot]
    s.render.filepath = str(rd/(shot+'.png'))
    bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
print('NATIVE_LATERAL_TAIL_TRIMMED', version, int(mask.sum()), flush=True)
