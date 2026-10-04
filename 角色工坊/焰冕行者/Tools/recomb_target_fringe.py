"""Rebuild the front flow on the actual character scalp, in a fresh scene.

This is a geometry study, not an image replacement. Existing Bystedt-derived
side/back fibers retain their license; dense groom is editable but baked.
"""
import bpy,sys,re,json,hashlib,math
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version,source_version=args[:2]
DRAFT='--draft' in args
LOCKS='--locks' in args
LOOSE='--loose-fringe' in args
VOLUME='--volume-locks' in args
ANATOMICAL='--anatomical-flow' in args
TIERED='--tiered-cut' in args
if LOOSE and not LOCKS:raise ValueError('--loose-fringe requires --locks')
if VOLUME and not LOOSE:raise ValueError('--volume-locks requires --locks --loose-fringe')
if ANATOMICAL and not VOLUME:raise ValueError('--anatomical-flow requires --volume-locks')
if TIERED and not ANATOMICAL:raise ValueError('--tiered-cut requires --anatomical-flow')
if not all(re.fullmatch('[A-Za-z0-9_-]+',s) for s in [version,source_version]):raise ValueError(args)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh output required')
out.mkdir(parents=True);render.mkdir(parents=True)
source=ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
body=bpy.data.objects['CC0 male body • retained topology'];bpy.context.view_layer.update()
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
center=np.array([0,-.044,1.771]);T=97;A=257
field=np.zeros((T,A),float);misses=0
for i,theta in enumerate(np.linspace(.0001,2.05,T)):
 for j,az in enumerate(np.linspace(-math.pi,math.pi,A)):
  d=Vector((math.sin(theta)*math.sin(az),-math.sin(theta)*math.cos(az),math.cos(theta)))
  hit,n,idx,dist=bv.ray_cast(Vector(center),d,.4)
  if hit is None:dist=.1;misses+=1
  field[i,j]=dist
def radius(d):
 theta=np.arccos(np.clip(d[:,2],-1,1));az=np.arctan2(d[:,0],-d[:,1])
 u=np.clip((theta-.0001)/2.0499*(T-1),0,T-1);v=(az+math.pi)/(2*math.pi)*(A-1)
 i=np.floor(u).astype(int);j=np.floor(v).astype(int);ii=np.minimum(i+1,T-1);jj=np.minimum(j+1,A-1)
 a=u-i;b=v-j
 return field[i,j]*(1-a)*(1-b)+field[ii,j]*a*(1-b)+field[i,jj]*(1-a)*b+field[ii,jj]*a*b
ob=next(o for o in bpy.data.collections['05_Hair'].objects if o.type=='CURVES')
old=ob.data;p=np.empty(len(old.points)*3,np.float32);old.attributes['position'].data.foreach_get('vector',p);p=p.reshape(-1,3)
sizes=np.array([len(c.points) for c in old.curves]);N=48;t=np.linspace(0,1,N);h=t*t*(3-2*t)
if ANATOMICAL:h=t**1.05
rng=np.random.default_rng(100410);cache={};guide_evidence={};new_positions=[];new_radii=[];offset=0;changed=0;support=0
for size in sizes:
 s=p[offset:offset+size].astype(float);offset+=size;r=s[0]
 front=(r[1]<-.045 and r[2]>1.812 and abs(r[0])<.087) or (r[1]<.003 and r[2]>1.850 and abs(r[0])<.063)
 if front:
  if LOCKS and changed%3==0:
   arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(s,axis=0),axis=1))]
   q=np.linspace(0,min(.045,float(arc[-1])),N)
   under=np.stack([np.interp(q,arc,s[:,j]) for j in range(3)],axis=1)
   ud=under-center;ud/=np.linalg.norm(ud,axis=1)[:,None]
   under=center+ud*(radius(ud)+.0014+.0018*np.sin(np.pi*t))[:,None];under[0]=r
   new_positions.append(under.astype(np.float32));new_radii.append((rng.uniform(.000030,.000041)*(1-.997*t**3)**.65).astype(np.float32));support+=1
  gridx=.014 if LOCKS else .010;gridy=.024 if LOCKS else .017
  key=(int(math.floor(r[0]/gridx)),int(math.floor(r[1]/gridy)))
  if key not in cache:
   heavy=(key[0]+.5)*gridx<.012
   cache[key]=(heavy,rng.uniform(-.032,.017) if LOCKS else rng.uniform(-.015,.014),rng.uniform(.005,.015) if LOCKS else rng.uniform(.003,.009),rng.uniform(0,6.28),rng.uniform(.006,.017) if LOCKS else rng.uniform(.004,.010))
  heavy,dz,lift,phase,swing=cache[key]
  endx=np.clip(r[0]+(-.021 if heavy else .014),-.095,.090)
  if LOCKS:endx=np.clip((key[0]+.5)*gridx+(-.028 if heavy else .021),-.097,.093)
  if LOOSE:endx=np.clip((key[0]+.5)*gridx+(-.016 if heavy else .012),-.097,.093)
  endz=1.782+dz+rng.uniform(-.003,.003)
  if LOCKS and abs(endx)<.022:endz=max(endz,1.790)
  if LOOSE:
   endz=1.779+dz+rng.uniform(-.0025,.0025)
   if abs(endx)<.018:endz=max(endz,1.777)
  if ANATOMICAL:
   # Actual retained eyebrow is at z=1.753..1.767, not at 1.79.
   # Stagger the heavy-side locks near the eyebrow and temple, open light side.
   endz=(1.754+dz*.60 if heavy else 1.771+dz*.40)+rng.uniform(-.0025,.0025)
   if abs(endx)<.018:endz=max(endz,1.762)
  endpoint=np.array([endx,-.169,endz])+rng.normal(0,.00065,3)
  a=r-center;a/=np.linalg.norm(a);b=endpoint-center;b/=np.linalg.norm(b)
  d=a[None,:]*(1-h[:,None])+b[None,:]*h[:,None]
  d[:,0]+=(swing/.12)*np.sin(t*6.2+phase*(1.0 if LOOSE else .18))*np.sin(np.pi*t)*(1 if heavy else -1)
  if ANATOMICAL:
   d=a[None,:]*(1-h[:,None])+b[None,:]*h[:,None]
   d[:,0]+=(swing/.12)*.9*np.sin(np.pi*t)*(1-2*t)*np.cos(phase)*(1 if heavy else -1)
  d/=np.linalg.norm(d,axis=1)[:,None]
  gap=.0005+lift*np.sin(np.pi*t)**.65+.002*t**3
  if ANATOMICAL:gap=.0005+lift*np.sin(np.pi*t)**1.6+.002*t**3
  if LOCKS:gap+=.003*t**3
  # Tiny independent fibers remain within a coherent lock, no reused endpoints.
  gap+=rng.uniform(-.0004,.0004)*np.sin(np.pi*t)
  s=center+d*(radius(d)+gap)[:,None]
  s[0]=r
  if VOLUME:
   # A shell alone is a hair-card-like sheet even when made of real strands.
   # Give each lock a 3D cross-section and smaller coherent sub-locks.
   tangent=np.gradient(s,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-8)
   normal=d-tangent*np.sum(d*tangent,axis=1)[:,None]
   normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-8)
   across=np.cross(tangent,normal)
   sub=int(rng.integers(0,7));subphase=sub*2.399963+phase
   aw=.0024*np.cos(subphase)+rng.normal(0,.00065)
   depth=.0017*np.sin(subphase)+rng.normal(0,.00055)
   envelope=np.minimum(1,t/.16)*(.12+.88*(1-t)**.7)
   s+=(across*aw+normal*depth)*envelope[:,None]
   # Small sub-lock undulations change strand tangents; do not coil the roots.
   s+=normal*(.0006*np.sin(t*9.0+subphase)*np.sin(np.pi*t))[:,None]
   if rng.random()<.22:
    limit=rng.uniform(.83,.985);q=t*limit
    s=np.stack([np.interp(q,t,s[:,j]) for j in range(3)],axis=1)
   if TIERED:
    # Crown layers should not all descend to the same brow-length curtain.
    short=rng.random()<(.64 if r[1]>-.083 else .16)
    if short:
     limit=rng.uniform(.52,.83) if r[1]>-.083 else rng.uniform(.74,.92)
     s=np.stack([np.interp(t*limit,t,s[:,j]) for j in range(3)],axis=1)
    drop=rng.uniform(.001,.006)
    s+=np.array([rng.uniform(-.0015,.0015),rng.uniform(-.001,.002),-drop])[None,:]*np.maximum(0,(t-.78)/.22)[:,None]**2
   delta=s-center;direction=delta/np.linalg.norm(delta,axis=1)[:,None]
   minimum=radius(direction)+.0008;length=np.linalg.norm(delta,axis=1)
   s+=direction*np.maximum(minimum-length,0)[:,None]
   s[0]=r
  if key not in guide_evidence:guide_evidence[key]=s.copy()
  changed+=1
 else:
  # Smooth interpolation retains the selected side/back haircut and tip flow.
  q=t*(size-1);i=np.minimum(np.floor(q).astype(int),size-2);u=(q-i)[:,None]
  pp=np.vstack([2*s[0]-s[1],s,2*s[-1]-s[-2]])
  a,b,c,d=pp[i],pp[i+1],pp[i+2],pp[i+3]
  s=.5*(2*b+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)
 new_positions.append(s.astype(np.float32));new_radii.append((rng.uniform(.000034,.000046)*(1-.997*t**3)**.65).astype(np.float32))
print('TARGET_FRINGE',changed,'PATCHES',len(cache),'FIELD_MISSES',misses,flush=True)
xyz=np.array(new_positions,np.float32);rad=np.array(new_radii,np.float32)
new=bpy.data.hair_curves.new('Fringe routed on actual target scalp');new.add_curves([N]*len(xyz))
new.attributes['position'].data.foreach_set('vector',xyz.ravel());new.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',rad.ravel())
for m in old.materials:new.materials.append(m)
ob.data=new;ob.name='Bystedt derivative • target scalp fringe flow'
gc=bpy.data.collections.new('07_Target_Fringe_Studies');bpy.context.scene.collection.children.link(gc);gc.hide_render=True
gd=bpy.data.curves.new('Representative target paths • evidence, not live drivers','CURVE');gd.dimensions='3D'
for s in guide_evidence.values():
 sp=gd.splines.new('POLY');sp.points.add(N-1)
 for pt,v in zip(sp.points,s):pt.co=(*v,1)
go=bpy.data.objects.new('Target scalp flow paths • editable evidence',gd);gc.objects.link(go);go.hide_render=True
bs=next(n for n in new.materials[0].node_tree.nodes if n.type=='BSDF_HAIR_PRINCIPLED');bs.inputs['Roughness'].default_value=.38;bs.inputs['Radial Roughness'].default_value=.48
if LOCKS:
 ramp=next(n for n in new.materials[0].node_tree.nodes if n.type=='VALTORGB')
 ramp.color_ramp.elements[0].color=(.025,.0015,.0025,1);ramp.color_ramp.elements[1].color=(.085,.005,.008,1)
tx=bpy.data.texts.get('ADAPTED_HAIR_CREDITS')
if tx:tx.write('\nFurther modifications: front fibers rerouted directly on target scalp; distinct ends, layered asymmetric fringe, retained side/back haircut. Evidence guides are not live drivers.\n')
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=64 if DRAFT else 192;scene.cycles.use_denoising=False;scene.cycles_curves.shape='THICK'
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=80 if DRAFT else 100
report=dict(version=version,source=source_version,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),hair_author='Daniel Bystedt',license='CC BY-SA; version unspecified in inspected source',method='front flow designed directly in target scalp coordinates; retained side/back, continuous local scalp radius field; separate fiber ends',front_curves_rerouted=changed,front_regions=len(cache),field_misses=misses,strands=len(xyz),points=int(xyz.shape[0]*N),draft=DRAFT,samples=scene.cycles.samples,status='unreviewed geometry study')
report.update(lock_clustering=LOCKS,loose_fringe=LOOSE,volumetric_lock_cross_sections=VOLUME,anatomical_fringe_length_and_tangent_start=ANATOMICAL,tiered_crown_lengths=TIERED,short_support_curves=support)
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('TARGET_FRINGE_SAVED',version,flush=True)
