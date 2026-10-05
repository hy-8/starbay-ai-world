"""Restyle native front sections on real follicles with scalp-fitted guide arcs.

Keep all existing side/rear and short scalp support. Existing Bystedt-derived
fibers/roots remain CC BY-SA (version unspecified); no source geometry sync.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version=a[0]
layered='--layered-wave' in a
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh frontal restyle required')
source=ROOT/'Exports/nativecoverage05/Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
assert all(c.points_length==65 for c in cu.curves)
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float);q=raw.copy();root=raw[:,0];tip=raw[:,-1]
ids=np.flatnonzero((tip[:,1]<-.14)&(tip[:,2]<1.81)&(root[:,2]>1.81)&(root[:,1]<-.035))
labels,inv=np.unique(np.round(tip[ids]/.007).astype(int),axis=0,return_inverse=True)
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
t=np.linspace(0,1,65);design=[];records=[];guides=[];guide_index=np.full(len(q),-1,np.int32);contacts=0
def smooth(v):v=np.clip(v,0,1);return v*v*(3-2*v)
def sample(control):
 c=np.array(control);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(c,axis=0),axis=1))]
 at=t*arc[-1];ix=np.minimum(np.maximum(np.searchsorted(arc,at,side='right')-1,0),len(c)-2)
 u=((at-arc[ix])/np.maximum(arc[ix+1]-arc[ix],1e-9))[:,None]
 ext=np.vstack([2*c[0]-c[1],c,2*c[-1]-c[-2]]);aa,bb,cc,dd=ext[ix],ext[ix+1],ext[ix+2],ext[ix+3]
 return .5*(2*bb+(-aa+cc)*u+(2*aa-5*bb+4*cc-dd)*u*u+(-aa+3*bb-3*cc+dd)*u*u*u)
for g in range(len(labels)):
 members=ids[inv==g];old=raw[members];center=np.mean(old,axis=0);r=center[0].copy();oldtip=center[-1]
 phase=(g*2.399963)%6.283185
 light=r[0]>.026 and oldtip[0]>.081 and r[1]>-.092
 if light:ex=np.clip(oldtip[0]*.96,.057,.100)
 elif r[0]>.012:ex=np.clip(.014-oldtip[0]*.83+.004*np.sin(phase),-.085,-.012)
 else:ex=np.clip(oldtip[0]*.97,-.102,-.027)
 # Central fringe ends above the eye; longer face frames stay outside the iris.
 ez=1.774-.047*smooth((abs(ex)-.042)/.047)+.0025*np.cos(phase)
 if light:ez=1.760-.026*smooth((ex-.068)/.032)+.002*np.cos(phase)
 if layered:
  # Vary the existing native endpoint sections, avoiding one fringe line.
  ez-=.006 if g%3 else -.006
  if abs(ex)<.040:ez=max(ez,1.765)
 endpoint=np.array([ex,-.183+.17*abs(ex),ez]);delta=endpoint-r
 control=[r]
 for fraction,lift in [(.19,.0055),(.45,.0090)]:
  hit,n,_,dist=bv.find_nearest(Vector(r+delta*fraction))
  control.append(np.array(hit+n*(lift+.0012*np.sin(phase))))
 side=1 if light else -1
 control.append(endpoint+np.array([-side*.004,.006,.026]))
 control.append(endpoint)
 guide=sample(control)
 guide[:,0]+=side*(.009 if layered else .004)*np.sin(t*(2.4 if layered else 2)*np.pi+(.35*np.sin(phase) if layered else 0))*np.sin(np.pi*t)
 if layered:
  guide[:,1]+=.0035*np.sin(t*2.1*np.pi+phase*.3)*np.sin(np.pi*t)
  guide[:,2]+=.0023*np.sin(t*2*np.pi)*np.sin(np.pi*t)
 guide[:,1]-=.0015*np.sin(t*np.pi)**2
 guide[0]=r
 tangent=np.gradient(guide,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-8)
 radial=guide-np.array([0,-.044,1.771]);normal=radial-tangent*np.sum(radial*tangent,axis=1)[:,None]
 normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-8)
 across=np.cross(tangent,normal);across/=np.maximum(np.linalg.norm(across,axis=1)[:,None],1e-8)
 coordinate=old[:,0]@across[0];lo,hi=np.quantile(coordinate,[.02,.98]);fraction=(coordinate-lo)/max(hi-lo,1e-6)
 # Retain actual native micro variation, add coherent small depth variation.
 residual=old-center[None];fade=1-.25*smooth((t-.38)/.62)
 v=guide[None]+residual*fade[None,:,None]
 depth=(np.sin(fraction*2.2*np.pi+phase)*.0023)[:,None]*np.sin(np.pi*t)[None]**1.35
 v+=normal[None]*depth[:,:,None]
 v[:,0]=old[:,0]
 for k,index in enumerate(members):
  for _ in range(2):
   correction=np.zeros((65,3))
   for j in range(1,64):
    if v[k,j,2]<1.79:continue
    hit,n,_,dist=bv.find_nearest(Vector(v[k,j]));gap=(Vector(v[k,j])-hit).dot(n)
    if dist<.02 and gap<.0005:
     d=np.array(n)*(.0007-gap);contacts+=1
     for l in range(max(1,j-2),min(65,j+3)):correction[l]+=d*np.exp(-.5*((l-j)/1.3)**2)
   v[k]+=correction
  v[k,0]=old[k,0];q[index]=v[k];guide_index[index]=g
 guides.append(guide)
 design.append(dict(index=g,role='short light side' if light else 'heavy diagonal fringe',control_points_m=np.array(control).tolist(),sampled_path_m=guide.tolist()))
 records.append(dict(fibers=len(members),light_side=bool(light),max_displacement_m=float(np.linalg.norm(v-old,axis=2).max())))
assert np.array_equal(q[:,0],raw[:,0]) and np.isfinite(q).all()
assert np.array_equal(q[guide_index<0],raw[guide_index<0])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
ob.data.attributes.new('native_front_guide_index','INT','CURVE').data.foreach_set('value',guide_index)
collection=bpy.data.collections.new('Native anatomical frontal guide controls');bpy.context.scene.collection.children.link(collection)
gd=bpy.data.curves.new('Fitted guide study, dense groom baked','CURVE');gd.dimensions='3D'
for guide in guides:
 sp=gd.splines.new('POLY');sp.points.add(len(guide)-1)
 for point,position in zip(sp.points,guide):point.co=(*position,1)
go=bpy.data.objects.new('Front restyle design guides • not live linked',gd);collection.objects.link(go);go.hide_render=True;go.hide_set(True)
out.mkdir(parents=True);render.mkdir(parents=True)
(out/'local_guide_design.json').write_text(json.dumps(design,indent=2),encoding='utf-8')
(out/'frontal_restyle_manifest.json').write_text(json.dumps(dict(source='nativecoverage05',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
 author='Daniel Bystedt',license='CC BY-SA; version unspecified',guide_sections=records,changed_fibers=len(ids),all_follicles_exactly_retained=True,
 layered_wave=layered,
 nonfrontal_primary_geometry_exactly_retained=True,all_short_support_unchanged=True,
 method='Measured native front sections restyled with actual scalp-fitted lead arcs, diagonal asymmetric fringe, central eye opening, existing microscale residuals and small coherent depth breakup',
 guide_controls_live_linked=False,smooth_contact_events=contacts,
 status='Unreviewed actual frontal shape study',scope='Discrete body points only; not full segments/eyes/clothing/animation or art acceptance'),indent=2),encoding='utf-8')
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
name='02_ThreeQuarter';s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('ANATOMICAL_NATIVE_FRONT_SAVED',version,len(ids),len(guides),flush=True)
