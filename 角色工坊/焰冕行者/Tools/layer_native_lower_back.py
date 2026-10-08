"""Stagger lower posterior native locks, leaving upper and fringe intact."""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
out,rd=ROOT/'Exports'/version,ROOT/'Renders'/version;assert not out.exists() and not rd.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float);q=raw.copy()
def flag(n):
    v=np.empty(len(raw),bool);cu.attributes[n].data.foreach_get('value',v);return v
fringe=flag('native_resculpted_fringe_sweeps');upper=flag('native_descending_fine_locks')
ids=np.flatnonzero((~(fringe|upper))&(raw[:,32,1]>.035)&(raw[:,-1,1]>.020)&(raw[:,-1,2]<1.770))
assert len(ids)>1000
feature=(raw[ids][:,[0,24,48,64]]*np.array([1.4,.8,.5,.6])[None,:,None]).reshape(len(ids),-1)
K=100;centers=[feature[len(feature)//2]];best=np.full(len(feature),np.inf)
for _ in range(1,K):
    best=np.minimum(best,np.sum((feature-centers[-1])**2,axis=1));centers.append(feature[np.argmax(best)])
centers=np.array(centers)
def assign():return np.argmin(np.maximum(0,(feature*feature).sum(1)[:,None]+(centers*centers).sum(1)[None]-2*feature@centers.T),axis=1)
for _ in range(18):
    labels=assign()
    for k in range(K):
        if (labels==k).any():centers[k]=feature[labels==k].mean(0)
labels=assign()
body=bpy.data.objects['CC0 male body • retained topology'];assert np.array_equal(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
t=np.linspace(0,1,65);rng=np.random.default_rng(138);mask=np.zeros(len(raw),bool);rows=[];repairs=0
def smooth(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)
for k in range(K):
    members=ids[labels==k]
    if len(members)<20:continue
    old=raw[members];c=old.mean(0);upper_root=float(smooth((c[0,2]-1.748)/.075))
    rate=float(rng.uniform(.80,.98)-.14*upper_root)
    rates=np.clip(rate+rng.normal(0,.012,len(members)),.64,1.)
    values=np.empty_like(old)
    for i,r in enumerate(rates):
        parameter=np.where(t<=11/64,t,11/64+(t-11/64)*(r-11/64)/(1-11/64))
        for axis in range(3):values[i,:,axis]=np.interp(parameter,t,old[i,:,axis])
    radial=np.array([c[40,0],c[40,1]+.035,0.]);radial/=max(np.linalg.norm(radial),1e-9)
    lateral=np.array([-radial[1],radial[0],0.])
    delta=radial*rng.uniform(.004,.010)+lateral*rng.uniform(-.004,.004)
    delta[2]+=rng.uniform(-.003,.004)
    w=smooth((t-11/64)/(1-11/64));values+=w[None,:,None]*delta[None,None]
    for i in range(len(members)):
        for j in range(12,65):
            hit,n,_,dist=bv.find_nearest(Vector(values[i,j]));gap=(Vector(values[i,j])-hit).dot(n)
            if dist<.025 and gap<.001:
                values[i,j]+=np.array(n)*(.0014-gap);repairs+=1
    values[:,:12]=old[:,:12];q[members]=values;mask[members]=True
    rows.append(dict(group=k,fibers=len(members),parameter_rate=rate,
        maximum_displacement_m=float(np.linalg.norm(values-old,axis=2).max())))
assert mask.sum()>1000 and np.isfinite(q).all() and np.array_equal(q[:,:12],raw[:,:12])
assert np.array_equal(q[~mask],raw[~mask]) and np.array_equal(q[fringe|upper],raw[fringe|upper])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_staggered_lower_posterior';assert not ob.data.attributes.get(attr)
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
out.mkdir(parents=True);rd.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
(out/'lower_posterior_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,
    selection_attribute=attr,target_groups=K,edited_groups=len(rows),changed_fibers=int(mask.sum()),
    groups=rows,discrete_body_repairs=repairs,
    method='Actual other-primary shafts exclude current fringe and133 upper. MidpointY>35mm/endY>20mm/endZ<1.770m,100 whole-flow target families. Per-family source-path parameter shortening .80-.98 minusup-to.14 forupper roots, independent .012 scatter, first12 points exact. Terminal4-10mm radial/+-4mm lateral stagger increases smoothly frompoint11. Existing source shapes reused rather than raised arches. Parameter rates are not strict arc-length cuts. Radii/topology/fringe/upper/othercomponents/materials/lighting exact; discrete body1/1.4mm point guard, no continuous clothing/motion proof.',
    status='Drafts pending artistic inspection, not reference complete'),indent=2),encoding='utf-8')
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
reflect=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=reflect@cam.matrix_world@reflect
for shot in ['04_Back','03_Side','05_OppositeSide','02_ThreeQuarter']:
    s.camera=bpy.data.objects[shot];s.render.filepath=str(rd/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
print('LOWER_BACK_LAYERED',version,int(mask.sum()),len(rows),flush=True)
