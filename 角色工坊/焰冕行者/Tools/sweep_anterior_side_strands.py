"""Turn isolated anterior-side curtains backward along a smooth local field."""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2];pilot='--pilot' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=ROOT/'Exports'/version;rd=ROOT/'Renders'/version;assert not out.exists() and not rd.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());raw=p.reshape(-1,65,3).astype(float)
protected=np.zeros(len(raw),bool)
for attr in ['native_resculpted_fringe_sweeps','native_inner_curtain_shift']:
    v=np.empty(len(raw),bool);cu.attributes[attr].data.foreach_get('value',v);protected|=v
r=raw[:,0]
box=(np.abs(raw[:,:,0])>.065)&(raw[:,:,1]>-.085)&(raw[:,:,1]<-.025)&(raw[:,:,2]>1.805)&(raw[:,:,2]<1.860)
mask=(~protected)&(box.sum(1)>=10)&(r[:,1]<-.035)&(raw[:,-1,1]<.010)&(raw[:,-1,2]>1.775)
if pilot:mask&=r[:,0]>.005
ids=np.flatnonzero(mask);assert len(ids)>100
t=np.linspace(0,1,65);u=np.clip((t-t[9])/(1-t[9]),0,1);fall=u*u*(3-2*u)
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
q=raw.copy();repairs=0
for i in ids:
    amplitude=.020+.010*(.5+.5*np.sin(r[i,0]*71+r[i,1]*94))
    q[i,:,1]+=amplitude*fall
    q[i,:,2]+=.003*fall
    correction=np.zeros((65,3))
    for j in range(10,65):
        hit,n,_,distance=bv.find_nearest(Vector(q[i,j]));gap=(Vector(q[i,j])-hit).dot(n)
        if distance<.030 and gap<.001:correction[j]=np.array(n)*(.0014-gap);repairs+=1
    for k in range(3):correction[:,k]=np.convolve(np.pad(correction[:,k],(2,2),mode='edge'),[.0625,.25,.375,.25,.0625],mode='valid')
    q[i]+=correction;q[i,:10]=raw[i,:10]
assert np.array_equal(q[:,:10],raw[:,:10]) and np.array_equal(q[~mask],raw[~mask]) and np.isfinite(q).all()
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_anterior_side_back_sweep';assert not ob.data.attributes.get(attr)
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=192;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
out.mkdir(parents=True);rd.mkdir(parents=True);bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'),compress=True)
(out/'anterior_sweep_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,pilot=pilot,selected_fibers=len(ids),selection_attribute=attr,preserved_prefix_points=10,sampled_body_repairs=repairs,max_displacement_m=float(np.linalg.norm(q-raw,axis=2).max()),method='Exclude accepted fringe/curtain. >=10 points in absX>65mm,Y(-85,-25)mm,Z(1.805,1.860)m;rootY<-35mm,tipY<10mm,tipZ>1.775m. Pilot positiveX. Smooth20-30mm backwardY field and3mm endZ rise after first10 points. Sampled body correction smoothed,not continuous collision proof.'),indent=2),encoding='utf-8')
if not pilot:
    cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for shot in (['03_Side','02_ThreeQuarter'] if pilot else ['03_Side','05_OppositeSide','02_ThreeQuarter']):
    s.camera=bpy.data.objects[shot];s.render.filepath=str(rd/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
print('ANTERIOR_SIDE_SWEPT',version,len(ids),flush=True)
