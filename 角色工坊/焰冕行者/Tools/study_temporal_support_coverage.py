"""Isolate temporal support radius/material response; real geometry, no source save."""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2];mode=a[2]
assert mode in ['radius','pigment','skin-control','hide-support']
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=ROOT/'Renders'/version;assert not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
records=[]
if mode=='skin-control':
 ob=bpy.data.objects['CC0 male body • retained topology']
 mat=bpy.data.materials.new('Black body diagnostic');mat.use_nodes=True
 bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.001,.001,.001,1);bs.inputs['Roughness'].default_value=1
 for slot in ob.material_slots:slot.material=mat
else:
 for name in ['Abhay flow derivative • real scalp sampled short support','Bystedt derivative • short scalp support']:
  ob=bpy.data.objects[name];cu=ob.data
  if mode=='hide-support':
   ob.hide_render=True;records.append(dict(object=name,temporarily_hidden=True));continue
  if mode=='radius':
   p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
   r=np.empty(len(p),np.float32);cu.attributes['radius'].data.foreach_get('value',r)
   starts=np.array([c.first_point_index for c in cu.curves]);sizes=np.array([c.points_length for c in cu.curves]);roots=p[starts]
   field=np.clip(1-((roots[:,1]+.083)/.043)**2-((roots[:,2]-1.844)/.047)**2,0,1)**.6
   field*=np.clip((roots[:,0]-.012)/.025,0,1)
   factor=1+.8*field;new=r*np.repeat(factor,sizes);cu.attributes['radius'].data.foreach_set('value',new)
   records.append(dict(object=name,changed_fibers=int((field>0).sum()),max_root_radius_m=float(new[starts].max())))
  else:
   mat=cu.materials[0].copy();cu.materials[0]=mat
   for e in mat.node_tree.nodes['Color Ramp'].color_ramp.elements:
    c=list(e.color);e.color=tuple(v*.30 for v in c[:3])+(c[3],)
   bs=next(n for n in mat.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfHairPrincipled')
   bs.inputs['Roughness'].default_value=.42;bs.inputs['Reflection'].default_value=.30
   records.append(dict(object=name,pigment_rgb_multiplier=.30,roughness=.42,reflection=.30))
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=192;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
out.mkdir(parents=True);shot='02_ThreeQuarter' if mode=='hide-support' else '03_Side';s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'coverage_study_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,source_unchanged=True,mode=mode,model_saved=False,records=records,image_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),scope='Read-only diagnostic. Radius mode changes support radii only with continuous positiveX temporal field; pigment mode changes two support materials only; skin-control replaces body material to identify skin contribution, never a candidate.'),indent=2),encoding='utf-8')
print('SUPPORT_COVERAGE_STUDY',version,flush=True)
