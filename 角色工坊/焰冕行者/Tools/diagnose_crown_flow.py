"""Isolate actual baked crown and fringe fibers without changing the source.

The authored design's contiguous fiber counts are checked against native
curves before selection. Diagnostic images are not final character art.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:]
version,source_version,design_version=args[:3]
CURRENT_SURFACE_REAR='--current-surface-rear' in args
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in args[:3]):raise ValueError(args)
out=ROOT/'Renders'/version
if out.exists():raise RuntimeError('Preserve diagnostic output')
out.mkdir(parents=True)
source=ROOT/'Exports'/source_version/'Ember_Regent.blend'
design=ROOT/'Exports'/design_version/'authored_fringe_design.json'
source_sha=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
objects=[o for o in bpy.data.objects if o.type=='CURVES' and not o.hide_render]
if CURRENT_SURFACE_REAR and not any(o.name.startswith('Original posterior shag') for o in objects):
 raise RuntimeError('Current surface-rear diagnostic requires the actual rebuilt posterior groom')
front=next(o for o in objects if o.name.startswith('Authored frontal revision'))
records=json.loads(design.read_text(encoding='utf-8'))
assert sum(r['assigned_visible_fibers'] for r in records)==len(front.data.curves)
sizes=[len(c.points) for c in front.data.curves]
assert len(set(sizes))==1
N=sizes[0]
xyz=np.empty(len(front.data.points)*3,np.float32)
front.data.attributes['position'].data.foreach_get('vector',xyz);xyz=xyz.reshape(-1,N,3)
rad=np.empty(len(front.data.points),np.float32)
front.data.attributes['radius'].data.foreach_get('value',rad);rad=rad.reshape(-1,N)
regions={'Crown':[],'Fringe':[]};offset=0
for r in records:
 count=r['assigned_visible_fibers'];key='Crown' if 'segmented crown' in r['name'] else 'Fringe'
 regions[key].extend(range(offset,offset+count));offset+=count
col=bpy.data.collections.new('Diagnostic temporary regions');bpy.context.scene.collection.children.link(col)
region_objects={}
for key,indices in regions.items():
 cu=bpy.data.hair_curves.new('Temporary '+key);cu.add_curves([N]*len(indices))
 cu.attributes['position'].data.foreach_set('vector',xyz[indices].ravel())
 cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',rad[indices].ravel())
 for m in front.data.materials:cu.materials.append(m)
 ob=bpy.data.objects.new('Diagnostic '+key,cu);col.objects.link(ob);ob.matrix_world=front.matrix_world.copy()
 region_objects[key]=ob
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=96;scene.cycles.use_denoising=False
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=80
report=dict(source=source_version,design_source=design_version,source_sha256=source_sha,
            method='Actual per-guide native curve subsets; non-destructive isolation',
            counts={key:len(indices) for key,indices in regions.items()},shots=[])
shots=[('01_All','01_Front','All'),('02_Crown','01_Front','Crown'),('03_Fringe','01_Front','Fringe'),
       ('04_Support','01_Front','Support'),('05_Rear','01_Front','Rear'),('06_CrownSide','03_Side','Crown')]
if CURRENT_SURFACE_REAR:
 shots += [('07_RearSide','03_Side','Rear'),('08_SupportSide','03_Side','Support')]
if '--profile-layers-only' in args:
 shots=[('06_CrownSide','03_Side','Crown'),('07_RearSide','03_Side','Rear'),('08_SupportSide','03_Side','Support'),('09_FringeSide','03_Side','Fringe')]
for name,camera,layer in shots:
 for ob in objects:
  support=('short scalp' in ob.name) or (CURRENT_SURFACE_REAR and ('short support' in ob.name or ob.name.startswith('Original posterior coverage')))
  rear=('whole rear' in ob.name) or (CURRENT_SURFACE_REAR and ob.name.startswith('Original posterior shag'))
  ob.hide_render=layer!='All' and not (layer=='Support' and support or layer=='Rear' and rear)
 for key,ob in region_objects.items():ob.hide_render=key!=layer
 scene.camera=bpy.data.objects[camera];scene.render.filepath=str(out/(name+'.png'))
 bpy.ops.render.render(write_still=True)
 report['shots'].append(dict(file=name+'.png',isolated_layer=layer,camera=camera,
                            sha256=hashlib.sha256((out/(name+'.png')).read_bytes()).hexdigest()))
report['source_unchanged']=hashlib.sha256(source.read_bytes()).hexdigest()==source_sha
report['current_surface_rear']=CURRENT_SURFACE_REAR
report['profile_layers_only']='--profile-layers-only' in args
(out/'region_diagnostic.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('CROWN_DIAGNOSTIC_COMPLETE',version,report['source_unchanged'],flush=True)
