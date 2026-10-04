"""Read-only packed shader and UV topology diagnosis; geometry report local."""
import bpy,json,sys
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[1]
source=root/'Source/BlenderKitResearch/Salman_ShortHairCard.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
bpy.context.view_layer.update()
report={'shaders':[], 'cards':[]}
for mat in bpy.data.materials:
 if not mat.node_tree:continue
 report['shaders'].append({'name':mat.name,'nodes':[{'name':n.name,'type':n.type,'inputs':{s.name:(list(s.default_value) if hasattr(s.default_value,'__len__') and not isinstance(s.default_value,str) else s.default_value) for s in n.inputs if hasattr(s,'default_value') and not s.is_linked},'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None} for n in mat.node_tree.nodes], 'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in mat.node_tree.links]})
for ob in bpy.data.objects:
 if ob.type!='MESH':continue
 me=ob.data; xyz=np.array([ob.matrix_world@v.co for v in me.vertices])
 uv=np.array([l.uv[:] for l in me.uv_layers.active.data]); ids=np.array([l.vertex_index for l in me.loops])
 vu=np.zeros((len(xyz),2)); count=np.zeros(len(xyz));np.add.at(vu,ids,uv);np.add.at(count,ids,1);vu/=np.maximum(count[:,None],1)
 parent=np.arange(len(xyz))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for e in me.edges:
  a,b=map(find,e.vertices)
  if a!=b:parent[b]=a
 groups={}
 for i in range(len(xyz)):groups.setdefault(find(i),[]).append(i)
 records=[]
 for ix in groups.values():
  a=xyz[ix];uvs=vu[ix]
  records.append({'vertices':len(ix),'bounds_min':a.min(0).tolist(),'bounds_max':a.max(0).tolist(),'uv_min':uvs.min(0).tolist(),'uv_max':uvs.max(0).tolist(),'unique_uv_u':len(np.unique(np.round(uvs[:,0],5))),'unique_uv_v':len(np.unique(np.round(uvs[:,1],5)))})
 report['cards'].append({'name':ob.name,'components':len(records),'records':records})
path=root/'Source/BlenderKitResearch/salman_shader_uv_diagnosis01.json'
if path.exists():raise RuntimeError('Fresh report required')
path.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'shaders':report['shaders'],'component_counts':[(r['name'],r['components'],r['records'][:3]) for r in report['cards']]},indent=2))
