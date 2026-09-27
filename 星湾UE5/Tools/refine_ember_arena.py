"""Original basalt/lava material and soft portrait lighting in the owned arena."""
import unreal,math,json
from pathlib import Path
E=unreal.EditorAssetLibrary;M=unreal.MaterialEditingLibrary;A=unreal.AssetToolsHelpers.get_asset_tools();D='/Game/Starbay/Ember_v04'
def n(mat,cls,**props):
    o=M.create_material_expression(mat,cls)
    for k,v in props.items():o.set_editor_property(k,v)
    return o
def ci(name):
    x=unreal.CustomInput();x.set_editor_property('input_name',name);return x
def make(name):return E.load_asset(D+'/'+name) if E.does_asset_exist(D+'/'+name) else A.create_asset(name,D,unreal.Material,unreal.MaterialFactoryNew())
stone=make('M_ArenaBasalt');M.delete_all_material_expressions(stone)
pos=n(stone,unreal.MaterialExpressionWorldPosition)
shader=n(stone,unreal.MaterialExpressionCustom,code='float grain=frac(sin(dot(floor(P.xy*.38),float2(12.9898,78.233)))*43758.5453); return float3(.019,.016,.023)*(0.7+grain*.6);',output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3,inputs=[ci('P')])
M.connect_material_expressions(pos,'XYZ',shader,'P');M.connect_material_property(shader,'',unreal.MaterialProperty.MP_BASE_COLOR)
rough=n(stone,unreal.MaterialExpressionConstant,r=.84);M.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
M.recompile_material(stone);E.save_loaded_asset(stone,False)
lava=make('M_ArenaLava');M.delete_all_material_expressions(lava)
lava.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
pos=n(lava,unreal.MaterialExpressionWorldPosition);tm=n(lava,unreal.MaterialExpressionTime)
code='''float2 uv=P.xy/145.;float2 id=floor(uv);float2 f=frac(uv);float d1=9.,d2=9.;
for(int x=-1;x<=1;x++){for(int y=-1;y<=1;y++){float2 g=float2(x,y);float2 h=frac(sin(float2(dot(id+g,float2(127.1,311.7)),dot(id+g,float2(269.5,183.3))))*43758.5453);float d=length(g+h-f);if(d<d1){d2=d1;d1=d;}else d2=min(d2,d);}}
float seam=1.-smoothstep(.01,.045,d2-d1);return float3(3.5,.19,.005)*seam*(.65+.2*sin(T*.8+P.x*.008))+float3(.018,.008,.009);'''
shader=n(lava,unreal.MaterialExpressionCustom,code=code,output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3,inputs=[ci('P'),ci('T')])
M.connect_material_expressions(pos,'XYZ',shader,'P');M.connect_material_expressions(tm,'',shader,'T');M.connect_material_property(shader,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
M.recompile_material(lava);E.save_loaded_asset(lava,False)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);existing={a.get_actor_label():a for a in actors.get_all_level_actors()}
for a in list(existing.values()):
    if isinstance(a,unreal.StaticMeshActor) and ('Basalt' in a.get_actor_label() or 'pillar' in a.get_actor_label()):
        a.static_mesh_component.set_material(0,stone)
        if 'Basalt' in a.get_actor_label():a.set_actor_scale3d(unreal.Vector(46,46,.5))
    if isinstance(a,unreal.PointLight):a.light_component.set_editor_property('intensity',1.0)
    if isinstance(a,unreal.DirectionalLight):
        a.light_component.set_editor_property('atmosphere_sun_light',True)
        a.set_actor_rotation(unreal.Rotator(-14,-35,0),False)
pp=existing.get('Ember fixed exposure')
if not pp:
    pp=actors.spawn_actor_from_class(unreal.PostProcessVolume,unreal.Vector(0,0,0));pp.set_actor_label('Ember fixed exposure')
pp.set_editor_property('unbound',True)
settings=pp.get_editor_property('settings')
for k,v in {'override_auto_exposure_min_brightness':True,'override_auto_exposure_max_brightness':True,'auto_exposure_min_brightness':1.0,'auto_exposure_max_brightness':1.0,'override_bloom_intensity':True,'bloom_intensity':.3}.items():settings.set_editor_property(k,v)
pp.set_editor_property('settings',settings)
if 'Lava surround' not in existing:
    a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,-70));a.set_actor_label('Lava surround');a.set_actor_scale3d(unreal.Vector(180,180,.1));a.static_mesh_component.set_static_mesh(E.load_asset('/Engine/BasicShapes/Cylinder'));a.static_mesh_component.set_material(0,lava)
if 'Portrait softbox' not in existing:
    loc=unreal.Vector(440,290,340);a=actors.spawn_actor_from_class(unreal.RectLight,loc);a.set_actor_label('Portrait softbox');a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(loc,unreal.Vector(0,0,125)),False)
    light=a.get_component_by_class(unreal.RectLightComponent);light.set_editor_property('intensity',12.0);light.set_editor_property('source_width',230.0);light.set_editor_property('source_height',230.0);light.set_editor_property('attenuation_radius',1800.0)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
