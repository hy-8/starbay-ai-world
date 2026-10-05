"""Isolated upper posterior scissor layers; retain lower nape and front.

Independent existing fibers receive actual arc cuts and outward feather exits.
No new globally oscillating wave field or altered roots.
"""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version,source_version=args[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in args[:2]):raise ValueError(args)
out,renders=ROOT/'Exports'/version,ROOT/'Renders'/version
if out.exists() or renders.exists():raise RuntimeError('Fresh version required')
source=ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
bpy.context.view_layer.update()
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
rear=next(o for o in bpy.data.objects if not o.hide_render and o.name.startswith('Original posterior shag'))
if not np.allclose(np.array(rear.matrix_world),np.eye(4)):raise RuntimeError('Neutral groom required')
p=np.empty(len(rear.data.points)*3,np.float32);rear.data.attributes['position'].data.foreach_get('vector',p)
N=len(rear.data.curves[0].points);p=p.reshape(-1,N,3);q=p.copy()
def smooth(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)
t=np.linspace(0,1,N)
root=p[:,0].astype(float)
include_side='--include-side' in args
weight=smooth((root[:,2]-(1.807 if include_side else 1.817))/.028)
if not include_side:weight*=smooth((root[:,1]-.005)/.025)
ids=np.flatnonzero(weight>0)
repairs=0;fractions=[]
cubic_guides='--cubic-guides' in args
layer_variety='--layer-variety' in args
if layer_variety and not cubic_guides:raise ValueError('Layer variety requires whole cubic guides')
for i in ids:
    if cubic_guides:break
    fiber=p[i].astype(float)
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(fiber,axis=0),axis=1))]
    # Adjacent follicles share scissor rhythm; no random opposing lock waves.
    target=.077+.014*np.sin(root[i,0]*110+root[i,1]*67)
    fraction=min(1,target/max(arc[-1],1e-8));fractions.append(fraction)
    cut=np.stack([np.interp(t*arc[-1]*fraction,arc,fiber[:,k]) for k in range(3)],axis=1)
    side=np.tanh(root[i,0]/.015)
    cut[:,0]+=side*.013*t**5
    cut[:,1]+=.009*t**5
    cut[:,2]+=.006*t**5
    cut=fiber*(1-weight[i])+cut*weight[i]
    for j in range(4,N,4):
        hit,normal,_,distance=bv.find_nearest(Vector(cut[j]));gap=(Vector(cut[j])-hit).dot(normal)
        if gap<.0008 and distance<.025:
            cut[j]+=np.array(normal)*(.001-gap);repairs+=1
    cut[0]=fiber[0];q[i]=cut
if cubic_guides:
    pool=root[ids[::8]];selected=[len(pool)//2];dmin=np.full(len(pool),np.inf)
    for _ in range(219):
        dmin=np.minimum(dmin,np.sum((pool-pool[selected[-1]])**2,axis=1));selected.append(int(np.argmax(dmin)))
    centers=pool[selected];labels=np.empty(len(ids),int)
    for start in range(0,len(ids),2048):
        labels[start:start+2048]=np.argmin(np.sum((root[ids[start:start+2048],None]-centers[None])**2,axis=2),axis=1)
    rng=np.random.default_rng(100507)
    for label in range(len(centers)):
        members=ids[labels==label]
        if not len(members):continue
        r0=np.median(root[members],axis=0)
        side=-1 if r0[0]<.014 else 1
        phase=r0[0]*55+r0[1]*33+r0[2]*9
        a=r0+np.array([side*(.038+.008*np.sin(phase)),.012,.020])
        b=r0+np.array([side*.082,.045+.006*np.sin(phase),-.035])
        e=r0+np.array([side*(.058+.010*np.sin(phase)),.035,-.067-.009*np.cos(phase)])
        if layer_variety:
            # Explicit independent parent lengths and exits, instead of one
            # smooth identical crown bowl repeated over all scalp patches.
            design_rng=np.random.default_rng(100508+label)
            end_shift=np.array([side*design_rng.uniform(.035,.074),design_rng.uniform(.016,.047),-design_rng.uniform(.045,.115)])
            e=r0+end_shift
            a=r0+np.array([side*design_rng.uniform(.021,.044),design_rng.uniform(.002,.012),design_rng.uniform(.008,.023)])
            b=r0+.5*end_shift+np.array([side*design_rng.uniform(.015,.028),design_rng.uniform(-.006,.007),.010])
        guide=(1-t)[:,None]**3*r0+3*((1-t)**2*t)[:,None]*a+3*((1-t)*t*t)[:,None]*b+t[:,None]**3*e
        arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(guide,axis=0),axis=1))]
        for i in members:
            length=rng.uniform(.84,1.0)
            personal=np.stack([np.interp(t*length*arc[-1],arc,guide[:,k]) for k in range(3)],axis=1)
            personal+=(root[i]-r0)[None]*(1-.70*smooth(t/.90))[:,None]
            personal+=rng.normal(0,.0004,3)[None]*np.sin(np.pi*t)[:,None]
            candidate=p[i]*(1-weight[i])+personal*weight[i]
            for j in range(1,N):
                hit,normal,_,distance=bv.find_nearest(Vector(candidate[j]));gap=(Vector(candidate[j])-hit).dot(normal)
                if gap<.0008 and distance<.025:candidate[j]+=np.array(normal)*(.001-gap);repairs+=1
            candidate[0]=p[i,0];q[i]=candidate
gather_tips='--gather-tips' in args
gather_groups=0
if gather_tips:
    # Scissors exposed wider interiors of the old bundles. Gather only the
    # newly shortened ends into local scalp neighborhoods, rather than leaving
    # a diffuse spray across the entire silhouette. No root movement.
    pool=root[ids[::8]];selected=[len(pool)//2];dmin=np.full(len(pool),np.inf)
    for _ in range(219):
        dmin=np.minimum(dmin,np.sum((pool-pool[selected[-1]])**2,axis=1));selected.append(int(np.argmax(dmin)))
    centers=pool[selected];labels=np.empty(len(ids),int)
    for start in range(0,len(ids),2048):
        labels[start:start+2048]=np.argmin(np.sum((root[ids[start:start+2048],None]-centers[None])**2,axis=2),axis=1)
    for label in range(len(centers)):
        members=ids[labels==label]
        if not len(members):continue
        guide=np.median(q[members],axis=0)
        collapse=.70*smooth((t-.40)/.60)[None,:,None]*weight[members,None,None]
        q[members]=q[members]*(1-collapse)+guide[None]*collapse
        q[members,0]=p[members,0];gather_groups+=1
    for i in ids:
        for j in range(4,N,4):
            hit,normal,_,distance=bv.find_nearest(Vector(q[i,j]));gap=(Vector(q[i,j])-hit).dot(normal)
            if gap<.0008 and distance<.025:q[i,j]+=np.array(normal)*(.001-gap);repairs+=1
assert np.array_equal(q[:,0],p[:,0]) and np.isfinite(q).all()
data=rear.data.copy();data.attributes['position'].data.foreach_set('vector',q.ravel())
r=np.empty(len(data.points),np.float32);data.attributes['radius'].data.foreach_get('value',r);r=r.reshape(-1,N)
old_r=r.copy();taper=(1-.997*t**2.6)**.7
for i in ids:r[i]=r[i,0]*taper
data.attributes['radius'].data.foreach_set('value',r.ravel());rear.data=data
out.mkdir(parents=True);renders.mkdir(parents=True)
report=dict(version=version,source=source_version,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    method=('Rebuild220 whole upper/side cubic parent paths with explicit lifted root handle, bowed side handle and inward/downward loose exit, independently staggered84..100% arc lengths and shrinking follicle field; lower nape/frontal object/underlay retained' if cubic_guides else 'Cut high roots on the original posterior object to spatially coherent63..91mm scissor lengths, continuous height transition and gentle outward exits; optional upper side region; regenerate taper on modified fibers; lower nape/frontal object/underlay retained'),
    components=[dict(object=rear.name,curves=len(p),actually_modified_curves=len(ids),exact_roots_preserved=True,
        maximum_displacement_m=float(np.linalg.norm(q-p,axis=2).max()),
        positions_before_sha256=hashlib.sha256(p.tobytes()).hexdigest(),positions_after_sha256=hashlib.sha256(q.tobytes()).hexdigest())],
    rear_only=True,front_only=False,cut_fraction_quantiles=None if cubic_guides else np.quantile(fractions,[0,.5,1]).tolist(),scalp_sampled_point_repairs=repairs,
    complete_cubic_upper_paths=cubic_guides,
    independent_parent_layer_lengths_and_handles=layer_variety,
    upper_side_region_included=include_side,
    local_shortened_tip_gather=gather_tips,local_tip_groups=gather_groups,
    unchanged_low_rear_curves=int((weight==0).sum()),
    collision_scope=('Every modified cubic interior point scalp guard; discrete points, not full surface/strand/garment or motion collision proof' if cubic_guides else 'Every fourth modified high posterior point scalp guard; not full surface/strand/garment or motion collision proof'),
    status='Unreviewed isolated scissor-layer native groom study; not artistic acceptance')
(out/'shag_cut_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=64;scene.cycles.use_denoising=False
scene.render.resolution_x,scene.render.resolution_y=1200,1400;scene.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['03_Side','04_Back']:
    scene.camera=bpy.data.objects[name];scene.render.filepath=str(renders/(name+'.png'))
    bpy.ops.render.render(write_still=True)
print('REAR_SCISSOR_LAYERS_RENDERED',version,len(ids),flush=True)
