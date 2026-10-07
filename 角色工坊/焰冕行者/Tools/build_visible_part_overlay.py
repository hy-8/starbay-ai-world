"""Camera-attributed local hair overlay using continuous saved donor paths.

Source and derived geometry stay local. This is a geometric prototype, not an
AI-generated portrait or a motion/continuous-collision validation.
"""
import bpy, sys, re, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
args = sys.argv[sys.argv.index('--') + 1:]
version, base, probe = args[:3]
assert all(re.fullmatch(r'[A-Za-z0-9_-]+', x) for x in args[:3])
out, renders = ROOT/'Exports'/version, ROOT/'Renders'/version
assert not out.exists() and not renders.exists(), 'Use a fresh version'
source = ROOT/'Exports'/base/'Ember_Regent.blend'
digest = hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
bpy.context.view_layer.update()

def paths(ob):
    counts = np.array([c.points_length for c in ob.data.curves])
    assert (counts == counts[0]).all()
    assert np.array_equal(np.array(ob.matrix_world), np.eye(4))
    p = np.empty((len(ob.data.points), 3), np.float32)
    ob.data.attributes['position'].data.foreach_get('vector', p.ravel())
    return p.reshape(-1, int(counts[0]), 3).astype(float)

support = bpy.data.objects['Abhay flow derivative • real scalp sampled short support']
main_ob = bpy.data.objects['Bystedt layercut derivative • native root reflow']
raw, main = paths(support), paths(main_ob)
report = json.loads((ROOT/'Exports'/probe/'visible_crown_probe.json').read_text())
assert report['source_sha256'] == digest and report['part_roi']
assert report['records'][0]['object'] == support.name
visible = np.load(ROOT/'Exports'/probe/'local_visible_crown_indices.npz')['0']
roots = raw[visible, 0]
selected = visible[(roots[:, 0] > .025) & (roots[:, 1] < -.060) & (roots[:, 2] > 1.810)]
assert len(selected) > 100
# A single entire trajectory per follicle; no changing nearest-point field.
donors = np.flatnonzero((main[:, -1, 0] > .055) & (main[:, -1, 2] < 1.820))
lookup = []
for i in donors:
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(main[i], axis=0), axis=1))]
    lookup.extend((int(i), j) for j in range(0, 41, 4) if arc[-1]-arc[j] > .065)
tree = KDTree(len(lookup))
for k, (i, j) in enumerate(lookup): tree.insert(Vector(main[i, j]), k)
tree.balance()
body = bpy.data.objects['CC0 male body • retained topology']
bv = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
t = np.linspace(0, 1, 65)
q, radii, distances, lengths = [], [], [], []
repairs = 0
for i in selected:
    root = raw[i, 0]
    direction = raw[i, -1]-root
    direction /= max(np.linalg.norm(direction), 1e-9)
    options = []
    for _, k, distance in tree.find_n(Vector(root), 32):
        donor, j = lookup[k]
        path = main[donor, j:]
        arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
        forward = path[min(6, len(path)-1)]-path[0]
        forward /= max(np.linalg.norm(forward), 1e-9)
        options.append((distance+.004*(1-np.dot(direction, forward)), distance, path, arc))
    _, distance, path, arc = min(options, key=lambda x: x[0])
    if distance > .018: continue
    phase = i*2.399963
    length = min(arc[-1]*.93, .085+.035*(.5+.5*np.sin(phase)))
    at = t*length
    v = np.column_stack([np.interp(at, arc, path[:, k]) for k in range(3)])
    fade = np.clip(1-at/.030, 0, 1)
    fade = fade*fade*(3-2*fade)
    v += (root-path[0])[None]*fade[:, None]
    normals = np.array([bv.find_nearest(Vector(p))[1][:] for p in v])
    normals = np.vstack([normals[0], (normals[:-2]+normals[1:-1]+normals[2:])/3, normals[-1]])
    normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-9)
    v += normals*(.0018*np.sin(np.pi*t))[..., None]
    for j in range(1, 65):
        hit, n, _, dist = bv.find_nearest(Vector(v[j]))
        gap = (Vector(v[j])-hit).dot(n)
        if dist < .020 and gap < .0005:
            v[j] += np.array(n)*(.0007-gap)
            repairs += 1
    v[0] = root
    q.append(v)
    radii.append(.000032*(.82+.18*np.sin(phase)**2)*(1-.94*t**2.8))
    distances.append(distance)
    lengths.append(np.linalg.norm(np.diff(v, axis=0), axis=1).sum())
q, radii = np.array(q, np.float32), np.array(radii, np.float32)
assert len(q)>100 and np.isfinite(q).all() and (radii>0).all()
cu = bpy.data.hair_curves.new('Actual camera ROI transition overlay')
cu.add_curves([65]*len(q))
cu.attributes['position'].data.foreach_set('vector', q.ravel())
cu.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', radii.ravel())
cu.materials.append(main_ob.data.materials[0])
ob = bpy.data.objects.new('Abhay part transition • continuous overlay', cu)
assert ob.name == 'Abhay part transition • continuous overlay'
bpy.context.scene.collection.objects.link(ob)
out.mkdir(parents=True); renders.mkdir(parents=True)
s = bpy.context.scene
pref = bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX'; pref.get_devices()
for device in pref.devices: device.use=device.type=='OPTIX'
s.cycles.device='GPU'; s.cycles.samples=96; s.cycles.use_denoising=False
s.render.resolution_x, s.render.resolution_y=1200, 1400
s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['02_ThreeQuarter', '01_Front', '03_Side']:
    s.camera=bpy.data.objects[name]
    s.render.filepath=str(renders/(name+'.png'))
    bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
manifest = dict(source=base, source_sha256=digest, probe=probe,
    added_object=ob.name, added_fibers=len(q), selected_visible_roots=len(selected),
    entry_distance_quantiles_m=np.quantile(distances,[0,.5,.9,1]).tolist(),
    final_length_quantiles_m=np.quantile(lengths,[0,.5,.9,1]).tolist(),
    discrete_body_repairs=repairs, all_existing_hair_and_meshes_retained=True,
    method='Actual ThreeQuarter ROI Abhay owners, positive-X/front roots; nearest of32 eligible saved continuous side paths, 85-120mm with tapered radii and 1.8mm lift. Each path entry translated to its exact source follicle, fading over30mm. Existing geometry retained.',
    status='Actual draft review pending',
    scope='Approximate point visibility and discrete body protection; not artistic, continuous hair/eye/clothing or animation collision acceptance',
    license='Source follicles and derived geometry remain local; no new source or license')
(out/'part_transition_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('VISIBLE_PART_OVERLAY_SAVED',version,len(q),flush=True)
