"""Cut and restyle authored long-hair guides before native node interpolation.

Daniel Bystedt Hair Styles derivative, CC BY-SA (version unspecified).
Fresh local studies only. Do not mistake controls or statistics for approval.
"""
import bpy,sys,re,json,math,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version=args[0]
LOOSE='--loose' in args
PART='--part' in args
SWEEP='--sweep' in args
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh version required')
out.mkdir(parents=True);render.mkdir(parents=True)
source=ROOT/'Source/BlenderHairStyles/Bystedt_HairStyles.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
hair=bpy.data.objects['long hair main'];rng=np.random.default_rng(100406)
guides=[];design=[]
for c in hair.data.curves:
 p=np.array([v.position for v in c.points],float)*.1;root=p[0].copy()
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
 front=root[1]<-.087 and root[2]>1.586 and -.045<root[0]<.075
 back=root[1]>-.015
 limit=rng.uniform(.108,.145) if front else (rng.uniform(.173,.240) if back else rng.uniform(.122,.180))
 if len(guides)%4==0:limit*=.77
 q=np.linspace(0,min(limit,float(arc[-1])),len(p))
 p=np.stack([np.interp(q,arc,p[:,j]) for j in range(3)],axis=1)
 t=np.linspace(0,1,len(p))
 if front:
  # Style source guides themselves, so native clump/noise/trim acts on bangs.
  end=np.array([root[0]-.027,-.180+abs(root[0])*.10,1.548-.012*abs(root[0])/.08])
  if LOOSE:
   end[0]=root[0]+.027
   end[2]=1.541-.012*abs(root[0])/.08
   if abs(end[0])<.025:end[2]=max(end[2],1.554)
  if PART:
   if root[0]<-.005:
    end[0]=root[0]-.015
    end[2]=1.549-.016*abs(root[0])/.060
   elif root[0]<.015:
    end[0]=root[0]+.010
    end[2]=1.548
  end[2]+=rng.uniform(-.012,.012)
  p+=(end-p[-1])[None,:]*np.maximum(0,(t-.18)/.82)[:,None]**1.50
  p[:,1]-=.011*np.sin(np.pi*t);p[:,2]+=.006*np.sin(np.pi*t)
 if LOOSE:
  phase=(math.floor(root[0]/.012)+2*math.floor(root[1]/.014))*.81
  p[:,0]+=.004*np.sin(t*7.5+phase)*np.sin(np.pi*t)
  p[:,1]+=.003*np.sin(t*7+phase+.8)*np.sin(np.pi*t)
 if SWEEP and front:
  if root[0]>=-.005:
   p[:,0]+=.010*np.sin(t*7.0)*np.sin(np.pi*t)
   p[:,2]+=.004*np.sin(np.pi*t)
  else:
   p[:,0]-=.004*np.sin(t*6.0)*np.sin(np.pi*t)
 for v,pt in zip(c.points,p/.1):v.position=pt
 guides.append(p);design.append(dict(root=root.tolist(),cut_length_m=float(q[-1]),front=bool(front),back=bool(back)))
changes=[]
for mod in hair.modifiers:
 if mod.type!='NODES':continue
 for node in mod.node_group.nodes:
  if node.type!='GROUP':continue
  name=node.node_tree.name;values={}
  if name.startswith('Roll Hair Curves'):values={'Factor':.18 if LOOSE else .45,'Roll Radius':.14 if LOOSE else .20,'Roll Length':.65 if LOOSE else .78,'Roll Taper':.65}
  elif name.startswith('Hair Curves Noise'):values={'Distance':.045,'Scale along Curve':4.5}
  elif name.startswith('Set Hair Curve Profile'):values={'Radius':.00040}
  elif name.startswith('Interpolate Hair Curves'):values={'Density':18000.0 if LOOSE else 10000.0}
  elif name.startswith('Duplicate Hair Curves'):values={'Amount':4,'Radius':.026}
  for key,value in values.items():
   sock=node.inputs.get(key)
   if sock is None or sock.is_linked:continue
   changes.append(dict(node=name,socket=key,before=str(sock.default_value),after=value));sock.default_value=value
hair.update_tag();bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
cu=hair.evaluated_get(dg).data
xyz=np.empty(len(cu.points)*3,np.float32);cu.attributes['position'].data.foreach_get('vector',xyz);xyz=xyz.reshape(-1,3).astype(float)
sizes=np.array([len(c.points) for c in cu.curves],np.int32)
rad=np.empty(len(cu.points),np.float32);cu.attributes['radius'].data.foreach_get('value',rad);rad=np.maximum(rad*.1,.000002)
m=np.array(hair.matrix_world);xyz=xyz@m[:3,:3].T+m[:3,3];xyz[:,0]-=5;xyz*=.1
guides=[(p/.1@m[:3,:3].T+m[:3,3]-np.array([5,0,0]))*.1 for p in guides]
head=bpy.data.objects['head'];sv=np.array([head.matrix_world@v.co for v in head.data.vertices],float)*.1
sb=BVHTree.FromPolygons([Vector(v) for v in sv],[list(p.vertices) for p in head.data.polygons])
cs=np.array([0,-.063,float(sv[:,2].max())-.100]);ct=np.array([0,-.044,1.771])
print('LAYER_CUT_BAKED',len(sizes),len(xyz),'FRONT_GUIDES',sum(d['front'] for d in design),flush=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports/hairrecongroom05/Ember_Regent.blend'),use_scripts=False)
body=bpy.data.objects['CC0 male body • retained topology'];bpy.context.view_layer.update()
tb=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
T=129;A=257;field=np.zeros((T,A,2));misses=0
for i,theta in enumerate(np.linspace(.001,2.04,T)):
 for j,az in enumerate(np.linspace(-math.pi,math.pi,A)):
  d=Vector((math.sin(theta)*math.sin(az),-math.sin(theta)*math.cos(az),math.cos(theta)))
  sh,_,_,sd=sb.ray_cast(Vector(cs),d,.5);th,_,_,td=tb.ray_cast(Vector(ct),d,.5)
  if sh is None or th is None:misses+=1;sd=.100;td=.103
  field[i,j]=[sd,td]
def transfer(p):
 v=p-cs;length=np.maximum(np.linalg.norm(v,axis=1),1e-8)
 theta=np.arccos(np.clip(v[:,2]/length,-1,1));az=np.arctan2(v[:,0],-v[:,1])
 u=np.clip((theta-.001)/2.039*(T-1),0,T-1);w=(az+math.pi)/(2*math.pi)*(A-1)
 i=np.floor(u).astype(int);j=np.floor(w).astype(int);ii=np.minimum(i+1,T-1);jj=np.minimum(j+1,A-1);fu=(u-i)[:,None];fw=(w-j)[:,None]
 f=field[i,j]*(1-fu)*(1-fw)+field[ii,j]*fu*(1-fw)+field[i,jj]*(1-fu)*fw+field[ii,jj]*fu*fw
 clearance=np.maximum((length-f[:,0])*1.06,.0010)
 radial=ct+v/length[:,None]*(f[:,1]+clearance)[:,None];free=ct+v*1.06
 b=np.clip((p[:,2]-(cs[2]-.075))/.075,0,1);b=b*b*(3-2*b)
 return radial*b[:,None]+free*(1-b[:,None])
xyz=transfer(xyz);guides=[transfer(g) for g in guides]
if '--mirror' in args:xyz[:,0]*=-1;guides=[g*np.array([-1,1,1]) for g in guides]
offset=0;repairs=0
for size in sizes:
 size=int(size);s=xyz[offset:offset+size];hit,n,_,dist=tb.find_nearest(Vector(s[0]))
 if dist<.030:s+=(np.array(hit+n*.0005)-s[0])[None,:]*(1-np.linspace(0,1,size))[:,None]**4
 for j,pt in enumerate(s):
  if pt[2]<1.775:continue
  hit,n,_,dist=tb.find_nearest(Vector(pt));gap=(Vector(pt)-hit).dot(n)
  if gap<.0008 and dist<.04:s[j]=np.array(hit+n*.0010);repairs+=1
 rad[offset:offset+size]=max(float(rad[offset]),.000030)*(1-.994*np.linspace(0,1,size)**3)**.65
 offset+=size
col=bpy.data.collections['05_Hair']
for o in list(col.objects):bpy.data.objects.remove(o,do_unlink=True)
cu=bpy.data.hair_curves.new('Cut Bystedt long hairstyle, fitted native strands');cu.add_curves(sizes.tolist())
cu.attributes['position'].data.foreach_set('vector',xyz.astype(np.float32).ravel());cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',rad)
mat=bpy.data.materials.new('Deep cherry layer cut');mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear()
bs=nt.nodes.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='COLOR';bs.inputs['Roughness'].default_value=.32;bs.inputs['Radial Roughness'].default_value=.44
hi=nt.nodes.new('ShaderNodeHairInfo');r=nt.nodes.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(.010,.0011,.0015,1);r.color_ramp.elements[1].color=(.055,.0045,.006,1)
nt.links.new(hi.outputs['Random'],r.inputs[0]);nt.links.new(r.outputs[0],bs.inputs['Color']);o=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(bs.outputs[0],o.inputs[0]);cu.materials.append(mat)
ob=bpy.data.objects.new('Daniel Bystedt adapted layered cut • CC BY-SA',cu);col.objects.link(ob)
gc=bpy.data.collections.new('06_Licensed_Cut_Guides');bpy.context.scene.collection.children.link(gc);gc.hide_render=True
gd=bpy.data.curves.new('Authored long-hair guides, cut before node styling','CURVE');gd.dimensions='3D'
for g in guides:
 sp=gd.splines.new('POLY');sp.points.add(len(g)-1)
 for p,q in zip(sp.points,g):p.co=(*q,1)
go=bpy.data.objects.new('Cut and shaped source guides • CC BY-SA',gd);gc.objects.link(go);go.hide_render=True
tx=bpy.data.texts.new('ADAPTED_HAIR_CREDITS');tx.write('Hair Styles by Daniel Bystedt\nhttps://www.blender.org/download/demo-files/\nCC BY-SA; version unspecified in inspected official/embedded evidence.\nModified long hair: guide cuts, fringe reshaping, node styling, scalp transfer, red material.\nLocal unapproved study; attribution and ShareAlike apply to adapted hair.\n')
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles_curves.shape='THICK';scene.cycles.samples=192;scene.cycles.use_denoising=False
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
report=dict(version=version,loose=LOOSE,part_by_root_side=PART,fringe_sweep=SWEEP,source_style='long hair main',hair_author='Daniel Bystedt',license='CC BY-SA; version unspecified in inspected evidence',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),method='authored guide cuts and fringe reshaping before native interpolation/clump/noise; whole-fiber radial scalp transfer',source_guides=len(guides),strands=len(sizes),points=len(rad),field_misses=misses,clearance_repairs=repairs,modifier_changes=changes,status='unreviewed actual 3D study')
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8');(out/'guide_cut_design.json').write_text(json.dumps(design,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('OFFICIAL_LAYER_CUT_SAVED',version,flush=True)
