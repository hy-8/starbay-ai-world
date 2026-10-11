"""Reconcile restored-donor strand gauge without moving existing hair paths."""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
all_restored='--all-restored' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=ROOT/'Renders'/version;assert not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
mask=np.empty(len(cu.curves),bool);cu.attributes['native_restored_raw_controls'].data.foreach_get('value',mask)
if not all_restored:
 upper=np.empty(len(mask),bool);cu.attributes['native_spatial_crown_release'].data.foreach_get('value',upper);mask&=upper
sizes=np.array([c.points_length for c in cu.curves]);starts=np.r_[0,np.cumsum(sizes)[:-1]]
r=np.empty(len(cu.points),np.float32);cu.attributes['radius'].data.foreach_get('value',r);old=r.copy()
factor=np.ones(len(mask),np.float32);factor[mask]=.50
r*=np.repeat(factor,sizes);cu.attributes['radius'].data.foreach_set('value',r)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE';s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
out.mkdir(parents=True);images={}
for shot in (['02_ThreeQuarter','03_Side','04_Back'] if all_restored else ['02_ThreeQuarter','03_Side']):
 s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=hashlib.sha256(dest.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'gauge_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,model_saved=False,source_unchanged=True,all_restored=all_restored,selected_fibers=int(mask.sum()),root_radius_before_m=np.quantile(old[starts[mask]],[0,.5,1]).tolist(),root_radius_after_m=np.quantile(r[starts[mask]],[0,.5,1]).tolist(),images_sha256=images,method='Read-only actual geometry study. Multiply selected restored raw donor radii by0.50, retaining existing taper, control positions, counts, materials, lights, and accepted frontal paths/radii. Upper-only mode intersects historical spatial_crown_release selection; all-restored uses full donor-restoration set. No final acceptance.'),indent=2),encoding='utf-8');print('STRAND_GAUGE_PREVIEW',version,flush=True)
