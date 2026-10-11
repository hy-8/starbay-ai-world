"""Read-only posterior coverage diagnostic; never saves its hidden layer."""
import bpy,sys,re,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';out=ROOT/'Renders'/version
assert not out.exists();digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Original posterior coverage • surface-grown short fibers'];assert not ob.hide_render
ob.hide_render=True
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=128;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
out.mkdir(parents=True);images={}
for shot in ['04_Back','03_Side']:
    s.camera=bpy.data.objects[shot];path=out/(shot+'.png');s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    images[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'coverage_diagnostic.json').write_text(json.dumps(dict(source=base,source_sha256=digest,source_unchanged=True,hidden_object=ob.name,images_sha256=images,samples=128,denoising='OpenImageDenoise',scope='Read-only diagnostic; existing posterior support hidden temporarily. Not adopted geometry.'),indent=2),encoding='utf-8')
print('COVER_DIAGNOSTIC_RENDERED',version,flush=True)
