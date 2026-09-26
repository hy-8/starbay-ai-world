"""Read-only editor checks for the CURRENT Starbay map; never loads/saves a map.

Run with Unreal Editor's Python plugin after bootstrap_scene.py has completed.
Writes only Saved/scene_validation_report.json. Does not start PIE, move actors,
update delivery_status, or establish that a character can actually walk a route.

UE 5.6 API references (checked before authoring):
https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/SystemLibrary?application_version=5.6
  line_trace_single_by_profile(...) -> HitResult or None, NOT (bool, HitResult).
https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/HitResult?application_version=5.6
https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/StructBase?application_version=5.6
  HitResult is a StructBase; to_tuple() breaks a struct into its properties.
https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/UnrealEditorSubsystem?application_version=5.6
https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EditorActorSubsystem?application_version=5.6
"""

import datetime
import json
import math
from pathlib import Path

import unreal

# Keep an editor launched with -ExecutePythonScript available for visual checks.
# This changes only script-runner lifetime, not the map or its assets.
unreal.EditorPythonScripting.set_keep_python_script_alive(True)


PROJECT = Path(unreal.Paths.project_dir()).resolve()
REPORT_PATH = PROJECT / 'Saved' / 'scene_validation_report.json'
GEOMETRY_LABELS = ('SM_District', 'SM_CourtyardDetails')
TEMPLATE_MODE = '/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode'

# Field sequence published in the UE 5.6 HitResult constructor. Before using it
# for traces, verify the layout against a synthetic in-memory HitResult below.
HIT_FIELDS = (
    'blocking_hit', 'initial_overlap', 'time', 'distance', 'location',
    'impact_point', 'normal', 'impact_normal', 'phys_mat', 'hit_actor',
    'hit_component', 'hit_bone_name', 'bone_name', 'hit_item', 'element_index',
    'face_index', 'trace_start', 'trace_end',
)

# Design/首次步行验收.md: game (x,z) meters and source FBX ground Z centimeters.
# These heights are comparison references, not character-center coordinates.
POINTS = {
    'S': (4, 22, 11.9), 'SE': (0, 19, 11.9),
    'A1': (0, -15, 11.0), 'A2': (26, -15, 11.8),
    'mall': (26, -16, 11.8), 'foyer': (26, -26, 11.9),
    'lobby': (35, -35, 11.9), 'atrium': (49, -45, 12.0),
    'books': (73, -45, 12.0), 'SW': (-39, 19, 11.9),
    'W1': (-39, 23, 11.0), 'courier': (-65, 23, 11.0),
    'market': (-105, 25, 11.9), 'park': (9, 40, 11.9),
    'G1': (17, 22, 11.9), 'bikes': (62, 21, 11.8),
    'C1': (58, 21, 11.0), 'C2': (58, 34, 11.9),
    'C3': (62, 34, 11.9), 'courtyard': (62, 43, 15.5),
    'P1': (68, 41, 15.5), 'P2': (73, 46, 15.5),
    'P3': (68, 50, 15.5), 'P4': (63, 46, 15.5),
    'bench_south': (17, 28, None),
}
GROUND_SAMPLES = (
    'S', 'mall', 'foyer', 'lobby', 'atrium', 'books', 'market',
    'park', 'bikes', 'C2', 'C3', 'courtyard', 'P2',
)
PASSAGE_SAMPLES = (
    ('S', 'SE'), ('SE', 'A1'), ('A1', 'A2'), ('mall', 'foyer'),
    ('foyer', 'lobby'), ('atrium', 'books'), ('SW', 'W1'),
    ('W1', 'courier'), ('courier', 'market'), ('S', 'park'),
    ('G1', 'bikes'), ('C1', 'C2'), ('C2', 'C3'), ('C3', 'courtyard'),
    ('courtyard', 'P1'), ('P1', 'P2'), ('P2', 'P3'),
    ('P3', 'P4'), ('P4', 'courtyard'),
)
# Positive controls from documented source-geometry obstructions. They help
# distinguish actual collision queries from a world that returns no hits at all.
BLOCKED_CONTROLS = (('bikes', 'courtyard'), ('G1', 'bench_south'))

report = {
    'schema': 1,
    'status': 'in_progress',
    'createdAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'engine': unreal.SystemLibrary.get_engine_version(),
    'scope': 'Current editor-world structure and sparse Pawn-profile complex line traces',
    'runtimeGameplayVerified': False,
    'pieTested': False,
    'capsuleMovementTested': False,
    'mapChangedOrSavedByScript': False,
    'deliveryStatusUpdated': False,
    'checks': [],
    'issues': [],
    'warnings': [],
    'groundSamples': [],
    'passageSamples': [],
    'blockedControls': [],
    'traceCount': 0,
    'limitations': [
        'Editor-world line traces are not PIE, character capsule sweeps, stepping, navigation or camera tests.',
        'Passages use only their centerline at world Z 45, 95 and 155 cm, in the listed direction.',
        'Ground rays start at Z 40 cm and can miss objects above that height or initial overlaps.',
        'Sparse samples do not prove the entire route, reverse direction or character clearance.',
        'Ground reference heights come from source FBX and require correct UE import calibration.',
        'Pawn collision profile queries do not establish CharacterMovement behavior or collision cooking correctness.',
        'Existing unsaved editor changes, if present, are inspected in memory and are never saved by this script.',
    ],
}


def xyz(value):
    return [float(value.x), float(value.y), float(value.z)]


def angle_delta(a, b):
    return abs((float(a) - float(b) + 180.0) % 360.0 - 180.0)


def check(name, passed, detail):
    report['checks'].append({'name': name, 'passed': bool(passed), 'detail': detail})
    if not passed:
        report['issues'].append(name)


def point(name, height_cm):
    game_x, game_z, _ = POINTS[name]
    return unreal.Vector(-game_z * 100.0, game_x * 100.0, height_cm)


def hit_fields(hit):
    values = hit.to_tuple()
    if len(values) != len(HIT_FIELDS):
        raise RuntimeError('Unsupported HitResult tuple layout: ' + str(len(values)))
    return dict(zip(HIT_FIELDS, values))


def verify_hit_reader():
    probe = unreal.HitResult(
        blocking_hit=True, initial_overlap=True, time=0.25, distance=123.0,
        location=unreal.Vector(1, 2, 3), impact_point=unreal.Vector(11, 22, 33),
        normal=unreal.Vector(0, 1, 0), impact_normal=unreal.Vector(0, 0, 1),
        trace_start=unreal.Vector(4, 5, 6), trace_end=unreal.Vector(7, 8, 9),
    )
    data = hit_fields(probe)
    valid = (
        data['blocking_hit'] is True and data['initial_overlap'] is True
        and abs(data['time'] - 0.25) < 1e-6
        and abs(data['distance'] - 123.0) < 1e-6
        and xyz(data['location']) == [1.0, 2.0, 3.0]
        and xyz(data['impact_point']) == [11.0, 22.0, 33.0]
        and xyz(data['normal']) == [0.0, 1.0, 0.0]
        and xyz(data['impact_normal']) == [0.0, 0.0, 1.0]
        and xyz(data['trace_start']) == [4.0, 5.0, 6.0]
        and xyz(data['trace_end']) == [7.0, 8.0, 9.0]
    )
    if not valid:
        raise RuntimeError('HitResult schema probe failed; refusing to misread collision results')
    report['hitResultSchemaProbePassed'] = True


def trace(world, start, end, ignored):
    # Official 5.6 wrapper returns the out HitResult, or None when no blocking hit.
    hit = unreal.SystemLibrary.line_trace_single_by_profile(
        world_context_object=world, start=start, end=end, profile_name='Pawn',
        trace_complex=True, actors_to_ignore=ignored,
        draw_debug_type=unreal.DrawDebugTrace.NONE, ignore_self=False,
    )
    report['traceCount'] += 1
    result = {'startCm': xyz(start), 'endCm': xyz(end), 'blockingHit': False}
    if hit is None:
        return result
    if not isinstance(hit, unreal.HitResult):
        raise RuntimeError('Unexpected trace return type: ' + str(type(hit)))
    data = hit_fields(hit)
    result.update({
        'blockingHit': bool(data['blocking_hit']),
        'initialOverlap': bool(data['initial_overlap']),
        'impactPointCm': xyz(data['impact_point']),
        'impactNormal': xyz(data['impact_normal']),
        'distanceCm': float(data['distance']),
        'actor': data['hit_actor'].get_path_name() if data['hit_actor'] else None,
        'component': data['hit_component'].get_path_name() if data['hit_component'] else None,
    })
    return result


def inspect_geometry(all_actors, calibration):
    result = []
    for label in GEOMETRY_LABELS:
        matches = [a for a in all_actors if a.get_actor_label() == label]
        check(label + ':uniqueActor', len(matches) == 1, {'count': len(matches)})
        if len(matches) != 1:
            continue
        actor = matches[0]
        check(label + ':staticMeshActor', isinstance(actor, unreal.StaticMeshActor), actor.get_class().get_name())
        if not isinstance(actor, unreal.StaticMeshActor):
            continue
        component = actor.static_mesh_component
        mesh = component.get_editor_property('static_mesh')
        rotation = actor.get_actor_rotation()
        scale = xyz(actor.get_actor_scale3d())
        location = xyz(actor.get_actor_location())
        entry = {
            'label': label, 'actor': actor.get_path_name(),
            'mesh': mesh.get_path_name() if mesh else None,
            'locationCm': location, 'scale': scale,
            'rotationDegrees': {'pitch': rotation.pitch, 'yaw': rotation.yaw, 'roll': rotation.roll},
            'collisionProfile': str(component.get_collision_profile_name()),
            'collisionEnabled': str(component.get_collision_enabled()),
        }
        check(label + ':meshBound', mesh is not None, entry['mesh'])
        check(label + ':horizontal', angle_delta(rotation.pitch, 0) < 0.01 and angle_delta(rotation.roll, 0) < 0.01, entry['rotationDegrees'])
        check(label + ':worldOrigin', max(abs(v) for v in location) < 0.1, location)
        check(label + ':finiteNonzeroScale', all(math.isfinite(v) and abs(v) > 1e-6 for v in scale), scale)
        query_modes = (unreal.CollisionEnabled.QUERY_ONLY, unreal.CollisionEnabled.QUERY_AND_PHYSICS, unreal.CollisionEnabled.QUERY_AND_PROBE)
        check(label + ':queryCollisionEnabled', component.get_collision_enabled() in query_modes, entry['collisionEnabled'])
        if mesh:
            body = mesh.get_editor_property('body_setup')
            flag = body.get_editor_property('collision_trace_flag') if body else None
            entry['collisionTraceFlag'] = str(flag)
            check(label + ':complexAsSimple', flag == unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE, entry['collisionTraceFlag'])
        if calibration:
            expected = [calibration['scale'], calibration['scale'] * calibration['mirrorY'], calibration['scale']]
            check(label + ':calibratedScale', all(abs(a-b) < 1e-5 * max(1, abs(b)) for a, b in zip(scale, expected)), {'actual': scale, 'expected': expected})
            check(label + ':calibratedYaw', angle_delta(rotation.yaw, calibration['yawDegrees']) < 0.01, {'actual': rotation.yaw, 'expected': calibration['yawDegrees']})
        result.append(entry)
    report['geometry'] = result


def main():
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    if not world:
        raise RuntimeError('No editor world; open the generated Starbay map first')
    report['world'] = world.get_path_name()
    if not report['world'].startswith('/Game/Starbay/Maps/'):
        raise RuntimeError('Current world is not a Starbay map; no map was switched: ' + report['world'])
    dirty = unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    report['dirtyMapsAtStart'] = [p.get_name() for p in dirty]
    if dirty:
        report['warnings'].append('Inspecting the current in-memory editor state, including unsaved map changes.')
    import_path = PROJECT / 'Saved' / 'scene_import_report.json'
    calibration = None
    if import_path.is_file():
        imported = json.loads(import_path.read_text(encoding='utf-8'))
        report['historicalImportRunnerStatus'] = imported.get('status')
        if imported.get('status') != 'scene_created':
            report['warnings'].append('Historical import runner did not finish cleanly: ' + str(imported.get('error', imported.get('status'))))
        # Calibration was completed before the initial runner's keep-alive error.
        # Preserve that historical failure; independently check the loaded map
        # transforms and collision against the completed calibration below.
        if imported.get('calibration', {}).get('passed') is True:
            calibration = imported['calibration']
    check('importCalibrationPassed', calibration is not None, calibration)
    all_actors = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    inspect_geometry(all_actors, calibration)

    starts = [a for a in all_actors if isinstance(a, unreal.PlayerStart)]
    named_starts = [a for a in starts if a.get_actor_label() == 'Player_Start']
    check('Player_Start:unique', len(named_starts) == 1, {'matching': len(named_starts), 'allPlayerStarts': len(starts)})
    if len(starts) > 1:
        report['warnings'].append('Multiple PlayerStart actors may affect the actual runtime spawn choice.')
    if len(named_starts) == 1:
        start = named_starts[0]
        location = xyz(start.get_actor_location())
        rotation = start.get_actor_rotation()
        report['playerStart'] = {'locationCm': location, 'yawDegrees': rotation.yaw}
        check('Player_Start:documentedLocation', max(abs(a-b) for a, b in zip(location, [-2200, 400, 130])) < 1.0, location)
        check('Player_Start:documentedFacing', angle_delta(rotation.yaw, 0) < 0.01, rotation.yaw)

    assets = unreal.EditorAssetLibrary
    template_exists = assets.does_asset_exist(TEMPLATE_MODE)
    # Loading a Blueprint class is read-only; nothing here creates or saves assets.
    template_class = assets.load_blueprint_class(TEMPLATE_MODE) if template_exists else None
    actual_mode = world.get_world_settings().get_editor_property('default_game_mode')
    configured = template_class is not None and actual_mode == template_class
    report['gameMode'] = {
        'templateAsset': TEMPLATE_MODE, 'templateExists': template_exists,
        'templateClassLoaded': template_class is not None,
        'mapOverrideClass': actual_mode.get_path_name() if actual_mode else None,
        'officialThirdPersonConfigured': configured,
        'note': 'Checks the map override only; no default pawn is spawned or controlled.',
    }
    if not configured:
        report['warnings'].append('Official Third Person GameMode is absent or not assigned; gameplay acceptance remains pending.')

    verify_hit_reader()
    for name in GROUND_SAMPLES:
        sample = trace(world, point(name, 40), point(name, -200), starts)
        expected = POINTS[name][2]
        sample.update({'point': name, 'sourceFbxGroundZCm': expected})
        passed = sample['blockingHit'] and not sample.get('initialOverlap', False)
        if sample['blockingHit']:
            sample['groundHeightErrorCm'] = abs(sample['impactPointCm'][2] - expected)
            passed = passed and sample['groundHeightErrorCm'] <= 2.0 and sample['impactNormal'][2] > 0.5
        sample['samplePassed'] = passed
        report['groundSamples'].append(sample)
        check('ground:' + name, passed, {'expectedZCm': expected, 'toleranceCm': 2.0})

    if len(named_starts) == 1:
        location = named_starts[0].get_actor_location()
        report['actualPlayerStartDownRay'] = trace(world, location, unreal.Vector(location.x, location.y, -200), starts)
        check('Player_Start:groundBelow', report['actualPlayerStartDownRay']['blockingHit'], report['actualPlayerStartDownRay'])

    for routes, target, expect_blocked in (
        (PASSAGE_SAMPLES, 'passageSamples', False),
        (BLOCKED_CONTROLS, 'blockedControls', True),
    ):
        for origin, destination in routes:
            rays = [trace(world, point(origin, height), point(destination, height), starts) for height in (45, 95, 155)]
            blocked = any(ray['blockingHit'] for ray in rays)
            passed = blocked if expect_blocked else not blocked
            entry = {'from': origin, 'to': destination, 'expectedBlocked': expect_blocked, 'samplePassed': passed, 'rays': rays}
            report[target].append(entry)
            check(target + ':' + origin + '->' + destination, passed, {'blockingRayCount': sum(r['blockingHit'] for r in rays)})

    report['sampleChecksPassed'] = not report['issues']
    report['thirdPersonConfigurationPassed'] = configured
    report['status'] = 'checks_completed'


try:
    main()
except Exception as exc:
    report['status'] = 'failed'
    report['error'] = str(exc)
    raise
finally:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    unreal.log('STARBAY_SCENE_VALIDATION ' + json.dumps({
        'status': report['status'], 'issues': len(report['issues']),
        'traces': report['traceCount'], 'report': str(REPORT_PATH),
        'runtimeGameplayVerified': False,
    }, ensure_ascii=False))
