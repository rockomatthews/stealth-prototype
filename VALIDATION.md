# Current checkpoint — October 19, 2026

October 20 update: temporary solo character selection now supports **1 = Spy**, **2 = Merc**, plus Tab/D-pad Right toggling. The editor build succeeds; direct selection and toggling were exercised in live practice, with a 60 cm first-person camera offset for merc and a 289 cm third-person offset for spy. No input isolation was enabled for this handoff. Internet/Host/Join work is deferred while the user tests feel and appearance. Runtime characters remain placeholders.

Xbox controller support is implemented and the Unreal 5.8.3 Development Editor build succeeds on this Mac. **44/44 automated gameplay checks passed**; see [TEST_RESULTS.md](TEST_RESULTS.md). The project is ready for a focused human controller playtest, with temporary art.

## Verified foundation

- Solo practice and competitive mode remain separate. Practice uses D-pad Right or Tab to switch role; scoring is disabled. Competitive PIE starts with four possessed characters and two players per team.
- Xbox sticks, radial dead zone, A traversal, B crouch/drop, X hacking, RT combat, LT merc aiming and Y role equipment run through Enhanced Input. Look rate is frame-rate independent; tuning and invert Y are Blueprint defaults.
- Spy camera actually sits behind the character on its spring-arm socket; merc camera is first person. Local HUD drawing and correct camera offsets were checked in all four clients. The controller prompts and both rendered views were inspected.
- Remote goggles, hanging and climbing replicate. Climbing was checked with 100 ms lag and 2% packet loss, with final position agreement within 25 cm. Death cancels traversal; the player respawns.
- Cover blocks shots, merc shots deal 34 damage, three shots down a spy, front takedowns are rejected and rear takedowns succeed. Remote hacking, both team wins and round reset pass.
- Project/map identity and selection were read through native MCP. Editor assets are saved. The endpoint binds loopback only.

## Current art and Xbox scope

The spy uses binocular flip-up goggles. Current references are `Art/Concepts/spy-v2-flip-up-goggles.png` and `spy-apose-v2-flip-up-goggles.png`. Merc references remain masked and SWAT-like. Runtime meshes, weapon and gear are placeholders; no final custom rigged characters or first-person arms have been made.

Xbox Series X|S is the current console target. Mac testing does not produce an Xbox console build. See [XBOX.md](XBOX.md) for controller controls and the Windows, Xbox developer access and console hardware requirements. No SDK enrollment, purchase, console packaging or certification has occurred.

## Resume with the human playtest

1. Connect the Xbox controller and click the solo practice game window. Move either stick to switch the HUD to Xbox hints. Use D-pad Right to compare roles, A at north platforms and low cover, B to drop, and Y for goggles/flashlight.
2. Judge sensitivity, turning, crouch speed, camera collision, dark-area readability and comfort. Tune ControllerYawRate, ControllerPitchRate, StickDeadZone, bInvertControllerY, AimSensitivity and role speeds in BP_Player defaults.
3. Still verify physical controller disconnect/reconnect, keyboard-to-pad switching under real hardware, blocked hacking, deliberately invalid/blocked ledges, disconnect/rejoin and prolonged play. Multi-process/multi-machine tests and controlled GPU profiling remain outstanding.
4. Final character modeling, UVs, textures, skinning, polished animation/first-person arms and a detailed industrial environment follow the movement feel test. Milestones D/E are not fully complete.

## Build and automated checks

After saving, close only this project's editor and run `bash Scripts/setup_mac.sh` (default engine `/Users/rob/Games/UE_5.8`). The build uses `-NoHotReloadFromIDE` so another open editor cannot leave the launch manifest pointing at a stale numbered module.

With this editor open, `python3 Scripts/run_acceptance.py` runs the bounded editor-only fixtures, temporarily isolates physical gameplay input to avoid interference, and restores ordinary solo practice afterward. Avoid closing PIE during that run. Snapshots and build logs live in ignored Saved/. Current game/test source is committed; no runtime LLMs or bots are involved.

The public source repository excludes Epic mannequin binaries and local generated files; [PUBLICATION.md](PUBLICATION.md) describes the safe export workflow. No user-file cleanup, purchases, optional large content downloads or internet hosting are included.
