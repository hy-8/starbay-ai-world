"""Test deeper original posterior undercoat pigment without changing groom geometry."""
import bpy,sys,re,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2];preview='--preview-only' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=ROOT/'Exports'/version;rd=ROOT/'Renders'/version;assert not out.exists() and not rd.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Original posterior coverage • surface-grown short fibers'];mat=ob.data.materials[0].copy();mat.name='Deep cherry • darker posterior root foundation'
nt=mat.node_tree;bs=next(n for n in nt.nodes if n.bl_idname=='ShaderNodeBsdfHairPrincipled');assert bs.model=='HUANG'
ramp=nt.nodes['Color Ramp'];assert len(ramp.color_ramp.elements)==2
before=[list(e.color) for e in ramp.color_ramp.elements]
for e in ramp.color_ramp.elements:
 rgb=list(e.color);e.color=tuple(x*.55 for x in rgb[:3])+(rgb[3],)
ob.data=ob.data.copy();ob.data.materials.clear();ob.data.materials.append(mat)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
out.mkdir(parents=True);rd.mkdir(parents=True)
if not preview:bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'),compress=True)
(out/'posterior_pigment_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,changed_object=ob.name,geometry_edit=False,preview_only=preview,before_random_colors=before,after_random_colors=[list(e.color) for e in ramp.color_ramp.elements],method='Only original posterior undercoat material copied;random strand RGB multiplied0.55. Existing root gradient,roughness,scattering and all other materials/lighting/geometry retained. Simulates darker inner hair under dyed outer layers;not a geometry fix.'),indent=2),encoding='utf-8')
for shot in ['04_Back','03_Side','02_ThreeQuarter']:
 s.camera=bpy.data.objects[shot];s.render.filepath=str(rd/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
print('POSTERIOR_PIGMENT_RENDERED',version,flush=True)
