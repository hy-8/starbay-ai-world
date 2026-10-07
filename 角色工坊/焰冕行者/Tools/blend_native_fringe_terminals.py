"""Retain new upper fall while reconnecting the donor's coherent terminal arcs."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base,donor=a[:3]
smooth_tail='--smooth-tail' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:3])
out,renders=ROOT/'Exports'/version,ROOT/'Renders'/version
assert not out.exists() and not renders.exists()
name='Bystedt layercut derivative • native root reflow';hashes={}
def load(v):
    path=ROOT/'Exports'/v/'Ember_Regent.blend';hashes[v]=hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
    cu=bpy.data.objects[name].data;p=np.empty((len(cu.points),3),np.float32)
    cu.attributes['position'].data.foreach_get('vector',p.ravel());return p.reshape(-1,65,3).astype(float)
dp=load(donor);raw=load(base);q=raw.copy();ob=bpy.data.objects[name];cu=ob.data
mask=np.empty(len(raw),bool);cu.attributes['native_directional_fringe_fall'].data.foreach_get('value',mask)
ids=np.flatnonzero(mask);t=np.linspace(0,1,65)
x=np.clip((t-.56)/.25,0,1);blend=x*x*(3-2*x)
if not smooth_tail:q[ids]=raw[ids]+(dp[ids]-raw[ids])*blend[None,:,None]
body=bpy.data.objects['CC0 male body • retained topology']
assert np.array_equal(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get());repairs=0
changed_terminals=0
for index in ids:
    if smooth_tail:
        p0=raw[index,42].copy();end=raw[index,64].copy()
        hit,n,_,dist=bv.find_nearest(Vector(end));gap=(Vector(end)-hit).dot(n)
        if dist<.025 and gap<.002:end+=np.array(n)*(.0022-gap)
        chord=end-p0;distance=np.linalg.norm(chord);direction=chord/max(distance,1e-9)
        initial=raw[index,46]-raw[index,39]
        initial/=max(np.linalg.norm(initial),1e-9)
        if initial.dot(direction)<.25:initial=direction
        p1=p0+initial*distance*.35;p2=end-direction*distance*.25
        u=np.linspace(0,1,23)[:,None]
        q[index,42:]=(1-u)**3*p0+3*(1-u)**2*u*p1+3*(1-u)*u*u*p2+u**3*end
        changed_terminals+=int(not np.array_equal(end,raw[index,64]))
    for j in (range(43,65) if smooth_tail else range(36,52)):
        hit,n,_,dist=bv.find_nearest(Vector(q[index,j]));gap=(Vector(q[index,j])-hit).dot(n)
        minimum=.0014 if smooth_tail else .0005
        if dist<.025 and gap<minimum:
            q[index,j]+=np.array(n)*((.0017 if smooth_tail else .0007)-gap);repairs+=1
if not smooth_tail:q[ids,52:]=dp[ids,52:]
assert np.isfinite(q).all() and np.array_equal(q[~mask],raw[~mask])
assert np.array_equal(q[:,:6],raw[:,:6])
if smooth_tail:assert np.array_equal(q[:,:43],raw[:,:43])
else:
    assert np.array_equal(q[:,-1],raw[:,-1])
    assert np.array_equal(q[mask,52:],dp[mask,52:])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_reconnected_fringe_terminals'
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
out.mkdir(parents=True);renders.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for shot in ['02_ThreeQuarter','01_Front','03_Side','05_OppositeSide']:
    s.camera=bpy.data.objects[shot];s.render.filepath=str(renders/(shot+'.png'));bpy.ops.render.render(write_still=True)
for v,h in hashes.items():assert hashlib.sha256((ROOT/'Exports'/v/'Ember_Regent.blend').read_bytes()).hexdigest()==h
(out/'terminal_blend_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=hashes[base],
    donor=donor,donor_sha256=hashes[donor],donor_role='read-only reference, not used by smooth-tail geometry' if smooth_tail else 'terminal suffix geometry donor',selection_attribute=attr,changed_fibers=int(mask.sum()),
    restored_suffix_first_point_index=None if smooth_tail else 52,discrete_body_repairs=repairs,
    smooth_tail=smooth_tail,designed_terminal_relocations=changed_terminals,
    method=('Selected8441 actual115 fringe shafts retain exact points0-42. Individual cubic terminal arcs42-64 use averaged source tangent and monotone chord end direction, allow former endpoint to move to2.2mm signed body point clearance if previously near scalp.1.4/1.7mm intermediate point guard. Radii/topology/materials/non-fringe unchanged; endpoints intentionally free.' if smooth_tail else 'Selected8441 actual115 fringe shafts retain upper directional fall. Smooth blend frompoint36 into113 coherent terminal arcs, points52-64 exact to113. Intermediate discrete body guard; source prefix0-5/endpoints/radii/topology/unselected/other hair/materials unchanged.'),
    status='Drafts pending art review, discrete geometry guards not complete reference/continuous collision acceptance'),indent=2),encoding='utf-8')
print('FRINGE_TERMINALS_RECONNECTED',version,int(mask.sum()),flush=True)
