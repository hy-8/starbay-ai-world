"""Round existing flat shaft groups in their local section, retaining scalp coverage."""
import bpy, sys, re, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--') + 1:]
version, base = a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+', v) for v in a[:2])
out, renders = ROOT/'Exports'/version, ROOT/'Renders'/version
assert not out.exists() and not renders.exists()
source = ROOT/'Exports'/base/'Ember_Regent.blend'
digest = hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
ob = bpy.data.objects['Bystedt layercut derivative • native root reflow']
cu = ob.data
p = np.empty((len(cu.points), 3), np.float32)
cu.attributes['position'].data.foreach_get('vector', p.ravel())
raw = p.reshape(-1, 65, 3).astype(float)
q = raw.copy()
roots = raw[:, 0]
eligible = np.flatnonzero(roots[:, 2] > 1.800)
# Group by whole shaft direction, not ten broad shared root zones.
features = (raw[eligible][:, [0, 8, 24, 40, 64]] *
            np.array([.8, 1., 1., .8, .55])[None, :, None]).reshape(len(eligible), -1)
K = 180
centers = [features[len(features)//2]]
best = np.full(len(features), np.inf)
for _ in range(1, K):
    best = np.minimum(best, np.sum((features-centers[-1])**2, axis=1))
    centers.append(features[np.argmax(best)])
centers = np.array(centers)
def assign():
    return np.argmin(np.maximum(0, (features*features).sum(1)[:, None] +
        (centers*centers).sum(1)[None] - 2*features@centers.T), axis=1)
for _ in range(20):
    labels = assign()
    for k in range(K):
        if (labels == k).any():
            centers[k] = features[labels == k].mean(0)
labels = assign()
body = bpy.data.objects['CC0 male body • retained topology']
assert np.array_equal(np.array(body.matrix_world), np.eye(4))
bv = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
t = np.linspace(0, 1, 65)
def smooth(x):
    x = np.clip(x, 0, 1)
    return x*x*(3-2*x)
mask = np.zeros(len(raw), bool)
rows = []
repairs = 0
for k in range(K):
    ids = eligible[labels == k]
    if len(ids) < 24:
        continue
    old = raw[ids]
    c = old.mean(0)
    tangent = np.gradient(c, axis=0)
    tangent /= np.maximum(np.linalg.norm(tangent, axis=1)[:, None], 1e-9)
    normals = []
    for point in c:
        hit, n, _, dist = bv.find_nearest(Vector(point))
        normals.append(np.array(n))
    normal = np.array(normals)
    normal -= (normal*tangent).sum(1)[:, None]*tangent
    normal /= np.maximum(np.linalg.norm(normal, axis=1)[:, None], 1e-9)
    across = np.cross(tangent, normal)
    # Source cross-section gives continuous coherent membership across the path.
    dev = old-c
    lateral = (dev*across[None]).sum(2)
    depth = (dev*normal[None]).sum(2)
    along = (dev*tangent[None]).sum(2)
    order = np.argsort(lateral[:, 24:40].mean(1), kind='stable')
    rank = np.empty(len(ids), float)
    rank[order] = (np.arange(len(ids))+.5)/len(ids)
    diskx = 2*rank-1
    # Paired upper/lower disk positions stop the group becoming a flat ribbon.
    azimuth = ids*2.3999632297
    diskz = np.sqrt(np.maximum(0, 1-diskx*diskx))*np.sin(azimuth)
    width = np.clip(np.quantile(np.abs(lateral[:, 16:48]), .80), .0023, .006)
    phi = k*2.3999632297
    taper = 1-.82*smooth((t-.45)/.55)
    blend = .88*smooth((t-.09)/.26)
    # Preserve all entry directions and source coverage before point6.
    new_lateral = diskx[:, None]*width*taper[None]
    new_depth = diskz[:, None]*(.002+.001*(.5+.5*np.sin(phi)))*taper[None]
    section = (new_lateral-lateral)[:, :, None]*across[None]
    section += (new_depth-depth)[:, :, None]*normal[None]
    values = old+section*blend[None, :, None]
    lift = (.002+.004*(.5+.5*np.sin(phi*.71))) * np.sin(np.pi*t)**2
    sway = .0025*np.sin(phi)*np.sin(np.pi*t)**2
    values += lift[None, :, None]*normal[None]+sway[None, :, None]*across[None]
    # Tail length differs among locks and shafts, without flattening the entry.
    tail = (.0025*np.sin(phi*.53)+.0015*np.sin(azimuth))*smooth((t-.66)/.34)[:, None]
    values += (tail.T[:, :, None])*tangent[None]
    for i in range(len(ids)):
        for j in range(6, 65):
            hit, n, _, dist = bv.find_nearest(Vector(values[i, j]))
            gap = (Vector(values[i, j])-hit).dot(n)
            if dist < .03 and gap < .0005:
                values[i, j] += np.array(n)*(.0007-gap)
                repairs += 1
    values[:, :6] = old[:, :6]
    q[ids] = values
    mask[ids] = True
    rows.append(dict(group=k, fibers=len(ids), section_half_width_m=float(width),
        maximum_displacement_m=float(np.linalg.norm(values-old, axis=2).max())))
assert np.isfinite(q).all() and np.array_equal(q[:, :6], raw[:, :6])
assert np.array_equal(q[~mask], raw[~mask]) and (q[:, -1, 2] < 1.640).sum() == 0
ob.data = cu.copy()
ob.data.attributes['position'].data.foreach_set('vector', q.astype(np.float32).ravel())
attr = 'native_volumetric_sections'
ob.data.attributes.new(attr, 'BOOLEAN', 'CURVE').data.foreach_set('value', mask)
ob.data.update_tag()
out.mkdir(parents=True)
renders.mkdir(parents=True)
s = bpy.context.scene
pref = bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type = 'OPTIX'
pref.get_devices()
for d in pref.devices:
    d.use = d.type == 'OPTIX'
s.cycles.device = 'GPU'
s.cycles.samples = 96
s.cycles.use_denoising = False
s.render.resolution_x, s.render.resolution_y = 1200, 1400
s.render.resolution_percentage = 80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam = bpy.data.objects['03_Side'].copy()
cam.data = cam.data.copy()
s.collection.objects.link(cam)
cam.name = '05_OppositeSide'
ref = Matrix.Diagonal((-1., 1., 1., 1.))
cam.matrix_world = ref@cam.matrix_world@ref
for shot in ['02_ThreeQuarter', '01_Front', '03_Side', '05_OppositeSide']:
    s.camera = bpy.data.objects[shot]
    s.render.filepath = str(renders/(shot+'.png'))
    bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
(out/'volume_manifest.json').write_text(json.dumps(dict(source=base, source_sha256=digest,
    selection_attribute=attr, changed_fibers=int(mask.sum()), groups=rows,
    discrete_body_repairs=repairs, method='180 whole-path groups, actual crown/fringe follicles Z>1.800m. Rounded elliptical cross sections, 2.3-6mm half width, 2-3mm depth, separate source-ranked shaft membership, 2-6mm central relief, varied tapered tails. First6 points, radii/topology/materials and other components retained.',
    status='Actual draft review pending; discrete guards not continuous collision or art acceptance'), indent=2), encoding='utf-8')
print('NATIVE_VOLUME_SCULPTED', version, int(mask.sum()), len(rows), flush=True)
