"""Actual primary shaft section IDs, including the previously preserved entry."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:2])
out=ROOT/'Renders'/version;assert not out.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());p=p.reshape(-1,65,3)
r=np.empty(len(cu.points),np.float32);cu.attributes['radius'].data.foreach_get('value',r);r=r.reshape(-1,65)
def emission(color,label):
 mat=bpy.data.materials.new(label);mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear()
 n=nt.nodes.new('ShaderNodeEmission');n.inputs['Color'].default_value=color;n.inputs['Strength'].default_value=1
 output=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(n.outputs[0],output.inputs['Surface']);return mat
neutral=emission((.07,.07,.07,1),'Neutral body diagnostic')
for item in bpy.data.objects:
 if item.type=='CURVES':item.hide_render=True
 elif item.type=='MESH' and not item.hide_render:
  for slot in item.material_slots:slot.material=neutral
sections=[(0,7,(.03,.12,1,1)),(7,16,(0,1,.08,1)),(16,32,(1,.03,.05,1)),(32,64,(1,.6,.02,1))]
legend=[]
for first,last,color in sections:
 q=p[:,first:last+1].copy();rr=r[:,first:last+1].copy();data=bpy.data.hair_curves.new('Primary section '+str(first));data.add_curves([last-first+1]*len(p))
 data.attributes['position'].data.foreach_set('vector',q.ravel());data.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',rr.ravel())
 data.materials.append(emission(color,'Section ID '+str(first)))
 new=bpy.data.objects.new('Primary points '+str(first)+'-'+str(last),data);bpy.context.scene.collection.objects.link(new);new.matrix_world=ob.matrix_world
 legend.append(dict(first_point_zero_based=first,last_point_zero_based=last,linear_color=color,actual_positions_sha256=hashlib.sha256(q.tobytes()).hexdigest(),method='Direct saved point/radius slices; adjacent sections share exact boundary point'))
s=bpy.context.scene;cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
reflection=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=reflection@cam.matrix_world@reflection
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=32;s.cycles.use_denoising=False
s.view_settings.view_transform='Standard';s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
out.mkdir(parents=True);images={}
for name in ['02_ThreeQuarter','05_OppositeSide']:
 s.camera=bpy.data.objects[name];path=out/(name+'.png');s.render.filepath=str(path);bpy.ops.render.render(write_still=True);images[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'shaft_section_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,source_unchanged=True,legend=legend,images_sha256=images,method='Primary-only emission ID sections. Saved65-point fibers split at7/16/32 with shared endpoints. Geometry taken directly from saved primary, all support hidden temporarily; no source save. Not final hair appearance or continuous visibility proof.'),indent=2),encoding='utf-8')
print('NATIVE_SHAFT_SECTIONS_RENDERED',version,flush=True)
