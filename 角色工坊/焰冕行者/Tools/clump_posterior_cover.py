"""Groom existing back coverage into fine locks without replacing its flow."""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2];pilot='--pilot' in a;smooth_flow='--smooth-flow' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=ROOT/'Exports'/version;rd=ROOT/'Renders'/version;assert not out.exists() and not rd.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Original posterior coverage • surface-grown short fibers'];cu=ob.data
counts=np.array([c.points_length for c in cu.curves]);assert (counts==36).all()
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());raw=p.reshape(-1,36,3).astype(float)
r=raw[:,0];eligible=(r[:,1]>.015)&(r[:,2]>1.800)&(r[:,2]<1.855)&(np.abs(r[:,0])<.070)
ids=np.flatnonzero(eligible);assert len(ids)>1000
feature=(raw[ids][:,[0,12,24,35]]*np.array([1.8,.7,.5,.35])[None,:,None]).reshape(len(ids),-1)
K=120;centers=[feature[len(feature)//2]];nearest=np.full(len(ids),np.inf)
for _ in range(1,K):
    nearest=np.minimum(nearest,np.sum((feature-centers[-1])**2,axis=1));centers.append(feature[np.argmax(nearest)])
centers=np.array(centers)
def assign():return np.argmin(np.maximum(0,(feature*feature).sum(1)[:,None]+(centers*centers).sum(1)[None]-2*feature@centers.T),axis=1)
for _ in range(18):
    labels=assign()
    for k in range(K):
        if (labels==k).any():centers[k]=feature[labels==k].mean(0)
labels=assign();bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
t=np.linspace(0,1,36);u=np.clip((t-t[3])/(1-t[3]),0,1);blend=np.minimum(u/.30,1);blend=blend*blend*(3-2*blend)
q=raw.copy();mask=np.zeros(len(raw),bool);groups=[];repairs=0
def unit(v):return v/max(np.linalg.norm(v),1e-9)
for k in range(K):
    members=ids[labels==k]
    if len(members)<12:continue
    old=raw[members];center=old.mean(0)
    tangent=np.gradient(center,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
    normal=center-np.array([0.,-.030,1.775]);normal[:,2]=0
    normal-=tangent*np.sum(normal*tangent,axis=1)[:,None]
    normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-9)
    width=np.cross(tangent,normal)
    dev=old-center
    along=np.sum(dev*tangent[None],axis=2);depth=np.sum(dev*normal[None],axis=2);spread=np.sum(dev*width[None],axis=2)
    # A finer lock taper grows gradually; retain native longitudinal scatter.
    widthscale=1-(.30 if smooth_flow else .62)*blend;depthscale=1-(.15 if smooth_flow else .30)*blend
    values=center+along[:,:,None]*tangent[None]+(depth*depthscale)[:,:,None]*normal[None]+(spread*widthscale)[:,:,None]*width[None]
    if smooth_flow:
        A=np.column_stack([3*(1-t)**2*t,3*(1-t)*t*t])
        B=center-(1-t[:,None])**3*center[0]-t[:,None]**3*center[-1]
        p1,p2=np.linalg.lstsq(A[1:-1],B[1:-1],rcond=None)[0]
        # One smooth fall, eliminating the inherited repeated lateral wave.
        p1[2]=np.clip(p1[2],center[-1,2]+.030,center[0,2]-.008)
        p2[2]=np.clip(p2[2],center[-1,2]+.008,p1[2]-.008)
        guide=(1-t[:,None])**3*center[0]+3*(1-t[:,None])**2*t[:,None]*p1+3*(1-t[:,None])*t[:,None]**2*p2+t[:,None]**3*center[-1]
        values+=(guide-center)[None]*blend[None,:,None]
    relief=.001+.003*(.5+.5*np.sin(k*2.399963))
    values+=normal[None]*(relief*np.sin(np.pi*u)**1.7)[None,:,None]
    active=(r[members,0]<-.005) if pilot else np.ones(len(members),bool)
    for j,index in enumerate(members):
        if not active[j]:continue
        correction=np.zeros((36,3))
        for h in range(4,36):
            hit,n,_,distance=bv.find_nearest(Vector(values[j,h]));gap=(Vector(values[j,h])-hit).dot(n)
            if distance<.030 and gap<.001:correction[h]=np.array(n)*(.0014-gap);repairs+=1
        for axis in range(3):correction[:,axis]=np.convolve(np.pad(correction[:,axis],(2,2),mode='edge'),np.array([1,4,6,4,1])/16,mode='valid')
        values[j]+=correction;values[j,:4]=old[j,:4];q[index]=values[j];mask[index]=True
    if active.any():groups.append(dict(group=k,source_fibers=len(members),edited_fibers=int(active.sum())))
assert np.array_equal(q[:,:4],raw[:,:4]) and np.array_equal(q[~mask],raw[~mask]) and np.isfinite(q).all()
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_posterior_fine_clumps';assert not ob.data.attributes.get(attr)
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
out.mkdir(parents=True);rd.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=192;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
method='Existing support rootY>15mm,Z1.800-1.855m,absX<70mm.120 global root/path clusters shared by pilot/full; pilot edits onlyX<-5mm. Existing mean flow retained; along spread exact before contact, cross width contracts gradually to38%,depth to70%,1-4mm mid normal relief. First4 points and unselected geometry exact; no material edits. Sampled contact is not continuous collision proof.'
if smooth_flow:method=method.replace('Existing mean flow retained;','Fit mean to single cubic with descending controlZ, retain mean root/end; transition over first30 percent of remaining path.').replace('to38%,depth to70%','to70%,depth to85%')
(out/'posterior_clump_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,changed_object=ob.name,pilot=pilot,smooth_flow=smooth_flow,eligible_fibers=len(ids),selected_fibers=int(mask.sum()),selection_attribute=attr,preserved_prefix_points=4,target_groups=K,edited_groups=len(groups),groups=groups,sampled_body_repairs=repairs,max_displacement_m=float(np.linalg.norm(q-raw,axis=2).max()),method=method,status='True back cover grooming study pending review'),indent=2),encoding='utf-8')
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for shot in ['04_Back','05_OppositeSide']:
    s.camera=bpy.data.objects[shot];s.render.filepath=str(rd/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
print('POSTERIOR_CLUMP_RENDERED',version,int(mask.sum()),flush=True)
