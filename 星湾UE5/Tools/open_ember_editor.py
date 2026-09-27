"""Open the isolated Ember arena and a bounded local development job runner.

Only used in the editor; never cooked into or needed by the packaged game.
Jobs are explicit local Python scripts placed in Saved/EmberJobs during authoring.
"""
import unreal,time,json,traceback,builtins
from pathlib import Path
P=Path(unreal.Paths.project_dir());D='/Game/Starbay/Ember_v04';J=P/'Saved/EmberJobs';J.mkdir(exist_ok=True)
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(D+'/L_EmberArena')
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([unreal.load_asset(D+'/BP_EmberCharacter')])
started=time.monotonic();last=[0];busy=[False]
def process_jobs(dt):
    if busy[0]:return
    if time.monotonic()-last[0]<.5:return
    last[0]=time.monotonic()
    if time.monotonic()-started>10800:
        unreal.unregister_slate_post_tick_callback(builtins._ember_jobs);return
    for path in sorted(J.glob('*.py')):
        if not path.exists():continue
        running=path.with_suffix('.running');path.rename(running)
        result={'job':path.name}
        busy[0]=True
        try:
            scope={'__file__':str(path),'__name__':'__main__'};exec(compile(running.read_text(encoding='utf-8'),str(path),'exec'),scope)
            result['status']='executed'
        except Exception:result['status']='failed';result['error']=traceback.format_exc()
        finally:busy[0]=False
        running.rename(path.with_suffix('.done'));path.with_suffix('.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
builtins._ember_jobs=unreal.register_slate_post_tick_callback(process_jobs)
(P/'Saved/ember_editor_ready.json').write_text(json.dumps({'ready':True,'namespace':D}),encoding='utf-8')
