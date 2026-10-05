"""Spatially coherent crown deformation on native fibers.

Neighboring positions share one smooth field instead of opposing per-lock
oscillations. Exact follicles and all non-crown native geometry are retained.
"""
import bpy, sys, json, re, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:]
version, source_version=args[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in args[:2]):raise ValueError(args)
out,renders=ROOT/'Exports'/version,ROOT/'Renders'/version
if out.exists() or renders.exists():raise RuntimeError('Fresh version required')
source=ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
front=next(o for o in bpy.data.objects if not o.hide_render and o.name.startswith('Authored frontal revision'))
if not np.allclose(np.array(front.matrix_world),np.eye(4)):raise RuntimeError('Neutral world-aligned crown required')
sizes=[len(c.points) for c in front.data.curves]
if len(set(sizes))!=1:raise RuntimeError('Uniform fibers required')
raw=np.empty(len(front.data.points)*3,np.float32)
front.data.attributes['position'].data.foreach_get('vector',raw)
raw=raw.reshape(-1,sizes[0],3);result=raw.copy()
records=json.loads((ROOT/'Exports/spatialfringe17/authored_fringe_design.json').read_text(encoding='utf-8'))
offset=0;ids=[]
for record in records:
    count=record['assigned_visible_fibers']
    if 'segmented crown' in record['name']:ids.extend(range(offset,offset+count))
    offset+=count
assert offset==len(raw)
p=raw[ids].astype(float);t=np.linspace(0,1,p.shape[1])
def smooth(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)
# No additional twist is introduced by nearest-face orientation frames.
# The field's spatial derivative magnitudes are small (x/z .52 and y/z .28).
# Root anchoring is the only strand-parameter modulation.
w=smooth(t/.30)[None]
phase=(p[:,:,2]-1.81)*52+p[:,:,0]*11
delta=np.zeros_like(p)
delta[:,:,0]=.010*np.sin(phase)*w
delta[:,:,1]=.006*np.cos((p[:,:,2]-1.81)*46+p[:,:,0]*9)*w
delta[:,:,2]=.003*np.sin(p[:,:,0]*26)*np.sin(np.pi*t)[None]
bpy.context.view_layer.update()
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
alpha=np.ones(p.shape[:2]);attenuated=0
for i in range(len(p)):
    for j in range(1,p.shape[1]):
        hit,normal,_,distance=bv.find_nearest(Vector(p[i,j]))
        gap=(Vector(p[i,j])-hit).dot(normal)
        inward=float(np.dot(delta[i,j],np.array(normal)))
        if inward<0 and distance<.025:
            alpha[i,j]=min(1,max(0,gap-.0012)/(-inward))
            attenuated+=int(alpha[i,j]<1)
# A minimum filter widens the attenuation rather than creating narrow kinks.
for _ in range(3):
    alpha[:,1:-1]=np.minimum(alpha[:,1:-1],np.minimum(alpha[:,:-2],alpha[:,2:]))
q=p+delta*alpha[:,:,None];repairs=0;maximum_repair=0.
for i in range(len(q)):
    for j in range(1,q.shape[1]):
        hit,normal,_,distance=bv.find_nearest(Vector(q[i,j]))
        gap=(Vector(q[i,j])-hit).dot(normal)
        if gap<.0008 and distance<.025:
            amount=.001-gap
            q[i,j]+=np.array(normal)*amount
            repairs+=1;maximum_repair=max(maximum_repair,amount)
q[:,0]=p[:,0]
result[ids]=q
assert np.array_equal(result[:,0],raw[:,0]) and np.isfinite(result).all()
data=front.data.copy();data.attributes['position'].data.foreach_set('vector',result.ravel());front.data=data
out.mkdir(parents=True);renders.mkdir(parents=True)
report=dict(version=version,source=source_version,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    method='Single smooth world-space vector field shared by adjacent crown positions; bounded lateral/depth bending and small height variation; exact roots, fringe and other objects retained',
    crown_spatial_field=True,full_crown_flow_rebuilt=False,front_only=True,rear_only=False,radii_unchanged=True,
    field_amplitudes_m=[.010,.006,.003],field_spatial_frequencies=[52,46,26],
    attenuation_points=attenuated,scalp_point_repairs=repairs,maximum_scalp_repair_m=maximum_repair,
    components=[dict(object=front.name,curves=len(raw),actually_modified_curves=len(ids),exact_roots_preserved=True,
        maximum_displacement_m=float(np.linalg.norm(result-raw,axis=2).max()),
        positions_before_sha256=hashlib.sha256(raw.tobytes()).hexdigest(),positions_after_sha256=hashlib.sha256(result.tobytes()).hexdigest())],
    collision_scope='Source-distance field attenuation and every modified crown interior point nearest-body guard; only discrete points, not full curve/strand/eye/garment or motion collision proof',
    status='Unreviewed coherent field study; not artistic acceptance')
(out/'shag_cut_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=64;scene.cycles.use_denoising=False
scene.render.resolution_x,scene.render.resolution_y=1200,1400;scene.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter']:
    scene.camera=bpy.data.objects[name];scene.render.filepath=str(renders/(name+'.png'))
    bpy.ops.render.render(write_still=True)
print('COHERENT_CROWN_FIELD_RENDERED',version,flush=True)
