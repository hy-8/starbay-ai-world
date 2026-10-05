"""Arc-length cuts or explicit spatial paths on the actual neutral groom.

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
preview_front = '--preview-front' in args
coverage_only = '--coverage-only' in args
feathered_flow = '--feathered-flow' in args
spatial_rear = '--spatial-rear' in args
loose_wave = '--loose-wave' in args
front_wave = '--front-wave' in args
transport_wave = '--transport-wave' in args
garment_clearance = '--garment-clearance' in args
free_nape = '--free-nape' in args
if free_nape and not spatial_rear:raise ValueError('Free nape requires spatial rear')
nape_extra = float(args[args.index('--nape-extra')+1]) if '--nape-extra' in args else .092
guard_transition = float(args[args.index('--guard-transition')+1]) if '--guard-transition' in args else .055
if not .04<=nape_extra<=.12 or not .03<=guard_transition<=.12:
    raise ValueError('Unsupported nape/clearance length')
if transport_wave and not front_wave:
    raise ValueError('Transported frames require front-wave')
wave_strength = float(args[args.index('--wave-strength')+1]) if '--wave-strength' in args else 1.0
if not 0<wave_strength<=1:
    raise ValueError('Wave strength must be in (0,1]')
if loose_wave and not spatial_rear:
    raise ValueError('Loose wave requires explicit spatial rear paths')
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
bpy.context.view_layer.update()
body = bpy.data.objects['CC0 male body • retained topology']
bv = BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
front = next(o for o in bpy.data.objects if not o.hide_render and o.name.startswith('Authored frontal revision'))
rear = next(o for o in bpy.data.objects if not o.hide_render and o.name.startswith('Original posterior shag'))
garment_bv=None
garment_top=None
garment_repairs=0
garment_max_shift=0.0
if garment_clearance:
    # Actual evaluated coat/collar back surfaces, in world space. A ray from
    # behind picks their exterior back envelope independent of open-shell
    # inside/outside signs. Keep all other scene geometry untouched.
    vv=[];ff=[];dg=bpy.context.evaluated_depsgraph_get()
    collar_z=[]
    for name in ['Fitted CC0 male_elegantsuit01','Tailored standing rear collar']:
        ob=bpy.data.objects[name];ev=ob.evaluated_get(dg);mesh=ev.to_mesh();mesh.calc_loop_triangles()
        xyz=[tuple(ob.matrix_world@v.co) for v in mesh.vertices]
        offset=len(vv);vv.extend(xyz)
        ff.extend([tuple(offset+i for i in tri.vertices) for tri in mesh.loop_triangles])
        if 'collar' in name:collar_z.extend(p[2] for p in xyz)
        ev.to_mesh_clear()
    garment_bv=BVHTree.FromPolygons(vv,ff,all_triangles=True)
    garment_top=max(collar_z)
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

def spatial_posterior(root, label, N):
    """New paths from roots, rather than another cut of the old shell paths.

    A short attached section leads into a free spatial sweep. Lower roots retain
    separate draping nape layers; the upper transition is continuous.
    """
    tt = np.linspace(0,1,N)
    phase = label*2.399963
    upper = float(smooth((root[2]-1.798)/.047))
    nape = float((1-smooth((root[2]-1.777)/.025))*smooth((root[1]-.008)/.045))
    side = 1 if root[0]>=0 else -1
    length = .058+.038*(.5+.5*np.sin(phase*.73))+nape_extra*nape
    release = .26+.17*upper-.12*nape
    hit, normal, _, _ = bv.find_nearest(Vector(root))
    heading = Vector((side*(.62-.45*nape)+.13*np.sin(phase),.36,-.66-.35*nape))
    heading -= normal*heading.dot(normal)
    heading.normalize()
    position = hit.copy()
    p = np.empty((N,3),float)
    normals = np.empty((N,3),float)
    p[0] = root
    normals[0] = normal
    for j in range(1,N):
        if tt[j]<release:
            candidate=position+heading*(length/(N-1))
            position,nn,_,_=bv.find_nearest(candidate)
            heading -= nn*heading.dot(nn)
            if heading.length>1e-8:heading.normalize()
            normal=nn
            lift=.0006+.004*np.sin(np.pi*tt[j]/(release*2))
            p[j]=position+normal*lift
        else:
            free=float((tt[j]-release)/(1-release))
            # Leave the head now: a smooth outward lift, then gravity. Nape
            # has less lift and keeps its broad root spread instead of a tail.
            outward=Vector((normal.x,normal.y,0))
            if outward.length>1e-8:outward.normalize()
            target=heading+outward*(.55*(1-nape)*np.sin(np.pi*free))
            target.z -= (.40+.25*nape)*free
            target.x += side*.24*np.sin(free*np.pi*1.35+phase*.31)*free
            if loose_wave:
                target.x += side*.46*(1-nape)*free**3
                target.z += .46*(1-nape)*free**3
            target.normalize()
            position += target*(length/(N-1))
            p[j]=position+normal*.0045
        normals[j]=normal
    tangent=np.gradient(p,axis=0)
    across=np.cross(tangent,normals)
    across/=np.maximum(np.linalg.norm(across,axis=1)[:,None],1e-8)
    p += across*((.003+.002*nape)*np.sin(tt*1.6*np.pi+phase)*np.sin(np.pi*tt))[:,None]
    if loose_wave:
        p += across*((.009+.004*nape)*np.sin(tt*2.05*np.pi+phase*.37)*np.sin(np.pi*tt))[:,None]
        p[:,1] += .008*nape*np.sin(tt*1.8*np.pi+phase*.47)*np.sin(np.pi*tt)
    if free_nape:
        # The scalp tangent turns inward at the neck. Real longer nape locks
        # leave that tangent and fall from their follicle depth, rather than
        # hugging the neck then making a sharp detour around the collar.
        drape_y=root[1]+.012*np.sin(np.pi*tt)+.038*tt**2
        drape_y+=.008*np.sin(tt*1.8*np.pi+phase*.47)*np.sin(np.pi*tt)
        drape_z=root[2]-.94*length*tt
        p[:,1]=p[:,1]*(1-nape)+drape_y*nape
        p[:,2]=p[:,2]*(1-nape)+drape_z*nape
    p[0]=root
    return p

def sublock(p,ids,label,crown=False,nape=False,rear_component=False):
    global garment_repairs,garment_max_shift
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
    if rear_component and spatial_rear:
        replacement=spatial_posterior(root,label,N)
        weight=1-float(smooth((root[2]-(1.834 if loose_wave else 1.816))/.024))
        new_base = new_base*(1-weight)+replacement*weight
        # Paths already have authored lengths. Independent endpoint variation
        # is applied below relative to this replacement, without re-cutting it.
        fraction=1.0
    tangent = np.gradient(new_base,axis=0)
    tangent /= np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-8)
    normals = []
    for point in new_base:
        hit, normal, face_index, distance = bv.find_nearest(Vector(point))
        normals.append(normal[:])
    normals = np.array(normals)
    across = np.cross(tangent,normals)
    across /= np.maximum(np.linalg.norm(across,axis=1)[:,None],1e-8)
    if front_wave and transport_wave and not rear_component:
        # A nearest-face normal is not a stable sculpting frame. Transport
        # one continuous lateral axis through the path instead of allowing
        # its direction to jump at skull/face surface transitions.
        for j in range(1,N):
            candidate=across[j-1]-tangent[j]*np.dot(across[j-1],tangent[j])
            norm=float(np.linalg.norm(candidate))
            if norm>1e-8:across[j]=candidate/norm
            else:across[j]=across[j-1]
        normals=np.cross(across,tangent)
        normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-8)
    # Single gentle cubic sweep, with no repeated sine curls. Upper feathers
    # get a small lifted tip; lower nape keeps a mostly downward exit.
    bend = (.0024 if rear_component else .0020)*np.sin(phase)
    envelope = 3*(1-t)*t*t
    new_base += across*(bend*envelope)[:,None]
    if rear_component and not spatial_rear:
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
    elif not rear_component:
        new_base += normals*(.0023*np.sin(phase*.73)*np.sin(np.pi*t))[:,None]
        if front_wave:
            # Vary the actual lock centers, including the crown interiors.
            # Endpoints stay close to the measured brow clearances.
            wave=wave_strength*(.009 if crown else .006)*np.sin(t*1.65*np.pi+phase*.47)*np.sin(np.pi*t)
            new_base += across*wave[:,None]
            relief=wave_strength*(.006 if crown else .0035)*np.sin(phase*.61)*np.sin(np.pi*t)**1.4
            new_base += normals*relief[:,None]
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
        if rear_component and garment_clearance:
            for j in range(1,N):
                if q[j,2]>=garment_top+guard_transition or q[j,1]<-.015:continue
                # Begin bending before the collar's top to avoid a hard kink.
                ray_z=min(float(q[j,2]),garment_top-.001)
                hit,normal,face,distance=garment_bv.ray_cast(Vector((q[j,0],.35,ray_z)),Vector((0,-1,0)),.5)
                if hit is None:continue
                weight=float(smooth((garment_top+guard_transition-q[j,2])/guard_transition))
                shift=max(0,float(hit.y)+.0025-float(q[j,1]))*weight
                if shift>0:
                    q[j,1]+=shift
                    garment_repairs+=1;garment_max_shift=max(garment_max_shift,shift)
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
    method=('Explicit scalp-root spatial posterior guides with early surface release and free draping/waving ends; independent per-fiber endpoint sampling; retain front and short coverage' if spatial_rear else 'Actual arc-length layered cuts, adjacent-root crown subdivisions, independently staggered fiber lengths and narrower ends; retain short scalp coverage'),
    components=report_components,front_only=front_only,rear_only=rear_only,gentle=gentle,coverage_only=coverage_only,
    keep_front_length=keep_front_length,preview=preview,personal_cut_applied_to_center_paths=True,feathered_flow=feathered_flow,
    spatial_rear=spatial_rear,
    loose_wave=loose_wave,
    front_wave=front_wave,front_wave_strength=wave_strength,preview_front=preview_front,
    transported_front_frame=transport_wave,
    garment_clearance=garment_clearance,garment_point_adjustments=garment_repairs,garment_maximum_y_shift_m=garment_max_shift,
    nape_extra_length_m=nape_extra,garment_bend_transition_m=guard_transition,
    free_falling_nape=free_nape,
    garment_scope='Every point on modified rear fibers in posterior collar region; ray-constrained back envelope of actual suit and rear collar, with declared upper bend transition. Not an all-garment/strand/motion collision proof' if garment_clearance else 'No new garment guard',
    median_study_paths=len(guide_studies),guide_status='Baked evidence only; not live-linked',
    status='Unreviewed real 3D hair study; no artistic or animation approval',
    collision_scope='Every fourth interior hair point with smoothed correction; not exhaustive scalp/eyes/clothes/strand or motion verification',
    license='Modified front/posterior fibers original; retained Bystedt CC BY-SA and Abhay Pratap Royalty Free short support unchanged; hidden licensed donor geometry local',
    samples=scene.cycles.samples,draft='--draft' in args,denoising=False)
(out/'shag_cut_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in (['01_Front','02_ThreeQuarter'] if preview_front else ['03_Side','04_Back'] if preview else ['01_Front','02_ThreeQuarter','03_Side','04_Back']):
    scene.camera=bpy.data.objects[name]
    scene.render.filepath=str(render/(name+'.png'))
    bpy.ops.render.render(write_still=True)
print('REFERENCE_SHAG_CUT_RENDERED',version,flush=True)
