"""Isolated primary-hair pigment gradient on saved real geometry."""
import bpy,sys,re,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=ROOT/'Exports'/version;rd=ROOT/'Renders'/version;assert not out.exists() and not rd.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow']
assert len(ob.data.materials)==1
old=ob.data.materials[0];mat=old.copy();mat.name='Garnet hair • gradual natural root depth'
nt=mat.node_tree;hair=next(n for n in nt.nodes if n.bl_idname=='ShaderNodeBsdfHairPrincipled')
info=next(n for n in nt.nodes if n.bl_idname=='ShaderNodeHairInfo')
link=next(l for l in nt.links if l.to_node==hair and l.to_socket==hair.inputs['Color'])
color_output=link.from_socket
root=nt.nodes.new('ShaderNodeValToRGB');root.name='Root to dyed length'
root.color_ramp.interpolation='EASE'
root.color_ramp.elements[0].position=0;root.color_ramp.elements[0].color=(.42,.42,.42,1)
root.color_ramp.elements[1].position=.62;root.color_ramp.elements[1].color=(1,1,1,1)
e=root.color_ramp.elements.new(.23);e.color=(.65,.65,.65,1)
mix=nt.nodes.new('ShaderNodeMixRGB');mix.name='Pigment depth along each real fiber';mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
nt.links.new(info.outputs['Intercept'],root.inputs['Fac'])
nt.links.new(color_output,mix.inputs[1]);nt.links.new(root.outputs['Color'],mix.inputs[2]);nt.links.new(mix.outputs['Color'],hair.inputs['Color'])
ob.data.materials[0]=mat
out.mkdir(parents=True);rd.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=128;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
(out/'root_pigment_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,edited_object=ob.name,geometry_edit=False,old_material=old.name,new_material=mat.name,method='Existing strand-random COLOR and Huang scattering preserved; multiply pigment by per-fiber Intercept EASE ramp0:.42,.23:.65,.62:1. Other visible hair, lights and geometry unchanged. Not a geometry fix.',status='True material-only two-view study awaiting visual review'),indent=2),encoding='utf-8')
for shot in ['02_ThreeQuarter','01_Front']:
    s.camera=bpy.data.objects[shot];s.render.filepath=str(rd/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
print('ROOT_PIGMENT_RENDERED',version,flush=True)
