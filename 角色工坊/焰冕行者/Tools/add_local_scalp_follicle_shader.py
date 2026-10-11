"""Localized procedural scalp backing beneath actual fibers; preserves all geometry."""
import bpy,sys,re,json,hashlib
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2];save='--save' in a
save_only='--save-only' in a
assert not save_only or save
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=ROOT/'Renders'/version;md=ROOT/'Exports'/version;assert not out.exists() and not md.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
body=bpy.data.objects['CC0 male body • retained topology'];changes=[]
for index,slot in enumerate(body.material_slots):
 old=slot.material
 if old is None:continue
 mat=old.copy();mat.name=old.name+' • localized follicle backing';slot.material=mat
 nt=mat.node_tree;output=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
 original=next(l.from_socket for l in nt.links if l.to_node==output and l.to_socket==output.inputs['Surface'])
 def node(kind,name):
  n=nt.nodes.new(kind);n.name=name;n.label=name;return n
 def math(op,x,y=None,name='Follicle mask'):
  n=node('ShaderNodeMath',name);n.operation=op
  for i,value in enumerate([x,y]):
   if value is None:continue
   if isinstance(value,(float,int)):n.inputs[i].default_value=value
   else:nt.links.new(value,n.inputs[i])
  return n.outputs[0]
 coord=node('ShaderNodeTexCoord','Head-local follicle coordinates');coord.object=body
 sep=node('ShaderNodeSeparateXYZ','Head coordinates in meters');nt.links.new(coord.outputs['Object'],sep.inputs[0])
 y=math('DIVIDE',math('ADD',sep.outputs['Y'],.078),.043)
 z=math('DIVIDE',math('SUBTRACT',sep.outputs['Z'],1.846),.052)
 ellipse=math('ADD',math('MULTIPLY',y,y),math('MULTIPLY',z,z))
 edge=math('MAXIMUM',math('SUBTRACT',1.0,ellipse),0.0)
 edge=math('MINIMUM',math('MULTIPLY',edge,2.5),1.0)
 # Smooth falloff; no paint on face center or low sideburn/ear skin.
 fade=math('MULTIPLY',math('MULTIPLY',edge,edge),math('SUBTRACT',3.0,math('MULTIPLY',edge,2.0)))
 lateral=math('MINIMUM',math('MAXIMUM',math('DIVIDE',math('SUBTRACT',math('ABSOLUTE',sep.outputs['X']),.019),.023),0.0),1.0)
 spatial=math('MULTIPLY',fade,lateral)
 noise=node('ShaderNodeTexNoise','Submillimeter follicle variation');noise.inputs['Scale'].default_value=3000;noise.inputs['Detail'].default_value=2
 nt.links.new(coord.outputs['Object'],noise.inputs['Vector'])
 density=node('ShaderNodeValToRGB','Feathered follicle coverage');density.color_ramp.elements[0].position=.25;density.color_ramp.elements[0].color=(.65,.65,.65,1)
 density.color_ramp.elements[1].position=.70;density.color_ramp.elements[1].color=(1,1,1,1);nt.links.new(noise.outputs['Fac'],density.inputs[0])
 strength=math('MULTIPLY',math('MULTIPLY',spatial,density.outputs['Color']),.95)
 bs=node('ShaderNodeBsdfPrincipled','Short root follicle backing');bs.inputs['Base Color'].default_value=(.012,.003,.004,1);bs.inputs['Roughness'].default_value=.65
 bump=node('ShaderNodeBump','Minute follicle relief');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.00008
 nt.links.new(noise.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
 mix=node('ShaderNodeMixShader','Skin and localized follicle backing');nt.links.new(strength,mix.inputs[0]);nt.links.new(original,mix.inputs[1]);nt.links.new(bs.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],output.inputs['Surface'])
 changes.append(dict(slot=index,source_material=old.name,new_material=mat.name))
md.mkdir(parents=True);out.mkdir(parents=True);modelhash=None
if save:
 bpy.ops.wm.save_as_mainfile(filepath=str(md/'Ember_Regent.blend'),compress=True);modelhash=hashlib.sha256((md/'Ember_Regent.blend').read_bytes()).hexdigest()
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE';s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
images={}
for shot in ([] if save_only else ['03_Side','02_ThreeQuarter','05_OppositeSide']):
 s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=hashlib.sha256(dest.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(md/'follicle_shader_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,model_saved=save,model_sha256=modelhash,geometry_edit=False,edited_object=body.name,material_changes=changes,images_sha256=images,method='Procedural head-local scalp follicle backing blended into copied body surface shaders only. EllipseYZ center(-.078,1.846)m,radii(.043,.052)m; lateral smooth threshold|X|19-42mm. Mask smoothstep,submillimeter noise and80um bump. Maximum effective blend95percent; outside ellipse/central face exactly original surface. All real hair geometry/materials and scene lighting retained. Not new fiber geometry, not a portrait replacement; static shader preview needs visual acceptance.'),indent=2),encoding='utf-8');print('FOLLICLE_BACKING_RENDERED',version,flush=True)
