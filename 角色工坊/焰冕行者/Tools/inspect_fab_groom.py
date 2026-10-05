"""Read-only inspection of the locally licensed Fab source; no autoexec."""
import bpy,json,sys,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'Source/FabMediumLayered/hairstyle.blend'
out=ROOT/'Source/FabMediumLayered/inspection.json'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
bpy.context.view_layer.update()
report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'blender_version':bpy.app.version_string,'objects':[],'materials':[],'images':[],
 'scripts_not_executed':True,'node_groups':[n.name for n in bpy.data.node_groups]}
for ob in bpy.data.objects:
 row={'name':ob.name,'type':ob.type,'hide_render':ob.hide_render,'location':list(ob.location),
 'matrix_world':[list(r) for r in ob.matrix_world],
 'materials':[m.name if m else None for m in getattr(ob.data,'materials',[])],
 'modifiers':[{'name':m.name,'type':m.type,'group':m.node_group.name if m.type=='NODES' and m.node_group else None} for m in ob.modifiers]}
 if ob.type=='MESH':
  row.update(vertices=len(ob.data.vertices),faces=len(ob.data.polygons),
   bounds=[list(ob.matrix_world@Vector(p)) for p in ob.bound_box])
 if ob.type=='CURVES':
  p=np.empty(len(ob.data.points)*3,np.float32);ob.data.attributes['position'].data.foreach_get('vector',p)
  p=p.reshape(-1,3)
  row.update(curves=len(ob.data.curves),points=len(ob.data.points),local_bounds=[p.min(0).tolist(),p.max(0).tolist()],
   attributes=[(x.name,x.data_type,x.domain) for x in ob.data.attributes],surface=ob.data.surface.name if ob.data.surface else None,
   surface_uv_map=ob.data.surface_uv_map)
 if ob.particle_systems:
  row['particles']=[{'name':ps.name,'type':ps.settings.type,'count':ps.settings.count,
   'children':ps.settings.child_type,'child_percent':ps.settings.child_percent,'rendered_child_count':ps.settings.rendered_child_count,
   'actual_particles':len(ps.particles),'hair_key_counts':[len(p.hair_keys) for p in list(ps.particles)[:5]],
   'first_hair_local_keys': [list(k.co) for k in ps.particles[0].hair_keys] if len(ps.particles) else [],
   'settings': {p.identifier:getattr(ps.settings,p.identifier) for p in ps.settings.bl_rna.properties if p.type in {'INT','FLOAT','BOOLEAN','ENUM'} and not getattr(p,'is_array',False)}} for ps in ob.particle_systems]
 report['objects'].append(row)
for m in bpy.data.materials:
 def val(v):
  if isinstance(v,(str,int,float,bool)):return v
  try:return list(v)
  except TypeError:return str(v)
 report['materials'].append({'name':m.name,'nodes':[{'name':n.name,'type':n.type,'inputs':[(i.name,val(i.default_value)) for i in n.inputs if hasattr(i,'default_value')],
  'outputs':[(i.name,val(i.default_value)) for i in n.outputs if hasattr(i,'default_value')],
  'ramp':[(e.position,list(e.color)) for e in n.color_ramp.elements] if n.type=='VALTORGB' else None} for n in m.node_tree.nodes] if m.use_nodes else [],
  'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links] if m.use_nodes else []})
for im in bpy.data.images:report['images'].append({'name':im.name,'path':im.filepath,'packed':bool(im.packed_file),'size':list(im.size)})
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=True),flush=True)
