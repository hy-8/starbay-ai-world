"""Preview asymmetric side-nape graduation on saved mixed-control hair."""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
save_archive='--save-archive' in a
save_model='--save' in a or save_archive
save_only='--save-only' in a
layered='--layered' in a;pilot='--pilot' in a
attribute='native_raw_rear_layers' if layered else 'native_rounded_nape'
assert not save_only or save_model
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=ROOT/'Renders'/version;assert not out.exists()
modeldir=(Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者\Exports') if save_archive else ROOT/'Exports')/version
if save_archive:assert not (ROOT/'Exports'/version).exists()
if save_model:assert not modeldir.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
assert attribute not in cu.attributes,'Fresh operation attribute required'
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
r=np.empty(len(cu.points),np.float32);cu.attributes['radius'].data.foreach_get('value',r)
sizes=np.array([c.points_length for c in cu.curves]);offsets=np.r_[0,np.cumsum(sizes)]
allowed=np.empty(len(sizes),bool);cu.attributes['native_restored_raw_controls'].data.foreach_get('value',allowed)
paths=[];radii=[];selected=[];shortened=[]
for i in range(len(sizes)):
 path=p[offsets[i]:offsets[i+1]].copy();radius=r[offsets[i]:offsets[i+1]].copy();tip=path[-1]
 eligible=tip[1]>.005 and tip[2]<1.745 and abs(tip[0])>.030
 if layered:eligible=tip[1]>.015 and tip[2]<1.800 and path[0,1]>-.030 and (not pilot or path[0,0]<-.005)
 if allowed[i] and eligible and len(path)>3:
  arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))]
  t=np.clip((abs(tip[0])-.030)/.065,0,1);t=t*t*(3-2*t)
  cut=min(.032*t*(.88+.12*np.sin(path[0,0]*111+path[0,1]*79)),arc[-1]*.22)
  if layered:
   h=np.clip((path[0,2]-1.775)/.090,0,1);h=h*h*(3-2*h)
   field=.45+.55*np.sin(path[0,0]*91+path[0,1]*65)**2
   cut=min(.035,arc[-1]*(.06+.20*h)*field)
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
new.attributes.new(attribute,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data=new
modelhash=None
if save_model:
 modeldir.mkdir(parents=True);new.name='Natural control flow with graduated side nape'
 bpy.ops.wm.save_as_mainfile(filepath=str(modeldir/'Ember_Regent.blend'),compress=True)
 modelhash=hashlib.sha256((modeldir/'Ember_Regent.blend').read_bytes()).hexdigest()
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
out.mkdir(parents=True);dest=out/'04_Back.png';images={}
if not save_only:
 for shot in (['04_Back','03_Side','02_ThreeQuarter'] if '--views' in a else ['04_Back']):
  s.camera=bpy.data.objects[shot];rd=out/(shot+'.png');s.render.filepath=str(rd);bpy.ops.render.render(write_still=True);images[rd.name]=hashlib.sha256(rd.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
manifest=dict(source=base,source_sha256=digest,model_saved=save_model,model_sha256=modelhash,selected_fibers=len(selected),polyline_shortening_quantiles_m=np.quantile(shortened,[0,.5,1]).tolist(),source_unchanged=True,image_sha256=hashlib.sha256(dest.read_bytes()).hexdigest() if dest.exists() else None,method='Restored raw fibers only, endpoints behindY5mm and belowZ1.745m,absX>30mm. Shorten along own control polyline by continuous lateral endpoint field up to32mm and at most22percent length; original control prefix retained, terminal tapered. Accepted frontal paths and central nape retained. Not continuous collision or final art acceptance.')
if layered:manifest.update(operation_attribute=attribute,pilot=pilot,archive_model_path=str(modeldir/'Ember_Regent.blend') if save_model else None,images_sha256=images,method='Restored raw rear fibers only;tipY>15mm,tipZ<1.800m,rootY>-30mm,pilot rootX<-5mm. Shorten own control polyline by6percent+up to20percent smooth root-height term,times coherent root spatial field0.45-1,capped35mm. Exact prefix and terminal interpolation,root unchanged,last4 radii tapered. No resampling of full curve,no common cutting plane;not art or collision proof.')
(out/'rounded_nape_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
if save_model:(modeldir/'rounded_nape_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('ROUNDED_NAPE_PREVIEW',version,flush=True)
