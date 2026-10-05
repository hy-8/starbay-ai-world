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
preview_crown = '--preview-crown' in args
coverage_only = '--coverage-only' in args
feathered_flow = '--feathered-flow' in args
spatial_rear = '--spatial-rear' in args
loose_wave = '--loose-wave' in args
front_wave = '--front-wave' in args
redirect_crown = '--redirect-crown' in args
retain_crown_arch = '--retain-crown-arch' in args
affine_crown_turn = '--affine-crown-turn' in args
free_crown_tips = '--free-crown-tips' in args
soft_crown_exits = '--soft-crown-exits' in args
rebuild_crown_flow = '--rebuild-crown-flow' in args
if rebuild_crown_flow and not front_only:raise ValueError('Crown rebuilding requires front-only')
rebuild_rear_crown = '--rebuild-rear-crown' in args
if rebuild_rear_crown and not rear_only:raise ValueError('Posterior crown rebuilding requires rear-only')
lifted_rear_layers = '--lifted-rear-layers' in args
if lifted_rear_layers and not rebuild_rear_crown:raise ValueError('Lifted layers require posterior crown rebuild')
clumped_rear_layers = '--clumped-rear-layers' in args
if clumped_rear_layers and not lifted_rear_layers:raise ValueError('Clumped layers require lifted layers')
if soft_crown_exits and not free_crown_tips:raise ValueError('Soft exits require free crown tips')
if free_crown_tips and not redirect_crown:raise ValueError('Free tips require crown redirect')
if affine_crown_turn and not redirect_crown:raise ValueError('Affine turn requires crown redirect')
fringe_sweep = '--fringe-sweep' in args
if fringe_sweep and not front_only:raise ValueError('Fringe sweep is isolated to front-only')
recover_nape_fan = '--recover-nape-fan' in args
retain_personal_nape = '--retain-personal-nape' in args
if retain_personal_nape and not recover_nape_fan:raise ValueError('Personal nape requires fan recovery')
if recover_nape_fan and not rear_only:raise ValueError('Nape fan is isolated to rear-only')
if retain_crown_arch and not redirect_crown:raise ValueError('Arch requires crown redirect')
if redirect_crown and not front_only:
    raise ValueError('Crown direction study is isolated to front-only')
transport_wave = '--transport-wave' in args
garment_clearance = '--garment-clearance' in args
free_nape = '--free-nape' in args
layered_nape = '--layered-nape' in args
if layered_nape and not (spatial_rear and free_nape):raise ValueError('Layered nape requires spatial rear and free nape')
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
    if layered_nape:
        # Longer lower layers include the occipital roots above the neckline.
        # This adds overlapping lengths using existing follicles, instead of
        # broadening only a few thin bottom-root patches into a sheer fan.
        nape=float((1-smooth((root[2]-1.788)/.035))*smooth((root[1]-.015)/.040))
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

def trace_rear_crown(root,label,N):
    """Attached scalp growth followed by a smooth gravity exit, no old curls."""
    tt=np.linspace(0,1,N);phase=label*2.399963
    side=1 if root[0]>=(.014 if clumped_rear_layers else 0) else -1
    length=(.122 if clumped_rear_layers else .104 if lifted_rear_layers else .086)+.018*np.sin(phase*.73)
    release=.36 if lifted_rear_layers else .52
    position,normal,_,_=bv.find_nearest(Vector(root))
    heading=Vector((side*(.85 if clumped_rear_layers else .48),.55 if clumped_rear_layers else .92,-.15))
    heading-=normal*heading.dot(normal);heading.normalize()
    p=np.empty((N,3),float);p[0]=root
    for j in range(1,N):
        if tt[j]<release:
            position,nn,_,_=bv.find_nearest(position+heading*length/(N-1))
            heading-=nn*heading.dot(nn);heading.normalize();normal=nn
            lift=(.019+.004*np.sin(phase*.47)) if clumped_rear_layers else .014 if lifted_rear_layers else .007
            p[j]=position+normal*(.0007+lift*np.sin(.5*np.pi*tt[j]/release))
        else:
            if tt[j-1]<release:position=Vector(p[j-1])
            u=(tt[j]-release)/(1-release)
            direction=heading+normal*((.23 if lifted_rear_layers else .10)*np.sin(np.pi*u))
            direction.z-=(.68 if lifted_rear_layers else .78)*np.sin(.5*np.pi*u)
            if lifted_rear_layers:direction.x+=side*.30*np.sin(np.pi*u)
            direction.normalize();position+=direction*length/(N-1)
            p[j]=position
    if lifted_rear_layers:
        p[:,0]+=.006*np.sin(tt*1.55*np.pi+phase*.39)*np.sin(np.pi*tt)
        p[:,1]+=.002*np.sin(tt*1.5*np.pi+phase*.39)*np.sin(np.pi*tt)
    return p

def sublock(p,ids,label,crown=False,nape=False,rear_component=False,name=''):
    global garment_repairs,garment_max_shift
    old = p[ids].astype(float)
    if rebuild_rear_crown and float(old[:,0,2].max())<1.825:return old.astype(np.float32)
    if rebuild_crown_flow and not crown and not fringe_sweep:return old.astype(np.float32)
    if redirect_crown and not crown and not fringe_sweep:return old.astype(np.float32)
    if fringe_sweep and crown and not (redirect_crown or rebuild_crown_flow):return old.astype(np.float32)
    N = old.shape[1]
    t = np.linspace(0,1,N)
    base = np.median(old,axis=0)
    root = base[0]
    if recover_nape_fan and (not rear_component or root[2]>1.792 or root[1]<.035):
        return old.astype(np.float32)
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
    if rebuild_rear_crown:
        new_base=trace_rear_crown(root,label,N);fraction=1.0
    if recover_nape_fan:
        new_base=base.copy();fraction=1.0
    if rebuild_crown_flow and crown:
        # Rebuild the full center, not an endpoint displacement of an already
        # twisted path. Follicles stay exact. Surface tracing is restricted to
        # the attached root section; free tips retain a continuous exit tangent.
        lateral='lateral scissor layer' in name
        side=-1 if name.startswith('heavy') else 1
        length=(.105 if lateral else .155)+.013*np.sin(label*.53)
        release=.44 if lateral else .38
        position,normal,_,_=bv.find_nearest(Vector(root))
        heading=Vector((side*(.86 if lateral else .60),-.72,-.06))
        heading-=normal*heading.dot(normal);heading.normalize()
        new_base=np.empty((N,3),float);new_base[0]=root
        for j in range(1,N):
            if t[j]<release:
                position,nn,_,_=bv.find_nearest(position+heading*length/(N-1))
                heading-=nn*heading.dot(nn);heading.normalize();normal=nn
                lift=.001+.009*np.sin(.5*np.pi*t[j]/release)
                new_base[j]=position+normal*lift
                if j==int(release*(N-1)):position=Vector(new_base[j])
            else:
                if t[j-1]<release:position=Vector(new_base[j-1])
                u=(t[j]-release)/(1-release)
                outward=Vector((normal.x,normal.y,0))
                if outward.length>1e-8:outward.normalize()
                direction=heading+outward*(.12*np.sin(np.pi*u))
                direction.z-=.85*np.sin(.5*np.pi*u)
                direction.x+=side*.12*np.sin(1.2*np.pi*u)
                direction.normalize();position+=direction*length/(N-1)
                new_base[j]=position
        fraction=1.0
    if redirect_crown and crown:
        # Redirect the actual short overlay centers, keeping the longer brow
        # layers. This changes the head's flow rather than adding another wave
        # to all of its old parallel paths. Root/face/coverage stay intact.
        lateral_layer='lateral scissor layer' in name
        direction=-1 if name.startswith(('heavy','short heavy')) else 1
        end_shift=np.array([direction*(.004 if lateral_layer else .001),
            (.038+.010*np.sin(label*.71)) if lateral_layer else .007,
            (.004 if retain_crown_arch else -.024) if lateral_layer else -.003])
        if affine_crown_turn and lateral_layer:
            # Turn the entire overlay path by shortening its forward reach.
            # End-only dragging left the earlier path in front of the new tip
            # and created a local return loop visible in profile.
            new_base=root[None]+(new_base-root[None])*np.array([.95,.60,.95])[None]
        else:
            new_base += end_shift[None]*smooth(t/.94)[:,None]
            new_base[:,2] -= (.002 if retain_crown_arch else .005)*np.sin(np.pi*t)
        if free_crown_tips and lateral_layer:
            # Replace the returning last part of a short overlay with a free
            # exit from its current tangent. Retain the attached root section;
            # do not move one endpoint backward through an existing arc.
            release_index=int(.56*(N-1))
            remaining=float(np.linalg.norm(np.diff(new_base[release_index:],axis=0),axis=1).sum())
            heading=new_base[release_index]-new_base[release_index-3]
            heading/=max(float(np.linalg.norm(heading)),1e-8)
            hit,nn,_,_=bv.find_nearest(Vector(new_base[release_index]))
            normal=np.array(nn)
            heading-=normal*min(0,float(np.dot(heading,normal)))
            exit_normal=normal.copy()
            if soft_crown_exits:
                exit_normal[2]=0
                exit_normal/=max(float(np.linalg.norm(exit_normal)),1e-8)
            position=new_base[release_index].copy()
            for j in range(release_index+1,N):
                u=(j-release_index)/(N-1-release_index)
                direction=heading+exit_normal*((.16 if soft_crown_exits else .30)*np.sin(np.pi*u*.8))
                direction[2]-=.80*np.sin(.5*np.pi*u) if soft_crown_exits else .22*u
                direction/=max(float(np.linalg.norm(direction)),1e-8)
                position+=direction*remaining/(N-1-release_index)
                new_base[j]=position
    if fringe_sweep and not crown:
        # Broad horizontal shaping uses a stable world-space plane rather
        # than lifting strands with rapidly changing nearest-face frames.
        # Neighboring children retain one parent flow; all endpoints remain
        # close to their already measured brow/temple locations.
        parent=re.search(r'(forehead|temple) (\d+)',name)
        if parent:
            parent_index=int(parent.group(2))
            phase0=parent_index*.83+(0 if name.startswith('heavy') else 1.1)
            amp=.010 if parent.group(1)=='forehead' else .006
            envelope=4*t*(1-t)
            new_base[:,0]+=amp*np.cos(np.pi*t+phase0)*envelope
            new_base[:,1]+=.003*np.sin(np.pi*t+phase0)*envelope
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
    if retain_personal_nape:new_base=base.copy()
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
        if redirect_crown or fringe_sweep:width=np.ones_like(t)
        if gentle:
            width = 1-(1-width)*.60
        q = personal_base+offsets*width[:,None]
        if rebuild_rear_crown:
            root_offset=fiber[0]-base[0]
            q=personal_base+root_offset[None]*(1-(.82 if clumped_rear_layers else .35)*smooth(t/.9))[:,None]
            q+=rng.normal(0,.0007,3)[None]*np.sin(np.pi*t)[:,None]
        if rebuild_crown_flow and crown:
            # Old interior offsets also contained the knots. Replace them with
            # a follicle-spread field and small coherent individual deviations,
            # rather than transporting the old curls onto the new center.
            root_offset=fiber[0]-base[0]
            q=personal_base+root_offset[None]*(1-.45*smooth(t/.9))[:,None]
            scatter=rng.normal(0,.0010,3)
            q+=scatter[None]*(np.sin(np.pi*t))[:,None]
        if recover_nape_fan:
            # Repeated narrowing compounded the inherited endpoint offsets.
            # Recover a coherent root-spread fan on the actual current median
            # center path, with independent endpoint sampling. Strand counts
            # and exact follicles are unchanged; no new blanket hair shell.
            personal=rng.uniform(.86,1.0)
            personal_base=sample_arc(new_base,t*personal)
            root_offset=fiber[0]-base[0]
            fan_width=1-.45*smooth(t/.92)
            q=personal_base+root_offset[None]*fan_width[:,None]
            if retain_personal_nape:
                # Keep the already staggered real strand paths/ends. Add back
                # root-spread width continuously, without averaging their
                # independent length variations into a sheer flat curtain.
                q=fiber+root_offset[None]*(.55*smooth(t/.82))[:,None]
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
        if rebuild_rear_crown:
            weight=float(smooth((fiber[0,2]-1.825)/.020))
            q=fiber*(1-weight)+q*weight
            q[0]=fiber[0]
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
            if len(ids):groups.append((ids,label,False,centers[label,2]<1.799 and centers[label,1]>.020,''))
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
                groups.append((part,label*2+child,'segmented crown' in record['name'],False,record['name']))
            offset += count
    for gi,(ids,label,crown,nape,name) in enumerate(groups):
        result[ids] = sublock(raw,ids,label,crown,nape,is_rear,name)
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
        actually_modified_curves=int(np.any(result!=raw,axis=(1,2)).sum()),
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
    method=('Rebuild upper posterior centers from actual scalp roots and replace inherited curly interior offsets, continuous root-height transition; retain lower nape and frontal groom' if rebuild_rear_crown else 'Rebuild complete frontal crown centers from scalp-traced attachment and free gravity exits; replace inherited internal offsets with follicle spread; retain brow/temple' if rebuild_crown_flow else 'Explicit scalp-root spatial posterior guides with early surface release and free draping/waving ends; independent per-fiber endpoint sampling; retain front and short coverage' if spatial_rear else 'Recover nape root-spread width on existing actual center/individual paths; existing follicles and strand count retained' if recover_nape_fan else 'Redirect short crown layers toward sides/back, retain longer brow layers; optional broad planar forehead/temple center sweeps; exact roots retained' if redirect_crown or fringe_sweep else 'Actual arc-length layered cuts, adjacent-root crown subdivisions, independently staggered fiber lengths and narrower ends; retain short scalp coverage'),
    components=report_components,front_only=front_only,rear_only=rear_only,gentle=gentle,coverage_only=coverage_only,
    keep_front_length=keep_front_length,preview=preview,personal_cut_applied_to_center_paths=True,feathered_flow=feathered_flow,
    spatial_rear=spatial_rear,
    loose_wave=loose_wave,
    front_wave=front_wave,front_wave_strength=wave_strength,preview_front=preview_front,
    crown_direction_redirect=redirect_crown,
    crown_arch_retained=retain_crown_arch,
    whole_crown_forward_reach_scaled=affine_crown_turn,preview_crown=preview_crown,
    free_short_crown_exits=free_crown_tips,
    soft_horizontal_crown_exits=soft_crown_exits,
    full_crown_flow_rebuilt=rebuild_crown_flow,
    upper_posterior_flow_rebuilt=rebuild_rear_crown,
    upper_posterior_lifted_layers=lifted_rear_layers,
    upper_posterior_clumped_layers=clumped_rear_layers,
    planar_fringe_sweep=fringe_sweep,
    nape_root_fan_recovery=recover_nape_fan,
    nape_personal_paths_retained=retain_personal_nape,
    transported_front_frame=transport_wave,
    garment_clearance=garment_clearance,garment_point_adjustments=garment_repairs,garment_maximum_y_shift_m=garment_max_shift,
    nape_extra_length_m=nape_extra,garment_bend_transition_m=guard_transition,
    free_falling_nape=free_nape,
    longer_occipital_nape_layers=layered_nape,
    garment_scope='Every point on modified rear fibers in posterior collar region; ray-constrained back envelope of actual suit and rear collar, with declared upper bend transition. Not an all-garment/strand/motion collision proof' if garment_clearance else 'No new garment guard',
    median_study_paths=len(guide_studies),guide_status='Baked evidence only; not live-linked',
    status='Unreviewed real 3D hair study; no artistic or animation approval',
    collision_scope='Every fourth interior hair point with smoothed correction; not exhaustive scalp/eyes/clothes/strand or motion verification',
    license='Modified front/posterior fibers original; retained Bystedt CC BY-SA and Abhay Pratap Royalty Free short support unchanged; hidden licensed donor geometry local',
    samples=scene.cycles.samples,draft='--draft' in args,denoising=False)
(out/'shag_cut_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in (['01_Front','03_Side'] if preview_crown else ['01_Front','02_ThreeQuarter'] if preview_front else ['03_Side','04_Back'] if preview else ['01_Front','02_ThreeQuarter','03_Side','04_Back']):
    scene.camera=bpy.data.objects[name]
    scene.render.filepath=str(render/(name+'.png'))
    bpy.ops.render.render(write_still=True)
print('REFERENCE_SHAG_CUT_RENDERED',version,flush=True)
