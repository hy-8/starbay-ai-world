"""Render the actual opposite profile camera without editing model geometry.

Counterpart to existing neutral left/front/back checks, never an image flip.
"""
import bpy,sys,re,json,hashlib,shutil
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version,source_version=args[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in args[:2]):raise ValueError(args)
out=ROOT/'Renders'/version
if out.exists():raise RuntimeError('Fresh check output required')
source=ROOT/'Exports'/source_version/'Ember_Regent.blend';before=hashlib.sha256(source.read_bytes()).hexdigest()
reuse_opposite=args[args.index('--reuse-opposite')+1] if '--reuse-opposite' in args else None
single_camera=args[args.index('--camera')+1] if '--camera' in args else None
if single_camera and (single_camera not in ['01_Front','02_ThreeQuarter','03_Side','04_Back','05_OppositeSide'] or '--five-views' in args or reuse_opposite):raise ValueError('Choose one valid camera or the existing five-view mode')
if reuse_opposite:
 if '--five-views' not in args or not re.fullmatch('[A-Za-z0-9_-]+',reuse_opposite):raise ValueError('Reuse requires five views and valid diagnostic version')
 prior_folder=ROOT/'Renders'/reuse_opposite
 prior=json.loads((prior_folder/'opposite_side_manifest.json').read_text(encoding='utf-8'))
 prior_image=prior_folder/'05_OppositeSide.png'
 if not (prior['source_sha256']==before and prior['source_unchanged'] and prior['samples']==192 and prior['resolution']==[1200,1400] and not prior['denoising'] and hashlib.sha256(prior_image.read_bytes()).hexdigest()==prior['image_sha256']):
  raise RuntimeError('Opposite image must match exact saved source and render settings')
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
out.mkdir(parents=True)
shots=[single_camera] if single_camera else ['01_Front','02_ThreeQuarter','03_Side','04_Back','05_OppositeSide'] if '--five-views' in args else ['05_OppositeSide']
images={}
for name in shots:
 scene.camera=bpy.data.objects[name]
 image=out/(name+'.png');scene.render.filepath=str(image)
 if name=='05_OppositeSide' and reuse_opposite:shutil.copyfile(prior_image,image)
 else:bpy.ops.render.render(write_still=True)
 images[name+'.png']=hashlib.sha256(image.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
report=dict(version=version,source=source_version,source_sha256=before,source_unchanged=True,method='Existing neutral camera'+(' '+single_camera if single_camera else 's when requested, plus actual opposite camera mirrored in world space with local-X handedness correction')+'; no pixel flip or geometry edit',samples=192,resolution=[1200,1400],denoising=False,image_sha256=images.get('05_OppositeSide.png',next(iter(images.values()))),images_sha256=images,status='Unreviewed actual neutral/opposite profile diagnostic, not artistic approval')
report['single_camera']=single_camera
report['opposite_image_reused_from']=reuse_opposite
(out/'opposite_side_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('OPPOSITE_GROOM_SIDE_RENDERED',version,flush=True)
