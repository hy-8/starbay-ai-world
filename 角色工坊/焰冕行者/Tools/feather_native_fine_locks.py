"""Fine, direction-compatible layered locks from actual native shafts.

Pilot before whole-head use. No fibers, image reconstruction or shader changes.
"""
import bpy, sys, re, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2];pilot='--pilot' in a
authored='--authored' in a
fall_tips='--fall-tips' in a
fringe_mode='--fringe' in a
assert not fall_tips or authored
assert not (fall_tips and fringe_mode)
assert all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:2])
out,rd=ROOT/'Exports'/version,ROOT/'Renders'/version
assert not out.exists() and not rd.exists()
src=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float);q=raw.copy();roots=raw[:,0]
fringe=np.empty(len(raw),bool);cu.attributes['native_resculpted_fringe_sweeps'].data.foreach_get('value',fringe)
selection=(~fringe)&(roots[:,2]>1.770)&(raw[:,-1,2]>1.695)
if fringe_mode:selection=fringe.copy()
if pilot:selection&=(roots[:,0]>.018)&(roots[:,2]>1.800)
ids=np.flatnonzero(selection);assert len(ids)>1000
# Root location dominates separation; full-direction samples keep incompatible
# crossing paths out of one lock. Far more fine families than previous108.
feature=(raw[ids][:,[0,16,36,64]]*np.array([1.9,1.,.55,.45])[None,:,None]).reshape(len(ids),-1)
K=160 if pilot or fringe_mode else 440;centers=[feature[len(feature)//2]];best=np.full(len(feature),np.inf)
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
t=np.linspace(0,1,65);u=t[:,None];rng=np.random.default_rng(130)
def smooth(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)
def unit(x):return x/max(np.linalg.norm(x),1e-9)
def frames(c):
    tangent=np.gradient(c,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
    n=np.empty_like(c)
    for j in range(65):
        hit,normal,_,_=bv.find_nearest(Vector(c[j]));normal=np.array(normal)
        projected=normal-normal.dot(tangent[j])*tangent[j]
        if np.linalg.norm(projected)<.15:projected=np.array([0.,0.,1.])-tangent[j,2]*tangent[j]
        n[j]=unit(projected)
        if j and n[j].dot(n[j-1])<0:n[j]*=-1
    return tangent,n,np.cross(tangent,n)
mask=np.zeros(len(raw),bool);rows=[];repairs=0
for k in range(K):
    members=ids[labels==k]
    if len(members)<20:continue
    old=raw[members];c=old.mean(0)
    # Stagger the exposed length of the smaller families, leaving original
    # follicle distribution intact. Shortened paths are individually sampled.
    rate=float(rng.uniform(.82,.99))
    rates=np.clip(rate+rng.normal(0,.018,len(members)),.78,1.)
    if fringe_mode:rate=1.;rates=np.ones(len(members))
    sampled=np.empty_like(old)
    for i,r in enumerate(rates):
        for axis in range(3):sampled[i,:,axis]=np.interp(t*r,t,old[i,:,axis])
    c=sampled.mean(0);p0,p3=c[0].copy(),c[-1].copy()
    A=np.column_stack([3*(1-t)**2*t,3*(1-t)*t*t])
    B=c-(1-u)**3*p0-u**3*p3
    p1,p2=np.linalg.lstsq(A[1:-1],B[1:-1],rcond=None)[0]
    radial=unit(np.array([c[32,0],c[32,1]+.035,0.]));lateral=np.array([-radial[1],radial[0],0.])
    p1+=radial*rng.uniform(.001,.004)
    p2+=lateral*rng.uniform(-.006,.006)+radial*rng.uniform(.001,.005)
    p3+=lateral*rng.uniform(-.004,.004)+radial*rng.uniform(.001,.005)
    if fringe_mode:p3=c[-1].copy()
    if authored:
        if fall_tips:
            xy=p3[:2]-np.array([0.,-.035]);radius=np.linalg.norm(xy)
            direction=xy/max(radius,1e-9)
            p3[:2]=np.array([0.,-.035])+direction*np.clip(radius,.090,.128)
            p3[2]=min(np.clip(p3[2],1.730,1.808),p0[2]-.050)
        hit,n,_,_=bv.find_nearest(Vector(p0));normal=np.array(n)
        chord=p3-p0;initial=chord-normal*chord.dot(normal)
        if np.linalg.norm(initial)<.005:initial=c[12]-c[0];initial-=normal*initial.dot(normal)
        initial=unit(initial)
        lead=np.clip(np.linalg.norm(chord)*.40,.028,.065)
        p1=p0+initial*lead+normal*rng.uniform(.004,.008)
        p2=p3-.28*chord+radial*rng.uniform(.001,.006)
        p2+=lateral*rng.uniform(-.003,.003)
        if fall_tips:
            p2=p3+np.array([0.,0.,rng.uniform(.023,.037)])-radial*.004
    guide=(1-u)**3*p0+3*(1-u)**2*u*p1+3*(1-u)*u*u*p2+u**3*p3
    if not authored:guide=.12*c+.88*guide
    ct,cn,cw=frames(c);gt,gn,gw=frames(guide)
    dev=sampled-c
    along=np.sum(dev*ct[None],axis=2);depth=np.sum(dev*cn[None],axis=2);width=np.sum(dev*cw[None],axis=2)
    # Preserve some loose native dispersion around smaller clumps. Hair is
    # not assigned cylindrical ranks; this remains a bundle of real shafts.
    taper=1-.32*smooth((t-.40)/.60)
    section=along[:,:,None]*gt[None]+(.50*depth*taper[None])[:,:,None]*gn[None]+(.65*width*taper[None])[:,:,None]*gw[None]
    values=guide[None]+section
    blend=smooth((t-.005)/.075) if authored else smooth((t-.04)/.22)
    values=old*(1-blend[None,:,None])+values*blend[None,:,None]
    low=smooth((1.705-old[:,:,2])/.040);values=values*(1-low[:,:,None])+old*low[:,:,None]
    for i in range(len(members)):
        correction=np.zeros((65,3))
        for j in range(1,65):
            hit,n,_,dist=bv.find_nearest(Vector(values[i,j]));gap=(Vector(values[i,j])-hit).dot(n)
            if dist<.03 and gap<.0007:
                correction[j]=np.array(n)*(.001-gap);repairs+=1
        envelope=correction.copy();mag=np.linalg.norm(correction,axis=1)
        for j in range(1,65):
            lo,hi=max(1,j-4),min(65,j+5);w=np.maximum(0,1-np.abs(np.arange(lo,hi)-j)/5)
            scores=mag[lo:hi]*w;h=int(np.argmax(scores))
            if scores[h]>np.linalg.norm(envelope[j]):envelope[j]=correction[lo+h]*w[h]
        values[i]+=envelope
    values[:,0]=old[:,0];q[members]=values;mask[members]=True
    rows.append(dict(group=k,fibers=len(members),design_parameter_rate=rate,
        maximum_displacement_m=float(np.linalg.norm(values-old,axis=2).max())))
assert mask.sum()>1000 and np.isfinite(q).all() and np.array_equal(q[:,0],raw[:,0])
assert np.array_equal(q[~mask],raw[~mask])
if not fringe_mode:assert np.array_equal(q[fringe],raw[fringe])
else:assert np.array_equal(q[~fringe],raw[~fringe])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr=('native_authored_fine_lock_pilot' if pilot else 'native_authored_fine_locks') if authored else ('native_feathered_fine_lock_pilot' if pilot else 'native_feathered_fine_locks')
if fall_tips:attr='native_descending_fine_lock_pilot' if pilot else 'native_descending_fine_locks'
if fringe_mode:attr='native_authored_fine_fringe' if authored else 'native_fitted_fine_fringe'
assert not ob.data.attributes.get(attr)
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
out.mkdir(parents=True);rd.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';pref.get_devices()
for device in pref.devices:device.use=device.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
(out/'fine_locks_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,
    selection_attribute=attr,pilot=pilot,authored=authored,fall_tips=fall_tips,fringe_mode=fringe_mode,target_groups=K,edited_groups=len(rows),changed_fibers=int(mask.sum()),
    discrete_body_repairs=repairs,groups=rows,
    method=('Authored single-fall guide from scalp-tangent first control28-65mm plus4-8mm root-normal relief; second control28% backward from end with1-6mm radial variation unless descending tip mode overrides. Source-to-guide transition full bynormalized .080, only true roots frozen. ' if authored else 'Broad cubic fitted current mean, source-to-guide transition full bynormalized .26. ')+ 'Selected direction-compatible root-weighted smaller families, individually resampled lengths unless fringe mode uses exact parameter rate1, transported native unranked scatter. 50% normal/65% lateral dispersion, staggered controls and roots exact. Original low paths blended back below1.705m. Parameter shortening is not exact arc-length shortening. No new fibers/materials/lighting.',
    descending_tip_method='Guide XY radius clamped90-128mm around[0,-35mm]; tipZ clipped1.730-1.808m and at least50mm belowroot; end control23-37mm aboveend and4mm inward. This is guide design, not strict all-fiber terminal bounds.' if fall_tips else None,
    fringe_method='Actual current fringe only; no length resampling, guide endpoint equals current group endpoint mean. Transported/scaled individual dispersion may change actual shaft endpoints; true roots and non-fringe exact.' if fringe_mode else None,
    status='Actual draft pending art review; no continuous collision or reference completion claim'),indent=2),encoding='utf-8')
shots=['02_ThreeQuarter'] if pilot else ['02_ThreeQuarter','03_Side','04_Back','05_OppositeSide']
if not pilot:
    cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
    reflection=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=reflection@cam.matrix_world@reflection
for shot in shots:
    s.camera=bpy.data.objects[shot];s.render.filepath=str(rd/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
print('FINE_LOCKS_RENDERED',version,int(mask.sum()),len(rows),flush=True)
