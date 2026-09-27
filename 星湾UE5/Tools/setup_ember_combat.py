"""Adapt Epic's installed Blueprint combat template to a native Ember spell controller.

Requires the licensed Standard/Variant_Combat content copied into this project.
The existing Starbay template/maps are untouched. No Python is used at runtime.
"""
import unreal,json,traceback
from pathlib import Path
P=Path(unreal.Paths.project_dir());D='/Game/Starbay/Ember_v04';E=unreal.EditorAssetLibrary
R={'status':'started'}
def make_key(name):
    result=unreal.Key();result.set_editor_property('key_name',name);return result
try:
    path=D+'/BP_EmberCombat'
    bp=E.load_asset(path) if E.does_asset_exist(path) else E.duplicate_asset('/Game/Variant_Combat/Blueprints/BP_CombatCharacter',path)
    cdo=unreal.get_default_object(bp.generated_class());mesh=cdo.get_component_by_class(unreal.SkeletalMeshComponent)
    mesh.set_skeletal_mesh_asset(E.load_asset(D+'/SK_EmberRegent'));mesh.set_anim_instance_class(E.load_blueprint_class(D+'/ABP_Ember'))
    montage=E.load_asset(D+'/AM_EmberSpell')
    for key,value in [('Combo Attack Montage',montage),('Combo Section Names',['Default']),('Charged Attack Montage',montage),('Charge Attack Section','Default'),('Charge Loop Section','Default')]:cdo.set_editor_property(key,value)
    cdo.get_component_by_class(unreal.CharacterMovementComponent).set_editor_property('max_walk_speed',600.0)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp);E.save_loaded_asset(bp)
    imc=E.load_asset('/Game/Variant_Combat/Input/IMC_Combat');combo=E.load_asset('/Game/Variant_Combat/Input/Actions/IA_ComboAttack')
    mappings=[m for m in imc.get_editor_property('mappings') if m.action];R['mapping_before']=[{'key':str(m.key),'action':m.action.get_name()} for m in mappings]
    imc.set_editor_property('mappings',mappings)
    if not any(str(m.key.get_editor_property('key_name'))=='Q' for m in mappings):imc.map_key(combo,make_key('Q'))
    sprint_path=D+'/IA_EmberSprint'
    if not E.does_asset_exist(sprint_path):
        sprint=E.duplicate_asset('/Game/Variant_Combat/Input/Actions/IA_ComboAttack',sprint_path)
        sprint.set_editor_property('triggers',[]);E.save_loaded_asset(sprint)
    else:sprint=E.load_asset(sprint_path)
    if not any(any(isinstance(t,unreal.InputTriggerChordAction) for t in m.triggers) for m in imc.get_editor_property('mappings')):
        if not any(m.action==sprint for m in imc.get_editor_property('mappings')):imc.map_key(sprint,make_key('LeftShift'))
        maps=list(imc.get_editor_property('mappings'));extra=[]
        for mapping in maps:
            if str(mapping.key.get_editor_property('key_name')) not in ['W','A','S','D'] or mapping.action.get_name()!='IA_Move':continue
            fast=unreal.EnhancedActionKeyMapping();fast.set_editor_property('key',mapping.key);fast.set_editor_property('action',mapping.action);fast.set_editor_property('modifiers',list(mapping.modifiers))
            chord=unreal.new_object(unreal.InputTriggerChordAction);chord.set_editor_property('chord_action',sprint);chord.rename('EmberChord_'+str(mapping.key.get_editor_property('key_name')),imc);fast.set_editor_property('triggers',[chord]);extra.append(fast)
            slow=unreal.new_object(unreal.InputModifierScalar);slow.set_editor_property('scalar',unreal.Vector(.5,.5,.5));slow.rename('EmberWalk_'+str(mapping.key.get_editor_property('key_name')),imc);mapping.set_editor_property('modifiers',list(mapping.modifiers)+[slow])
        imc.set_editor_property('mappings',maps+extra)
    E.save_loaded_asset(imc)
    seq=E.load_asset(D+'/A_Ember_Spell');lib=unreal.AnimationLibrary
    tracks=lib.get_animation_notify_track_names(seq)
    if 'EmberFX' not in [str(x) for x in tracks]:
        lib.add_animation_notify_track(seq,'EmberFX')
        notify=lib.add_animation_notify_event(seq,'EmberFX',1.62,unreal.AnimNotify_PlayNiagaraEffect)
        notify.set_editor_property('template',E.load_asset('/Game/Variant_Combat/VFX/NS_Damage'));notify.set_editor_property('socket_name','hand_r');notify.set_editor_property('attached',True);notify.set_editor_property('scale',unreal.Vector(1.8,1.8,1.8));notify.set_editor_property('should_fire_in_editor',False)
        E.save_loaded_asset(seq)
    gm=E.load_asset(D+'/BP_EmberGameMode');g=unreal.get_default_object(gm.generated_class());g.set_editor_property('default_pawn_class',bp.generated_class());g.set_editor_property('player_controller_class',E.load_blueprint_class('/Game/Variant_Combat/Blueprints/BP_CombatPlayerController'));unreal.BlueprintEditorLibrary.compile_blueprint(gm);E.save_loaded_asset(gm)
    R['status']='native combat Blueprint configured; Enhanced Input and notify tests pending'
except Exception:R['status']='failed';R['error']=traceback.format_exc();raise
finally:(P/'Saved/ember_combat.json').write_text(json.dumps(R,indent=2),encoding='utf-8')
