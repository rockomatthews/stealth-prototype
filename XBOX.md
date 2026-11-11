# Xbox target and controller workflow

The current console target is Xbox Series X|S. Keep portable gameplay and Enhanced Input on Mac; build and validate console releases through an approved Windows/Xbox development environment. A next-generation Xbox target requires its actual available SDK and Epic support; no unreleased hardware compatibility is claimed.

## Prototype controller layout

| Xbox control | Spy | Merc |
| --- | --- | --- |
| Left stick | Analog movement; up/down on rope, neutral holds | Analog movement |
| Right stick | Third-person look | First-person look |
| A | Jump, catch marked ledge, vault, climb from hanging; mount rope | Jump; no ledge grabs or climbing |
| B | Toggle crouch; drop during ledge/rope traversal | Toggle crouch |
| X | Rear grab with empty hands; hold to hack terminal | Unused |
| RT press | Start rear hold with hands; finish held merc; taser when drawn | One shot per press |
| Hold LT | Aim equipped launcher | Aim: narrower FOV and reduced look sensitivity |
| Y | Hands ↔ taser | Equip / holster carbine |
| Right bumper | Fire selected gadget | Throw grenade (shared supply with spy theft) |
| D-pad Down | Select sticky camera / tracking dart; preserve weapon state | Unused |
| D-pad Up | Goggles and night vision | Flashlight |
| D-pad Left | Appearance view in practice | Appearance view in practice |
| Left bumper | Enter / leave deployed sticky camera | Unused |
| D-pad Right | Switch role in solo practice only | Switch role in solo practice only |

Both sticks use a radial dead zone (default 0.18; full response at 0.95). Look uses degrees per second, independent of frame rate. Blueprint defaults expose yaw/pitch rate, dead zone, invert Y and aim sensitivity. Keyboard/mouse remain supported; HUD hints follow the most recent active input.

Connect a compatible Xbox controller to macOS by Bluetooth or USB. Start one-player PIE, click its game window, and move a stick. Shift+F1 releases mouse focus. The controller drives the focused PIE participant; four PIE clients do not establish four physical-controller routing or split-screen support.

## Console work still required

- Approved Xbox developer status, Epic console access, appropriate Xbox development hardware, and a supported Windows development machine.
- Install compatible Xbox console GDK extensions and Unreal console platform support through the authorized channels. Public Xbox-on-PC plugins alone do not produce an Xbox console build.
- Validate console packaging, performance on both Series S and Series X, user/device pairing, controller disconnect/reconnect, suspend/resume, safe-area UI, online/session services and certification requirements on actual hardware.
- Keep restricted platform code, SDKs and credentials outside the public repository. No console build, enrollment, purchase or certification has occurred in this milestone.

Official references checked October 19, 2026:

- [Epic Xbox console access](https://dev.epicgames.com/documentation/unreal-engine/xbox-development-in-unreal-engine?lang=en-US)
- [Microsoft development-PC requirements](https://learn.microsoft.com/gaming/gdk/docs/gdk-dev/get-started/overviews/set-up-dev-pc)
- [Unreal 5.8 public Xbox-on-PC plugins](https://developer.microsoft.com/en-us/games/articles/2026/06/building-xbox-games-with-unreal-engines-new-gdk-plug-ins/)

## Original Xbox Versus reference

Use Chaos Theory's Xbox Versus layout as the classic reference. The current project preserves the user's A jump, Y draw/holster and D-pad Up equipment preferences.

| Original button | Spy | Merc |
| --- | --- | --- |
| A | Interact/grab/assist | Interact/charge/slam |
| B | Crouch; hold roll | Crouch |
| X | Draw/holster | Reload/fire-rate |
| Y | Jump | Jump |
| RT | Shocker; unarmed quick-slot 2 | Gunfire |
| LT | Gadget; unarmed quick-slot 1 | Secondary fire |
| Left stick | Move | Move |
| Hold left-stick click | Inventory | Inventory |
| Right stick | Camera | Aim |
| Double-click right stick | Binoculars | Scope |
| D-pad Up | Camera feed | Flashlight |
| D-pad Left | Night vision | Motion vision |
| D-pad Right | Thermal | EMF |
| D-pad Down | Binding unverified | Laser |
| White | Cooperative move | Not listed |
| Black | Enemy communications, contextual | Enemy communications, contextual |
| Back / Start | Map / menu | Map / menu |

Scopes repurpose Up/Down for zoom. Merc LT focuses while scoped. The shocker has rechargeable energy; gadget choice is separate from drawing it. Selected devices launch through the weapon's secondary function.

Sources: Ubisoft Xbox manual, visually checked [scan 32](https://www.manualslib.com/manual/379207/Ubisoft-Splinter-Cell-Chaos-Theory.html?page=32), [33](https://www.manualslib.com/manual/379207/Ubisoft-Splinter-Cell-Chaos-Theory.html?page=33), [43](https://www.manualslib.com/manual/379207/Ubisoft-Splinter-Cell-Chaos-Theory.html?page=43), [44](https://www.manualslib.com/manual/379207/Ubisoft-Splinter-Cell-Chaos-Theory.html?page=44), [45](https://www.manualslib.com/manual/379207/Ubisoft-Splinter-Cell-Chaos-Theory.html?page=45). These are Versus bindings; campaign, PlayStation versions and community PC layouts have different mappings. The spy laser shortcut remains unverified in the inspected retail scan, so no modern equivalent is assigned from inference.

## Equipment catalogue and project priorities

Ubisoft's original [spy equipment page](https://static-wordpress.ubisoft.com/ubisoft.co.jp/static-files/splintercell3/equipment/multi/index2.html) lists sticky cameras, spy bullets, alarm snares, smoke, flashbangs, chaff, a heartbeat sensor and camouflage. Cameras support distraction and gas; chaff disrupts electronics; tracking rounds provide enemy location information. Sensors and worn equipment require separate use behavior from fired payloads.

The [merc equipment page](https://static-wordpress.ubisoft.com/ubisoft.co.jp/static-files/splintercell3/equipment/multi/index.html) lists flares, a close-range shock device, mines, camera-network access, spy detection, a gas mask, supply backpack and frag grenades. Its gas mask has limited duration; the backpack supports sharing supplies. These tools establish counterplay between reconnaissance, disruption and defense.

Recommended implementation order for our original prototype:

1. **Weapon and gadget separation, implemented now:** Y/Q toggles hands/shocker; RT/click fires the shocker; RB/G fires the selected gadget. Sticky camera and Spy Bullets are implemented spy gadgets, selected with D-pad Down / R. LB/C opens its feed. LT remains modern aim, making RB our equivalent of the original secondary-fire input. NV/flashlight remain on D-pad Up. Gadget fire requires the launcher drawn and shares its firing cooldown; neither gadget fire nor camera viewing changes the weapon selection.
2. **Selected gadget inventory, implemented November 5:** D-pad Down / R cycles camera and Spy Bullets independently of Y/Q. Each life starts with three cameras and four Spy Bullets. HUD shows selection and both counts, including EMPTY; the server rejects empty fire. A valid camera attachment spends one charge, replaces the previous camera, and failed attachments spend nothing. Every accepted tracking shot spends a round, including misses. Death/round reset restore supplies; holstering, inspection and practice role switching do not. Starting supplies are exposed in Blueprint defaults. No inert gadget entries are displayed.
3. **Complete the existing pair:** add shocker charge/recharge and temporary effects on suitable electronic map devices; camera look/zoom, night vision and gas/distraction controls are now implemented. Balance camera lifespan, ammunition and stun recovery together. [a contemporary first-hand Xbox preview](https://www.gamespot.com/articles/splinter-cell-chaos-theory-updated-hands-on/1100-6118502/) documents shocker disruption of surveillance equipment.
4. **Expand payloads in a testable sequence:** dual-use Spy Bullets for reconnaissance (implemented November 5); alarm snare for audio deception; smoke for movement cover; flashbang for escape; chaff after mines/sensors and detection visions exist. Each needs collision, server validation, finite resources, replicated feedback, duration and a merc countermeasure. Beyond Spy Bullets, these payloads remain planned.
5. **Merc combat and counters:** ammunition/reload, automatic/burst behavior, close-range defensive strike, then detection modes and mines. Keep normal jumping and reject spy traversal. Tune the weapon choices around sightlines and cover before adding more art.
6. **Classic interaction and stealth feel:** contextual interaction/grabs rather than immediate takedown alone, slow analog movement and meaningful sound, roll/drop behavior, readable detection feedback, teammate assistance and role-specific tutorials. X supports contextual rear grabbing. During a hold, tap RT for the quick finish or hold RT for the grenade/back-choke specialty. Hacking expansion is deferred; controller prompts must describe the current action.

The current build remains a movement/equipment prototype. It has one cumulative-hack terminal, a three-minute 2v2 round, practice switching, replicated climbing/combat, taser stun, camera placement/viewing and dual-use Spy Bullets with finite gadget supplies. It does not yet reproduce the original objective catalogue, equipment economy, detection systems or full close-combat interactions. Internet Host/Join and separate-machine testing remain deferred.

## October 30 stop and next session

The user approved the implementation order above. Resume with gadget selection and ammunition counts, then camera look/zoom/distraction/gas, additional spy payloads, and merc ammunition/reload/detection counterplay. Keep Y exclusively draw/holster and D-pad Up night vision/flashlight. Do not begin internet Host/Join until movement and equipment feel have been playtested.

Today's control-separation build passed 77/77 automated checks. The project was saved for shutdown; physical-controller evaluation remains pending. See TEST_RESULTS.md for the evidence and limitations.

## November 5 inventory behavior

Spy Bullets are a prototype hitscan payload with a 25 m maximum range. A hit on a living merc marks him on the spy radar for 12 seconds; a wall hit places a 10 m area sensor for up to 45 seconds. Mercs see a warning when tagged. It does not damage or stun. Tags and sensors supply radar information through cover without rendering a character silhouette. RT remains taser fire regardless of selected gadget; taser energy/recharge, merc magazines and reload are later work.

## Manual correction and camera controls

Rechecked the retail Xbox Versus manual before implementing camera controls. [Spy Bullets, scan 45](https://www.manualslib.com/manual/379207/Ubisoft-Splinter-Cell-Chaos-Theory.html?page=45) have two uses: attach to a merc to mark him on radar, or attach to a wall to detect mercs in the surrounding area. Our previous direct-hit-only tracking dart was incomplete; both uses now work on the spy radar. Ubisoft lists the [Spy Finder as merc equipment](https://static-wordpress.ubisoft.com/ubisoft.co.jp/static-files/splintercell3/equipment/multi/index.html); its [spy catalogue](https://static-wordpress.ubisoft.com/ubisoft.co.jp/static-files/splintercell3/equipment/multi/index2.html) separately lists Spy Bullets and the heartbeat sensor. These are different devices.

The manual also describes communications interception from tagged mercs. Spy Bullet interception of the opposing team radio is not implemented; ordinary team voice remains private and grab voice requires an active hold. Do not claim complete historical parity. The 12-second attached tag, 10 m wall-sensor radius, 45-second sensor lifetime and 30 m radar display are our tunable prototype balance values, not verified original specifications. Wall sensors are removed on owner death or role change and at round reset.

In a sticky-camera feed, right stick looks, held LT/RT zoom in/out, X emits distraction noise, B releases gas, Up toggles camera NV and LB exits. Y remains draw/holster and exits the feed. Outside the feed the existing combat and goggles controls remain. Noise and gas use server-validated ownership/view state; noise plays from the deployed camera on all clients. Each camera has one gas release, with a visible puff and spatial audio. The current gas uses a 3 m radius, a five-second non-damaging stun and a solid-cover check; it does not affect spies. These timings and our button mapping are adaptations. Thermal camera vision, enemy voice interception and merc gas-mask counterplay remain pending.

## Mandatory voice and sustained rear grab

User requirement, November 5: teammate voice is mandatory for both teams, and a spy must be able to speak to the merc they are holding from behind. These are required for the first human multiplayer playtest and take priority over expanding the remaining gadget catalogue.

Required behavior:

- Team voice lets spies speak privately with their spy teammate and mercs with their merc teammate.
- A successful rear grab establishes a server-authorized held-victim state rather than immediately executing the existing takedown. The spy can hold, release or finish the encounter through explicit contextual actions.
- While the hold is valid, the grabbing spy and held merc can hear each other through a separate pair channel. Ordinary team speech retains its team routing; grabbing does not expose either team's radio to the opposing team.
- Release, takedown, either player's death, disconnect, respawn and round reset immediately close the pair channel and clear the grab. No stale recipient may continue receiving audio.
- Team voice uses open microphone by user preference. Grab-partner speech opens automatically for both players for the entire hold; View/M mutes the microphone. No stick-click talk binding is used. The HUD shows the route, incoming activity and capture/device status. Y remains weapon draw/holster.
- Validate routing with four participants and actual live speech on two separate Apple Silicon Macs. Automated flags, generated tones or a compiled voice module alone do not establish a working microphone-to-speaker conversation. Include headset/device changes, mute and reconnect behavior in the human test.

Current implementation status: server-validated sustained grabs, private team voice and bidirectional grab voice are implemented. Team voice defaults to open microphone; grab voice opens automatically while held and returns to team speech afterward. Game connections carry bounded Opus frames only to authorized recipients. Round epochs and pair tokens reject stale audio and clear playback on release. Local capture stops and buffers are cleared when muted or changing channels. Normal live capture is disabled in automated/multi-client PIE tests; the separately invoked device-open probe opens and closes the microphone without reading any samples.

The core implementation is not yet a verified human conversation: real microphone/speaker operation between separate Macs, headsets, internet conditions and Xbox platform communication permissions remain acceptance requirements. Front strikes, merc gun-butt/charge and production grab animation polish also remain pending.

## Paired movement and finishers — November 6

X/E grabs from behind with hands holstered. The spy can slowly drag (85 cm/s) and turn the captive with the normal movement/look sticks. B/Ctrl releases, including aborting a finisher before impact. Y/Q stays draw/holster only; D-pad Up stays goggles/flashlight.

Tap RT for the quick neck snap. Hold RT for 0.5 seconds to select the longer inventory-dependent move: steal/pull/plant a real merc grenade into the waistband, shove away and release at 2.8 seconds, or mount a five-second back choke when no grenades remain. The back choke is nonlethal: the merc can walk, turn, aim, fire and throw while carrying the spy, then becomes unconscious and uses the existing protected recovery. The planted-grenade victim instead panics and reaches into the waistband until the live fuse detonates at his waist. The spy remains vulnerable; another merc can shoot and rescue their partner. A pin-pulled grenade keeps its fuse after interruption, with friendly blast damage and geometry checks. Supply starts at two per merc life; RB / G now throws from that same supply, with gravity, bounces and a 2.9-second fuse. Holding RB throws once; re-press after the 0.65-second cooldown. Blocked release, restraint, stun and death prevent throwing without spending ammunition. Y stays draw/holster.

These use original paired prototype clips and server-controlled damage/timing. They need physical controller and human animation/feel review; they are not finished cinematic animation.

## Aerial knockout reliability

A spy falling onto the upper part of a merc triggers a nonlethal knockout automatically; no additional controller button is needed. Server CharacterMovement landing/impact collisions resolve the contact during movement simulation. Side collisions, upward movement, other spies, solid intervening geometry and inactive/restrained players do not qualify. A one-second attacker cooldown and the merc’s active knockout state prevent duplicate awards from collision callbacks or replayed moves. The six-second knockout, shared equipment rules and normal respawn behavior are retained.

`Scripts/run_knockout_acceptance.py` exercises repeated recovery, high-speed falls and network replication with temporary editor frame caps down to 6 FPS. It records measured frame times and restores the prior cap. Requested 30/60 FPS caps are upper bounds, not proof the Mac maintained those rates. Run the same landing, moving/crouched-target, latency and frame-hitch cases on approved Xbox hardware before claiming console validation.

## Recovery protection

Mercs automatically charge a visible electrical shield at the end of a drop knockout. The get-up transition lasts 0.8 seconds; protection lasts three seconds from its start, leaving about 2.2 seconds of normal movement and firing protected from rear grabs and repeat drop knockouts. Head landings are pushed away. A countdown communicates the window in first person. No controller binding changes. See `RECOVERY_SHIELD.md` for rules and tuning.
