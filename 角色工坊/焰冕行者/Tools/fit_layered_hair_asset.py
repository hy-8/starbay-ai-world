"""Fit inspected Salman Ramezani layered cards into a fresh real model.

BlenderKit Royalty Free. Original/derived asset geometry kept local; processing
code, source metadata and reviewed rendered evidence may be tracked.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version,base_version=args[:2]
DRAFT='--draft' in args
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in args[:2]):raise ValueError(args)
out,render=ROOT/'Exports'/version,ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh directories only')
out.mkdir(parents=True);render.mkdir(parents=True)
base=ROOT/'Exports'/base_version/'Ember_Regent.blend'
asset=ROOT/'Source/BlenderKitResearch/Salman_ShortHairCard.blend'
source_hash=hashlib.sha256(asset.read_bytes()).hexdigest()
if source_hash!='ead836aeaae3fd349da52b16c42e5cf9f3de3d41cf67f53db0b458a13198e6d1':raise RuntimeError('Changed source requires new inspection')
bpy.ops.wm.open_mainfile(filepath=str(base),use_scripts=False)
for ob in bpy.data.objects:
    if ob.type=='CURVES':ob.hide_render=True;ob.hide_viewport=True
    if ob.name.startswith('Ddr Rcs hair-card'):ob.hide_render=True;ob.hide_viewport=True
with bpy.data.libraries.load(str(asset),link=False) as (available,loaded):
    loaded.objects=['Caps','Short hair card.001','Short hair card']
col=bpy.data.collections.new('05_Salman_Layered_Card_Fit');bpy.context.scene.collection.children.link(col)
for ob in loaded.objects:col.objects.link(ob)
bpy.context.view_layer.update()
body=bpy.data.objects['CC0 male body • retained topology'];bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
print('BODY_BOUNDS', [list(body.matrix_world@Vector(v)) for v in body.bound_box],flush=True)
source_center=np.array([0.,-.012,.210]);target=np.array([0.,-.044,1.771]);scale=.45
if '--center-z' in args:source_center[2]=float(args[args.index('--center-z')+1])
repairs=0;objects=[];materials=set()
for ob in loaded.objects:
    if ob.type!='MESH':continue
    matrix=ob.matrix_world.copy();xyz=np.array([matrix@v.co for v in ob.data.vertices],float)
    ob.parent=None;ob.matrix_world=Matrix.Identity(4)
    print('SOURCE_BAKED_BOUNDS',ob.name,xyz.min(axis=0).tolist(),xyz.max(axis=0).tolist(),flush=True)
    fitted=target+(xyz-source_center)*scale
    if '--wolf-extension' in args:
        # Smooth spatial extension of existing authored geometry, UVs unchanged.
        lower=np.clip((.245-xyz[:,2])/.23,0,1)**1.4
        rear=np.clip((xyz[:,1]+.13)/.22,0,1)
        fitted[:,2]-=lower*(.035+.090*rear)
        fitted[:,1]+=lower*.012*rear
        fitted[:,0]*=1-.12*lower*rear
    for i,p in enumerate(fitted):
        hit,n,face,dist=bv.find_nearest(Vector(p));gap=(Vector(p)-hit).dot(n)
        if gap<.001 and dist<.05:
            fitted[i]=np.array(hit+n*.0015);repairs+=1
    ob.data.vertices.foreach_set('co',fitted.astype(np.float32).ravel());ob.data.update()
    # Preserve the author's actual texture/opacity/shading graph; only add
    # an explicit multiplier to its final base color for this red variant.
    for mat in ob.data.materials:
        if not mat or mat.name in materials or not mat.node_tree:continue
        materials.add(mat.name);nt=mat.node_tree
        bs=next((n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'),None)
        if not bs:continue
        tint=nt.nodes.new('ShaderNodeMixRGB');tint.name='Project crimson tint';tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1.;tint.inputs[2].default_value=(.52,.055,.070,1)
        if bs.inputs['Base Color'].is_linked:
            old_link=bs.inputs['Base Color'].links[0];socket=old_link.from_socket;nt.links.remove(old_link);nt.links.new(socket,tint.inputs[1])
        else:tint.inputs[1].default_value=bs.inputs['Base Color'].default_value
        nt.links.new(tint.outputs[0],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.42
        if '--crimson-remap' in args:
            # Black source albedo cannot be recolored by multiplication alone.
            # Preserve its strand-value variation and map it to dyed crimson.
            ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.name='Crimson albedo value remap'
            ramp.color_ramp.elements[0].color=(.035,.0018,.004,1)
            ramp.color_ramp.elements[1].position=.35
            ramp.color_ramp.elements[1].color=(.30,.018,.035,1)
            if tint.inputs[1].is_linked:nt.links.new(tint.inputs[1].links[0].from_socket,ramp.inputs[0])
            else:ramp.inputs[0].default_value=.18
            nt.links.new(ramp.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.54
            for socket in ('Roughness','Specular IOR Level','Specular Tint'):
                for link in list(bs.inputs[socket].links):nt.links.remove(link)
            if bs.inputs.get('Weight'):bs.inputs['Weight'].default_value=1
            bs.inputs['Subsurface Weight'].default_value=0
            bs.inputs['Coat Weight'].default_value=0
            bs.inputs['Specular IOR Level'].default_value=.30
            bs.inputs['Specular Tint'].default_value=(.7,.18,.22,1)
    old_name=ob.name;ob.name='Salman layered hair derivative • '+old_name
    objects.append(dict(name=ob.name,vertices=len(ob.data.vertices),min=fitted.min(axis=0).tolist(),max=fitted.max(axis=0).tolist()))
empty=next(o for o in loaded.objects if o.type=='EMPTY');empty.hide_render=True;empty.hide_viewport=True
tx=bpy.data.texts.new('SALMAN_HAIR_CREDITS')
tx.write('Short hair card by Salman Ramezani, BlenderKit asset 4793aff4-5e46-4902-a329-314731ebde09, Royalty Free, not CC0. Original packed textures and subdivision retained. Modified world transform, real body clearance and crimson material tint. Keep original and modified geometry locally; do not distribute as a standalone hair asset pack. Unapproved static fitting control.\n')
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=64 if DRAFT else 192;scene.cycles.use_denoising=False;scene.cycles.transparent_max_bounces=24
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=80 if DRAFT else 100
report=dict(version=version,base=base_version,base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),asset='Short hair card',author='Salman Ramezani',asset_sha256=source_hash,license='BlenderKit Royalty Free, not CC0; geometric source and derivatives local',source_center_m=source_center.tolist(),target_center_m=target.tolist(),scale=scale,body_clearance_repairs=repairs,objects=objects,draft=DRAFT,status='unreviewed actual fitted asset control',processing_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
report['crimson_value_remap']='--crimson-remap' in args
report['smooth_existing_card_nape_extension']='--wolf-extension' in args
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
    scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('SALMAN_FIT_RENDERED',version,repairs,flush=True)
