"""Raw donor controls with protected fringe; optional fresh saved candidate."""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
guard_front='--guard-front' in a
guard_crown='--guard-crown' in a
save_model='--save' in a
save_only='--save-only' in a
assert not save_only or save_model
assert not guard_crown or guard_front
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';donorpath=ROOT/'Exports/layercut04/Ember_Regent.blend'
digest=hashlib.sha256(source.read_bytes()).hexdigest();dh=hashlib.sha256(donorpath.read_bytes()).hexdigest()
out=ROOT/'Renders'/version;assert not out.exists()
modeldir=ROOT/'Exports'/version
if save_model:assert not modeldir.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());raw=p.reshape(-1,65,3)
rad=np.empty(len(cu.points),np.float32);cu.attributes['radius'].data.foreach_get('value',rad);rad=rad.reshape(-1,65)
protected=np.zeros(len(raw),bool)
for n in ['native_resculpted_fringe_sweeps','native_inner_curtain_shift']:
 f=np.empty(len(raw),bool);cu.attributes[n].data.foreach_get('value',f);protected|=f
mapping=np.load(ROOT/'Exports/nativefocusedpart177/local_retained_indices.npz')['retained'];assert len(mapping)==len(raw)
with bpy.data.libraries.load(str(donorpath),link=False) as (src,dst):dst.objects=['Daniel Bystedt adapted layered cut • CC BY-SA']
donor=dst.objects[0];assert donor and np.array_equal(np.array(donor.matrix_world),np.eye(4))
dc=donor.data;dp=np.empty((len(dc.points),3),np.float32);dc.attributes['position'].data.foreach_get('vector',dp.ravel())
drad=np.empty(len(dc.points),np.float32);dc.attributes['radius'].data.foreach_get('value',drad)
sz=np.array([c.points_length for c in dc.curves]);off=np.r_[0,np.cumsum(sz)]
paths=[];radii=[];trimmed=0;rootdelta=[]
accepted_count=int(protected.sum())
if guard_front:
 for i,k in enumerate(mapping):
  if dp[off[k]:off[k+1],1].min()<-.090:protected[i]=True
if guard_crown:
 for i,k in enumerate(mapping):
  dpath=dp[off[k]:off[k+1]]
  if dpath[0,1]<.015 and dpath[:,2].max()>1.880:protected[i]=True
for i,k in enumerate(mapping):
 if protected[i]:paths.append(raw[i].copy());radii.append(rad[i].copy());continue
 path=dp[off[k]:off[k+1]].copy();r=drad[off[k]:off[k+1]].copy();rootdelta.append(float(np.linalg.norm(path[0]-raw[i,0])))
 floor=1.681+.010*np.sin(path[0,0]*83+path[0,1]*67)+.007*np.clip(abs(path[0,0])/.09,0,1)
 below=np.flatnonzero(path[:,2]<floor)
 if guard_front and len(below) and below[0]==0:
  delta=path[1]-path[0];path=np.vstack([path[0],path[0]+delta*min(1,.004/max(np.linalg.norm(delta),1e-9))]);r=np.array([r[0],r[0]*.01],np.float32);trimmed+=1
 elif len(below) and below[0]>(0 if guard_front else 1):
  j=int(below[0]);frac=(floor-path[j-1,2])/(path[j,2]-path[j-1,2]);end=path[j-1]+frac*(path[j]-path[j-1]);path=np.vstack([path[:j],end]);r=r[:j+1].copy();trimmed+=1
  taper=np.linspace(0,1,min(4,len(r)));r[-len(taper):]*=(1-.99*taper**1.4)
 assert len(path)>=2 and np.isfinite(path).all() and np.all(r>0)
 paths.append(path);radii.append(r)
bpy.data.objects.remove(donor,do_unlink=True)
new=bpy.data.hair_curves.new('Raw donor controls and accepted current fringe • diagnostic')
new.add_curves([len(p) for p in paths]);new.attributes['position'].data.foreach_set('vector',np.concatenate(paths).ravel());new.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.concatenate(radii));new.materials.append(cu.materials[0])
copied=[]
for attribute in cu.attributes:
 if attribute.domain!='CURVE':continue
 field,width,dtype={'BOOLEAN':('value',1,bool),'INT':('value',1,np.int32),'FLOAT':('value',1,np.float32),'FLOAT_VECTOR':('vector',3,np.float32),'FLOAT2':('vector',2,np.float32),'FLOAT_COLOR':('color',4,np.float32)}[attribute.data_type]
 values=np.empty(len(attribute.data)*width,dtype=dtype);attribute.data.foreach_get(field,values)
 target=new.attributes.get(attribute.name) or new.attributes.new(attribute.name,attribute.data_type,'CURVE')
 target.data.foreach_set(field,values);copied.append(attribute.name)
new.attributes.new('native_restored_raw_controls','BOOLEAN','CURVE').data.foreach_set('value',~protected)
new.attributes.new('native_original_donor_index','INT','CURVE').data.foreach_set('value',mapping.astype(np.int32))
hidden=[]
for other in bpy.data.objects:
 if other.type=='CURVES' and not other.hide_render and other!=ob:
  if not guard_front or other.name.startswith('Original posterior coverage'):other.hide_render=True;hidden.append(other.name)
ob.data=new
modelhash=None
if save_model:
 new.name='Original control flow with protected side part'
 modeldir.mkdir(parents=True)
 np.savez_compressed(modeldir/'local_raw_control_mapping.npz',donor_indices=mapping,protected=protected)
 bpy.ops.wm.save_as_mainfile(filepath=str(modeldir/'Ember_Regent.blend'),compress=True)
 modelhash=hashlib.sha256((modeldir/'Ember_Regent.blend').read_bytes()).hexdigest()
 print('RAW_CONTROL_MODEL_SAVED',version,flush=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100;out.mkdir(parents=True)
images={}
for shot in ([] if save_only else ['03_Side','02_ThreeQuarter','04_Back']):
 s.camera=bpy.data.objects[shot];path=out/(shot+'.png');s.render.filepath=str(path);bpy.ops.render.render(write_still=True);images[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest and hashlib.sha256(donorpath.read_bytes()).hexdigest()==dh
method='Read-only diagnostic. Current accepted fringe exact; other mapped strands retain original donor control positions/root/radius, cut at first raw-control segment crossing a varied nape floor and taper last4 controls. No Catmull-Rom dense resampling,root movement or body contact correction; support objects hidden temporarily. Current primary material and lights. This deliberately changes non-fringe root attachment and topology; NOT contact-validated or saved delivery.'
if guard_front:method+=' Preserve current paths wherever donor has any controlY<-90mm;retain Abhay/Bystedt support,hide only original posterior support. Low-root donor controls beginning below floor cut to at most4mm first segment; first-segment floor crossings handled.'
if guard_crown:method+=' Also preserve current paths for donorrootY<15mm with anycontrolZ>1.880m to retain the settled frontal crown.'
if save_model:method=method.replace('Read-only diagnostic.','Saved candidate.').replace('support objects hidden temporarily','original posterior support hidden in render').replace('NOT contact-validated or saved delivery','NOT contact-validated or final delivery')
manifest=dict(source=base,source_sha256=digest,donor='layercut04',donor_sha256=dh,source_unchanged=True,model_saved=save_model,model_sha256=modelhash,guard_front=guard_front,guard_crown=guard_crown,accepted_fringe_fibers=accepted_count,current_paths_preserved=int(protected.sum()),raw_donor_fibers=int((~protected).sum()),trimmed_fibers=trimmed,point_count=len(new.points),source_root_delta_quantiles_m=np.quantile(rootdelta,[0,.5,1]).tolist(),hidden_support_objects=hidden,copied_curve_attributes=copied,images_sha256=images,method=method)
(out/'raw_control_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
if save_model:(modeldir/'raw_control_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('RAW_CONTROL_DIAGNOSTIC_RENDERED',version,flush=True)
