"""Blender asset preview only; not an Unreal gameplay screenshot."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
GAME=ROOT.parent/'星湾街区_3D探索'
OUT=ROOT/'Preview';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(GAME/'星湾街区_第六版场景.blend'))
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    if any(d.type=='OPTIX' for d in prefs.devices):scene.cycles.device='GPU'
except Exception:pass
bpy.ops.object.camera_add(location=(54,-34,4.0))
cam=bpy.context.object;cam.name='UE_migration_asset_review'
cam.rotation_euler=(Vector((68,-46,2.1))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.lens=25;scene.camera=cam
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(OUT/'茶庭_Blender资产预览.png')
bpy.ops.render.render(write_still=True)
(OUT/'preview_source.json').write_text(json.dumps({'renderer':'Blender Cycles','samples':32,'notUnrealScreenshot':True,'cameraBlenderMeters':[54,-34,4],'source':'星湾街区_第六版场景.blend'},ensure_ascii=False,indent=2),encoding='utf-8')
