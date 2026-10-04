"""Layered male shag: fitted licensed undercoat plus authored free-space locks.

Preserves every source. Bystedt-derived undercoat remains CC BY-SA (version
unspecified by the inspected source). Output is a local, unapproved study.
"""
import bpy, sys, re, json, math, hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version=args[0]
NATURAL='--natural' in args
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh version required')
out.mkdir(parents=True);render.mkdir(parents=True)
source=ROOT/'Exports/officialwave04/Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
col=bpy.data.collections['05_Hair'];base=next(o for o in col.objects if o.type=='CURVES')
body=bpy.data.objects['CC0 male body • retained topology'];bpy.context.view_layer.update()
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
C=np.array([0,-.044,1.771]);rng=np.random.default_rng(100405)
N=64;t=np.linspace(0,1,N)

def scalp(x,y):
 p,n,_,_=bv.ray_cast(Vector((x,y,2.05)),Vector((0,0,-1)),.40)
 if p is None:raise RuntimeError('Missed root')
 return np.array(p+n*.0005)

def rayroot(theta,az):
 d=Vector((math.sin(theta)*math.sin(az),-math.sin(theta)*math.cos(az),math.cos(theta)))
 p,n,_,_=bv.ray_cast(Vector(C),d,.35)
 if p is None:raise RuntimeError('Missed radial root')
 return np.array(p+n*.0005)

def catmull(knots):
 p=np.array(knots);pp=np.vstack([2*p[0]-p[1],p,2*p[-1]-p[-2]])
 q=t*(len(p)-1);i=np.minimum(np.floor(q).astype(int),len(p)-2);u=(q-i)[:,None]
 a,b,c,d=pp[i],pp[i+1],pp[i+2],pp[i+3]
 return .5*((2*b)+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)

# Crop the donor to coverage, removing its bob silhouette and broad fringe.
cu=base.data;p=np.empty(len(cu.points)*3,np.float32)
cu.attributes['position'].data.foreach_get('vector',p);p=p.reshape(-1,3)
sizes=[len(c.points) for c in cu.curves];offset=0;cover=[];cr=[]
for size in sizes:
 strand=p[offset:offset+size];offset+=size
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(strand,axis=0),axis=1))]
 limit=rng.uniform(.026,.045) if strand[0,2]>1.80 else rng.uniform(.020,.034)
 if NATURAL:limit=float(arc[-1])
 length=min(float(arc[-1]),limit);q=np.linspace(0,length,16)
 s=np.stack([np.interp(q,arc,strand[:,j]) for j in range(3)],axis=1)
 for j,pt in enumerate(s):
  hit,n,_,dist=bv.find_nearest(Vector(pt));gap=(Vector(pt)-hit).dot(n)
  if pt[2]>1.78 and abs(gap)<.050:
   target=max(.0006,min(.022,gap*.62)) if NATURAL else max(.0006,min(.0045,gap*.18))
   s[j]=np.array(hit+n*target)
 if NATURAL:
  u=np.linspace(0,1,len(s));lower=np.clip((1.82-s[:,2])/.09,0,1)
  s[:,0]*=1-.15*lower
  if strand[0,1]>.005 or (abs(strand[0,0])>.05 and strand[0,1]>-.015):
   s[:,2]-=rng.uniform(.025,.050)*u**3
   s[:,0]*=1-.16*u**3
  elif strand[0,1]<-.03 and abs(strand[0,0])>.050:
   s[:,2]+=rng.uniform(.010,.020)*u**3
 cover.append(s);cr.append(.000035*(1-.995*np.linspace(0,1,16)**3)**.65 if NATURAL else np.linspace(.000040,.000006,16))
new=bpy.data.hair_curves.new('Cropped fitted support, CC BY-SA')
new.add_curves([16]*len(cover));new.attributes['position'].data.foreach_set('vector',np.array(cover,np.float32).ravel())
new.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.array(cr,np.float32).ravel())
for m in cu.materials:new.materials.append(m)
base.data=new;base.name='Bystedt fitted support only • CC BY-SA'

design=[]
def add(zone,knots,width=.004,count=550):
 design.append(dict(zone=zone,knots=np.array(knots).tolist(),width=width,count=count))

# Diagonal swept crown. Multiple lengths terminate at different heights.
for side,num in [(-1,35),(1,23)]:
 for k in range(num):
  f=(k+.5)/num;y=-.137+.175*f
  p=scalp(.023+rng.uniform(-.009,.009),y)
  zp=min(1.889,max(p[2]+.010,1.866))+rng.uniform(-.004,.004)
  xx=side*(.080+rng.uniform(-.006,.006));short=k%3==0
  endz=(1.810-.041*f if short else 1.765-.055*f)+rng.uniform(-.010,.014)
  endy=y-.017 if side<0 else y+.008
  knots=[p,(side*.012,y-.006,zp),(side*.050,y-.017,zp-.003),
         (side*.085,y-.006,1.833-.033*f),(side*.074,y-.018,1.793-.036*f),
         (xx,endy,endz)]
  if short:knots=knots[:4]+[(xx+side*.007,y+.005,endz)]
  if not NATURAL or k%3==1:add('swept_crown',knots,rng.uniform(.0034,.0050),650)

# Narrow independent forehead locks; no common endpoint or broad ribbon.
for k in range(17):
 f=(k+.5)/17;p=scalp(.017+rng.uniform(-.012,.008),-.148+.069*f)
 x=-.018-.061*f;endz=1.801-.062*f+rng.uniform(-.009,.010)
 if NATURAL:x=.015-.086*f;endz=1.780-.035*f+rng.uniform(-.010,.015)
 knots=[p,(.004,-.156+.029*f,1.879+.006*f),
        (-.040,-.176+.021*f,1.850-.003*f),
        (-.057,-.182+.025*f,1.806-.015*f),
        (x,-.170+.022*f,endz)]
 add('fringe',knots,rng.uniform(.0017,.0028),520)
for k in range(8):
 f=(k+.5)/8;p=scalp(.032+rng.uniform(-.006,.006),-.143+.040*f)
 add('light_fringe',[p,(.056,-.156+.018*f,1.861),
     (.074,-.166+.020*f,1.814),(.062,-.159+.022*f,1.786),
     (.069,-.141+.025*f,1.756+.028*f)],.0024,430)

# Short ear layers open the silhouette. Long hair starts behind the ear.
for side in [-1,1]:
 for k in range(29):
  f=(k+.5)/29;az=side*(.80+1.60*f);theta=rng.uniform(.65,1.24)
  p=rayroot(theta,az);x=side*(.082+rng.uniform(-.004,.006))
  front=f<.40;endz=rng.uniform(1.723,1.775) if front else rng.uniform(1.679,1.740)
  knots=[p,(x,p[1]+.008,p[2]+.004),
         (x+side*.007,p[1]+.015,p[2]-.025),
         (x-side*.003,p[1]+.015,(p[2]+endz)/2),
         (x+side*.005,p[1]+.023,endz)]
  if not NATURAL or k%2==0:add('ear_layers',knots,rng.uniform(.0028,.0040),480)

# Tapered wolf-cut nape: narrow at the neck, unequal soft S shaped ends.
for k in range(49):
 f=(k+.5)/49;az=math.pi*.64+math.pi*.72*f;theta=rng.uniform(.45,1.38)
 p=rayroot(theta,az);x=p[0];y=max(.054,p[1]+.010)
 endz=rng.uniform(1.610,1.688) if k%3 else rng.uniform(1.715,1.755)
 knots=[p,(x*1.05,y,p[2]+.005),
        (x*1.13+.003,y+.009,p[2]-.030),
        (x*.83-.005,y+.021,(p[2]+endz)/2),
        (x*.78+rng.uniform(-.010,.010),y+.032,endz)]
 if not NATURAL or k%2==0:add('nape',knots,rng.uniform(.0025,.0040),550)

paths=[];radii=[];guides=[];fixed=0
for g in design:
 path=catmull(g['knots']);width=g['width'];count=g['count']
 for i,pt in enumerate(path):
  if pt[2]<1.73:continue
  hit,n,_,dist=bv.find_nearest(Vector(pt));gap=(Vector(pt)-hit).dot(n)
  if gap<.0020 and dist<.045:path[i]=np.array(hit+n*.0025);fixed+=1
 tangent=np.gradient(path,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-8)
 normal=path-C;normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-8)
 lateral=np.cross(tangent,normal);lateral/=np.maximum(np.linalg.norm(lateral,axis=1,keepdims=True),1e-8)
 normal=np.cross(lateral,tangent)
 # Broad root footprint, converging into a finer coherent lock, then loose tip.
 shape=.85-.58*t+.12*np.sin(np.pi*t)
 if NATURAL:shape=(.65+.55*np.sin(np.pi*t))*(1-.85*t**4)
 across=rng.uniform(-1,1,(count,1))*width*shape
 depth=rng.normal(0,width*.28,(count,1))*shape
 phase=rng.uniform(0,6.28,(count,1))
 across+=rng.uniform(.00008,.00030,(count,1))*np.sin(t*11+phase)*np.sin(np.pi*t)
 depth+=.00015*np.sin(t*9+phase)*np.sin(np.pi*t)
 if NATURAL:
  across+=rng.uniform(.0008,.0026,(count,1))*np.sin(t*7+phase)*np.sin(np.pi*t)
  depth+=rng.uniform(.0007,.0020,(count,1))*np.sin(t*6+phase+.7)*np.sin(np.pi*t)
 across+=rng.normal(0,.0007,(count,1))*t**5
 xyz=path[None,:,:]+lateral[None,:,:]*across[:,:,None]+normal[None,:,:]*depth[:,:,None]
 for j in range(count):
  hit,n,_,_=bv.find_nearest(Vector(xyz[j,0]));cor=np.array(hit+n*.0005)-xyz[j,0]
  xyz[j]+=cor[None,:]*(1-t[:,None])**4
 ends=rng.uniform(.58 if NATURAL else .86,1,(count,1));q=t*ends*(N-1);lo=np.floor(q).astype(int);hi=np.minimum(N-1,lo+1);b=(q-lo)[:,:,None]
 xyz=xyz[np.arange(count)[:,None],lo]*(1-b)+xyz[np.arange(count)[:,None],hi]*b
 paths.append(xyz.astype(np.float32));radii.append((rng.uniform(.000029,.000045,(count,1))*(1-.996*t**3)**.65).astype(np.float32));guides.append(path)
xyz=np.concatenate(paths);rad=np.concatenate(radii)
cu=bpy.data.hair_curves.new('Independent layered male shag');cu.add_curves([N]*len(xyz))
cu.attributes['position'].data.foreach_set('vector',xyz.ravel());cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',rad.ravel())
mat=bpy.data.materials.new('Cherry coherent outer locks');mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear()
bs=nt.nodes.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='COLOR';bs.inputs['Roughness'].default_value=.28;bs.inputs['Radial Roughness'].default_value=.42
hi=nt.nodes.new('ShaderNodeHairInfo');r=nt.nodes.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(.010,.0009,.0012,1);r.color_ramp.elements[1].color=(.045,.0030,.0040,1)
nt.links.new(hi.outputs['Random'],r.inputs[0]);nt.links.new(r.outputs[0],bs.inputs['Color']);o=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(bs.outputs[0],o.inputs[0]);cu.materials.append(mat)
ob=bpy.data.objects.new('Authored asymmetrical fringe and layered shag',cu);col.objects.link(ob)
gc=bpy.data.collections.new('07_Hybrid_Authored_Guides');bpy.context.scene.collection.children.link(gc);gc.hide_render=True
gd=bpy.data.curves.new('Male shag control guides','CURVE');gd.dimensions='3D'
for path in guides:
 sp=gd.splines.new('POLY');sp.points.add(N-1)
 for p,q in zip(sp.points,path):p.co=(*q,1)
go=bpy.data.objects.new('Independent groom control guides',gd);gc.objects.link(go);go.hide_render=True
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles_curves.shape='THICK';scene.cycles.samples=192;scene.cycles.use_denoising=False
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
report=dict(version=version,source='officialwave04',natural=NATURAL,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),undercoat_author='Daniel Bystedt',undercoat_license='CC BY-SA; version unspecified in inspected source',method='continuous compressed fitted support plus independent relaxed layered male shag' if NATURAL else 'cropped compressed fitted support plus independent free-space layered male shag',support_fibers=len(sizes),outer_fibers=len(xyz),guides=len(design),guide_clearance_repairs=fixed,status='unreviewed actual geometry candidate; no release')
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(out/'guide_design.json').write_text(json.dumps(design,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('HYBRID_SHAG_SAVED',version,flush=True)
