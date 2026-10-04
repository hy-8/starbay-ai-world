"""Editable portrait sculpture on the retained neutral CC0 mesh.

Separate relative shape keys keep the original geometry available. Hair/scalp,
UVs, vertex order and eyeballs are preserved. Brows follow the sculpted surface;
lashes follow the eye-region deformation. This is a static art study only.
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
out, render = ROOT/'Exports'/version, ROOT/'Renders'/version
if out.exists() or render.exists():
    raise RuntimeError('Fresh output required')
source = ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
body = bpy.data.objects['CC0 male body • retained topology']
eyes = bpy.data.objects['Fitted CC0 high-poly']
if not np.allclose(np.array(body.matrix_world), np.eye(4)) or body.data.shape_keys:
    raise RuntimeError('Neutral world-aligned body without existing shape keys required')
original = np.array([v.co[:] for v in body.data.vertices], float)
eye_points = np.array([eyes.matrix_world@v.co for v in eyes.data.vertices], float)
eye_center_z = float((eye_points[:, 2].max()+eye_points[:, 2].min())*.5)
eye_center_x = float(np.mean(np.abs(eye_points[:, 0])))

def g(x, center, width):
    return np.exp(-((x-center)/width)**2)

def smooth(x):
    x = np.clip(x, 0, 1)
    return x*x*(3-2*x)

def fields(points):
    x, y, z = points.T
    a = np.abs(x)
    face = smooth((-y-.080)/.055)*(1-smooth((z-1.772)/.010))*smooth((z-1.603)/.020)
    eye = g(a, .034, .018)
    lid = np.zeros_like(points)
    # Measured eyeball center ~1.749m; old nominal brow location 1.779m
    # missed the actual brow cards at 1.753..1.767m. These controls use the
    # actual retained eye region, with a continuous falloff into the face.
    lid[:, 2] = eye*(-.0028*g(z, eye_center_z+.007, .006)
                          +.00075*g(z, eye_center_z-.006, .005))
    lid[:, 2] += .00115*g(a, .051, .010)*g(z, eye_center_z+.002, .014)
    lid *= face[:, None]
    brow = np.zeros_like(points)
    brow[:, 2] = (-.0015*g(a, .019, .014)+.00065*g(a, .050, .012))*g(z, 1.762, .007)*face
    brow[:, 1] = -.00065*eye*g(z, 1.763, .010)*face
    planes = np.zeros_like(points)
    planes[:, 1] = (-.0020*g(a, .053, .020)*g(z, 1.721, .012)
                    +.0022*g(a, .056, .023)*g(z, 1.696, .013)
                    -.0012*g(x, 0, .023)*g(z, 1.639, .014))*face
    planes[:, 0] = -x*.035*g(z, 1.684, .018)*face
    nose = np.zeros_like(points)
    nose[:, 0] = -x*.075*g(x, 0, .021)*g(z, 1.706, .018)*face
    nose[:, 1] = -.0011*g(x, 0, .012)*g(z, 1.733, .022)*face
    lip = np.zeros_like(points)
    lip[:, 2] = (1.669-z)*.13*g(x, 0, .030)*g(z, 1.669, .010)*face
    return {'01_Focused_upper_lids': lid, '02_Angled_brow_ridge': brow,
            '03_Cheek_and_jaw_planes': planes, '04_Nasal_bridge_and_alar': nose,
            '05_Resting_lip_balance': lip}

body.shape_key_add(name='Basis')
sculpt_fields = fields(original)
key_records = []
for name, delta in sculpt_fields.items():
    key = body.shape_key_add(name=name)
    key.data.foreach_set('co', (original+delta).astype(np.float32).ravel())
    key.value = 1
    key_records.append(dict(name=name, value=1, changed_vertices=int((np.linalg.norm(delta, axis=1)>1e-7).sum()),
                            maximum_displacement_m=float(np.linalg.norm(delta, axis=1).max())))
total = sum(sculpt_fields.values())
assert np.isfinite(total).all() and np.array_equal(total[original[:, 2]>=1.782], np.zeros_like(total[original[:, 2]>=1.782]))
body.data.update()
bpy.context.view_layer.update()
bv = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
accessory_records = []
for ob in bpy.data.collections['01_Body'].objects:
    if ob.hide_render or ob==body or ob==eyes:
        continue
    matrix, inv = ob.matrix_world.copy(), ob.matrix_world.inverted()
    if ob.type=='MESH' and 'eyebrow' in ob.name.lower():
        moved, missed = 0, 0
        for v in ob.data.vertices:
            p = matrix@v.co
            delta = sum(fields(np.array([p], float)).values())[0]
            p += Vector(delta)
            hit, normal, face_index, distance = bv.ray_cast(Vector((p.x, -.5, p.z)), Vector((0, 1, 0)), .5)
            if hit is not None:
                p.y = hit.y-.00065
                moved += 1
            else:
                missed += 1
            v.co = inv@p
        ob.data.update()
        accessory_records.append(dict(object=ob.name, reprojected_vertices=moved, missed=missed))
    elif ob.type=='CURVE' and 'eyelash' in ob.name.lower():
        for spline in ob.data.splines:
            for point in spline.points:
                p = matrix@Vector(point.co[:3])
                f = fields(np.array([p], float))
                p += Vector(f['01_Focused_upper_lids'][0]+f['02_Angled_brow_ridge'][0])
                point.co = (*(inv@p), point.co.w)
        accessory_records.append(dict(object=ob.name, method='Continuous eyelid-region deformation; no lash root re-anchoring claim'))

# Quantify local lid/eye contact as sample evidence, not exhaustive collision QA.
eye_bv = BVHTree.FromObject(eyes, bpy.context.evaluated_depsgraph_get())
e = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
me = e.to_mesh()
samples = []
for v in me.vertices:
    p = v.co
    if not (.012<abs(p.x)<.056 and abs(p.z-eye_center_z)<.013 and p.y<-.13):
        continue
    hit, normal, index, distance = eye_bv.find_nearest(p)
    gap = (p-hit).dot(normal)
    if distance<.008:
        samples.append(gap)
e.to_mesh_clear()
out.mkdir(parents=True)
render.mkdir(parents=True)
scene = bpy.context.scene
pref = bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type = 'OPTIX'
pref.get_devices()
for d in pref.devices:
    d.use = d.type=='OPTIX'
scene.cycles.device = 'GPU'
scene.cycles.samples = 64 if '--draft' in args else 192
scene.cycles.use_denoising = False
scene.render.resolution_x, scene.render.resolution_y = 1200, 1400
scene.render.resolution_percentage = 80 if '--draft' in args else 100
report = dict(version=version, source=source_version,
    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    measured_eye_center_z_m=eye_center_z, measured_eye_abs_x_mean_m=eye_center_x,
    method='Five editable relative anatomical shape keys, actual eyebrow surface re-projection, continuous lash following',
    controls=key_records, original_topology_retained=True, original_uvs_retained=True,
    scalp_z_ge_1_782_unchanged=True, eyeball_geometry_unchanged=True,
    accessory_following=accessory_records, eyelid_eye_sample_count=len(samples),
    eyelid_eye_signed_gap_quantiles_m=np.quantile(samples, [0,.5,.95,1]).tolist() if samples else [],
    collision_scope='Spatially selected evaluated eyelid vertices near retained eye mesh only; normal signed gap is approximate, not exhaustive eyelid/contact/motion validation',
    status='Unreviewed static sculpture experiment; not artistic or animation acceptance',
    license='Retained CC0 mesh/UV, original shape-key sculpture; retained hair licenses unchanged',
    samples=scene.cycles.samples, draft='--draft' in args, denoising=False)
(out/'portrait_sculpt_manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
    scene.camera = bpy.data.objects[name]
    scene.render.filepath = str(render/(name+'.png'))
    bpy.ops.render.render(write_still=True)
print('PORTRAIT_LANDMARK_SCULPT_RENDERED', version, flush=True)
