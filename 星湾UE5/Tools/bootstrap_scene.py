"""Run inside Unreal Editor's Python plugin, after asset export.
Creates a NEW map only. Engine execution must pass before calling this a working UE build.
"""
import unreal
import json, math
from pathlib import Path

PROJECT=Path(unreal.Paths.project_dir()).resolve()
SOURCE=PROJECT/'SourceAssets'
CONTENT='/Game/Starbay/Import_v01'
MAP='/Game/Starbay/Maps/L_Starbay'
tools=unreal.AssetToolsHelpers.get_asset_tools()
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assets=unreal.EditorAssetLibrary
report={'status':'in_progress','engine':unreal.SystemLibrary.get_engine_version(),'assets':[],'warnings':[]}

def vec(v):return unreal.Vector(*v)
def center(mesh):
    b=mesh.get_bounding_box()
    return [(getattr(b.min,k)+getattr(b.max,k))*.5 for k in ['x','y','z']]

def imported_mesh(record):
    name=record['name'];path=CONTENT+'/Geometry/'+name
    if assets.does_asset_exist(path):
        raise RuntimeError('Import target already exists; preserve user edits. Choose a new import version: '+path)
    task=unreal.AssetImportTask()
    task.filename=str(SOURCE/record['file']);task.destination_path=CONTENT+'/Geometry'
    task.destination_name=name;task.automated=True;task.replace_existing=False;task.save=True
    # Explicit legacy FBX factory, stable across UE5 and independent of glTF scene import defaults.
    task.factory=unreal.FbxFactory()
    options=unreal.FbxImportUI()
    options.set_editor_property('import_as_skeletal',False)
    options.set_editor_property('import_mesh',True)
    options.set_editor_property('import_materials',True)
    options.set_editor_property('import_textures',True)
    options.set_editor_property('automated_import_should_detect_type',False)
    options.set_editor_property('mesh_type_to_import',unreal.FBXImportType.FBXIT_STATIC_MESH)
    data=options.static_mesh_import_data
    data.set_editor_property('combine_meshes',True)
    data.set_editor_property('auto_generate_collision',False)
    data.set_editor_property('convert_scene',True)
    data.set_editor_property('convert_scene_unit',True)
    task.options=options
    tools.import_asset_tasks([task])
    result=[o for o in task.get_objects() if isinstance(o,unreal.StaticMesh)]
    if len(result)!=1:raise RuntimeError(f'{name}: expected one static mesh, got {len(result)}')
    mesh=result[0]
    body=mesh.get_editor_property('body_setup')
    if body:
        body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    assets.save_loaded_asset(mesh)
    report['assets'].append({'source':record['file'],'asset':mesh.get_path_name(),'sourceSha256':record['sha256']})
    return mesh

def spawn(cls,label,location=(0,0,0),rotation=(0,0,0)):
    actor=actors.spawn_actor_from_class(cls,vec(location),unreal.Rotator(*rotation))
    if not actor:raise RuntimeError('Cannot create '+label)
    actor.set_actor_label(label)
    actor.set_folder_path('Starbay')
    return actor

def create_pbr_materials():
    source_file=SOURCE/'Materials'/'material_sources.json'
    if not source_file.exists():
        report['warnings'].append('Optional CC0 PBR maps missing; using embedded Blender materials.')
        return {}
    entries=json.loads(source_file.read_text(encoding='utf-8'))
    groups={}
    import hashlib
    for entry in entries:
        src=SOURCE/'Materials'/entry['file']
        if hashlib.sha256(src.read_bytes()).hexdigest()!=entry['sha256']:raise RuntimeError('PBR checksum mismatch')
        task=unreal.AssetImportTask();task.filename=str(src)
        task.destination_path=CONTENT+'/Textures';task.automated=True;task.save=True;task.replace_existing=False
        tools.import_asset_tasks([task])
        textures=[o for o in task.get_objects() if isinstance(o,unreal.Texture2D)]
        if len(textures)!=1:raise RuntimeError('Texture import failed: '+entry['file'])
        tex=textures[0]
        if entry['role']=='normal':
            tex.set_editor_property('srgb',False)
            tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
        elif entry['role']=='roughness':tex.set_editor_property('srgb',False)
        assets.save_loaded_asset(tex)
        groups.setdefault(entry['asset'],{})[entry['role']]=tex
    materials={}
    properties={'color':unreal.MaterialProperty.MP_BASE_COLOR,'normal':unreal.MaterialProperty.MP_NORMAL,'roughness':unreal.MaterialProperty.MP_ROUGHNESS}
    for name,textures in groups.items():
        mat=tools.create_asset('M_'+name,CONTENT+'/Materials',unreal.Material,unreal.MaterialFactoryNew())
        if not mat:raise RuntimeError('Cannot create PBR material')
        for i,(role,tex) in enumerate(textures.items()):
            node=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionTextureSample,-350,i*230)
            node.set_editor_property('texture',tex)
            if role=='normal':node.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
            elif role=='roughness':node.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
            unreal.MaterialEditingLibrary.connect_material_property(node,'R' if role=='roughness' else 'RGB',properties[role])
        unreal.MaterialEditingLibrary.recompile_material(mat);assets.save_loaded_asset(mat)
        materials[name]=mat
    return materials

def main():
    if assets.does_asset_exist(MAP):raise RuntimeError('Map already exists; not overwriting hand edits: '+MAP)
    manifest=json.loads((SOURCE/'asset_manifest.json').read_text(encoding='utf-8'))
    import hashlib
    for r in manifest['assets']:
        if hashlib.sha256((SOURCE/r['file']).read_bytes()).hexdigest()!=r['sha256']:
            raise RuntimeError('Asset checksum changed: '+r['file'])
    meshes={r['name']:imported_mesh(r) for r in manifest['assets']}
    pbr=create_pbr_materials()
    replacements={'v6_stone':'cobblestone_floor_01','v6_wood':'brown_planks_03'}
    details=meshes['SM_CourtyardDetails']
    for i,slot in enumerate(details.static_materials):
        for match,target in replacements.items():
            if match in str(slot.material_slot_name) and target in pbr:details.set_material(i,pbr[target])
    assets.save_loaded_asset(details)
    # Infer FBX orientation rather than assuming a Blender / Unreal axis convention.
    o=center(meshes['SM_Calibration_Origin']);e=center(meshes['SM_Calibration_East']);n=center(meshes['SM_Calibration_North'])
    east=[e[i]-o[i] for i in range(3)];north=[n[i]-o[i] for i in range(3)]
    scale=1000/math.hypot(east[0],east[1])
    transform=None
    for mirror in [1,-1]:
        yaw=math.pi/2-math.atan2(east[1]*mirror,east[0])
        c,s=math.cos(yaw),math.sin(yaw)
        nx=(north[0]*c-north[1]*mirror*s)*scale
        ny=(north[0]*s+north[1]*mirror*c)*scale
        if abs(nx-1000)<1 and abs(ny)<1:
            transform=(yaw,mirror,scale);break
    if transform is None:raise RuntimeError('Calibration failed; do not place misaligned art.')
    yaw,mirror,scale=transform
    box=meshes['SM_Calibration_Origin'].get_bounding_box()
    height=(box.max.z-box.min.z)*scale
    if abs(height-100)>1 or abs(o[2]*scale-50)>1:raise RuntimeError('Vertical scale or origin failed 1 m check')
    report['calibration']={'yawDegrees':math.degrees(yaw),'mirrorY':mirror,'scale':scale,'oneMeterHeightCm':height,'passed':True}
    if not levels.new_level(MAP):raise RuntimeError('Could not create map')
    for name in ['SM_District','SM_CourtyardDetails']:
        actor=spawn(unreal.StaticMeshActor,name,rotation=(0,math.degrees(yaw),0))
        actor.static_mesh_component.set_static_mesh(meshes[name])
        actor.set_actor_scale3d(vec((scale,scale*mirror,scale)))
    # Door art is intentionally not placed across the entry until the native door interaction exists.
    # Keep imported door meshes available for a later Blueprint; the first map stays walkable.
    report['warnings'].append('Door assets imported; native sliding-door Blueprint not implemented yet.')
    sun=spawn(unreal.DirectionalLight,'GoldenHour_Sun',rotation=(-18,-35,0))
    sun.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sun.light_component.set_editor_property('intensity',6.0)
    sun.light_component.set_editor_property('light_color',unreal.Color(255,218,173,255))
    sun.light_component.set_editor_property('atmosphere_sun_light',True)
    sky=spawn(unreal.SkyLight,'Sky_Fill')
    sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property('real_time_capture',True)
    sky.light_component.set_editor_property('intensity',1.0)
    spawn(unreal.SkyAtmosphere,'Atmosphere')
    fog=spawn(unreal.ExponentialHeightFog,'Distance_Haze')
    fog.component.set_editor_property('fog_density',.008)
    fog.component.set_editor_property('volumetric_fog',True)
    post=spawn(unreal.PostProcessVolume,'Cinematic_Grade')
    post.set_editor_property('unbound',True)
    settings=post.get_editor_property('settings')
    settings.set_editor_property('override_auto_exposure_bias',True)
    settings.set_editor_property('auto_exposure_bias',.25)
    settings.set_editor_property('override_bloom_intensity',True)
    settings.set_editor_property('bloom_intensity',.25)
    post.set_editor_property('settings',settings)
    # Original game position (4,22), facing toward the district. Engine units are centimeters.
    spawn(unreal.PlayerStart,'Player_Start',(-2200,400,130),rotation=(0,0,0))
    camera=spawn(unreal.CineCameraActor,'Courtyard_Review_Camera',(-3500,5400,330),rotation=(-8,48,0))
    camera.get_cine_camera_component().set_editor_property('current_focal_length',24.0)
    # Reuse the official template if present; do not pretend a flying default pawn is a third-person game.
    mode='/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode'
    if assets.does_asset_exist(mode):
        unreal.EditorLevelLibrary.get_editor_world().get_world_settings().set_editor_property('default_game_mode',assets.load_blueprint_class(mode))
        report['thirdPersonTemplate']=True
    else:
        report['thirdPersonTemplate']=False
        report['warnings'].append('Add the official Third Person content pack before gameplay acceptance. Current map is an environment review scene.')
    if not levels.save_current_level():raise RuntimeError('Could not save map')
    assets.save_directory('/Game/Starbay',only_if_is_dirty=True,recursive=True)
    report['status']='scene_created'
    report['runtimeGameplayVerified']=False

try:main()
except Exception as exc:
    report['status']='failed';report['error']=str(exc)
    raise
finally:
    (PROJECT/'Saved').mkdir(exist_ok=True)
    (PROJECT/'Saved'/'scene_import_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    unreal.log(json.dumps(report,ensure_ascii=False))
