"""Remove a small, inspected projected set in a fresh groom; preserve all remaining paths."""
import bpy,sys,json,hashlib,re
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base,idsversion=a[:3]
assert all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:3])
save='--save-archive' in a;save_only='--save-only' in a;assert not save_only or save
short_hook='--short-hook' in a;assert not (short_hook and save),'Preview this filtered removal before enabling a saved variant'
archive=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者')
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
sel=ROOT/'Renders'/idsversion
if not (sel/'edit_id_manifest.json').exists():sel=archive/'Renders'/idsversion
idm=json.loads((sel/'edit_id_manifest.json').read_text());assert idm['source_sha256']==digest
selected=np.load(sel/'local_projected_indices.npz')['selected'];assert 0<len(selected)<=(500 if short_hook else 200),'Only small inspected stray sets allowed'
out=(archive if '--archive' in a else ROOT)/'Renders'/version;assert not out.exists()
md=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者\Exports')/version
if save:assert not md.exists() and not (ROOT/'Exports'/version).exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
if short_hook:
 lengths=np.array([c.points_length for c in cu.curves]);ends=np.cumsum(lengths)-1
 xyz=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',xyz.ravel())
 selected=selected[(xyz[ends[selected],2]>=1.800)&(xyz[ends[selected],1]>.030)]
 assert 0<len(selected)<=300
 for key in ['native_resculpted_fringe_sweeps','native_curved_projected_tips']:
  flags=np.empty(len(cu.curves),bool);cu.attributes[key].data.foreach_get('value',flags);assert not flags[selected].any()
accepted=np.empty(len(cu.curves),bool);cu.attributes['native_inner_curtain_shift'].data.foreach_get('value',accepted);assert not accepted[selected].any()
keep=np.ones(len(cu.curves),bool);keep[selected]=False;sizes=np.array([c.points_length for c in cu.curves]);pointkeep=np.repeat(keep,sizes)
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());r=np.empty(len(p),np.float32);cu.attributes['radius'].data.foreach_get('value',r)
new=bpy.data.hair_curves.new('Native hair with inspected stray arch removed');new.add_curves(sizes[keep].tolist());new.attributes['position'].data.foreach_set('vector',p[pointkeep].ravel());new.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',r[pointkeep]);new.materials.append(cu.materials[0])
for attr in cu.attributes:
 if attr.domain!='CURVE':continue
 field,width,dtype={'BOOLEAN':('value',1,bool),'INT':('value',1,np.int32),'FLOAT':('value',1,np.float32),'FLOAT_VECTOR':('vector',3,np.float32),'FLOAT2':('vector',2,np.float32),'FLOAT_COLOR':('color',4,np.float32)}[attr.data_type]
 values=np.empty((len(attr.data),width),dtype);attr.data.foreach_get(field,values.ravel());target=new.attributes.get(attr.name) or new.attributes.new(attr.name,attr.data_type,'CURVE');target.data.foreach_set(field,values[keep].ravel())
ob.data=new;modelhash=None
if save:
 md.mkdir(parents=True);bpy.ops.wm.save_as_mainfile(filepath=str(md/'Ember_Regent.blend'),compress=True);modelhash=hashlib.sha256((md/'Ember_Regent.blend').read_bytes()).hexdigest();np.savez_compressed(md/'local_retained_indices.npz',retained=np.flatnonzero(keep))
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE';s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
out.mkdir(parents=True);images={}
for shot in ([] if save_only else ['04_Back','03_Side','02_ThreeQuarter'] if short_hook else ['02_ThreeQuarter','01_Front']):
 s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=hashlib.sha256(dest.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
manifest=dict(source=base,source_sha256=digest,source_unchanged=True,model_saved=save,model_sha256=modelhash,archive_model_path=str(md/'Ember_Regent.blend') if save else None,selection=idsversion,removed_fibers=len(selected),retained_fibers=int(keep.sum()),images_sha256=images,method='Remove only small actual inspected projected stray set;all retained mixed-count positions,radii and historical CURVE attributes copied exactly. No accepted inner-curtain fibers removed. Source remains unchanged;topology count intentionally reduced. Requires art review,not continuous collision proof.')
if short_hook:manifest.update(short_hook_filter='Intersect projected set with tipZ>=1.800m and tipY>30mm. Accepted inner curtain/frontal sweeps/curved accent excluded. Preview only;preserve overall hairstyle ends in retained hair,remove this short upper hook layer only.')
(out/'stray_removal_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
if save:(md/'stray_removal_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('STRAY_REMOVAL',version,len(selected),flush=True)
