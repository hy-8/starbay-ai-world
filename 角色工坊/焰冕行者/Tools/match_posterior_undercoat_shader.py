"""Compare posterior support using the existing primary crimson shader.

Geometry stays exactly the same. This is a material isolation, not a haircut.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
out,renders=ROOT/'Exports'/version,ROOT/'Renders'/version
assert not out.exists() and not renders.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend'
digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
primary=bpy.data.objects['Bystedt layercut derivative • native root reflow']
target=bpy.data.objects['Original posterior coverage • surface-grown short fibers']
old_materials=[m.name for m in target.data.materials]
assert len(primary.data.materials)==1
target.data=target.data.copy()
target.data.materials.clear();target.data.materials.append(primary.data.materials[0])
out.mkdir(parents=True);renders.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';pref.get_devices()
for device in pref.devices:device.use=device.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
reflect=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=reflect@cam.matrix_world@reflect
for name in ['02_ThreeQuarter','03_Side','05_OppositeSide','04_Back']:
    s.camera=bpy.data.objects[name];s.render.filepath=str(renders/(name+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'undercoat_match_manifest.json').write_text(json.dumps(dict(
    source=base,source_sha256=digest,changed_component=target.name,source_materials=old_materials,
    target_material=primary.data.materials[0].name,geometry_edit=False,
    method='Only the original posterior support material slot is assigned the existing103 pure-Huang primary shader. No new shader parameters, geometry, color-grading or lights. Other supports/primary/mesh material slots retained.',
    status='Actual draft awaits art review; shader matching does not fix flat geometry'),indent=2),encoding='utf-8')
print('POSTERIOR_SHADER_MATCH',version,flush=True)
