"""Rebuild crown sections with transported frames and loose shallow fans.

Uses only locally licensed native strands. No image reconstruction or new fibers.
"""
import bpy, sys, re, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:]
version,base,donor,volume=a[:4]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:4])
out,renders=ROOT/'Exports'/version,ROOT/'Renders'/version
assert not out.exists() and not renders.exists()
name='Bystedt layercut derivative • native root reflow'
hashes={}
def load(v):
    path=ROOT/'Exports'/v/'Ember_Regent.blend'
    hashes[v]=hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
    cu=bpy.data.objects[name].data
    p=np.empty((len(cu.points),3),np.float32)
    cu.attributes['position'].data.foreach_get('vector',p.ravel())
    return p.reshape(-1,65,3).astype(float)
source=load(donor)
rounded=load(volume)
raw=load(base);q=raw.copy()
ob=bpy.data.objects[name];cu=ob.data
fringe=np.empty(len(raw),bool)
cu.attributes['native_resculpted_fringe_sweeps'].data.foreach_get('value',fringe)
ids=np.flatnonzero((~fringe)&(source[:,0,2]>1.820))
features=(source[ids][:,[0,8,24,40,64]]*np.array([.8,1,1,.8,.55])[None,:,None]).reshape(len(ids),-1)
K=140
centers=[features[len(features)//2]];best=np.full(len(features),np.inf)
for _ in range(1,K):
    best=np.minimum(best,np.sum((features-centers[-1])**2,axis=1));centers.append(features[np.argmax(best)])
centers=np.array(centers)
def assign():return np.argmin(np.maximum(0,(features*features).sum(1)[:,None]+(centers*centers).sum(1)[None]-2*features@centers.T),axis=1)
for _ in range(20):
    labels=assign()
    for k in range(K):
        if (labels==k).any():centers[k]=features[labels==k].mean(0)
labels=assign()
body=bpy.data.objects['CC0 male body • retained topology']
assert np.array_equal(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
t=np.linspace(0,1,65)
def smooth(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)
def unit(x):return x/max(np.linalg.norm(x),1e-9)
mask=np.zeros(len(raw),bool);rows=[];repairs=0
for k in range(K):
    members=ids[labels==k]
    if len(members)<24:continue
    # Keep112's added nape displacement, using108's pre-cylinder section donor.
    paths=source[members]+(raw[members]-rounded[members])
    c=paths.mean(0)
    tangent=np.gradient(c,axis=0)
    tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
    hit,n,_,dist=bv.find_nearest(Vector(c[4]))
    initial=np.array(n);initial-=initial.dot(tangent[4])*tangent[4]
    normal=np.empty((65,3));normal[0]=unit(initial-initial.dot(tangent[0])*tangent[0])
    # Minimal-rotation transport stops cross-section axes flipping when the
    # nearest body triangle changes at a scalp/forehead/ear transition.
    for j in range(1,65):
        axis=np.cross(tangent[j-1],tangent[j]);sn=np.linalg.norm(axis)
        cs=np.clip(tangent[j-1].dot(tangent[j]),-1,1)
        if sn>1e-7:
            axis/=sn
            prev=normal[j-1]
            rotated=prev*cs+np.cross(axis,prev)*sn+axis*axis.dot(prev)*(1-cs)
        else:rotated=normal[j-1]
        normal[j]=unit(rotated-rotated.dot(tangent[j])*tangent[j])
    across=np.cross(tangent,normal)
    dev=paths-c
    lateral=(dev*across[None]).sum(2);depth=(dev*normal[None]).sum(2)
    order=np.argsort(lateral[:,18:42].mean(1),kind='stable')
    rank=np.empty(len(members));rank[order]=(np.arange(len(members))+.5)/len(members)
    xrank=2*rank-1
    width=np.clip(np.quantile(np.abs(lateral[:,16:48]),.80),.0035,.009)
    phi=k*2.3999632297;az=members*2.3999632297
    taper=1-.60*smooth((t-.54)/.46)
    blend=.64*smooth((t-.09)/.30)
    # Shallow fan-shaped sections leave original shaft dispersion visible.
    targetx=xrank[:,None]*width*taper[None]
    targetz=(.00065+.0005*(.5+.5*np.sin(phi)))*np.cos(xrank[:,None]*np.pi/2)*taper[None]
    targetz+=.00045*np.sin(az)[:,None]*np.sin(np.pi*t)[None]
    values=paths+(targetx-lateral)[:,:,None]*across[None]*blend[None,:,None]
    values+=(targetz-depth)[:,:,None]*normal[None]*blend[None,:,None]
    values+=(.001+.002*(.5+.5*np.sin(phi*.71)))*np.sin(np.pi*t)[None,:,None]**2*normal[None]
    # A minority follows a less clustered donor path as a loose transition veil.
    loose=(members%5)==0
    values[loose]=.45*values[loose]+.55*paths[loose]
    for i in range(len(members)):
        for j in range(6,65):
            hit,n,_,dist=bv.find_nearest(Vector(values[i,j]));gap=(Vector(values[i,j])-hit).dot(n)
            if dist<.03 and gap<.0005:
                values[i,j]+=np.array(n)*(.0007-gap);repairs+=1
    # Keep112's corrected lower nape and all actual fringe untouched.
    low=smooth((1.710-raw[members,:,2])/.055)
    values=values*(1-low[:,:,None])+raw[members]*low[:,:,None]
    values[:,:6]=raw[members,:6]
    q[members]=values;mask[members]=True
    rows.append(dict(group=k,fibers=len(members),loose_fibers=int(loose.sum()),fan_half_width_m=float(width),
        maximum_displacement_m=float(np.linalg.norm(values-raw[members],axis=2).max())))
assert np.isfinite(q).all() and np.array_equal(q[:,:6],raw[:,:6])
assert np.array_equal(q[~mask],raw[~mask]) and np.array_equal(q[fringe],raw[fringe])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_transported_fan_crown'
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
(out/'fan_crown_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=hashes[base],
    donor=donor,donor_sha256=hashes[donor],volume_source=volume,volume_source_sha256=hashes[volume],
    selection_attribute=attr,changed_fibers=int(mask.sum()),groups=rows,discrete_body_repairs=repairs,
    method='140 actual donor108 whole-path groups excluding106 fringe, roots Z>1.820m. Minimal-rotation transported sections replace per-point nearest-triangle axes. Shallow3.5-9mm fan width,0.65-1.15mm central thickness,64% section adjustment retains source dispersion;20% loosely follow donor flow.112-110 displacement carries nape extension, existing112 lower paths blended back below1.710m and exact below1.655m. First6 points/fringe/source roots/radii/topology/materials/other components retained.',
    status='Actual drafts pending art review; no continuous collision or completed-reference claim'),indent=2),encoding='utf-8')
print('TRANSPORTED_FAN_CROWN',version,int(mask.sum()),len(rows),flush=True)
