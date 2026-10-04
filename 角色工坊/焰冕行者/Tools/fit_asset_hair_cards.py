"""Fresh actual-geometry fitting study of Ddr Rcs's licensed hair-card asset.

Royalty Free from BlenderKit, not CC0. Keep source/derivative locally; do not
redistribute as a hair asset pack. This control fit is not artistic approval.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version,base_version=args[:2];DRAFT='--draft' in args
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in (version,base_version)):raise ValueError(args)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh directories only')
out.mkdir(parents=True);render.mkdir(parents=True)
base=ROOT/'Exports'/base_version/'Ember_Regent.blend'
asset=ROOT/'Source/BlenderKitResearch/DdrRcs_ShaggyMullet.blend'
asset_hash=hashlib.sha256(asset.read_bytes()).hexdigest()
if asset_hash!='59f67664be3a88217b14c273d941963ec2e02ca3ad93258e7e93fb0656019ba7':raise RuntimeError('Inspect changed source before reuse')
bpy.ops.wm.open_mainfile(filepath=str(base),use_scripts=False)
for ob in bpy.data.collections['05_Hair'].objects:ob.hide_render=True;ob.hide_viewport=True
with bpy.data.libraries.load(str(asset),link=False) as (available,loaded):
 loaded.objects=['Female_Shaggy_Mullet_Haircut']
hair=loaded.objects[0]
collection=bpy.data.collections.new('05_Licensed_Hair_Card_Study');bpy.context.scene.collection.children.link(collection);collection.objects.link(hair)
hair.parent=None;hair.matrix_world.identity();hair.name='Ddr Rcs hair-card derivative • actual fitted geometry'
mesh=hair.data;xyz=np.array([v.co[:] for v in mesh.vertices],float)
factor=np.array([v.color[0] for v in mesh.attributes['Factor'].data])
# Independent card strips are identified by actual mesh connectivity.
parent=np.arange(len(xyz))
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for edge in mesh.edges:
 a,b=map(int,edge.vertices);a=find(a);b=find(b)
 if a!=b:parent[b]=a
groups={}
for i in range(len(xyz)):groups.setdefault(find(i),[]).append(i)
source_center=np.array([.034,-.0096,.270]);target_center=np.array([0,-.044,1.771]);scale=1.15
fitted=target_center+(xyz-source_center)*scale
body=bpy.data.objects['CC0 male body • retained topology'];bpy.context.view_layer.update()
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
adjustments=[]
for ids in groups.values():
 ids=np.asarray(ids);u=factor[ids];root_ids=ids[u<=u.min()+.006]
 root=fitted[root_ids].mean(axis=0);direction=root-target_center;direction/=np.linalg.norm(direction)
 hit,n,face,dist=bv.ray_cast(Vector(target_center),Vector(direction),.25)
 if hit is None:hit,n,face,dist=bv.find_nearest(Vector(root))
 desired=np.array(hit+n*.001);delta=desired-root
 fitted[ids]+=delta[None,:]*np.maximum(0,1-u[:,None])**.8
 adjustments.append(float(np.linalg.norm(delta)))
repairs=0
for i,p in enumerate(fitted):
 hit,n,face,dist=bv.find_nearest(Vector(p));gap=(Vector(p)-hit).dot(n)
 if gap<.0007 and dist<.035:fitted[i]=np.array(hit+n*.0010);repairs+=1
mesh.vertices.foreach_set('co',fitted.astype(np.float32).ravel());mesh.update()
for mat in mesh.materials:
 for node in mat.node_tree.nodes:
  if node.type=='GROUP' and node.node_tree.name.startswith('HairShaderMain'):
   for name,value in [('Base Color',(.065,.0027,.005,1)),('Root Color',(.018,.0008,.0015,1)),('Root Color Mix Factor',.45),('Root Color Range',.28),('Tip Color',(.11,.005,.007,1)),('Tip Color Mix Factor',.18),('Tip Color Range',.75),('SpecRoughness',.18),('MetalicRoughness',.4)]:
    socket=node.inputs.get(name)
    if socket and not socket.is_linked:socket.default_value=value
credits=bpy.data.texts.new('DDR_RCS_HAIR_CREDITS')
credits.write('Female Shaggy Mullet Haircut by Ddr Rcs, BlenderKit asset 7e71d351-a00e-4188-82ef-54d0ade05423. Royalty Free, not CC0. Source SHA256 '+asset_hash+'. Modified: actual-body fitting, per-card scalp-root adjustment, surface clearance, crimson shading. Do not resell/redistribute as a standalone 3D hair asset or asset pack. Original donor is kept locally. This is a WIP control fit.\n')
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for device in pref.devices:device.use=device.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=64 if DRAFT else 192;scene.cycles.use_denoising=False;scene.cycles.transparent_max_bounces=24
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=80 if DRAFT else 100
report=dict(version=version,base=base_version,base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),asset_author='Ddr Rcs',asset_name='Female Shaggy Mullet Haircut',asset_base_id='7e71d351-a00e-4188-82ef-54d0ade05423',asset_sha256=asset_hash,license='BlenderKit Royalty Free, not CC0; no standalone asset resale',source_origin='https://www.blenderkit.com/',license_source='https://www.blenderkit.com/docs/licenses/',visible_hair='actual textured mesh cards, not native fibers or an image replacement',card_components=len(groups),vertices=len(xyz),root_adjustment_median_m=float(np.median(adjustments)),root_adjustment_max_m=float(np.max(adjustments)),clearance_repairs=repairs,source_center_m=source_center.tolist(),target_center_m=target_center.tolist(),scale=scale,draft=DRAFT,artistic_status='unreviewed control fitting, not final',images=[])
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
 path=render/(name+'.png');report['images'].append(dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
(out/'asset_fit_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('ASSET_HAIR_CONTROL_RENDERED',version,len(groups),flush=True)
