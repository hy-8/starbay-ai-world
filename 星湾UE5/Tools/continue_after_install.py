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

from install_third_person import completed_install_registration

PROJECT = Path(__file__).resolve().parents[1]
SAVED = PROJECT / 'Saved'
STATUS = SAVED / 'continuation_status.json'
LOCK = SAVED / 'continue_after_install.lock'


def classify_lock_process(pid):
    """Use Windows CIM to identify the lock owner; never act on unknown identity."""
    if os.name != 'nt' or not isinstance(pid, int) or pid <= 0:
        return 'unknown'
    shell = shutil.which('powershell') or shutil.which('pwsh')
    if not shell:
        candidate = Path(os.environ.get('SystemRoot', 'C:/Windows')) / (
            'System32/WindowsPowerShell/v1.0/powershell.exe'
        )
        shell = str(candidate) if candidate.is_file() else None
    if not shell:
        return 'unknown'
    command = (
        "$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[Text.UTF8Encoding]::new($false); "
        f"$p=Get-CimInstance Win32_Process -Filter 'ProcessId={pid}'; "
        "if($null -eq $p){@{exists=$false}|ConvertTo-Json -Compress}"
        "else{@{exists=$true;commandLine=$p.CommandLine}|ConvertTo-Json -Compress}"
    )
    try:
        result = subprocess.run(
            [shell, '-NoProfile', '-NonInteractive', '-Command', command],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=20, check=True, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        process = json.loads(result.stdout.lstrip('\ufeff'))
        if process.get('exists') is False:
            return 'missing'
        command_line = process.get('commandLine')
        if process.get('exists') is not True or not isinstance(command_line, str) or not command_line:
            return 'unknown'

        # Windows' own parser handles quoted paths without guessing shell escaping.
        import ctypes
        from ctypes import wintypes
        shell32 = ctypes.WinDLL('shell32', use_last_error=True)
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        shell32.CommandLineToArgvW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
        shell32.CommandLineToArgvW.restype = ctypes.POINTER(wintypes.LPWSTR)
        kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        kernel32.LocalFree.restype = ctypes.c_void_p
        count = ctypes.c_int()
        arguments = shell32.CommandLineToArgvW(command_line, ctypes.byref(count))
        if not arguments:
            return 'unknown'
        try:
            args = [arguments[index] for index in range(count.value)]
        finally:
            kernel32.LocalFree(arguments)
        script = Path(__file__).resolve()
        for argument in args[1:]:
            path = Path(argument)
            if path.name.casefold() == script.name.casefold():
                if not path.is_absolute():
                    return 'unknown'
                if os.path.normcase(str(path.resolve())) == os.path.normcase(str(script)):
                    return 'same_script'
        # A wrapper or python -c invocation may contain the script in a larger argument.
        if script.name.casefold() in command_line.casefold():
            return 'unknown'
        return 'other_process'
    except (OSError, ValueError, subprocess.SubprocessError):
        return 'unknown'


def acquire_lock(path=LOCK, classifier=classify_lock_process):
    recovery = None
    if path.exists():
        previous = path.read_text(encoding='utf-8').strip()
        try:
            previous_pid = int(previous)
        except ValueError:
            raise RuntimeError('Existing continuation lock has unknown ownership; leaving it untouched')
        identity = classifier(previous_pid)
        if identity == 'same_script':
            raise RuntimeError(f'Continuation is already running with PID {previous_pid}')
        if identity not in ('missing', 'other_process'):
            raise RuntimeError(f'Cannot identify lock owner PID {previous_pid}; leaving the lock untouched')
        # Recheck content after querying CIM; do not move a lock another worker changed.
        if path.read_text(encoding='utf-8').strip() != previous:
            raise RuntimeError('Continuation lock changed during inspection; leaving it untouched')
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        backup = path.with_name(f'{path.name}.stale-{stamp}-{os.getpid()}.bak')
        path.rename(backup)
        recovery = {'previousProcessId': previous_pid, 'identity': identity, 'backup': str(backup)}
        print(json.dumps({'staleLockRecovered': recovery}), flush=True)
    # Exclusive creation prevents duplicate waiting jobs from racing into an import.
    with path.open('x', encoding='utf-8') as handle:
        handle.write(str(os.getpid()))
    return recovery


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine-root', required=True, type=Path)
    parser.add_argument('--timeout-minutes', type=float, default=120)
    args = parser.parse_args()
    if args.timeout_minutes <= 0:
        raise ValueError('Timeout must be positive')
    engine = args.engine_root.resolve(strict=True)
    scene_report = SAVED / 'scene_import_report.json'
    SAVED.mkdir(parents=True, exist_ok=True)
    recovery = acquire_lock(LOCK)
    started = time.monotonic()
    last_heartbeat = started
    state = {'processId': os.getpid(), 'engineRoot': str(engine),
             'oneShot': True, 'runtimeGameplayVerified': False, 'lockRecovery': recovery}

    def update(phase, **extra):
        nonlocal last_heartbeat
        now = datetime.now(timezone.utc).isoformat()
        state.update(phase=phase, updatedAtUtc=now, heartbeatAtUtc=now, **extra)
        pending = STATUS.with_suffix('.tmp')
        pending.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        pending.replace(STATUS)
        last_heartbeat = time.monotonic()
        print(json.dumps(state, ensure_ascii=False), flush=True)

    def wait_step():
        if time.monotonic() - started > args.timeout_minutes * 60:
            raise TimeoutError('Continuation timed out; Epic and the editor were left untouched')
        time.sleep(15)
        if time.monotonic() - last_heartbeat >= 60:
            update(state['phase'])

    try:
        if scene_report.exists():
            raise RuntimeError('An earlier scene import report exists; inspect it before continuing')
        update('waiting_for_epic_verification')
        while True:
            registration = completed_install_registration(engine)
            if registration is not None:
                state['installationRegistration'] = registration
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
        if LOCK.exists() and LOCK.read_text(encoding='utf-8').strip() == str(os.getpid()):
            LOCK.unlink()


if __name__ == '__main__':
    main()
