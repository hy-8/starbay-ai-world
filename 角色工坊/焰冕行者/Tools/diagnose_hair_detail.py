"""Same-sample noisy/denoised crop; unchanged saved native geometry."""
import bpy, json, hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者\Renders\nativedetail315')
assert not OUT.exists()
source=ROOT/'Exports/nativegentlefan309/Ember_Regent.blend'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=digest(source)
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
s=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=1024;s.cycles.use_adaptive_sampling=False;s.cycles.use_denoising=False
s.view_layers[0].cycles.denoising_store_passes=True
s.render.resolution_x=1920;s.render.resolution_y=2240;s.render.resolution_percentage=100
s.camera=bpy.data.objects['04_Back']
s.render.use_border=True;s.render.use_crop_to_border=True
s.render.border_min_x=.42;s.render.border_max_x=.64
s.render.border_min_y=.40;s.render.border_max_y=.68
s.use_nodes=True;nt=s.node_tree;nt.nodes.clear()
rl=nt.nodes.new('CompositorNodeRLayers')
dn=nt.nodes.new('CompositorNodeDenoise');dn.use_hdr=True
nt.links.new(rl.outputs['Image'],dn.inputs['Image'])
nt.links.new(rl.outputs['Denoising Normal'],dn.inputs['Normal'])
nt.links.new(rl.outputs['Denoising Albedo'],dn.inputs['Albedo'])
OUT.mkdir(parents=True)
for name,socket in [('noisy',rl.outputs['Image']),('denoised',dn.outputs['Image'])]:
 node=nt.nodes.new('CompositorNodeOutputFile');node.base_path=str(OUT);node.file_slots[0].path=name+'_';node.format.file_format='PNG';node.format.color_mode='RGB';node.format.color_depth='8';nt.links.new(socket,node.inputs[0])
comp=nt.nodes.new('CompositorNodeComposite');nt.links.new(dn.outputs['Image'],comp.inputs[0])
stats=[]
for o in bpy.data.objects:
 if o.type=='CURVES' and not o.hide_render:
  r=np.empty(len(o.data.points),np.float32);o.data.attributes['radius'].data.foreach_get('value',r)
  stats.append(dict(object=o.name,curves=len(o.data.curves),radius_quantiles_m=np.quantile(r,[0,.1,.5,.9,1]).tolist()))
bpy.ops.render.render()
assert digest(source)==before
(OUT/'detail_manifest.json').write_text(json.dumps(dict(source_sha256=before,source_unchanged=True,samples=1024,adaptive_sampling=False,geometry_changed=False,model_saved=False,method='One Cycles render; same samples feed raw Image and compositor OIDN with normal/albedo; crop coordinates recorded, not a full-view quality claim.',border=[.42,.64,.40,.68],radii=stats,images_sha256={p.name:digest(p) for p in OUT.glob('*.png')}),indent=2),encoding='utf-8')
print('DETAIL_DIAGNOSTIC_FINISHED',flush=True)
