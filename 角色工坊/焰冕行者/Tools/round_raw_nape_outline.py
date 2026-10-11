"""Preview asymmetric side-nape graduation on saved mixed-control hair."""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
save_model='--save' in a
save_only='--save-only' in a
assert not save_only or save_model
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=ROOT/'Renders'/version;assert not out.exists()
modeldir=ROOT/'Exports'/version
if save_model:assert not modeldir.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
r=np.empty(len(cu.points),np.float32);cu.attributes['radius'].data.foreach_get('value',r)
sizes=np.array([c.points_length for c in cu.curves]);offsets=np.r_[0,np.cumsum(sizes)]
allowed=np.empty(len(sizes),bool);cu.attributes['native_restored_raw_controls'].data.foreach_get('value',allowed)
paths=[];radii=[];selected=[];shortened=[]
for i in range(len(sizes)):
 path=p[offsets[i]:offsets[i+1]].copy();radius=r[offsets[i]:offsets[i+1]].copy();tip=path[-1]
 if allowed[i] and tip[1]>.005 and tip[2]<1.745 and abs(tip[0])>.030 and len(path)>3:
  arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))]
  t=np.clip((abs(tip[0])-.030)/.065,0,1);t=t*t*(3-2*t)
  cut=min(.032*t*(.88+.12*np.sin(path[0,0]*111+path[0,1]*79)),arc[-1]*.22)
  target=arc[-1]-cut;j=int(np.searchsorted(arc,target,side='left'))
  if j>1 and cut>.001:
   f=(target-arc[j-1])/max(arc[j]-arc[j-1],1e-9)
   end=path[j-1]+f*(path[j]-path[j-1]);path=np.vstack([path[:j],end]);radius=radius[:j+1]
   # Taper the retained source radii; existing taper may still be in this prefix.
   k=min(4,len(radius)-1);ramp=np.linspace(0,1,k);radius[-k:]*=1-.99*ramp**1.4
   selected.append(i);shortened.append(float(cut))
 paths.append(path);radii.append(radius)
new=bpy.data.hair_curves.new('Rounded side nape outline • diagnostic');new.add_curves([len(x) for x in paths])
new.attributes['position'].data.foreach_set('vector',np.concatenate(paths).ravel());new.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.concatenate(radii));new.materials.append(cu.materials[0])
for attr in cu.attributes:
 if attr.domain!='CURVE':continue
 field,width,dtype={'BOOLEAN':('value',1,bool),'INT':('value',1,np.int32),'FLOAT':('value',1,np.float32),'FLOAT_VECTOR':('vector',3,np.float32),'FLOAT2':('vector',2,np.float32),'FLOAT_COLOR':('color',4,np.float32)}[attr.data_type]
 values=np.empty(len(attr.data)*width,dtype);attr.data.foreach_get(field,values)
 target=new.attributes.get(attr.name) or new.attributes.new(attr.name,attr.data_type,'CURVE');target.data.foreach_set(field,values)
mask=np.zeros(len(sizes),bool);mask[selected]=True
new.attributes.new('native_rounded_nape','BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data=new
modelhash=None
if save_model:
 modeldir.mkdir(parents=True);new.name='Natural control flow with graduated side nape'
 bpy.ops.wm.save_as_mainfile(filepath=str(modeldir/'Ember_Regent.blend'),compress=True)
 modelhash=hashlib.sha256((modeldir/'Ember_Regent.blend').read_bytes()).hexdigest()
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
out.mkdir(parents=True);dest=out/'04_Back.png'
if not save_only:
 s.camera=bpy.data.objects['04_Back'];s.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
manifest=dict(source=base,source_sha256=digest,model_saved=save_model,model_sha256=modelhash,selected_fibers=len(selected),polyline_shortening_quantiles_m=np.quantile(shortened,[0,.5,1]).tolist(),source_unchanged=True,image_sha256=hashlib.sha256(dest.read_bytes()).hexdigest() if dest.exists() else None,method='Restored raw fibers only, endpoints behindY5mm and belowZ1.745m,absX>30mm. Shorten along own control polyline by continuous lateral endpoint field up to32mm and at most22percent length; original control prefix retained, terminal tapered. Accepted frontal paths and central nape retained. Not continuous collision or final art acceptance.')
(out/'rounded_nape_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
if save_model:(modeldir/'rounded_nape_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('ROUNDED_NAPE_PREVIEW',version,flush=True)
