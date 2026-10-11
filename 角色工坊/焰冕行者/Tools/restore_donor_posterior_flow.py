"""Recover early donor posterior flow, resampled smoothly onto current fibers."""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2];pilot='--pilot' in a;blend_boundary='--blend-boundary' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';donorfile=ROOT/'Exports/layercut04/Ember_Regent.blend'
digest=hashlib.sha256(source.read_bytes()).hexdigest();donorhash=hashlib.sha256(donorfile.read_bytes()).hexdigest()
out=ROOT/'Exports'/version;rd=ROOT/'Renders'/version;assert not out.exists() and not rd.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());raw=p.reshape(-1,65,3).astype(float)
mapping=np.load(ROOT/'Exports/nativefocusedpart177/local_retained_indices.npz')['retained'];assert len(mapping)==len(raw)
with bpy.data.libraries.load(str(donorfile),link=False) as (src,dst):dst.objects=['Daniel Bystedt adapted layered cut • CC BY-SA']
donor=dst.objects[0];assert donor and np.array_equal(np.array(donor.matrix_world),np.eye(4))
dcu=donor.data;dp=np.empty((len(dcu.points),3),np.float32);dcu.attributes['position'].data.foreach_get('vector',dp.ravel())
sizes=np.array([c.points_length for c in dcu.curves]);off=np.r_[0,np.cumsum(sizes)];assert len(sizes)==49268 and mapping.max()<len(sizes)
paths=[dp[off[i]:off[i+1]].astype(float).copy() for i in mapping]
bpy.data.objects.remove(donor,do_unlink=True)
dr=np.array([v[0] for v in paths]);dm=np.array([v[len(v)//2] for v in paths]);r=raw[:,0]
protected=np.zeros(len(raw),bool)
for n in ['native_resculpted_fringe_sweeps','native_inner_curtain_shift']:
    v=np.empty(len(raw),bool);cu.attributes[n].data.foreach_get('value',v);protected|=v
mask=(~protected)&(dr[:,1]>.002)&(r[:,1]>.005)&(dm[:,1]>.025)&(r[:,2]>1.730)
if pilot:mask&=r[:,0]<-.005
ids=np.flatnonzero(mask);assert len(ids)>500
root_delta=r[ids]-dr[ids];assert np.linalg.norm(root_delta,axis=1).max()<.030
def smooth_donor(points):
    # Explicit uniform Catmull-Rom, not a claim about exact donor render tessellation.
    control=np.vstack([2*points[0]-points[1],points,2*points[-1]-points[-2]])
    f=np.linspace(0,len(points)-1,513);seg=np.minimum(f.astype(int),len(points)-2);t=(f-seg)[:,None]
    p0,p1,p2,p3=[control[seg+i] for i in range(4)]
    return .5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
q=raw.copy();repairs=0;trimmed=0;lengths=[]
for i in ids:
    dense=smooth_donor(paths[i]);t=np.linspace(0,1,len(dense))
    dense+=(r[i]-dr[i])*(1-t[:,None])**2
    floor=1.673+.010*np.sin(r[i,0]*67+r[i,1]*91)+.004*np.cos(r[i,0]*231-r[i,1]*153)
    hits=np.flatnonzero(dense[:,2]<floor)
    if len(hits):
        j=int(hits[0]);assert j>0
        f=(floor-dense[j-1,2])/(dense[j,2]-dense[j-1,2]);end=dense[j-1]+f*(dense[j]-dense[j-1]);dense=np.vstack([dense[:j],end]);trimmed+=1
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(dense,axis=0),axis=1))];assert arc[-1]>.015
    values=np.column_stack([np.interp(np.linspace(0,arc[-1],65),arc,dense[:,k]) for k in range(3)])
    correction=np.zeros_like(values)
    for j in range(1,65):
        hit,n,_,dist=bv.find_nearest(Vector(values[j]));gap=(Vector(values[j])-hit).dot(n)
        if dist<.030 and gap<.001:correction[j]=np.array(n)*(.0014-gap);repairs+=1
    for axis in range(3):correction[:,axis]=np.convolve(np.pad(correction[:,axis],(2,2),mode='edge'),np.array([1,4,6,4,1])/16,mode='valid')
    values+=correction
    if blend_boundary:
        b=float(np.clip((r[i,1]-.005)/.045,0,1));b=.25+.75*b*b*(3-2*b)
        values=raw[i]+b*(values-raw[i])
    values[0]=r[i];q[i]=values;lengths.append(float(np.linalg.norm(np.diff(values,axis=0),axis=1).sum()))
assert np.array_equal(q[~mask],raw[~mask]) and np.array_equal(q[:,0],raw[:,0]) and np.isfinite(q).all()
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_recovered_donor_back';assert not ob.data.attributes.get(attr)
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
out.mkdir(parents=True);rd.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=192;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
method='Match49268 original donor curves through177 retained mapping. Exclude accepted curtain/fringe; originalrootY>2mm,currentrootY>5mm,donormidY>25mm,currentrootZ>1.730m;pilotcurrentrootX<-5mm. Explicit Catmull-Rom dense sampling,root delta decays along source parameter; cut first crossing root-field1.673m+-14mm plane then65 arc samples. Current true roots/radii/topology/materials retained. Not exact original tessellation,not continuous collision proof.'
if blend_boundary:method+=' After sampled contact correction, source/candidate position blend by rootY:25% at5mm smoothly rising to100% at50mm. This blend does not prove collision clearance.'
(out/'donor_back_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,donor='layercut04',donor_sha256=donorhash,pilot=pilot,blend_boundary=blend_boundary,selected_fibers=len(ids),selection_attribute=attr,root_shift_quantiles_m=np.quantile(np.linalg.norm(root_delta,axis=1),[0,.5,1]).tolist(),trimmed_fibers=trimmed,sampled_body_repairs=repairs,length_quantiles_m=np.quantile(lengths,[0,.5,1]).tolist(),method=method,status='Actual recovered-flow study awaiting visual review'),indent=2),encoding='utf-8')
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for shot in ['04_Back','05_OppositeSide','02_ThreeQuarter']:
    s.camera=bpy.data.objects[shot];s.render.filepath=str(rd/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest and hashlib.sha256(donorfile.read_bytes()).hexdigest()==donorhash
print('DONOR_BACK_RENDERED',version,len(ids),flush=True)
