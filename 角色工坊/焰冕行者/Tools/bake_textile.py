"""Bake Blender's textile bump and metal mask into portable PBR maps using Cycles."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'Materials'
if not bpy.app.background:raise RuntimeError('Background only; keeps interactive scene safe.')
for name in ['Ember_Brocade_ORM.png','Ember_Brocade_Normal.png']:
    if (DEST/name).exists():raise RuntimeError('Existing texture protected: '+name)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_plane_add(size=2)
obj=bpy.context.object;mat=bpy.data.materials.new('Bake textile');mat.use_nodes=True;obj.data.materials.append(mat)
nt=mat.node_tree;nt.nodes.clear();output=nt.nodes.new('ShaderNodeOutputMaterial')
image=nt.nodes.new('ShaderNodeTexImage');image.image=bpy.data.images.load(str(DEST/'Ember_Brocade_Albedo.png'))
sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(image.outputs['Color'],sep.inputs[0])
mask=nt.nodes.new('ShaderNodeMapRange');mask.inputs['From Min'].default_value=.035;mask.inputs['From Max'].default_value=.30;mask.inputs['To Min'].default_value=.02;mask.inputs['To Max'].default_value=.70
nt.links.new(sep.outputs['Green'],mask.inputs['Value'])
rgb=nt.nodes.new('ShaderNodeCombineColor');rgb.inputs['Red'].default_value=1;rgb.inputs['Green'].default_value=.49;nt.links.new(mask.outputs[0],rgb.inputs['Blue'])
em=nt.nodes.new('ShaderNodeEmission');nt.links.new(rgb.outputs[0],em.inputs[0]);nt.links.new(em.outputs[0],output.inputs[0])
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.bake.margin=4
try:
    p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
    for d in p.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:pass
for suffix,bake_type in [('ORM','EMIT'),('Normal','NORMAL')]:
    target=bpy.data.images.new('Ember_Brocade_'+suffix,1024,1024,alpha=False);target.colorspace_settings.name='Non-Color'
    node=nt.nodes.new('ShaderNodeTexImage');node.image=target;nt.nodes.active=node
    if bake_type=='NORMAL':
        shader=nt.nodes.new('ShaderNodeBsdfPrincipled');bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.24;bump.inputs['Distance'].default_value=.0014
        nt.links.new(sep.outputs['Green'],bump.inputs['Height']);nt.links.new(bump.outputs[0],shader.inputs['Normal']);nt.links.new(shader.outputs[0],output.inputs[0])
    bpy.ops.object.bake(type=bake_type)
    target.filepath_raw=str(DEST/('Ember_Brocade_'+suffix+'.png'));target.file_format='PNG';target.save()
print('BAKED_TEXTILE_PBR_MAPS')
