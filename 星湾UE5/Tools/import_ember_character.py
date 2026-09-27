"""Import a new skinned character namespace, leaving template assets/maps unchanged."""
import unreal,json,traceback
from pathlib import Path
P=Path(unreal.Paths.project_dir()).resolve();C=P.parent/'角色工坊/焰冕行者'
DEST='/Game/Starbay/Ember_v04';REPORT=P/'Saved/ember_import_v04.json'
E=unreal.EditorAssetLibrary;A=unreal.AssetToolsHelpers.get_asset_tools()
report={'status':'started','destination':DEST,'assets':[]}
if E.does_directory_exist(DEST):raise RuntimeError('Existing character namespace is protected; use new version')
def save_report():REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8')
def run_import(file,name,options):
    task=unreal.AssetImportTask();task.filename=str(file);task.destination_path=DEST;task.destination_name=name;task.automated=True;task.replace_existing=False;task.save=True;task.options=options
    task.factory=unreal.FbxFactory()
    A.import_asset_tasks([task]);paths=list(task.imported_object_paths);report['assets']+=paths;save_report()
    if not paths:raise RuntimeError('Import produced no assets: '+name)
    return [unreal.load_asset(x) for x in paths]
try:
    options=unreal.FbxImportUI();options.automated_import_should_detect_type=False;options.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH
    options.import_mesh=True;options.import_as_skeletal=True;options.import_animations=False;options.import_materials=False;options.import_textures=False;options.create_physics_asset=False
    options.skeletal_mesh_import_data.import_uniform_scale=1
    options.skeletal_mesh_import_data.set_editor_property('import_morph_targets',False)
    options.skeletal_mesh_import_data.set_editor_property('normal_import_method',unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)
    imported=run_import(C/'Exports/rig04/SK_EmberRegent.fbx','SK_EmberRegent',options)
    mesh=next(x for x in imported if isinstance(x,unreal.SkeletalMesh));skeleton=mesh.get_editor_property('skeleton')
    report['mesh']=mesh.get_path_name();report['skeleton']=skeleton.get_path_name();report['materials']=[str(x.material_slot_name) for x in mesh.get_editor_property('materials')]
    skeleton.set_editor_property('compatible_skeletons',[unreal.load_asset('/Game/Characters/Mannequins/Meshes/SK_Mannequin')]);E.save_loaded_asset(skeleton)
    report['animations']={}
    for name in ['Idle','Walk','Run','Jump','Fall','Land','Spell']:
        options=unreal.FbxImportUI();options.automated_import_should_detect_type=False;options.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION
        options.import_mesh=False;options.import_animations=True;options.skeleton=skeleton;options.import_materials=False;options.import_textures=False
        options.anim_sequence_import_data.set_editor_property('animation_length',unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
        options.anim_sequence_import_data.set_editor_property('use_default_sample_rate',True)
        results=run_import(C/'Exports/motion05'/('A_Ember_'+name+'.fbx'),'A_Ember_'+name,options)
        seq=next(x for x in results if isinstance(x,unreal.AnimSequence));report['animations'][name]={'asset':seq.get_path_name(),'seconds':seq.get_play_length()}
    report['status']='imported; materials, controller and runtime validation pending';save_report()
    unreal.log('EMBER_IMPORT_COMPLETE')
except Exception:
    report['status']='failed';report['error']=traceback.format_exc();save_report();raise
