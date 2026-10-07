"""Paired physical hair model study; exact old pigment/geometry/lights retained."""
import bpy,sys,json,re,hashlib
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
physical_control='--physical-control' in a
if not all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:2]):raise ValueError(a)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh shader model study')
source=ROOT/'Exports'/base/'Ember_Regent.blend';bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
old=bpy.data.objects['Bystedt layercut derivative • native root reflow'].data.materials[0]
mat=old.copy();mat.name='Native red pigment • Huang reflection control'
node=mat.node_tree.nodes['Principled Hair BSDF'];assert node.type=='BSDF_HAIR_PRINCIPLED' and node.model=='CHIANG' and node.parametrization=='COLOR'
node.model='HUANG';node.inputs['Reflection'].default_value=1.0 if physical_control else .45;node.inputs['Transmission'].default_value=1.0;node.inputs['Secondary Reflection'].default_value=1.0 if physical_control else .80
for ob in bpy.data.objects:
 if ob.type=='CURVES' and not ob.hide_render:
  for slot in ob.material_slots:
   if slot.material==old:slot.material=mat
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
out.mkdir(parents=True);render.mkdir(parents=True);bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
camera=bpy.data.objects['03_Side'].copy();camera.data=camera.data.copy();s.collection.objects.link(camera);camera.name='05_OppositeSide'
r=Matrix.Diagonal((-1.,1.,1.,1.));camera.matrix_world=r@camera.matrix_world@r
for name in ['02_ThreeQuarter','05_OppositeSide']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
(out/'huang_reflection_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),geometry_lighting_and_color_inputs_unchanged=True,effective_absorption_equivalence_not_asserted=True,physical_model='HUANG',physical_control=physical_control,reflection=1.0 if physical_control else .45,transmission=1.0,secondary_reflection=1.0 if physical_control else .80,legacy_directional_mix_retained=.25,status='Unreviewed actual shader-model study'),indent=2),encoding='utf-8')
print('NATIVE_HUANG_STUDY_SAVED',version,flush=True)
