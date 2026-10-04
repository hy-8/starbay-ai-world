"""Non-destructive layer-isolation renders of an existing actual CURVES groom.

Outputs only new diagnostic PNG/JSON evidence. Never saves over the source.
Layer isolation is not a finished character presentation.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:]
version,source_version=args[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in (version,source_version)):raise ValueError(args)
output=ROOT/'Renders'/version
if output.exists():raise RuntimeError('Preserve previous diagnostics')
output.mkdir(parents=True)
source=ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
objects=[o for o in bpy.data.collections['05_Hair'].objects if o.type=='CURVES']
assert len(objects)==3,[o.name for o in objects]
report=dict(source=source_version,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),layers=[],shots=[])
for ob in objects:
 cu=ob.data
 xyz=np.empty(len(cu.points)*3,np.float32);cu.attributes['position'].data.foreach_get('vector',xyz);xyz=xyz.reshape(-1,3)
 offsets=np.r_[0,np.cumsum([len(c.points) for c in cu.curves])]
 roots=xyz[offsets[:-1]]
 active=[]
 for a,b in zip(offsets[:-1],offsets[1:]):
  s=xyz[a:b]
  if ((s[:,1]<-.11)&(s[:,2]>1.83)).any():active.append(int(a))
 report['layers'].append(dict(object=ob.name,curves=len(cu.curves),root_min=roots.min(axis=0).tolist(),root_max=roots.max(axis=0).tolist(),root_quantiles=np.quantile(roots,[.1,.5,.9],axis=0).tolist(),strands_reaching_upper_front=len(active)))
scene=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for device in pref.devices:device.use=device.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=96;scene.cycles.use_denoising=False
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=70
scene.camera=bpy.data.objects['01_Front']
shots=[('01_All_Layers',None),('02_Only_Authored','Authored'),('03_Only_Support','short scalp'),('04_Only_Preserved','retained side')]
for name,keyword in shots:
 for ob in objects:ob.hide_render=keyword is not None and keyword not in ob.name
 scene.render.filepath=str(output/(name+'.png'));bpy.ops.render.render(write_still=True)
 report['shots'].append(dict(file=name+'.png',isolated_layer=keyword,sha256=hashlib.sha256((output/(name+'.png')).read_bytes()).hexdigest()))
report['source_unchanged']=hashlib.sha256(source.read_bytes()).hexdigest()==report['source_sha256']
(output/'layer_diagnostic.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('LAYER_DIAGNOSTIC_COMPLETE',version,report['source_unchanged'],flush=True)
