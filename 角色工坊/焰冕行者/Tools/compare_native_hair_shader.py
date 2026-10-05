"""Material-only directional lobe control; exact saved groom geometry retained."""
import bpy,sys,re,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version=a[0]
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh control only')
source=ROOT/'Exports/nativeroot03/Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
mat=bpy.data.materials.new('Original red directional reflection-transmission control');mat.use_nodes=True
nt=mat.node_tree;nt.nodes.clear();info=nt.nodes.new('ShaderNodeHairInfo');ramp=nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color=(.045,.0025,.006,1);ramp.color_ramp.elements[1].color=(.16,.012,.023,1)
nt.links.new(info.outputs['Random'],ramp.inputs[0])
reflection=nt.nodes.new('ShaderNodeBsdfHair');reflection.component='Reflection'
transmission=nt.nodes.new('ShaderNodeBsdfHair');transmission.component='Transmission'
for bs in [reflection,transmission]:
 for key,value in [('RoughnessU',.28),('RoughnessV',.38)]:
  sock=bs.inputs.get(key)
  if sock is None:raise RuntimeError('Inspect hair shader sockets: '+str(bs.inputs.keys()))
  sock.default_value=value
nt.links.new(ramp.outputs[0],reflection.inputs['Color'])
transmission.inputs['Color'].default_value=(.055,.003,.008,1)
mix=nt.nodes.new('ShaderNodeMixShader');mix.inputs[0].default_value=.40
nt.links.new(reflection.outputs[0],mix.inputs[1]);nt.links.new(transmission.outputs[0],mix.inputs[2])
output=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(mix.outputs[0],output.inputs[0])
if '--mixed' in a:
 # Recreate the saved donor material's documented simple Principled branch.
 # Keep its actual colors/roughness, compare only a restrained 25% lobe mix.
 saved=next(o for o in bpy.data.objects if o.type=='CURVES' and not o.hide_render).data.materials[0]
 oldbs=next(n for n in saved.node_tree.nodes if n.type=='BSDF_HAIR_PRINCIPLED')
 oldramp=next(n for n in saved.node_tree.nodes if n.type=='VALTORGB')
 physical=nt.nodes.new('ShaderNodeBsdfHairPrincipled');physical.parametrization=oldbs.parametrization
 for key in ['Roughness','Radial Roughness']:
  physical.inputs[key].default_value=oldbs.inputs[key].default_value
 cr=nt.nodes.new('ShaderNodeValToRGB')
 for dst,src in zip(cr.color_ramp.elements,oldramp.color_ramp.elements):dst.position=src.position;dst.color=src.color
 nt.links.new(info.outputs['Random'],cr.inputs[0]);nt.links.new(cr.outputs[0],physical.inputs['Color'])
 blend=nt.nodes.new('ShaderNodeMixShader');blend.inputs[0].default_value=.25
 nt.links.new(physical.outputs[0],blend.inputs[1]);nt.links.new(mix.outputs[0],blend.inputs[2]);nt.links.new(blend.outputs[0],output.inputs[0])
names=[]
for ob in bpy.data.objects:
 if ob.type=='CURVES' and not ob.hide_render:
  ob.data=ob.data.copy();ob.data.materials.clear();ob.data.materials.append(mat);names.append(ob.name)
out.mkdir(parents=True);render.mkdir(parents=True)
(out/'shader_control_manifest.json').write_text(json.dumps(dict(source='nativeroot03',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
 components=names,mixed_with_saved_principled='--mixed' in a,method='Material only; native Hair BSDF reflection/transmission lobes with unlinked default tangent input, optionally 25% blended with recreated saved Principled branch; all geometry preserved',
 status='Unreviewed actual material comparison',artistic_goal_completed=False),indent=2),encoding='utf-8')
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
s.camera=bpy.data.objects['02_ThreeQuarter'];s.render.filepath=str(render/'02_ThreeQuarter.png');bpy.ops.render.render(write_still=True)
print('NATIVE_SHADER_CONTROL_SAVED',version,flush=True)
