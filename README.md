# Stealth Prototype — original 2v2 asymmetric game

Status: **development prototype built against Unreal 5.8.3 on this Mac**. Native editor MCP is connected locally. Automated gameplay observations are recorded in `Saved/acceptance.json`; see `VALIDATION.md` for verified coverage and remaining checks. Character meshes are temporary mannequins with proxy gear, not finished character art.

## Character concepts first

- `Art/Concepts/spy-v2-flip-up-goggles.png`: lean infiltrator, charcoal fabric, compact harness, climbing equipment, and binocular night-vision goggles on a flip-up mount. This supersedes the historical monocular design.
- `Art/Concepts/spy-apose-v2-flip-up-goggles.png` and `merc-apose-v1.png`: front, side and back modeling references. Weapons and accessories should remain separate mesh parts.
- `Art/Concepts/merc-v1.png`: broad SWAT silhouette, navy uniform, plate carrier, helmet, dark goggles and a fully masked face.
- Halo influence means clean, readable high-quality game rendering and material shapes. Equipment remains present-day. These are concept images, **not 3D models, animations, or screenshots**.
- Built-in imagegen produced two separate character sheets. Prompt specifications are in `Art/Concepts/prompts.md`.

The playable characters use a mannequin-compatible skeletal mesh and eight temporary movement clips. The merc has a masked head, plate-carrier proxy, and an owner-visible weapon proxy; the spy has a two-optic animated goggle proxy. Final mesh modeling, UVs, textures, skinning, first-person arms and polished animation remain future work.

## Set up on this Mac

1. The verified engine location is `/Users/rob/Games/UE_5.8`. Full Xcode and its Metal Toolchain are installed. The C++ targets use BuildSettingsVersion.V7 and Unreal5_8 include order.
2. From this project directory, run `bash Scripts/setup_mac.sh`. It builds the Editor target with three compile workers, runs the repeatable asset bootstrap, verifies assets, then opens the prototype. Pass an engine folder argument to override the location.
3. The public repository includes the map, materials, sounds and Blueprint child. Epic-derived mannequin mesh and animation binaries remain outside this public repository. In your licensed Unreal 5.8 installation, enable the MoverExamples editor plugin, restart, and execute `Scripts/migrate_mannequin.py` through Tools > Execute Python Script with normal rendering enabled. This imports the installed example mannequin and eight clips into `Content/Prototype/Mannequin/`. Then disable MoverExamples, restart, and run `Scripts/bootstrap_editor.py`. Runtime gameplay does not use Mover. Until migration, primitive fallback characters are available; missing-asset messages are expected.
4. Open `StealthPrototype.uproject`, then `/Game/Maps/Prototype`. A single-player Play session starts development-only practice; Tab changes roles and scoring is disabled. Console command `Match` starts standalone competitive waiting mode; `Practice` restores practice.

The blank generated map is deliberate: the GameMode constructs arena geometry and spawn points when Play begins. The editor viewport will be empty until then. Select the generated map as Editor Startup Map in Project Settings if desired.

## First four-player test

In the Play dropdown's multiplayer options, choose **4 players**, **Play As Listen Server**, and **New Editor Window (PIE)**. Begin with Low scalability and small windows on this Mac. Click a window to give it keyboard/mouse focus; Shift+F1 releases the mouse. All windows are real network participants, but only the focused window is controlled locally. A simultaneous match needs additional humans/machines or controllers in a later input pass; bots and split-screen are not included.

The first four players are assigned alternately Spy, Merc, Spy, Merc. The timer waits for exactly 2 players on each team. Extra connections are rejected. On disconnect the round resets and waits for a replacement. Local PIE does not require public network exposure. Internet matchmaking, accounts, hosting, dedicated-server packaging and anti-cheat are not implemented.

| Input | Spy | Merc |
| --- | --- | --- |
| WASD / mouse | Move / third-person camera | Move / first-person camera |
| Left Ctrl | Toggle crouch / drop from ledge | Toggle crouch |
| Space | Jump / catch marked ledge / vault / climb from hanging | — |
| Hold E | Hack within 2 m of central terminal, with line of sight | — |
| Left click | Aimed rear takedown within 1.8 m | One hitscan shot per click |
| F | — | Toggle flashlight |
| N | Lower binocular goggles and enable night vision / raise and disable | — |
| Tab | Switch role in solo practice only | Switch role in solo practice only |

Spies need 20 cumulative seconds of hacking. Two spies do not accelerate the hack. Released progress persists. Mercs win if the 180-second timer expires; a completed hack takes priority on the same tick. Merc shots do 34 damage; spies can do 100 damage from behind. Friendly fire is ignored. Dead players respawn after 5 seconds. Results display for 8 seconds, then the round resets. The server checks attack cadence, role, trace, target and takedown angle; the server also checks hack distance and visibility. This is prototype validation, not production cheat prevention.

## Development and focused playtests

C++ owns movement, combat and server rules. `BP_Player` exposes role speed, camera distance, reach and damage tuning. `SPTraversalMovement` extends CharacterMovement with replicated root-motion sources. Only static tagged geometry supports traversal; moving ledges and shimmying are excluded. The warehouse blockout includes cover, an elevated route, dark approaches and a spy-only crouch passage.

The project's native MCP toolset registers from `Content/Python/init_unreal.py`. The endpoint uses loopback port 8000. It provides identity/selection readback, saving, repeatable asset preparation and bounded editor-only test fixtures. Runtime gameplay contains no LLMs or bots. The bundled Unreal plugin supplies the Codex connection; no existing Codex configuration was replaced.

With the editor open, run `python3 Scripts/run_acceptance.py` for solo and four-client observations. It temporarily disables background editor throttling, uses 640×360 client windows, and leaves solo practice running. Test placements and shortened win-condition timers are editor-only fixtures; network input still travels through the owning client and server RPCs.

For a human playtest, begin with one player. Try both roles with Tab; test crouch, Space at low cover and at the north raised platform, Ctrl to drop, and N to flip the goggles. Then use four PIE clients to test visibility, flashlight, rear takedowns, terminal hacking and round restarts. Focus one window at a time; Shift+F1 releases its mouse. Judge turning, speed, camera collision, dark-area readability and spatial audio on this Mac before increasing detail.

See `VALIDATION.md` for remaining evidence gaps. Internet matchmaking, final characters, first-person arms, polished traversal animation, moving ledges, lateral shimmying, gadgets, spawn protection, dedicated-server packaging and production anti-cheat are outside this prototype.

## Official references

- [Install Unreal Engine](https://dev.epicgames.com/documentation/unreal-engine/install-unreal-engine)
- [macOS development requirements](https://dev.epicgames.com/documentation/unreal-engine/macos-development-requirements-for-unreal-engine)
- [Multiplayer programming quick start](https://dev.epicgames.com/documentation/en-us/unreal-engine/multiplayer-programming-quick-start-for-unreal-engine)
- [Testing multiplayer](https://dev.epicgames.com/documentation/en-us/unreal-engine/testing-multiplayer-in-unreal-engine)
- [Editor Python scripting](https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-unreal-editor-using-python)
