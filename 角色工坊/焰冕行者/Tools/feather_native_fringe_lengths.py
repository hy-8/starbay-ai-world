"""Free frontal ends: deliberate staggered lengths with untouched crown/root."""
import bpy,sys,json,re,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:2]):raise ValueError(a)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh fringe-length study')
source=ROOT/'Exports'/base/'Ember_Regent.blend';bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float);q=raw.copy();labels=np.empty(len(cu.curves),np.int32);cu.attributes['native_front_guide_index'].data.foreach_get('value',labels)
t=np.linspace(0,1,65);mask=np.zeros(len(raw),bool);rows=[]
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
for g in np.unique(labels[labels>=0]):
 ids=np.flatnonzero(labels==g);old=raw[ids];tip=old[:,-1].mean(axis=0)
 if not (-.076<tip[0]<-.014 and tip[2]>1.751):continue
 phase=g*2.399963
 # Long central feather and shorter adjacent tips, rather than one cut line.
 drop=.006+.012*smooth((.067-abs(tip[0]))/.044)+.003*np.cos(phase)
 delta=np.array([.002*np.sin(phase),-.002,-drop])
 free=smooth((t-.48)/.52)[None]*smooth((1.821-old[:,:,2])/.025)
 values=old+delta[None,None]*free[:,:,None]
 values[:,:,0]+=.002*np.sin(np.pi*smooth((t-.49)/.51))[None]*np.sin(phase)*free
 values[:,:4]=old[:,:4];q[ids]=values;mask[ids]=True
 rows.append(dict(fibers=len(ids),tip_drop_m=float(drop),max_displacement_m=float(np.linalg.norm(values-old,axis=2).max())))
assert np.array_equal(q[:,:4],raw[:,:4]) and np.array_equal(q[~mask],raw[~mask]) and np.isfinite(q).all()
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
ob.data.attributes.new('native_fringe_feather','BOOLEAN','CURVE').data.foreach_set('value',mask)
out.mkdir(parents=True);render.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
(out/'fringe_feather_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),changed_fibers=int(mask.sum()),sections=rows,all_first_four_points_exact=True,unselected_primary_exact=True,other_hair_unchanged=True,method='Central/heavy-side existing native fringe: 6-21mm staggered end extension below z1.821, lower48%-100% shaft window, small coherent tip sway; crown and real follicles retained',status='Unreviewed actual fringe-length study',scope='No eye/face/clothing/segment/animation collision approval'),indent=2),encoding='utf-8')
print('NATIVE_FRINGE_FEATHER_SAVED',version,int(mask.sum()),len(rows),flush=True)
