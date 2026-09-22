"""One-shot continuation of the current Epic install; not a recurring task.

Waits for Epic to register this UE 5.6 installation, copies the official template
once, and opens the editor for the first scene import. Never retries a mutation.
Local progress is written to Saved/continuation_status.json. Successful import
does not establish that gameplay, collision, or a packaged build was tested.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

PROJECT = Path(__file__).resolve().parents[1]
SAVED = PROJECT / 'Saved'
STATUS = SAVED / 'continuation_status.json'
LOCK = SAVED / 'continue_after_install.lock'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine-root', required=True, type=Path)
    parser.add_argument('--timeout-minutes', type=float, default=120)
    args = parser.parse_args()
    if args.timeout_minutes <= 0:
        raise ValueError('Timeout must be positive')
    engine = args.engine_root.resolve(strict=True)
    manifest = Path(os.environ.get('ProgramData', 'C:/ProgramData')) / 'Epic/UnrealEngineLauncher/LauncherInstalled.dat'
    scene_report = SAVED / 'scene_import_report.json'
    if scene_report.exists():
        raise RuntimeError('An earlier scene import report exists; inspect it before continuing')
    SAVED.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents duplicate waiting jobs from racing into an import.
    with LOCK.open('x', encoding='utf-8') as handle:
        handle.write(str(os.getpid()))
    started = time.monotonic()
    state = {'processId': os.getpid(), 'engineRoot': str(engine),
             'oneShot': True, 'runtimeGameplayVerified': False}

    def update(phase, **extra):
        state.update(phase=phase, updatedAtUtc=datetime.now(timezone.utc).isoformat(), **extra)
        pending = STATUS.with_suffix('.tmp')
        pending.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        pending.replace(STATUS)
        print(json.dumps(state, ensure_ascii=False), flush=True)

    def wait_step():
        if time.monotonic() - started > args.timeout_minutes * 60:
            raise TimeoutError('Continuation timed out; Epic and the editor were left untouched')
        time.sleep(15)

    try:
        update('waiting_for_epic_verification')
        while True:
            try:
                entries = json.loads(manifest.read_text(encoding='utf-8-sig')).get('InstallationList', [])
            except (FileNotFoundError, json.JSONDecodeError):
                entries = []
            if any(e.get('AppName') == 'UE_5.6' and e.get('InstallLocation')
                   and Path(e['InstallLocation']).resolve() == engine for e in entries):
                break
            wait_step()
        # Each existing tool performs its own complete preflight. A failure stops here.
        update('copying_official_template')
        subprocess.run([sys.executable, str(PROJECT / 'Tools/install_third_person.py'),
                        '--engine-root', str(engine)], check=True)
        update('opening_editor_for_first_import')
        shell = shutil.which('pwsh') or shutil.which('powershell')
        if not shell:
            raise RuntimeError('PowerShell was not found')
        subprocess.run([shell, '-NoProfile', '-File', str(PROJECT / 'Tools/Open-Starbay.ps1'),
                        '-EngineRoot', str(engine), '-ImportScene'], check=True)
        update('waiting_for_scene_import_report')
        while True:
            if scene_report.exists():
                try:
                    result = json.loads(scene_report.read_text(encoding='utf-8'))
                except json.JSONDecodeError:
                    wait_step()
                    continue
                if result.get('status') == 'scene_created':
                    update('scene_created_awaiting_manual_gameplay_validation',
                           importReport=str(scene_report), calibration=result.get('calibration'))
                    return
                if result.get('status') == 'failed':
                    raise RuntimeError('Scene import stopped: ' + result.get('error', 'see import report'))
            wait_step()
    except Exception as error:
        update('stopped_with_error', error=str(error))
        raise
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
