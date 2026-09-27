"""Independent native walk/sprint mappings after isolated Combat BP remapping."""
import unreal,json
from pathlib import Path
E=unreal.EditorAssetLibrary;D='/Game/Starbay/Ember_v04'
imc=E.load_asset('/Game/Variant_Combat/Input/IMC_Combat')
walk=E.load_asset('/Game/Input/Actions/IA_Move');run=E.load_asset(D+'/IA_EmberSprintMove');shift=E.load_asset(D+'/IA_EmberSprint')
assert run
def key(name):
    k=unreal.Key();k.set_editor_property('key_name',name);return k
def mapping(action,name,mods=(),triggers=()):
    m=unreal.EnhancedActionKeyMapping();m.set_editor_property('action',action);m.set_editor_property('key',key(name));m.set_editor_property('modifiers',list(mods));m.set_editor_property('triggers',list(triggers));return m
maps=[]
for m in imc.get_editor_property('mappings'):
    if not m.action or m.action in [walk,run,shift] or str(m.key.get_editor_property('key_name')) in ['SpaceBar','RightMouseButton']:continue
    maps.append(m)
template=E.load_asset('/Game/Input/IMC_Default')
for original in template.get_editor_property('mappings'):
    if original.action!=walk:continue
    name=str(original.key.get_editor_property('key_name'));mods=list(original.modifiers)
    slow=unreal.new_object(unreal.InputModifierScalar);slow.set_editor_property('scalar',unreal.Vector(.5,.5,.5));slow.rename('WalkScale_'+name,imc)
    maps.append(mapping(walk,name,mods+[slow]))
    chord=unreal.new_object(unreal.InputTriggerChordAction);chord.set_editor_property('chord_action',shift);chord.rename('SprintChord_'+name,imc)
    maps.append(mapping(run,name,mods,[chord]))
maps.append(mapping(shift,'LeftShift'));maps.append(mapping(E.load_asset('/Game/Input/Actions/IA_Jump'),'SpaceBar'));maps.append(mapping(E.load_asset('/Game/Input/Actions/IA_Jump'),'Gamepad_FaceButton_Bottom'))
imc.set_editor_property('mappings',maps);E.save_loaded_asset(imc,False)
hero=E.load_asset(D+'/BP_EmberHero');unreal.BlueprintEditorLibrary.compile_blueprint(hero);E.save_loaded_asset(hero,False)
(Path(unreal.Paths.project_dir())/'Saved/ember_control_repair.json').write_text(json.dumps({'status':'configured','walk_action':walk.get_path_name(),'sprint_action':run.get_path_name(),'bindings':len(maps)}),encoding='utf-8')
