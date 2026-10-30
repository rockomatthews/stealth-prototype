# Xbox target and controller workflow

The current console target is Xbox Series X|S. Keep portable gameplay and Enhanced Input on Mac; build and validate console releases through an approved Windows/Xbox development environment. A next-generation Xbox target requires its actual available SDK and Epic support; no unreleased hardware compatibility is claimed.

## Prototype controller layout

| Xbox control | Spy | Merc |
| --- | --- | --- |
| Left stick | Analog movement | Analog movement |
| Right stick | Third-person look | First-person look |
| A | Jump, catch marked ledge, vault, climb from hanging | Jump; no ledge grabs or climbing |
| B | Toggle crouch; drop during traversal | Toggle crouch |
| Hold X | Hack nearby visible terminal; release stops | Unused |
| RT press | Rear takedown with hands; fire taser when drawn | One shot per press |
| Hold LT | Aim equipped launcher | Aim: narrower FOV and reduced look sensitivity |
| Y | Hands ↔ taser | Equip / holster carbine |
| Right bumper | Fire selected gadget (sticky camera currently) | Reserved for future merc gadgets |
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

1. **Weapon and gadget separation, implemented now:** Y/Q toggles hands/shocker; RT/click fires the shocker; RB/G fires the selected gadget. Sticky camera is currently the only implemented spy gadget. LB/C opens its feed. LT remains modern aim, making RB our equivalent of the original secondary-fire input. NV/flashlight remain on D-pad Up. Gadget fire requires the launcher drawn and shares its firing cooldown; neither gadget fire nor camera viewing changes the weapon selection.
2. **Selected gadget inventory:** add a loadout, visible gadget name/count, inventory selection and ammunition validation. Keep selection separate from the weapon state and let one launch action dispatch the chosen payload. Design a selector once at least two gadgets work; do not expose inert entries.
3. **Complete the existing pair:** add shocker charge/recharge and temporary effects on suitable electronic map devices; add useful camera look/zoom and a clearly signaled gas/distraction action. Balance camera lifespan, ammunition and stun recovery together. [a contemporary first-hand Xbox preview](https://www.gamespot.com/articles/splinter-cell-chaos-theory-updated-hands-on/1100-6118502/) documents shocker disruption of surveillance equipment.
4. **Expand payloads in a testable sequence:** tracking dart for reconnaissance; alarm snare for audio deception; smoke for movement cover; flashbang for escape; chaff after mines/sensors and detection visions exist. Each needs collision, server validation, finite resources, replicated feedback, duration and a merc countermeasure. These payloads are planned, not implemented.
5. **Merc combat and counters:** ammunition/reload, automatic/burst behavior, close-range defensive strike, then detection modes and mines. Keep normal jumping and reject spy traversal. Tune the weapon choices around sightlines and cover before adding more art.
6. **Classic interaction and stealth feel:** contextual interaction/grabs rather than immediate takedown alone, slow analog movement and meaningful sound, roll/drop behavior, readable detection feedback, teammate assistance and role-specific tutorials. Current X only hacks and unarmed RT performs a rear takedown; these differ from the original contextual system.

The current build remains a movement/equipment prototype. It has one cumulative-hack terminal, a three-minute 2v2 round, practice switching, replicated climbing/combat, taser stun and camera placement/viewing. It does not yet reproduce the original objective catalogue, equipment economy, detection systems or full close-combat interactions. Internet Host/Join and separate-machine testing remain deferred.

## October 30 stop and next session

The user approved the implementation order above. Resume with gadget selection and ammunition counts, then camera look/zoom/distraction/gas, additional spy payloads, and merc ammunition/reload/detection counterplay. Keep Y exclusively draw/holster and D-pad Up night vision/flashlight. Do not begin internet Host/Join until movement and equipment feel have been playtested.

Today's control-separation build passed 77/77 automated checks. The project was saved for shutdown; physical-controller evaluation remains pending. See TEST_RESULTS.md for the evidence and limitations.
