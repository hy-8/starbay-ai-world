"""Explicit spatial shag guides with separate native strand support/styling.

Fresh actual geometry studies only. Retained Bystedt-derived hair/roots retain
CC BY-SA, source version unspecified. Guides are saved as editable evidence;
the dense output is baked, not live-linked to edits of those guides.
"""
import bpy,sys,re,json,hashlib,math
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version,source_version=args[:2];DRAFT='--draft' in args
RELAXED='--relaxed' in args
CHOPPY='--choppy-locks' in args
REFERENCE_CUT='--reference-cut' in args
SCULPTED='--sculpted-clumps' in args
ROOT_PATCHES='--root-patches' in args
SOFT_PATCHES='--soft-patches' in args
if SOFT_PATCHES and not ROOT_PATCHES:raise ValueError('--soft-patches requires --root-patches')
PATCH_FIBERS=int(args[args.index('--fibers-per-guide')+1]) if '--fibers-per-guide' in args else 420
if not 50<=PATCH_FIBERS<=2000:raise ValueError('Fibers per guide must be 50..2000')
if ROOT_PATCHES and not REFERENCE_CUT:raise ValueError('--root-patches requires --reference-cut')
if ROOT_PATCHES and SCULPTED:raise ValueError('Patch-root study must not include early-collapse sculpted flow')
if SCULPTED and not REFERENCE_CUT:raise ValueError('--sculpted-clumps requires --reference-cut')
if REFERENCE_CUT and not CHOPPY:raise ValueError('--reference-cut requires --choppy-locks')
if CHOPPY and RELAXED:raise ValueError('Choppy authored locks must not be averaged by --relaxed')
if not all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in [version,source_version]):raise ValueError(args)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh output required')
out.mkdir(parents=True);render.mkdir(parents=True)
source=ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
body=bpy.data.objects['CC0 male body • retained topology'];bpy.context.view_layer.update()
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get());center=np.array([0,-.044,1.771])
spec=[
 ('heavy crown sweep',[[-.025,-.030,1.865],[-.031,-.079,1.891],[-.078,-.126,1.865],[-.094,-.143,1.812]]),
 ('heavy upper S',[[0,-.035,1.877],[.004,-.098,1.893],[-.050,-.154,1.854],[-.028,-.169,1.810],[-.047,-.174,1.764]]),
 ('part inner fall',[[.025,-.025,1.873],[.025,-.089,1.882],[-.017,-.144,1.851],[-.030,-.169,1.813],[-.013,-.173,1.766]]),
 ('heavy temple curl',[[-.030,-.068,1.866],[-.042,-.110,1.882],[-.065,-.162,1.837],[-.044,-.169,1.791],[-.069,-.169,1.746]]),
 ('heavy eye frame',[[.015,-.074,1.869],[.011,-.132,1.878],[-.038,-.166,1.828],[-.056,-.170,1.793],[-.038,-.173,1.749]]),
 ('heavy low fringe',[[-.005,-.115,1.850],[-.020,-.149,1.845],[-.041,-.167,1.815],[-.029,-.166,1.774],[-.049,-.170,1.741]]),
 ('heavy outer frame',[[-.040,-.102,1.840],[-.059,-.149,1.845],[-.068,-.171,1.810],[-.054,-.169,1.769],[-.076,-.159,1.732]]),
 ('heavy side wave',[[-.060,-.091,1.839],[-.085,-.125,1.849],[-.096,-.153,1.806],[-.082,-.152,1.777],[-.098,-.132,1.750]]),
 ('heavy sideburn',[[-.065,-.115,1.811],[-.080,-.144,1.800],[-.084,-.160,1.779],[-.075,-.154,1.748],[-.085,-.137,1.731]]),
 ('light part sweep',[[.050,-.057,1.853],[.067,-.101,1.871],[.080,-.141,1.833],[.061,-.150,1.802],[.075,-.145,1.775]]),
 ('light forehead S',[[.040,-.101,1.850],[.047,-.143,1.846],[.073,-.156,1.814],[.056,-.163,1.780],[.071,-.160,1.753]]),
 ('light temple wave',[[.065,-.095,1.824],[.085,-.123,1.835],[.092,-.149,1.801],[.078,-.148,1.775],[.094,-.139,1.742]]),
 ('light inner fringe',[[.018,-.125,1.843],[.031,-.152,1.831],[.055,-.166,1.805],[.043,-.167,1.778],[.056,-.169,1.761]]),
 ('light crown frame',[[.057,-.021,1.850],[.075,-.060,1.874],[.091,-.108,1.846],[.081,-.133,1.809],[.094,-.134,1.780]]),
 ('short heavy crown',[[-.010,-.030,1.872],[-.019,-.075,1.895],[-.056,-.121,1.872],[-.071,-.153,1.837]]),
 ('short central crown',[[.032,-.019,1.862],[.030,-.070,1.886],[.006,-.116,1.862],[-.030,-.155,1.818]]),
 ('short upper feather',[[.013,-.055,1.865],[-.001,-.105,1.890],[-.050,-.144,1.859],[-.055,-.153,1.800]]),
 ('short light feather',[[.052,-.028,1.850],[.064,-.065,1.872],[.080,-.118,1.856],[.090,-.133,1.815]])
]
if '--design' in args:
 design_path=Path(args[args.index('--design')+1]).resolve()
 records=json.loads(design_path.read_text(encoding='utf-8-sig'))
 spec=[]
 for record in records:
  points=np.asarray(record['control_points_m'],float)
  if points.ndim!=2 or points.shape[1]!=3 or len(points)<4 or not np.isfinite(points).all():raise ValueError('Invalid spatial guide points')
  spec.append((str(record['name']),points.tolist()))
 if len(spec)<2:raise ValueError('At least two guides required')
N=64;t=np.linspace(0,1,N);rng=np.random.default_rng(100421)
def sample(p):
 p=np.asarray(p,float);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];q=t*arc[-1]
 i=np.minimum(np.maximum(np.searchsorted(arc,q,side='right')-1,0),len(p)-2);u=((q-arc[i])/(arc[i+1]-arc[i]))[:,None]
 pp=np.vstack([2*p[0]-p[1],p,2*p[-1]-p[-2]]);a,b,c,d=pp[i],pp[i+1],pp[i+2],pp[i+3]
 return .5*(2*b+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)
if CHOPPY and '--design' not in args:
 # Deliberately independent silhouettes: averaging neighboring paths erases
 # the short overlapping layers and turns the front into a smooth curtain.
 expanded=[]
 design_rng=np.random.default_rng(100426)
 for name,points in spec:
  base=np.asarray(points,float)
  base[1:,2]-=np.clip((base[1:,2]-1.867)/.026,0,1)*.008
  for layer in range(3):
   q=np.linspace(0,[.76,.91,1.0][layer],8)
   arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(base,axis=0),axis=1))]
   pts=np.stack([np.interp(q*arc[-1],arc,base[:,j]) for j in range(3)],axis=1)
   side=1 if 'light' in name else -1
   amp=design_rng.uniform(.004,.009)
   phase=design_rng.uniform(-.4,.4)+(layer-1)*.6
   pts[:,0]+=(layer-1)*.005+side*amp*np.sin(q*2.4*np.pi+phase)*np.sin(np.pi*q)
   pts[:,1]-=(.002+layer*.002)*np.sin(np.pi*q)
   pts[:,2]+=(layer-1)*.002*np.sin(np.pi*q)
   pts[-1,0]+=side*design_rng.uniform(.002,.006)
   pts[-1,2]-=design_rng.uniform(.002,.008)
   expanded.append((name+' / layer '+str(layer+1),pts.tolist()))
 spec=expanded
paths=[];design=[]
for name,points in spec:
 pts=np.array(points,float);hit,n,idx,dist=bv.find_nearest(Vector(pts[0]));pts[0]=np.array(hit+n*.0005)
 if RELAXED:
  pts[1:-1]=pts[1:-1]*.70+(pts[:-2]+pts[2:])*.15
  pts[1:,2]-=np.clip((pts[1:,2]-1.869)/.025,0,1)*.007
 s=sample(pts)
 for i,p in enumerate(s):
  hit,n,idx,dist=bv.find_nearest(Vector(p));gap=(Vector(p)-hit).dot(n)
  if gap<.002 and dist<.045:s[i]=np.array(hit+n*(.0005 if i==0 else .002))
 paths.append(s);design.append(dict(name=name,control_points_m=pts.tolist()))
paths=np.array(paths);roots=paths[:,0];counts=np.zeros(len(paths),int)
if SCULPTED:
 # Coherent lock-scale surface relief, unlike independent fiber noise.
 # The early clump convergence lets the short support cover the scalp while
 # preserving distinct overlying waves in the crown itself.
 sculpt_rng=np.random.default_rng(100428)
 for k,path in enumerate(paths):
  tang=np.gradient(path,axis=0);tang/=np.maximum(np.linalg.norm(tang,axis=1)[:,None],1e-8)
  radial=path-center;radial/=np.maximum(np.linalg.norm(radial,axis=1)[:,None],1e-8)
  normal=radial-tang*np.sum(radial*tang,axis=1)[:,None];normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-8)
  wave=sculpt_rng.uniform(.002,.005)*np.sin(t*2.6*np.pi+sculpt_rng.uniform(-.6,.6))*np.sin(np.pi*t)
  paths[k]=path+normal*wave[:,None]
  for j,pt in enumerate(paths[k]):
   hit,n,idx,dist=bv.find_nearest(Vector(pt));gap=(Vector(pt)-hit).dot(n)
   if gap<.0012 and dist<.035:paths[k,j]=np.array(hit+n*(.0005 if j==0 else .0012))
  paths[k,0]=path[0]
ob=next(o for o in bpy.data.collections['05_Hair'].objects if o.type=='CURVES');old=ob.data
p=np.empty(len(old.points)*3,np.float32);old.attributes['position'].data.foreach_get('vector',p);p=p.reshape(-1,3)
sizes=[len(c.points) for c in old.curves];back=[];support=[];styled=[];offset=0;front_count=0;repairs=0
for size in sizes:
 s=p[offset:offset+size].astype(float);offset+=size;r=s[0].copy()
 front=(r[1]<-.045 and r[2]>1.812 and abs(r[0])<.087) or (r[1]<.003 and r[2]>1.850 and abs(r[0])<.063)
 if not front:back.append(sample(s).astype(np.float32));continue
 index=front_count;front_count+=1
 if index%(3 if REFERENCE_CUT else 2)==0:
  arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(s,axis=0),axis=1))];q=t*min(float(arc[-1]),rng.uniform(.018,.033) if CHOPPY else rng.uniform(.043,.075))
  under=np.stack([np.interp(q,arc,s[:,j]) for j in range(3)],axis=1)
  for j,pt in enumerate(under):
   hit,n,idx,dist=bv.find_nearest(Vector(pt));under[j]=np.array(hit+n*(.0005 if j==0 else .0018+.0015*np.sin(np.pi*t[j])))
  support.append(under.astype(np.float32))
 if ROOT_PATCHES:continue
 if index%(2 if SCULPTED else (3 if REFERENCE_CUT else 4))!=0:continue
 distances=np.linalg.norm((roots-r)*np.array([1,1,1.2]),axis=1)
 if RELAXED or CHOPPY:
  # Keep the side part coherent while opening secondary strands between guides.
  for k0,(name,_) in enumerate(spec):
   heavy=not name.startswith('light') and 'light' not in name
   if heavy!=(r[0]<.029):distances[k0]+=1.0
 nearest=np.argsort(distances)[:2]
 if CHOPPY:
  # Choose a discrete nearby layer, then keep that wave intact.
  candidates=np.argsort(distances)[:6]
  weights=np.exp(-(distances[candidates]-distances[candidates[0]])/.012);weights/=weights.sum()
  k=int(rng.choice(candidates,p=weights))
 else:k=int(nearest[0] if rng.random()<.78 else nearest[1])
 base=paths[k].copy();counts[k]+=1
 if RELAXED:
  secondary=int(nearest[1] if k==nearest[0] else nearest[0]);w=rng.uniform(.12,.32)
  base=base*(1-w)+paths[secondary]*w
 # Original real roots spread over the scalp, then gather into authored locks.
 s=base+(r-base[0])[None,:]*(1-t[:,None])**(4.5 if SCULPTED else (1.45 if REFERENCE_CUT else 2.6))
 tangent=np.gradient(s,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-8)
 radial=s-center;radial/=np.linalg.norm(radial,axis=1)[:,None]
 normal=radial-tangent*np.sum(radial*tangent,axis=1)[:,None];normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-8)
 across=np.cross(tangent,normal);phase=rng.uniform(0,6.28)
 width=rng.normal(0,.0009 if CHOPPY else (.0023 if RELAXED else .0013));depth=rng.normal(0,.0008 if CHOPPY else (.0015 if RELAXED else .0011));env=(1-np.exp(-t*18))*(.10+.90*(1-t)**.75)
 s+=(across*width+normal*depth)*env[:,None]
 s+=normal*(.00065*np.sin(t*8+phase)*np.sin(np.pi*t))[:,None]
 s+=rng.normal(0,.0014 if RELAXED else .0007,3)[None,:]*t[:,None]**3
 if rng.random()<(.30 if RELAXED else .12):
  q=t*rng.uniform(.86,.99);s=np.stack([np.interp(q,t,s[:,j]) for j in range(3)],axis=1)
 for j,pt in enumerate(s):
  hit,n,idx,dist=bv.find_nearest(Vector(pt));gap=(Vector(pt)-hit).dot(n)
  if gap<.0008 and dist<.040:s[j]=np.array(hit+n*.0010);repairs+=1
 s[0]=r;styled.append(s.astype(np.float32))
if ROOT_PATCHES:
 # Wide donor-root offsets created a fan/sheet even for independently authored
 # guides. Grow each long lock from its own small actual-surface root patch.
 # Side/nape and short coverage remain the attributed donor derivatives.
 for k,base in enumerate(paths):
  hit,root_normal,idx,dist=bv.find_nearest(Vector(base[0]));root_center=np.array(hit);root_normal=np.array(root_normal)
  growth=base[4]-base[0];growth-=root_normal*np.dot(growth,root_normal)
  if np.linalg.norm(growth)<1e-6:growth=np.cross(root_normal,np.array([1.,0.,0.]))
  growth/=np.linalg.norm(growth);across_root=np.cross(root_normal,growth)
  for strand in range(PATCH_FIBERS):
   angle=rng.uniform(0,2*np.pi);span=(.0078 if SOFT_PATCHES else .0045)*np.sqrt(rng.random())
   probe=root_center+(growth*np.cos(angle)+across_root*np.sin(angle))*span
   hit,n,idx,dist=bv.find_nearest(Vector(probe));r=np.array(hit+n*.0005)
   s=base+(r-base[0])[None,:]*(1-t[:,None])**2.0
   tangent=np.gradient(s,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-8)
   radial=s-center;radial/=np.maximum(np.linalg.norm(radial,axis=1)[:,None],1e-8)
   normal=radial-tangent*np.sum(radial*tangent,axis=1)[:,None];normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-8)
   across=np.cross(tangent,normal)
   # A finite lock cross-section, rather than a surface-wide root fan.
   width=rng.normal(0,.0028 if SOFT_PATCHES else .00125);depth=rng.normal(0,.0014 if SOFT_PATCHES else .00085)
   env=(1-np.exp(-t*15))*(.18+.82*(1-t)**.6)
   s+=(across*width+normal*depth)*env[:,None]
   phase=rng.uniform(0,2*np.pi)
   s+=normal*(.0004*np.sin(t*7+phase)*np.sin(np.pi*t))[:,None]
   if rng.random()<(.78 if SOFT_PATCHES else .36):
    q=t*rng.uniform(.74 if SOFT_PATCHES else .90,.99);s=np.stack([np.interp(q,t,s[:,j]) for j in range(3)],axis=1)
   s+=rng.normal(0,.0006,3)[None,:]*t[:,None]**3
   for j,pt in enumerate(s):
    hit,n,idx,dist=bv.find_nearest(Vector(pt));gap=(Vector(pt)-hit).dot(n)
    if gap<.0008 and dist<.040:s[j]=np.array(hit+n*.0010);repairs+=1
   s[0]=r;styled.append(s.astype(np.float32));counts[k]+=1
col=bpy.data.collections['05_Hair'];mat=old.materials[0]
for o in list(col.objects):bpy.data.objects.remove(o,do_unlink=True)
def create(name,curves,min_radius,max_radius):
 xyz=np.array(curves,np.float32);cu=bpy.data.hair_curves.new(name);cu.add_curves([N]*len(xyz));cu.attributes['position'].data.foreach_set('vector',xyz.ravel())
 radius=rng.uniform(min_radius,max_radius,(len(xyz),1))*(1-.997*t[None,:]**3)**.65
 cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',radius.astype(np.float32).ravel());cu.materials.append(mat)
 o=bpy.data.objects.new(name,cu);col.objects.link(o)
create('Bystedt derivative • retained side and nape',back,.000033,.000045)
create('Bystedt derivative • short scalp support',support,.000028,.000039)
create('Authored spatial fringe • '+('actual scalp root patches' if ROOT_PATCHES else 'retained Bystedt roots'),styled,.000032,.000044)
nt=mat.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_HAIR_PRINCIPLED');bs.inputs['Roughness'].default_value=.34;bs.inputs['Radial Roughness'].default_value=.45
ramp=next(n for n in nt.nodes if n.type=='VALTORGB');ramp.color_ramp.elements[0].color=(.025,.0015,.0025,1);ramp.color_ramp.elements[1].color=(.085,.005,.008,1)
gc=bpy.data.collections.new('08_Authored_Spatial_Fringe');bpy.context.scene.collection.children.link(gc);gc.hide_render=True
gd=bpy.data.curves.new('Explicit spatial shag guide evidence','CURVE');gd.dimensions='3D'
for s in paths:
 sp=gd.splines.new('POLY');sp.points.add(N-1)
 for pt,v in zip(sp.points,s):pt.co=(*v,1)
go=bpy.data.objects.new('Authored guide paths • not live-linked',gd);gc.objects.link(go);go.hide_render=True
for record,count in zip(design,counts):record['assigned_visible_fibers']=int(count)
(out/'authored_fringe_design.json').write_text(json.dumps(design,indent=2),encoding='utf-8')
tx=bpy.data.texts.get('ADAPTED_HAIR_CREDITS')
if tx:tx.write('\nFurther modifications: explicit spatial frontal S guides, reduced frontal density, separate scalp support and retained side/nape. Original adapted roots and side/nape remain CC BY-SA. Hidden guide evidence is not live-linked to baked fibers.\n')
if tx and ROOT_PATCHES:tx.write('Patch-root variant: new styling roots sampled from local patches on the actual body scalp; donor side/nape and short support remain CC BY-SA derivatives.\n')
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=64 if DRAFT else 192;scene.cycles.use_denoising=False;scene.cycles_curves.shape='THICK'
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=80 if DRAFT else 100
report=dict(version=version,source=source_version,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),hair_author='Daniel Bystedt + project spatial fringe design',license='Bystedt-derived roots/support/side/nape retain CC BY-SA; source version unspecified',method='explicit spatial guide shapes; actual scalp roots, separate short support, sparse volumetric styling fibers; retain side/nape',front_roots=len(styled),support_curves=len(support),side_nape_curves=len(back),guide_count=len(paths),clearance_repairs=repairs,draft=DRAFT,samples=scene.cycles.samples,status='unreviewed actual geometry study')
report['relaxed_spatial_guides']=RELAXED
report['discrete_choppy_layers']=CHOPPY
report['reference_cut']=REFERENCE_CUT
report['sculpted_lock_relief']=SCULPTED
report['local_scalp_patch_roots']=ROOT_PATCHES
report['soft_patch_cross_sections']=SOFT_PATCHES
if ROOT_PATCHES:report['patch_fibers_per_guide']=PATCH_FIBERS
if '--design' in args:
 report['design_sha256']=hashlib.sha256(design_path.read_bytes()).hexdigest()
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
print('SPATIAL_FRINGE_SAVED',version,'VISIBLE',len(styled),'SUPPORT',len(support),flush=True)
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('SPATIAL_FRINGE_RENDERED',version,flush=True)
