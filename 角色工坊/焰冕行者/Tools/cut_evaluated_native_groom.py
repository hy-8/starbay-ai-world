"""Scissor the actual evaluated artist groom rather than deforming its guides.

Daniel Bystedt Hair Styles CC BY-SA (version unspecified), local derivative.
Keeps native roll/parting/clump/noise shape untouched before whole-shaft cut.
"""
import bpy,sys,re,json,hashlib,math
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version=a[0]
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh study only')
asset=ROOT/'Source/BlenderHairStyles/Bystedt_HairStyles.blend'
stable=ROOT/'Exports/napeunderlay02/Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(asset),use_scripts=False)
hair=bpy.data.objects['long hair main'];changes=[]
for mod in hair.modifiers:
 if mod.type!='NODES':continue
 for node in mod.node_group.nodes:
  if node.type!='GROUP':continue
  name=node.node_tree.name
  values={'Density':18000.0} if name.startswith('Interpolate Hair Curves') else {}
  for key,value in values.items():
   sock=node.inputs.get(key)
   if sock is None or sock.is_linked:raise RuntimeError(name+'/'+key)
   changes.append(dict(node=name,socket=key,before=float(sock.default_value),after=value));sock.default_value=value
hair.update_tag();bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
cu=hair.evaluated_get(dg).data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
sizes=[c.points_length for c in cu.curves];m=np.array(hair.matrix_world)
p=(p@m[:3,:3].T+m[:3,3]-np.array([5,0,0]))*.1
head=bpy.data.objects['head'];sv=np.array([head.matrix_world@v.co for v in head.data.vertices],float)*.1
sb=BVHTree.FromPolygons([Vector(v) for v in sv],[list(f.vertices) for f in head.data.polygons])
cs=np.array([0,-.063,float(sv[:,2].max())-.100]);ct=np.array([0,-.044,1.771])
bpy.ops.wm.open_mainfile(filepath=str(stable),use_scripts=False);bpy.context.view_layer.update()
body=bpy.data.objects['CC0 male body • retained topology'];assert np.allclose(np.array(body.matrix_world),np.eye(4))
tb=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
T,A=129,257;field=np.empty((T,A,2));misses=0
for i,theta in enumerate(np.linspace(.001,2.04,T)):
 for j,az in enumerate(np.linspace(-math.pi,math.pi,A)):
  d=Vector((math.sin(theta)*math.sin(az),-math.sin(theta)*math.cos(az),math.cos(theta)))
  sh,_,_,sd=sb.ray_cast(Vector(cs),d,.5);th,_,_,td=tb.ray_cast(Vector(ct),d,.5)
  if sh is None or th is None:misses+=1;sd=.100;td=.103
  field[i,j]=[sd,td]
v=p-cs;r=np.maximum(np.linalg.norm(v,axis=1),1e-8)
theta=np.arccos(np.clip(v[:,2]/r,-1,1));az=np.arctan2(v[:,0],-v[:,1])
u=np.clip((theta-.001)/2.039*(T-1),0,T-1);w=(az+math.pi)/(2*math.pi)*(A-1)
i=np.floor(u).astype(int);j=np.floor(w).astype(int);ii=np.minimum(i+1,T-1);jj=np.minimum(j+1,A-1)
fu=(u-i)[:,None];fw=(w-j)[:,None]
f=field[i,j]*(1-fu)*(1-fw)+field[ii,j]*fu*(1-fw)+field[i,jj]*(1-fu)*fw+field[ii,jj]*fu*fw
clearance=np.maximum((r-f[:,0])*1.06,.001)
radial=ct+v/r[:,None]*(f[:,1]+clearance)[:,None];free=ct+v*1.06
b=np.clip((p[:,2]-(cs[2]-.075))/.075,0,1);b=b*b*(3-2*b)
p=radial*b[:,None]+free*(1-b[:,None])
hidden=[];mat=next(o for o in bpy.data.objects if o.type=='CURVES' and not o.hide_render and o.name.startswith('Authored')).data.materials[0]
for ob in bpy.data.objects:
 if not ob.hide_render and (ob.type=='CURVES' or ob.name.startswith('Original nape underlay')):
  hidden.append(ob.name);ob.hide_render=True;ob.hide_set(True)
paths=[];offset=0;N=65;t=np.linspace(0,1,N);cuts=0;roots=[];guards=0;regions={}
for size in sizes:
 q=p[offset:offset+size].copy();offset+=size;root=q[0].copy()
 if root[1]<-.09 and root[2]>1.80:
  region='front';height=1.771-.023*np.clip(abs(root[0])/.08,0,1)
 elif root[1]>.0:
  region='rear';height=1.635+.075*np.clip((root[2]-1.79)/.08,0,1)
 else:
  region='side';height=1.685+.070*np.clip((root[2]-1.79)/.08,0,1)
 height+=.006*np.sin(root[0]*57+root[1]*29)
 cross=np.flatnonzero(q[:,2]<height)
 if len(cross) and cross[0]>1:
  j=int(cross[0]);s=np.clip((q[j-1,2]-height)/max(q[j-1,2]-q[j,2],1e-9),0,1)
  q=np.vstack([q[:j],q[j-1]+(q[j]-q[j-1])*s]);cuts+=1
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))]
 if arc[-1]<1e-8:raise RuntimeError('Degenerate actual source strand')
 q=np.stack([np.interp(t*arc[-1],arc,q[:,k]) for k in range(3)],axis=1)
 hit,n,_,dist=tb.find_nearest(Vector(q[0]));delta=np.array(hit+n*.0005)-q[0]
 q+=delta[None]*(1-t[:,None])**3;roots.append(float(np.linalg.norm(delta)))
 for k in range(1,N):
  if q[k,2]<1.785:continue
  hit,n,_,dist=tb.find_nearest(Vector(q[k]));gap=(Vector(q[k])-hit).dot(n)
  if dist<.035 and gap<.0006:q[k]=np.array(hit+n*.0008);guards+=1
 paths.append(q.astype(np.float32));regions[region]=regions.get(region,0)+1
new=bpy.data.hair_curves.new('Bystedt actual styled shafts • post-evaluation layer scissors')
new.add_curves([N]*len(paths));new.attributes['position'].data.foreach_set('vector',np.array(paths).ravel())
radius=np.broadcast_to(.000037*(1-.997*t**3)**.65,(len(paths),N)).astype(np.float32)
new.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',radius.ravel());new.materials.append(mat)
ob=bpy.data.objects.new('Bystedt derivative • unreshaped source flow, regional scissors',new);bpy.context.scene.collection.objects.link(ob)
credits=bpy.data.texts.new('POST_EVALUATION_SCISSOR_CREDITS')
credits.write('Hair Styles by Daniel Bystedt, CC BY-SA, version unspecified in inspected evidence.\nhttps://www.blender.org/download/demo-files/\nNative style nodes and guides untouched except interpolation density. After evaluation: scalp transfer, regional whole-shaft cuts, red material and radius. Local derivative, not public standalone hair asset.\n')
out.mkdir(parents=True);render.mkdir(parents=True)
report=dict(source_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),stable_sha256=hashlib.sha256(stable.read_bytes()).hexdigest(),
 author='Daniel Bystedt',license='CC BY-SA; version unspecified',guides_reshaped=False,native_style_node_changes=changes,
 method='Original native artist flow evaluated before regional complete-shaft scissor cuts; scalp radial transfer; root attachment',
 curves=len(paths),curves_cut=cuts,regions=regions,radial_field_misses=misses,discrete_guard_events=guards,
 root_correction_quantiles_m=np.quantile(roots,[0,.5,.9,1]).tolist(),hidden_old_components=hidden,
 status='Unreviewed actual 3D study',scope='Discrete scalp points only; not complete segments/clothing/animation proof')
(out/'scissor_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in (['02_ThreeQuarter'] if '--single-view' in a else ['01_Front','02_ThreeQuarter','03_Side','04_Back']):
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('NATIVE_POST_SCISSORS_SAVED',version,len(paths),flush=True)
