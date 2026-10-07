"""Return positive-side frontal follicles to a loose same-side curtain flow."""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:2]):raise ValueError(a)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh curtain study required')
source=ROOT/'Exports'/base/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float);q=raw.copy();root=raw[:,0]
front=np.empty(len(cu.curves),np.int32);cu.attributes['native_front_guide_index'].data.foreach_get('value',front)
groups=np.unique(front[(front>=0)&(root[:,0]>.022)])
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get());t=np.linspace(0,1,65)
mask=np.zeros(len(raw),bool);rows=[];contacts=0
def smooth(v):v=np.clip(v,0,1);return v*v*(3-2*v)
def sample(c):
 c=np.array(c);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(c,axis=0),axis=1))]
 at=t*arc[-1];ix=np.minimum(np.maximum(np.searchsorted(arc,at,side='right')-1,0),len(c)-2)
 u=((at-arc[ix])/np.maximum(arc[ix+1]-arc[ix],1e-9))[:,None]
 ext=np.vstack([2*c[0]-c[1],c,2*c[-1]-c[-2]]);aa,bb,cc,dd=ext[ix],ext[ix+1],ext[ix+2],ext[ix+3]
 return .5*(2*bb+(-aa+cc)*u+(2*aa-5*bb+4*cc-dd)*u*u+(-aa+3*bb-3*cc+dd)*u*u*u)
for g in groups:
 members=np.flatnonzero((front==g)&(root[:,0]>.022));old=raw[members];center=old.mean(axis=0);r=center[0];phase=g*2.399963
 ex=float(np.clip(.057+.40*r[0]+.003*np.sin(phase),.062,.101))
 ez=1.777-.052*smooth((ex-.062)/.033)+.005*np.cos(phase)
 end=np.array([ex,-.180+.40*ex,ez]);delta=end-r;anchors=[r]
 for u,lift in [(.21,.009),(.47,.014)]:
  hit,n,_,_=bv.find_nearest(Vector(r+delta*u));anchors.append(np.array(hit+n*lift))
 anchors.extend([end+np.array([.009,.010,.027]),end])
 guide=sample(anchors);guide[:,0]+=.005*np.sin(2.2*np.pi*t)*np.sin(np.pi*t)
 guide[:,1]+=.003*np.sin(2*np.pi*t+phase*.2)*np.sin(np.pi*t)
 residual=old-center[None];fade=1-.48*smooth(t/.75)
 values=guide[None]+residual*fade[None,:,None]
 for k in range(len(members)):
  for _ in range(2):
   correction=np.zeros((65,3))
   for j in range(1,64):
    if values[k,j,2]<1.794:continue
    hit,n,_,dist=bv.find_nearest(Vector(values[k,j]));gap=(Vector(values[k,j])-hit).dot(n)
    if dist<.014 and gap<.0004:
     d=np.array(n)*(.0006-gap);contacts+=1
     for l in range(max(1,j-2),min(65,j+3)):correction[l]+=d*np.exp(-.5*((l-j)/1.3)**2)
   values[k]+=correction
 values[:,0]=old[:,0];q[members]=values;mask[members]=True
 rows.append(dict(fibers=len(members),max_displacement_m=float(np.linalg.norm(values-old,axis=2).max())))
assert np.array_equal(q[:,0],raw[:,0]) and np.array_equal(q[~mask],raw[~mask]) and np.isfinite(q).all()
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
ob.data.attributes.new('native_curtain_balance','BOOLEAN','CURVE').data.foreach_set('value',mask)
out.mkdir(parents=True);render.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
camera=bpy.data.objects['03_Side'].copy();camera.data=camera.data.copy();s.collection.objects.link(camera);camera.name='05_OppositeSide'
reflect=Matrix.Diagonal((-1.,1.,1.,1.));camera.matrix_world=reflect@camera.matrix_world@reflect
for name in ['01_Front','02_ThreeQuarter','03_Side','05_OppositeSide']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
(out/'curtain_balance_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),changed_fibers=int(mask.sum()),sections=rows,all_roots_exactly_retained=True,unselected_primary_exactly_retained=True,other_hair_unchanged=True,discrete_contact_events=contacts,method='Positive-side frontal follicles x>.022 return to same-side scalp-fitted curtain arcs, outside-iris longer face frames and small coherent wave; previous side/back cut unchanged',status='Unreviewed actual curtain-balance study',scope='Discrete upper-head body guard only, not full segments/eye/clothing/animation or art acceptance'),indent=2),encoding='utf-8')
print('NATIVE_CURTAIN_BALANCED',version,int(mask.sum()),len(rows),flush=True)
