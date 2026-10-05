"""Small side-part study using actual upper-side follicles and scalp lead arcs."""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:2]):raise ValueError(a)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh study required')
source=ROOT/'Exports'/base/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float);q=raw.copy();roots=raw[:,0];tips=raw[:,-1]
front=np.empty(len(cu.curves),np.int32);cu.attributes['native_front_guide_index'].data.foreach_get('value',front)
ids=np.flatnonzero((roots[:,0]<-.023)&(roots[:,0]>-.085)&(roots[:,1]<.03)&(roots[:,1]>-.105)&(roots[:,2]>1.827)&(front<0))
assert len(ids)>100,'Upper side follicles missing'
labels,inv=np.unique(np.round(roots[ids]/.006).astype(int),axis=0,return_inverse=True)
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
t=np.linspace(0,1,65);rows=[];contact=0
for g in range(len(labels)):
 members=ids[inv==g];old=raw[members];center=old.mean(axis=0);r=center[0];phase=g*2.399963
 # Follow the observed opposite-side crown toward temple/ear, ending above ear.
 end=np.array([-.095-.004*np.sin(phase),r[1]+.022,1.790+.009*np.sin(phase)])
 anchors=[]
 for u in np.linspace(0,1,12):
  target=r*(1-u)+end*u
  hit,n,_,dist=bv.find_nearest(Vector(target))
  lift=.0015+.009*np.sin(np.pi*u)**1.1
  anchors.append(np.array(hit+n*lift))
 anchors[0]=r;anchors[-1]=end
 x=np.linspace(0,1,len(anchors));anchors=np.array(anchors)
 guide=np.column_stack([np.interp(t,x,anchors[:,j]) for j in range(3)])
 guide[:,0]-=.003*np.sin(2*np.pi*t)*np.sin(np.pi*t)
 guide[:,1]+=.004*np.sin(np.pi*t)*np.sin(phase)
 residual=old-center[None]
 # Preserve actual root scatter; progressively replace old long-path scatter.
 fade=(1-t)**2*.8+.2
 v=guide[None]+residual*fade[None,:,None]
 for k in range(len(members)):
  for j in range(1,64):
   hit,n,_,dist=bv.find_nearest(Vector(v[k,j]));gap=(Vector(v[k,j])-hit).dot(n)
   if dist<.012 and gap<.0004:v[k,j]+=np.array(n)*(.0006-gap);contact+=1
 v[:,0]=old[:,0];q[members]=v
 rows.append(dict(fibers=len(members),max_displacement_m=float(np.linalg.norm(v-old,axis=2).max())))
assert np.array_equal(q[:,0],raw[:,0])
mask=np.ones(len(raw),bool);mask[ids]=False;assert np.array_equal(q[mask],raw[mask])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr=ob.data.attributes.new('native_part_cover','BOOLEAN','CURVE');attr.data.foreach_set('value',~mask)
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
(out/'part_cover_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),changed_fibers=len(ids),sections=rows,all_roots_exactly_retained=True,unselected_primary_exactly_retained=True,short_support_unchanged=True,discrete_contact_events=contact,method='Actual 6mm root sections redirected along measured upper-side scalp arcs with short ear-level feather tips',status='Unreviewed paired actual 3D study',scope='Static discrete body points only, not whole-segment/eye/clothing/animation or art acceptance'),indent=2),encoding='utf-8')
print('NATIVE_PART_STUDY_SAVED',version,len(ids),len(rows),flush=True)
