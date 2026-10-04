"""Local crown sculpt and individual tip relaxation of saved actual hair.

Read protected layercut04 by default. Bystedt-derived hair remains CC BY-SA,
version unspecified in inspected source. No source file is overwritten.
"""
import bpy,sys,re,json,math,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version=args[0];source_version=args[1] if len(args)>1 else 'layercut04'
if not all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in [version,source_version]):raise ValueError(args)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh version required')
out.mkdir(parents=True);render.mkdir(parents=True)
source=ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=next(o for o in bpy.data.collections['05_Hair'].objects if o.type=='CURVES')
old=ob.data;positions=np.empty(len(old.points)*3,np.float32)
old.attributes['position'].data.foreach_get('vector',positions);positions=positions.reshape(-1,3).astype(float)
sizes=[len(c.points) for c in old.curves]
body=bpy.data.objects['CC0 male body • retained topology'];bpy.context.view_layer.update()
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
N=64;u=np.linspace(0,1,N);rng=np.random.default_rng(100407)

def crown_weight(p):
 return np.exp(-((p[:,0]-.023)/.028)**2-((p[:,1]+.075)/.053)**2)*np.clip((p[:,2]-1.837)/.029,0,1)

def cubic_resample(p):
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
 arc=np.maximum.accumulate(arc+np.arange(len(p))*1e-10)
 q=np.interp(u,np.linspace(0,1,len(p)),arc)
 idx=np.minimum(np.searchsorted(arc,q,side='right')-1,len(p)-2);idx=np.maximum(idx,0)
 t=((q-arc[idx])/(arc[idx+1]-arc[idx]))[:,None]
 pp=np.vstack([2*p[0]-p[1],p,2*p[-1]-p[-2]])
 a,b,c,d=pp[idx],pp[idx+1],pp[idx+2],pp[idx+3]
 return .5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)

all_p=[];all_r=[];offset=0;crown_changed=0;fixed=0;min_before=0.;tips=[]
for size in sizes:
 s=positions[offset:offset+size].copy();offset+=size
 # Compress only the excess volume near the raised part, preserving the root.
 weights=crown_weight(s)*(1-np.exp(-np.linspace(0,1,size)*24))
 for i,w in enumerate(weights):
  if w<.015:continue
  hit,n,_,dist=bv.find_nearest(Vector(s[i]));gap=(Vector(s[i])-hit).dot(n)
  if gap>.006 and dist<.045:
   s[i]-=np.array(n)*(gap-.006)*.62*w;crown_changed+=1
 # Gently relax local kinks; first and last points remain pinned.
 for iteration in range(2):
  target=(s[:-2]+2*s[1:-1]+s[2:])/4
  w=crown_weight(s[1:-1])*.38
  s[1:-1]=s[1:-1]*(1-w[:,None])+target*w[:,None]
 s=cubic_resample(s)
 # Source native clumps shared exact endpoints. Give each shaft a distinct
 # ending while retaining the coherent main lock and its crown silhouette.
 tangent=s[-1]-s[-3];tangent/=max(np.linalg.norm(tangent),1e-8)
 drop=rng.uniform(-.013,.005);jitter=rng.normal(0,.0018,3)
 jitter-=tangent*np.dot(jitter,tangent)
 delta=tangent*drop+jitter
 s+=delta[None,:]*np.maximum(0,(u-.67)/.33)[:,None]**1.8
 # Resolve the actual saved fibers, not just their guide center paths.
 for i,pt in enumerate(s):
  if pt[2]<1.735:continue
  hit,n,_,dist=bv.find_nearest(Vector(pt));gap=(Vector(pt)-hit).dot(n)
  min_before=min(min_before,gap)
  if gap<.00070 and dist<.040:s[i]=np.array(hit+n*.0010);fixed+=1
 all_p.append(s.astype(np.float32));all_r.append((rng.uniform(.000031,.000042)*(1-.997*u**3)**.65).astype(np.float32));tips.append(drop)
xyz=np.array(all_p);radii=np.array(all_r)
new=bpy.data.hair_curves.new('Crown-sculpted layered cut with distinct fiber tips');new.add_curves([N]*len(xyz))
new.attributes['position'].data.foreach_set('vector',xyz.ravel());new.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',radii.ravel())
for m in old.materials:new.materials.append(m)
ob.data=new;ob.name='Bystedt adapted cut • local crown sculpt and relaxed tips'
# Source guide evidence gets the same crown sculpt, but is not a live driver.
for go in bpy.data.objects:
 if go.type!='CURVE' or 'Cut and shaped source guides' not in go.name:continue
 for sp in go.data.splines:
  p=np.array([q.co[:3] for q in sp.points],float);w=crown_weight(p)*(1-np.exp(-np.linspace(0,1,len(p))*24))
  for i,ww in enumerate(w):
   if ww<.015:continue
   hit,n,_,dist=bv.find_nearest(Vector(p[i]));gap=(Vector(p[i])-hit).dot(n)
   if gap>.006 and dist<.045:p[i]-=np.array(n)*(gap-.006)*.62*ww
  for q,v in zip(sp.points,p):q.co=(*v,1)
mat=new.materials[0];nt=mat.node_tree
bs=next(n for n in nt.nodes if n.type=='BSDF_HAIR_PRINCIPLED');hi=next(n for n in nt.nodes if n.type=='HAIR_INFO')
rough=nt.nodes.new('ShaderNodeMapRange');rough.inputs['To Min'].default_value=.32;rough.inputs['To Max'].default_value=.39
nt.links.new(hi.outputs['Random'],rough.inputs['Value']);nt.links.new(rough.outputs[0],bs.inputs['Roughness'])
bs.inputs['Radial Roughness'].default_value=.47
credits=bpy.data.texts.get('ADAPTED_HAIR_CREDITS')
if credits:credits.write('\nFurther modifications: local crown compression/smoothing, individual fiber ends and shaft roughness variation. Hidden guide curves are editable evidence, not live drivers of the baked visible groom.\n')
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=192;scene.cycles.use_denoising=False;scene.cycles_curves.shape='THICK'
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
report=dict(version=version,source=source_version,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),hair_author='Daniel Bystedt',license='CC BY-SA; version unspecified in inspected source',method='localized excess crown compression and kink smoothing; separate fiber endpoints, original main clump flow preserved',strands=len(xyz),points=int(xyz.shape[0]*N),crown_points_changed=crown_changed,clearance_repairs=fixed,minimum_signed_gap_before_repairs_m=min_before,tip_length_delta_range_m=[min(tips),max(tips)],guide_status='editable source evidence; not live control of baked dense hair',status='unreviewed local candidate')
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('POLISHED_LAYER_CUT_SAVED',version,flush=True)
