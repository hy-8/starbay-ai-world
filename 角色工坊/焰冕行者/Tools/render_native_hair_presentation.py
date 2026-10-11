"""High-sample actual Cycles render, no geometry/lighting substitution."""
import bpy,sys,re,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
camera=a[a.index('--camera')+1] if '--camera' in a else '02_ThreeQuarter'
if camera not in ['01_Front','02_ThreeQuarter','03_Side','04_Back','05_OppositeSide']:raise ValueError(camera)
draft='--draft' in a
raw='--no-denoise' in a
if not all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:2]):raise ValueError(a)
out=ROOT/'Renders'/version
if out.exists():raise RuntimeError('Fresh presentation required')
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=192 if draft else 512;s.cycles.use_denoising=not raw;s.cycles.denoiser='OPENIMAGEDENOISE'
s.render.resolution_x,s.render.resolution_y=(1200,1400) if draft else (1920,2240);s.render.resolution_percentage=100
if camera=='05_OppositeSide':
 from mathutils import Matrix
 cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name=camera
 ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
s.camera=bpy.data.objects[camera];out.mkdir(parents=True)
render_file=out/(camera+'.png')
s.render.filepath=str(render_file);bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'presentation_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,source_unchanged=True,camera=camera,diagnostic_opposite_camera=camera=='05_OppositeSide',geometry_lighting_unchanged=True,resolution=[s.render.resolution_x,s.render.resolution_y],samples=s.cycles.samples,denoising='None' if raw else 'OpenImageDenoise',image_sha256=hashlib.sha256(render_file.read_bytes()).hexdigest(),status='Actual render pending art review; no generative image replacement'),indent=2),encoding='utf-8')
print('NATIVE_PRESENTATION_RENDERED',version,flush=True)
