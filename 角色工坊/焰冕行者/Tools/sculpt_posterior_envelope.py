"""Compress excessive posterior hair clearance on the actual body scalp.

Real source-derived native curve deformation, fresh variants only. Preserves
roots and lower nape tips; statistical clearance is not exhaustive collision QA.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version,source_version=args[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in args[:2]):raise ValueError(args)
limit=float(args[args.index('--gap')+1]) if '--gap' in args else .016
if not .008<=limit<=.030:raise ValueError('Posterior gap must be 8..30mm')
out,render=ROOT/'Exports'/version,ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh output required')
source=ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
ob=next(o for o in bpy.data.objects if o.name.startswith('Volumetric recomb • retained rear') and not o.hide_render)
sizes=[len(c.points) for c in ob.data.curves]
if len(set(sizes))!=1:raise RuntimeError('Uniform native point count required')
N=sizes[0];p=np.empty(len(ob.data.points)*3,np.float32);ob.data.attributes['position'].data.foreach_get('vector',p);p=p.reshape(-1,N,3)
old=p.copy();roots=p[:,0].copy();t=np.linspace(0,1,N)
body=bpy.data.objects['CC0 male body • retained topology'];bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
before=[];after=[];changed=0
def smooth01(x):
 x=np.clip(x,0,1);return x*x*(3-2*x)
for i in range(len(p)):
 for j in range(1,N):
  point=p[i,j]
  weight=float(smooth01((point[1]-.005)/.045)*smooth01((point[2]-1.766)/.040)*smooth01(t[j]/.12))
  if weight<1e-6:continue
  hit,n,face,dist=bv.find_nearest(Vector(point));gap=(Vector(point)-hit).dot(n)
  if gap<=limit or dist>.085:continue
  before.append(gap)
  # Smooth spatial and root envelope prevent a clipping plane or hard ring.
  q=Vector(point)-n*((gap-limit)*weight)
  p[i,j]=np.array(q);after.append((q-hit).dot(n));changed+=1
assert np.array_equal(p[:,0],roots) and np.isfinite(p).all()
ob.data.attributes['position'].data.foreach_set('vector',p.ravel())
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=64 if '--draft' in args else 192;scene.cycles.use_denoising=False
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=80 if '--draft' in args else 100
out.mkdir(parents=True);render.mkdir(parents=True)
report=dict(version=version,source=source_version,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),method='Posterior/upper native strand clearance compressed along actual nearest-scalp normals with smooth root and spatial envelopes; lower nape unchanged',target_gap_m=limit,modified_points=changed,exact_roots_preserved=True,max_displacement_m=float(np.linalg.norm(p-old,axis=2).max()),affected_point_gap_before_quantiles_m=np.quantile(before,[0,.5,.95,1]).tolist() if before else [],affected_point_gap_after_quantiles_m=np.quantile(after,[0,.5,.95,1]).tolist() if after else [],geometry_finite=True,draft='--draft' in args,samples=scene.cycles.samples,status='unreviewed actual geometry study',collision_scope='Selected posterior points only, no exhaustive hair/clothing/motion check',license='Project original frontal; Ddr Rcs Royalty Free rear; Bystedt CC BY-SA support; Abhay Pratap Royalty Free source-flow support')
(out/'envelope_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('POSTERIOR_ENVELOPE_RENDERED',version,changed,flush=True)
