"""Reconcile restored-donor strand gauge without moving existing hair paths."""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
all_restored='--all-restored' in a
rear='--rear-midshaft' in a
selection=a[a.index('--surface-selection')+1] if '--surface-selection' in a else None
if selection:assert rear and re.fullmatch('[A-Za-z0-9_-]+',selection)
archive=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者')
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=(archive if '--archive' in a else ROOT)/'Renders'/version;assert not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
mask=np.empty(len(cu.curves),bool);cu.attributes['native_restored_raw_controls'].data.foreach_get('value',mask)
if not all_restored and not rear:
 upper=np.empty(len(mask),bool);cu.attributes['native_spatial_crown_release'].data.foreach_get('value',upper);mask&=upper
sizes=np.array([c.points_length for c in cu.curves]);starts=np.r_[0,np.cumsum(sizes)[:-1]]
r=np.empty(len(cu.points),np.float32);cu.attributes['radius'].data.foreach_get('value',r);old=r.copy()
factor=np.ones(len(mask),np.float32);factor[mask]=.50
if rear:
 p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());ends=starts+sizes-1
 mask&=(p[starts,1]>-.030)&(p[ends,1]>.015)&(p[ends,2]<1.800)
 if selection:
  selected=archive/'Renders'/selection
  meta=json.loads((selected/'edit_id_manifest.json').read_text());assert meta['source_sha256']==digest
  visible=np.zeros(len(mask),bool);visible[np.load(selected/'local_projected_indices.npz')['selected']]=True
  mask&=visible
  mask&=np.maximum.reduceat(old,starts)>.000060
  for key in ['native_inner_curtain_shift','native_resculpted_fringe_sweeps','native_curved_projected_tips']:
   protected=np.empty(len(mask),bool);cu.attributes[key].data.foreach_get('value',protected);mask&=~protected
 for i in np.flatnonzero(mask):
  st=starts[i];end=st+sizes[i];path=p[st:end];arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))]
  if selection:
   t=np.clip((arc-.012)/.020,0,1);t=t*t*(3-2*t)
   r[st:end]=old[st:end]+(np.minimum(old[st:end],.000045)-old[st:end])*t
  else:
   t=np.clip((arc-.008)/.027,0,1);t=t*t*(3-2*t);r[st:end]*=1-.38*t
else:r*=np.repeat(factor,sizes)
cu.attributes['radius'].data.foreach_set('value',r)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE';s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
out.mkdir(parents=True);images={}
for shot in (['04_Back','02_ThreeQuarter'] if selection else ['04_Back','03_Side'] if rear else ['02_ThreeQuarter','03_Side','04_Back'] if all_restored else ['02_ThreeQuarter','03_Side']):
 s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=hashlib.sha256(dest.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
method='Read-only actual geometry study. Multiply selected restored raw donor radii by0.50, retaining existing taper, control positions, counts, materials, lights, and accepted frontal paths/radii. Upper-only mode intersects historical spatial_crown_release selection;all-restored uses full donor-restoration set. No final acceptance.'
if rear:method='Restored raw rear fibers with rootY>-30mm,tipY>15mm,tipZ<1.800m. Keep first8mm radius exact,then smooth transition over27mm to62percent original radius. Positions/counts/materials/lights and nonselected fibers unchanged;intended to retain root coverage. Actual art review required.'
if selection:method='Intersect inspected approximate visible-control selection with restored rear-reaching fibers and max radius>60microns; exclude accepted inner curtain/frontal sweeps/curved accent. Preserve first12mm radii, smooth20mm ramp toward capped45micron radius. Existing thinner shafts unaffected. Positions/counts/materials/lights unchanged. Approximate point-depth selection is not ray visibility; preview only, no art acceptance.'
(out/'gauge_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,model_saved=False,source_unchanged=True,all_restored=all_restored,rear_midshaft=rear,selected_fibers=int(mask.sum()),root_radius_before_m=np.quantile(old[starts[mask]],[0,.5,1]).tolist(),root_radius_after_m=np.quantile(r[starts[mask]],[0,.5,1]).tolist(),images_sha256=images,method=method),indent=2),encoding='utf-8');print('STRAND_GAUGE_PREVIEW',version,flush=True)
