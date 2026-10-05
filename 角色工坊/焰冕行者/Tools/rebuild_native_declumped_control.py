"""Source-node control: reduce native clump strength before evaluation.

Reuse recorded layercut04 guide cut/loose/part/sweep settings, then control
clump fields or native roll. Fit/reflow without character mesh changes.
CC BY-SA derivative remains local; no generated portrait substitution.
"""
import bpy,sys,re,json,math,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version=a[0]
factor_only='--factor-only' in a
factor_scale=float(a[a.index('--factor-scale')+1]) if '--factor-scale' in a else .55
if not 0<factor_scale<=1:raise ValueError('Require bounded clump scale')
roll_factor=float(a[a.index('--roll-factor')+1]) if '--roll-factor' in a else .18
if not 0<=roll_factor<=.5:raise ValueError('Require bounded native roll')
branch_control='--branch-control' in a
affine_transfer='--affine-transfer' in a
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh clump control only')
asset=ROOT/'Source/BlenderHairStyles/Bystedt_HairStyles.blend'
stable=ROOT/'Exports/nativecoverage05/Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(asset),use_scripts=False)
hair=bpy.data.objects['long hair main'];rng=np.random.default_rng(100406)
for c in hair.data.curves:
 p=np.array([v.position for v in c.points],float)*.1;root=p[0].copy()
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
 front=root[1]<-.087 and root[2]>1.586 and -.045<root[0]<.075
 back=root[1]>-.015
 limit=rng.uniform(.108,.145) if front else (rng.uniform(.173,.240) if back else rng.uniform(.122,.180))
 if c.index%4==0:limit*=.77
 tt=np.linspace(0,min(limit,float(arc[-1])),len(p))
 p=np.stack([np.interp(tt,arc,p[:,j]) for j in range(3)],axis=1);t=np.linspace(0,1,len(p))
 if front:
  end=np.array([root[0]+.027,-.180+abs(root[0])*.10,1.541-.012*abs(root[0])/.08])
  if abs(end[0])<.025:end[2]=max(end[2],1.554)
  if root[0]<-.005:end[0]=root[0]-.015;end[2]=1.549-.016*abs(root[0])/.060
  elif root[0]<.015:end[0]=root[0]+.010;end[2]=1.548
  end[2]+=rng.uniform(-.012,.012)
  p+=(end-p[-1])[None]*np.maximum(0,(t-.18)/.82)[:,None]**1.50
  p[:,1]-=.011*np.sin(np.pi*t);p[:,2]+=.006*np.sin(np.pi*t)
 phase=(math.floor(root[0]/.012)+2*math.floor(root[1]/.014))*.81
 p[:,0]+=.004*np.sin(t*7.5+phase)*np.sin(np.pi*t)
 p[:,1]+=.003*np.sin(t*7+phase+.8)*np.sin(np.pi*t)
 if front:
  if root[0]>=-.005:p[:,0]+=.010*np.sin(t*7.0)*np.sin(np.pi*t);p[:,2]+=.004*np.sin(np.pi*t)
  else:p[:,0]-=.004*np.sin(t*6.0)*np.sin(np.pi*t)
 for v,pt in zip(c.points,p/.1):v.position=pt
changes=[]
for mod in hair.modifiers:
 if mod.type!='NODES':continue
 for node in mod.node_group.nodes:
  if node.type!='GROUP':continue
  name=node.node_tree.name;values={};control=False
  if name.startswith('Roll Hair Curves'):values={'Factor':roll_factor,'Roll Radius':.14,'Roll Length':.65,'Roll Taper':.65}
  elif name.startswith('Hair Curves Noise'):values={'Distance':.045,'Scale along Curve':4.5}
  elif name.startswith('Interpolate Hair Curves'):values={'Density':18000.0}
  elif name.startswith('Duplicate Hair Curves'):values={'Amount':4,'Radius':.026}
  elif name.startswith('Set Hair Curve Profile'):values={'Radius':.00040}
  elif name.startswith('Clump Hair Curves'):
   control=True
   if factor_only:
    sock=node.inputs['Factor']
    if sock.is_linked:
     link=sock.links[0];upstream=link.from_socket;upstream_name=link.from_node.name
     ng=mod.node_group;ng.links.remove(link)
     scale=ng.nodes.new('ShaderNodeMath');scale.operation='MULTIPLY';scale.label='Local clump control, preserve source profile';scale.inputs[1].default_value=factor_scale
     ng.links.new(upstream,scale.inputs[0]);ng.links.new(scale.outputs[0],sock)
     changes.append(dict(node=name,socket='Factor',before='Linked source field from '+upstream_name,after='Same source field multiplied by '+str(factor_scale),new_clump_control=True))
    else:
     values={'Factor':float(sock.default_value)*factor_scale}
   else:
    factor=float(node.inputs['Factor'].default_value);values={'Factor':.48 if factor>.5 else .12,'Tip Spread':.032,'Clump Offset':.025}
  for key,value in values.items():
   sock=node.inputs.get(key)
   if sock is None or sock.is_linked:continue
   changes.append(dict(node=name,socket=key,before=float(sock.default_value),after=value,new_clump_control=control));sock.default_value=value
if branch_control:
 tagged=0
 for mod in hair.modifiers:
  if mod.type!='NODES':continue
  ng=mod.node_group;join=ng.nodes.get('Join Geometry.001')
  if join is None:continue
  links=list(join.inputs['Geometry'].links)
  assert {link.from_node.name for link in links}=={'Join Geometry','Group.012'},'Inspect source join before changing it'
  for link in links:
   upstream=link.from_socket;origin=link.from_node.name;ng.links.remove(link)
   store=ng.nodes.new('GeometryNodeStoreNamedAttribute');store.data_type='INT';store.domain='CURVE'
   store.inputs['Name'].default_value='native_source_branch'
   store.inputs['Value'].default_value=1 if origin=='Join Geometry' else 2
   ng.links.new(upstream,store.inputs['Geometry']);ng.links.new(store.outputs['Geometry'],join.inputs['Geometry']);tagged+=1
 assert tagged==2,'Expected two actual source branches'
hair.update_tag();bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
cu=hair.evaluated_get(dg).data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
sizes=[c.points_length for c in cu.curves];m=np.array(hair.matrix_world)
tags=None
if branch_control:
 attr=cu.attributes.get('native_source_branch');assert attr is not None and attr.domain=='CURVE'
 tags=np.empty(len(cu.curves),np.int32);attr.data.foreach_get('value',tags)
 assert set(tags)=={1,2}
p=(p@m[:3,:3].T+m[:3,3]-np.array([5,0,0]))*.1
head=bpy.data.objects['head'];sv=np.array([head.matrix_world@v.co for v in head.data.vertices],float)*.1
sb=BVHTree.FromPolygons([Vector(v) for v in sv],[list(f.vertices) for f in head.data.polygons])
cs=np.array([0,-.063,float(sv[:,2].max())-.100]);ct=np.array([0,-.044,1.771])
print('DECLUMP_SOURCE_EVALUATED',len(sizes),flush=True)
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
transfer_report={}
if affine_transfer:
 theta_grid,az_grid=np.meshgrid(np.linspace(.001,2.04,T),np.linspace(-math.pi,math.pi,A),indexing='ij')
 directions=np.stack([np.sin(theta_grid)*np.sin(az_grid),-np.sin(theta_grid)*np.cos(az_grid),np.cos(theta_grid)],axis=2)
 # Fit one spatial map on measured upper scalp rays. Every free shaft uses
 # the same map rather than a different radial projection at each point.
 mask=(theta_grid<1.83)&((np.cos(az_grid)<.25)|(theta_grid<1.55))
 src=(cs+directions*field[:,:,0,None])[mask];dst=(ct+directions*field[:,:,1,None])[mask]
 ww=np.sqrt(np.maximum(np.sin(theta_grid[mask]),.02))
 design=np.column_stack([src,np.ones(len(src))])
 affine=np.linalg.lstsq(design*ww[:,None],dst*ww[:,None],rcond=None)[0]
 fitted=design@affine;residual=np.linalg.norm(fitted-dst,axis=1)
 p=np.column_stack([p,np.ones(len(p))])@affine
 transfer_report=dict(type='One global affine fit on actual source/target upper-scalp rays',correspondences=len(src),
  scalp_ray_residual_quantiles_m=np.quantile(residual,[0,.5,.9,1]).tolist(),
  linear_map_singular_values=np.linalg.svd(affine[:3],compute_uv=False).tolist(),
  root_reflow_disabled=True,whole_shaft_root_translation=True)
else:
 radial=ct+v/r[:,None]*(f[:,1]+np.maximum((r-f[:,0])*1.06,.001))[:,None];free=ct+v*1.06
 b=np.clip((p[:,2]-(cs[2]-.075))/.075,0,1);b=b*b*(3-2*b);p=radial*b[:,None]+free*(1-b[:,None])
 transfer_report=dict(type='Per-point radial/free blend, initial root region reflow')
previous=bpy.data.objects['Bystedt layercut derivative • native root reflow'];mat=previous.data.materials[0];previous.hide_render=True;previous.hide_set(True)
paths=[];offset=0;N=65;t=np.linspace(0,1,N);rootshift=[];contact=0
for size in sizes:
 old=p[offset:offset+size];offset+=size
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(old,axis=0),axis=1))]
 if arc[-1]<1e-8:raise RuntimeError('Degenerate source fiber')
 q=np.stack([np.interp(t*arc[-1],arc,old[:,k]) for k in range(3)],axis=1);root=q[0].copy()
 if not affine_transfer and root[2]>1.81 and root[1]<.02:
  u=np.clip(t/.48,0,1);weight=1-u*u*(3-2*u)
  for k in range(N):
   if weight[k]<.001 or q[k,2]<1.818:continue
   hit,n,_,dist=tb.find_nearest(Vector(q[k]))
   if dist>.055:continue
   target=np.array(hit+n*(.0006+.0075*np.sin(np.pi*u[k])))
   q[k]=q[k]*(1-weight[k])+target*weight[k]
  for _ in range(5):
   mid=(q[:-2]+2*q[1:-1]+q[2:])*.25;ww=weight[1:-1]*.55
   q[1:-1]=q[1:-1]*(1-ww[:,None])+mid*ww[:,None]
 hit,n,_,dist=tb.find_nearest(Vector(q[0]));delta=np.array(hit+n*.0005)-q[0]
 q+=delta[None] if affine_transfer else delta[None]*(1-t[:,None])**3
 rootshift.append(float(np.linalg.norm(delta)))
 for _ in range(2):
  correction=np.zeros_like(q)
  for k in range(1,N-1):
   if q[k,2]<1.80:continue
   hit,n,_,dist=tb.find_nearest(Vector(q[k]));gap=(Vector(q[k])-hit).dot(n)
   if dist<.025 and gap<.0004:
    d=np.array(n)*(.0005-gap);contact+=1
    for l in range(max(1,k-2),min(N-1,k+3)):correction[l]+=d*np.exp(-.5*((l-k)/1.15)**2)
  q+=correction
 paths.append(q.astype(np.float32))
new=bpy.data.hair_curves.new('Bystedt source-node declumped complete shafts');new.add_curves([N]*len(paths));new.attributes['position'].data.foreach_set('vector',np.array(paths).ravel())
radius=np.broadcast_to(.000037*(1-.997*t**3)**.65,(len(paths),N)).astype(np.float32)
new.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',radius.ravel());new.materials.append(mat)
if branch_control:new.attributes.new('native_source_branch','INT','CURVE').data.foreach_set('value',tags)
ob=bpy.data.objects.new('Bystedt derivative • relaxed native clump nodes',new);bpy.context.scene.collection.objects.link(ob)
out.mkdir(parents=True);render.mkdir(parents=True)
report=dict(source_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),character_source_sha256=hashlib.sha256(stable.read_bytes()).hexdigest(),
 author='Daniel Bystedt',license='CC BY-SA; version unspecified',native_node_changes=changes,
 factor_only=factor_only,linked_factor_profile_scale=factor_scale if factor_only else None,native_roll_factor=roll_factor,
 source_branches_tagged=branch_control,
 head_transfer=transfer_report,
 method='Reuse recorded layercut04 loose/part/sweep guide-design settings (native Roll Factor '+str(roll_factor)+'); '+('scale all three clump Factors, multiply the two linked source fields; preserve Tip Spread/Clump Offset' if factor_only else 'Unlinked Factor and Tip Spread/Clump Offset controls; the two linked Factor sockets unchanged')+' before evaluation; '+('whole-shaft affine scalp transfer, root reflow disabled' if affine_transfer else 'scalp transfer and root reflow')+', retain all short support',
 strands=len(paths),field_misses=misses,smooth_contact_events=contact,root_correction_quantiles_m=np.quantile(rootshift,[0,.5,.9,1]).tolist(),
 status='Unreviewed actual source-clump study',scope='Same guide-shaping design, new evaluation; not identical final geometry outside clumps or full collision/art acceptance')
(out/'declump_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
name='02_ThreeQuarter';s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
if branch_control:
 data=np.array(paths);branch_records=[];ob.hide_render=True
 for branch,label in [(1,'08_MainOnly'),(2,'09_AccentOnly')]:
  ix=np.flatnonzero(tags==branch);pts=data[ix];rad=radius[ix]
  branch_cu=bpy.data.hair_curves.new('Diagnostic actual native branch '+str(branch));branch_cu.add_curves([N]*len(ix))
  branch_cu.attributes['position'].data.foreach_set('vector',pts.ravel());branch_cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',rad.ravel());branch_cu.materials.append(mat)
  separate=bpy.data.objects.new('Diagnostic source branch '+str(branch),branch_cu);s.collection.objects.link(separate)
  s.render.filepath=str(render/(label+'.png'));bpy.ops.render.render(write_still=True);separate.hide_render=True
  roots=pts[:,0];tips=pts[:,-1]
  branch_records.append(dict(tag=branch,source='Main interpolated/clumped groom' if branch==1 else 'Separate authored-strand duplicate/clump/noise accent branch',
   fibers=len(ix),highest_z_m=float(pts[:,:,2].max()),
   frontal_tip_fibers=int(((tips[:,1]<-.14)&(tips[:,2]<1.81)&(roots[:,2]>1.81)&(roots[:,1]<-.035)).sum()),
   visible_crown_points=int(((pts[:,:,2]>1.86)&(pts[:,:,1]<.02)).sum())))
 (out/'source_branch_manifest.json').write_text(json.dumps(dict(branches=branch_records,
  tag_method='Store integer CURVE attribute on each observed original source join input, propagated through whole-shaft fitting/resampling',
  saved_model='Full tagged groom; split views temporary diagnostics, saved whole model unchanged',
  short_support_retained_in_both_diagnostics=True,
  scope='Actual source attribution and one-view removal controls, not whole-head art acceptance'),indent=2),encoding='utf-8')
print('DECLUMPED_NATIVE_GROOM_SAVED',version,len(paths),flush=True)
