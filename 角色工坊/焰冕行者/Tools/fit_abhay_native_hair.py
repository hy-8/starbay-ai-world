"""Fit and scissor real Abhay Pratap spline hair into a local native groom.

BlenderKit Royalty Free, not CC0. Source and derivative geometry stay local.
Read source with automatic scripts disabled. No image-based character output.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version,body_version=args[:2]
LAYERED='--layered' in args
FOUNDATION='--scalp-foundation' in args
if FOUNDATION and (LAYERED or '--fringe-source' in args):raise ValueError('Foundation retains the source styling, not the layered replacement')
if FOUNDATION and body_version!='flowgroom02':raise ValueError('Foundation experiment requires reviewed flowgroom02 with unchanged spatialfringe17 front')
fringe_version=args[args.index('--fringe-source')+1] if '--fringe-source' in args else None
if fringe_version and not re.fullmatch('[A-Za-z0-9_-]+',fringe_version):raise ValueError(fringe_version)
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in args[:2]):raise ValueError(args)
out,render=ROOT/'Exports'/version,ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh output required')
out.mkdir(parents=True);render.mkdir(parents=True)
asset=ROOT/'Source/BlenderKitResearch/Abhay_RealisticHair.blend'
source=ROOT/'Exports'/body_version/'Ember_Regent.blend'
expected='016558262252e29d841eadc87cc12554d26b6800734939deac693c9cf2bb9c1e'
if hashlib.sha256(asset.read_bytes()).hexdigest()!=expected:raise RuntimeError('Author source hash mismatch')
bpy.ops.wm.open_mainfile(filepath=str(asset),use_scripts=False);bpy.context.view_layer.update()
paths=[]
for ob in bpy.data.objects:
 if ob.type!='CURVE':continue
 for sp in ob.data.splines:
  if sp.type!='POLY':raise RuntimeError('Expected inspected poly splines')
  p=np.array([ob.matrix_world@Vector(pt.co[:3]) for pt in sp.points],float)
  paths.append((ob.name,p.copy()))
print('ACTUAL_SOURCE_SPLINES',len(paths),flush=True)
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
body=bpy.data.objects['CC0 male body • retained topology']
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
visible=[o for o in bpy.data.objects if o.type=='CURVES' and not o.hide_render]
mat=next(o for o in visible if o.name.startswith('Authored')).data.materials[0].copy()
for o in visible:
 if (FOUNDATION and 'short scalp' in o.name) or (not FOUNDATION and 'short scalp' not in o.name):o.hide_render=True;o.hide_viewport=True
N=72;t=np.linspace(0,1,N);rng=np.random.default_rng(100451)
fibers=[];radii=[];trimmed=0;repairs=0;roots_repaired=0;low_root_length_cuts=0
def resample(p,fraction=1.):
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
 keep=np.r_[True,np.diff(arc)>1e-8];arc=arc[keep];p=p[keep]
 if len(p)<3:return None
 return np.stack([np.interp(t*arc[-1]*fraction,arc,p[:,j]) for j in range(3)],axis=1)
for index,(name,p) in enumerate(paths):
 p=p*np.array([1.06,1.22,1.])+np.array([0,-.080,1.382])
 r=p[0];end=p[-1]
 front=name in ['Mesh','Mesh.001','Mesh.004','Mesh.005']
 if LAYERED:
  # Keep natural crown flow as a short overlapping layer above the separate
  # brow fringe. Rear heights vary coherently with root location, plus a small
  # per-fiber variation, rather than leaving a level bob hem.
  if front:target_z=1.798+.024*np.sin(r[0]*32+r[1]*15)+rng.uniform(-.008,.008)
  else:target_z=1.651+.080*np.clip((r[2]-1.780)/.085,0,1)+.012*np.sin(r[0]*47+r[1]*20)+rng.uniform(-.010,.010)
 elif front:target_z=rng.uniform(1.738,1.797)
 elif end[1]>.005:target_z=rng.uniform(1.624,1.748)
 else:target_z=rng.uniform(1.680,1.756)
 crossing=np.flatnonzero(p[:,2]<target_z)
 if len(crossing) and crossing[0]>3:
  j=int(crossing[0]);a,b=p[j-1,2],p[j,2]
  f=np.clip((a-target_z)/max(a-b,1e-8),0,1)
  p=np.vstack([p[:j],p[j-1]+(p[j]-p[j-1])*f]);trimmed+=1
 elif LAYERED:
  # A root already below target_z must still be cut by actual arc length.
  # The earlier study accidentally retained those entire long side strands.
  minimum_height=1.676 if r[1]<-.030 else 1.630
  max_length=np.clip((r[2]-minimum_height)*1.18,.035,.145)
  if front:max_length=min(max_length,.075)
  arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
  if arc[-1]>max_length:
   p=resample(p,max_length/arc[-1]);low_root_length_cuts+=1
 base=resample(p)
 if base is None:continue
 if FOUNDATION:
  # Natural source supplies short surface-following flow only, never its bob
  # silhouette. Keep styled original front and rear visible from the source.
  arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(base,axis=0),axis=1))]
  base=resample(base,min(1.,(.037+.008*np.sin(r[0]*36+r[1]*20))/arc[-1]))
 hit,n,face,dist=bv.find_nearest(Vector(base[0]));true_root=np.array(hit+n*.0005)
 base+=(true_root-base[0])[None,:]*(1-t[:,None])**2.0
 if FOUNDATION:
  for j,point in enumerate(base):
   hit,n,face,dist=bv.find_nearest(Vector(point))
   base[j]=np.array(hit+n*(.0005+.0025*np.sin(np.pi*t[j])+.0009*t[j]))
 if LAYERED:
  # Restrained spatially coherent waves retain the source's native flow.
  # Root-dependent phase produces real overlapping layers, not 9,870
  # independent noisy curls. Roots remain on the actual scalp.
  phase=r[0]*46+r[1]*24
  env=np.sin(np.pi*t)
  base[:,0]+=.0036*np.sin(t*2.6*np.pi+phase)*env
  base[:,1]+=.0030*np.cos(t*2.3*np.pi+phase)*env
  base[:,2]+=.0028*np.sin(t*2.1*np.pi+phase)*env
  # Reduce the round lower side mass and keep the ear-front region short.
  low=np.clip((1.795-base[:,2])/.110,0,1)
  base[:,0]*=1-.13*low*t
  if r[1]<-.030 and abs(r[0])>.055:
   base[:,1]+=.017*t**2
 roots_repaired+=1
 for j,point in enumerate(base):
  hit,n,face,dist=bv.find_nearest(Vector(point));gap=(Vector(point)-hit).dot(n)
  if j and gap<.0015 and dist<.040:base[j]=np.array(hit+n*.0018);repairs+=1
 tangent=np.gradient(base,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-8)
 radial=base-np.array([0,-.044,1.771]);radial/=np.maximum(np.linalg.norm(radial,axis=1)[:,None],1e-8)
 normal=radial-tangent*np.sum(radial*tangent,axis=1)[:,None]
 normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-8)
 across=np.cross(tangent,normal)
 for k in range(4):
  q=base.copy()
  offset=(across*rng.normal(0,.00042)+normal*rng.normal(0,.00030))
  q+=offset*np.sin(np.pi*t[:,None])
  q+=normal*(.00025*np.sin(t*7+rng.uniform(0,6.28))*np.sin(np.pi*t))[:,None]
  if k:
   q=resample(q,rng.uniform(.94,1.))
  q[0]=true_root
  fibers.append(q.astype(np.float32))
  radii.append((rng.uniform(.000031,.000041)*(1-.997*t**3)**.65).astype(np.float32))
col=bpy.data.collections.new('05_Abhay_Native_Scissor_Study');bpy.context.scene.collection.children.link(col)
cu=bpy.data.hair_curves.new('Abhay Pratap derivative • real poly splines to native fibers')
cu.add_curves([N]*len(fibers));cu.attributes['position'].data.foreach_set('vector',np.array(fibers).ravel())
cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.array(radii).ravel());cu.materials.append(mat)
ob=bpy.data.objects.new('Abhay Royalty Free hair derivative • fitted scissor study',cu);col.objects.link(ob)
if FOUNDATION:
 # The new foundation permits lowering the overlying authored crown slightly
 # while retaining every crown path and all fringe/nape ends.
 for frontob in visible:
  if not frontob.name.startswith('Authored'):continue
  design_path=ROOT/'Exports/spatialfringe17/authored_fringe_design.json'
  design=json.loads(design_path.read_text(encoding='utf-8'))
  sizes=[len(c.points) for c in frontob.data.curves]
  if len(set(sizes))!=1 or sum(r['assigned_visible_fibers'] for r in design)!=len(sizes):raise RuntimeError('Foundation expects unchanged spatialfringe17 frontal paths')
  fn=sizes[0];xyz=np.empty(len(frontob.data.points)*3,np.float32);frontob.data.attributes['position'].data.foreach_get('vector',xyz);xyz=xyz.reshape(-1,fn,3)
  offset=0;ft=np.linspace(0,1,fn)
  for record in design:
   count=record['assigned_visible_fibers']
   if 'segmented crown' in record['name']:
    q=xyz[offset:offset+count];envelope=np.sin(np.pi*ft)
    q[:,:,2]-=.004*envelope
    q[:,:,0]*=1-.045*envelope
   offset+=count
  frontob.data.attributes['position'].data.foreach_set('vector',xyz.ravel())
fringe_count=0
if fringe_version:
 # Extract only contiguous original brow/temple subsets. Importing the entire
 # groom would reintroduce its rejected broad crown and duplicate coverage.
 fpath=ROOT/'Exports'/fringe_version/'Ember_Regent.blend'
 design=json.loads((ROOT/'Exports'/fringe_version/'authored_fringe_design.json').read_text(encoding='utf-8'))
 canonical='Authored spatial fringe • actual scalp root patches'
 with bpy.data.libraries.load(str(fpath),link=False) as (available,loaded):
  if canonical not in available.objects:raise RuntimeError('Expected authored fringe object absent')
  loaded.objects=[canonical]
 fob=loaded.objects[0];sizes=[len(c.points) for c in fob.data.curves]
 if len(set(sizes))!=1 or sum(x['assigned_visible_fibers'] for x in design)!=len(sizes):raise RuntimeError('Fringe design/geometry count mismatch')
 fn=sizes[0];xyz=np.empty(len(fob.data.points)*3,np.float32);fob.data.attributes['position'].data.foreach_get('vector',xyz);xyz=xyz.reshape(-1,fn,3)
 rad=np.empty(len(fob.data.points),np.float32);fob.data.attributes['radius'].data.foreach_get('value',rad);rad=rad.reshape(-1,fn)
 indices=[];offset=0
 for record in design:
  count=record['assigned_visible_fibers']
  if 'segmented crown' not in record['name']:indices.extend(range(offset,offset+count))
  offset+=count
 fringe_count=len(indices);fcu=bpy.data.hair_curves.new('Original lower fringe subset • crown excluded')
 fcu.add_curves([fn]*fringe_count);fcu.attributes['position'].data.foreach_set('vector',xyz[indices].ravel())
 fcu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',rad[indices].ravel());fcu.materials.append(mat)
 newob=bpy.data.objects.new('Original asymmetric brow and temple fringe • native fibers',fcu);col.objects.link(newob);newob.matrix_world=fob.matrix_world.copy()
 bpy.data.objects.remove(fob,do_unlink=True)
credits=bpy.data.texts.new('ABHAY_HAIR_SOURCE_CREDIT')
credits.write('Realistic Hair by Abhay Pratap, BlenderKit Royalty Free, not CC0. Original source poly spline fibers fitted to male scalp, cut along growth and converted to native CURVES with fine neighboring fibers. Source/derived geometry kept local. Retained source includes Bystedt CC BY-SA support, hidden in the foundation study, and Ddr Rcs Royalty Free rear, visible only in the foundation study. Unapproved static study, no animation/game validation.\n')
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=64 if '--draft' in args else 192;scene.cycles.use_denoising=False
scene.cycles_curves.shape='THICK';scene.render.resolution_x=1200;scene.render.resolution_y=1400
scene.render.resolution_percentage=80 if '--draft' in args else 100
report=dict(version=version,source_body=body_version,author='Abhay Pratap',asset='Realistic Hair',
            license='Abhay Pratap BlenderKit Royalty Free, not CC0; Bystedt support CC BY-SA; foundation also retains Ddr Rcs Royalty Free rear',
            asset_sha256=expected,body_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            original_splines=len(paths),native_fibers=len(fibers),actually_trimmed_splines=trimmed,
            layered_growth_cuts=LAYERED,low_root_arc_length_cuts=low_root_length_cuts,
            natural_scalp_foundation=FOUNDATION,
            original_brow_fringe_source=fringe_version,original_brow_fringe_fibers=fringe_count,
            roots_attached=roots_repaired,base_body_clearance_repairs=repairs,
            method='Actual existing poly fiber shapes, affine scalp fitting, along-growth cuts, native CURVES conversion',
            draft='--draft' in args,samples=scene.cycles.samples,status='unreviewed real-geometry alternative',
            collision_scope='Base centerline clearance only; no exhaustive fine-fiber/clothing/motion test')
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('ABHAY_NATIVE_STUDY_RENDERED',version,len(fibers),flush=True)
