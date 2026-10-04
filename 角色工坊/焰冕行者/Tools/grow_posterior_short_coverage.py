"""Independent short posterior fibers sampled on the actual body scalp.

An original anatomical downward/backward flow fills sparse donor-root bands.
No solid cap, image paint, long shell or copied third-party guide geometry.
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
if source_version not in {'rootlayer01', 'rootlayer03'}:
    raise ValueError('Calibrated to reviewed root-layer cuts only')
out, render = ROOT/'Exports'/version, ROOT/'Renders'/version
if out.exists() or render.exists():
    raise RuntimeError('Fresh output required')
source = ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
bpy.context.view_layer.update()
if any(o.name.startswith('Original posterior coverage') and not o.hide_render for o in bpy.data.objects):
    raise RuntimeError('Posterior coverage already present')
body = bpy.data.objects['CC0 male body • retained topology']
if not np.allclose(np.array(body.matrix_world), np.eye(4)):
    raise RuntimeError('World-aligned scalp required')
dg = bpy.context.evaluated_depsgraph_get()
bv = BVHTree.FromObject(body, dg)
evaluated = body.evaluated_get(dg)
mesh = evaluated.to_mesh()
mesh.calc_loop_triangles()
verts = np.array([v.co[:] for v in mesh.vertices], float)
tri = np.array([t.vertices[:] for t in mesh.loop_triangles], int)
xyz = verts[tri]
c = xyz.mean(axis=1)
normals = np.cross(xyz[:, 1]-xyz[:, 0], xyz[:, 2]-xyz[:, 0])
areas = np.linalg.norm(normals, axis=1)*.5
normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-10)
mask = ((c[:, 1]>.004)&(c[:, 2]>1.787)) | ((np.abs(c[:, 0])>.056)&(c[:, 1]>-.042)&(c[:, 2]>1.802))
wide_temples = '--wide-temples' in args
if wide_temples:
    mask = ((c[:, 1]>.004)&(c[:, 2]>1.787)) | ((c[:, 1]>-.077)&(c[:, 2]>1.807))
measured_band = '--measured-band' in args
if measured_band:
    # Actual orthographic-camera ray probes locate the exposed band around
    # z=1.77..1.79m, below the previous assumed z=1.807m selection.
    mask = ((c[:, 1]>.025)&(c[:, 2]>1.754)) | ((c[:, 1]>-.074)&(c[:, 2]>1.773))
# Exclude ear folds and downward-facing triangles from the hair-bearing area.
mask &= (normals[:, 2]>-.45)&(c[:, 2]<1.900)
xyz, areas = xyz[mask], areas[mask]
if len(xyz)<50:
    raise RuntimeError('Posterior scalp selection failed')
rng = np.random.default_rng(100408)
count, N = (36000 if wide_temples or measured_band else 26000), 36
t = np.linspace(0, 1, N)
ids = rng.choice(len(xyz), count, p=areas/areas.sum())
bary = rng.random((count, 2))
bary[bary.sum(axis=1)>1] = 1-bary[bary.sum(axis=1)>1]
samples = xyz[ids, 0]+bary[:, 0, None]*(xyz[ids, 1]-xyz[ids, 0])+bary[:, 1, None]*(xyz[ids, 2]-xyz[ids, 0])
paths = np.empty((count, N, 3), np.float32)
root_gaps = []
for i, sample in enumerate(samples):
    hit, normal, face, dist = bv.find_nearest(Vector(sample))
    root = hit+normal*.0005
    paths[i, 0] = root
    root_gaps.append((root-hit).dot(normal))
    side = np.sign(sample[0])
    heading = Vector((side*.14, .70, -.85))
    heading -= normal*heading.dot(normal)
    if heading.length<1e-7:
        heading = Vector((side*.3, .6, -.2))
        heading -= normal*heading.dot(normal)
    heading.normalize()
    length = rng.uniform(.037, .061)
    lift = rng.uniform(.0015, .0040)
    position = hit
    for j in range(1, N):
        candidate = position+heading*(length/(N-1))
        point, n, face, dist = bv.find_nearest(candidate)
        heading -= n*heading.dot(n)
        if heading.length>1e-8:
            heading.normalize()
        position = point
        gap = .0005+lift*np.sin(np.pi*t[j])+.0012*t[j]
        paths[i, j] = point+n*gap
evaluated.to_mesh_clear()
assert np.isfinite(paths).all()
cu = bpy.data.hair_curves.new('Original anatomical short posterior coverage')
cu.add_curves([N]*count)
cu.attributes['position'].data.foreach_set('vector', paths.ravel())
radius = rng.uniform(.000029, .000042, (count, 1))*(1-.996*t[None, :]**3)**.65
cu.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', radius.astype(np.float32).ravel())
mat = next(o for o in bpy.data.objects if o.type=='CURVES' and o.name.startswith('Root-region shag')).data.materials[0]
cu.materials.append(mat)
ob = bpy.data.objects.new('Original posterior coverage • surface-grown short fibers', cu)
bpy.context.scene.collection.objects.link(ob)
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
    method='Area-sampled real posterior scalp; original anatomical backward/downward flow parallel-transported on surface',
    additional_native_curves=count, points_per_curve=N,
    wide_temple_selection=wide_temples,
    ray_measured_lower_scalp_band=measured_band,
    scalp_area_m2=float(areas.sum()), scalp_triangles=len(xyz),
    root_gap_quantiles_m=np.quantile(root_gaps, [0, .5, 1]).tolist(),
    samples=scene.cycles.samples, draft='--draft' in args, denoising=False,
    status='Unreviewed actual 3D study, not artistic approval',
    license='New short coverage original; previous Ddr Rcs Royalty Free rear, original frontal, Bystedt CC BY-SA support and Abhay Pratap Royalty Free flow-derived support retained',
    collision_scope='Root/surface attachment only; not exhaustive hair/clothing/motion validation')
(out/'posterior_coverage_manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front', '02_ThreeQuarter', '03_Side', '04_Back']:
    scene.camera = bpy.data.objects[name]
    scene.render.filepath = str(render/(name+'.png'))
    bpy.ops.render.render(write_still=True)
print('POSTERIOR_SHORT_COVERAGE_RENDERED', version, flush=True)
