"""Three independently designed thin crown accents over retained full coverage."""
import bpy,numpy as np,sys,re,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
drape='--surface-drape' in a
if not all(re.fullmatch('[A-Za-z0-9_-]+',s) for s in a[:2]):raise ValueError(a)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh small sample required')
source=ROOT/'Exports'/base/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
mat=bpy.data.objects['Bystedt layercut derivative • native root reflow'].data.materials[0]
tree=None
if drape:
 src=bpy.data.objects['Bystedt layercut derivative • native root reflow'];assert np.array_equal(np.array(src.matrix_world),np.eye(4))
 sp=np.empty((len(src.data.points),3),np.float32);src.data.attributes['position'].data.foreach_get('vector',sp.ravel());sp=sp.reshape(-1,65,3)[:,::4].reshape(-1,3)
 tree=KDTree(len(sp))
 for i,p in enumerate(sp):tree.insert(Vector(p),i)
 tree.balance()
design=[
 ('Original crown accent A',[[.016,-.030,1.869],[-.012,-.063,1.898],[-.044,-.105,1.895],[-.076,-.141,1.858],[-.055,-.161,1.810],[-.046,-.157,1.776]],.008),
 ('Original crown accent B',[[.002,.015,1.863],[-.034,-.010,1.902],[-.063,-.046,1.885],[-.076,-.061,1.840],[-.080,-.036,1.810]],.009),
 ('Original crown accent C',[[.020,-.030,1.869],[.055,-.056,1.897],[.087,-.086,1.866],[.080,-.120,1.830],[.086,-.098,1.794]],.007)]
rng=np.random.default_rng(102828);N=80;t=np.linspace(0,1,N);reports=[]
for name,knots,width in design:
 controls=np.array(knots,float)
 hit,n,_,_=bv.find_nearest(Vector(controls[0]));controls[0]=np.array(hit+n*.0004)
 def sample(at):
  u=at*(len(controls)-1);ix=np.minimum(np.floor(u).astype(int),len(controls)-2);f=(u-ix)[:,None]
  ex=np.vstack([2*controls[0]-controls[1],controls,2*controls[-1]-controls[-2]])
  aa,bb,cc,dd=ex[ix],ex[ix+1],ex[ix+2],ex[ix+3]
  return .5*(2*bb+(-aa+cc)*f+(2*aa-5*bb+4*cc-dd)*f*f+(-aa+3*bb-3*cc+dd)*f*f*f)
 guide=sample(t)
 if drape:
  # The first trial's 1.898-1.904m crest was 14-20mm above the measured
  # original 1.884m maximum, producing detached arches. Fit the proposed
  # accents against the ACTUAL existing shaft field before making fibers.
  for j in range(5,N):
   hit,_,dist=tree.find(Vector(guide[j]));normal=np.array(hit)-np.array([0,-.035,1.776]);normal/=max(np.linalg.norm(normal),1e-9)
   if dist>.0025:guide[j]=np.array(hit)+normal*.0012
  for _ in range(3):guide[6:-2]=.25*guide[5:-3]+.5*guide[6:-2]+.25*guide[7:-1]
  # Piecewise interpolation now samples this fitted path. It does not
  # silently keep using the detached original Catmull trajectory.
  def sample(at):return np.column_stack([np.interp(at,t,guide[:,k]) for k in range(3)])
 tangent=np.gradient(guide,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
 across=np.zeros_like(guide);previous=np.array([0.,1.,0.])
 for j in range(N):
  previous-=tangent[j]*np.dot(previous,tangent[j]);previous/=max(np.linalg.norm(previous),1e-9);across[j]=previous
 depth=np.cross(tangent,across);depth/=np.maximum(np.linalg.norm(depth,axis=1)[:,None],1e-9)
 fibers=[];radii=[];repairs=0
 for i in range(700):
  angle=rng.uniform(0,2*np.pi);radial=np.sqrt(rng.uniform(0,1));w=radial*np.cos(angle)*width/2;d=radial*np.sin(angle)*.0015
  tt=t*rng.uniform(.91,1);value=sample(tt)
  ac=np.column_stack([np.interp(tt,t,across[:,k]) for k in range(3)]);de=np.column_stack([np.interp(tt,t,depth[:,k]) for k in range(3)])
  profile=1-.82*tt**1.6;phase=rng.uniform(0,2*np.pi)
  value+=ac*(w*profile+.00035*np.sin(tt*9+phase)*np.sin(np.pi*tt))[:,None]+de*(d*(1-.65*tt))[:,None]
  hit,n,_,_=bv.find_nearest(Vector(value[0]));delta=np.array(hit+n*.0004)-value[0]
  value+=delta[None]*(1-t[:,None])**2
  for j in range(1,N):
   hit,n,_,dist=bv.find_nearest(Vector(value[j]));gap=(Vector(value[j])-hit).dot(n)
   if dist<.030 and gap<.0004:value[j]+=np.array(n)*(.0005-gap);repairs+=1
  fibers.append(value);radii.append(rng.uniform(.000026,.000036)*(.012+.988*(1-t**2.0))**.7)
 p=np.array(fibers,np.float32);rr=np.array(radii,np.float32);assert np.isfinite(p).all() and (rr>0).all()
 cu=bpy.data.hair_curves.new(name);cu.add_curves([N]*len(p));cu.attributes['position'].data.foreach_set('vector',p.ravel());cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',rr.ravel());cu.materials.append(mat)
 ob=bpy.data.objects.new(name,cu);bpy.context.scene.collection.objects.link(ob)
 reports.append(dict(name=name,fibers=len(p),points_per_fiber=N,discrete_body_point_repairs=repairs,root_strip_width_m=width))
out.mkdir(parents=True);render.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False;s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
(out/'accent_sample_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),design_count=len(design),surface_drape=drape,samples=reports,method='Three separate authored Catmull crown/side paths'+(', fitted against sampled actual primary shafts with 1.2mm outward offset and three smooth passes' if drape else '')+', 2100 thin original native fibers, elliptical transported sections and staggered ends, retained full source coverage/materials/lighting',status='Unreviewed actual additive small sample, not whole-head acceptance',scope='Discrete body-point guard only, not full segment/eye/clothing/animation collision or art approval'),indent=2),encoding='utf-8')
print('CROWN_ACCENT_SAMPLE',version,flush=True)
