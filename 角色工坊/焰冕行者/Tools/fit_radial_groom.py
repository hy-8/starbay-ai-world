"""Transfer donor fibers through a body-only, smoothly sampled scalp field.

Preserves each point's exterior clearance instead of extrapolating one tiny
root triangle along an entire strand. CC0 donor; fresh Blender candidates.
"""
import bpy, sys, json, re, math, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version,style=args[:2]
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
if style not in ['basic_short_hair','straight_hair_to_shoulder']:raise ValueError(style)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh output required')
out.mkdir(parents=True);render.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Source/HairEditorCC0/hair/haireditor/hair.blend'))
surface=bpy.data.objects[style].data.surface
sv=np.array([surface.matrix_world@v.co for v in surface.data.vertices],dtype=float)
gi=surface.vertex_groups['body'].index
body_ids=set(v.index for v in surface.data.vertices if any(g.group==gi and g.weight>.5 for g in v.groups))
polys=[list(p.vertices) for p in surface.data.polygons if all(i in body_ids for i in p.vertices)]
sb=BVHTree.FromPolygons([Vector(v) for v in sv],polys)
filename=('native_'+style+'_evaluated.npz') if '--native' in args else ('baked2_'+style+'.npz')
pack=ROOT/'Source/HairEditorCC0'/filename;data=np.load(pack)
xyz=data['positions'].astype(float);sizes=data['sizes'];radii=data['radii'].astype(float)*.85
m=data['matrix'];xyz=xyz@m[:3,:3].T+m[:3,3]
cs=np.array([0,-.063,1.565]);ct=np.array([0,-.044,1.771])
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports/hairrecongroom05/Ember_Regent.blend'))
body=bpy.data.objects['CC0 male body • retained topology'];bpy.context.view_layer.update()
if not np.allclose(np.array(body.matrix_world),np.eye(4)):raise RuntimeError('Target must be in world coordinates')
tb=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
T=129;A=257;field=np.zeros((T,A,2));misses=0
for i,theta in enumerate(np.linspace(.001,1.99,T)):
 for j,az in enumerate(np.linspace(-math.pi,math.pi,A)):
  d=Vector((math.sin(theta)*math.sin(az),-math.sin(theta)*math.cos(az),math.cos(theta)))
  sh,_,_,sd=sb.ray_cast(Vector(cs),d,.5);th,_,_,td=tb.ray_cast(Vector(ct),d,.5)
  if sh is None or th is None:misses+=1;sd=.10;td=.103
  field[i,j]=[sd,td]
print('SCALP_FIELD',len(body_ids),len(polys),misses,flush=True)
v=xyz-cs;length=np.linalg.norm(v,axis=1);theta=np.arccos(np.clip(v[:,2]/length,-1,1));az=np.arctan2(v[:,0],-v[:,1])
u=np.clip((theta-.001)/1.989*(T-1),0,T-1);w=(az+math.pi)/(2*math.pi)*(A-1)
i=np.floor(u).astype(int);j=np.floor(w).astype(int);ii=np.minimum(i+1,T-1);jj=np.minimum(j+1,A-1)
fu=(u-i)[:,None];fw=(w-j)[:,None]
f=field[i,j]*(1-fu)*(1-fw)+field[ii,j]*fu*(1-fw)+field[i,jj]*(1-fu)*fw+field[ii,jj]*fu*fw
clearance=length-f[:,0]
newlength=f[:,1]+clearance*1.02
radial=ct+v/length[:,None]*newlength[:,None]
rigid=ct+v*1.02
# Lower free ends do not follow a torso/neck ray. Smoothly extend the upper
# skull displacement; retain the donor's hanging length and character.
blend=np.clip((xyz[:,2]-1.48)/.065,0,1);blend=blend*blend*(3-2*blend)
mapped=radial*blend[:,None]+rigid*(1-blend[:,None])
offset=0;corrections=[]
for size in sizes:
 size=int(size);root=Vector(mapped[offset]);p,n,_,dist=tb.find_nearest(root)
 if p is not None and dist<.026:
  correction=np.array(p+n*.0005)-mapped[offset]
  weight=(1-np.linspace(0,1,size))**3
  mapped[offset:offset+size]+=correction[None,:]*weight[:,None]
  corrections.append(float(np.linalg.norm(correction)))
 offset+=size
if '--source' in args:
 mapped=ct+(xyz-cs)*1.02
 for o in list(bpy.data.collections['01_Body'].objects):o.hide_render=True
 mesh=bpy.data.meshes.new('Donor body only, no helpers');mesh.from_pydata((ct+(sv-cs)*1.02).tolist(),[],polys);mesh.update()
 ob=bpy.data.objects.new('CC0 donor shape control',mesh);bpy.data.collections['01_Body'].objects.link(ob)
 mat=bpy.data.materials.new('Neutral donor skin');mat.diffuse_color=(.38,.27,.20,1);mesh.materials.append(mat)
 for p in mesh.polygons:p.use_smooth=True
for ob in list(bpy.data.collections['05_Hair'].objects):bpy.data.objects.remove(ob,do_unlink=True)
cu=bpy.data.hair_curves.new('Scalp field transferred CC0 groom');cu.add_curves(sizes.tolist())
cu.attributes['position'].data.foreach_set('vector',mapped.astype(np.float32).ravel());cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',radii.astype(np.float32))
mat=bpy.data.materials.new('Dark cherry physical hair');mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear()
bs=nt.nodes.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='COLOR';bs.inputs['Roughness'].default_value=.38;bs.inputs['Radial Roughness'].default_value=.5
hi=nt.nodes.new('ShaderNodeHairInfo');r=nt.nodes.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(.009,.0016,.0020,1);r.color_ramp.elements[1].color=(.055,.008,.008,1)
nt.links.new(hi.outputs['Random'],r.inputs[0]);nt.links.new(r.outputs[0],bs.inputs['Color']);o=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(bs.outputs[0],o.inputs[0]);cu.materials.append(mat)
ob=bpy.data.objects.new('Radial authored '+style,cu);bpy.data.collections['05_Hair'].objects.link(ob)
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles_curves.shape='THICK';scene.cycles.samples=96;scene.cycles.use_denoising=True
scene.render.resolution_x=1000;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
cam=scene.camera;cam.data.type='ORTHO';cam.data.ortho_scale=.53
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
report={'version':version,'base':'hairrecongroom05','source_control':'--source' in args,'style':style,'method':'body-only spherical scalp field, whole-fiber exterior clearance and tapered root attachment','source_body_vertices':len(body_ids),'source_body_polygons':len(polys),'field_misses':misses,'strands':len(sizes),'median_root_correction_m':float(np.median(corrections)),'source_hash':hashlib.sha256(pack.read_bytes()).hexdigest(),'source_author':'Tomas Klecer','license':'CC0','status':'unreviewed candidate'}
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
for name,loc in [('01_Front',(0,-4,1.76)),('03_Side',(4,-.025,1.76)),('04_Back',(0,4,1.76))]:
 cam.location=loc;cam.rotation_euler=(Vector((0,-.025,1.744))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('RADIAL_GROOM_SAVED',version,flush=True)
