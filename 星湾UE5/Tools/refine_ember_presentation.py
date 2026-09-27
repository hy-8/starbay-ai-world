"""Refine the owned arena and character material response. Editor-only authoring."""
import unreal,json
from pathlib import Path
E=unreal.EditorAssetLibrary;M=unreal.MaterialEditingLibrary;D='/Game/Starbay/Ember_v04'
P=Path(unreal.Paths.project_dir());r={}
def node(mat,cls,**values):
    n=M.create_material_expression(mat,cls)
    for k,v in values.items():n.set_editor_property(k,v)
    return n
def const(mat,v,prop):M.connect_material_property(node(mat,unreal.MaterialExpressionConstant,r=v),'',prop)
def rgb(mat,v,prop):M.connect_material_property(node(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(*v,1)),'',prop)
palette={
'Amber iris':((.12,.045,.008),0,.35),'Brushed champagne gold':((.52,.25,.055),.85,.36),
'Garnet cabochon':((.19,.006,.003),.15,.22),'Amber hot filament':((.5,.06,.001),0,.4),
'Obsidian brocade':((.013,.009,.016),0,.63),'Garnet woven silk':((.13,.004,.009),0,.62),
'Deep oxblood silk velvet':((.065,.002,.006),0,.7),'Porcelain warm skin':((.48,.31,.23),0,.61),
'Ivory fiber 0':((.55,.57,.59),0,.63),'Pupil':((.003,.002,.001),0,.4),
'Vermilion silk lining':((.16,.005,.008),0,.62),'Warm ivory silk':((.57,.49,.36),0,.65),
'Thin dark garnet organza':((.045,.002,.006),0,.7),'Basalt bronze inset':((.014,.008,.003),.5,.45),
'Natural scalp beneath white hair':((.48,.32,.24),0,.66),'Eye sclera':((.59,.56,.51),0,.33)}
mesh=E.load_asset(D+'/SK_EmberRegent');r['slots']=[]
for i,slot in enumerate(mesh.get_editor_property('materials')):
    name=str(slot.material_slot_name);color,metal,rough=palette[name];mat=E.load_asset(D+'/M_Ember_%02d'%i)
    M.delete_all_material_expressions(mat);mat.set_editor_property('two_sided',True)
    rgb(mat,color,unreal.MaterialProperty.MP_BASE_COLOR);const(mat,metal,unreal.MaterialProperty.MP_METALLIC);const(mat,rough,unreal.MaterialProperty.MP_ROUGHNESS);const(mat,.3,unreal.MaterialProperty.MP_SPECULAR)
    if name in ['Garnet woven silk','Vermilion silk lining']:
        albedo=node(mat,unreal.MaterialExpressionTextureSample,texture=E.load_asset(D+'/T_Ember_Albedo'))
        M.connect_material_property(albedo,'RGB',unreal.MaterialProperty.MP_BASE_COLOR)
        normal=node(mat,unreal.MaterialExpressionTextureSample,texture=E.load_asset(D+'/T_Ember_Normal'),sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        M.connect_material_property(normal,'RGB',unreal.MaterialProperty.MP_NORMAL)
    if name=='Amber hot filament':rgb(mat,(2.2,.18,.003),unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    M.recompile_material(mat);E.save_loaded_asset(mat,False);r['slots'].append(name)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in actors.get_all_level_actors():
    if isinstance(a,unreal.PointLight):
        a.light_component.set_editor_property('intensity',4.0)
        a.light_component.set_light_color(unreal.LinearColor(1,.22,.06,1))
    if isinstance(a,unreal.DirectionalLight):
        a.light_component.set_editor_property('intensity',3.0);a.light_component.set_light_color(unreal.LinearColor(1,.94,.85,1))
    if isinstance(a,unreal.SkyLight):a.light_component.set_editor_property('intensity',.6)
    if isinstance(a,unreal.StaticMeshActor) and ('Basalt' in a.get_actor_label() or 'pillar' in a.get_actor_label()):a.static_mesh_component.set_material(0,E.load_asset(D+'/M_ArenaBasalt'))
# Keep the normal play camera far enough to see the robe and staff.
bp=E.load_asset(D+'/BP_EmberHero');c=unreal.get_default_object(bp.generated_class())
sub=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem);lib=unreal.SubobjectDataBlueprintFunctionLibrary
for h in sub.k2_gather_subobject_data_for_blueprint(bp):
    o=lib.get_object_for_blueprint(lib.get_data(h),bp)
    if isinstance(o,unreal.SpringArmComponent):o.set_editor_property('target_arm_length',560.0);o.set_editor_property('socket_offset',unreal.Vector(0,60,65))
unreal.BlueprintEditorLibrary.compile_blueprint(bp);E.save_loaded_asset(bp,False)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
(P/'Saved/ember_presentation.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
