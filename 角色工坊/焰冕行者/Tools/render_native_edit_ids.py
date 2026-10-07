"""Actual temporary edited/untouched hair IDs, with no saved-source mutation."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base,attribute=a[:3]
crown='--crown-peaks' in a
front_views='--front-views' in a
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:3]):raise ValueError(a)
out=ROOT/'Renders'/version
if out.exists():raise RuntimeError('Fresh ID renders required')
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
def emission(name,color):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.node_tree.nodes.clear();e=m.node_tree.nodes.new('ShaderNodeEmission');e.inputs['Color'].default_value=(*color,1);e.inputs['Strength'].default_value=1
 o=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(e.outputs[0],o.inputs[0]);return m
gray=emission('ID body',(.06,.06,.06));support=emission('ID support',(0,1,.08))
for ob in bpy.data.objects:
 if ob.type=='MESH' and not ob.hide_render:
  for slot in ob.material_slots:slot.material=gray
 elif ob.type=='CURVES' and not ob.hide_render and not ob.name.startswith('Bystedt layercut'):
  ob.data=ob.data.copy();ob.data.materials.clear();ob.data.materials.append(support)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data;mask=np.empty(len(cu.curves),bool)
if not crown:cu.attributes[attribute].data.foreach_get('value',mask)
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());p=p.reshape(-1,65,3)
if crown:mask=p[:,:,2].max(axis=1)>1.875
r=np.empty(len(cu.points),np.float32);cu.attributes['radius'].data.foreach_get('value',r);r=r.reshape(-1,65)
for selected,color,name in [(True,(.04,.16,1),'Edited native shafts'),(False,(1,.03,.07),'Untouched native shafts')]:
 rows=mask==selected;new=bpy.data.hair_curves.new(name);new.add_curves([65]*int(rows.sum()));new.attributes['position'].data.foreach_set('vector',p[rows].ravel());new.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',r[rows].ravel());new.materials.append(emission(name,color))
 item=bpy.data.objects.new(name,new);bpy.context.scene.collection.objects.link(item);item.matrix_world=ob.matrix_world
ob.hide_render=True
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=32;s.cycles.use_denoising=False;s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80;s.view_settings.view_transform='Standard';out.mkdir(parents=True)
for name in (['02_ThreeQuarter','01_Front'] if front_views else ['04_Back','03_Side']):
 s.camera=bpy.data.objects[name];s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'edit_id_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,source_unchanged=True,selection_attribute=None if crown else attribute,selection_rule='Primary shaft maximum z>1.875m' if crown else attribute,legend={'blue':'High crown primary shafts' if crown else 'Edited primary curves','red':'Other primary shafts' if crown else 'Untouched primary curves','green':'All short support components','gray':'Body/clothes'},edited_fibers=int(mask.sum()),unselected_fibers=int((~mask).sum()),method='Exact temporary curve subsets with original radii/matrix, actual cameras, emission diagnostic only',status='Unreviewed actual component diagnostic'),indent=2),encoding='utf-8');print('NATIVE_EDIT_IDS_RENDERED',version,flush=True)
