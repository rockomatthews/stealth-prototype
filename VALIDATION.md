# Current checkpoint — October 30, 2026

Merc jumping, separate spy goggles, skeletal weapons, first-person merc arms and the spy shoulder launcher are implemented. **Y / Q toggles hands/shocker; RB / G fires the selected spy gadget. D-pad Up controls night vision / flashlight. D-pad Left / V is temporary appearance view.** See [CHARACTER_PLAYTEST.md](CHARACTER_PLAYTEST.md) for the complete controls and current limitations. The final result of this checkpoint is recorded in TEST_RESULTS.md. Internet Host/Join remains deferred.

## Verified foundation

- Solo practice and competitive mode remain separate. Practice uses D-pad Right or Tab to switch role; scoring is disabled. Competitive PIE starts with four possessed characters and two players per team.
- Xbox sticks, radial dead zone, A traversal, B crouch/drop, X hacking, RT combat, LT merc aiming and Y weapon switching and D-pad Up role equipment run through Enhanced Input. Look rate is frame-rate independent; tuning and invert Y are Blueprint defaults.
- Spy camera actually sits behind the character on its spring-arm socket; merc camera is first person. Local HUD drawing and correct camera offsets were checked in all four clients. The controller prompts and both rendered views were inspected.
- Remote goggles, hanging and climbing replicate. Climbing was checked with 100 ms lag and 2% packet loss, with final position agreement within 25 cm. Death cancels traversal; the player respawns.
- Cover blocks shots, merc shots deal 34 damage, three shots down a spy, front takedowns are rejected and rear takedowns succeed. Remote hacking, both team wins and round reset pass.
- Project/map identity and selection were read through native MCP. Editor assets are saved. The endpoint binds loopback only.

## Current art and Xbox scope

The spy and fully masked SWAT-like merc use textured prototype rigs. Goggles are independently hinged with two switched emissive optics. The launcher has draw/holster and ready poses, taser primary fire and separate sticky-camera secondary fire. The merc carbine is equipped, with owner-only first-person arms and a world model for other players. First-person hand deformation, reload/ammunition systems and production animation polish remain unfinished. Reference documents remain in `Art/ModelingReferences/2026-10-20`.

Xbox Series X|S is the current console target. Mac testing does not produce an Xbox console build. See [XBOX.md](XBOX.md) for controller controls and the Windows, Xbox developer access and console hardware requirements. No SDK enrollment, purchase, console packaging or certification has occurred.

## Resume with the human playtest

1. Connect the Xbox controller and click the solo practice game window. Move either stick to switch the HUD to Xbox hints. Use D-pad Right to compare roles, A at north platforms and low cover, B to drop, and Y for goggles/flashlight.
2. Judge sensitivity, turning, crouch speed, camera collision, dark-area readability and comfort. Tune ControllerYawRate, ControllerPitchRate, StickDeadZone, bInvertControllerY, AimSensitivity and role speeds in BP_Player defaults.
3. Still verify physical controller disconnect/reconnect, keyboard-to-pad switching under real hardware, blocked hacking, deliberately invalid/blocked ledges, disconnect/rejoin and prolonged play. Multi-process/multi-machine tests and controlled GPU profiling remain outstanding.
4. Production character deformation cleanup, polished animation and equipment detail and a detailed industrial environment follow the movement feel test. Milestones D/E are not fully complete.

## Build and automated checks

After saving, close only this project's editor and run `bash Scripts/setup_mac.sh` (default engine `/Users/rob/Games/UE_5.8`). The build uses `-NoHotReloadFromIDE` so another open editor cannot leave the launch manifest pointing at a stale numbered module.

With this editor open, `python3 Scripts/run_acceptance.py` runs the bounded editor-only fixtures, temporarily isolates physical gameplay input to avoid interference, and restores ordinary solo practice afterward. Avoid closing PIE during that run. Snapshots and build logs live in ignored Saved/. Current game/test source is committed; no runtime LLMs or bots are involved.

The public source repository excludes Epic mannequin binaries and local generated files; [PUBLICATION.md](PUBLICATION.md) describes the safe export workflow. No user-file cleanup, purchases, optional large content downloads or internet hosting are included.
