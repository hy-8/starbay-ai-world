"""Sample actual UV triangles and painted opacity into editable native fibers.

Salman Ramezani Royalty Free geometry derivative stays local.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version,source_version=args[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in args[:2]):raise ValueError(args)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh directories only')
out.mkdir(parents=True);render.mkdir(parents=True)
source=ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
dg=bpy.context.evaluated_depsgraph_get();body=bpy.data.objects['CC0 male body • retained topology'];bv=BVHTree.FromObject(body,dg)
im=bpy.data.images['Tex_N_1.jpg'];pixels=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(pixels);alpha=pixels.reshape(im.size[1],im.size[0],4)[:,:,:3].mean(2)
def opacity(uv):
 a=np.clip((uv[:,0]*(im.size[0]-1)).astype(int),0,im.size[0]-1)
 b=np.clip((uv[:,1]*(im.size[1]-1)).astype(int),0,im.size[1]-1)
 return alpha[b,a]
rng=np.random.default_rng(101005);fibers=[];records=[];skipped=0;bangs=0
for ob in list(bpy.data.objects):
 if not ob.name.startswith('Salman layered hair derivative'):continue
 evaluated=ob.evaluated_get(dg);me=evaluated.to_mesh();me.calc_loop_triangles()
 xyz=np.array([ob.matrix_world@v.co for v in me.vertices]);uv=np.array([v.uv[:] for v in me.uv_layers.active.data])
 parent=np.arange(len(xyz))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for edge in me.edges:
  a,b=map(find,edge.vertices)
  if a!=b:parent[b]=a
 groups={}
 for tri in me.loop_triangles:groups.setdefault(find(tri.vertices[0]),[]).append(tri)
 for gi,tris in enumerate(groups.values()):
  uvtri=np.array([[uv[i] for i in tr.loops] for tr in tris]);sptri=np.array([[xyz[i] for i in tr.vertices] for tr in tris]);lo=uvtri.min((0,1));hi=uvtri.max((0,1))
  a=uvtri[:,0];e=uvtri[:,1]-a;f=uvtri[:,2]-a;det=e[:,0]*f[:,1]-e[:,1]*f[:,0]
  valid=np.abs(det)>1e-12;a=a[valid];e=e[valid];f=f[valid];det=det[valid];sptri=sptri[valid]
  if not len(det):continue
  def surface(points):
   delta=points[:,None,:]-a[None,:,:]
   b=(delta[:,:,0]*f[None,:,1]-delta[:,:,1]*f[None,:,0])/det[None,:]
   c=(e[None,:,0]*delta[:,:,1]-e[None,:,1]*delta[:,:,0])/det[None,:]
   inside=(b>=-1e-5)&(c>=-1e-5)&(b+c<=1.00001)
   ix=inside.argmax(1);alive=inside.any(1);rr=np.arange(len(points))
   v=sptri[ix,0]+b[rr,ix,None]*(sptri[ix,1]-sptri[ix,0])+c[rr,ix,None]*(sptri[ix,2]-sptri[ix,0])
   return v,alive
  count=160 if 'Caps' in ob.name else 240;accepted=0;vs=np.linspace(lo[1],hi[1],96);phase=rng.uniform(-.5,.5)
  for u in np.linspace(lo[0],hi[0],count+2)[1:-1]:
   u+=rng.uniform(-.00012,.00012);samples=np.c_[np.full(96,u),vs];sp,inside=surface(samples)
   alive=np.flatnonzero(inside&(opacity(samples)>.26))
   if len(alive)<15:skipped+=1;continue
   sp=sp[alive];arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(sp,axis=0),axis=1))]
   if arc[-1]<.012 or arc[-1]>.50:skipped+=1;continue
   # Pick the endpoint closer to the actual head as the root; compare both.
   gaps=[]
   for p in [sp[0],sp[-1]]:
    hit,n,_,dist=bv.find_nearest(Vector(p));gaps.append(dist)
   flip=gaps[-1]<gaps[0]
   if '--higher-root' in args and abs(sp[-1,2]-sp[0,2])>.008:flip=sp[-1,2]>sp[0,2]
   if flip:sp=sp[::-1];arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(sp,axis=0),axis=1))]
   t=np.linspace(0,1,56);s=np.stack([np.interp(t*arc[-1],arc,sp[:,j]) for j in range(3)],1)
   if '--extend-bangs' in args and s[-1,1]<-.095 and s[-1,2]>1.79:
    dz=(1.775+rng.uniform(-.014,.010))-s[-1,2]
    s[:,2]+=dz*t**1.7;s[:,1]-=.006*np.sin(np.pi*t);bangs+=1
   if '--lock-waves' in args:
    s[:,0]+=.004*np.sin(2.3*np.pi*t+phase)*np.sin(np.pi*t)
    s[:,1]+=.003*np.sin(2*np.pi*t+phase)*np.sin(np.pi*t)
   normal=np.array([s[0,0],s[0,1]+.044,max(s[0,2]-1.77,.012)]);normal/=max(np.linalg.norm(normal),1e-9)
   s+=normal[None,:]*(rng.uniform(-.0003,.0005)*np.sin(np.pi*t))[:,None]
   if rng.random()<.12:s+=normal[None,:]*(rng.uniform(.0005,.0018)*np.sin(np.pi*t))[:,None]
   for j,p in enumerate(s):
    hit,n,_,dist=bv.find_nearest(Vector(p));gap=(Vector(p)-hit).dot(n)
    if gap<.0006 and dist<.035:s[j]=np.array(hit+n*.0009)
   fibers.append(s.astype(np.float32));accepted+=1
  records.append({'object':ob.name,'component':gi,'sampled_fibers':accepted})
 evaluated.to_mesh_clear();ob.hide_render=True;ob.hide_viewport=True
if len(fibers)<1000:raise RuntimeError('Insufficient painted card coverage')
mat=bpy.data.materials.new('Physical crimson • actual UV-derived fibers');mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear()
bs=nt.nodes.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='COLOR';bs.inputs['Roughness'].default_value=.34;bs.inputs['Radial Roughness'].default_value=.40
info=nt.nodes.new('ShaderNodeHairInfo');ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.028,.0018,.003,1);ramp.color_ramp.elements[1].color=(.105,.008,.012,1)
output=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(info.outputs['Random'],ramp.inputs[0]);nt.links.new(ramp.outputs['Color'],bs.inputs['Color']);nt.links.new(bs.outputs[0],output.inputs[0])
cu=bpy.data.hair_curves.new('UV triangle sampled editable native hair');cu.add_curves([56]*len(fibers));cu.attributes['position'].data.foreach_set('vector',np.array(fibers).ravel())
t=np.linspace(0,1,56);radius=rng.uniform(.000028,.000040,(len(fibers),1))*(1-.998*t[None,:]**3)**.65
cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',radius.astype(np.float32).ravel());cu.materials.append(mat)
ob=bpy.data.objects.new('Salman native derivative • real painted UV strands',cu);bpy.context.scene.collection.objects.link(ob)
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for device in pref.devices:device.use=device.type=='OPTIX'
draft='--draft' in args;scene.cycles.device='GPU';scene.cycles.samples=64 if draft else 192;scene.cycles.use_denoising=False;scene.cycles_curves.shape='THICK'
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=80 if draft else 100
report={'version':version,'source':source_version,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'license':'Salman Ramezani, BlenderKit Royalty Free derivative, not CC0; geometry local','method':'Evaluated UV triangle barycentric sampling gated by actual grayscale opacity; native fibers','native_fibers':len(fibers),'components':len(records),'skipped_uv_columns':skipped,'extended_bangs':'--extend-bangs' in args,'draft':draft,'artistic_status':'unreviewed actual geometry','processing_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
report.update(extended_bang_fibers=bangs,higher_endpoint_root_rule='--higher-root' in args,coherent_millimeter_lock_waves='--lock-waves' in args)
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('UV_NATIVE_RENDERED',version,len(fibers),flush=True)
