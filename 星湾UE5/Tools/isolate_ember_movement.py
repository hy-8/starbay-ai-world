"""Run ONLY in a disposable project copy, then transfer the Combat BP alone.

Consolidation gives the parent combat Blueprint a separate movement action.
The original project and the Epic template are never consolidated or deleted.
"""
import unreal,json
from pathlib import Path
P=Path(unreal.Paths.project_dir());assert (P/'EMBER_DISPOSABLE_COPY').is_file(), 'Refuse consolidation in live project'
E=unreal.EditorAssetLibrary;D='/Game/Starbay/Ember_v04'
source=E.load_asset('/Game/Input/Actions/IA_Move')
target=E.duplicate_asset('/Game/Input/Actions/IA_Move',D+'/IA_EmberSprintMove');assert target
E.save_loaded_asset(target,False)
bp=E.load_asset(D+'/BP_EmberCombat')
assert E.consolidate_assets(target,[source])
unreal.BlueprintEditorLibrary.compile_blueprint(bp);assert E.save_loaded_asset(bp,False)
(P/'Saved/movement_isolation.json').write_text(json.dumps({'status':'saved','copy_back_only':['Content/Starbay/Ember_v04/BP_EmberCombat.uasset','Content/Starbay/Ember_v04/IA_EmberSprintMove.uasset']}),encoding='utf-8')
