# Stealth Prototype — original 2v2 asymmetric game

Status: **development prototype built against Unreal 5.8.3 on this Mac**. Native editor MCP is connected locally. Automated gameplay observations are recorded in `Saved/acceptance.json`; see `VALIDATION.md` for verified coverage and remaining checks. Playable characters use the imported Meshy spy and merc rigs, separate equipment and prototype animation; final animation polish remains in progress.

The intended console target is Xbox Series X|S. Xbox controller input is implemented for both roles, including sticks, A/B traversal/crouch, X hacking, triggers for attack/aim Y weapon switching and D-pad Up equipment. See [XBOX.md](XBOX.md) for controls, Mac playtesting and the later console build requirements.

## Character concepts first

- `Art/Concepts/spy-v2-flip-up-goggles.png`: lean infiltrator, charcoal fabric, compact harness, climbing equipment, and binocular night-vision goggles on a flip-up mount. This supersedes the historical monocular design.
- `Art/Concepts/spy-apose-v2-flip-up-goggles.png` and `merc-apose-v1.png`: front, side and back modeling references. Weapons and accessories should remain separate mesh parts.
- `Art/Concepts/merc-v1.png`: broad SWAT silhouette, navy uniform, plate carrier, helmet, dark goggles and a fully masked face.
- Halo influence means clean, readable high-quality game rendering and material shapes. Equipment remains present-day. These are concept images, **not 3D models, animations, or screenshots**.
- Built-in imagegen produced two separate character sheets. Prompt specifications are in `Art/Concepts/prompts.md`.

The playable Meshy spy and merc use mannequin-compatible rigs and temporary movement clips. The spy has independently hinged binocular goggles with two switched lights and an equipped shoulder launcher. The merc has a skeletal carbine, first-person arms and ordinary jumping without ledge traversal. Authored upper-body equipment poses blend over locomotion. See [CHARACTER_PLAYTEST.md](CHARACTER_PLAYTEST.md) for the current controls and prototype limitations.

## Set up on this Mac

1. The verified engine location is `/Users/rob/Games/UE_5.8`. Full Xcode and its Metal Toolchain are installed. The C++ targets use BuildSettingsVersion.V7 and Unreal5_8 include order.
2. From this project directory, run `bash Scripts/setup_mac.sh`. It builds the Editor target with three compile workers, runs the repeatable asset bootstrap, verifies assets, then opens the prototype. Pass an engine folder argument to override the location.
3. The public repository includes the map, materials, sounds and Blueprint child. Epic-derived mannequin mesh and animation binaries remain outside this public repository. In your licensed Unreal 5.8 installation, enable the MoverExamples editor plugin, restart, and execute `Scripts/migrate_mannequin.py` through Tools > Execute Python Script with normal rendering enabled. This imports the installed example mannequin and eight clips into `Content/Prototype/Mannequin/`. Then disable MoverExamples, restart, and run `Scripts/bootstrap_editor.py`. Runtime gameplay does not use Mover. Until migration, primitive fallback characters are available; missing-asset messages are expected.
4. Open `StealthPrototype.uproject`, then `/Game/Maps/Warehouse`. A single-player Play session starts development-only practice; Tab changes roles and scoring is disabled. Console command `Match` starts standalone competitive waiting mode; `Practice` restores practice.

Warehouse is the default playable and editor startup map. Its saved modular environment previews in the editor; the GameMode adds replicated gameplay routes, the entrance door and objectives at runtime. `/Game/Maps/Prototype` remains an isolated regression-test fixture.

## First four-player test

In the Play dropdown's multiplayer options, choose **4 players**, **Play As Listen Server**, and **New Editor Window (PIE)**. Begin with Low scalability and small windows on this Mac. Click a window to give it keyboard/mouse focus; Shift+F1 releases the mouse. All windows are real network participants, but only the focused window is controlled locally. A simultaneous match needs additional humans/machines or controllers in a later input pass; bots and split-screen are not included.

The first four players are assigned alternately Spy, Merc, Spy, Merc. The timer waits for exactly 2 players on each team. Extra connections are rejected. On disconnect the round resets and waits for a replacement. Local PIE does not require public network exposure. Internet matchmaking, accounts, hosting, dedicated-server packaging and anti-cheat are not implemented.

| Input | Spy | Merc |
| --- | --- | --- |
| WASD / mouse | Move / third-person camera | Move / first-person camera |
| Left Ctrl | Toggle crouch / drop from ledge | Toggle crouch |
| Space | Jump / catch marked ledge / vault / climb from hanging | Jump, no traversal |
| E | Rear grab with empty hands; hold to hack terminal | — |
| Left click | Start rear hold with hands; finish held merc; taser when drawn | One hitscan shot per click |
| F | — | Toggle flashlight |
| N | Lower binocular goggles and enable night vision / raise and disable | — |
| Tab | Switch role in solo practice only | Switch role in solo practice only |
| 1 / 2 | Select Spy / Merc directly in solo practice | Select Spy / Merc directly in solo practice |

Each spy life starts with three cameras and four Spy Bullets; remaining counts appear on the HUD. Q / Y toggles hands and the spy shocker; G / RB fires the selected spy gadget; R / D-pad Down selects camera or Spy Bullet; V / D-pad Left toggles appearance view. D-pad Up controls night vision / flashlight. C / LB enters or leaves the spy’s deployed sticky camera. Character switching is a temporary local playtest control. D-pad Right also toggles the practice character. These controls do not change teams during competitive matches.

Spies need 20 cumulative seconds of hacking. Two spies do not accelerate the hack. Released progress persists. Mercs win if the 180-second timer expires; a completed hack takes priority on the same tick. Merc shots do 34 damage. A falling spy can knock a merc unconscious for six seconds by landing directly from above; near misses and intervening cover do not count. Rear holds retain their separate explicit finishing controls. Friendly fire is ignored. Dead players respawn after 5 seconds. Results display for 8 seconds, then the round resets. The server checks attack cadence, role, trace, target and takedown angle; the server also checks hack distance and visibility. This is prototype validation, not production cheat prevention.

## Development and focused playtests

C++ owns movement, combat and server rules. `BP_Player` exposes role speed, camera distance, reach and damage tuning. `SPTraversalMovement` extends CharacterMovement with replicated root-motion sources. Only static tagged geometry supports traversal; moving ledges and shimmying are excluded. The warehouse follows the supplied industrial references: dense crate stacks, intermediate climbing routes and bridges, perimeter catwalks, skylights, six ropes and connected overhead ducts. Only spies climb ropes; merc bullets penetrate the thin duct skins. The main room stays readable without night vision. Mercs enter from one spawn-room door; the future office remains a closed facade.

The project's native MCP toolset registers from `Content/Python/init_unreal.py`. The endpoint uses loopback port 8000. It provides identity/selection readback, saving, repeatable asset preparation and bounded editor-only test fixtures. Runtime gameplay contains no LLMs or bots. The bundled Unreal plugin supplies the Codex connection; no existing Codex configuration was replaced.

With the editor open, run `python3 Scripts/run_acceptance.py` for solo and four-client observations. It temporarily disables background editor throttling, uses 640×360 client windows, and leaves solo practice running. Test placements and shortened win-condition timers are editor-only fixtures; network input still travels through the owning client and server RPCs.

For a human playtest, begin with one player. Try both roles with Tab; test crouch, Space at low cover and at the north raised platform, Ctrl to drop, and N to flip the goggles. Then use four PIE clients to test visibility, flashlight, rear takedowns, terminal hacking and round restarts. Focus one window at a time; Shift+F1 releases its mouse. Judge turning, speed, camera collision, dark-area readability and spatial audio on this Mac before increasing detail.

See `VALIDATION.md` for remaining evidence gaps. Internet matchmaking, final character polish, polished traversal animation, moving ledges, lateral shimmying, remaining gadgets, spawn protection, dedicated-server packaging and production anti-cheat are outside this prototype.

## Official references

- [Install Unreal Engine](https://dev.epicgames.com/documentation/unreal-engine/install-unreal-engine)
- [macOS development requirements](https://dev.epicgames.com/documentation/unreal-engine/macos-development-requirements-for-unreal-engine)
- [Multiplayer programming quick start](https://dev.epicgames.com/documentation/en-us/unreal-engine/multiplayer-programming-quick-start-for-unreal-engine)
- [Testing multiplayer](https://dev.epicgames.com/documentation/en-us/unreal-engine/testing-multiplayer-in-unreal-engine)
- [Editor Python scripting](https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-unreal-editor-using-python)

Sticky cameras now support pan/tilt, held-trigger zoom, spatial distraction sound, one gas burst and camera night vision. See CHARACTER_PLAYTEST.md for the contextual controls. Spy Bullets now have the retail manual's enemy-tag and wall-area-sensor functions, displayed on a spy radar. Prototype ranges/durations differ from unverified original balance values; enemy communications interception, thermal camera vision and merc gas masks remain pending.

Sustained rear holds and two private voice routes are now implemented. Team voice is open-mic; a rear hold automatically switches both participants to private open-mic grab conversation. View/M mutes the microphone. X/E grabs; the spy can slowly drag and turn the merc. B releases; tap RT snaps the neck; hold RT commits to a longer grenade-theft finisher if the merc has ammunition, or a hands-and-knees kick finisher otherwise. Both remain vulnerable to interruption. A pulled-pin grenade survives interruption. Y remains draw/holster only. Multi-client PIE tests use generated tones through the real Opus/network/playback path and never open live microphones. Human two-Mac speech and internet hosting remain unverified. See CHARACTER_PLAYTEST.md for controls, capture/device behavior and prototype animation limitations.

Mercs can now throw grenades with **RB / G**, using the same two-per-life inventory that spies steal from. Grenades follow an arc, bounce and detonate after 2.9 seconds; solid cover blocks blast damage. Y remains draw/holster. See CHARACTER_PLAYTEST.md for throw restrictions and supply behavior.

## Warehouse controller additions — November 7

A mounts a nearby rope for spies; left stick climbs up/down, neutral holds and B drops. At the top, a 3.2-second mantle plants the hands, pulls the chest up, braces a knee and brings the trailing leg inside, then hands off to matching four-point crawl/idle. Rope poses follow height traveled, with alternating planted boot grips. Merc A remains an ordinary jump. RB/G starts a merc overhand grenade throw: the hand prop releases at 0.42 seconds, consumes one shared grenade and recovers by 0.97 seconds. First-person arms and the remote body share that release beat. Y remains draw/holster.

The merc HUD uses a segmented aiming reticle, movement/recoil spread, hit feedback and a short audible-footstep bearing cue. See [WAREHOUSE.md](WAREHOUSE.md) for provenance, rebuild steps and focused playtest checks.
