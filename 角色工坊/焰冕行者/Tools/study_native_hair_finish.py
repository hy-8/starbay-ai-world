"""Isolated native hair shader study; geometry and saved source untouched."""
import bpy,sys,json,re,hashlib
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:2]):raise ValueError(a)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh study required')
source=ROOT/'Exports'/base/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
old=bpy.data.objects['Bystedt layercut derivative • native root reflow'].data.materials[0]
mat=old.copy();mat.name='Deep garnet native hair • pigment finish study'
nt=mat.node_tree;nt.nodes.clear()
info=nt.nodes.new('ShaderNodeHairInfo');ramp=nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color=(.027,.0038,.0058,1)
ramp.color_ramp.elements[1].color=(.115,.017,.023,1)
hair=nt.nodes.new('ShaderNodeBsdfHairPrincipled');hair.parametrization='COLOR'
hair.inputs['Roughness'].default_value=.235
hair.inputs['Radial Roughness'].default_value=.30
hair.inputs['Random Roughness'].default_value=.08
output=nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(info.outputs['Random'],ramp.inputs['Fac'])
nt.links.new(ramp.outputs['Color'],hair.inputs['Color'])
nt.links.new(hair.outputs['BSDF'],output.inputs['Surface'])
objects=[]
for ob in bpy.data.objects:
 if ob.type=='CURVES' and not ob.hide_render:
  for slot in ob.material_slots:
   if slot.material==old:slot.material=mat
  objects.append(ob.name)
s=bpy.context.scene;p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
for d in p.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
out.mkdir(parents=True);render.mkdir(parents=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
camera=bpy.data.objects['03_Side'].copy();camera.data=camera.data.copy();s.collection.objects.link(camera);camera.name='05_OppositeSide'
reflect=Matrix.Diagonal((-1.,1.,1.,1.));camera.matrix_world=reflect@camera.matrix_world@reflect
for name in ['02_ThreeQuarter','05_OppositeSide']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
(out/'finish_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),geometry_edit=False,visible_native_objects=objects,shader='Principled Hair COLOR, random per-strand garnet ramp, roughness .235/radial .30/random .08',status='Unreviewed actual paired shader study; not artistic acceptance'),indent=2),encoding='utf-8')
print('HAIR_FINISH_STUDY_SAVED',version,flush=True)
