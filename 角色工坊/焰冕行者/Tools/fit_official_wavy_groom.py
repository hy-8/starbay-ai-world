"""Fit a softened official Hair Styles groom to the concert character.

Derived hairstyle: Daniel Bystedt, Hair Styles, CC BY-SA, version unspecified
in the inspected official listing and embedded license. Local WIP only.
Original source and all earlier candidates are preserved.
"""
import bpy,sys,json,re,math,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version=args[0]
LAYERED='--layered' in args
SHAPE='--shape' in args
if SHAPE:LAYERED=True
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh candidate required')
out.mkdir(parents=True);render.mkdir(parents=True)
source=ROOT/'Source/BlenderHairStyles/Bystedt_HairStyles.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
hair=bpy.data.objects['curly hair'];ng=hair.modifiers['Curly hair'].node_group
changes=[]
for node in ng.nodes:
 if node.type!='GROUP':continue
 name=node.node_tree.name
 values={}
 if name.startswith('Roll Hair Curves'):values={'Factor':.22,'Roll Length':.60,'Roll Radius':.18,'Roll Taper':.65}
 elif name.startswith('Curl Hair Curves'):values={'Factor':.32,'Radius':.060,'Frequency':.80}
 elif name.startswith('Hair Curves Noise'):values={'Distance':.035,'Scale along Curve':4.0}
 elif name.startswith('Set Hair Curve Profile'):values={'Radius':.00045}
 if LAYERED and name.startswith('Interpolate Hair Curves'):values={'Density':10000.0}
 for key,value in values.items():
  sock=node.inputs.get(key)
  if sock is None or sock.is_linked:raise RuntimeError('Cannot safely change '+name+'/'+key)
  changes.append({'node':name,'socket':key,'before':float(sock.default_value),'after':value});sock.default_value=value
hair.update_tag();bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
cu=hair.evaluated_get(dg).data
xyz=np.empty(len(cu.points)*3,np.float32);cu.attributes['position'].data.foreach_get('vector',xyz);xyz=xyz.reshape(-1,3).astype(np.float64)
sizes=np.array([len(c.points) for c in cu.curves],np.int32)
rad=np.empty(len(cu.points),np.float32);cu.attributes['radius'].data.foreach_get('value',rad)
m=np.array(hair.matrix_world);xyz=xyz@m[:3,:3].T+m[:3,3];xyz[:,0]-=10.;xyz*=.1
rad=np.maximum(rad*.1,.0000015)
head=bpy.data.objects['head'];sv=np.array([head.matrix_world@v.co for v in head.data.vertices],dtype=float)*.1
sb=BVHTree.FromPolygons([Vector(v) for v in sv],[list(p.vertices) for p in head.data.polygons])
cs=np.array([0,-.063,float(sv[:,2].max())-.100]);ct=np.array([0,-.044,1.771])
print('BAKED_OFFICIAL',len(sizes),len(xyz),'SOURCE_CENTER',cs,flush=True)
# Keep a compact, licensed and editable guide source separate from dense fibers.
guide_data=hair.data;guides=[]
for c in guide_data.curves:
 points=np.array([p.position for p in c.points],dtype=float)
 points=points@m[:3,:3].T+m[:3,3];points[:,0]-=10;points*=.1;guides.append(points)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports/hairrecongroom05/Ember_Regent.blend'))
body=bpy.data.objects['CC0 male body • retained topology'];bpy.context.view_layer.update()
if not np.allclose(np.array(body.matrix_world),np.eye(4)):raise RuntimeError('Unexpected target transform')
tb=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
T=129;A=257;field=np.zeros((T,A,2));misses=0
for i,theta in enumerate(np.linspace(.001,2.04,T)):
 for j,az in enumerate(np.linspace(-math.pi,math.pi,A)):
  direction=Vector((math.sin(theta)*math.sin(az),-math.sin(theta)*math.cos(az),math.cos(theta)))
  sh,_,_,sd=sb.ray_cast(Vector(cs),direction,.5);th,_,_,td=tb.ray_cast(Vector(ct),direction,.5)
  if sh is None or th is None:misses+=1;sd=.100;td=.103
  field[i,j]=[sd,td]
def transfer(points):
 v=points-cs;length=np.maximum(np.linalg.norm(v,axis=1),1e-8)
 theta=np.arccos(np.clip(v[:,2]/length,-1,1));az=np.arctan2(v[:,0],-v[:,1])
 u=np.clip((theta-.001)/2.039*(T-1),0,T-1);w=(az+math.pi)/(2*math.pi)*(A-1)
 i=np.floor(u).astype(int);j=np.floor(w).astype(int);ii=np.minimum(i+1,T-1);jj=np.minimum(j+1,A-1);fu=(u-i)[:,None];fw=(w-j)[:,None]
 f=field[i,j]*(1-fu)*(1-fw)+field[ii,j]*fu*(1-fw)+field[i,jj]*(1-fu)*fw+field[ii,jj]*fu*fw
 clearance=(length-f[:,0])*1.06
 if LAYERED:clearance=np.maximum(clearance,.0013)
 radial=ct+v/length[:,None]*(f[:,1]+clearance)[:,None]
 free=ct+v*1.06
 b=np.clip((points[:,2]-(cs[2]-.075))/.075,0,1);b=b*b*(3-2*b)
 return radial*b[:,None]+free*(1-b[:,None])
xyz=transfer(xyz);guides=[transfer(g) for g in guides]
styled_front=0;styled_nape=0
def layer_strand(strand):
 global styled_front,styled_nape
 root=strand[0].copy();t=np.linspace(0,1,len(strand));envelope=np.sin(np.pi*t)**1.2
 phase=((math.floor(root[0]/.009)+3*math.floor(root[1]/.012))%9)*.71
 # A small independent bend per root patch preserves coherent locks.
 strand[:,0]+=.0040*np.sin(t*7.5+phase)*envelope
 strand[:,1]+=.0035*np.sin(t*8.0+phase+.8)*envelope
 front=root[2]>1.806 and root[1]<-.068
 if SHAPE:front=front and -.067<root[0]<.065 and math.cos(phase)>.15
 if front:
  left=root[0]<.022
  end=np.array([root[0]-.040 if left else root[0]+.030,-.157+(abs(root[0])/.1)*.014,1.789-.025*(abs(root[0])/.1)])
  end[2]+=.012*np.sin(root[0]*137+root[1]*113)
  if SHAPE:
   end[0]=root[0]-.027 if left else root[0]+.020
   end[1]=-.171+abs(root[0])*.13
   end[2]-=.014
  shift=end-strand[-1];weight=np.maximum(0,(t-.28)/.72)**1.65
  strand+=shift[None,:]*weight[:,None]
  # Lift the bend away from the forehead before its free tip descends.
  strand[:,1]-=.012*envelope;strand[:,2]+=.006*envelope
  styled_front+=1
 elif root[1]>.004 or (abs(root[0])>.060 and root[2]<1.815):
  drop=.035+.032*(.5+.5*np.sin(root[0]*143+root[1]*91))
  free=np.maximum(0,(t-.45)/.55)**1.3
  strand[:,2]-=drop*free;strand[:,1]+=.012*free
  strand[:,0]+=.008*np.sin(t*8+phase)*free;styled_nape+=1
 else:
  normal=strand-ct;normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-8)
  strand+=normal*(.006*envelope)[:,None]
 return strand
if LAYERED:
 offset=0
 for size in sizes:
  size=int(size);xyz[offset:offset+size]=layer_strand(xyz[offset:offset+size]);offset+=size
 guides=[layer_strand(g) for g in guides]
 print('STYLED_FRONT_NAPE',styled_front,styled_nape,flush=True)
def sculpt_shell(points):
 p=points.copy();v=p-ct;length=np.maximum(np.linalg.norm(v,axis=1),1e-8)
 if '--mirror' in args:
  p[:,0]*=-1;v=p-ct
 theta=np.arccos(np.clip(v[:,2]/length,-1,1));az=np.arctan2(v[:,0],-v[:,1])
 u=np.clip((theta-.001)/2.039*(T-1),0,T-1);w=(az+math.pi)/(2*math.pi)*(A-1)
 i=np.floor(u).astype(int);j=np.floor(w).astype(int);ii=np.minimum(i+1,T-1);jj=np.minimum(j+1,A-1);fu=u-i;fw=w-j
 skin=field[i,j,1]*(1-fu)*(1-fw)+field[ii,j,1]*fu*(1-fw)+field[i,jj,1]*(1-fu)*fw+field[ii,jj,1]*fu*fw
 weight=np.clip((p[:,2]-1.776)/.050,0,1)
 # Leave lower free tips alone. Compress just the excess crown/temple shell.
 excess=np.maximum(0,length-skin-.0015);delta=excess*.32*weight
 p-=v/length[:,None]*delta[:,None]
 high=np.clip((p[:,2]-1.822)/.058,0,1)
 p[:,0]+=.020*np.exp(-(p[:,0]/.052)**2)*high
 # Lower the lighter side of the offset part to avoid paired equal peaks.
 p[:,2]-=.008*np.clip(p[:,0]/.06,0,1)*high
 return p
if SHAPE:
 xyz=sculpt_shell(xyz);guides=[sculpt_shell(g) for g in guides]
offset=0;root_corrections=[]
for size in sizes:
 size=int(size);p=Vector(xyz[offset]);hit,n,_,dist=tb.find_nearest(p)
 if hit is not None and dist<.03:
  correction=np.array(hit+n*.00045)-xyz[offset]
  xyz[offset:offset+size]+=correction[None,:]*(1-np.linspace(0,1,size))[:,None]**4
  root_corrections.append(float(np.linalg.norm(correction)))
 offset+=size
clearance_repairs=0;minimum_before=0.0
if '--resolve' in args:
 for i,p in enumerate(xyz):
  if p[2]<1.785:continue
  q=Vector(p);hit,n,_,dist=tb.find_nearest(q)
  gap=(q-hit).dot(n);minimum_before=min(minimum_before,gap)
  if gap<.0008 and dist<.040:
   xyz[i]=np.array(hit+n*.0011);clearance_repairs+=1
 print('SCALP_CLEARANCE_REPAIRS',clearance_repairs,minimum_before,flush=True)
if '--shaft' in args:
 offset=0
 for size in sizes:
  size=int(size);t=np.linspace(0,1,size)
  rad[offset:offset+size]=max(float(rad[offset]),.000035)*(1-.985*t**4)**.60
  offset+=size
col=bpy.data.collections['05_Hair']
for ob in list(col.objects):bpy.data.objects.remove(ob,do_unlink=True)
cu=bpy.data.hair_curves.new('Adapted Bystedt softened wavy hair');cu.add_curves(sizes.tolist());cu.attributes['position'].data.foreach_set('vector',xyz.astype(np.float32).ravel());cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',rad)
mat=bpy.data.materials.new('Deep cherry physical strands');mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear()
bs=nt.nodes.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='COLOR';bs.inputs['Roughness'].default_value=.38;bs.inputs['Radial Roughness'].default_value=.5
hi=nt.nodes.new('ShaderNodeHairInfo');r=nt.nodes.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(.008,.0010,.0014,1);r.color_ramp.elements[1].color=(.045,.0045,.0060,1)
nt.links.new(hi.outputs['Random'],r.inputs[0]);nt.links.new(r.outputs[0],bs.inputs['Color']);o=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(bs.outputs[0],o.inputs[0]);cu.materials.append(mat)
ob=bpy.data.objects.new('Daniel Bystedt adapted loose red waves • CC BY-SA',cu);col.objects.link(ob)
gc=bpy.data.collections.new('06_Licensed_Source_Guides');bpy.context.scene.collection.children.link(gc);gc.hide_render=True
gd=bpy.data.curves.new('Fitted authored source guides, pre modifier','CURVE');gd.dimensions='3D'
for g in guides:
 sp=gd.splines.new('POLY');sp.points.add(len(g)-1)
 for p,q in zip(sp.points,g):p.co=(*q,1)
go=bpy.data.objects.new('Authored guide control geometry • CC BY-SA',gd);gc.objects.link(go);go.hide_render=True
credits=bpy.data.texts.new('ADAPTED_HAIR_CREDITS');credits.write('Hair Styles by Daniel Bystedt\nOfficial source: https://www.blender.org/download/demo-files/\nCC BY-SA; version unspecified in the inspected source evidence.\nModifications: softer curl/roll/noise, scalp fitting, red strand material.\nLocal WIP; no public redistribution. Preserve attribution and ShareAlike for adapted hair.\n')
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles_curves.shape='THICK';scene.cycles.samples=192;scene.cycles.use_denoising=False
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
report={'version':version,'source_scene':'hairrecongroom05','layered':LAYERED,'sculpt_shell':SHAPE,'mirrored':'--mirror' in args,'shaft_taper':'--shaft' in args,'clearance_repairs':clearance_repairs,'minimum_gap_before_repairs_m':minimum_before,'hair_author':'Daniel Bystedt','hair_license':'CC BY-SA, version unspecified in inspected source','source_url':'https://download.blender.org/demo/geometry-nodes/hair_nodes-female_hair_styles.blend','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'modifier_changes':changes,'method':'body-only whole-fiber radial scalp transfer, tapered root correction','strands':len(sizes),'points':len(rad),'source_guides':len(guides),'field_misses':misses,'median_root_correction_m':float(np.median(root_corrections)),'styled_front':styled_front,'styled_nape':styled_nape,'status':'unreviewed local adaptation candidate; no redistribution'}
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('OFFICIAL_WAVY_GROOM_SAVED',version,flush=True)
