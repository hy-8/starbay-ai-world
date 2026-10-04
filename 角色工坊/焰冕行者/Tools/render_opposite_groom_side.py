"""Render the actual opposite profile camera without editing model geometry.

Counterpart to existing neutral left/front/back checks, never an image flip.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version,source_version=args[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in args[:2]):raise ValueError(args)
out=ROOT/'Renders'/version
if out.exists():raise RuntimeError('Fresh check output required')
source=ROOT/'Exports'/source_version/'Ember_Regent.blend';before=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
original=bpy.data.objects['03_Side'];camera=original.copy();camera.data=original.data.copy()
bpy.context.scene.collection.objects.link(camera);camera.name='05_OppositeSide'
reflect=Matrix.Diagonal((-1.,1.,1.,1.))
camera.matrix_world=reflect@original.matrix_world@reflect
if camera.matrix_world.to_3x3().determinant()<=0:raise RuntimeError('Camera must retain proper handedness')
scene=bpy.context.scene;scene.camera=camera
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=192;scene.cycles.use_denoising=False
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
out.mkdir(parents=True);image=out/'05_OppositeSide.png';scene.render.filepath=str(image)
bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
report=dict(version=version,source=source_version,source_sha256=before,source_unchanged=True,method='Actual camera mirrored in world space with local-X handedness correction; no pixel flip or geometry edit',samples=192,resolution=[1200,1400],denoising=False,image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),status='Unreviewed actual opposite profile diagnostic, not artistic approval')
(out/'opposite_side_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('OPPOSITE_GROOM_SIDE_RENDERED',version,flush=True)
