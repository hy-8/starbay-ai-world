"""Restyle actual native locks as smooth spatial cubics with retained roots.

Does not alter source geometry/files or imply animation/art acceptance.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version,source_version=args[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in args[:2]):raise ValueError(args)
out,render=ROOT/'Exports'/version,ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh output required')
source=ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
body=bpy.data.objects['CC0 male body • retained topology'];bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
front=next(o for o in bpy.data.objects if not o.hide_render and o.name.startswith('Authored frontal revision'))
records=json.loads((ROOT/'Exports/spatialfringe17/authored_fringe_design.json').read_text(encoding='utf-8'))
sizes=[len(c.points) for c in front.data.curves]
if len(set(sizes))!=1 or sum(r['assigned_visible_fibers'] for r in records)!=len(sizes):raise RuntimeError('Expected known original frontal groups')
N=sizes[0];t=np.linspace(0,1,N);v=t[:,None]
p=np.empty(len(front.data.points)*3,np.float32);front.data.attributes['position'].data.foreach_get('vector',p);p=p.reshape(-1,N,3)
old_roots=p[:,0].copy();offset=0;repairs=0;max_delta=0.
for record in records:
 count=record['assigned_visible_fibers'];group=p[offset:offset+count].astype(float);base=np.median(group,axis=0)
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(base,axis=0),axis=1))];L=float(arc[-1])
 start=base[min(12,N-1)]-base[0];start/=max(np.linalg.norm(start),1e-8)
 end=base[-1]-base[-min(12,N)];end/=max(np.linalg.norm(end),1e-8)
 handles=np.array([base[0],base[0]+start*L*.39,base[-1]-end*L*.30,base[-1]])
 cubic=(1-v)**3*handles[0]+3*(1-v)**2*v*handles[1]+3*(1-v)*v*v*handles[2]+v**3*handles[3]
 # Preserve a little low-frequency source shape while suppressing repeated
 # crossed S loops. Ends/roots remain identical; no collapsing onto one line.
 newbase=.78*cubic+.22*base
 for j,point in enumerate(newbase):
  hit,n,face,dist=bv.find_nearest(Vector(point));gap=(Vector(point)-hit).dot(n)
  if j and gap<.0014 and dist<.040:newbase[j]=np.array(hit+n*.0016);repairs+=1
 result=group+(newbase-base)[None,:,:]
 result[:,0]=group[:,0]
 max_delta=max(max_delta,float(np.linalg.norm(result-group,axis=2).max()))
 p[offset:offset+count]=result.astype(np.float32);offset+=count
assert np.array_equal(p[:,0],old_roots)
if not np.isfinite(p).all():raise RuntimeError('Invalid restyling')
front.data.attributes['position'].data.foreach_set('vector',p.ravel())
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=64 if '--draft' in args else 192;scene.cycles.use_denoising=False
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=80 if '--draft' in args else 100
out.mkdir(parents=True);render.mkdir(parents=True)
report=dict(version=version,source=source_version,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),method='Actual per-lock median paths blended 78% spatial cubic, 22% old shape; retain true fiber offsets and exact roots',frontal_groups=len(records),frontal_curves=len(sizes),exact_original_roots_preserved=True,base_clearance_repairs=repairs,max_delta_m=max_delta,samples=scene.cycles.samples,draft='--draft' in args,status='unreviewed actual geometry study',license='Project original frontal; Ddr Rcs Royalty Free rear; Bystedt CC BY-SA support; Abhay Pratap Royalty Free flow-derived scalp support',collision_scope='Base clearance only, not exhaustive fiber/clothing/motion validation')
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('SMOOTH_STYLING_RENDERED',version,flush=True)
