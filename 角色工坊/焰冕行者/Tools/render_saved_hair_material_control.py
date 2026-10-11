"""Read-only saved donor material control on the exact current groom."""
import bpy,sys,re,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2];all_hair='--all-hair' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';donor=ROOT/'Exports/layercut04/Ember_Regent.blend'
digest=hashlib.sha256(source.read_bytes()).hexdigest();dh=hashlib.sha256(donor.read_bytes()).hexdigest()
out=ROOT/'Renders'/version;assert not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
with bpy.data.libraries.load(str(donor),link=False) as (src,dst):dst.materials=['Deep cherry layer cut']
mat=dst.materials[0];assert mat
changed=[]
for ob in bpy.data.objects:
    if ob.type=='CURVES' and not ob.hide_render and (all_hair or ob.name=='Bystedt layercut derivative • native root reflow'):
        ob.data=ob.data.copy();ob.data.materials.clear();ob.data.materials.append(mat);changed.append(ob.name)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
out.mkdir(parents=True);images={}
for shot in ['02_ThreeQuarter','03_Side']:
    s.camera=bpy.data.objects[shot];path=out/(shot+'.png');s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    images[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest and hashlib.sha256(donor.read_bytes()).hexdigest()==dh
(out/'saved_material_control.json').write_text(json.dumps(dict(source=base,source_sha256=digest,source_unchanged=True,donor='layercut04',donor_sha256=dh,changed_objects=changed,all_hair=all_hair,images_sha256=images,samples=256,resolution=[1200,1400],denoising='OpenImageDenoise',method='Temporarily assign exact saved Deep cherry layer cut donor material to current groom. No geometry/light edits or model save.'),indent=2),encoding='utf-8')
print('SAVED_MATERIAL_CONTROL_RENDERED',version,flush=True)
