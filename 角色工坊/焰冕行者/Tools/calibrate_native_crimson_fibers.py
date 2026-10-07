"""Material-only crimson calibration on the actual native groom."""
import bpy,sys,re,json,hashlib
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
balanced='--balanced' in a
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2]):raise ValueError(a)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh material study required')
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
old=bpy.data.objects['Bystedt layercut derivative • native root reflow'].data.materials[0]
before=[]
for n in old.node_tree.nodes:
 if n.type=='BSDF_HAIR_PRINCIPLED':before.append(dict(name=n.name,model=n.model,parametrization=n.parametrization,roughness=n.inputs['Roughness'].default_value,radial_roughness=n.inputs['Radial Roughness'].default_value))
 elif n.type=='VALTORGB':before.append(dict(name=n.name,colors=[list(e.color) for e in n.color_ramp.elements]))
mat=bpy.data.materials.new('Crimson optical fiber • Chiang calibrated');mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear()
info=nt.nodes.new('ShaderNodeHairInfo');ramp=nt.nodes.new('ShaderNodeValToRGB')
colors=[(.055,.0035,.006,1),(.125,.011,.019,1)] if balanced else [(.28,.022,.040,1),(.45,.055,.070,1)]
for e,c in zip(ramp.color_ramp.elements,colors):e.color=c
nt.links.new(info.outputs['Random'],ramp.inputs[0]);hair=nt.nodes.new('ShaderNodeBsdfHairPrincipled');hair.model='CHIANG';hair.parametrization='COLOR'
roughness=.35 if balanced else .32;radial=.35 if balanced else .50
hair.inputs['Roughness'].default_value=roughness;hair.inputs['Radial Roughness'].default_value=radial;hair.inputs['IOR'].default_value=1.55
nt.links.new(ramp.outputs[0],hair.inputs['Color']);output=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(hair.outputs[0],output.inputs['Surface'])
components=[]
for ob in bpy.data.objects:
 if ob.type=='CURVES' and not ob.hide_render:
  ob.data=ob.data.copy();ob.data.materials.clear();ob.data.materials.append(mat);components.append(ob.name)
out.mkdir(parents=True);render.mkdir(parents=True);s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False;s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for name in ['02_ThreeQuarter','05_OppositeSide']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'crimson_calibration_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,geometry_and_lighting_unchanged=True,before_nodes=before,components=components,model='CHIANG',parametrization='COLOR',balanced=balanced,colors_linear_rgba=colors,roughness=roughness,radial_roughness=radial,ior=1.55,method='Replace legacy25% directional mix with pure native Chiang; explicitly recalibrate pigment rather than assume model-switch absorption equivalence',status='Actual drafts pending review; no geometry repair or target acceptance'),indent=2),encoding='utf-8');print('CRIMSON_CALIBRATION_SAVED',version,flush=True)
