"""Equal temporary rear key on two saved models, without source mutation."""
import bpy, sys, re, json, hashlib, shutil
from pathlib import Path
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--')+1:]
version, source_version, candidate_version = a[:3]
energy = float(a[a.index('--energy')+1]) if '--energy' in a else 100.
reuse_source = a[a.index('--reuse-source')+1] if '--reuse-source' in a else None
if reuse_source:assert re.fullmatch('[A-Za-z0-9_-]+',reuse_source)
assert 0 < energy <= 1000
assert all(re.fullmatch('[A-Za-z0-9_-]+', v) for v in a[:3])
out = ROOT/'Renders'/version
assert not out.exists()
out.mkdir(parents=True)
records = []
for label, model in [('source', source_version), ('candidate', candidate_version)]:
    path = ROOT/'Exports'/model/'Ember_Regent.blend'
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path), use_scripts=False)
    scene = bpy.context.scene
    data = bpy.data.lights.new('Temporary rear shape inspection key', 'AREA')
    data.energy = energy
    data.shape = 'DISK'
    data.size = .45
    data.color = (1., .93, .90)
    lamp = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(lamp)
    lamp.location = (-.40, .60, 2.15)
    direction = Vector((0., .03, 1.800))-lamp.location
    lamp.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    pref = bpy.context.preferences.addons['cycles'].preferences
    pref.compute_device_type = 'OPTIX'
    pref.get_devices()
    for d in pref.devices: d.use = d.type == 'OPTIX'
    scene.cycles.device = 'GPU'
    scene.cycles.samples = 256
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.render.resolution_x, scene.render.resolution_y = 1200, 1400
    scene.render.resolution_percentage = 100
    scene.camera = bpy.data.objects['04_Back']
    image = out/(label+'_04_Back.png')
    scene.render.filepath = str(image)
    if label=='source' and reuse_source:
        prior_folder=ROOT/'Renders'/reuse_source
        prior=json.loads((prior_folder/'rear_lighting_manifest.json').read_text(encoding='utf-8'))
        prior_row=prior['records'][0]
        expected_key=dict(energy_w=energy,disk_size_m=.45,color=[1.,.93,.90],location_m=[-.40,.60,2.15],target_m=[0.,.03,1.800])
        assert prior['added_temporary_key']==expected_key and prior['samples']==256 and prior['resolution']==[1200,1400] and prior['denoising']=='OpenImageDenoise'
        assert prior_row['model']==model and prior_row['source_sha256']==digest and prior_row['source_unchanged']
        previous=prior_folder/prior_row['image']
        assert hashlib.sha256(previous.read_bytes()).hexdigest()==prior_row['image_sha256']
        shutil.copyfile(previous,image)
    else:bpy.ops.render.render(write_still=True)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    records.append(dict(model=model, source_sha256=digest, source_unchanged=True,
                        image=image.name, image_sha256=hashlib.sha256(image.read_bytes()).hexdigest()))
(out/'rear_lighting_manifest.json').write_text(json.dumps(dict(
    records=records, reused_source_from=reuse_source, original_geometry_materials_lights_retained=True,
    added_temporary_key=dict(energy_w=energy, disk_size_m=.45, color=[1.,.93,.90],
                             location_m=[-.40,.60,2.15], target_m=[0.,.03,1.800]),
    samples=256, denoising='OpenImageDenoise', resolution=[1200,1400],
    scope='Equal temporary additional rear key on both source/candidate actual Blender geometry. No source saves, image substitution or lighting-only aesthetic completion claim.',
    status='Actual pair pending visual review'), indent=2), encoding='utf-8')
print('NATIVE_REAR_LIGHTING_PAIR_RENDERED', version, flush=True)
