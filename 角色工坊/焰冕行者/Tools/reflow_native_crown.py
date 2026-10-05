"""Re-lay a limited root region of the saved Bystedt layered groom.

Local CC BY-SA derivative (version unspecified). Complete shafts preserved,
only root-to-crown flow is changed. No generative source input or publication.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version=a[0]
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh candidate only')
source=ROOT/'Exports/napeunderlay02/Ember_Regent.blend'
donor=ROOT/'Exports/layercut04/Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
hidden=[]
for o in bpy.data.objects:
 if not o.hide_render and (o.type=='CURVES' or o.name.startswith('Original nape underlay')):
  o.hide_render=True;o.hide_set(True);hidden.append(o.name)
with bpy.data.libraries.load(str(donor),link=False) as (src,dst):
 dst.objects=['Daniel Bystedt adapted layered cut • CC BY-SA']
ob=dst.objects[0]
if ob is None:raise RuntimeError('Inspected donor object missing')
bpy.context.scene.collection.objects.link(ob)
assert np.allclose(np.array(ob.matrix_world),np.eye(4))
ob.name='Bystedt layercut derivative • native root reflow'
body=bpy.data.objects['CC0 male body • retained topology'];bpy.context.view_layer.update()
assert np.allclose(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
cu=ob.data;p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
N=65;t=np.linspace(0,1,N);paths=[];radii=[];changed=0;repairs=0;rootmoves=[];displacements=[];crestpoints=0
sample='--region-sample' in a;control='--control' in a
for c in cu.curves:
 old=p[c.first_point_index:c.first_point_index+c.points_length].astype(float)
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(old,axis=0),axis=1))]
 if arc[-1]<1e-8:raise RuntimeError('Degenerate native strand')
 q=np.stack([np.interp(t*arc[-1],arc,old[:,k]) for k in range(3)],axis=1)
 original=q.copy();root=q[0].copy()
 region=(root[2]>1.81 and root[1]<.02)
 if sample:region=region and root[0]>.015 and root[1]<-.025
 if region and not control:
  # Original source clumping has tight root arches. Blend to a soft scalp
  # lift for the initial root section, keeping the free fringe trajectory.
  u=np.clip(t/.48,0,1);weight=1-u*u*(3-2*u)
  weights=[]
  for j in range(N):
   if weight[j]<.001:continue
   hit,n,_,dist=bv.find_nearest(Vector(q[j]))
   # Do not drag a free hanging tip or distant front path onto the face.
   if q[j,2]<1.818 or dist>.055:continue
   height=.0006+.0075*np.sin(np.pi*u[j])
   target=np.array(hit+n*height)
   q[j]=q[j]*(1-weight[j])+target*weight[j]
  # Small curvature relaxation restricted to the same transition region.
  for _ in range(5):
   mid=(q[:-2]+2*q[1:-1]+q[2:])*.25
   w=weight[1:-1]*.55
   q[1:-1]=q[1:-1]*(1-w[:,None])+mid*w[:,None]
  # Hair contact is a broad path displacement, not isolated snapped kinks.
  for _ in range(2):
   correction=np.zeros_like(q)
   for j in range(1,N-1):
    if q[j,2]<1.80:continue
    hit,n,_,dist=bv.find_nearest(Vector(q[j]));gap=(Vector(q[j])-hit).dot(n)
    if dist<.025 and gap<.0004:
     d=np.array(n)*(.0005-gap);repairs+=1
     for k in range(max(1,j-2),min(N-1,j+3)):
      correction[k]+=d*np.exp(-.5*((k-j)/1.15)**2)
   q+=correction
  hit,n,_,dist=bv.find_nearest(Vector(q[0]));q[0]=np.array(hit+n*.0005)
  changed+=1;rootmoves.append(float(np.linalg.norm(q[0]-root)))
  displacements.append(float(np.linalg.norm(q-original,axis=1).max()))
 if '--crest-settle' in a and not control:
  # Probe of the actual whole groom locates its tight crest on negative X.
  # The old positive-X compression could not address this source arch.
  w=np.exp(-((q[:,0]+.020)/.030)**2-((q[:,1]+.058)/.035)**2)
  w*=np.clip((q[:,2]-1.846)/.035,0,1)*(1-np.exp(-t*22))
  for j in np.flatnonzero(w>.012):
   hit,n,_,dist=bv.find_nearest(Vector(q[j]));gap=(Vector(q[j])-hit).dot(n)
   if gap>.008 and dist<.05:
    q[j]-=np.array(n)*(gap-.008)*.62*w[j];crestpoints+=1
 paths.append(q.astype(np.float32))
 # Keep the inspected physical scale; fuller shaft with a fine terminal tip.
 radii.append((.000037*(1-.997*t**3)**.65).astype(np.float32))
new=bpy.data.hair_curves.new('Reflowed complete Bystedt layered strands')
new.add_curves([N]*len(paths));new.attributes['position'].data.foreach_set('vector',np.array(paths).ravel())
new.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.array(radii).ravel())
for mat in cu.materials:new.materials.append(mat)
ob.data=new;ob.hide_render=False;ob.hide_set(False)
credits=bpy.data.texts.new('NATIVE_CROWN_REFLOW_CREDITS')
credits.write('Daniel Bystedt Hair Styles, CC BY-SA; version unspecified in inspected evidence.\nhttps://www.blender.org/download/demo-files/\nDerivative of locally retained layercut04: native strands resampled and root-region scalp-lift blending, smooth contact, physical radius. No live-node source relationship implied.\n')
out.mkdir(parents=True);render.mkdir(parents=True)
report=dict(stable_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),donor_sha256=hashlib.sha256(donor.read_bytes()).hexdigest(),
 author='Daniel Bystedt',license='CC BY-SA, version unspecified',strands=len(paths),changed_strands=changed,
 region_sample=sample,control=control,root_correction_quantiles_m=np.quantile(rootmoves,[0,.5,.9,1]).tolist() if rootmoves else [],
 max_point_displacement_quantiles_m=np.quantile(displacements,[0,.5,.9,1]).tolist() if displacements else [],
 displacement_quantile_scope='Root reflow stage before optional separate crest settlement; not full final operation displacement',
 smooth_contact_events=repairs,measured_crest_settlement='--crest-settle' in a,crest_points_settled=crestpoints,hidden_old_components=hidden,
 method='Complete donor shafts preserved, initial 48% softly re-laid on evaluated scalp with smooth lift/contact',
 scope='Static root/crown operation only; not artistic acceptance or full segment/clothing/animation collision proof',status='Unreviewed real 3D candidate')
(out/'root_reflow_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in (['02_ThreeQuarter'] if '--single-view' in a else ['01_Front','02_ThreeQuarter','03_Side','04_Back']):
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('NATIVE_CROWN_REFLOWED',version,changed,flush=True)
