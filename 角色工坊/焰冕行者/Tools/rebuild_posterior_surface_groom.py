"""Original posterior guide patches distributed over real scalp triangles.

Replaces the donor rear in a fresh copy. Retains frontal design and the short
surface-grown coverage. Geometry must be judged in all rendered views.
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
if source_version != 'rootlayer06':
    raise ValueError('Requires reviewed measured-band coverage checkpoint')
out, render = ROOT/'Exports'/version, ROOT/'Renders'/version
if out.exists() or render.exists():
    raise RuntimeError('Fresh output required')
source = ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
bpy.context.view_layer.update()
rear = next(o for o in bpy.data.objects if o.name.startswith('Root-region shag') and not o.hide_render)
if not any(o.name.startswith('Original posterior coverage') and not o.hide_render for o in bpy.data.objects):
    raise RuntimeError('Independent short scalp coverage required')
body = bpy.data.objects['CC0 male body • retained topology']
if not np.allclose(np.array(body.matrix_world), np.eye(4)):
    raise RuntimeError('World-aligned scalp required')
dg = bpy.context.evaluated_depsgraph_get()
bv = BVHTree.FromObject(body, dg)
evaluated = body.evaluated_get(dg)
mesh = evaluated.to_mesh()
mesh.calc_loop_triangles()
v = np.array([v.co[:] for v in mesh.vertices], float)
tri = np.array([t.vertices[:] for t in mesh.loop_triangles], int)
xyz = v[tri]
c = xyz.mean(axis=1)
n = np.cross(xyz[:, 1]-xyz[:, 0], xyz[:, 2]-xyz[:, 0])
area = np.linalg.norm(n, axis=1)*.5
n /= np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-10)
mask = ((c[:, 1]>.025)&(c[:, 2]>1.754)) | ((c[:, 1]>-.074)&(c[:, 2]>1.773))
mask &= (n[:, 2]>-.45)&(c[:, 2]<1.900)
xyz, area = xyz[mask], area[mask]
rng = np.random.default_rng(100409)
soft_nape = '--soft-nape' in args
if soft_nape and '--long-nape' not in args:
    raise ValueError('Soft-nape requires long-nape')
count, N, guide_count = 64000, 64, (240 if soft_nape else 160)
t = np.linspace(0, 1, N)
ids = rng.choice(len(xyz), count, p=area/area.sum())
bary = rng.random((count, 2))
bary[bary.sum(axis=1)>1] = 1-bary[bary.sum(axis=1)>1]
roots = xyz[ids, 0]+bary[:, 0, None]*(xyz[ids, 1]-xyz[ids, 0])+bary[:, 1, None]*(xyz[ids, 2]-xyz[ids, 0])
# Irregular farthest-point guide roots span the surface; not two donor bands.
pool = roots[::16]
selected = [int(rng.integers(len(pool)))]
nearest_distance = np.full(len(pool), np.inf)
while len(selected)<guide_count:
    d = np.sum((pool-pool[selected[-1]])**2, axis=1)
    nearest_distance = np.minimum(nearest_distance, d)
    selected.append(int(np.argmax(nearest_distance)))
guide_roots = pool[selected]
guides = []
lengths = []
long_nape = '--long-nape' in args
for gi, root in enumerate(guide_roots):
    hit, normal, face, dist = bv.find_nearest(Vector(root))
    side = 1 if root[0]>=0 else -1
    upper = np.clip((root[2]-1.790)/.068, 0, 1)
    neck = (1-upper)*np.clip((root[1]-.010)/.040, 0, 1)
    length = .070+.027*(.5+.5*np.sin(gi*2.399))+neck*(.048+.022*np.exp(-(root[0]/.055)**2))
    heading = Vector((side*.65, .45, -.85))
    if long_nape:
        length = .070+.027*(.5+.5*np.sin(gi*2.399))+neck*(.090+.055*np.exp(-(root[0]/.055)**2))
        # Central nape flows down together rather than symmetrically splitting
        # into two side tails. Upper posterior has a small asymmetric sweep.
        lateral = (side*.55)*(1-neck)-root[0]*3.0*neck
        lateral += .22*upper*(1-abs(root[0])/.105)
        if soft_nape:
            # Preserve the spread of the lower follicles instead of converging
            # every long neck patch into a few central pointed tails.
            lateral = (side*.55)*(1-neck)+(side*.14+.09*np.sin(gi*1.37))*neck
            lateral += .18*upper*(1-abs(root[0])/.105)
        heading = Vector((lateral, .35, -.90-.20*neck))
    heading -= normal*heading.dot(normal)
    if heading.length<1e-6:
        heading = Vector((side*.4, .7, -.2))
        heading -= normal*heading.dot(normal)
    heading.normalize()
    p = np.empty((N, 3), float)
    p[0] = hit+normal*.00055
    position = hit
    release = .64 if upper>.55 else .52
    current_normal = normal.copy()
    for j in range(1, N):
        candidate = position+heading*(length/(N-1))
        if t[j]<release:
            point, nn, face, dist = bv.find_nearest(candidate)
            heading -= nn*heading.dot(nn)
            if heading.length>1e-8:
                heading.normalize()
            position = point
            current_normal = nn
        else:
            # Free ends follow the leaving tangent, with gravity in the last
            # third. They are not indefinitely projected onto head or neck.
            position = candidate
            heading.z -= .012
            heading.normalize()
        lift = .00055+(.006+.003*np.sin(gi*1.71))*np.sin(np.pi*t[j])**1.2+.003*t[j]
        p[j] = position+current_normal*lift
    tangent = np.gradient(p, axis=0)
    tangent /= np.maximum(np.linalg.norm(tangent, axis=1)[:, None], 1e-8)
    lateral = np.cross(tangent, np.array([0, 1, 0]))
    lateral /= np.maximum(np.linalg.norm(lateral, axis=1)[:, None], 1e-8)
    phase = gi*2.399963
    p += lateral*(.005*np.sin(t*1.8*np.pi+phase)*np.sin(np.pi*t))[:, None]
    if soft_nape:
        p[:, 1] += .006*neck*np.sin(t*1.75*np.pi+phase*.6)*np.sin(np.pi*t)
    p[0] = hit+normal*.00055
    guides.append(p)
    lengths.append(length)
guides = np.array(guides)
labels = np.empty(count, int)
for start in range(0, count, 2048):
    distance = np.sum((roots[start:start+2048, None]-guide_roots[None])**2, axis=2)
    labels[start:start+2048] = np.argmin(distance, axis=1)
paths = np.empty((count, N, 3), np.float32)
repairs = 0
for i, root in enumerate(roots):
    gi = labels[i]
    guide = guides[gi]
    fraction = rng.uniform(.88, 1)
    p = np.stack([np.interp(t*fraction, t, guide[:, k]) for k in range(3)], axis=1)
    hit, normal, face, dist = bv.find_nearest(Vector(root))
    attached = np.array(hit+normal*.00055)
    offset = attached-guide[0]
    p += offset[None, :]*(1-.70*t[:, None]**1.1)
    # Submillimeter fiber variation, keeping narrow coherent guide patches.
    phase = rng.uniform(0, 2*np.pi)
    p[:, 0] += .00035*np.sin(t*6+phase)*np.sin(np.pi*t)
    p[:, 1] += .00030*np.sin(t*5+phase*.7)*np.sin(np.pi*t)
    for j in range(1, N):
        point, nn, face, dist = bv.find_nearest(Vector(p[j]))
        gap = (Vector(p[j])-point).dot(nn)
        if gap<.0008 and dist<.025:
            p[j] = np.array(point+nn*.0010)
            repairs += 1
    p[0] = attached
    paths[i] = p
evaluated.to_mesh_clear()
assert np.isfinite(paths).all()
cu = bpy.data.hair_curves.new('Original distributed posterior surface groom')
cu.add_curves([N]*count)
cu.attributes['position'].data.foreach_set('vector', paths.ravel())
radius = rng.uniform(.000027, .000038, (count, 1))*(1-.997*t[None, :]**3)**.65
cu.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', radius.astype(np.float32).ravel())
cu.materials.append(rear.data.materials[0])
ob = bpy.data.objects.new('Original posterior shag • distributed surface roots', cu)
bpy.context.scene.collection.objects.link(ob)
rear.hide_render = True
rear.hide_viewport = True
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
    method='Original area-distributed scalp roots, irregular farthest-point guide patches; shorter crown and free long nape tips',
    original_new_curves=count, original_guides=guide_count,
    elongated_centripetal_nape=long_nape,
    spread_soft_nape=soft_nape,
    hidden_old_rear=rear.name, scalp_area_m2=float(area.sum()),
    guide_length_quantiles_m=np.quantile(lengths, [0, .5, 1]).tolist(),
    nearest_body_point_repairs=repairs,
    samples=scene.cycles.samples, draft='--draft' in args, denoising=False,
    status='Unreviewed actual 3D study; not artistic approval',
    license='New posterior shape/roots original; retained original frontal/short posterior, Bystedt CC BY-SA support and Abhay Pratap Royalty Free source-flow support. Hidden donor rear remains local.',
    collision_scope='Pointwise nearest body repairs, no exhaustive hair/clothing/motion verification')
(out/'surface_groom_manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front', '02_ThreeQuarter', '03_Side', '04_Back']:
    scene.camera = bpy.data.objects[name]
    scene.render.filepath = str(render/(name+'.png'))
    bpy.ops.render.render(write_still=True)
print('ORIGINAL_POSTERIOR_SURFACE_GROOM_RENDERED', version, flush=True)
