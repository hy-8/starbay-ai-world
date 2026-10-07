"""Temporary emission color IDs of actual visible components; no source save."""
import bpy,sys,json,hashlib,re,numpy as np
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
back_view='--back' in a
if not all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:2]):raise ValueError(a)
out=ROOT/'Renders'/version
if out.exists():raise RuntimeError('Fresh IDs required')
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
palette=[(.04,.15,1,1),(0,1,.12,1),(1,.03,.08,1),(1,.5,.02,1),(.65,.04,1,1)]
legend=[]
def emission(color,label):
 m=bpy.data.materials.new(label);m.use_nodes=True;m.node_tree.nodes.clear()
 n=m.node_tree.nodes.new('ShaderNodeEmission');n.inputs['Color'].default_value=color;n.inputs['Strength'].default_value=1
 o=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(n.outputs[0],o.inputs['Surface']);return m
body=emission((.08,.08,.08,1),'ID body neutral')
for ob in bpy.data.objects:
 if ob.type=='MESH' and not ob.hide_render:
  for slot in ob.material_slots:slot.material=body
visible=sorted([o for o in bpy.data.objects if o.type=='CURVES' and not o.hide_render],key=lambda o:o.name)
if len(visible)>len(palette):raise RuntimeError('Every visible component requires an explicit ID color')
for ob,color in zip(visible,palette):
 ob.data=ob.data.copy();ob.data.materials.clear();ob.data.materials.append(emission(color,'ID '+ob.name))
 record=dict(object=ob.name,linear_color=color,fibers=len(ob.data.curves))
 if back_view:
  p=np.empty((len(ob.data.points),3),np.float32);ob.data.attributes['position'].data.foreach_get('vector',p.ravel())
  p=(np.c_[p,np.ones(len(p))]@np.array(ob.matrix_world).T)[:,:3]
  tips=p[np.array([c.first_point_index+c.points_length-1 for c in ob.data.curves])]
  record.update(tip_elevation_quantiles_m=np.quantile(tips[:,2],[0,.01,.1,.5,1]).tolist(),tips_below_1_710m=int((tips[:,2]<1.710).sum()))
 legend.append(record)
s=bpy.context.scene;cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
r=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=r@cam.matrix_world@r
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
for d in p.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=32;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
s.view_settings.view_transform='Standard';out.mkdir(parents=True)
for name in (['05_OppositeSide','02_ThreeQuarter','04_Back'] if back_view else ['05_OppositeSide','02_ThreeQuarter']):
 s.camera=bpy.data.objects[name];s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
assert digest==hashlib.sha256(source.read_bytes()).hexdigest()
(out/'component_id_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,source_unchanged=True,legend=legend,back_view=back_view,method='Temporary real components emission IDs; diagnostic color only, not final beauty render. Full world-space tip aggregates when back requested are geometry statistics, not visibility proof.'),indent=2),encoding='utf-8')
print('HAIR_COMPONENT_IDS_RENDERED',version,flush=True)
