"""Whole-fiber composition: UV-authored crown, original fringe and prior nape.

Mixed licensed geometry remains local. No artistic approval implied.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version,source_version=args[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in args[:2]):raise ValueError(args)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh output only')
out.mkdir(parents=True);render.mkdir(parents=True)
source=ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
counts={};repairs=0
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
def subset(ob,name,predicate):
 global repairs
 cu=ob.data;xyz=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',xyz.ravel())
 rad=np.empty(len(cu.points),np.float32);cu.attributes['radius'].data.foreach_get('value',rad)
 strands=[];radii=[]
 for c in cu.curves:
  ix=slice(c.first_point_index,c.first_point_index+c.points_length);s=xyz[ix]
  if predicate(s):
   s=s.copy()
   if '--settle-crown' in args and name.startswith('Salman crown'):
    weight=np.clip((s[:,2]-1.85)/.075,0,1);s[:,2]-=.012*weight*weight
    for j,p in enumerate(s):
     hit,n,_,dist=bv.find_nearest(Vector(p));gap=(Vector(p)-hit).dot(n)
     if gap<.0007 and dist<.035:s[j]=np.array(hit+n*.001);repairs+=1
   strands.append(s);radii.append(rad[ix])
 if not strands:raise RuntimeError('No retained curves: '+name)
 nc=bpy.data.hair_curves.new(name);nc.add_curves([len(s) for s in strands]);nc.attributes['position'].data.foreach_set('vector',np.concatenate(strands).ravel())
 nc.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.concatenate(radii))
 nc.materials.append(bpy.data.objects['Authored spatial fringe • actual scalp root patches'].data.materials[0])
 new=bpy.data.objects.new(name,nc);bpy.context.scene.collection.objects.link(new);ob.hide_render=True;ob.hide_viewport=True;counts[name]=len(strands)
front=bpy.data.objects['Authored spatial fringe • actual scalp root patches']
subset(front,'Original long fringe • whole-fiber retained',lambda s:s[-1,2]<1.81 and s[-1,1]<-.085)
crown=bpy.data.objects['Salman native derivative • real painted UV strands']
subset(crown,'Salman crown • whole-fiber selected',lambda s:s[-1,2]>1.805 and s[0,2]>1.825)
for name in ['Ddr Rcs derivative • whole rear locks','Bystedt derivative • short scalp support']:
 ob=bpy.data.objects[name];ob.hide_render=False;ob.hide_viewport=False;counts[name]=len(ob.data.curves)
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
draft='--draft' in args;scene.cycles.device='GPU';scene.cycles.samples=64 if draft else 192;scene.cycles.use_denoising=False;scene.cycles_curves.shape='THICK'
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=80 if draft else 100
report={'version':version,'source':source_version,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'method':'Whole-fiber composition, no crown point deletion; retained original long fringe, side/nape and short support','visible_component_curves':counts,'license':'Salman crown and Ddr Rcs rear Royalty Free; Bystedt short support CC BY-SA, version unspecified; original frontal geometry; keep licensed geometry local','draft':draft,'artistic_status':'unreviewed actual composition','processing_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
report.update(crown_height_settlement='--settle-crown' in args,crown_clearance_repairs=repairs,samples=scene.cycles.samples)
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('LAYERED_CROWN_COMPOSED',version,counts,flush=True)
