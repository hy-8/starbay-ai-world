"""Actual beauty ablation of saved main groom; source remains untouched."""
import bpy,sys,re,json,hashlib
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:2])
out=ROOT/'Renders'/version;assert not out.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
primary='Bystedt layercut derivative • native root reflow';hidden=[]
for ob in bpy.data.objects:
 if ob.type=='CURVES' and not ob.hide_render and ob.name!=primary:
  ob.hide_render=True;hidden.append(ob.name)
assert len(hidden)==3
s=bpy.context.scene
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
r=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=r@cam.matrix_world@r
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=192;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
out.mkdir(parents=True);images={}
for name in ['02_ThreeQuarter','01_Front','05_OppositeSide']:
 s.camera=bpy.data.objects[name];p=out/(name+'.png');s.render.filepath=str(p);bpy.ops.render.render(write_still=True);images[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'ablation_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,source_unchanged=True,hidden_components=hidden,retained_primary_geometry_material_exact=True,resolution=[960,1120],samples=192,denoising=False,images_sha256=images,method='Temporary hide_render of three support components after loading actual saved68. Existing primary/body/material/lights retained. Diagnostic beauty ablation, not adopted model.'),indent=2),encoding='utf-8')
print('PRIMARY_ONLY_ABLATION_RENDERED',version,flush=True)
