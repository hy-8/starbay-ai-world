"""Separate upper root sheets into lifted, continuously framed small locks.

Uses saved native strands only. Keeps true roots, radii, topology, foreground,
tips and all nonselected objects. No neural source processing or new assets.
"""
import bpy, sys, re, json, hashlib, numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
ROOT = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--') + 1:]; version, base = a[:2]
path_groups = '--path-groups' in a
relax_curved = '--relax-curved-groups' in a
if relax_curved and not path_groups: raise ValueError('Curvature relaxation requires path grouping')
assert all(re.fullmatch('[A-Za-z0-9_-]+', v) for v in a[:2])
out = ROOT / 'Exports' / version; render = ROOT / 'Renders' / version
assert not out.exists() and not render.exists()
source = ROOT / 'Exports' / base / 'Ember_Regent.blend'
digest = hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False); bpy.context.view_layer.update()
ob = bpy.data.objects['Bystedt layercut derivative • native root reflow']; cu = ob.data
p = np.empty((len(cu.points), 3), np.float32)
cu.attributes['position'].data.foreach_get('vector', p.ravel()); raw = p.reshape(-1, 65, 3).astype(float); q = raw.copy()
frame = np.empty(len(raw), bool); cu.attributes['native_front_frame_sculpture'].data.foreach_get('value', frame)
r = raw[:, 0]; eligible = np.flatnonzero((~frame) & (r[:, 2] > 1.830) & (r[:, 1] < .065))
roots = r[eligible]; K = 150
# Whole root-to-midshaft flow separates neighbors whose source strands travel
# in different directions. Root-only patches can average an artificial ridge.
features = (raw[eligible][:, [0, 8, 16, 24, 40]] * np.array([.7, .9, 1., 1., .4])[None, :, None]).reshape(len(eligible), -1) if path_groups else roots
centers = [features[len(features) // 2]]; best = np.full(len(features), np.inf)
for _ in range(1, K):
    best = np.minimum(best, np.sum((features - centers[-1]) ** 2, axis=1)); centers.append(features[np.argmax(best)])
centers = np.array(centers)
def assign():
    return np.argmin(np.maximum(0, (features * features).sum(axis=1)[:, None] + (centers * centers).sum(axis=1)[None] - 2 * features @ centers.T), axis=1)
for _ in range(24):
    labels = assign()
    for k in range(K):
        if (labels == k).any(): centers[k] = features[labels == k].mean(axis=0)
labels = assign(); body = bpy.data.objects['CC0 male body • retained topology']
assert np.array_equal(np.array(body.matrix_world), np.eye(4))
bv = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
mask = np.zeros(len(raw), bool); t = np.linspace(0, 1, 65); rows = []; repairs = 0
def smooth(x):
    x = np.clip(x, 0, 1); return x*x*(3 - 2*x)
# Unlike the short microtuft test80, lofts occupy a broad root-to-midshaft span.
# All sculpted offsets fade out by point44, retaining complete original tails.
envelope = smooth(t / .16) * (1 - smooth((t - .30) / .38)); envelope[44:] = 0
for k in range(K):
    ids = eligible[labels == k]
    if len(ids) < 30: continue
    old = raw[ids]; center = old.mean(axis=0)
    tangent = np.gradient(center, axis=0); tangent /= np.maximum(np.linalg.norm(tangent, axis=1)[:, None], 1e-9)
    hit, nn, _, _ = bv.find_nearest(Vector(center[0])); scalp_normal = np.array(nn)
    across = np.zeros_like(tangent); prev = np.cross(scalp_normal, tangent[0]); prev /= max(np.linalg.norm(prev), 1e-9)
    for j in range(65):
        prev -= tangent[j] * np.dot(prev, tangent[j]); prev /= max(np.linalg.norm(prev), 1e-9); across[j] = prev
    normal = np.cross(tangent, across)
    if np.dot(normal[0], scalp_normal) < 0: normal = -normal
    delta = old - center[None]
    wide = np.sum(delta * across[None], axis=2); deep = np.sum(delta * normal[None], axis=2); along = np.sum(delta * tangent[None], axis=2)
    source_turn = float(np.degrees(np.arccos(np.clip(np.sum(tangent[:43] * tangent[1:44], axis=1), -1, 1))).sum())
    # Existing curved guides need less new loft: adding a full crest to a
    # source curl produces a raised loop rather than a relaxed layered sweep.
    curved_strength = 1 - .65 * smooth((source_turn - 100) / 80) if relax_curved else 1.
    phase = k * 2.399963; lift = (.005 + .009 * (.5 + .5 * np.sin(phase))) * curved_strength
    # A single broad asymmetric crest with phase-dependent sweep, not repeated
    # periodic curls. Transported lock section separates overlapping root fans.
    crest = envelope * (1 + .22 * np.sin(np.pi * t + phase))
    sideways = (.002 + .004 * np.cos(phase)) * envelope * np.sin(np.pi * t / .68) * curved_strength
    guide = center + normal * (lift * crest)[:, None] + across * sideways[:, None]
    values = guide[None] + tangent[None] * along[:, :, None]
    values += across[None] * (wide * (1 - .58 * envelope[None]))[:, :, None]
    values += normal[None] * (deep * (1 - .35 * envelope[None]))[:, :, None]
    # Three secondary flow bands retain internal fiber breakup without turning
    # each root into a tiny raised knot or repeating one tight curl per patch.
    internal = np.sin(ids * 2.399963)
    values += normal[None] * (.0013 * internal[:, None] * envelope[None])[:, :, None]
    values += across[None] * (.0009 * np.sin(ids[:, None] * .71 + t[None] * 5) * envelope[None])[:, :, None]
    for i in range(len(ids)):
        for j in range(1, 44):
            if envelope[j] < .001: continue
            hit, n, _, dist = bv.find_nearest(Vector(values[i, j])); gap = (Vector(values[i, j]) - hit).dot(n)
            if dist < .03 and gap < .0005:
                values[i, j] += np.array(n) * (.0007 - gap); repairs += 1
    values[:, 0] = old[:, 0]; values[:, 44:] = old[:, 44:]; q[ids] = values; mask[ids] = True
    rows.append(dict(patch=k, fibers=len(ids), root_mean_m=center[0].tolist(), source_guide_turn_deg=source_turn,
        curved_strength=float(curved_strength), loft_m=float(lift), max_displacement_m=float(np.linalg.norm(values-old, axis=2).max())))
assert mask.sum() > 100 and np.isfinite(q).all()
assert np.array_equal(q[:, 0], raw[:, 0]) and np.array_equal(q[:, 44:], raw[:, 44:])
assert np.array_equal(q[frame], raw[frame]) and np.array_equal(q[~mask], raw[~mask])
ob.data = cu.copy(); ob.data.attributes['position'].data.foreach_set('vector', q.astype(np.float32).ravel()); ob.data.update_tag()
attr = 'native_layered_root_lofts'; prior = ob.data.attributes.get(attr)
if prior: ob.data.attributes.remove(prior)
ob.data.attributes.new(attr, 'BOOLEAN', 'CURVE').data.foreach_set('value', mask)
out.mkdir(parents=True); render.mkdir(parents=True); s = bpy.context.scene
pref = bpy.context.preferences.addons['cycles'].preferences; pref.compute_device_type='OPTIX'; pref.get_devices()
for d in pref.devices: d.use=d.type=='OPTIX'
s.cycles.device='GPU'; s.cycles.samples=96; s.cycles.use_denoising=False
s.render.resolution_x, s.render.resolution_y=1200, 1400; s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy(); cam.data=cam.data.copy(); s.collection.objects.link(cam); cam.name='05_OppositeSide'
ref=Matrix.Diagonal((-1.,1.,1.,1.)); cam.matrix_world=ref @ cam.matrix_world @ ref
for name in ['02_ThreeQuarter','05_OppositeSide','01_Front']:
    s.camera=bpy.data.objects[name]; s.render.filepath=str(render/(name+'.png')); bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'root_loft_manifest.json').write_text(json.dumps(dict(source=base, source_sha256=digest, selection_attribute=attr,
    eligible_fibers=len(eligible), changed_fibers=int(mask.sum()), target_patches=K, patches=rows,
    all_roots_exact=True, explicit_foreground_exact=True, all_points_44_through_64_exact=True,
    unselected_primary_exact=True, discrete_body_repairs=repairs,
    path_groups=path_groups, relax_curved_groups=relax_curved,
    method=('150 whole root-to-midshaft path groups (saved points0/8/16/24/40, weights.7/.9/1/1/.4)' if path_groups else '150 root-space patches') + ', minimum30 shafts; continuously transported width/depth sections, broad5-14mm asymmetric root lofts fading by point44'+('; source guide cumulative turning100-180deg smoothly reduces extra loft and sideways sweep to35%' if relax_curved else '')+',58% width/35% depth contraction with internal1.3/.9mm variation; original tails retained.',
    status='Actual drafts pending review; static point checks are not art or continuous collision acceptance.'), indent=2), encoding='utf-8')
print('ROOT_LOFTS_SAVED', version, int(mask.sum()), flush=True)
