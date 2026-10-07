"""Support-only shader control: disconnect the legacy lobe, keep pigment/geometry."""
import bpy,sys,re,json,hashlib
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
records=[];copies={}
for ob in bpy.data.objects:
 if ob.type!='CURVES' or ob.hide_render or ob==primary:continue
 ob.data=ob.data.copy()
 for slot in ob.material_slots:
  old=slot.material
  if old not in copies:
   mat=old.copy();mat.name='Support only • existing Chiang pigment, no legacy lobe'
   nt=mat.node_tree
   hair=[n for n in nt.nodes if n.type=='BSDF_HAIR_PRINCIPLED'];assert len(hair)==1 and hair[0].model=='CHIANG'
   output=[n for n in nt.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output];assert len(output)==1
   before=[(l.from_node.name,l.from_socket.name) for l in output[0].inputs['Surface'].links]
   nt.links.new(hair[0].outputs[0],output[0].inputs['Surface'])
   copies[old]=mat
   records.append(dict(source_material=old.name,new_material=mat.name,previous_surface_links=before,new_surface_node=hair[0].name,model=hair[0].model))
  slot.material=copies[old]
out.mkdir(parents=True);render.mkdir(parents=True);s=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for name in ['02_ThreeQuarter','05_OppositeSide']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'support_lobe_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,materials=records,method='Support materials only: connect the existing Chiang node directly to Surface instead of75%Chiang/25%legacy directional mixture. All original nodes/input values/pigment ramps retained; primary slots, geometry and lights unmodified. Changes the effective mixed shader; no absorption-equivalence assumption.',status='Actual two-view control pending review, not a geometry repair'),indent=2),encoding='utf-8')
print('SUPPORT_LOBE_SAVED',version,flush=True)
