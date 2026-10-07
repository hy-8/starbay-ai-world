"""Recomb upper locks while restoring locally licensed shaft dispersion.

The body/materials remain intact. No added fibers or neural reconstruction.
"""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base,donor=a[:3]
fringe_mode='--fringe' in a
swept_upper='--swept-upper' in a
assert not (fringe_mode and swept_upper)
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:3])
out,renders=ROOT/'Exports'/version,ROOT/'Renders'/version
assert not out.exists() and not renders.exists()
name='Bystedt layercut derivative • native root reflow'
hashes={}
def load(v):
    path=ROOT/'Exports'/v/'Ember_Regent.blend';hashes[v]=hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
    cu=bpy.data.objects[name].data;p=np.empty((len(cu.points),3),np.float32)
    cu.attributes['position'].data.foreach_get('vector',p.ravel())
    return p.reshape(-1,65,3).astype(float)
original=load(donor);raw=load(base);q=raw.copy()
assert np.array_equal(original[:,0],raw[:,0])
ob=bpy.data.objects[name];cu=ob.data
fringe=np.empty(len(raw),bool);cu.attributes['native_resculpted_fringe_sweeps'].data.foreach_get('value',fringe)
ids=np.flatnonzero((~fringe)&(raw[:,0,2]>1.800)&(raw[:,-1,2]>1.690))
if fringe_mode:ids=np.flatnonzero(fringe)
features=(raw[ids][:,[0,10,24,42,64]]*np.array([.8,.7,1.,1.,.8])[None,:,None]).reshape(len(ids),-1)
K=48 if fringe_mode else 108;centers=[features[len(features)//2]];best=np.full(len(features),np.inf)
for _ in range(1,K):
    best=np.minimum(best,np.sum((features-centers[-1])**2,axis=1));centers.append(features[np.argmax(best)])
centers=np.array(centers)
def assign():return np.argmin(np.maximum(0,(features*features).sum(1)[:,None]+(centers*centers).sum(1)[None]-2*features@centers.T),axis=1)
for _ in range(22):
    labels=assign()
    for k in range(K):
        if (labels==k).any():centers[k]=features[labels==k].mean(0)
labels=assign()
body=bpy.data.objects['CC0 male body • retained topology']
assert np.array_equal(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
t=np.linspace(0,1,65);u=t[:,None]
def smooth(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)
def unit(x):return x/max(np.linalg.norm(x),1e-9)
def frame(c):
    tangent=np.gradient(c,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
    hit,n,_,_=bv.find_nearest(Vector(c[0]))
    normal=np.empty((65,3));normal[0]=unit(np.array(n)-np.array(n).dot(tangent[0])*tangent[0])
    for j in range(1,65):
        axis=np.cross(tangent[j-1],tangent[j]);sn=np.linalg.norm(axis);cs=np.clip(tangent[j-1].dot(tangent[j]),-1,1)
        if sn>1e-7:
            axis/=sn;prev=normal[j-1]
            rotated=prev*cs+np.cross(axis,prev)*sn+axis*axis.dot(prev)*(1-cs)
        else:rotated=normal[j-1]
        normal[j]=unit(rotated-rotated.dot(tangent[j])*tangent[j])
    return tangent,normal,np.cross(tangent,normal)
mask=np.zeros(len(raw),bool);rows=[];repairs=0
for k in range(K):
    members=ids[labels==k]
    if len(members)<24:continue
    old=raw[members];don=original[members];c=old.mean(0);d=don.mean(0)
    phase=k*2.3999632297
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(c,axis=0),axis=1))];v=(arc/max(arc[-1],1e-9))[:,None]
    p0,p3=c[0].copy(),c[-1].copy()
    A=np.column_stack([3*(1-v[:,0])**2*v[:,0],3*(1-v[:,0])*v[:,0]**2])
    B=c-(1-v)**3*p0-v**3*p3
    p1,p2=np.linalg.lstsq(A[1:-1],B[1:-1],rcond=None)[0]
    # One broad falling flow per family removes repeated source S bends. Small
    # group-specific lateral drift and end levels avoid a shared flat sheet.
    radial=c[24]-np.array([0,-.035,1.776]);radial[2]=0;radial=unit(radial)
    lateral=np.array([-radial[1],radial[0],0.])
    p1+=radial*(.002+.003*(.5+.5*np.sin(phase*.41)))
    p2+=lateral*(.005*np.sin(phase*.67));p2[2]-=.007*(.5+.5*np.cos(phase*.73))
    p3+=radial*(.004*np.sin(phase*.53))+lateral*(.003*np.cos(phase*.47))
    p3[2]+=.007*np.sin(phase*.61)
    if swept_upper:
        hit,n,_,_=bv.find_nearest(Vector(p0));root_normal=np.array(n)
        initial=unit(c[10]-c[0])
        lead=min(.075,max(.028,arc[-1]*.34))
        p1=p0+initial*lead+root_normal*(.012+.010*(.5+.5*np.sin(phase*.47)))
        p3=c[-1].copy()+radial*(.003+.007*(.5+.5*np.cos(phase*.67)))
        p3+=lateral*(.006*np.sin(phase*.73));p3[2]+=.020*np.sin(phase*.61)
        p2=p3-.28*(p3-p0)+radial*(.013+.012*(.5+.5*np.sin(phase*.43)))
        p2+=lateral*(.010*np.cos(phase*.59))
    if fringe_mode:
        side=1 if c[-1,0]>=0 else -1
        p3=c[-1].copy();p3[0]+=side*(.002+.004*(.5+.5*np.sin(phase*.57)))
        p3[1]-=.003;p3[2]+=.008*np.sin(phase*.61)
        p1=p0+np.array([side*(.006+.007*(.5+.5*np.cos(phase*.43))),
                       -.002,.006+.009*(.5+.5*np.sin(phase*.37))])
        p2=p3-.36*(p3-p0)
        p2+=np.array([side*.006,-.004,.012])
    guide=(1-v)**3*p0+3*(1-v)**2*v*p1+3*(1-v)*v*v*p2+v**3*p3
    if not (fringe_mode or swept_upper):guide=.13*c+.87*guide
    dt,dn,dx=frame(d);gt,gn,gx=frame(guide)
    dev=don-d
    along=np.sum(dev*dt[None],axis=2)
    deep=np.sum(dev*dn[None],axis=2)
    wide=np.sum(dev*dx[None],axis=2)
    if fringe_mode:
        taper=1-.60*smooth((t-.43)/.57)
        along*=taper[None];deep*=taper[None];wide*=taper[None]
    # Restore the real donor's diverse section, rather than forcing all shafts
    # onto ranked cylindrical/fan coordinates. Retain some current scatter so
    # long nape edits and new side layering are not simply replaced by donor.
    section=along[:,:,None]*gt[None]+deep[:,:,None]*gn[None]+wide[:,:,None]*gx[None]
    values=guide[None]+.75*section+.25*(old-c)
    blend=smooth((t-.025)/.22)
    values=old*(1-blend[None,:,None])+values*blend[None,:,None]
    low=smooth((1.740-old[:,:,2])/.060)
    values=values*(1-low[:,:,None])+old*low[:,:,None]
    for i in range(len(members)):
        correction=np.zeros((65,3))
        for j in range(1,65):
            hit,n,_,dist=bv.find_nearest(Vector(values[i,j]));gap=(Vector(values[i,j])-hit).dot(n)
            if dist<.030 and gap<.0006:
                correction[j]=np.array(n)*(.0009-gap);repairs+=1
        envelope=correction.copy();magnitude=np.linalg.norm(correction,axis=1)
        for j in range(1,65):
            lo,hi=max(1,j-4),min(65,j+5);weights=np.maximum(0,1-np.abs(np.arange(lo,hi)-j)/5)
            scores=magnitude[lo:hi]*weights;h=int(np.argmax(scores))
            if scores[h]>np.linalg.norm(envelope[j]):envelope[j]=correction[lo+h]*weights[h]
        values[i]+=envelope
    values[:,0]=old[:,0];q[members]=values;mask[members]=True
    rows.append(dict(group=k,fibers=len(members),maximum_displacement_m=float(np.linalg.norm(values-old,axis=2).max()),
        donor_section_width_m=float(np.quantile(np.abs(wide[:,12:52]),.9)),donor_section_depth_m=float(np.quantile(np.abs(deep[:,12:52]),.9))))
assert mask.sum()>100 and np.isfinite(q).all() and np.array_equal(q[:,0],raw[:,0])
assert np.array_equal(q[~mask],raw[~mask])
if not fringe_mode:assert np.array_equal(q[fringe],raw[fringe])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_authored_swept_upper' if swept_upper else 'native_unranked_fringe_fall' if fringe_mode else 'native_unranked_free_sections'
assert not ob.data.attributes.get(attr)
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
out.mkdir(parents=True);renders.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';pref.get_devices()
for device in pref.devices:device.use=device.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for shot in ['02_ThreeQuarter','01_Front','03_Side','05_OppositeSide']:
    s.camera=bpy.data.objects[shot];s.render.filepath=str(renders/(shot+'.png'));bpy.ops.render.render(write_still=True)
for vv,h in hashes.items():assert hashlib.sha256((ROOT/'Exports'/vv/'Ember_Regent.blend').read_bytes()).hexdigest()==h
(out/'free_sections_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=hashes[base],
    donor=donor,donor_sha256=hashes[donor],selection_attribute=attr,changed_fibers=int(mask.sum()),
    target_groups=K,edited_groups=len(rows),groups=rows,discrete_body_repairs=repairs,
    fringe_mode=fringe_mode,
    swept_upper=swept_upper,
    method=('Non-fringe upper108 whole-path groups use authored tangent-led lead28-75mm plus12-22mm scalp-normal first control,13-25mm radial shoulder relief/10mm lateral stagger,3-10mm radial/6mm lateral and20mm vertical end variation. Full cubic mean,75% transported native103 section plus25% current scatter, low paths blended back. True roots/fringe/radii/topology/other components/materials unchanged.' if swept_upper else 'Actual8539 fringe region in48 whole-flow groups. Explicit6-13mm own-side/6-15mm upward first control; second control lies36% of root-terminal chord back from endpoint plus6mm outward/12mm up/4mm forward. Source endpoints free to stagger8mm vertically/2-6mm laterally/3mm forward. Full broad cubic mean replaces old crossings and tail suffix, native103 section projected into transported frame with60% terminal taper;75% donor plus25% current scatter, true roots/radii/non-fringe/materials retained.' if fringe_mode else 'Non-fringe upper folliclesZ>1.800m with tipsZ>1.690m,108 whole-flow groups. Arc-parameter broad cubic87% mean relaxation with independently staggered controls; minimal-rotation frame transfer restores75% unranked103 intra-lock dispersion plus25% current scatter, without forced fan/cylinder coordinates. First point/true follicle/fringe/radii/topology/materials retained; low current paths blended back below1.740m.'),
    status='Actual draft pending art review; no continuous body/eyes/clothing/motion guarantee'),indent=2),encoding='utf-8')
print('UNRANKED_FREE_SECTIONS',version,int(mask.sum()),len(rows),flush=True)
