"""Copy the installed UE 5.6 Blueprint Third Person template without overwriting assets.

Run with ordinary Python after Epic finishes installing Templates and Feature Packs:
    python Tools/install_third_person.py --engine-root "D:/Program Files/Epic Games/UE_5.6"
This prepares content only; it does not run Unreal, select a GameMode, or test gameplay.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys


PROJECT = Path(__file__).resolve().parents[1]
REPORT = PROJECT / "Saved" / "template_import_report.json"
MAPPINGS = (
    ("Templates/TP_ThirdPersonBP/Content", "Content"),
    ("Templates/TemplateResources/High/Characters/Content", "Content/Characters"),
    ("Templates/TemplateResources/High/Input/Content", "Content/Input"),
    ("Templates/TemplateResources/High/LevelPrototyping/Content", "Content/LevelPrototyping"),
)
INPUT_SOURCE = "Templates/TP_ThirdPersonBP/Config/DefaultInput.ini"
REQUIRED_CONTENT = (
    "Content/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.uasset",
    "Content/ThirdPerson/Blueprints/BP_ThirdPersonGameMode.uasset",
    "Content/ThirdPerson/Blueprints/BP_ThirdPersonPlayerController.uasset",
    "Content/Characters/Mannequins/Meshes/SKM_Quinn_Simple.uasset",
    "Content/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed.uasset",
    "Content/Input/IMC_Default.uasset",
    "Content/Input/IMC_MouseLook.uasset",
    "Content/Input/Actions/IA_Move.uasset",
    "Content/Input/Actions/IA_Look.uasset",
    "Content/Input/Actions/IA_MouseLook.uasset",
    "Content/Input/Actions/IA_Jump.uasset",
    "Content/Input/Touch/BPI_TouchInterface.uasset",
    "Content/Input/Touch/UI_TouchSimple.uasset",
)


def normalized(path):
    return os.path.normcase(str(Path(path).resolve()))


def completed_install_registration(engine, program_data=None):
    """Return a completed Epic registration, including the newer EOS item format."""
    data_root = Path(program_data or os.environ.get("ProgramData", "C:/ProgramData"))

    def read_record(path):
        try:
            record = json.loads(path.read_text(encoding="utf-8-sig"))
            return record if isinstance(record, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
            # Epic can replace these files while updating its installation database.
            return {}

    def same_install(entry):
        return (
            isinstance(entry, dict)
            and entry.get("AppName") == "UE_5.6"
            and isinstance(entry.get("InstallLocation"), str)
            and bool(entry["InstallLocation"])
            and normalized(entry["InstallLocation"]) == normalized(engine)
        )

    legacy = data_root / "Epic/UnrealEngineLauncher/LauncherInstalled.dat"
    entries = read_record(legacy).get("InstallationList", [])
    if isinstance(entries, list) and any(same_install(entry) for entry in entries):
        return {"format": "LauncherInstalled.dat", "path": str(legacy)}

    items_dir = data_root / "Epic/EpicGamesLauncher/Data/Manifests"
    for item in sorted(items_dir.glob("*.item")):
        entry = read_record(item)
        # Missing, null, numeric zero and true are not proof that installation finished.
        if same_install(entry) and entry.get("bIsIncompleteInstall") is False:
            return {"format": "Epic item manifest", "path": str(item)}
    return None


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_destination(path):
    # Resolve existing parents too, so a junction cannot redirect the copy elsewhere.
    path.resolve().relative_to(PROJECT)
    if path.exists() or path.is_symlink():
        raise RuntimeError(f"Destination already exists; refusing to overwrite: {path}")
    for parent in path.parents:
        if parent == PROJECT:
            break
        if parent.exists() and not parent.is_dir():
            raise RuntimeError(f"Destination parent is not a directory: {parent}")


def preflight(engine):
    if completed_install_registration(engine) is None:
        raise RuntimeError(
            "Epic has not registered UE_5.6 as installed at this engine root. "
            "Wait for installation to finish; no files have been copied."
        )

    version = json.loads((engine / "Engine/Build/Build.version").read_text(encoding="utf-8-sig"))
    if (version.get("MajorVersion"), version.get("MinorVersion")) != (5, 6):
        raise RuntimeError("This importer supports only the verified UE 5.6 template layout.")

    pairs = []
    for source_relative, target_relative in MAPPINGS:
        source_dir = engine / source_relative
        if not source_dir.is_dir():
            raise RuntimeError(f"Missing template directory: {source_dir}")
        source_files = []
        for source in sorted(source_dir.rglob("*")):
            if source.is_symlink():
                raise RuntimeError(f"Unexpected link in template content: {source}")
            source.resolve().relative_to(engine)
            if source.is_file():
                source_files.append(source)
        if not source_files:
            raise RuntimeError(f"Template directory is empty: {source_dir}")
        pairs.extend(
            (source, PROJECT / target_relative / source.relative_to(source_dir))
            for source in source_files
        )
    pairs.append((engine / INPUT_SOURCE, PROJECT / "Config/DefaultInput.ini"))

    # All sources and all destination conflicts are checked before creating anything.
    records = []
    targets = set()
    for source, destination in pairs:
        source.resolve().relative_to(engine)
        if not source.is_file() or source.is_symlink() or source.stat().st_size == 0:
            raise RuntimeError(f"Missing, empty, or linked source file: {source}")
        target_key = normalized(destination)
        if target_key in targets:
            raise RuntimeError(f"Two source files would write the same destination: {destination}")
        targets.add(target_key)
        check_destination(destination)
        before = source.stat()
        checksum = sha256(source)
        after = source.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise RuntimeError(f"Source changed during inspection; retry after installation: {source}")
        records.append({
            "source": source.relative_to(engine).as_posix(),
            "destination": destination.relative_to(PROJECT).as_posix(),
            "bytes": after.st_size,
            "sha256": checksum,
        })

    available = {record["destination"] for record in records}
    missing = set(REQUIRED_CONTENT) - available
    if missing:
        raise RuntimeError(f"Required Third Person dependencies are missing: {sorted(missing)}")
    input_text = (engine / INPUT_SOURCE).read_text(encoding="utf-8-sig")
    for setting in (
        "DefaultPlayerInputClass=/Script/EnhancedInput.EnhancedPlayerInput",
        "DefaultInputComponentClass=/Script/EnhancedInput.EnhancedInputComponent",
    ):
        if setting not in input_text:
            raise RuntimeError(f"Unexpected template input configuration; missing: {setting}")
    check_destination(REPORT)
    return version, sorted(records, key=lambda record: record["destination"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine-root", required=True, type=Path)
    args = parser.parse_args()
    engine = args.engine_root.resolve(strict=True)
    version, records = preflight(engine)

    report = {
        "status": "copying",
        "createdAtUtc": datetime.now(timezone.utc).isoformat(),
        "engineVersion": version,
        "engineRoot": str(engine),
        "scope": "Official Blueprint Third Person content and DefaultInput.ini only",
        "unrealRuntimeTested": False,
        "plannedFileCount": len(records),
        "verifiedFileCount": 0,
        "verifiedBytes": 0,
        "files": [],
    }
    # The exclusive report handle also prevents two copies of this script racing.
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("x", encoding="utf-8") as report_stream:
        try:
            for record in records:
                source = engine / record["source"]
                destination = PROJECT / record["destination"]
                report["currentDestination"] = record["destination"]
                check_destination(destination)
                destination.parent.mkdir(parents=True, exist_ok=True)
                # Exclusive creation protects edits even if a file appears after preflight.
                with source.open("rb") as source_stream, destination.open("xb") as output:
                    for chunk in iter(lambda: source_stream.read(1024 * 1024), b""):
                        output.write(chunk)
                if destination.stat().st_size != record["bytes"] or sha256(destination) != record["sha256"]:
                    raise RuntimeError(f"Copied file checksum mismatch: {destination}")
                report["files"].append(record)
                report["verifiedFileCount"] += 1
                report["verifiedBytes"] += record["bytes"]
            report.pop("currentDestination", None)
            report["status"] = "content_copied"
            report["checksumSummarySha256"] = hashlib.sha256(
                json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
        except Exception as error:
            report["status"] = "copy_failed"
            report["error"] = str(error)
            report["recovery"] = (
                "No existing files were overwritten. Newly copied files remain for inspection; "
                "the importer will refuse to overwrite them on retry."
            )
            raise
        finally:
            json.dump(report, report_stream, ensure_ascii=False, indent=2)
            report_stream.write("\n")

    print(f"STARBAY_THIRD_PERSON_CONTENT_COPIED files={len(records)} report={REPORT}")
    print("Content prepared only. Unreal loading, movement, animation, and packaging are not yet verified.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        print(f"THIRD_PERSON_IMPORT_REFUSED_OR_FAILED: {error}", file=sys.stderr)
        sys.exit(1)
