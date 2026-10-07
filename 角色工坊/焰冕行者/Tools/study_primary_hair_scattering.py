"""Primary-only pure Huang comparison with explicitly recalibrated red pigment."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version;assert not out.exists() and not render.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow']
visible=sorted([o for o in bpy.data.objects if o.type=='CURVES' and not o.hide_render],key=lambda o:o.name)
def geometry():
 h=hashlib.sha256()
 for o in visible:
  p=np.empty((len(o.data.points),3),np.float32);o.data.attributes['position'].data.foreach_get('vector',p.ravel())
  r=np.empty(len(o.data.points),np.float32);o.data.attributes['radius'].data.foreach_get('value',r)
  h.update(o.name.encode());h.update(p.tobytes());h.update(r.tobytes());h.update(np.array(o.matrix_world).tobytes());h.update(np.array([c.points_length for c in o.data.curves]).tobytes())
 return h.hexdigest()
before=geometry();support_slots={o.name:[s.material for s in o.material_slots] for o in visible if o!=ob}
old=ob.data.materials[0];mat=bpy.data.materials.new('Primary scarlet • pure Huang control');mat.use_nodes=True
nt=mat.node_tree;nt.nodes.clear();info=nt.nodes.new('ShaderNodeHairInfo');ramp=nt.nodes.new('ShaderNodeValToRGB')
colors=[(.11,.005,.007,1),(.25,.013,.015,1)]
for e,c in zip(ramp.color_ramp.elements,colors):e.color=c
hair=nt.nodes.new('ShaderNodeBsdfHairPrincipled');hair.model='HUANG';hair.parametrization='COLOR'
values={'Roughness':.32,'Random Roughness':.12,'IOR':1.55,'Reflection':.55,'Transmission':1.0,'Secondary Reflection':.85}
for k,v in values.items():hair.inputs[k].default_value=v
nt.links.new(info.outputs['Random'],ramp.inputs[0]);nt.links.new(ramp.outputs[0],hair.inputs['Color'])
output=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(hair.outputs[0],output.inputs['Surface'])
ob.data=ob.data.copy();ob.data.materials.clear();ob.data.materials.append(mat)
assert geometry()==before and support_slots=={o.name:[s.material for s in o.material_slots] for o in visible if o!=ob}
out.mkdir(parents=True);render.mkdir(parents=True);s=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for name in ['02_ThreeQuarter','05_OppositeSide','01_Front']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'primary_scattering_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,changed_object=ob.name,source_material=old.name,new_material=mat.name,colors_linear_rgba=colors,model='HUANG',parametrization='COLOR',inputs=values,geometry_before_sha256=before,geometry_after_sha256=geometry(),support_material_slots_exact=True,method='Primary only: pure Huang replaces legacy75%Chiang/25%directional mix; explicitly new red pigment and controlled reflection weights. No assumption of model-switch absorption equivalence. Existing geometry, support materials and lighting retained.',status='Actual drafts pending review; material study, not geometry repair or target acceptance'),indent=2),encoding='utf-8')
print('PRIMARY_SCATTERING_SAVED',version,flush=True)
