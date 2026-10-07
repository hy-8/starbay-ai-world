"""Isolate undercoat reflectance; preserve geometry, pigment and primary shader."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
assert not out.exists() and not render.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
primary=bpy.data.objects['Bystedt layercut derivative • native root reflow']
visible=sorted([o for o in bpy.data.objects if o.type=='CURVES' and not o.hide_render],key=lambda o:o.name)
assert len(visible)==4
def geometry():
 h=hashlib.sha256()
 for o in visible:
  p=np.empty((len(o.data.points),3),np.float32);o.data.attributes['position'].data.foreach_get('vector',p.ravel())
  r=np.empty(len(o.data.points),np.float32);o.data.attributes['radius'].data.foreach_get('value',r)
  h.update(o.name.encode());h.update(p.tobytes());h.update(r.tobytes());h.update(np.array(o.matrix_world).tobytes());h.update(np.array([c.points_length for c in o.data.curves]).tobytes())
 return h.hexdigest()
def graph(mat):
 rows=[]
 for n in mat.node_tree.nodes:
  row=dict(name=n.name,type=n.bl_idname,inputs=[(i.name,repr(i.default_value[:]) if hasattr(i.default_value,'__len__') else repr(i.default_value)) for i in n.inputs if hasattr(i,'default_value')])
  if n.type=='VALTORGB':row['ramp']=[(e.position,list(e.color)) for e in n.color_ramp.elements]
  if n.type=='BSDF_HAIR_PRINCIPLED':row.update(model=n.model,parametrization=n.parametrization)
  rows.append(row)
 return dict(nodes=rows,links=[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in mat.node_tree.links])
def pigments(mat):
 return [(n.name,[tuple(e.color) for e in n.color_ramp.elements] if n.type=='VALTORGB' else [(i.name,repr(i.default_value[:])) for i in n.inputs if i.name in ['Color','Base Color'] and hasattr(i,'default_value')]) for n in mat.node_tree.nodes if n.type=='VALTORGB' or n.type in ['BSDF_PRINCIPLED','BSDF_HAIR_PRINCIPLED']]
before=geometry();primary_before=[graph(s.material) for s in primary.material_slots]
copies={};records=[];changed=[]
for ob in visible:
 if ob==primary:continue
 ob.data=ob.data.copy()
 for slot in ob.material_slots:
  old=slot.material;assert old and old.use_nodes
  if old not in copies:
   mat=old.copy();mat.name=old.name+' • matte undercoat comparison'
   before_pigments=pigments(old);changes=[]
   for n in mat.node_tree.nodes:
    values=[('Roughness',.65),('Specular IOR Level',.15)] if n.type=='BSDF_PRINCIPLED' else [('Roughness',.55),('Radial Roughness',.60)] if n.type=='BSDF_HAIR_PRINCIPLED' else []
    for name,value in values:
     socket=n.inputs[name];changes.append(dict(node=n.name,input=name,old_default=float(socket.default_value),removed_links=len(socket.links),new_default=value))
     for link in list(socket.links):mat.node_tree.links.remove(link)
     socket.default_value=value
   assert changes and pigments(mat)==before_pigments
   copies[old]=mat;records.append(dict(source_material=old.name,cloned_material=mat.name,changes=changes,pigment_inputs_and_ramps_exact=True))
  slot.material=copies[old]
 changed.append(ob.name)
assert geometry()==before and [graph(s.material) for s in primary.material_slots]==primary_before
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
(out/'undercoat_sheen_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,changed_components=changed,materials=records,all_visible_hair_geometry_before_sha256=before,all_visible_hair_geometry_after_sha256=geometry(),primary_material_graph_exact=True,pigment_inputs_and_ramps_exact=True,method='Clone only three support component materials and change only the shader sockets explicitly listed in materials.changes. In source68 only Principled Hair roughness/radial inputs exist; no standard Principled surface shader is present. Keep pigment, mix factors, primary material and all geometry.',status='Actual drafts pending review; material control is not geometry repair or art completion'),indent=2),encoding='utf-8')
print('UNDERCOAT_SHEEN_SAVED',version,flush=True)
