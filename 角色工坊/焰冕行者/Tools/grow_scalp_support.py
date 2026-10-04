"""Sample real scalp surface to fill uncovered roots using native flow directions.

This is local source-derived geometry, not image output or a claim of art
acceptance. Original/licensed guides and prior files remain unchanged.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version,source_version,flow_version=args[:3]
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in args[:3]):raise ValueError(args)
out,render=ROOT/'Exports'/version,ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh output required')
source=ROOT/'Exports'/source_version/'Ember_Regent.blend'
flow=ROOT/'Exports'/flow_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(flow),use_scripts=False)
native=next(o for o in bpy.data.objects if not o.hide_render and o.name.startswith('Abhay Royalty'))
N0=len(native.data.curves[0].points)
a=np.empty(len(native.data.points)*3,np.float32);native.data.attributes['position'].data.foreach_get('vector',a);a=a.reshape(-1,N0,3)
roots=a[:,0].copy();directions=a[:,min(8,N0-1)]-a[:,0]
kd=KDTree(len(roots))
for i,p in enumerate(roots):kd.insert(Vector(p),i)
kd.balance()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
body=bpy.data.objects['CC0 male body • retained topology'];dg=bpy.context.evaluated_depsgraph_get()
if not np.allclose(np.array(body.matrix_world),np.eye(4)):raise RuntimeError('Expected world-aligned retained body')
evaluated=body.evaluated_get(dg);mesh=evaluated.to_mesh();mesh.calc_loop_triangles()
bv=BVHTree.FromObject(body,dg)
verts=np.array([v.co[:] for v in mesh.vertices],float)
tri=np.array([t.vertices[:] for t in mesh.loop_triangles],int)
xyz=verts[tri];c=xyz.mean(axis=1)
mask=(c[:,2]>1.826)|((c[:,1]>.010)&(c[:,2]>1.786))|((np.abs(c[:,0])>.069)&(c[:,1]>-.072)&(c[:,2]>1.790))
xyz=xyz[mask];area=np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1)*.5
if len(xyz)<50 or not np.isfinite(area).all():raise RuntimeError('Scalp region selection failed')
rng=np.random.default_rng(100462);count=14000;N=40;t=np.linspace(0,1,N)
ids=rng.choice(len(xyz),size=count,p=area/area.sum());bary=rng.random((count,2))
bary[bary.sum(axis=1)>1]=1-bary[bary.sum(axis=1)>1]
samples=xyz[ids,0]+bary[:,0,None]*(xyz[ids,1]-xyz[ids,0])+bary[:,1,None]*(xyz[ids,2]-xyz[ids,0])
paths=[];min_root=1.;max_root=0.
for i,p in enumerate(samples):
 hit,normal,face,dist=bv.find_nearest(Vector(p));root=hit+normal*.00055
 neighbors=kd.find_n(hit,6)
 weights=np.array([1/(n[2]+.003)**2 for n in neighbors]);weights/=weights.sum()
 direction=np.sum(np.array([directions[n[1]] for n in neighbors])*weights[:,None],axis=0)
 heading=Vector(direction);heading-=normal*heading.dot(normal)
 if heading.length<1e-6:
  heading=Vector((float(p[0]-.020),-.035,-.020));heading-=normal*heading.dot(normal)
 heading.normalize();length=rng.uniform(.028,.047)
 q=np.empty((N,3),np.float32);q[0]=root
 position=hit;lift=rng.uniform(.0012,.0026)
 for j in range(1,N):
  candidate=position+heading*(length/(N-1))
  nh,nn,face,dist=bv.find_nearest(candidate)
  # Parallel transport the tangential source flow over the true scalp.
  heading-=nn*heading.dot(nn)
  if heading.length>1e-8:heading.normalize()
  position=nh
  q[j]=np.array(nh+nn*(.00055+lift*np.sin(np.pi*t[j])+.00075*t[j]))
 paths.append(q)
 gap=(root-hit).dot(normal);min_root=min(min_root,gap);max_root=max(max_root,gap)
evaluated.to_mesh_clear()
paths=np.array(paths,np.float32)
if not np.isfinite(paths).all():raise RuntimeError('Invalid support geometry')
mat=next(o for o in bpy.data.objects if not o.hide_render and o.type=='CURVES' and o.name.startswith('Authored')).data.materials[0]
cu=bpy.data.hair_curves.new('Surface sampled source-flow scalp support');cu.add_curves([N]*count)
cu.attributes['position'].data.foreach_set('vector',paths.ravel())
radius=rng.uniform(.000027,.000038,(count,1))*(1-.997*t[None,:]**3)**.65
cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',radius.astype(np.float32).ravel());cu.materials.append(mat)
col=bpy.data.collections.new('05_Surface_Sampled_Foundation');bpy.context.scene.collection.children.link(col)
ob=bpy.data.objects.new('Abhay flow derivative • real scalp sampled short support',cu);col.objects.link(ob)
txt=bpy.data.texts.new('SCALP_SUPPORT_SOURCE_CREDIT');txt.write('Short support sampled from the actual retained CC0 scalp. Tangential directions adapted from Realistic Hair by Abhay Pratap, BlenderKit Royalty Free, not CC0. Source and derived geometry local. Original frontal design, Ddr Rcs Royalty Free rear and Bystedt CC BY-SA support retained. Unapproved static study.\n')
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=64 if '--draft' in args else 192;scene.cycles.use_denoising=False;scene.cycles_curves.shape='THICK'
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=80 if '--draft' in args else 100
out.mkdir(parents=True);render.mkdir(parents=True)
report=dict(version=version,source=source_version,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),flow_source=flow_version,flow_sha256=hashlib.sha256(flow.read_bytes()).hexdigest(),method='Area-weighted real scalp roots; nearest-six native flow tangents, parallel transport on real scalp; short support only',additional_native_curves=count,points_per_curve=N,root_gap_min_m=min_root,root_gap_max_m=max_root,scalp_triangle_count=len(xyz),scalp_area_m2=float(area.sum()),draft='--draft' in args,samples=scene.cycles.samples,status='unreviewed actual geometric study',collision_scope='Exact root attachment and centerline surface projection; not exhaustive fibers/clothing/motion verification',license='Abhay Pratap BlenderKit Royalty Free flow derivative; Ddr Rcs Royalty Free rear; Bystedt CC BY-SA short support retained; project original frontal')
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('SURFACE_SCALP_SUPPORT_RENDERED',version,count,flush=True)
