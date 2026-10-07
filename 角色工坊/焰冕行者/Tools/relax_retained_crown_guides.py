"""Relax the observed retained crown guides without losing their cross sections."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base,donor=a[:3]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:3])
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version;assert not out.exists() and not render.exists()
name='Bystedt layercut derivative • native root reflow'
def read(v):
    path=ROOT/'Exports'/v/'Ember_Regent.blend';digest=hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False);cu=bpy.data.objects[name].data
    p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
    return path,digest,p.reshape(-1,65,3).astype(float)
donorpath,donorhash,old=read(donor);source,digest,raw=read(base);ob=bpy.data.objects[name];cu=ob.data
def flag(n):
    m=np.empty(len(raw),bool);cu.attributes[n].data.foreach_get('value',m);return m
frame=flag('native_front_frame_sculpture');loft=flag('native_layered_root_lofts');relief=flag('native_visible_crest_relief')
retained=loft&~relief;roots=old[:,0];eligible=np.flatnonzero((~frame)&(roots[:,2]>1.830)&(roots[:,1]<.065))
features=(old[eligible][:,[0,8,16,24,40]]*np.array([.7,.9,1.,1.,.4])[None,:,None]).reshape(len(eligible),-1)
K=150;centers=[features[len(features)//2]];best=np.full(len(features),np.inf)
for _ in range(1,K):
    best=np.minimum(best,np.sum((features-centers[-1])**2,axis=1));centers.append(features[np.argmax(best)])
centers=np.array(centers)
def assign():return np.argmin(np.maximum(0,(features*features).sum(axis=1)[:,None]+(centers*centers).sum(axis=1)[None]-2*features@centers.T),axis=1)
for _ in range(24):
    labels=assign()
    for k in range(K):
        if (labels==k).any():centers[k]=features[labels==k].mean(axis=0)
labels=assign();q=raw.copy();mask=np.zeros(len(raw),bool);rows=[];repairs=0
body=bpy.data.objects['CC0 male body • retained topology'];assert np.array_equal(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
for k in range(K):
    ids=eligible[labels==k]
    if not len(ids) or not retained[ids].all():continue
    #94 restores whole groups. Retained groups must have original90 membership.
    assert len(ids)>=30
    src=old[ids].mean(axis=0);current=raw[ids].mean(axis=0);delta=current-src
    tangent=np.gradient(src,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
    hit,nn,_,_=bv.find_nearest(Vector(src[0]));normal=np.array(nn)
    across=np.zeros_like(tangent);prev=np.cross(normal,tangent[0]);prev/=max(np.linalg.norm(prev),1e-9)
    for j in range(65):
        prev-=tangent[j]*np.dot(prev,tangent[j]);prev/=max(np.linalg.norm(prev),1e-9);across[j]=prev
    transported_normal=np.cross(tangent,across)
    if np.dot(transported_normal[0],normal)<0:transported_normal=-transported_normal
    # Remove only70% of the added positive guide-normal lift; retained internal
    # width/depth contraction, lateral sweep and tail geometry remain in place.
    amplitude=np.maximum(np.sum(delta*transported_normal,axis=1),0)
    offset=transported_normal*(.70*amplitude)[:,None];offset[0]=0;offset[44:]=0
    values=raw[ids]-offset[None]
    for i in range(len(ids)):
        for j in range(1,44):
            if amplitude[j]<.0001:continue
            hit,n,_,dist=bv.find_nearest(Vector(values[i,j]));gap=(Vector(values[i,j])-hit).dot(n)
            if dist<.03 and gap<.0005:values[i,j]+=np.array(n)*(.0007-gap);repairs+=1
    values[:,0]=raw[ids,0];values[:,44:]=raw[ids,44:];q[ids]=values;mask[ids]=True
    rows.append(dict(group=k,fibers=len(ids),guide_max_added_normal_lift_m=float(amplitude.max()),
        before_group_peak_z_m=float(raw[ids,:,2].max()),after_group_peak_z_m=float(values[:,:,2].max()),
        maximum_displacement_m=float(np.linalg.norm(values-raw[ids],axis=2).max())))
assert np.array_equal(mask,retained) and np.array_equal(q[:,0],raw[:,0]) and np.array_equal(q[:,44:],raw[:,44:])
assert np.array_equal(q[frame],raw[frame]) and np.array_equal(q[~mask],raw[~mask]) and np.isfinite(q).all()
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel());ob.data.update_tag()
attr='native_retained_guide_relaxation';previous=ob.data.attributes.get(attr)
if previous:ob.data.attributes.remove(previous)
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask)
out.mkdir(parents=True);render.mkdir(parents=True);s=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for shot in ['02_ThreeQuarter','03_Side','05_OppositeSide']:
    s.camera=bpy.data.objects[shot];s.render.filepath=str(render/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest and hashlib.sha256(donorpath.read_bytes()).hexdigest()==donorhash
(out/'guide_relaxation_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,donor=donor,donor_sha256=donorhash,
    selection_attribute=attr,changed_fibers=int(mask.sum()),changed_groups=len(rows),groups=rows,discrete_body_repairs=repairs,
    method='Reproduce90 original150 whole-path groups using86 donor; select all retained94 loft groups. Remove70% of positive transported-normal center-guide displacement relative86, leaving current within-lock cross sections and lateral sweep. Point0 and all44-64 retained. Materials/lights unchanged.',
    status='Actual drafts pending review; no artistic or continuous collision acceptance.'),indent=2),encoding='utf-8')
print('RETAINED_GUIDES_RELAXED',version,int(mask.sum()),len(rows),flush=True)
