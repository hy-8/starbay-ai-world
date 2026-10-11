"""Form smaller coherent sections within mixed-control posterior flow."""
import bpy,sys,json,hashlib,re
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2];pilot='--pilot' in a
fine='--fine' in a
save='--save-archive' in a
save_only='--save-only' in a
assert not save_only or save
modeldir=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者\Exports')/version
assert not save or not modeldir.exists()
assert all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest();out=ROOT/'Renders'/version;assert not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());original=p.copy()
sizes=np.array([c.points_length for c in cu.curves]);off=np.r_[0,np.cumsum(sizes)];roots=p[off[:-1]];tips=p[off[1:]-1]
mask=np.empty(len(sizes),bool);cu.attributes['native_restored_raw_controls'].data.foreach_get('value',mask)
mask&=(roots[:,1]>-.030)&(tips[:,1]>.015)&(tips[:,2]<1.800)
if pilot:mask&=roots[:,0]<-.005
ids=np.flatnonzero(mask);assert len(ids)>500
ts=np.linspace(0,1,32);sampled=[];arcs=[]
for i in ids:
 path=p[off[i]:off[i+1]];arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))];arcs.append(arc)
 sampled.append(np.column_stack([np.interp(ts*arc[-1],arc,path[:,j]) for j in range(3)]))
sampled=np.array(sampled);features=sampled[:,[0,9,18,27],:].reshape(len(ids),-1)
K=(48 if pilot else 96) if fine else (18 if pilot else 32);centers=[features[len(ids)//2]];distance=np.full(len(ids),np.inf)
for k in range(1,K):
 distance=np.minimum(distance,((features-centers[-1])**2).sum(1));centers.append(features[np.argmax(distance)])
centers=np.array(centers)
for _ in range(18):
 labels=np.argmin(((features[:,None]-centers[None])**2).sum(2),axis=1)
 for k in range(K):
  if np.any(labels==k):centers[k]=features[labels==k].mean(0)
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get());reverted=0;groups=[]
for k in range(K):
 rows=np.flatnonzero(labels==k);center=sampled[rows].mean(0)
 tangent=np.gradient(center,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-10)
 normal=center-np.array([0,-.035,1.776]);normal-=tangent*np.sum(normal*tangent,axis=1)[:,None];normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-10)
 across=np.cross(tangent,normal)
 for row in rows:
  i=ids[row];path=original[off[i]:off[i+1]].astype(float);arc=arcs[row];t=arc/max(arc[-1],1e-8)
  c=np.column_stack([np.interp(t,ts,center[:,j]) for j in range(3)]);ac=np.column_stack([np.interp(t,ts,across[:,j]) for j in range(3)]);ac/=np.maximum(np.linalg.norm(ac,axis=1)[:,None],1e-10)
  width=np.sum((path-c)*ac,axis=1);envelope=smooth((arc-.008)/.017)*(1-smooth((t-(.86 if fine else .72))/(.12 if fine else .23)))
  cap=.0045 if fine else .0024;strength=.78 if fine else .48
  shift=cap*np.tanh(width*strength/cap)*envelope;vals=path-ac*shift[:,None];vals[0]=path[0];vals[-1]=path[-1]
  for j in range(1,len(path)-1):
   if abs(shift[j])<.000001:continue
   h,n,_,d=bv.find_nearest(Vector(vals[j]));oh,on,_,od=bv.find_nearest(Vector(path[j]))
   if (Vector(vals[j])-h).dot(n)<min(.0003,(Vector(path[j])-oh).dot(on)):
    vals[j]=path[j];reverted+=1
  p[off[i]:off[i+1]]=vals.astype(np.float32)
 groups.append(dict(group=k,fibers=len(rows)))
cu.attributes['position'].data.foreach_set('vector',p.ravel());cu.update_tag()
modelhash=None
if save:
 cu.attributes.new('native_fine_rear_sections','BOOLEAN','CURVE').data.foreach_set('value',mask)
 modeldir.mkdir(parents=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(modeldir/'Ember_Regent.blend'),compress=True)
 modelhash=hashlib.sha256((modeldir/'Ember_Regent.blend').read_bytes()).hexdigest()
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE';s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
out.mkdir(parents=True);images={}
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';reflection=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=reflection@cam.matrix_world@reflection
for shot in (['04_Back','05_OppositeSide'] if pilot else ['04_Back','03_Side','05_OppositeSide','02_ThreeQuarter']):
 if save_only:break
 s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=hashlib.sha256(dest.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'rear_sections_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,source_unchanged=True,model_saved=False,pilot=pilot,selected_fibers=len(ids),groups=groups,max_same_index_displacement_m=float(np.linalg.norm(p-original,axis=1).max()),reverted_points=reverted,images_sha256=images,method='Mixed raw rear curves grouped by whole-path features.18pilot/32full deterministic families;48percent transverse contraction smoothly bounded2.4mm,no outward loft. Positions sampled32points only to compute families/frames;original control counts retained. Root8mm and last5percent retained,transition near ends;all radii/materials unchanged. Revert points worsening original signed gap or crossing0.3mm positive gap. Discrete guard,not continuous collision proof.'),indent=2),encoding='utf-8')
print('RAW_REAR_SECTIONS',version,len(ids),flush=True)
manifest=json.loads((out/'rear_sections_manifest.json').read_text(encoding='utf-8'))
manifest.update(model_saved=save,model_sha256=modelhash,archive_model_path=str(modeldir/'Ember_Regent.blend') if save else None,fine_sections=fine,section_count=K,contraction_fraction=.78 if fine else .48,displacement_limit_m=.0045 if fine else .0024,root_retained_arc_m=.008,terminal_retained_fraction=.02 if fine else .05,method='Mixed raw rear curves grouped by whole-path features, parameters recorded separately. Transverse contraction without outward loft.32 arc samples used only for clustering/frames,original control counts and all radii retained. First8mm retained,17mm smooth root onset;terminal fade. Revert any moved control worsening original signed body gap or crossing0.3mm positive gap. Discrete guard only;not continuous collision or art proof.')
(out/'rear_sections_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
if save:(modeldir/'rear_sections_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
