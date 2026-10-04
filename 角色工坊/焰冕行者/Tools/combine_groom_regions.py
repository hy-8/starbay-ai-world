"""Combine independently reviewed actual curve regions in a fresh static scene.

Mixed-license hair study: Bystedt CC BY-SA frontal support; Ddr Rcs Royalty
Free side/nape derivatives. Keep geometric candidate local, not an asset pack.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version,side_version,front_version=args[:3];DRAFT='--draft' in args
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in (version,side_version,front_version)):raise ValueError(args)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh output only')
out.mkdir(parents=True);render.mkdir(parents=True)
source=ROOT/'Exports'/side_version/'Ember_Regent.blend';frontal=ROOT/'Exports'/front_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
old=bpy.data.objects['Licensed Ddr Rcs derivative • actual native curves'];cu=old.data
positions=np.empty(len(cu.points)*3,np.float32);cu.attributes['position'].data.foreach_get('vector',positions);positions=positions.reshape(-1,3)
radii=np.empty(len(cu.points),np.float32);cu.attributes['radius'].data.foreach_get('value',radii)
sizes=[len(c.points) for c in cu.curves];kept=[];kept_radii=[];offset=0;removed=0;nape=0
rng=np.random.default_rng(100510);cache={}
for size in sizes:
 s=positions[offset:offset+size].copy();rad=radii[offset:offset+size].copy();offset+=size;r=s[0];end=s[-1]
 retain=(r[1]>-.025 and r[2]<1.868) or (abs(r[0])>.071 and r[2]<1.844) or r[2]<1.803
 if end[1]<-.14 and end[2]>1.72:retain=False
 if not retain:removed+=1;continue
 t=np.linspace(0,1,size)
 if end[2]<1.710 and r[1]>-.016:
  key=(int(np.floor(r[0]/.014)),int(np.floor(r[1]/.018)))
  if key not in cache:cache[key]=(rng.uniform(.009,.042),rng.uniform(.003,.007),rng.uniform(-.7,.7))
  drop,amp,phase=cache[key];env=np.maximum(0,(t-.48)/.52)**1.6
  s[:,2]-=(drop+rng.uniform(-.002,.002))*env
  s[:,0]+=amp*np.sin(t*2.6*np.pi+phase)*np.sin(np.pi*t)
  s[:,1]+=.008*env
  s[0]=r;nape+=1
 kept.append(s);kept_radii.append(rad)
if len(kept)<1000:raise RuntimeError('Insufficient retained side/nape coverage')
old.hide_render=True;old.hide_viewport=True
collection=bpy.data.collections.new('05_Region_Composite_Groom');bpy.context.scene.collection.children.link(collection)
new=bpy.data.hair_curves.new('Ddr Rcs retained side/nape • layered derivative');new.add_curves([len(s) for s in kept]);new.attributes['position'].data.foreach_set('vector',np.concatenate(kept).ravel())
new.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.concatenate(kept_radii));new.materials.append(cu.materials[0])
side=bpy.data.objects.new('Ddr Rcs derivative • region-selected side and nape',new);collection.objects.link(side)
selected=['Authored spatial fringe • actual scalp root patches','Bystedt derivative • short scalp support']
with bpy.data.libraries.load(str(frontal),link=False) as (available,loaded):
 if not all(n in available.objects for n in selected):raise RuntimeError('Expected regional source objects missing')
 loaded.objects=selected
imported=[]
for ob in loaded.objects:
 ob.hide_render=False;ob.hide_viewport=False;collection.objects.link(ob);imported.append(dict(object=ob.name,curves=len(ob.data.curves)))
credits=bpy.data.texts.new('REGIONAL_GROOM_CREDITS')
credits.write('Frontal styling: local scalp patches and project-authored spatial paths. Short frontal support retains Daniel Bystedt Hair Styles CC BY-SA, version unspecified in inspected evidence. Side/nape: Ddr Rcs Female Shaggy Mullet Haircut, BlenderKit Royalty Free, actual card-derived curves; shortened and mildly waved. Preserve both original credits and modification notices. Keep original/derived geometry locally; do not distribute as a standalone hair asset pack. This is an unapproved static modeling study.\n')
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for device in pref.devices:device.use=device.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=64 if DRAFT else 192;scene.cycles.use_denoising=False;scene.cycles_curves.shape='THICK'
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=80 if DRAFT else 100
report=dict(version=version,side_source=side_version,side_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),front_source=front_version,front_source_sha256=hashlib.sha256(frontal.read_bytes()).hexdigest(),retained_side_nape=len(kept),discarded_source_front=removed,nape_curves_relayered=nape,imported_front=imported,license='Mixed component licenses: Bystedt-derived support CC BY-SA, version unspecified; Ddr Rcs side/nape Royalty Free. Not CC0.',draft=DRAFT,status='unreviewed actual regional study',collision_validation='not exhaustive; no animation or clothing collision proof')
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('REGIONAL_GROOM_RENDERED',version,len(kept),removed,nape,flush=True)
