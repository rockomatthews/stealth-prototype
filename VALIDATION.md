# Current checkpoint — November 7, 2026

The new Warehouse map passed 46/46 focused solo and four-client checks, including six rope entrances, crouched vent clearance, top remount/descent, 100 ms latency with 2% packet loss, gunfire through duct skins, drop knockouts/recovery, the merc entrance, and owner/remote grenade animation props. The current layout contains 375 crates. Evidence and art provenance are documented in [WAREHOUSE.md](WAREHOUSE.md).

Merc jumping, separate spy goggles, skeletal weapons, first-person merc arms and the spy shoulder launcher are implemented. **D-pad Down / R selects sticky camera or Spy Bullet. Three cameras and four darts are supplied per life, with live HUD counts. Y / Q toggles hands/shocker; RB / G fires the selected spy gadget. D-pad Up controls night vision / flashlight. D-pad Left / V is temporary appearance view.** See [CHARACTER_PLAYTEST.md](CHARACTER_PLAYTEST.md) for the complete controls and current limitations. The final result of this checkpoint is recorded in TEST_RESULTS.md. Internet Host/Join remains deferred.

The inventory extension passed 44/44 focused checks, including depletion, invalid surfaces, tracking expiry, team readouts, remote replication under latency, respawn and round reset.

## Verified foundation

- Solo practice and competitive mode remain separate. Practice uses D-pad Right or Tab to switch role; scoring is disabled. Competitive PIE starts with four possessed characters and two players per team.
- Xbox sticks, radial dead zone, A traversal, B crouch/drop, X hacking, RT combat, LT merc aiming and Y weapon switching and D-pad Up role equipment run through Enhanced Input. Look rate is frame-rate independent; tuning and invert Y are Blueprint defaults.
- Spy camera actually sits behind the character on its spring-arm socket; merc camera is first person. Local HUD drawing and correct camera offsets were checked in all four clients. The controller prompts and both rendered views were inspected.
- Remote goggles, hanging and climbing replicate. Climbing was checked with 100 ms lag and 2% packet loss, with final position agreement within 25 cm. Death cancels traversal; the player respawns.
- Cover blocks shots, merc shots deal 34 damage, three shots down a spy, front takedowns are rejected and rear takedowns succeed. Remote hacking, both team wins and round reset pass.
- Project/map identity and selection were read through native MCP. Editor assets are saved. The endpoint binds loopback only.

## Current art and Xbox scope

The spy and fully masked SWAT-like merc use textured prototype rigs. Goggles are independently hinged with two switched emissive optics. The launcher has draw/holster and ready poses, taser primary fire and separate selected-gadget secondary fire. The merc carbine is equipped, with owner-only first-person arms and a world model for other players. First-person hand deformation, merc reload/ammunition systems and production animation polish remain unfinished. Reference documents remain in `Art/ModelingReferences/2026-10-20`.

Xbox Series X|S is the current console target. Mac testing does not produce an Xbox console build. See [XBOX.md](XBOX.md) for controller controls and the Windows, Xbox developer access and console hardware requirements. No SDK enrollment, purchase, console packaging or certification has occurred.

## Resume with the human playtest

1. Connect the Xbox controller and click the solo practice game window. Move either stick to switch the HUD to Xbox hints. Use D-pad Right to compare roles, A at north platforms and low cover, B to drop, D-pad Up for goggles/flashlight, Y for draw/holster and D-pad Down for gadget selection.
2. Judge sensitivity, turning, crouch speed, camera collision, dark-area readability and comfort. Tune ControllerYawRate, ControllerPitchRate, StickDeadZone, bInvertControllerY, AimSensitivity and role speeds in BP_Player defaults.
3. Still verify physical controller disconnect/reconnect, keyboard-to-pad switching under real hardware, blocked hacking, deliberately invalid/blocked ledges, disconnect/rejoin and prolonged play. Multi-process/multi-machine tests and controlled GPU profiling remain outstanding.
4. Production character deformation cleanup, polished animation and equipment detail and a detailed industrial environment follow the movement feel test. Milestones D/E are not fully complete.

## Build and automated checks

After saving, close only this project's editor and run `bash Scripts/setup_mac.sh` (default engine `/Users/rob/Games/UE_5.8`). The build uses `-NoHotReloadFromIDE` so another open editor cannot leave the launch manifest pointing at a stale numbered module.

With this editor open, `python3 Scripts/run_acceptance.py` runs the bounded editor-only fixtures, temporarily isolates physical gameplay input to avoid interference, and restores ordinary solo practice afterward. Avoid closing PIE during that run. Snapshots and build logs live in ignored Saved/. Current game/test source is committed; no runtime LLMs or bots are involved.

The public source repository excludes Epic mannequin binaries and local generated files; [PUBLICATION.md](PUBLICATION.md) describes the safe export workflow. No user-file cleanup, purchases, optional large content downloads or internet hosting are included.

## Manual-aligned Spy Bullets and sticky camera controls

The retail Xbox Versus manual was rechecked before camera work. Spy Bullets now mark a merc directly or become a proximity radar sensor on a wall. The spy-only radar uses actual detected merc positions, and sensor contacts disappear on exit from range/expiry. Spy Bullet interception of enemy team radio remains pending; the implemented voice routes preserve team privacy except for the explicit held-merc pair channel. Detection radius and lifetimes are prototype tuning values.

Camera viewing now routes right stick/mouse into a clamped mount, LT/RT into continuous zoom, X/E into spatial distraction noise, B/Ctrl into a single gas release, and Up/N into camera NV. LB/C exits; Y remains weapon draw/holster. Server view/ownership validation protects gas/noise actions; visible gas stuns exposed mercs with a geometry check and ignores spies. Thermal vision and merc gas-mask counterplay are pending.

## Required human multiplayer communications

Do not call the first human multiplayer playtest ready until both teams have working private teammate voice and a spy can speak with a merc during a sustained rear grab. The server must authorize the grab's pair channel and revoke it on release, death, disconnect and round reset. Verify real speech in both directions on separate Macs, alongside team isolation and cleanup. Both voice routes and sustained grabs are now implemented; real two-Mac speech acceptance is still pending; see XBOX.md for the required behavior. These requirements precede expansion of remaining gadgets.

## Grab and voice implementation

The rear hold is server-authorized and replicated. It replaces the instant rear kill with hold, release and finish states. Peer voice is bound to the two controllers in that hold; team voice is sent only to same-team controllers. Encoded packets are bounded/rate-limited, and epoch/pair validation prevents stale grab playback after release, death, pawn recreation, round reset and disconnect. Source audio is never multicast to opposing clients. Open team mic is the chosen default; Grab speech opens automatically for the pair and returns to team speech on release; View/M is the master mute.

Generated audio tests exercise real Opus encode/decode and procedural playback creation, not just channel flags. Multi-client/automated PIE never opens a live microphone. Live speech, input/output devices, echo behavior and external-machine internet sessions must still be validated. Original paired hold, snap, kick and grenade clips now replace the equipment-pose placeholder; production animation polish remains pending.

## Slow holds and vulnerable finishers

The captor walks slowly and rotates the pair, constrained by server capsule sweeps and floor checks. The captive owner receives token-validated smoothed poses. Tap RT starts a short neck snap; holding 0.5 seconds selects a 3.8-second grenade theft/plant if inventory allows, or a 3.1-second kneeling kick. Both participants remain damageable and interruptions clear pending actions. An armed grenade survives interruption; round epochs remove stale grenades safely. Extended movement corridors are checked before committing.

Run `Scripts/run_finisher_acceptance.py` for four-client controller, ammunition, rescue, wall, bone-contact, stale-input and latency checks. Current final results are in TEST_RESULTS.md. Merc RB/G throwing now uses the same replicated count as theft. The server validates release clearance and player state, launches a bouncing projectile, and owns fuse/blast damage. Run `Scripts/run_merc_grenade_acceptance.py` for shared depletion, theft after throwing, empty kick fallback, blast cover, death and latency checks. Production animation polish remains pending.

## Supported vent mantle

Run `Scripts/validate_vent_entry_art.py` for source-bone support/clearance and exact crawl handoff checks, then `Scripts/run_vent_entry_acceptance.py` against the live editor. The latter samples rendered bone positions and the full clip timeline, then tests interruption, death/respawn and remote convergence at 100 ms lag / 2% packet loss. Rerun warehouse acceptance after movement changes. Use `Scripts/review_vent_entry.py` for bounded frozen poses and `Scripts/record_vent_entry_review.py` for actual gameplay footage. Physical-controller weight, camera comfort and animation appeal still need human review.

## Collision-based aerial knockouts

Run `Scripts/run_knockout_acceptance.py` for actual falling-capsule contacts, repeated knockouts after recovery, fast falls, near misses, cover rejection, host/remote spies, exactly-once awards, replicated body placement, controller restrictions, death/respawn and 100 ms lag / 2% loss. The matrix requests 60/30/15/6 FPS caps and reports measured frame times. All caps and lag settings are restored in `finally`. Run warehouse acceptance afterward to cover traversal and equipment together. These Mac PIE checks do not establish Xbox hardware certification or controller feel.

## Merc recovery shield

Run `Scripts/run_recovery_acceptance.py`, followed by warehouse and knockout acceptance. Verify actual cyan arcs in the captured game view, not only active-state flags. Check the merc can move/fire while still protected, real landing and rear-grab attempts are blocked during the window, both work after expiry, rejected grabs do not open pair voice, and death/respawn/round changes leave no stale shield. The low-frame-rate/network case uses four local clients at a 6 FPS cap with 100 ms lag / 2% loss. Repeat-knockout regression waits until the new shield has expired.
