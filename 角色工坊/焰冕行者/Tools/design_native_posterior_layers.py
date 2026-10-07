"""Sculpt staggered posterior layers from locally licensed native curves.

No new fibers or image reconstruction. Keep actual fringe and source follicles.
"""
import bpy, sys, re, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--') + 1:]
version, base = a[:2]
outer_locks = '--outer-locks' in a
posterior_panels = '--posterior-panels' in a
assert not (outer_locks and posterior_panels)
assert all(re.fullmatch('[A-Za-z0-9_-]+', v) for v in a[:2])
out, renders = ROOT / 'Exports' / version, ROOT / 'Renders' / version
assert not out.exists() and not renders.exists()
source = ROOT / 'Exports' / base / 'Ember_Regent.blend'
digest = hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
ob = bpy.data.objects['Bystedt layercut derivative • native root reflow']
cu = ob.data
p = np.empty((len(cu.points), 3), np.float32)
cu.attributes['position'].data.foreach_get('vector', p.ravel())
raw = p.reshape(-1, 65, 3).astype(float)
q = raw.copy()
r = raw[:, 0]
fringe = np.empty(len(raw), bool)
cu.attributes['native_resculpted_fringe_sweeps'].data.foreach_get('value', fringe)
ids = np.flatnonzero((~fringe) & ((r[:, 1] > .005) |
                     ((np.abs(r[:, 0]) > .038) & (r[:, 1] > -.032))))
features = (raw[ids][:, [0, 12, 28, 48, 64]] *
            np.array([1., .8, .7, .65, .7])[None, :, None]).reshape(len(ids), -1)
K = 180
centers = [features[len(features) // 2]]
best = np.full(len(features), np.inf)
for _ in range(1, K):
    best = np.minimum(best, np.sum((features - centers[-1]) ** 2, axis=1))
    centers.append(features[np.argmax(best)])
centers = np.array(centers)

def assign():
    return np.argmin(np.maximum(0, (features * features).sum(1)[:, None] +
        (centers * centers).sum(1)[None] - 2 * features @ centers.T), axis=1)

for _ in range(22):
    labels = assign()
    for k in range(K):
        if (labels == k).any():
            centers[k] = features[labels == k].mean(0)
labels = assign()
body = bpy.data.objects['CC0 male body • retained topology']
assert np.array_equal(np.array(body.matrix_world), np.eye(4))
bv = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
garments = []
for name in ['Tailored standing rear collar', 'Fitted CC0 male_elegantsuit01']:
    garment = bpy.data.objects[name]
    evaluated = garment.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    garments.append(BVHTree.FromPolygons([garment.matrix_world @ v.co for v in mesh.vertices],
                    [list(poly.vertices) for poly in mesh.polygons]))
    evaluated.to_mesh_clear()
t = np.linspace(0, 1, 65)
u = t[:, None]

def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)

mask = np.zeros(len(raw), bool)
rows = []
body_repairs = collar_repairs = 0
for k in range(K):
    members = ids[labels == k]
    if len(members) < 24:
        continue
    old = raw[members]
    c = old.mean(0)
    phase = k * 2.3999632297
    if posterior_panels:
        if c[32,1] < .030 or abs(c[32,0]) > .064:
            continue
        members = members[(members%5)!=0]
        if len(members)<24:
            continue
        old=raw[members]
        c=old.mean(0)
    if outer_locks and (c[0, 2] < 1.792 or np.sin(phase*.83) < -.10):
        continue
    # Different whole locks end at different levels. Lower follicles retain
    # the deliberate long nape; high follicles supply shorter outer layers.
    upper = float(smooth((c[0, 2] - 1.780) / .075))
    cut = 1 - upper * (.10 + .25 * (.5 + .5 * np.sin(phase * .73)))
    if posterior_panels:
        cut = .64+.29*(.5+.5*np.sin(phase*.73))
    cut_per_fiber = np.clip(cut + .025 * np.sin(members * 2.399963), .62, 1.)
    sampled = np.empty_like(old)
    for i, rate in enumerate(cut_per_fiber):
        for axis in range(3):
            sampled[i, :, axis] = np.interp(t * rate, t, old[i, :, axis])
    center = sampled.mean(0)
    # Fit a single broad flow instead of retaining repeated high-frequency
    # center waves. Native intra-lock dispersion remains independently visible.
    p0, p3 = center[0].copy(), center[-1].copy()
    A = np.column_stack([3 * (1-t)**2 * t, 3 * (1-t) * t*t])
    B = center - (1-u)**3 * p0 - u**3 * p3
    p1, p2 = np.linalg.lstsq(A[1:-1], B[1:-1], rcond=None)[0]
    radial = center[34] - np.array([0., -.035, 1.776])
    radial[2] = 0
    radial /= max(np.linalg.norm(radial), 1e-9)
    lateral = np.array([-radial[1], radial[0], 0.])
    flare = .004 + .013 * (.5 + .5 * np.cos(phase * .61))
    lift = .002 + .008 * (.5 + .5 * np.sin(phase * .43))
    p1 += radial * lift
    p2 += radial * (.5 * lift + .25 * flare)
    p3 += radial * flare + lateral * (.005 * np.sin(phase))
    # Some ends flick out, others remain descending: no shared S-wave phase.
    p3[2] += .006 * np.sin(phase * .89)
    guide = (1-u)**3 * p0 + 3 * (1-u)**2*u*p1 + 3*(1-u)*u*u*p2 + u**3*p3
    if outer_locks:
        # A separate high-follicle outer shell uses explicit swept landmarks,
        # leaving the dense unselected inner locks as coverage. This does not
        # simply apply another common sinusoid to the entire posterior sheet.
        side = 1 if c[0,0] >= 0 else -1
        root_theta = np.arctan2(c[0,0], c[0,1]+.035)
        # Positive Y is behind the head. Upper outer locks converge gradually
        # toward that direction, while lateral roots remain swept to own side.
        tip_theta = root_theta * (.66 + .15*(.5+.5*np.sin(phase*.47)))
        tip_z = np.clip(c[-1,2] + .026 + .025*(.5+.5*np.sin(phase*.91)), 1.704, 1.789)
        tip_radius = .092 + .025*(.5+.5*np.cos(phase*.59))
        end = np.array([np.sin(tip_theta)*tip_radius,
                        -.035+np.cos(tip_theta)*tip_radius, tip_z])
        crown = c[0] + radial*(.010+.010*(.5+.5*np.cos(phase*.37)))
        crown[2] += .006+.011*(.5+.5*np.sin(phase*.41))
        shoulder = np.array([np.sin(root_theta*.88)*(.105+.007*np.sin(phase)),
                        -.035+np.cos(root_theta*.88)*(.105+.007*np.sin(phase)),
                        max(tip_z+.029,1.802+.009*np.sin(phase*.67))])
        # Cubic controls are constructed from scalp-adjacent crown and swept
        # shoulder/end landmarks. Tip directions vary by follicle family.
        outer_guide = (1-u)**3*p0 + 3*(1-u)**2*u*crown + 3*(1-u)*u*u*shoulder + u**3*end
        outer_guide += lateral[None]*(.003*np.sin(phase)*np.sin(np.pi*t)**2)[:,None]
        spread = old-c
        values = outer_guide[None]+spread*.60
        values += (old[:,0]-c[0])[:,None,:]*(.40*(1-t))[None,:,None]
        values += radial[None,None]*(.0012*np.sin(members*2.399963))[:,None,None]*smooth((t-.6)/.4)[None,:,None]
    else:
        values = sampled + .90 * (guide - center)[None]
    if posterior_panels:
        # The actual middle-back panel contains lower-root shafts too. Split
        # their visible midsections into narrower locks and leave20% of each
        # original family unchanged as an inner coverage veil.
        bump = (.012+.012*(.5+.5*np.cos(phase*.39)))*np.sin(np.pi*t)**1.3
        guide += radial[None]*bump[:,None]
        guide += lateral[None]*(.010*np.sin(phase*.67)*np.sin(np.pi*t)**2)[:,None]
        values=sampled+.93*(guide-center)[None]
        dev=sampled-center
        wide=np.sum(dev*lateral,axis=2)
        order=np.argsort(wide[:,18:44].mean(1),kind='stable')
        rank=np.empty(len(members));rank[order]=(np.arange(len(members))+.5)/len(members)
        half_width=.003+.004*(.5+.5*np.sin(phase*.83))
        width_target=(2*rank-1)[:,None]*half_width*(1-.7*smooth((t-.54)/.46))[None]
        weight=.72*smooth((t-.12)/.26)
        values+=(width_target-wide)[:,:,None]*lateral[None,None]*weight[None,:,None]
    # Preserve a broad soft section, with less planar middle scattering.
    deviation = sampled - center
    if not posterior_panels:
        values -= .20 * np.sum(deviation * lateral, axis=2)[:, :, None] * lateral[None, None]
    blend = smooth((t - .075) / .25)
    values = old * (1 - blend[None, :, None]) + values * blend[None, :, None]
    for i in range(len(members)):
        correction = np.zeros((65, 3))
        for j in range(6, 65):
            hit, n, _, dist = bv.find_nearest(Vector(values[i, j]))
            gap = (Vector(values[i, j]) - hit).dot(n)
            if dist < .03 and gap < .0007:
                correction[j] = np.array(n) * (.0010 - gap)
                body_repairs += 1
        # Spread correction to neighboring samples rather than creating a
        # one-point corner; this remains a discrete guard, not simulation.
        envelope = correction.copy()
        norm = np.linalg.norm(correction, axis=1)
        for j in range(6, 65):
            lo, hi = max(6, j-4), min(65, j+5)
            weights = np.maximum(0, 1 - np.abs(np.arange(lo, hi)-j)/5)
            scores = norm[lo:hi] * weights
            h = int(np.argmax(scores))
            if scores[h] > np.linalg.norm(envelope[j]):
                envelope[j] = correction[lo+h] * weights[h]
        values[i] += envelope
        required = np.zeros(65)
        for j in range(6, 65):
            if values[i, j, 2] > 1.670:
                continue
            for collider in garments:
                hit, _, _, _ = collider.ray_cast(Vector((values[i,j,0], .5, values[i,j,2])),
                                                Vector((0, -1, 0)), 1.)
                if hit is not None and values[i,j,1] < hit.y + .003:
                    required[j] = max(required[j], hit.y+.003-values[i,j,1])
        envelope_y = required.copy()
        for shift in range(1, 9):
            envelope_y[:-shift] = np.maximum(envelope_y[:-shift], required[shift:]*(1-shift/10))
            envelope_y[shift:] = np.maximum(envelope_y[shift:], required[:-shift]*(1-shift/10))
        envelope_y[:6] = 0
        values[i, :, 1] += envelope_y
        collar_repairs += int((required > 0).sum())
    values[:, :6] = old[:, :6]
    q[members] = values
    mask[members] = True
    rows.append(dict(group=k, fibers=len(members), designed_path_fraction=float(cut),
        radial_flare_m=float(flare), root_lift_m=float(lift),
        authored_outer_landmarks_m=([p0.tolist(),crown.tolist(),shoulder.tolist(),end.tolist()] if outer_locks else None),
        maximum_displacement_m=float(np.linalg.norm(values-old, axis=2).max())))
assert mask.sum() > 100 and np.isfinite(q).all()
assert np.array_equal(q[:, :6], raw[:, :6]) and np.array_equal(q[~mask], raw[~mask])
assert np.array_equal(q[fringe], raw[fringe])
ob.data = cu.copy()
ob.data.attributes['position'].data.foreach_set('vector', q.astype(np.float32).ravel())
attr = ('native_posterior_panel_locks' if posterior_panels else
        'native_authored_outer_locks' if outer_locks else 'native_staggered_posterior_layers')
assert not ob.data.attributes.get(attr), 'Fresh selection attribute required'
ob.data.attributes.new(attr, 'BOOLEAN', 'CURVE').data.foreach_set('value', mask)
ob.data.update_tag()
out.mkdir(parents=True)
renders.mkdir(parents=True)
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
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'Ember_Regent.blend'))
cam = bpy.data.objects['03_Side'].copy()
cam.data = cam.data.copy()
s.collection.objects.link(cam)
cam.name = '05_OppositeSide'
reflection = Matrix.Diagonal((-1., 1., 1., 1.))
cam.matrix_world = reflection @ cam.matrix_world @ reflection
for shot in ['02_ThreeQuarter', '03_Side', '05_OppositeSide', '04_Back']:
    s.camera = bpy.data.objects[shot]
    s.render.filepath = str(renders / (shot + '.png'))
    bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
(out / 'posterior_layers_manifest.json').write_text(json.dumps(dict(
    source=base, source_sha256=digest, selection_attribute=attr, changed_fibers=int(mask.sum()),
    eligible_fibers=len(ids), target_groups=K, edited_groups=len(rows), groups=rows,
    outer_locks=outer_locks,
    posterior_panels=posterior_panels,
    discrete_body_repairs=body_repairs, discrete_collar_ray_repairs=collar_repairs,
    fringe_exact=True, prefix_points=6,
    method=('Actual posterior center-panel families, center point32 Y>=30mm/absX<=64mm,20% source fibers per family remain unselected as coverage. Full-path fractions64-93% with2.5% individual scatter, broad fitted93% mean,12-24mm radial middle relief and10mm independent lateral lock stagger;72% blend toward3-7mm fan halfwidth tapering70% at ends. Roots/first6/fringe/materials/radii/other components retained.' if posterior_panels else '180 actual whole-path groups; high roots Z>=1.792m and independent family selection retain inner source coverage. Explicit authored crown/shoulder/end landmarks give backward-swept outer cubic locks, tips1.704-1.789m at92-117mm radial range. Original intra-lock scatter retained60%; source follicles, first6 points/fringe/radii/topology/materials/other components unchanged.' if outer_locks else '180 actual whole-path groups, non-fringe posterior/side follicles. High-root locks shorten by10-35% of source path parameter with individual2.5% scatter; low nape retained. Broad fitted cubic mean flow90%,4-17mm outward staggered terminal flare,2-10mm upper lift,20% lateral section reduction. Actual source follicles, first6 points, fringe, radii/topology, other components/materials/lighting retained.'),
    status='Actual draft awaiting art review; no continuous or dynamic collision claim'), indent=2), encoding='utf-8')
print('STAGGERED_POSTERIOR_LAYERS', version, int(mask.sum()), len(rows), flush=True)
