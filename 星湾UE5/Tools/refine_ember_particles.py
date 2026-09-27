"""Original procedural ember sprite on a licensed template burst simulation.
Driven by animation notifies, so effects work in a packaged native game.
"""
import unreal,json,traceback
from pathlib import Path
P=Path(unreal.Paths.project_dir());D='/Game/Starbay/Ember_v04';E=unreal.EditorAssetLibrary;A=unreal.AssetToolsHelpers.get_asset_tools();M=unreal.MaterialEditingLibrary
R={'status':'started'}
def create(name,cls,factory):return E.load_asset(D+'/'+name) if E.does_asset_exist(D+'/'+name) else A.create_asset(name,D,cls,factory)
def n(mat,cls,**props):
    out=M.create_material_expression(mat,cls)
    for k,v in props.items():out.set_editor_property(k,v)
    return out
def ci(name):
    x=unreal.CustomInput();x.set_editor_property('input_name',name);return x
try:
    mat=create('M_EmberFireSprite',unreal.Material,unreal.MaterialFactoryNew());M.delete_all_material_expressions(mat)
    mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_ADDITIVE);mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT);mat.set_editor_property('two_sided',True);mat.set_editor_property('used_with_niagara_sprites',True)
    uv=n(mat,unreal.MaterialExpressionTextureCoordinate);tm=n(mat,unreal.MaterialExpressionTime);pc=n(mat,unreal.MaterialExpressionParticleColor)
    code='''float2 p=(UV-.5)*2.;float y=p.y;float width=.25+.10*sin(y*13.+T*21.);
float flame=pow(saturate(1.-abs(p.x)/max(.04,width))*(1.-smoothstep(-.4,1.,y)),2.);
float core=exp(-dot(p,p)*8.);float mask=saturate(core+flame*.65)*A;
return lerp(float3(8.,.45,.008),float3(10.,3.8,.32),core)*mask;'''
    shader=n(mat,unreal.MaterialExpressionCustom,code=code,output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3,inputs=[ci('UV'),ci('T'),ci('A')])
    M.connect_material_expressions(uv,'',shader,'UV');M.connect_material_expressions(tm,'',shader,'T');M.connect_material_expressions(pc,'A',shader,'A');M.connect_material_property(shader,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    one=n(mat,unreal.MaterialExpressionConstant,r=1);M.connect_material_property(one,'',unreal.MaterialProperty.MP_OPACITY);M.recompile_material(mat);E.save_loaded_asset(mat)
    name=D+'/NS_EmberCast';system=E.load_asset(name) if E.does_asset_exist(name) else E.duplicate_asset('/Game/Variant_Combat/VFX/NS_Damage',name)
    changed=[]
    for obj in unreal.ObjectIterator():
        if isinstance(obj,unreal.NiagaraSpriteRendererProperties) and unreal.SystemLibrary.get_path_name(obj).startswith(system.get_path_name()+':'):
            obj.set_editor_property('material',mat);changed.append(obj.get_path_name())
    assert changed,'Burst renderer not found';E.save_loaded_asset(system);R['renderers']=changed
    seq=E.load_asset(D+'/A_Ember_Spell');lib=unreal.AnimationLibrary
    for obj in unreal.ObjectIterator():
        if isinstance(obj,unreal.AnimNotify_PlayNiagaraEffect) and obj.get_path_name().startswith(seq.get_path_name()+':'):obj.set_editor_property('template',system)
    if 'EmberFireV2' not in [str(x) for x in lib.get_animation_notify_track_names(seq)]:
        lib.add_animation_notify_track(seq,'EmberFireV2')
        for when,scale in [(.32,.32),(.70,.45),(1.84,1.1),(2.05,.60)]:
            notify=lib.add_animation_notify_event(seq,'EmberFireV2',when,unreal.AnimNotify_PlayNiagaraEffect)
            for k,v in {'template':system,'socket_name':'hand_r','attached':True,'scale':unreal.Vector(scale,scale,scale),'should_fire_in_editor':False}.items():notify.set_editor_property(k,v)
    E.save_loaded_asset(seq);R['status']='native notify-driven fire burst saved; visual verification pending'
except Exception:R['status']='failed';R['error']=traceback.format_exc();raise
finally:(P/'Saved/ember_particles.json').write_text(json.dumps(R,indent=2),encoding='utf-8')
