"""Arc-length layer cuts and root-sorted sublocks on the actual neutral groom.

Edits real native fibers in a fresh version. Exact roots, face, UV and short
coverage are retained. Saved guide studies are evidence, not live drivers.
"""
import bpy, sys, re, json, hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
args = sys.argv[sys.argv.index('--')+1:]
version, source_version = args[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in args[:2]):
    raise ValueError(args)
out, render = ROOT/'Exports'/version, ROOT/'Renders'/version
if out.exists() or render.exists():
    raise RuntimeError('Fresh output required')
source = ROOT/'Exports'/source_version/'Ember_Regent.blend'
front_only = '--front-only' in args
rear_only = '--rear-only' in args
if front_only and rear_only:
    raise ValueError('Choose one isolated component or the complete study')
gentle = '--gentle' in args
keep_front_length = '--keep-front-length' in args
preview = '--preview' in args
coverage_only = '--coverage-only' in args
feathered_flow = '--feathered-flow' in args
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
bpy.context.view_layer.update()
body = bpy.data.objects['CC0 male body • retained topology']
bv = BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
front = next(o for o in bpy.data.objects if not o.hide_render and o.name.startswith('Authored frontal revision'))
rear = next(o for o in bpy.data.objects if not o.hide_render and o.name.startswith('Original posterior shag'))
if not np.allclose(np.array(front.matrix_world),np.eye(4)) or not np.allclose(np.array(rear.matrix_world),np.eye(4)):
    raise RuntimeError('Requires neutral world-aligned groom')
records = json.loads((ROOT/'Exports/spatialfringe17/authored_fringe_design.json').read_text(encoding='utf-8'))
rng = np.random.default_rng(100445)
guide_studies = []
report_components = []

def read(ob):
    sizes = [len(c.points) for c in ob.data.curves]
    if len(set(sizes))!=1:
        raise RuntimeError('Uniform native curve points required')
    p = np.empty(len(ob.data.points)*3,np.float32)
    ob.data.attributes['position'].data.foreach_get('vector',p)
    return p.reshape(-1,sizes[0],3)

def smooth(x):
    x = np.clip(x,0,1)
    return x*x*(3-2*x)

def sample_arc(p,q):
    arc = np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
    return np.stack([np.interp(q*arc[-1],arc,p[:,k]) for k in range(3)],axis=1)

def sublock(p,ids,label,crown=False,nape=False,rear_component=False):
    old = p[ids].astype(float)
    N = old.shape[1]
    t = np.linspace(0,1,N)
    base = np.median(old,axis=0)
    root = base[0]
    upper = float(smooth((root[2]-1.795)/.045))
    side = 1 if root[0]>=0 else -1
    phase = (label*2.399963)%6.283185
    # Narrow overlying feathers, fuller longer nape. Each actual fiber has its
    # own cut length, rather than one repeated patch ending on a broad band.
    if rear_component:
        fraction = (.69+.17*(.5+.5*np.sin(phase))) if upper>.4 else (.92 if nape else .83)
        if feathered_flow:
            fraction = (.89+.09*(.5+.5*np.sin(phase))) if upper>.4 else (.99 if nape else .93)
    else:
        fraction = (.78+.18*(.5+.5*np.cos(phase))) if crown else (.93 if label%3 else .86)
        if keep_front_length:
            fraction = 1.0
    if gentle:
        fraction = 1-(1-fraction)*.55
    new_base = sample_arc(base,t*fraction)
    tangent = np.gradient(new_base,axis=0)
    tangent /= np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-8)
    normals = []
    for point in new_base:
        hit, normal, face_index, distance = bv.find_nearest(Vector(point))
        normals.append(normal[:])
    normals = np.array(normals)
    across = np.cross(tangent,normals)
    across /= np.maximum(np.linalg.norm(across,axis=1)[:,None],1e-8)
    # Single gentle cubic sweep, with no repeated sine curls. Upper feathers
    # get a small lifted tip; lower nape keeps a mostly downward exit.
    bend = (.0024 if rear_component else .0020)*np.sin(phase)
    envelope = 3*(1-t)*t*t
    new_base += across*(bend*envelope)[:,None]
    if rear_component:
        relief = (.0035 if not gentle else .0020)*upper*np.sin(np.pi*t)
        relief += (.0035 if not gentle else .0020)*upper*t**3
        new_base += normals*relief[:,None]
        new_base[:,0] += side*(.0020 if nape else .0035)*t**4
        if feathered_flow:
            # Explicit detached feather tips instead of the old downward
            # tangent/gravity shell. Upper side/back tips leave the scalp,
            # rise and turn laterally; the lower nape stays long/downward.
            horizontal = normals.copy()
            horizontal[:,2] = 0
            horizontal /= np.maximum(np.linalg.norm(horizontal,axis=1)[:,None],1e-8)
            new_base += horizontal*(upper*(.012*np.sin(np.pi*t)+.010*t**3))[:,None]
            new_base[:,2] += upper*.018*t**3
            new_base += across*(.007*np.sin(phase*.71)*3*(1-t)*t*t)[:,None]
    else:
        new_base += normals*(.0023*np.sin(phase*.73)*np.sin(np.pi*t))[:,None]
    new_base[0] = base[0]
    guide_studies.append(new_base)
    result = np.empty_like(old,dtype=np.float32)
    for i,fiber in enumerate(old):
        personal = fraction*rng.uniform(.78,1) if rear_component else fraction*rng.uniform(.97 if keep_front_length else .89,1)
        if gentle:
            personal = fraction*(.5+.5*personal/fraction)
        sampled = sample_arc(fiber,t*personal)
        old_base_sample = sample_arc(base,t*personal)
        personal_base = sample_arc(new_base,t*personal/fraction)
        offsets = sampled-old_base_sample
        # End width is reduced independently of cut length. The root fan is
        # kept exactly; the separate short support covers the spaces below.
        width = 1-(.65 if rear_component else .38)*smooth(t/.82)
        if gentle:
            width = 1-(1-width)*.60
        q = personal_base+offsets*width[:,None]
        q += rng.normal(0,.0006,3)[None]*t[:,None]**3
        # Sample contact repair displacements, smooth along the whole path.
        # This is only a point-sampled guard, never a full collision proof.
        corrections = np.zeros_like(q)
        indices = np.unique(np.r_[np.arange(4,N,4),N-1])
        for j in indices:
            hit, normal, face_index, distance = bv.find_nearest(Vector(q[j]))
            gap = (Vector(q[j])-hit).dot(normal)
            if gap<.0008 and distance<.025:
                corrections[j] = np.array(normal)*(.001-gap)
        if np.any(corrections):
            for k in range(3):
                corrections[:,k] = np.interp(t,t[indices],corrections[indices,k],left=0)
            q += corrections*smooth(t/.15)[:,None]
        q[0] = fiber[0]
        result[i] = q
    return result

for ob,is_rear in [(front,False),(rear,True)]:
    if coverage_only:
        continue
    if front_only and is_rear or rear_only and not is_rear:
        continue
    raw = read(ob)
    result = raw.copy()
    groups = []
    if is_rear:
        # Spatial guide partitions are irregular; nearest-root groups remain
        # local on the actual scalp and do not mix opposite sides of the head.
        roots = raw[:,0].astype(float)
        pool = roots[::16]
        # Original posterior sampling used 64k probability draws then 128k
        # barycentric draws. Match its farthest-point seed rather than
        # introducing coarse partitions that average neighboring wave flows.
        partition_rng = np.random.default_rng(100409)
        partition_rng.random(64000)
        partition_rng.random((64000,2))
        selected = [int(partition_rng.integers(len(pool)))]
        dmin = np.full(len(pool),np.inf)
        while len(selected)<240:
            d = np.sum((pool-pool[selected[-1]])**2,axis=1)
            dmin = np.minimum(dmin,d)
            selected.append(int(np.argmax(dmin)))
        centers = pool[selected]
        labels = np.empty(len(roots),int)
        for start in range(0,len(roots),2048):
            distances = np.sum((roots[start:start+2048,None]-centers[None])**2,axis=2)
            labels[start:start+2048] = np.argmin(distances,axis=1)
        for label in range(len(centers)):
            ids = np.flatnonzero(labels==label)
            if len(ids):groups.append((ids,label,False,centers[label,2]<1.799 and centers[label,1]>.020))
    else:
        assert sum(r['assigned_visible_fibers'] for r in records)==len(raw)
        offset = 0
        for label,record in enumerate(records):
            count = record['assigned_visible_fibers']
            ids = np.arange(offset,offset+count)
            # Root-sort subdivisions keep adjacent follicles together, not
            # interleaved copies of the same broad fan.
            group = raw[ids]
            direction = np.median(group,axis=0)[min(5,raw.shape[1]-1)]-np.median(group[:,0],axis=0)
            normal = np.array(bv.find_nearest(Vector(np.median(group[:,0],axis=0)))[1])
            across = np.cross(direction,normal)
            ordered = ids[np.argsort(raw[ids,0]@across)]
            parts = np.array_split(ordered,2 if 'segmented crown' in record['name'] else 1)
            for child,part in enumerate(parts):
                groups.append((part,label*2+child,'segmented crown' in record['name'],False))
            offset += count
    for gi,(ids,label,crown,nape) in enumerate(groups):
        result[ids] = sublock(raw,ids,label,crown,nape,is_rear)
    assert np.isfinite(result).all() and np.array_equal(raw[:,0],result[:,0])
    data = ob.data.copy()
    data.attributes['position'].data.foreach_set('vector',result.ravel())
    # Regenerate the taper for newly cut fibers instead of retaining old blunt
    # cut radii, preserving each original root radius.
    radii = np.empty(len(ob.data.points),np.float32)
    ob.data.attributes['radius'].data.foreach_get('value',radii)
    radii = radii.reshape(len(raw),-1)
    taper = (1-.997*np.linspace(0,1,raw.shape[1])[None]**2.6)**.7
    radii = radii[:,0,None]*taper
    data.attributes['radius'].data.foreach_set('value',radii.astype(np.float32).ravel())
    ob.data = data
    before_arc = np.linalg.norm(np.diff(raw,axis=1),axis=2).sum(axis=1)
    after_arc = np.linalg.norm(np.diff(result,axis=1),axis=2).sum(axis=1)
    report_components.append(dict(object=ob.name,curves=len(raw),local_groups=len(groups),exact_roots_preserved=True,
        actual_fiber_arc_before_quantiles_m=np.quantile(before_arc,[0,.5,.95,1]).tolist(),
        actual_fiber_arc_after_quantiles_m=np.quantile(after_arc,[0,.5,.95,1]).tolist(),
        maximum_displacement_m=float(np.linalg.norm(result-raw,axis=2).max()),
        positions_before_sha256=hashlib.sha256(raw.tobytes()).hexdigest(),positions_after_sha256=hashlib.sha256(result.tobytes()).hexdigest()))
    print('RESTYLED_COMPONENT',ob.name,len(groups),flush=True)

if coverage_only:
    coverage = next(o for o in bpy.data.objects if not o.hide_render and o.name.startswith('Original posterior coverage'))
    raw = read(coverage)
    result = np.empty_like(raw)
    N = raw.shape[1]
    t = np.linspace(0,1,N)
    for i,fiber in enumerate(raw):
        length = float(np.linalg.norm(np.diff(fiber,axis=0),axis=1).sum())
        target = rng.uniform(.018,.029)
        result[i] = sample_arc(fiber,t*min(1,target/max(length,1e-9)))
        result[i,0] = raw[i,0]
    assert np.array_equal(raw[:,0],result[:,0]) and np.isfinite(result).all()
    data = coverage.data.copy()
    data.attributes['position'].data.foreach_set('vector',result.ravel())
    r = np.empty(len(data.points),np.float32)
    coverage.data.attributes['radius'].data.foreach_get('value',r)
    root_radius = r.reshape(len(raw),N)[:,0,None]
    radius = root_radius*(1-.997*t[None]**2.6)**.7
    data.attributes['radius'].data.foreach_set('value',radius.astype(np.float32).ravel())
    coverage.data = data
    before_arc = np.linalg.norm(np.diff(raw,axis=1),axis=2).sum(axis=1)
    after_arc = np.linalg.norm(np.diff(result,axis=1),axis=2).sum(axis=1)
    report_components.append(dict(object=coverage.name,curves=len(raw),exact_roots_preserved=True,
        method='Shorten real coverage fibers along their original growth arcs to 18..29mm; keep every root and regenerate taper',
        actual_fiber_arc_before_quantiles_m=np.quantile(before_arc,[0,.5,.95,1]).tolist(),
        actual_fiber_arc_after_quantiles_m=np.quantile(after_arc,[0,.5,.95,1]).tolist(),
        positions_before_sha256=hashlib.sha256(raw.tobytes()).hexdigest(),positions_after_sha256=hashlib.sha256(result.tobytes()).hexdigest()))
    print('SHORTENED_COVERAGE',len(raw),flush=True)

# Retain sparse actual median design paths for inspection; the dense baked
# fibers remain the rendered geometry and are not live-linked to these guides.
col = bpy.data.collections.new('Shag cut median studies • baked reference only')
bpy.context.scene.collection.children.link(col)
cu = bpy.data.curves.new('Median path studies, not live groom controls','CURVE')
cu.dimensions = '3D'
for guide in guide_studies:
    spline = cu.splines.new('POLY')
    spline.points.add(len(guide)-1)
    for point,p in zip(spline.points,guide):point.co=(*p,1)
ob = bpy.data.objects.new('Median paths • edits do not update baked fibers',cu)
col.objects.link(ob)
ob.hide_render = True
ob.hide_viewport = True
scene = bpy.context.scene
pref = bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=64 if '--draft' in args else 192
scene.cycles.use_denoising=False
scene.render.resolution_x,scene.render.resolution_y=1200,1400
scene.render.resolution_percentage=80 if '--draft' in args else 100
out.mkdir(parents=True);render.mkdir(parents=True)
report=dict(version=version,source=source_version,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    method='Actual arc-length layered cuts, adjacent-root crown subdivisions, independently staggered fiber lengths and narrower ends; retain short scalp coverage',
    components=report_components,front_only=front_only,rear_only=rear_only,gentle=gentle,coverage_only=coverage_only,
    keep_front_length=keep_front_length,preview=preview,personal_cut_applied_to_center_paths=True,feathered_flow=feathered_flow,
    median_study_paths=len(guide_studies),guide_status='Baked evidence only; not live-linked',
    status='Unreviewed real 3D hair study; no artistic or animation approval',
    collision_scope='Every fourth interior hair point with smoothed correction; not exhaustive scalp/eyes/clothes/strand or motion verification',
    license='Modified front/posterior fibers original; retained Bystedt CC BY-SA and Abhay Pratap Royalty Free short support unchanged; hidden licensed donor geometry local',
    samples=scene.cycles.samples,draft='--draft' in args,denoising=False)
(out/'shag_cut_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in (['03_Side','04_Back'] if preview else ['01_Front','02_ThreeQuarter','03_Side','04_Back']):
    scene.camera=bpy.data.objects[name]
    scene.render.filepath=str(render/(name+'.png'))
    bpy.ops.render.render(write_still=True)
print('REFERENCE_SHAG_CUT_RENDERED',version,flush=True)
