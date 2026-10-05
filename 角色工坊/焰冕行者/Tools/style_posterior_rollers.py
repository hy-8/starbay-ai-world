"""Bend posterior locks by transported tangent rotations, not cubic bowls.

Use fresh neutral versions; preserve the exact original follicles and all other
objects. Regional large-roller bends and reverse tip bends are a study, not an
artistic acceptance. Saved control curves are editable evidence, not live links.
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
out, renders = ROOT/'Exports'/version, ROOT/'Renders'/version
if out.exists() or renders.exists():
    raise RuntimeError('Fresh versions required')
source = ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
bpy.context.view_layer.update()
bv = BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],
                        bpy.context.evaluated_depsgraph_get())
ob = next(o for o in bpy.data.objects if not o.hide_render and
          o.name.startswith('Original posterior shag'))
if not np.allclose(np.array(ob.matrix_world), np.eye(4)):
    raise RuntimeError('Neutral world-aligned groom required')
N = len(ob.data.curves[0].points)
raw = np.empty(len(ob.data.points)*3, np.float32)
ob.data.attributes['position'].data.foreach_get('vector', raw)
raw = raw.reshape(-1, N, 3)
result = raw.copy()
roots = raw[:, 0].astype(float)
t = np.linspace(0, 1, N)

def smooth(x):
    x = np.clip(x, 0, 1)
    return x*x*(3-2*x)

def rotate(v, axis, angle):
    return (v*np.cos(angle) + np.cross(axis, v)*np.sin(angle) +
            axis*np.dot(axis, v)*(1-np.cos(angle)))

# Keep long nape. The transition belongs to follicles, not a flat height cut
# across points along different locks.
weight = smooth((roots[:, 2]-1.798)/.036)
whole_rear = '--whole-rear' in args
if whole_rear:
    weight[:] = 1
ids = np.flatnonzero(weight > 0)
pool = roots[ids[::8]]
chosen = [int(np.argmin(np.linalg.norm(pool-[.015,.02,1.865], axis=1)))]
nearest = np.full(len(pool), np.inf)
for _ in range(95):
    nearest = np.minimum(nearest, np.sum((pool-pool[chosen[-1]])**2, axis=1))
    chosen.append(int(np.argmax(nearest)))
centers = pool[chosen]
labels = np.empty(len(ids), int)
for start in range(0, len(ids), 2048):
    labels[start:start+2048] = np.argmin(np.sum(
        (roots[ids[start:start+2048], None]-centers[None])**2, axis=2), axis=1)

control = []
repairs, max_repair = 0, 0.
rng = np.random.default_rng(100510)
loose_tips = '--loose-tips' in args
for gi, center in enumerate(centers):
    members = ids[labels == gi]
    if not len(members):
        continue
    old = np.median(raw[members].astype(float), axis=0)
    guide_root = np.median(roots[members], axis=0)
    old += guide_root-old[0]
    # Four overlapping layers have deliberately different bend/reversal
    # profiles. These rotate the original tangent field at constant segment
    # arc length rather than translating every point in a shared sine field.
    top = center[2] > 1.845
    side = abs(center[0]) > .052
    lower = center[2] < 1.812 and center[1] > .020
    layer = gi % 4
    fraction = [.84, .97, .76, 1.04][layer] if top else [.86, .99, .78, 1.08][layer]
    if loose_tips:
        fraction = [.78, .96, .70, .88][layer] if top else [.88, .99, .74, .94][layer]
    if whole_rear and lower:
        fraction = [.89, 1., .94, .97][layer]
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(old, axis=0), axis=1))]
    sampled = np.stack([np.interp(t*arc[-1]*min(fraction, 1), arc, old[:, k])
                        for k in range(3)], axis=1)
    tangents = np.diff(sampled, axis=0)
    length = np.linalg.norm(tangents, axis=1)
    if fraction > 1:
        length *= fraction
    tangent = tangents/np.maximum(np.linalg.norm(tangents, axis=1)[:, None], 1e-9)
    # The scalp normal and original leaving tangent establish a stable local
    # roller axis. Its sign is chosen outward for BOTH actual head sides.
    _, nn, _, _ = bv.find_nearest(Vector(guide_root))
    normal = np.array(nn)
    mid = tangent[int(.35*(N-1))]
    axis = np.cross(mid, normal)
    axis /= max(np.linalg.norm(axis), 1e-9)
    sign = 1 if center[0] >= .010 else -1
    q = np.empty_like(old)
    q[0] = guide_root
    main_angle = [.65, .42, .80, .54][layer]
    reverse = [.90, .70, .55, 1.05][layer]
    if loose_tips:
        # Study01 rolled tips back into little crown rings. Open the end bend,
        # reduce middle curvature and shorten overlapping upper locks.
        main_angle = [.36, .26, .48, .33][layer]
        reverse = [-.55, -.28, -.42, -.64][layer]
    if whole_rear and lower:
        main_angle = [.24, .15, .28, .21][layer]
        reverse = [.22, .05, .12, .26][layer]
    for j in range(1, N):
        u = (j-.5)/(N-1)
        bend = main_angle*np.sin(np.pi*smooth((u-.08)/.72))
        bend -= reverse*smooth((u-.67)/.33)
        v = rotate(tangent[j-1], axis, bend)
        # Sweep neighboring visible locks toward the back at different
        # stages, so the cut is diagonal, not one horizontal spray line.
        sweep = sign*(.28 if side else .14)*np.sin(np.pi*u)
        v = rotate(v, np.array([0.,0.,1.]), sweep)
        q[j] = q[j-1] + v*length[j-1]
    if whole_rear and lower:
        # Isolation03 shows the untouched low-root main paths remain the
        # diffuse occipital curtain. Give these separate long neck layers,
        # with shallow lateral S bends instead of upper outward rollers.
        phase = center[0]*24+center[1]*35
        q[:,0] += .010*np.sin(t*1.8*np.pi+phase)*np.sin(np.pi*t)
        q[:,1] += .004*np.sin(t*1.4*np.pi+phase*.4)*np.sin(np.pi*t)
        if '--restore-nape-length' in args:
            # Whole-rear study04 made the neck layers too short when distant
            # native paths were gathered. Restore selected long lower tips,
            # leaving the shorter interleaved layers and exact roots intact.
            finish = 1.632+.030*min(1,abs(center[0])/.085)+.012*np.sin(phase)
            extension = min(.045,max(0,q[-1,2]-finish))
            q[:,2] -= extension*smooth((t-.35)/.65)
    # Head clearance on the guide first. Distal points are then guarded again
    # on actual fibers, retaining exact roots, not a projected solid wig.
    for j in range(1, N):
        hit, nn, _, distance = bv.find_nearest(Vector(q[j]))
        gap = (Vector(q[j])-hit).dot(nn)
        if gap < .0015 and distance < .030:
            q[j] = np.array(hit+nn*.0015)
    # Retain irregular original fiber detail at the root; gather later into
    # visible roller-shaped locks, with independent shorter strands and tips.
    for i in members:
        personal_fraction = rng.uniform(.88, 1)
        p = np.stack([np.interp(t*personal_fraction, t, q[:, k]) for k in range(3)], axis=1)
        p += (roots[i]-guide_root)[None]*(1-.83*smooth(t/.95))[:, None]
        residual = raw[i].astype(float)-old
        residual -= residual[0][None]*(1-.83*smooth(t/.95))[:, None]
        p += residual*(.35*np.sin(np.pi*t))[:, None]
        p += rng.normal(0,.0003,3)[None]*np.sin(np.pi*t)[:, None]
        p = raw[i]*(1-weight[i])+p*weight[i]
        for j in range(1, N):
            hit, nn, _, distance = bv.find_nearest(Vector(p[j]))
            gap = (Vector(p[j])-hit).dot(nn)
            if gap < .0008 and distance < .030:
                amount = .001-gap
                p[j] += np.array(nn)*amount
                repairs += 1
                max_repair = max(max_repair, amount)
        p[0] = raw[i,0]
        result[i] = p
    control.append(dict(group=gi, layer=layer, assigned_fibers=len(members),
                        top=bool(top), side=bool(side), length_fraction=fraction,
                        long_lower_layer=bool(whole_rear and lower),
                        restored_nape_length='--restore-nape-length' in args,
                        main_bend_rad=main_angle, reverse_bend_rad=reverse,
                        root=guide_root.tolist(), path=q.tolist()))

tuck_occipital = '--tuck-occipital' in args
tucked_points = 0
if tuck_occipital:
    # Diagnosis: the main posterior fibers themselves form the rounded back,
    # including low-root long paths; the undercoat does not account for it.
    # Sculpt that shared envelope against actual head skin. Preserve crown
    # crest and long neck tips, with a gradual height/strand transition.
    for i in range(len(result)):
        p = result[i].astype(float)
        gate = smooth((1.862-p[:,2])/.036)*smooth((p[:,2]-1.743)/.038)*smooth(t/.28)
        if not np.any(gate>.001):
            continue
        delta = np.zeros_like(p)
        spacing = .007+.003*np.sin(roots[i,0]*80+roots[i,1]*43)
        for j in range(1,N):
            if gate[j] <= .001:
                continue
            hit, nn, _, distance = bv.find_nearest(Vector(p[j]))
            gap = (Vector(p[j])-hit).dot(nn)
            amount = min(.028, max(0,gap-spacing))*.88*gate[j]
            if distance < .07 and amount > 0:
                delta[j] = -np.array(nn)*amount
                tucked_points += 1
        for _ in range(3):
            delta[1:-1] = .25*delta[:-2]+.5*delta[1:-1]+.25*delta[2:]
        p += delta
        for j in range(1,N):
            if gate[j] <= .001:
                continue
            hit, nn, _, distance = bv.find_nearest(Vector(p[j]))
            gap = (Vector(p[j])-hit).dot(nn)
            if gap < .0008 and distance < .030:
                amount = .001-gap
                p[j] += np.array(nn)*amount
                repairs += 1
                max_repair = max(max_repair,amount)
        p[0] = raw[i,0]
        result[i] = p

assert np.array_equal(result[:,0],raw[:,0]) and np.isfinite(result).all()
data = ob.data.copy()
data.attributes['position'].data.foreach_set('vector', result.ravel())
radius = np.empty(len(data.points), np.float32)
data.attributes['radius'].data.foreach_get('value', radius)
radius = radius.reshape(-1,N)
radius[ids] = radius[ids,0,None]*(1-.997*t**2.5)[None]**.7
data.attributes['radius'].data.foreach_set('value',radius.ravel())
ob.data = data
gc = bpy.data.collections.new('Roller study controls • baked evidence')
bpy.context.scene.collection.children.link(gc)
gc.hide_render = True
gd = bpy.data.curves.new('Posterior roller paths • not live groom links','CURVE')
gd.dimensions = '3D'
for record in control:
    sp = gd.splines.new('POLY')
    sp.points.add(N-1)
    for v, p in zip(sp.points,record['path']):
        v.co = (*p,1)
go = bpy.data.objects.new('Editable roller paths • re-bake required',gd)
gc.objects.link(go)
go.hide_render = True
out.mkdir(parents=True)
renders.mkdir(parents=True)
report = dict(version=version, source=source_version,
              source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
              method=('96 regional transported-tangent roller bends, four staggered actual arc lengths, all frontal geometry retained; '+
                      ('separate shallow lateral S-bent long lower layers' if whole_rear else 'lower-root nape flow retained')+
                      ('; actual head-skin occipital envelope contraction' if tuck_occipital else '')),
              rear_only=True, front_only=False,
              opened_loose_tips=loose_tips,
              whole_rear_with_separate_long_lower_layers=whole_rear,
              restored_lower_nape_length='--restore-nape-length' in args,
              occipital_envelope_tuck=tuck_occipital,tucked_points=tucked_points,
              components=[dict(object=ob.name,curves=len(raw),actually_modified_curves=int(np.any(result!=raw,axis=(1,2)).sum()),
                               exact_roots_preserved=True,maximum_displacement_m=float(np.linalg.norm(result-raw,axis=2).max()),
                               positions_before_sha256=hashlib.sha256(raw.tobytes()).hexdigest(),
                               positions_after_sha256=hashlib.sha256(result.tobytes()).hexdigest())],
              sampled_point_repairs=repairs, maximum_point_repair_m=max_repair,
              unchanged_low_posterior_fibers=int(np.all(result[weight==0]==raw[weight==0],axis=(1,2)).sum()),
              saved_control_paths='Editable pre-envelope construction guides; personal strand detail/clearance/envelope corrections are baked separately. Not live linked or simulated',
              collision_scope='Modified discrete fiber interior points checked against body; not all surfaces, clothes, segment interiors or motion',
              status='Unreviewed roller-shape study, no artistic acceptance')
(out/'shag_cut_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(out/'roller_control_design.json').write_text(json.dumps(control,indent=2),encoding='utf-8')
scene = bpy.context.scene
pref = bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX'
pref.get_devices()
for d in pref.devices:
    d.use = d.type=='OPTIX'
scene.cycles.device='GPU'
scene.cycles.samples=64
scene.cycles.use_denoising=False
scene.render.resolution_x,scene.render.resolution_y=1200,1400
scene.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['03_Side','04_Back']:
    scene.camera=bpy.data.objects[name]
    scene.render.filepath=str(renders/(name+'.png'))
    bpy.ops.render.render(write_still=True)
print('POSTERIOR_ROLLER_STUDY_RENDERED',version,len(ids),flush=True)
