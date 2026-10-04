"""Native-fiber study from actual fitted Ddr Rcs hair-card centerlines.

Source shape remains a Royalty Free derivative. Not CC0, not an image-based
replacement. Keep geometric source/derivative files local, never an asset pack.
"""
import bpy,sys,re,json,hashlib,math
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version,source_version=args[:2]
DRAFT='--draft' in args;WAVE='--wave-cut' in args
ATLAS='--atlas-fibers' in args
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in (version,source_version)):raise ValueError(args)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh output required')
out.mkdir(parents=True);render.mkdir(parents=True)
source=ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
card=bpy.data.objects['Ddr Rcs hair-card derivative • actual fitted geometry'];mesh=card.data
xyz=np.array([v.co[:] for v in mesh.vertices],float)
factor_attr=mesh.attributes['Factor']
factor=np.array([v.color_srgb[0] for v in factor_attr.data])
atlas_rejected=0
if ATLAS:
 # The source atlas is sparse. Filling every card uniformly with fibers made
 # an opaque bob; recover its real painted strand coverage and feathered tips.
 uv_layer=next((u for u in mesh.uv_layers if u.active_render),mesh.uv_layers.active)
 loop_uv=np.array([v.uv[:] for v in uv_layer.data]);loop_ids=np.array([v.vertex_index for v in mesh.loops])
 vertex_uv=np.zeros((len(xyz),2));uv_count=np.zeros(len(xyz))
 np.add.at(vertex_uv,loop_ids,loop_uv);np.add.at(uv_count,loop_ids,1);vertex_uv/=np.maximum(uv_count[:,None],1)
 image=bpy.data.images['depht+alpha.png'];pixel=np.empty(len(image.pixels),np.float32);image.pixels.foreach_get(pixel)
 alpha=pixel.reshape(image.size[1],image.size[0],4)[:,:,3].copy();del pixel
 def sample_alpha(uv):
  x=np.clip(uv[:,0],0,1)*(alpha.shape[1]-1);y=np.clip(uv[:,1],0,1)*(alpha.shape[0]-1)
  a=x.astype(int);b=y.astype(int);aa=np.minimum(a+1,alpha.shape[1]-1);bb=np.minimum(b+1,alpha.shape[0]-1);u=x-a;v=y-b
  return alpha[b,a]*(1-u)*(1-v)+alpha[b,aa]*u*(1-v)+alpha[bb,a]*(1-u)*v+alpha[bb,aa]*u*v
parent=np.arange(len(xyz))
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for edge in mesh.edges:
 a,b=map(int,edge.vertices);a=find(a);b=find(b)
 if a!=b:parent[b]=a
groups={}
for i in range(len(xyz)):groups.setdefault(find(i),[]).append(i)
body=bpy.data.objects['CC0 male body • retained topology'];bpy.context.view_layer.update()
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
N=56;t=np.linspace(0,1,N);rng=np.random.default_rng(100504)
fibers=[];guide_records=[];skipped=0;bangs=0;shortened=0;repairs=0
for index,ids in enumerate(groups.values()):
 ids=np.asarray(ids);values=np.round(factor[ids],6);unique=np.unique(values)
 if len(unique)<4:skipped+=1;continue
 centers=[];widths=[];uv_low=[];uv_high=[]
 for u in unique:
  row_ids=ids[values==u];row=xyz[row_ids];p=row.mean(axis=0);centers.append(p)
  delta=row-p
  if len(row)>1:
   _,_,v=np.linalg.svd(delta,full_matrices=False);across=v[0]
   if widths and np.dot(across,widths[-1])<0:across=-across
   widths.append(across*max(.0008,float(np.max(np.abs(delta@across)))))
   if ATLAS:
    coordinates=delta@across;uv_low.append(vertex_uv[row_ids[np.argmin(coordinates)]]);uv_high.append(vertex_uv[row_ids[np.argmax(coordinates)]])
  else:
   widths.append(widths[-1] if widths else np.array([.001,0,0]))
   if ATLAS:uv_low.append(vertex_uv[row_ids[0]]);uv_high.append(vertex_uv[row_ids[0]])
 centers=np.array(centers);widths=np.array(widths)
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(centers,axis=0),axis=1))]
 keep=np.r_[True,np.diff(arc)>1e-7];arc=arc[keep];centers=centers[keep];widths=widths[keep]
 if ATLAS:uv_low=np.asarray(uv_low)[keep];uv_high=np.asarray(uv_high)[keep]
 if len(arc)<4 or arc[-1]<.007:skipped+=1;continue
 length=float(arc[-1]);root=centers[0].copy();endpoint=centers[-1].copy();limit=1.0
 classification='retained authored flow'
 if WAVE and endpoint[2]<1.665:
  desired_z=(1.690+rng.uniform(-.026,.025) if root[1]<-.038 or abs(root[0])>.065 else 1.630+rng.uniform(-.030,.040)) if ATLAS else 1.630+rng.uniform(-.014,.024)
  limit=np.clip((root[2]-desired_z)/max(root[2]-endpoint[2],.001),.48,.90)
  classification='layered side/nape shortening';shortened+=1
 q=t*arc[-1]*limit
 base=np.stack([np.interp(q,arc,centers[:,j]) for j in range(3)],axis=1)
 across=np.stack([np.interp(q,arc,widths[:,j]) for j in range(3)],axis=1)
 is_bang=endpoint[1]<(-.098 if ATLAS else -.132) and endpoint[2]>(1.735 if ATLAS else 1.755) and root[2]>1.813
 if WAVE:
  phase=rng.uniform(-.35,.35)
  if is_bang:
   heavy=root[0]<.024;tip=base[-1].copy()
   tip[0]=np.clip(tip[0]+(-.017 if heavy else .012),-.091,.086)
   tip[2]=(1.759 if heavy else 1.780)+rng.uniform(-.012,.017)
   if abs(tip[0])<.012:tip[2]=max(tip[2],1.782)
   base+=(tip-base[-1])[None,:]*t[:,None]**1.7
   base[:,0]+=(rng.uniform(.008,.014) if ATLAS else rng.uniform(.004,.009))*np.sin(t*2*np.pi+phase)*np.sin(np.pi*t)
   base[:,1]-=rng.uniform(.003,.008)*np.sin(np.pi*t)
   classification='asymmetric extended wavy bang';bangs+=1
  else:
   # Small coherent waves on each authored card, never a repeated big coil.
   base[:,0]+=rng.uniform(.003,.008)*np.sin(t*2.5*np.pi+phase)*np.sin(np.pi*t)
   base[:,1]+=rng.uniform(.002,.006)*np.sin(t*2*np.pi+phase)*np.sin(np.pi*t)
   base[:,2]+=rng.uniform(.001,.004)*np.sin(t*2*np.pi)*np.sin(np.pi*t)
 tangent=np.gradient(base,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-8)
 width_length=np.linalg.norm(across,axis=1)
 cross_dir=across-tangent*np.sum(across*tangent,axis=1)[:,None]
 cross_dir/=np.maximum(np.linalg.norm(cross_dir,axis=1)[:,None],1e-8)
 across=cross_dir*width_length[:,None];normal=np.cross(tangent,cross_dir)
 count=int(np.clip(90+np.max(width_length)*20000,100,250))
 if ATLAS:
  # Texture UVs traverse the full original tip even when the spatial cut is shorter.
  a_uv=np.stack([np.interp(t*arc[-1],arc,uv_low[:,j]) for j in range(2)],axis=1)
  b_uv=np.stack([np.interp(t*arc[-1],arc,uv_high[:,j]) for j in range(2)],axis=1)
 accepted=0
 for strand in range(count):
  u=rng.uniform(-.92,.92)
  end_fraction=1.
  if ATLAS:
   texture_alpha=sample_alpha(a_uv*(1-(u+1)/2)+b_uv*((u+1)/2))
   alive=np.flatnonzero(texture_alpha>.18)
   if len(alive)<10 or texture_alpha[8:40].mean()<.23:atlas_rejected+=1;continue
   end_fraction=max(.25,float(alive[-1])/(N-1));accepted+=1
  s=base+across*u
  s+=normal*(rng.normal(0,.00045)*np.sin(np.pi*t))[:,None]
  phase_s=rng.uniform(0,2*np.pi)
  s+=normal*(rng.uniform(.00008,.00024)*np.sin(t*10+phase_s)*np.sin(np.pi*t))[:,None]
  if rng.random()<.34:
   frac=rng.uniform(.89,.995);s=np.stack([np.interp(t*frac,t,s[:,j]) for j in range(3)],axis=1)
  if ATLAS and end_fraction<1:
   s=np.stack([np.interp(t*end_fraction,t,s[:,j]) for j in range(3)],axis=1)
  for j,p in enumerate(s):
   hit,n,face,dist=bv.find_nearest(Vector(p));gap=(Vector(p)-hit).dot(n)
   if j==0:s[j]=np.array(hit+n*.0005)
   elif gap<.0007 and dist<.035:s[j]=np.array(hit+n*.0009);repairs+=1
  fibers.append(s.astype(np.float32))
 guide_records.append(dict(source_component=index,kind=classification,source_length_m=length,retained_arc_fraction=float(limit),fibers=accepted if ATLAS else count,control_points_m=base[np.linspace(0,N-1,10).astype(int)].tolist()))
for ob in list(bpy.data.objects):
 if ob.type=='CURVES' or ob==card:ob.hide_render=True;ob.hide_viewport=True
col=bpy.data.collections.new('05_Licensed_Card_Derived_Native_Groom');bpy.context.scene.collection.children.link(col)
mat=bpy.data.materials.new('Project physical crimson hair • Ddr Rcs geometry derivative');mat.use_nodes=True
nt=mat.node_tree;nt.nodes.clear();output=nt.nodes.new('ShaderNodeOutputMaterial');bs=nt.nodes.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='COLOR'
bs.inputs['Roughness'].default_value=.30;bs.inputs['Radial Roughness'].default_value=.38
info=nt.nodes.new('ShaderNodeHairInfo');ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.026,.0015,.0025,1);ramp.color_ramp.elements[1].color=(.079,.0045,.006,1)
nt.links.new(info.outputs['Random'],ramp.inputs[0]);nt.links.new(ramp.outputs['Color'],bs.inputs['Color']);nt.links.new(bs.outputs[0],output.inputs[0])
if len(fibers)<1000:raise RuntimeError('Insufficient actual atlas-derived fiber coverage; inspect UVs')
positions=np.array(fibers,np.float32);cu=bpy.data.hair_curves.new('Ddr Rcs card-derived native fibers');cu.add_curves([N]*len(positions));cu.attributes['position'].data.foreach_set('vector',positions.ravel())
rad=rng.uniform(.000027,.000040,(len(positions),1))*(1-.997*t[None,:]**3)**.65
cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',rad.astype(np.float32).ravel());cu.materials.append(mat)
ob=bpy.data.objects.new('Licensed Ddr Rcs derivative • actual native curves',cu);col.objects.link(ob)
gc=bpy.data.collections.new('08_Card_Derived_Guide_Evidence');bpy.context.scene.collection.children.link(gc);gc.hide_render=True
gd=bpy.data.curves.new('Baked source-card centerline evidence','CURVE');gd.dimensions='3D'
for record in guide_records:
 sp=gd.splines.new('POLY');points=record['control_points_m'];sp.points.add(len(points)-1)
 for p,v in zip(sp.points,points):p.co=(*v,1)
guide=bpy.data.objects.new('Guide evidence • not live-linked',gd);gc.objects.link(guide);guide.hide_render=True
(out/'licensed_groom_design.json').write_text(json.dumps(guide_records,indent=2),encoding='utf-8')
credits=bpy.data.texts.get('DDR_RCS_HAIR_CREDITS')
if credits:credits.write('Further modifications: recover 424 card centerlines by connectivity and Factor; layered nape shortening, asymmetric fringe extension and mild spatial waves; convert actual geometry to native fibers with body-root clearance. Textured source cards remain hidden. Guides are baked evidence, not live-linked. Royalty Free derivative, not CC0.\n')
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for device in pref.devices:device.use=device.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=64 if DRAFT else 192;scene.cycles.use_denoising=False;scene.cycles_curves.shape='THICK'
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=80 if DRAFT else 100
report=dict(version=version,source=source_version,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),asset_author='Ddr Rcs',license='BlenderKit Royalty Free derivative, not CC0; keep geometric assets local, no standalone asset resale',method='actual fitted card centerlines, independent fiber cross-section, optional layered shortening and wavy fringe extension',guides=len(guide_records),skipped_components=skipped,native_fibers=len(fibers),extended_bang_guides=bangs,shortened_guides=shortened,clearance_repairs=repairs,wave_cut=WAVE,draft=DRAFT,status='unreviewed actual geometry study')
report.update(atlas_coverage_sampling=ATLAS,atlas_rejected_columns=atlas_rejected)
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('LICENSED_NATIVE_GROOM_RENDERED',version,len(fibers),bangs,shortened,flush=True)
