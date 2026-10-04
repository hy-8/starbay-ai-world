"""Cut actual posterior fibers by root region and arc length, not tip lifting.

The separate short native scalp coverage stays visible. No uncut long shell is
kept beneath the shorter layers. Fresh local studies only; license unchanged.
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
if source_version != 'sheengroom02':
    raise ValueError('This root-region study is calibrated to sheengroom02 only')
out, render = ROOT/'Exports'/version, ROOT/'Renders'/version
if out.exists() or render.exists():
    raise RuntimeError('Fresh output required')
source = ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
bpy.context.view_layer.update()
ob = next(o for o in bpy.data.objects if o.name.startswith('Volumetric recomb') and not o.hide_render)
cu = ob.data
sizes = [len(c.points) for c in cu.curves]
if len(set(sizes)) != 1:
    raise RuntimeError('Uniform native point count required')
N = sizes[0]
raw = np.empty(len(cu.points)*3, np.float32)
cu.attributes['position'].data.foreach_get('vector', raw)
raw = raw.reshape(-1, N, 3)
result = raw.copy()
body = bpy.data.objects['CC0 male body • retained topology']
bv = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
t = np.linspace(0, 1, N)

def smooth(x):
    x = np.clip(x, 0, 1)
    return x*x*(3-2*x)

# Continuous spatial fields define length, so adjacent roots do not form a
# horizontal cutoff band. Fibers remain independent and rooted exactly.
roots = raw[:, 0].astype(float)
upper = smooth((roots[:, 2]-1.775)/.070)
posterior = smooth((roots[:, 1]+.025)/.065)
side = smooth((np.abs(roots[:, 0])-.035)/.045)
field = .5+.5*np.sin(roots[:, 0]*97+roots[:, 1]*71+roots[:, 2]*43)
shorter_crown = '--shorter-crown' in args
cut_base, cut_variation = (.36, .22) if shorter_crown else (.20, .18)
fractions = 1-upper*(cut_base+cut_variation*field)*(.60+.40*posterior)
fractions *= 1-.10*side*smooth((roots[:, 2]-1.79)/.035)
rng = np.random.default_rng(100407)
fractions *= rng.uniform(.965, 1, len(raw))
repairs = 0
extended = 0
for i, p0 in enumerate(raw):
    p = p0.astype(float)
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    if arc[-1] < 1e-7:
        continue
    arc /= arc[-1]
    target = t*fractions[i]
    q = np.stack([np.interp(target, arc, p[:, k]) for k in range(3)], axis=1)
    root = roots[i]
    # Neck silhouette contracts gradually after the occipital volume. A small
    # continuous S bend avoids a straight parallel fall below the collar.
    neck = smooth((1.790-q[:, 2])/.095)*smooth((q[:, 1]-.005)/.040)
    q[:, 0] *= 1-.22*neck
    q[:, 1] -= .009*neck
    phase = root[0]*85+root[1]*49
    q[:, 0] += .007*np.sin(t*1.8*np.pi+phase)*neck*t
    q[:, 1] += .005*np.sin(t*1.45*np.pi+phase*.7)*neck*t
    lower_root = (1-smooth((root[2]-1.792)/.037))*smooth((root[1]-.002)/.035)
    tip_gate = smooth((1.755-q[-1, 2])/.045)
    extension = lower_root*tip_gate*(.025+.026*np.exp(-(root[0]/.045)**2))
    if extension > .001:
        q[:, 2] -= extension*t**2.4
        q[:, 0] += .005*np.sin(t*2.0*np.pi+phase)*t**2.4*lower_root
        extended += 1
    # Feathered short ends only; do not lift the whole coverage envelope.
    feather = upper[i]*side[i]
    q[:, 0] += np.sign(root[0])*.007*feather*t**3
    q[:, 1] += .004*upper[i]*posterior[i]*t**3
    for j in range(1, N):
        hit, normal, face, dist = bv.find_nearest(Vector(q[j]))
        gap = (Vector(q[j])-hit).dot(normal)
        if gap < .0008 and dist < .030:
            q[j] = np.array(hit+normal*.0010)
            repairs += 1
    q[0] = p0[0]
    result[i] = q.astype(np.float32)
assert np.array_equal(raw[:, 0], result[:, 0]) and np.isfinite(result).all()
new_data = cu.copy()
new_data.attributes['position'].data.foreach_set('vector', result.ravel())
ob.data = new_data
ob.name = 'Root-region shag • actual arc-length cut rear'

scene = bpy.context.scene
pref = bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type = 'OPTIX'
pref.get_devices()
for device in pref.devices:
    device.use = device.type == 'OPTIX'
scene.cycles.device = 'GPU'
scene.cycles.samples = 64 if '--draft' in args else 192
scene.cycles.use_denoising = False
scene.render.resolution_x = 1200
scene.render.resolution_y = 1400
scene.render.resolution_percentage = 80 if '--draft' in args else 100
out.mkdir(parents=True)
render.mkdir(parents=True)
report = dict(version=version, source=source_version,
    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    method='Continuous root-region arc-length cuts on all posterior fibers; separate short scalp coverage retained; tapered curved nape',
    actual_rear_curves=len(raw), all_roots_preserved_exactly=True,
    unchanged_long_coverage_shell=False, lower_root_nape_extensions=extended,
    shorter_crown=shorter_crown, build_only='--build-only' in args,
    length_fraction_quantiles=np.quantile(fractions, [0, .25, .5, .75, 1]).tolist(),
    root_coordinate_quantiles_m=np.quantile(roots, [0, .25, .5, .75, 1], axis=0).tolist(),
    nearest_body_repairs=repairs, draft='--draft' in args,
    samples=scene.cycles.samples, denoising=False,
    status='Unreviewed actual geometry study, not artistic approval',
    license='Ddr Rcs Royalty Free rear; retained original frontal, Bystedt CC BY-SA short support and Abhay Pratap Royalty Free flow-derived scalp support',
    collision_scope='Nearest body point repairs only; not exhaustive scalp/clothing/motion validation')
(out/'layer_length_manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
if '--build-only' not in args:
    for name in ['01_Front', '02_ThreeQuarter', '03_Side', '04_Back']:
        scene.camera = bpy.data.objects[name]
        scene.render.filepath = str(render/(name+'.png'))
        bpy.ops.render.render(write_still=True)
print('SHAG_LAYER_LENGTHS_SAVED' if '--build-only' in args else 'SHAG_LAYER_LENGTHS_RENDERED', version, flush=True)
