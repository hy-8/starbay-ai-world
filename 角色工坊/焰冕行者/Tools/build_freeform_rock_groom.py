"""Editable free-space guide design for layered red concert hair.

No surface wig tracing and no angular spherical sweep. Scalp attachment is
limited to roots; visible locks follow separately authored Catmull-Rom knots.
"""
import bpy,sys,re,json,math,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version=args[0]
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh version required')
out.mkdir(parents=True);render.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports/hairrecongroom05/Ember_Regent.blend'))
col=bpy.data.collections['05_Hair']
for ob in list(col.objects):
 if ob.name!='Scalp rooted coverage beneath sculpted locks':bpy.data.objects.remove(ob,do_unlink=True)
body=bpy.data.objects['CC0 male body • retained topology'];bpy.context.view_layer.update()
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get());center=np.array([0,-.044,1.771])
rng=np.random.default_rng(100402);N=72;t=np.linspace(0,1,N);design=[]
REFINE='--refine' in args
FLOW='--flow' in args
def root(x,y):
 p,n,_,_=bv.ray_cast(Vector((x,y,2.05)),Vector((0,0,-1)),.4)
 if p is None:raise RuntimeError('Root ray missed')
 return np.array(p+n*.0004)
def catmull(knots):
 p=np.array(knots);pp=np.vstack([2*p[0]-p[1],p,2*p[-1]-p[-2]])
 q=t*(len(p)-1);i=np.minimum(np.floor(q).astype(int),len(p)-2);u=(q-i)[:,None]
 a,b,c,d=pp[i],pp[i+1],pp[i+2],pp[i+3]
 return .5*((2*b)+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)
def add(zone,knots,width,count=460):
 if REFINE:
  knots=np.array(knots,dtype=float)
  if zone in ['left_crown','right_crown']:
   # Rebalance the part and remove the paired high arches seen in v01.
   knots[0]=root(.035+rng.uniform(-.004,.008),knots[0,1])
   lift=np.maximum(0,knots[:,2]-1.865);knots[:,2]-=lift*.30
   if zone=='right_crown':knots[1:,2]-=.006*np.sin(np.linspace(0,math.pi,len(knots)-1))
   knots[1:,0]+=rng.uniform(-.004,.004,len(knots)-1)
   knots[1:,1]+=rng.uniform(-.007,.007,len(knots)-1)
   # Unequal tips separate the visible layers, while preserving smooth bends.
   knots[-1,2]+=rng.uniform(-.025,.024)
  if zone=='s_fringe':
   knots[:,1]-=.014*np.sin(np.linspace(0,math.pi*.85,len(knots)))
   knots[-1,0]+=.015;knots[-1,2]-=.012
  width*=.85
 if FLOW and zone in ['left_crown','right_crown']:
  knots=np.array(knots,dtype=float)
  knots[1:,2]-=np.maximum(0,knots[1:,2]-1.865)*.16
  width*=.70
 design.append({'zone':zone,'knots':np.array(knots).tolist(),'width':width,'count':count})
# Larger side of offset part: distinct crest heights, asymmetric free ends,
# forward fringe and side crown layers deliberately occupy different depths.
for k in range(32):
 f=(k+.5)/32;y=-.137+.174*f;x=.018+rng.uniform(-.006,.009);p=root(x,y)
 zpeak=max(p[2]+.022,1.888)+rng.uniform(-.006,.009)
 tipz=1.768-.06*f+rng.uniform(-.018,.018);tipy=y-.024+rng.uniform(-.014,.014)
 knots=[p,(-.016,y-.012,zpeak),(-.061,y-.025,zpeak-.010),(-.093,y-.017,1.831-.035*f),(-.084,y-.031,1.797-.035*f),(-.091+rng.uniform(-.011,.005),tipy,tipz)]
 if k%4==0:
  knots=knots[:-1];knots[-1]=(-.105,y+.004,1.807-.040*f)
 add('left_crown',knots,rng.uniform(.0023,.0040),520)
# Lighter side of part bends back, rather than mirroring the left fringe.
for k in range(23):
 f=(k+.5)/23;y=-.131+.172*f;p=root(.024+rng.uniform(-.005,.010),y)
 zp=max(p[2]+.022,1.880)+rng.uniform(-.005,.011)
 knots=[p,(.055,y-.008,zp),(.088,y-.018,zp-.032),(.100,y+.001,1.804-.025*f),(.084,y+.004,1.754-.038*f),(.097,y+.023,1.730-.026*f)]
 if k%4==1:knots=knots[:-1];knots[-1]=(.105,y+.023,1.765-.027*f)
 add('right_crown',knots,rng.uniform(.0023,.0038),470)
# Front S-fringe is separately designed, with tapered tips and eye clearance.
for k in range(19):
 f=(k+.5)/19;y=-.149+.075*f;p=root(.017+rng.uniform(-.004,.006),y)
 xe=-.030-.057*f;ze=1.791-.071*f;ye=-.157+.035*f
 knots=[p,(-.006,-.147+.037*f,1.891+rng.uniform(-.003,.008)),(-.047,-.166+.026*f,1.862-.014*f),(-.066,-.171+.030*f,1.825-.027*f),(xe,ye,ze)]
 if k%3==0:knots[-1]=(xe-.010,ye+.004,ze+.028)
 add('s_fringe',knots,rng.uniform(.0017,.0030),370)
for k in range(9):
 f=(k+.5)/9;p=root(.028+rng.uniform(-.004,.006),-.14+.036*f)
 knots=[p,(.053,-.154+.022*f,1.867),(.070,-.162+.020*f,1.824),(.059,-.154+.020*f,1.784),(.069,-.137+.024*f,1.753+.024*f)]
 add('right_face',knots,.0019,340)
if REFINE:
 for k in range(12):
  f=(k+.5)/12;p=root(.031+rng.uniform(-.003,.005),-.145+.065*f)
  xe=.008-.063*f;ze=1.795-.044*f
  knots=[p,(.022-.013*f,-.164+.015*f,1.872+.006*f),(-.019-.026*f,-.186+.016*f,1.841),(-.034-.020*f,-.183+.018*f,1.804),(xe,-.173+.006*f,ze)]
  add('loose_brow_fringe',knots,rng.uniform(.0011,.0020),230)
# Ear and nape layers: three length bands and alternating shallow S bends.
for side in [-1,1]:
 for k in range(22):
  f=(k+.5)/22;az=side*(.88+1.48*f);theta=rng.uniform(.72,1.24)
  d=Vector((math.sin(theta)*math.sin(az),-math.sin(theta)*math.cos(az),math.cos(theta)))
  p,n,_,_=bv.ray_cast(Vector(center),d,.35);p=np.array(p+n*.0004)
  xx=side*(.090+rng.uniform(-.006,.007));yy=p[1]+.008
  end=1.665+rng.uniform(0,.059);end+=.055 if k%3==0 else 0
  knots=[p,(xx,yy,p[2]+.012),(xx+side*.008,yy+.006,p[2]-.032),(xx-side*.007,yy+.017,(p[2]+end)/2),(xx+side*.006,yy+.027,end)]
  add('temple',knots,rng.uniform(.0023,.0036),420)
for k in range(52):
 f=(k+.5)/52;az=math.pi*.62+math.pi*.76*f;theta=rng.uniform(.28,1.23)
 d=Vector((math.sin(theta)*math.sin(az),-math.sin(theta)*math.cos(az),math.cos(theta)))
 p,n,_,_=bv.ray_cast(Vector(center),d,.35);p=np.array(p+n*.0004)
 x=p[0];y=.054+rng.uniform(-.005,.012);end=rng.uniform(1.626,1.705)
 if k%3==0:end+=.07
 knots=[p,(x*1.12,y,1.850+rng.uniform(-.025,.025)),(x*1.20+.004,y+.015,1.790),(x*1.10-.005,y+.012,1.720),(x*1.13+rng.uniform(-.01,.01),y+.025,end)]
 if FLOW:
  # Lower nape roots must descend, not rise into a repeated arch.
  knots=[p,(x*1.08,max(p[1]+.010,y-.01),p[2]+.009),(x*1.18+.004,y+.014,min(p[2]-.020,1.813)),(x*1.08-.005,y+.017,(min(p[2]-.020,1.813)+end)/2),(x*1.15+rng.uniform(-.012,.012),y+.032,end-.022)]
 add('nape',knots,rng.uniform(.0023,.0037),450)
paths=[];radius=[];guides=[];clipped=0
for g in design:
 path=catmull(g['knots']);zone=g['zone'];count=g['count'];width=g['width']
 if FLOW and zone in ['left_crown','right_crown'] and rng.random()<.38:
  # Shorter shingled layers terminate independently instead of every crown
  # lock travelling all the way down to the same ear/nape line.
  q=t*rng.uniform(.61,.80)*(N-1);lo=np.floor(q).astype(int);hi=np.minimum(N-1,lo+1);b=(q-lo)[:,None]
  path=path[lo]*(1-b)+path[hi]*b
  path[:,0]+=np.sign(path[-1,0])*.007*t**3
  path[:,1]+=.005*t**3
 if REFINE:
  # A second bend distinguishes the silhouette from a single smooth cap.
  wave=np.sin(np.pi*t)**1.1;phase=rng.uniform(0,6.28)
  path[:,0]+=rng.uniform(.002,.006)*np.sin(t*9+phase)*wave
  path[:,1]+=rng.uniform(.002,.006)*np.sin(t*8+phase+.8)*wave
  path[:,2]+=rng.uniform(.001,.003)*np.sin(t*10+phase)*wave
 # Resolve any guide/skull intersection without flattening the entire style.
 for i,p in enumerate(path):
  if p[2]<1.715:continue
  hit,n,_,_=bv.find_nearest(Vector(p));gap=(Vector(p)-hit).dot(n)
  if gap<.001:
   path[i]=np.array(hit+n*.0015);clipped+=1
 tangent=np.gradient(path,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-8)
 normal=path-center;normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-8)
 lateral=np.cross(tangent,normal);lateral/=np.maximum(np.linalg.norm(lateral,axis=1,keepdims=True),1e-8);normal=np.cross(lateral,tangent)
 phase=rng.uniform(0,2*np.pi,(count,1));shape=(.30+.70*np.sin(np.pi*t)**.65)*(1-.87*t**4)
 cross=rng.normal(0,width,(count,1))*shape
 depth=rng.normal(0,width*.73,(count,1))*shape
 cross+=rng.uniform(.00025,.0008,(count,1))*np.sin(t*16+phase)*np.sin(np.pi*t)
 depth+=rng.uniform(.0003,.0008,(count,1))*np.sin(t*12+phase)*np.sin(np.pi*t)
 # Fibers relax out of the main clump towards their tips at unequal lengths.
 cross+=rng.normal(0,.0014,(count,1))*np.maximum(0,(t-.60)/.40)**1.3
 xyz=path[None,:,:]+lateral[None,:,:]*cross[:,:,None]+normal[None,:,:]*depth[:,:,None]
 for j in range(count):
  hit,n,_,_=bv.find_nearest(Vector(xyz[j,0]));delta=np.array(hit+n*.00045)-xyz[j,0]
  xyz[j]+=delta[None,:]*(1-t[:,None])**4
 ends=rng.uniform(.80,1,(count,1));q=t*ends*(N-1);lo=np.floor(q).astype(int);hi=np.minimum(N-1,lo+1);b=(q-lo)[:,:,None]
 xyz=xyz[np.arange(count)[:,None],lo]*(1-b)+xyz[np.arange(count)[:,None],hi]*b
 paths.append(xyz.astype(np.float32));radius.append((rng.uniform(.000026,.000045,(count,1))*(1-.985*t)**.72).astype(np.float32));guides.append(path)
xyz=np.concatenate(paths);radii=np.concatenate(radius)
cu=bpy.data.hair_curves.new('Independently authored free-space rock layers');cu.add_curves([N]*len(xyz));cu.attributes['position'].data.foreach_set('vector',xyz.ravel());cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',radii.ravel())
mat=bpy.data.materials.new('Cherry red anisotropic fiber');mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear();bs=nt.nodes.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='COLOR';bs.inputs['Roughness'].default_value=.34;bs.inputs['Radial Roughness'].default_value=.46
hi=nt.nodes.new('ShaderNodeHairInfo');r=nt.nodes.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(.007,.0010,.0015,1);r.color_ramp.elements[1].color=(.060,.0055,.007,1);nt.links.new(hi.outputs['Random'],r.inputs[0]);nt.links.new(r.outputs[0],bs.inputs['Color']);o=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(bs.outputs[0],o.inputs[0]);cu.materials.append(mat)
ob=bpy.data.objects.new('Free-space sculpted rock hair',cu);col.objects.link(ob)
# Keep guide curves hidden, editable and separate from generated fibers.
gc=bpy.data.collections.new('06_Editable_Groom_Guides');bpy.context.scene.collection.children.link(gc);gc.hide_render=True
gd=bpy.data.curves.new('Authored center guides','CURVE');gd.dimensions='3D'
for p in guides:
 sp=gd.splines.new('POLY');sp.points.add(N-1)
 for q,v in zip(sp.points,p):q.co=(*v,1)
go=bpy.data.objects.new('Visible layer design guides',gd);gc.objects.link(go);go.hide_render=True
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles_curves.shape='THICK';scene.cycles.samples=128;scene.cycles.use_denoising=False
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
report={'version':version,'base':'hairrecongroom05','refine':REFINE,'flow':FLOW,'method':'free-space independently authored S-shaped scalp-attached guides; tapered native hair fibers','seed':100402,'guides':len(design),'outer_fibers':len(xyz),'guide_clearance_corrections':clipped,'status':'candidate requiring visual review'}
(out/'guide_design.json').write_text(json.dumps(design,indent=2),encoding='utf-8')
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('FREEFORM_GROOM_SAVED',version,flush=True)
