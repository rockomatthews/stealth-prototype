# Current checkpoint — October 20, 2026

Both original Meshy characters are rigged and optimized to 80,000 triangles each. Solo practice supports **1 = Spy**, **2 = Merc**, **Tab/D-pad Right = switch**, and **V/D-pad Up = appearance view**. The Development Editor build and **50/50 automated checks passed**. See [CHARACTER_PLAYTEST.md](CHARACTER_PLAYTEST.md) and [TEST_RESULTS.md](TEST_RESULTS.md). Internet Host/Join remains deferred while feel and appearance are tested. PIE is stopped and the project is saved for tomorrow.

## Verified foundation

- Solo practice and competitive mode remain separate. Practice uses D-pad Right or Tab to switch role; scoring is disabled. Competitive PIE starts with four possessed characters and two players per team.
- Xbox sticks, radial dead zone, A traversal, B crouch/drop, X hacking, RT combat, LT merc aiming and Y role equipment run through Enhanced Input. Look rate is frame-rate independent; tuning and invert Y are Blueprint defaults.
- Spy camera actually sits behind the character on its spring-arm socket; merc camera is first person. Local HUD drawing and correct camera offsets were checked in all four clients. The controller prompts and both rendered views were inspected.
- Remote goggles, hanging and climbing replicate. Climbing was checked with 100 ms lag and 2% packet loss, with final position agreement within 25 cm. Death cancels traversal; the player respawns.
- Cover blocks shots, merc shots deal 34 damage, three shots down a spy, front takedowns are rejected and rear takedowns succeed. Remote hacking, both team wins and round reset pass.
- Project/map identity and selection were read through native MCP. Editor assets are saved. The endpoint binds loopback only.

## Current art and Xbox scope

The spy and fully masked SWAT-like merc now use textured prototype rigs. Three modeling reference documents and source images are in `Art/ModelingReferences/2026-10-20`. Goggles and back gear remain baked into the spy body; separate hinged goggles, state-controlled lens emission and drawn launcher animations remain work to do. The merc carbine import is included but not yet equipped. First-person arms and production weight cleanup are unfinished.

Xbox Series X|S is the current console target. Mac testing does not produce an Xbox console build. See [XBOX.md](XBOX.md) for controller controls and the Windows, Xbox developer access and console hardware requirements. No SDK enrollment, purchase, console packaging or certification has occurred.

## Resume with the human playtest

1. Connect the Xbox controller and click the solo practice game window. Move either stick to switch the HUD to Xbox hints. Use D-pad Right to compare roles, A at north platforms and low cover, B to drop, and Y for goggles/flashlight.
2. Judge sensitivity, turning, crouch speed, camera collision, dark-area readability and comfort. Tune ControllerYawRate, ControllerPitchRate, StickDeadZone, bInvertControllerY, AimSensitivity and role speeds in BP_Player defaults.
3. Still verify physical controller disconnect/reconnect, keyboard-to-pad switching under real hardware, blocked hacking, deliberately invalid/blocked ledges, disconnect/rejoin and prolonged play. Multi-process/multi-machine tests and controlled GPU profiling remain outstanding.
4. Production character deformation cleanup, polished animation/first-person arms, equipment integration and a detailed industrial environment follow the movement feel test. Milestones D/E are not fully complete.

## Build and automated checks

After saving, close only this project's editor and run `bash Scripts/setup_mac.sh` (default engine `/Users/rob/Games/UE_5.8`). The build uses `-NoHotReloadFromIDE` so another open editor cannot leave the launch manifest pointing at a stale numbered module.

With this editor open, `python3 Scripts/run_acceptance.py` runs the bounded editor-only fixtures, temporarily isolates physical gameplay input to avoid interference, and restores ordinary solo practice afterward. Avoid closing PIE during that run. Snapshots and build logs live in ignored Saved/. Current game/test source is committed; no runtime LLMs or bots are involved.

The public source repository excludes Epic mannequin binaries and local generated files; [PUBLICATION.md](PUBLICATION.md) describes the safe export workflow. No user-file cleanup, purchases, optional large content downloads or internet hosting are included.
