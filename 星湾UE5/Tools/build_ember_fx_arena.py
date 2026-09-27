"""Versioned native spell shader, character components and a separate test arena."""
import unreal,json,math,traceback
from pathlib import Path
P=Path(unreal.Paths.project_dir());D='/Game/Starbay/Ember_v04'
E=unreal.EditorAssetLibrary;A=unreal.AssetToolsHelpers.get_asset_tools();M=unreal.MaterialEditingLibrary
R={'status':'started'}
def save_report(): (P/'Saved/ember_arena.json').write_text(json.dumps(R,indent=2),encoding='utf-8')
def create(name,cls,factory):return E.load_asset(D+'/'+name) if E.does_asset_exist(D+'/'+name) else A.create_asset(name,D,cls,factory)
def expr(mat,cls,**kw):
    n=M.create_material_expression(mat,cls)
    for k,v in kw.items():n.set_editor_property(k,v)
    return n
def ci(name):
    v=unreal.CustomInput();v.set_editor_property('input_name',name);return v
try:
    collection=create('MPC_EmberSpell',unreal.MaterialParameterCollection,unreal.MaterialParameterCollectionFactoryNew())
    scalar=unreal.CollectionScalarParameter();scalar.set_editor_property('parameter_name','SpellStart');scalar.set_editor_property('default_value',-1000.0)
    collection.set_editor_property('scalar_parameters',[scalar]);E.save_loaded_asset(collection)
    mat=create('M_EmberSpellGlyph',unreal.Material,unreal.MaterialFactoryNew())
    M.delete_all_material_expressions(mat);mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_ADDITIVE);mat.set_editor_property('two_sided',True)
    mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
    uv=expr(mat,unreal.MaterialExpressionTextureCoordinate);tm=expr(mat,unreal.MaterialExpressionTime)
    start=expr(mat,unreal.MaterialExpressionCollectionParameter,collection=collection,parameter_name='SpellStart')
    code='''float a=T-S; float env=smoothstep(0.,.3,a)*(1.-smoothstep(2.5,4.,a))*step(0.,a);
float2 p=(UV-.5)*2.; float r=length(p); float th=atan2(p.y,p.x)+T*.35;
float ring=exp(-abs(r-.78)*180.)+exp(-abs(r-.66)*160.)*.55;
float rune=pow(saturate(sin(th*12.+r*28.)),12.)*exp(-abs(r-.72)*45.);
float pulse=exp(-abs(r-frac(max(0.,a)*.85)) *65.)*.7;
float spokes=pow(saturate(cos(th*6.)),50.)*smoothstep(.25,.5,r)*(1.-smoothstep(.60,.67,r));
return float3(12.,1.65,.075)*(ring+rune+spokes+pulse)*env;'''
    custom=expr(mat,unreal.MaterialExpressionCustom,code=code,output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3,inputs=[ci('UV'),ci('T'),ci('S')])
    for n,pin in [(uv,'UV'),(tm,'T'),(start,'S')]:M.connect_material_expressions(n,'',custom,pin)
    M.connect_material_property(custom,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    one=expr(mat,unreal.MaterialExpressionConstant,r=1.0);M.connect_material_property(one,'',unreal.MaterialProperty.MP_OPACITY)
    M.recompile_material(mat);E.save_loaded_asset(mat)
    bp=E.load_asset(D+'/BP_EmberCharacter');sub=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem);lib=unreal.SubobjectDataBlueprintFunctionLibrary
    handles=sub.k2_gather_subobject_data_for_blueprint(bp)
    def obj(h):return lib.get_object_for_blueprint(lib.get_data(h),bp)
    R['components']=[str(obj(h)) for h in handles]
    capsule=next(h for h in handles if isinstance(obj(h),unreal.CapsuleComponent))
    mesh_handle=next(h for h in handles if isinstance(obj(h),unreal.SkeletalMeshComponent))
    for label,parent,loc,scale in [('SpellGround',capsule,(0,0,-87),(3.6,3.6,3.6)),('SpellHalo',capsule,(60,0,45),(1.25,1.25,1.25))]:
        found=next((h for h in handles if obj(h) and label in obj(h).get_name()),None)
        if found is None:
            params=unreal.AddNewSubobjectParams();params.set_editor_property('parent_handle',parent);params.set_editor_property('new_class',unreal.StaticMeshComponent);params.set_editor_property('blueprint_context',bp)
            found,reason=sub.add_new_subobject(params=params)
            if not lib.is_handle_valid(found):raise RuntimeError(str(reason))
            sub.rename_subobject(found,unreal.Text(label));sub.attach_subobject(parent,found)
        comp=obj(found);comp.set_static_mesh(E.load_asset('/Engine/BasicShapes/Plane'));comp.set_material(0,mat)
        comp.set_editor_property('relative_location',unreal.Vector(*loc));comp.set_editor_property('relative_scale3d',unreal.Vector(*scale));comp.set_editor_property('cast_shadow',False)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        if label=='SpellHalo':comp.set_editor_property('relative_rotation',unreal.Rotator(90,0,0))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp);E.save_loaded_asset(bp)
    mapname=D+'/L_EmberArena'
    if not E.does_asset_exist(mapname):
        levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);assert levels.new_level(mapname)
        actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        def spawn(cls,loc,label):
            actor=actors.spawn_actor_from_class(cls,unreal.Vector(*loc));actor.set_actor_label(label);return actor
        stone=create('M_ArenaBasalt',unreal.Material,unreal.MaterialFactoryNew())
        if M.get_num_material_expressions(stone)==0:
            n=expr(stone,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.027,.019,.025,1));M.connect_material_property(n,'',unreal.MaterialProperty.MP_BASE_COLOR)
            n=expr(stone,unreal.MaterialExpressionConstant,r=.38);M.connect_material_property(n,'',unreal.MaterialProperty.MP_ROUGHNESS);M.recompile_material(stone);E.save_loaded_asset(stone)
        for i in range(13):
            if i==0:loc=(0,0,-30);scale=(28,28,.5)
            else:
                angle=i/12*math.tau;loc=(math.cos(angle)*1050,math.sin(angle)*1050,70);scale=(.6,.6,1.9+(i%3)*.2)
            a=spawn(unreal.StaticMeshActor,loc,'Basalt stage' if i==0 else 'Obsidian pillar %02d'%i);a.set_actor_scale3d(unreal.Vector(*scale))
            c=a.static_mesh_component;c.set_static_mesh(E.load_asset('/Engine/BasicShapes/Cylinder' if i==0 else '/Engine/BasicShapes/Cube'));c.set_material(0,stone)
        light=spawn(unreal.DirectionalLight,(0,0,700),'Warm key');light.set_actor_rotation(unreal.Rotator(-35,-35,0),False);light.light_component.set_editor_property('intensity',5.0)
        sky=spawn(unreal.SkyLight,(0,0,500),'Soft fill');sky.light_component.set_editor_property('intensity',.8);sky.light_component.set_editor_property('real_time_capture',True)
        spawn(unreal.SkyAtmosphere,(0,0,0),'Atmosphere')
        for i in range(6):
            angle=i/6*math.tau;light=spawn(unreal.PointLight,(math.cos(angle)*650,math.sin(angle)*650,100),'Ember rim %d'%i)
            light.light_component.set_light_color(unreal.LinearColor(1,.075,.008,1));light.light_component.set_editor_property('intensity',12000.0);light.light_component.set_editor_property('attenuation_radius',800.0)
        spawn(unreal.PlayerStart,(0,0,110),'Ember Spawn')
        world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();world.get_world_settings().set_editor_property('default_game_mode',E.load_blueprint_class(D+'/BP_EmberGameMode'))
        levels.save_current_level()
    R['status']='arena and native shader/components saved; runtime/input verification pending';save_report();unreal.log('EMBER_ARENA_CREATED')
except Exception:R['status']='failed';R['error']=traceback.format_exc();save_report();raise
