"""Replace only an actual frontal native groom in a fresh static candidate.

Existing side/rear and short-support components retain their own licenses.
No author-source geometry is redistributed by this processing script.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version,source_version,front_version=args[:3]
DRAFT='--draft' in args
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in args[:3]):raise ValueError(args)
out,render=ROOT/'Exports'/version,ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh output required')
out.mkdir(parents=True);render.mkdir(parents=True)
source=ROOT/'Exports'/source_version/'Ember_Regent.blend'
front=ROOT/'Exports'/front_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
old=bpy.data.objects.get('Authored spatial fringe • actual scalp root patches')
if old is None or old.hide_render:raise RuntimeError('Expected visible canonical frontal groom')
old.hide_render=True;old.hide_viewport=True
name=old.name
with bpy.data.libraries.load(str(front),link=False) as (available,loaded):
    if name not in available.objects:raise RuntimeError('Frontal candidate missing')
    loaded.objects=[name]
col=bpy.data.collections.new('05_Frontal_Replacement_Study');bpy.context.scene.collection.children.link(col)
new=loaded.objects[0];col.objects.link(new);new.hide_render=False;new.hide_viewport=False
new.name='Authored frontal revision • native scalp-patch geometry'
if '--dry-groom' in args:
    for i,mat in enumerate(new.data.materials):
        if not mat or not mat.node_tree:continue
        mat=mat.copy();new.data.materials[i]=mat
        for node in mat.node_tree.nodes:
            if node.type=='BSDF_HAIR_PRINCIPLED':
                node.inputs['Roughness'].default_value=.42
                node.inputs['Radial Roughness'].default_value=.48
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=64 if DRAFT else 192;scene.cycles.use_denoising=False;scene.cycles_curves.shape='THICK'
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=80 if DRAFT else 100
report=dict(version=version,source=source_version,front_source=front_version,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),front_source_sha256=hashlib.sha256(front.read_bytes()).hexdigest(),processing_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),method='Only replace actual frontal native curves; preserve existing side/nape and short scalp support',frontal_curves=len(new.data.curves),draft=DRAFT,status='unreviewed actual static study',license='Project-authored frontal patches; retained side/nape Ddr Rcs Royalty Free and short support Bystedt CC BY-SA',collision_scope='No extra clothing/animation verification by replacement')
report['frontal_dry_roughness_matched']='--dry-groom' in args
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
    scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('FRONTAL_REPLACEMENT_RENDERED',version,flush=True)
