"""Measured ID-led local undercoat flow study. Preserve follicles and other hair."""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
primary='--primary-crown' in a
if not all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:2]):raise ValueError(a)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh study required')
source=ROOT/'Exports'/base/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
name='Bystedt layercut derivative • native root reflow' if primary else 'Abhay flow derivative • real scalp sampled short support';ob=bpy.data.objects[name];cu=ob.data
lengths=np.array([c.points_length for c in cu.curves]);assert (lengths==lengths[0]).all();N=int(lengths[0])
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,N,3).astype(float);q=raw.copy();roots=raw[:,0]
ids=np.flatnonzero((roots[:,0]<-.010)&(roots[:,0]>-.090)&(roots[:,1]>-.115)&(roots[:,1]<.065)&(roots[:,2]>1.816))
if primary:
 front=np.empty(len(cu.curves),np.int32);cu.attributes['native_front_guide_index'].data.foreach_get('value',front)
 ids=np.flatnonzero((front<0)&(raw[:,-1,2]>1.803)&(roots[:,2]>1.822))
assert len(ids)>100
labels,inv=np.unique(np.round(roots[ids]/.008).astype(int),axis=0,return_inverse=True)
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get());t=np.linspace(0,1,N)
rows=[];contacts=0
for g in range(len(labels)):
 members=ids[inv==g];old=raw[members];center=old.mean(axis=0);r=center[0];phase=g*2.399963
 # Short intermediate layer bridging observed crown support toward the ear.
 side=(1 if r[0]>.014 else -1) if primary else -1
 end=np.array([side*(.093+.003*np.sin(phase)),r[1]+.014,1.785+.007*np.cos(phase)])
 anchors=[]
 for u in np.linspace(0,1,16):
  target=r*(1-u)+end*u;hit,n,_,dist=bv.find_nearest(Vector(target))
  lift=.0008+.009*np.sin(np.pi*u)**.8
  anchors.append(np.array(hit+n*lift))
 anchors[0]=r;anchors[-1]=end;anchors=np.array(anchors)
 # Interpolate a smooth Catmull path rather than independently snapping fibers.
 xx=t*(len(anchors)-1);ix=np.minimum(np.floor(xx).astype(int),len(anchors)-2);u=(xx-ix)[:,None]
 ext=np.vstack([2*anchors[0]-anchors[1],anchors,2*anchors[-1]-anchors[-2]])
 aa,bb,cc,dd=ext[ix],ext[ix+1],ext[ix+2],ext[ix+3]
 guide=.5*(2*bb+(-aa+cc)*u+(2*aa-5*bb+4*cc-dd)*u*u+(-aa+3*bb-3*cc+dd)*u*u*u)
 guide[:,1]+=.0025*np.sin(np.pi*t)*np.sin(phase)
 if primary:
  guide[:,0]+=side*.004*np.sin(2.2*np.pi*t)*np.sin(np.pi*t)
  guide[:,2]+=.0025*np.sin(2*np.pi*t)*np.sin(np.pi*t)
 # Carry the actual follicle scatter across the full path, with taper at end.
 residual=old-center[None];root_residual=residual[:,0]
 v=guide[None]+root_residual[:,None]*(1-.65*t)[None,:,None]+(residual-root_residual[:,None])*.15*(1-t)[None,:,None]
 for k in range(len(members)):
  for j in range(1,N-1):
   hit,n,_,dist=bv.find_nearest(Vector(v[k,j]));gap=(Vector(v[k,j])-hit).dot(n)
   if dist<.012 and gap<.0004:v[k,j]+=np.array(n)*(.0006-gap);contacts+=1
 v[:,0]=old[:,0];q[members]=v
 rows.append(dict(fibers=len(members),median_length_m=float(np.median(np.linalg.norm(np.diff(v,axis=1),axis=2).sum(axis=1))),max_displacement_m=float(np.linalg.norm(v-old,axis=2).max())))
mask=np.zeros(len(raw),bool);mask[ids]=True
assert np.array_equal(q[:,0],raw[:,0]) and np.array_equal(q[~mask],raw[~mask]) and np.isfinite(q).all()
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attribute='native_crown_flow' if primary else 'native_undercoat_flow'
ob.data.attributes.new(attribute,'BOOLEAN','CURVE').data.foreach_set('value',mask)
out.mkdir(parents=True);render.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
camera=bpy.data.objects['03_Side'].copy();camera.data=camera.data.copy();s.collection.objects.link(camera);camera.name='05_OppositeSide'
reflect=Matrix.Diagonal((-1.,1.,1.,1.));camera.matrix_world=reflect@camera.matrix_world@reflect
for name in ['05_OppositeSide','02_ThreeQuarter']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
(out/'undercoat_flow_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),changed_object=ob.name,changed_fibers=len(ids),sections=rows,primary_crown=primary,selection='Non-frontal native tips above z1.803 and follicles above z1.822' if primary else 'Opposite upper-side Abhay follicles',all_roots_exactly_retained=True,unselected_fibers_exactly_retained=True,other_native_objects_unchanged=True,discrete_contact_events=contacts,method='Actual 8mm root sections, intermediate side layer from measured scalp arcs; primary mode adds small coherent waves and leaves the designed fringe unchanged',status='Unreviewed paired actual 3D study',scope='Static discrete body points only; not full hair segments/eye/clothing/animation or art acceptance'),indent=2),encoding='utf-8')
print('NATIVE_UNDERCOAT_FLOW_SAVED',version,len(ids),len(rows),flush=True)
