"""Per-follicle scalp lead arcs, preserving accepted local fringe ends."""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
scalp_wave='--scalp-wave' in a
if not all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:2]):raise ValueError(a)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh per-follicle study')
source=ROOT/'Exports'/base/'Ember_Regent.blend';bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float);q=raw.copy();labels=np.empty(len(cu.curves),np.int32);cu.attributes['native_front_guide_index'].data.foreach_get('value',labels)
ids=np.flatnonzero(labels>=0);mask=labels>=0;t=np.linspace(0,1,65);contacts=0;displacements=[]
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def sample(c):
 c=np.array(c);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(c,axis=0),axis=1))]
 at=t*arc[-1];ix=np.minimum(np.maximum(np.searchsorted(arc,at,side='right')-1,0),len(c)-2)
 u=((at-arc[ix])/np.maximum(arc[ix+1]-arc[ix],1e-9))[:,None]
 ext=np.vstack([2*c[0]-c[1],c,2*c[-1]-c[-2]]);aa,bb,cc,dd=ext[ix],ext[ix+1],ext[ix+2],ext[ix+3]
 return .5*(2*bb+(-aa+cc)*u+(2*aa-5*bb+4*cc-dd)*u*u+(-aa+3*bb-3*cc+dd)*u*u*u)
for index in ids:
 old=raw[index];r=old[0];end=old[-1];phase=labels[index]*2.399963+r[0]*350+r[1]*280
 controls=[r]
 for u,lift in [(.19,.005),(.45,.009)]:
  hit,n,_,_=bv.find_nearest(Vector(r*(1-u)+end*u))
  controls.append(np.array(hit+n*(lift+.001*np.sin(phase))))
 side=1 if end[0]>0 else -1
 controls.extend([end+np.array([-side*.003,.006,.025]),end])
 guide=sample(controls)
 guide[:,0]+=side*.004*np.sin(2.2*np.pi*t)*np.sin(np.pi*t)
 guide[:,1]+=.0006*np.sin(4*np.pi*t+phase)*np.sin(np.pi*t)
 if scalp_wave:
  tangent=np.gradient(guide,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-8)
  normal=guide-np.array([0,-.035,1.776]);normal-=tangent*np.sum(normal*tangent,axis=1)[:,None];normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-8)
  across=np.cross(tangent,normal);across/=np.maximum(np.linalg.norm(across,axis=1)[:,None],1e-8)
  root_phase=np.arctan2(r[0],r[1]+.060)*2+(r[2]-1.822)*90
  wave=.010*np.sin(2.5*np.pi*t+root_phase)*np.sin(np.pi*t)**1.1
  guide+=across*wave[:,None]+normal*(.003*np.cos(root_phase)*np.sin(np.pi*t))[:,None]
 weight=smooth((old[:,2]-1.785)/.025)*smooth((t-.04)/.16)*(1-smooth((t-.70)/.28))
 values=old*(1-weight[:,None])+guide*weight[:,None]
 for _ in range(2):
  correction=np.zeros_like(values)
  for j in range(4,62):
   if weight[j]<.001 or values[j,2]<1.790:continue
   hit,n,_,dist=bv.find_nearest(Vector(values[j]));gap=(Vector(values[j])-hit).dot(n)
   if dist<.014 and gap<.0004:
    d=np.array(n)*(.0006-gap);contacts+=1
    for l in range(max(4,j-2),min(62,j+3)):correction[l]+=d*np.exp(-.5*((l-j)/1.3)**2)*float(weight[l]>.001)
  values+=correction
 values[:4]=old[:4];values[62:]=old[62:];q[index]=values
 displacements.append(float(np.linalg.norm(values-old,axis=1).max()))
assert np.array_equal(q[:,:4],raw[:,:4]) and np.array_equal(q[:,62:],raw[:,62:]) and np.array_equal(q[~mask],raw[~mask]) and np.isfinite(q).all()
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
ob.data.attributes.new('native_individual_root_flow','BOOLEAN','CURVE').data.foreach_set('value',mask)
out.mkdir(parents=True);render.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
camera=bpy.data.objects['03_Side'].copy();camera.data=camera.data.copy();s.collection.objects.link(camera);camera.name='05_OppositeSide'
r=Matrix.Diagonal((-1.,1.,1.,1.));camera.matrix_world=r@camera.matrix_world@r
for name in ['01_Front','02_ThreeQuarter','05_OppositeSide']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
(out/'individual_root_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),changed_fibers=len(ids),scalp_wave=scalp_wave,max_displacement_quantiles_m=np.quantile(displacements,[0,.5,.9,1]).tolist(),first_four_and_last_three_points_exact=True,unselected_primary_exact=True,other_hair_unchanged=True,discrete_smooth_contact_events=contacts,method='Each of 11092 actual frontal follicles gets its own nearest-scalp lead arcs, small coherent same-flow wave and elevated-shaft blend; retain original root prefix/free tips and all side/back hair'+('; spatially coherent 10mm tangent-cross wave and 3mm depth variation phased by actual root scalp angle/elevation' if scalp_wave else ''),status='Unreviewed actual per-follicle study',scope='Discrete upper-body guard only; not complete segments/eye/clothing/animation or art approval'),indent=2),encoding='utf-8')
print('INDIVIDUAL_NATIVE_ROOT_SAVED',version,len(ids),flush=True)
