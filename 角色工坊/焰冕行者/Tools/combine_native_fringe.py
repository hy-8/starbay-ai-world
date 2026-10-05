"""Retain natural source crown/rear and add complete reflowed frontal shafts.

Both local grooms derive from Bystedt Hair Styles, CC BY-SA, version unspecified.
No point deletion to build a visible shell; complete selected fibers retained.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version=a[0]
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh composition only')
base=ROOT/'Exports/postscissor02/Ember_Regent.blend';fringe=ROOT/'Exports/nativeroot03/Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(base),use_scripts=False)
with bpy.data.libraries.load(str(fringe),link=False) as (src,dst):dst.objects=['Bystedt layercut derivative • native root reflow']
donor=dst.objects[0];assert donor is not None and np.allclose(np.array(donor.matrix_world),np.eye(4))
cu=donor.data;p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
r=np.empty(len(cu.points),np.float32);cu.attributes['radius'].data.foreach_get('value',r)
paths=[];radii=[]
for c in cu.curves:
 ix=slice(c.first_point_index,c.first_point_index+c.points_length);q=p[ix]
 if q[-1,1]<-.145 and q[-1,2]<1.810 and q[0,2]>1.810 and q[0,1]<-.055:
  paths.append(q.copy());radii.append(r[ix].copy())
assert paths,'No true frontal strands selected'
new=bpy.data.hair_curves.new('Complete selected Bystedt reflowed fringe fibers')
new.add_curves([len(q) for q in paths]);new.attributes['position'].data.foreach_set('vector',np.concatenate(paths).ravel())
new.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.concatenate(radii))
mat=next(o for o in bpy.data.objects if o.type=='CURVES' and not o.hide_render).data.materials[0]
new.materials.append(mat)
ob=bpy.data.objects.new('Bystedt derivative • whole frontal shafts over natural source crown',new);bpy.context.scene.collection.objects.link(ob)
# The unlinked imported donor is only the read source; no hidden duplicate
# full head is linked into the scene or presented as live controls.
bpy.data.objects.remove(donor,do_unlink=True)
out.mkdir(parents=True);render.mkdir(parents=True)
report=dict(base='postscissor02',fringe='nativeroot03',base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),
 fringe_sha256=hashlib.sha256(fringe.read_bytes()).hexdigest(),frontal_complete_fibers=len(paths),
 author='Daniel Bystedt',license='CC BY-SA; version unspecified',
 method='Complete actual frontal fibers selected by root and free-tip region, no per-point shell selection; natural unreshaped source crown/rear retained',
 scope='Static combination; does not assert seam/collision/art quality',status='Unreviewed real 3D composition')
(out/'composition_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('NATIVE_FRINGE_COMPOSED',version,len(paths),flush=True)
