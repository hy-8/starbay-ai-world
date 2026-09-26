"""Bounded native CharacterMovement smoke test in the interactive UE 5.6 editor.

Open L_Starbay with no PIE session, then execute this file in the editor's Python
console. It returns immediately; Slate callbacks run the test and end its PIE.
Do not press game controls during the test. No map is loaded, edited or saved.
For -ExecutePythonScript in an interactive editor, the script temporarily enables
EditorPythonScripting keep-alive and restores it after confirmed cleanup. Do not
use a Python commandlet or -NullRHI: this test requires an active level viewport.

Verified against installed UE 5.6 source (Engine-relative paths):
  Source/Editor/LevelEditor/{Public/LevelEditorSubsystem.h,
                            Private/LevelEditorSubsystem.cpp}
    EditorRequestBeginPlay, EditorRequestEndPlay, IsInPlayInEditor.
  Source/Editor/UnrealEd/Private/Subsystems/UnrealEditorSubsystem.cpp:
    GetGameWorld returns the PIE world, not the editor world.
  Plugins/Editor/EditorScriptingUtilities/.../EditorLevelLibrary.{h,cpp}:
    GetPIEWorlds(bool) enumerates only EWorldType::PIE contexts.
  Plugins/Experimental/PythonScriptPlugin/.../Private/PySlate.cpp:
    register_slate_post_tick_callback / unregister_slate_post_tick_callback.
  .../Private/EditorUtilities/EditorPythonScriptingLibrary.h:
    ScriptName="EditorPythonScripting", Get/SetKeepPythonScriptAlive.
  Source/Runtime/Engine/Classes/{Kismet/GameplayStatics.h,
    GameFramework/{Actor,Character,Pawn,NavMovementComponent}.h}:
    GetPlayerCharacter, GetWorldDeltaSeconds, GetTimeSeconds, GetComponentByClass,
    GetActorLocation, GetVelocity, AddMovementInput, Jump, StopJumping,
    IsMovingOnGround, IsFalling. All used methods have reflected UFUNCTIONs.

This tests a short clear path near PlayerStart, not the whole map, real keyboard
bindings, visual animation quality, AI, GPU performance or a packaged build.
Timeouts are observed on Slate ticks: a blocked editor/OS cannot be interrupted
by Python. RequestEndPlayMap cannot cancel a not-yet-created PlayWorld; that
case is reported explicitly with manual recovery instructions.
"""
import builtins
import json
import math
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(__file__).resolve().parents[1]
REPORT = PROJECT / "Saved" / "native_play_smoke.json"
EXPECTED_MAP = "/Game/Starbay/Maps/L_Starbay.L_Starbay"
EXPECTED_CHARACTER = "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.BP_ThirdPersonCharacter_C"
EXPECTED_SPAWN = (-2200.0, 400.0, 130.0)
# Toward the audited first waypoint (-1900,0), staying on the same pavement.
DIRECTION = (0.6, -0.8, 0.0)
WALL_LIMIT = 45.0
CLEANUP_LIMIT = 5.0
STARTUP_LIMIT = 20.0
MOVE_GAME_SECONDS = 1.6
INPUT_SCALE = 0.4
SENTINEL = "_starbay_native_play_smoke"


def xyz(value):
    return [float(value.x), float(value.y), float(value.z)]


def horizontal_distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def valid(obj):
    return obj is not None and unreal.SystemLibrary.is_valid(obj)


class NativePlaySmoke:
    def __init__(self):
        self.active = False
        self.handle = None
        self.begin_requested = False
        self.owned_world_path = None
        self.world = self.character = self.movement = None
        self.phase = "preflight"
        self.start_wall = time.monotonic()
        self.phase_wall = self.start_wall
        self.phase_game = None
        self.last_game_time = None
        self.grounded_since = None
        self.move_start = None
        self.jump_start = None
        self.jump_released = False
        self.max_jump_rise = 0.0
        self.saw_airborne = False
        self.saw_upward_velocity = False
        self.move_input_frames = 0
        self.move_velocity_frames = 0
        self.stop_requested = False
        self.cleanup_started = None
        self.keep_alive_before = None
        self.result = {
            "schema": 1,
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "status": "preflight",
            "scope": "native PIE CharacterMovement smoke only; not full-map acceptance",
            "movement_method": "add_movement_input; no actor relocation/teleport",
            "jump_method": "Character.jump and Character.stop_jumping",
            "limits_seconds": {"wall": WALL_LIMIT, "cleanup": CLEANUP_LIMIT,
                               "startup": STARTUP_LIMIT},
            "checks": {"spawn": False, "native_movement": False,
                       "jump_takeoff": False, "jump_landing": False},
            "frames": [], "events": [], "cleanup": {},
            "limitations": [
                "Slate and game delta samples are editor timing, not GPU timings or packaged-game FPS.",
                "A frozen editor cannot be interrupted until another Slate callback runs.",
                "No keyboard mapping, visual gait, entire route, NPC, AI or packaged-build validation.",
            ],
            "manual_fallback": [
                "Open the saved L_Starbay map in the interactive UE editor and make its viewport active.",
                "Set the level GameMode to the official BP_ThirdPersonGameMode if it is missing, then save manually.",
                "With no existing play session, press Play; verify the third-person character spawns on pavement.",
                "Walk a short distance, release movement, press Space, and verify takeoff and landing.",
                "Press the editor Stop button (or Escape while PIE has focus); do not Keep Simulation Changes.",
                "Record manual observations separately; they do not change this automated report to passed.",
            ],
        }

    def write_report(self):
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        temporary = REPORT.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(self.result, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(REPORT)

    def event(self, name, **details):
        self.result["events"].append({"wall_seconds": round(time.monotonic() - self.start_wall, 4),
                                      "event": name, **details})

    def require(self, obj, names):
        missing = [name for name in names if not callable(getattr(obj, name, None))]
        if missing:
            raise RuntimeError("Required reflected UE API unavailable: " + ", ".join(missing))

    def start(self):
        previous = getattr(builtins, SENTINEL, None)
        if previous is not None and getattr(previous, "active", False):
            # Preserve the running test and its report instead of creating a second owner.
            unreal.log_warning("Starbay smoke already running; duplicate request refused.")
            return
        try:
            self.require(unreal, ["get_editor_subsystem", "register_slate_post_tick_callback",
                                  "unregister_slate_post_tick_callback"])
            self.level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
            self.editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
            self.require(self.level, ["is_in_play_in_editor", "editor_request_begin_play",
                                      "editor_request_end_play", "get_viewport_config_keys"])
            self.require(self.editor, ["get_game_world", "get_editor_world"])
            self.require(unreal.EditorLevelLibrary, ["get_pie_worlds"])
            self.require(unreal.GameplayStatics, ["get_player_character", "get_time_seconds",
                                                  "get_world_delta_seconds"])
            self.require(unreal.EditorPythonScripting, ["get_keep_python_script_alive",
                                                        "set_keep_python_script_alive"])
            if (self.level.is_in_play_in_editor() or self.editor.get_game_world() is not None
                    or len(unreal.EditorLevelLibrary.get_pie_worlds(True))):
                raise RuntimeError("Existing PIE/SIE session detected; it was not modified or stopped.")
            editor_world = self.editor.get_editor_world()
            if not valid(editor_world) or editor_world.get_path_name() != EXPECTED_MAP:
                raise RuntimeError("Open the saved Starbay map before testing; this script never loads a map.")
            if len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()):
                raise RuntimeError("Unsaved map changes detected; save or resolve them manually before testing.")
            if not len(self.level.get_viewport_config_keys()):
                raise RuntimeError("No interactive level viewport; PIE cannot be started by this API.")
            self.result["editor_world"] = editor_world.get_path_name()
            self.result["engine_version"] = unreal.SystemLibrary.get_engine_version()
            self.keep_alive_before = bool(unreal.EditorPythonScripting.get_keep_python_script_alive())
            unreal.EditorPythonScripting.set_keep_python_script_alive(True)
            self.phase = "await_world"
            self.active = True
            self.result["status"] = "running"
            setattr(builtins, SENTINEL, self)
            self.handle = unreal.register_slate_post_tick_callback(self.tick)
            self.write_report()
            # Recheck immediately before the only start mutation.
            if self.level.is_in_play_in_editor() or self.editor.get_game_world() is not None:
                self.begin_finish("refused", "Another PIE session started before our request.")
                return
            self.begin_requested = True
            self.level.editor_request_begin_play()
            self.event("pie_begin_requested")
            unreal.log("Starbay native smoke started; leave game controls untouched, max 45 + 5 seconds.")
        except Exception:
            self.result["error"] = traceback.format_exc()
            self.begin_finish("refused" if not self.begin_requested else "failed", "Startup failed.")

    def own_world(self, current):
        return valid(current) and current.get_path_name() == self.owned_world_path

    def set_phase(self, name, game_time):
        self.phase = name
        self.phase_game = game_time
        self.phase_wall = time.monotonic()
        self.grounded_since = None
        self.event("phase", phase_name=name)

    def acquire_character(self, current):
        if not valid(current):
            return False
        worlds = list(unreal.EditorLevelLibrary.get_pie_worlds(True))
        if len(worlds) != 1 or worlds[0] != current:
            raise RuntimeError("Expected one local PIE world; multi-client/server tests are not supported.")
        path = current.get_path_name()
        if "UEDPIE_" not in path or "L_Starbay" not in path:
            raise RuntimeError("New game world is not the expected temporary Starbay PIE world: " + path)
        if self.owned_world_path is None:
            self.owned_world_path = path
            self.world = current
            self.result["pie_world"] = path
            self.event("pie_world_observed", path=path)
        elif not self.own_world(current):
            raise RuntimeError("PIE world changed during startup; test ownership lost.")
        character = unreal.GameplayStatics.get_player_character(current, 0)
        if not valid(character):
            return False
        if character.get_class().get_path_name() != EXPECTED_CHARACTER:
            raise RuntimeError("Player 0 is not the official BP_ThirdPersonCharacter; refusing to drive it.")
        self.require(character, ["get_component_by_class", "get_actor_location", "get_velocity",
                                 "add_movement_input", "jump", "stop_jumping", "can_jump"])
        movement = character.get_component_by_class(unreal.CharacterMovementComponent)
        if not valid(movement):
            raise RuntimeError("Player character lacks native CharacterMovementComponent.")
        self.require(movement, ["is_falling", "is_moving_on_ground"])
        position = xyz(character.get_actor_location())
        if horizontal_distance(position, EXPECTED_SPAWN) > 150 or not -100 < position[2] < 400:
            raise RuntimeError("Player did not spawn near the audited PlayerStart; no movement was applied.")
        self.character, self.movement = character, movement
        self.result["character"] = character.get_path_name()
        self.result["character_class"] = character.get_class().get_path_name()
        self.result["spawn_position_cm"] = position
        self.result["movement_direction"] = list(DIRECTION)
        self.result["movement_input_scale"] = INPUT_SCALE
        self.result["movement_max_walk_speed_cm_s"] = float(movement.get_editor_property("max_walk_speed"))
        self.result["movement_max_step_height_cm"] = float(movement.get_editor_property("max_step_height"))
        capsule = character.get_component_by_class(unreal.CapsuleComponent)
        if valid(capsule):
            self.result["capsule_radius_cm"] = float(capsule.get_scaled_capsule_radius())
            self.result["capsule_half_height_cm"] = float(capsule.get_scaled_capsule_half_height())
        self.set_phase("settle", float(unreal.GameplayStatics.get_time_seconds(current)))
        return True

    def tick(self, slate_delta):
        if not self.active:
            return
        try:
            now = time.monotonic()
            if self.phase == "cleanup":
                self.cleanup_tick(now)
                return
            current = self.editor.get_game_world()
            if now - self.start_wall > WALL_LIMIT:
                self.begin_finish("failed", "Wall-clock deadline exceeded.")
                return
            if self.phase == "await_world":
                if self.acquire_character(current):
                    return
                if now - self.start_wall > STARTUP_LIMIT:
                    self.begin_finish("failed", "PIE world/player character did not become ready within startup limit.")
                return
            if not self.own_world(current) or not valid(self.character):
                self.begin_finish("interrupted", "Test PIE world or player ended/changed externally.")
                return
            game_time = float(unreal.GameplayStatics.get_time_seconds(self.world))
            # Slate can tick without the game progressing (paused PIE / background).
            # Never accumulate movement inputs or frame statistics on such callbacks.
            if self.last_game_time is not None and game_time <= self.last_game_time + 1e-7:
                return
            self.last_game_time = game_time
            position = xyz(self.character.get_actor_location())
            velocity = xyz(self.character.get_velocity())
            grounded = bool(self.movement.is_moving_on_ground())
            falling = bool(self.movement.is_falling())
            if not all(math.isfinite(x) for x in position + velocity):
                raise RuntimeError("Non-finite character state.")
            if position[2] < -100 or horizontal_distance(position, EXPECTED_SPAWN) > 700:
                raise RuntimeError("Character left the bounded spawn test area or fell below the pavement.")
            elapsed = game_time - self.phase_game
            sample = {"wall_seconds": round(now - self.start_wall, 5),
                      "game_seconds": round(game_time, 5), "phase": self.phase,
                      "slate_delta_ms": round(float(slate_delta) * 1000, 3),
                      "world_delta_ms": round(float(unreal.GameplayStatics.get_world_delta_seconds(self.world)) * 1000, 3),
                      "position_cm": [round(x, 3) for x in position],
                      "velocity_cm_s": [round(x, 3) for x in velocity],
                      "grounded": grounded, "falling": falling}
            # Bound report memory even at very high editor tick rates.
            if len(self.result["frames"]) < 6000:
                self.result["frames"].append(sample)
            if self.phase == "settle":
                if grounded and abs(velocity[2]) < 5 and math.hypot(*velocity[:2]) < 5:
                    if self.grounded_since is None:
                        self.grounded_since = game_time
                    if game_time - self.grounded_since >= 0.5:
                        self.result["checks"]["spawn"] = True
                        self.result["settled_position_cm"] = position
                        self.move_start = position
                        self.set_phase("move", game_time)
                else:
                    self.grounded_since = None
                if elapsed > 6:
                    raise RuntimeError("Player did not settle on walkable ground.")
            elif self.phase == "move":
                if math.hypot(*velocity[:2]) > 25:
                    self.move_velocity_frames += 1
                if elapsed < MOVE_GAME_SECONDS:
                    self.character.add_movement_input(unreal.Vector(*DIRECTION), INPUT_SCALE, False)
                    self.move_input_frames += 1
                else:
                    delta = [position[i] - self.move_start[i] for i in range(3)]
                    projection = sum(delta[i] * DIRECTION[i] for i in range(3))
                    lateral = abs(delta[0] * DIRECTION[1] - delta[1] * DIRECTION[0])
                    self.result["movement_result"] = {"start_cm": self.move_start, "end_cm": position,
                        "projected_cm": projection, "lateral_cm": lateral,
                        "input_frames": self.move_input_frames, "velocity_frames": self.move_velocity_frames}
                    if not (projection >= 100 and lateral < 75 and grounded
                            and self.move_input_frames >= 3 and self.move_velocity_frames >= 2):
                        raise RuntimeError("Native movement did not meet distance/direction/grounding evidence thresholds.")
                    self.result["checks"]["native_movement"] = True
                    self.set_phase("brake", game_time)
            elif self.phase == "brake":
                if grounded and math.hypot(*velocity[:2]) < 5 and elapsed >= 0.4:
                    if not self.character.can_jump():
                        raise RuntimeError("Grounded character cannot jump.")
                    self.jump_start = position
                    self.character.jump()
                    self.set_phase("jump", game_time)
                    self.event("jump_requested", position_cm=position)
                elif elapsed > 4:
                    raise RuntimeError("Character did not stop after movement input ceased.")
            elif self.phase == "jump":
                if elapsed >= 0.15 and not self.jump_released:
                    self.character.stop_jumping()
                    self.jump_released = True
                self.max_jump_rise = max(self.max_jump_rise, position[2] - self.jump_start[2])
                self.saw_airborne = self.saw_airborne or (falling and not grounded)
                self.saw_upward_velocity = self.saw_upward_velocity or velocity[2] > 50
                takeoff = self.saw_airborne and self.saw_upward_velocity and self.max_jump_rise >= 30
                self.result["checks"]["jump_takeoff"] = takeoff
                if takeoff and grounded and elapsed > 0.25:
                    if self.grounded_since is None:
                        self.grounded_since = game_time
                    if game_time - self.grounded_since >= 0.4:
                        landing_delta = abs(position[2] - self.jump_start[2])
                        self.result["jump_result"] = {"start_cm": self.jump_start, "land_cm": position,
                            "maximum_rise_cm": self.max_jump_rise, "landing_height_difference_cm": landing_delta,
                            "saw_falling_mode": self.saw_airborne, "saw_upward_velocity": self.saw_upward_velocity}
                        if landing_delta > 15 or abs(velocity[2]) > 5:
                            raise RuntimeError("Jump ended at an unexpected height or without stable landing.")
                        self.result["checks"]["jump_landing"] = True
                        self.begin_finish("passed", "Spawn, native movement, jump takeoff and landing observed.")
                else:
                    self.grounded_since = None
                if elapsed > 6 and self.phase != "cleanup":
                    raise RuntimeError("Jump/takeoff/stable landing evidence timed out.")
        except Exception:
            self.result["error"] = traceback.format_exc()
            if self.phase == "cleanup":
                self.finalize(False, "Cleanup API failed; use editor Stop manually.")
            else:
                self.begin_finish("failed", "Runtime test failed; see error.")

    def begin_finish(self, status, reason):
        if self.phase == "cleanup":
            return
        self.result["test_outcome"] = status
        self.result["reason"] = reason
        self.result["status"] = "stopping" if self.begin_requested else status
        self.phase = "cleanup"
        self.cleanup_started = time.monotonic()
        if self.begin_requested and self.handle is not None:
            self.cleanup_tick(self.cleanup_started)
        else:
            self.finalize(True, "No PIE session was started by this test; existing sessions were left untouched.")

    def cleanup_tick(self, now):
        current = self.editor.get_game_world()
        if valid(current) and self.owned_world_path is None and self.begin_requested:
            # A delayed world may appear after startup timeout. Only adopt the expected
            # temporary map created after our start request, never a different map.
            path = current.get_path_name()
            if "UEDPIE_" in path and "L_Starbay" in path:
                self.owned_world_path = path
        if valid(current) and not self.own_world(current):
            self.finalize(False, "Different game world observed; it was not stopped because ownership is uncertain.")
            return
        if self.own_world(current):
            if not self.stop_requested:
                if valid(self.character):
                    self.character.stop_jumping()
                self.level.editor_request_end_play()
                self.stop_requested = True
                self.event("pie_end_requested")
        elif self.owned_world_path is not None:
            if not self.level.is_in_play_in_editor() and not len(unreal.EditorLevelLibrary.get_pie_worlds(True)):
                self.finalize(True, "Owned PIE world ended; no PIE worlds remain.")
                return
        if now - self.cleanup_started >= CLEANUP_LIMIT:
            reason = "Editor did not confirm test world stopped; press the editor Stop button manually."
            if self.owned_world_path is None:
                reason = ("No PIE world appeared; reflected EndPlay cannot cancel an uncreated PlayWorld. "
                          "If a delayed PIE starts, press editor Stop. Cleanup is unconfirmed.")
            self.finalize(False, reason)

    def finalize(self, cleanup_ok, note):
        self.active = False
        unregister_error = None
        if self.handle is not None:
            try:
                unreal.unregister_slate_post_tick_callback(self.handle)
            except Exception:
                unregister_error = traceback.format_exc()
            self.handle = None
        self.result["cleanup"] = {"confirmed": cleanup_ok, "note": note,
                                  "end_play_requested": self.stop_requested,
                                  "slate_callback_unregistered": unregister_error is None}
        if unregister_error:
            self.result["cleanup"]["error"] = unregister_error
        outcome = self.result.get("test_outcome", "failed")
        self.result["status"] = outcome if cleanup_ok and not unregister_error else "cleanup_unconfirmed"
        self.result["finished_utc"] = datetime.now(timezone.utc).isoformat()
        self.result["elapsed_wall_seconds"] = round(time.monotonic() - self.start_wall, 4)
        deltas = sorted(x["world_delta_ms"] for x in self.result["frames"] if x["world_delta_ms"] > 0)
        self.result["editor_frame_summary"] = {"sample_count": len(deltas),
            "meaning": "PIE game delta samples during smoke; no GPU timing or performance target validated"}
        if deltas:
            self.result["editor_frame_summary"].update({"mean_ms": sum(deltas) / len(deltas),
                "median_ms": deltas[len(deltas) // 2],
                "p95_ms": deltas[min(len(deltas) - 1, math.ceil(len(deltas) * .95) - 1)],
                "max_ms": deltas[-1]})
        if self.keep_alive_before is not None:
            # With ExecutePythonScript, restoring False can close this editor on
            # its next tick. Leave it alive when cleanup requires operator action.
            self.result["cleanup"]["keep_alive_restored"] = bool(cleanup_ok and not unregister_error)
        self.write_report()
        unreal.log("Starbay native smoke: " + self.result["status"] + "; report: " + str(REPORT))
        if self.keep_alive_before is not None and cleanup_ok and not unregister_error:
            unreal.EditorPythonScripting.set_keep_python_script_alive(self.keep_alive_before)

    def cancel(self):
        """Optional manual cancellation: builtins._starbay_native_play_smoke.cancel()."""
        if self.active:
            self.begin_finish("interrupted", "Cancelled by operator.")


NativePlaySmoke().start()
