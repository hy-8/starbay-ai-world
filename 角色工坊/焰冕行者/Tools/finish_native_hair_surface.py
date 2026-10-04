"""Review a restrained hair sheen on unchanged native strand geometry.

Fresh local Blender variant. Material changes are not geometric/art approval.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version,source_version=args[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in args[:2]):raise ValueError(args)
roughness=float(args[args.index('--roughness')+1]) if '--roughness' in args else .30
radial=float(args[args.index('--radial')+1]) if '--radial' in args else .36
if not (.2<=roughness<=.5 and .2<=radial<=.6):raise ValueError('Restrained valid hair roughness required')
out,render=ROOT/'Exports'/version,ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh output required')
source=ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
visible=[o for o in bpy.data.objects if o.type=='CURVES' and not o.hide_render]
def geometry_hash():
 h=hashlib.sha256()
 for ob in sorted(visible,key=lambda o:o.name):
  h.update(ob.name.encode('utf-8'));xyz=np.empty(len(ob.data.points)*3,np.float32)
  ob.data.attributes['position'].data.foreach_get('vector',xyz);h.update(xyz.tobytes())
  r=np.empty(len(ob.data.points),np.float32);ob.data.attributes['radius'].data.foreach_get('value',r);h.update(r.tobytes())
 return h.hexdigest()
before=geometry_hash();clones={};records=[]
for ob in visible:
 for slot in ob.material_slots:
  material=slot.material
  if not material:raise RuntimeError('Missing native hair material')
  if material not in clones:
   clone=material.copy();clone.name=material.name+' • restrained sheen study'
   nodes=[n for n in clone.node_tree.nodes if n.type=='BSDF_HAIR_PRINCIPLED']
   if len(nodes)!=1:raise RuntimeError('Expected inspected single Principled Hair shader')
   shader=nodes[0];changed={}
   for key,value in [('Roughness',roughness),('Radial Roughness',radial)]:
    socket=shader.inputs[key];changed[key]={'old_default':float(socket.default_value),'removed_input_links':len(socket.links),'new_default':value}
    for link in list(socket.links):clone.node_tree.links.remove(link)
    socket.default_value=value
   clones[material]=clone;records.append(dict(source=material.name,new_material=clone.name,changes=changed))
  slot.material=clones[material]
assert geometry_hash()==before
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=128 if '--draft' in args else 192;scene.cycles.use_denoising=False
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=80 if '--draft' in args else 100
out.mkdir(parents=True);render.mkdir(parents=True)
report=dict(version=version,source=source_version,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),method='Fresh cloned hair materials, explicit Roughness/Radial Roughness, preserve color and actual geometry',visible_strands=sum(len(o.data.curves) for o in visible),geometry_before_sha256=before,geometry_after_sha256=geometry_hash(),all_positions_and_radii_unchanged=True,materials=records,samples=scene.cycles.samples,draft='--draft' in args,status='unreviewed true Blender surface study',license='Retained project original frontal / Ddr Rcs Royalty Free rear / Bystedt CC BY-SA support / Abhay Pratap Royalty Free source-flow support')
(out/'surface_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('NATIVE_SURFACE_STUDY_RENDERED',version,flush=True)
