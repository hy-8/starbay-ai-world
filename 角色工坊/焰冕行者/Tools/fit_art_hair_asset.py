"""Fit and physically relight an explicitly CC-BY authored hair-card asset.

Fresh offline candidate, author/source attribution stored with every output.
"""
import bpy,sys,re,math,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];VERSION,STYLE=args[:2];DRAFT='--draft' in args
if not re.fullmatch('[A-Za-z0-9_-]+',VERSION):raise ValueError(VERSION)
if STYLE not in ['elvs_maxwell_hair','elvs_grump_hair','elvs_inverted_curly_bob','elvs_wavy_bob']:raise ValueError(STYLE)
OUT=ROOT/'Exports'/VERSION;RENDER=ROOT/'Renders'/VERSION
if OUT.exists() or RENDER.exists():raise RuntimeError('Fresh output required')
OUT.mkdir(parents=True);RENDER.mkdir(parents=True)
folder=ROOT/'Source/HairStylesCCBY/hair'/STYLE;clo=folder/(STYLE+'.mhclo');lines=clo.read_text().splitlines()
license_header=[l for l in lines if l.lower().startswith('# license')]
if not license_header or not any('cc_by' in l.lower() or 'cc-by' in l.lower() for l in license_header):raise RuntimeError('Explicit CC-BY license required')
settings={};mapping=[];scales=[1,1,1];active=False
src=[]
for line in (ROOT/'Source/base.obj').read_text().splitlines():
 q=line.split()
 if q and q[0]=='v':src.append(Vector(tuple(map(float,q[1:4]))))
for line in (ROOT/'Source/male_young.target').read_text().splitlines():
 q=line.split()
 if len(q)==4 and q[0].isdigit():src[int(q[0])]+=Vector(tuple(map(float,q[1:4])))
for record in json.loads((ROOT/'Source/couture_sources.json').read_text(encoding='utf-8')):
 for line in (ROOT/'Source'/record['file']).read_text().splitlines():
  q=line.split()
  if len(q)==4 and q[0].isdigit():src[int(q[0])]+=Vector(tuple(map(float,q[1:4])))*record['weight']
for line in lines:
 q=line.split()
 if not q or q[0].startswith('#'):continue
 if q[0] in ['obj_file','material']:settings[q[0]]=q[1]
 if q[0] in ['x_scale','y_scale','z_scale']:
  ax='xyz'.index(q[0][0]);scales[ax]=abs(src[int(q[1])][ax]-src[int(q[2])][ax])/float(q[3])
 if q[0]=='verts':active=True;continue
 if active:
  if not q[0].lstrip('-').isdigit():active=False;continue
  if len(q)==9:
   p=sum((src[int(q[j])]*float(q[j+3]) for j in range(3)),Vector())+Vector(tuple(float(q[j+6])*scales[j] for j in range(3)))
  elif len(q)==1:p=src[int(q[0])].copy()
  else:active=False;continue
  mapping.append(Vector((p.x*.115,-p.z*.115,(p.y+8.188)*.115)))
uvs=[];faces=[];uvfaces=[];count=0
obj=folder/settings['obj_file']
for line in obj.read_text().splitlines():
 q=line.split()
 if not q:continue
 if q[0]=='v':count+=1
 elif q[0]=='vt':uvs.append(tuple(map(float,q[1:3])))
 elif q[0]=='f':faces.append([int(v.split('/')[0])-1 for v in q[1:]]);uvfaces.append([int(v.split('/')[1])-1 for v in q[1:]])
if count!=len(mapping):raise RuntimeError('Proxy vertex count differs')
texture=None
for line in (folder/settings['material']).read_text().splitlines():
 q=line.split()
 if q and q[0]=='diffuseTexture':texture=folder/q[1]
if not texture or not texture.exists():raise RuntimeError('Source hair texture absent')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports/atelier09/Ember_Regent.blend'))
col=bpy.data.collections['05_Hair']
for ob in list(col.objects):bpy.data.objects.remove(ob,do_unlink=True)
body=max((o for o in bpy.data.collections['01_Body'].objects if o.type=='MESH' and not o.hide_render and 'high-poly' not in o.name),key=lambda o:len(o.data.vertices))
bpy.context.view_layer.update();bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
corrected=0
for v in mapping:
 hit,n,_,_=bv.find_nearest(v)
 if hit is not None and (hit-v).length<.014 and (v-hit).dot(n)<.001:
  v[:]=hit+n*.001;corrected+=1
me=bpy.data.meshes.new('Authored hair card UV');me.from_pydata(mapping,[],faces);me.update();ob=bpy.data.objects.new('Fitted '+STYLE+' - Elvaerwyn CC-BY',me);col.objects.link(ob)
uv=me.uv_layers.new(name='OriginalHairUV')
for p,uf in zip(me.polygons,uvfaces):
 p.use_smooth=True
 for li,ti in zip(p.loop_indices,uf):uv.data[li].uv=uvs[ti]
sub=ob.modifiers.new('Smooth fitted hair silhouette','SUBSURF');sub.levels=2;sub.render_levels=2
mat=bpy.data.materials.new('Authored deep auburn alpha hair');mat.use_nodes=True;nt=mat.node_tree;p=nt.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.42;p.inputs['Specular IOR Level'].default_value=.28;p.inputs['Anisotropic'].default_value=.45
im=bpy.data.images.load(str(texture));im.pack();tx=nt.nodes.new('ShaderNodeTexImage');tx.image=im;bw=nt.nodes.new('ShaderNodeRGBToBW');nt.links.new(tx.outputs['Color'],bw.inputs[0]);r=nt.nodes.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(.010,.0015,.002,1);r.color_ramp.elements[1].color=(.20,.023,.025,1);nt.links.new(bw.outputs[0],r.inputs[0]);nt.links.new(r.outputs[0],p.inputs['Base Color']);nt.links.new(tx.outputs['Alpha'],p.inputs['Alpha'])
bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.0003;nt.links.new(bw.outputs[0],bump.inputs['Height']);nt.links.new(bump.outputs[0],p.inputs['Normal']);me.materials.append(mat)
stage=bpy.data.collections['90_Stage'];scene=bpy.context.scene
for ob in list(stage.objects):
 if ob.type in ['LIGHT','CAMERA']:bpy.data.objects.remove(ob,do_unlink=True)
def area(name,loc,power,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=size;o=bpy.data.objects.new(name,d);stage.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,-.025,1.74))-o.location).to_track_quat('-Z','Y').to_euler()
area('Neutral key',(-1.5,-2,2.7),115,1.5);area('Neutral fill',(1.5,-1.5,1.9),48,1.5);area('Neutral rim',(1,1.7,2.5),90,1.2)
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.055,.055,.055,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.3
scene.render.engine='CYCLES';scene.cycles.samples=48 if DRAFT else 128;scene.cycles.use_denoising=True;scene.cycles.transparent_max_bounces=24
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-.25;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=70 if DRAFT else 100
for name,loc in [('01_Front',(0,-4,1.76)),('02_ThreeQuarter',(.95,-3,1.79)),('03_Side',(4,-.025,1.76)),('04_Back',(0,4,1.76))]:
 d=bpy.data.cameras.new(name);cam=bpy.data.objects.new(name,d);stage.objects.link(cam);cam.location=loc;cam.rotation_euler=(Vector((0,-.025,1.745))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=.55;scene.camera=cam;scene.render.filepath=str(RENDER/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Ember_Regent.blend'))
report={'version':VERSION,'source':'atelier09','asset':STYLE,'author':'Elvaerwyn','license':'CC-BY, as declared in asset file; version unspecified','license_header':license_header,'source_page':'https://static.makehumancommunity.org/assets/assetpacks/hair02.html','asset_page':'http://www.makehumancommunity.org/node/1639' if STYLE=='elvs_maxwell_hair' else None,'changes':'MakeHuman barycentric fitting with facial morphs, scalp clearance, subdivision and original UV hair texture recolored to auburn in physical Blender shader','mesh_sha256':hashlib.sha256(obj.read_bytes()).hexdigest(),'texture_sha256':hashlib.sha256(texture.read_bytes()).hexdigest(),'scalp_clearance_vertices':corrected,'status':'comparison candidate; requires visual inspection'}
(OUT/'groom_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('AUTHORED_HAIR_ASSET_SAVED',VERSION,flush=True)
