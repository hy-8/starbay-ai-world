"""Configure the owned Ember_v02 candidate with PBR materials and native locomotion BP.
Does not change the official template assets or the existing Starbay map.
"""
import unreal,json,traceback
from pathlib import Path
P=Path(unreal.Paths.project_dir()).resolve();C=P.parent/'角色工坊/焰冕行者';D='/Game/Starbay/Ember_v04'
E=unreal.EditorAssetLibrary;A=unreal.AssetToolsHelpers.get_asset_tools();M=unreal.MaterialEditingLibrary
REPORT=P/'Saved/ember_setup_v04.json';report={'status':'started','changes':[]}
def write():REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8')
def create(name,cls,factory):
    old=E.load_asset(D+'/'+name) if E.does_asset_exist(D+'/'+name) else None
    return old or A.create_asset(name,D,cls,factory)
def duplicate(src,name):return E.load_asset(D+'/'+name) if E.does_asset_exist(D+'/'+name) else E.duplicate_asset(src,D+'/'+name)
def node(mat,cls,**props):
    obj=M.create_material_expression(mat,cls)
    for k,v in props.items():obj.set_editor_property(k,v)
    return obj
def constant(mat,value,prop):
    n=node(mat,unreal.MaterialExpressionConstant,r=value);M.connect_material_property(n,'',prop);return n
def custom_input(name):
    item=unreal.CustomInput();item.set_editor_property('input_name',name);return item
def rgb(mat,value,prop):
    n=node(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(*value,1));M.connect_material_property(n,'',prop);return n
try:
    mesh=E.load_asset(D+'/SK_EmberRegent');sk=mesh.get_editor_property('skeleton')
    texture={}
    for suffix in ['Albedo','ORM','Normal']:
        name='T_Ember_'+suffix;tex=E.load_asset(D+'/'+name) if E.does_asset_exist(D+'/'+name) else None
        if not tex:
            t=unreal.AssetImportTask();t.filename=str(C/'Materials'/('Ember_Brocade_'+suffix+'.png'));t.destination_path=D;t.destination_name=name;t.automated=True;t.save=True
            A.import_asset_tasks([t]);tex=E.load_asset(t.imported_object_paths[0])
        if suffix!='Albedo':tex.set_editor_property('srgb',False)
        if suffix=='Normal':tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
        E.save_loaded_asset(tex);texture[suffix]=tex
    palette={
      'Amber iris':((.16,.06,.008),.05,.26), 'Brushed champagne gold':((.62,.29,.065),.82,.28),
      'Garnet cabochon':((.31,.005,.001),.32,.16), 'Amber hot filament':((1,.09,.002),.0,.30),
      'Obsidian brocade':((.01,.006,.01),.1,.52), 'Garnet woven silk':((.18,.003,.008),.2,.5),
      'Deep oxblood silk velvet':((.10,.002,.004),0,.59), 'Porcelain warm skin':((.53,.32,.24),0,.51),
      'Ivory fiber 0':((.68,.70,.72),.05,.36), 'Pupil':((.004,.002,.001),0,.30),
      'Vermilion silk lining':((.18,.003,.008),.2,.50), 'Warm ivory silk':((.66,.57,.42),.02,.50),
      'Thin dark garnet organza':((.045,.002,.006),0,.52), 'Basalt bronze inset':((.012,.006,.002),.6,.35),
      'Natural scalp beneath white hair':((.53,.34,.24),0,.65), 'Eye sclera':((.66,.63,.58),0,.21)}
    slots=list(mesh.get_editor_property('materials'))
    for index,slot in enumerate(slots):
        key=str(slot.material_slot_name);color,metal,rough=palette[key]
        existing=E.load_asset(D+'/M_Ember_%02d'%index) if E.does_asset_exist(D+'/M_Ember_%02d'%index) else None
        if not existing and E.does_asset_exist('/Game/Starbay/Ember_v02/M_Ember_%02d'%index):
            existing=E.duplicate_asset('/Game/Starbay/Ember_v02/M_Ember_%02d'%index,D+'/M_Ember_%02d'%index)
        if existing:
            E.save_loaded_asset(existing);slot.set_editor_property('material_interface',existing);slots[index]=slot;continue
        mat=create('M_Ember_%02d'%index,unreal.Material,unreal.MaterialFactoryNew())
        M.delete_all_material_expressions(mat);mat.set_editor_property('two_sided',True)
        rgb(mat,color,unreal.MaterialProperty.MP_BASE_COLOR);constant(mat,metal,unreal.MaterialProperty.MP_METALLIC);constant(mat,rough,unreal.MaterialProperty.MP_ROUGHNESS)
        if key in ['Garnet woven silk','Vermilion silk lining']:
            base=node(mat,unreal.MaterialExpressionTextureSample,texture=texture['Albedo']);M.connect_material_property(base,'RGB',unreal.MaterialProperty.MP_BASE_COLOR)
            orm=node(mat,unreal.MaterialExpressionTextureSample,texture=texture['ORM'],sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
            M.connect_material_property(orm,'G',unreal.MaterialProperty.MP_ROUGHNESS);M.connect_material_property(orm,'B',unreal.MaterialProperty.MP_METALLIC)
            norm=node(mat,unreal.MaterialExpressionTextureSample,texture=texture['Normal'],sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL);M.connect_material_property(norm,'RGB',unreal.MaterialProperty.MP_NORMAL)
        if key=='Amber hot filament':
            uv=node(mat,unreal.MaterialExpressionTextureCoordinate);time=node(mat,unreal.MaterialExpressionTime)
            custom=node(mat,unreal.MaterialExpressionCustom,code='return float3(5.0,0.48,0.012)*(0.70+0.30*sin(T*4+UV.x*19+UV.y*28));',output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3,inputs=[custom_input('UV'),custom_input('T')])
            M.connect_material_expressions(uv,'',custom,'UV');M.connect_material_expressions(time,'',custom,'T');M.connect_material_property(custom,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        M.recompile_material(mat);E.save_loaded_asset(mat);slot.material_interface=mat;slots[index]=slot
    mesh.set_editor_property('materials',slots);E.save_loaded_asset(mesh)
    report['changes'].append('16 PBR slots assigned; animated molten emission');write()
    anims={name:E.load_asset(D+'/A_Ember_'+name) for name in ['Idle','Walk','Run','Jump','Fall','Land','Spell']}
    template_bs=E.load_asset('/Game/Characters/Mannequins/Anims/Unarmed/BS_Idle_Walk_Run')
    bf=unreal.BlendSpaceFactoryNew();bf.set_editor_property('target_skeleton',sk)
    bs=create('BS_EmberMotion',unreal.BlendSpace,bf)
    samples=list(template_bs.get_editor_property('sample_data'))
    bs.set_editor_property('blend_parameters',template_bs.get_editor_property('blend_parameters'))
    report['blend_samples']=[]
    for sample in samples:
        old=sample.get_editor_property('animation');name=old.get_name()
        key='Idle' if 'Idle' in name else ('Walk' if 'Walk' in name else 'Run')
        sample.set_editor_property('animation',anims[key]);report['blend_samples'].append({'old':name,'new':key,'position':str(sample.get_editor_property('sample_value'))})
    bs.set_editor_property('sample_data',samples);E.save_loaded_asset(bs)
    bp=duplicate('/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed','ABP_Ember')
    bp.set_editor_property('target_skeleton',sk)
    changes=[]
    for obj in unreal.ObjectIterator():
        if isinstance(obj,type):continue
        if not unreal.SystemLibrary.get_path_name(obj).startswith(bp.get_path_name()+':'):continue
        if isinstance(obj,unreal.AnimGraphNode_SequencePlayer):
            data=obj.get_editor_property('node');old=data.get_editor_property('sequence')
            if not old:continue
            name=old.get_name();key=next((k for k in ['Idle','Jump','Fall','Land'] if k in name),None)
            if key:data.set_editor_property('sequence',anims[key]);obj.set_editor_property('node',data);changes.append(obj.get_path_name())
        elif isinstance(obj,unreal.AnimGraphNode_BlendSpacePlayer):
            data=obj.get_editor_property('node');data.set_editor_property('blend_space',bs);obj.set_editor_property('node',data);changes.append(obj.get_path_name())
    assert changes,'No animation graph nodes remapped'
    unreal.BlueprintEditorLibrary.compile_blueprint(bp);E.save_loaded_asset(bp);report['remapped_nodes']=changes;write()
    character=duplicate('/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter','BP_EmberCharacter')
    cdo=unreal.get_default_object(character.generated_class());comp=cdo.get_component_by_class(unreal.SkeletalMeshComponent)
    comp.set_skeletal_mesh_asset(mesh);comp.set_anim_instance_class(bp.generated_class())
    cdo.get_component_by_class(unreal.CharacterMovementComponent).set_editor_property('max_walk_speed',300.0)
    unreal.BlueprintEditorLibrary.compile_blueprint(character);E.save_loaded_asset(character)
    gm=duplicate('/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode','BP_EmberGameMode')
    unreal.get_default_object(gm.generated_class()).set_editor_property('default_pawn_class',character.generated_class());unreal.BlueprintEditorLibrary.compile_blueprint(gm);E.save_loaded_asset(gm)
    factory=unreal.AnimMontageFactory();factory.target_skeleton=sk;factory.source_animation=anims['Spell']
    montage=create('AM_EmberSpell',unreal.AnimMontage,factory);E.save_loaded_asset(montage)
    report['character']=character.get_path_name();report['montage']=montage.get_path_name();report['status']='configured; input binding and runtime tests pending';write();unreal.log('EMBER_SETUP_COMPLETE')
except Exception:
    report['status']='failed';report['error']=traceback.format_exc();write();raise
