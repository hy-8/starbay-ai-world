"""Deterministic staggered tip lengths; no transverse displacement or new hairs."""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=ROOT/'Renders'/version;assert not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
r=np.empty(len(p),np.float32);cu.attributes['radius'].data.foreach_get('value',r)
sizes=np.array([c.points_length for c in cu.curves]);off=np.r_[0,np.cumsum(sizes)];roots=p[off[:-1]]
def flag(name):
 v=np.empty(len(sizes),bool);cu.attributes[name].data.foreach_get('value',v);return v
rng=np.random.default_rng(246);choice=rng.random(len(sizes));depth=rng.random(len(sizes))
mask=(~flag('native_restored_raw_controls'))&(~flag('native_inner_curtain_shift'))&(roots[:,0]>.003)&(roots[:,2]>1.820)&(choice<.60)
paths=[];radii=[];cuts=[]
for i,n in enumerate(sizes):
 path=p[off[i]:off[i+1]].copy();rad=r[off[i]:off[i+1]].copy()
 if mask[i]:
  arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))]
  target=arc[-1]*(.80+.15*depth[i]);j=max(12,int(np.searchsorted(arc,target)))
  if j>=n:mask[i]=False
  else:
   cuts.append(float(arc[-1]-arc[j-1]));path=path[:j];rad=rad[:j]
   t=np.linspace(0,1,min(6,j-1));rad[-len(t):]*=1-.99*t**1.4
 paths.append(path);radii.append(rad)
new=bpy.data.hair_curves.new('Staggered frontal tip layers');new.add_curves([len(x) for x in paths])
new.attributes['position'].data.foreach_set('vector',np.concatenate(paths).ravel());new.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.concatenate(radii));new.materials.append(cu.materials[0])
for attr in cu.attributes:
 if attr.domain!='CURVE':continue
 field,width,dtype={'BOOLEAN':('value',1,bool),'INT':('value',1,np.int32),'FLOAT':('value',1,np.float32),'FLOAT_VECTOR':('vector',3,np.float32),'FLOAT2':('vector',2,np.float32),'FLOAT_COLOR':('color',4,np.float32)}[attr.data_type]
 values=np.empty(len(attr.data)*width,dtype);attr.data.foreach_get(field,values)
 target=new.attributes.get(attr.name) or new.attributes.new(attr.name,attr.data_type,'CURVE');target.data.foreach_set(field,values)
new.attributes.new('native_pointcut_front','BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data=new
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE';s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
out.mkdir(parents=True);images={}
for shot in ['02_ThreeQuarter','03_Side']:
 s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=hashlib.sha256(dest.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'pointcut_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,source_unchanged=True,model_saved=False,selected_fibers=int(mask.sum()),cut_quantiles_m=np.quantile(cuts,[0,.5,1]).tolist(),images_sha256=images,method='Deterministic60percent sample of positiveX nonrestored non-inner-curtain high-root fibers. Retain own exact control prefixes up to80-95percent arc length, minimum12controls. Last6radiuses tapered. No roots moved, no transverse bend, no material changes; preview needs actual art review.'),indent=2),encoding='utf-8')
print('FRONTAL_POINTCUT_PREVIEW',version,int(mask.sum()),flush=True)
