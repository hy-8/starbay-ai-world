"""Export installed Epic template reference for use in this UE project only.
Never modify template assets or redistribute as CC0/original artwork.
"""
import unreal,json,hashlib
from pathlib import Path
project=Path(unreal.Paths.project_dir()).resolve()
out=project.parent/'角色工坊/焰冕行者/Source/UE_Reference'
out.mkdir(parents=True,exist_ok=True)
assets={
 'Manny':'/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple',
 'Idle':'/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle',
 'Walk':'/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd',
 'Run':'/Game/Characters/Mannequins/Anims/Unarmed/Jog/MF_Unarmed_Jog_Fwd',
 'Jump':'/Game/Characters/Mannequins/Anims/Unarmed/Jump/MM_Jump',
 'Fall':'/Game/Characters/Mannequins/Anims/Unarmed/Jump/MM_Fall_Loop',
 'Land':'/Game/Characters/Mannequins/Anims/Unarmed/Jump/MM_Land',
}
report=[]
for name,path in assets.items():
    obj=unreal.load_asset(path)
    if obj is None:raise RuntimeError('Missing installed template '+path)
    dest=out/(name+'.fbx')
    if dest.exists():raise RuntimeError('Protected export '+str(dest))
    task=unreal.AssetExportTask();task.object=obj;task.filename=str(dest);task.automated=True;task.prompt=False;task.replace_identical=False
    opt=unreal.FbxExportOption();opt.set_editor_property('ascii',False);opt.set_editor_property('level_of_detail',False);opt.set_editor_property('collision',False);opt.set_editor_property('export_preview_mesh',False)
    task.options=opt
    if not unreal.Exporter.run_asset_export_task(task):raise RuntimeError('Failed to export '+name)
    report.append({'name':name,'asset':path,'file':dest.name,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
(out/'sources.json').write_text(json.dumps({'license':'Epic Unreal Engine template content; use subject to Epic license, not CC0','assets':report},indent=2),encoding='utf-8')
unreal.log('REFERENCE_EXPORT_COMPLETE')
