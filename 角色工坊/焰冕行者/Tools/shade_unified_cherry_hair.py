"""Unify native groom pigment while keeping exact geometry and scene lights."""
import bpy,sys,re,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=ROOT/'Exports'/version;rd=ROOT/'Renders'/version;assert not out.exists() and not rd.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
primary=bpy.data.objects['Bystedt layercut derivative • native root reflow'];mat=primary.data.materials[0].copy();mat.name='Deep cherry • coherent native groom pigment'
nt=mat.node_tree;bs=next(n for n in nt.nodes if n.bl_idname=='ShaderNodeBsdfHairPrincipled');assert bs.model=='HUANG'
ramp=nt.nodes['Color Ramp'];assert len(ramp.color_ramp.elements)==2
ramp.color_ramp.elements[0].color=(.035,.002,.003,1);ramp.color_ramp.elements[1].color=(.110,.006,.009,1)
bs.inputs['Roughness'].default_value=.30;bs.inputs['Random Roughness'].default_value=.16
changed=[]
for ob in bpy.data.objects:
    if ob.type=='CURVES' and not ob.hide_render:
        ob.data=ob.data.copy();ob.data.materials.clear();ob.data.materials.append(mat);changed.append(ob.name)
assert len(changed)==4
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
out.mkdir(parents=True);rd.mkdir(parents=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'),compress=True)
(out/'unified_cherry_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,changed_objects=changed,geometry_edit=False,method='Copy current primary Huang material with its root gradient. Strand color range(.035,.002,.003)-(.110,.006,.009),roughness.30,random roughness.16. Assign to all four visible native hair components. Other scattering settings retained. No geometry,mesh material or lighting edits.'),indent=2),encoding='utf-8')
for shot in ['02_ThreeQuarter','03_Side','04_Back']:
    s.camera=bpy.data.objects[shot];s.render.filepath=str(rd/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
print('UNIFIED_CHERRY_RENDERED',version,flush=True)
