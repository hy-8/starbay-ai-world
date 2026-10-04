"""Read a supplied local Blender asset with auto scripts disabled; no source save."""
import bpy,sys,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:];source=Path(args[0]).resolve();output=Path(args[1]).resolve()
if output.exists():raise RuntimeError('Keep previous inspection')
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
items=[]
for o in bpy.data.objects:
 bounds=[o.matrix_world@Vector(v) for v in o.bound_box] if o.type in ('MESH','CURVE','CURVES') else []
 record=dict(name=o.name,type=o.type,hide_render=o.hide_render,location=list(o.location),scale=list(o.scale),bounds_min=[min(v[i] for v in bounds) for i in range(3)] if bounds else None,bounds_max=[max(v[i] for v in bounds) for i in range(3)] if bounds else None,materials=[m.name if m else None for m in o.data.materials] if hasattr(o.data,'materials') else [],modifiers=[dict(name=m.name,type=m.type,node_group=m.node_group.name if m.type=='NODES' and m.node_group else None) for m in o.modifiers])
 if o.type=='MESH':
  record.update(vertices=len(o.data.vertices),faces=len(o.data.polygons),uv_layers=[uv.name for uv in o.data.uv_layers],attributes=[a.name for a in o.data.attributes])
  stats={}
  for name in ('Factor','curve_group_id_ht','Random'):
   attr=o.data.attributes.get(name)
   if attr and attr.data_type in ('FLOAT','INT','BYTE_COLOR','FLOAT_COLOR'):
    a=np.array([d.value if attr.data_type in ('FLOAT','INT') else d.color[0] for d in attr.data]);stats[name]=dict(domain=attr.domain,type=attr.data_type,min=float(a.min()),max=float(a.max()),unique=len(np.unique(a)))
  record['attribute_stats']=stats
  factor=o.data.attributes.get('Factor')
  if factor and factor.domain=='POINT':
   a=np.array([d.value if factor.data_type in ('FLOAT','INT') else d.color[0] for d in factor.data]);xyz=np.array([o.matrix_world@v.co for v in o.data.vertices]);roots=xyz[a<.025]
   if len(roots):record['low_factor_points']=dict(count=len(roots),min=roots.min(axis=0).tolist(),max=roots.max(axis=0).tolist(),mean=roots.mean(axis=0).tolist())
 if o.type=='CURVES':record.update(points=len(o.data.points),curves=len(o.data.curves),attributes=[a.name for a in o.data.attributes])
 items.append(record)
materials=[]
for mat in bpy.data.materials:
 materials.append(dict(name=mat.name,nodes=[dict(name=n.name,type=n.type,image=n.image.name if n.type=='TEX_IMAGE' and n.image else None) for n in mat.node_tree.nodes] if mat.node_tree else []))
groups=[]
for nt in bpy.data.node_groups:
 groups.append(dict(name=nt.name,nodes=len(nt.nodes),inputs=[dict(name=it.name,type=it.socket_type,default=list(it.default_value) if hasattr(it,'default_value') and not isinstance(it.default_value,(str,int,float,bool)) else getattr(it,'default_value',None)) for it in nt.interface.items_tree if it.item_type=='SOCKET' and it.in_out=='INPUT']))
report=dict(source_filename=source.name,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),objects=items,materials=materials,images=[dict(name=i.name,path=i.filepath,size=list(i.size),packed=bool(i.packed_file)) for i in bpy.data.images],node_groups=groups,auto_scripts_enabled=False)
output.write_text(json.dumps(report,indent=2),encoding='utf-8')
print('INSPECTED_ASSET',source.name,len(items),flush=True)
