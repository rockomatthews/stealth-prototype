# Gameplay reference and controller priorities

The user's reference is [CovertOwl's Enhanced Warehouse match](https://www.youtube.com/watch?v=61oqwG5kcy0). The marked times are starting points for watching sequences, not isolated poses. It shows PC input prompts; our game uses Xbox controller controls. This recording is an Enhanced PC version, so visible behavior is useful evidence but does not establish every retail Xbox rule or numerical threshold.

## Observed sequences

- [0:33 onward](https://www.youtube.com/watch?v=61oqwG5kcy0&t=33s): supported ladder/duct access, followed by crouching, night/thermal vision changes, camouflage use and equipment changes.
- [0:50 onward](https://www.youtube.com/watch?v=61oqwG5kcy0&t=50s): thermal presentation and movement through stacked cover; selected equipment and visible meters remain separate.
- [1:10 onward](https://www.youtube.com/watch?v=61oqwG5kcy0&t=70s): box-edge traversal, elevated routes, and smoke selection.
- [3:33 onward](https://www.youtube.com/watch?v=61oqwG5kcy0&t=213s): elevated vent approach followed by a dedicated sticky-camera view with zoom and gas controls.
- [11:00 onward](https://www.youtube.com/watch?v=61oqwG5kcy0&t=660s): merc role, substantial utility rifle, amber weapon display, directional reticle cues, flashlight and separate gadget stock.
- [11:17 onward](https://www.youtube.com/watch?v=61oqwG5kcy0&t=677s): proximity-mine placement is confirmed by an activation message and stock decrement.
- [13:00 onward](https://www.youtube.com/watch?v=61oqwG5kcy0&t=780s): mask overlay/meter, severe visibility disruption, gunfire, recovery/respawn and later close combat. The spectator tip explicitly describes silent crouching, sneaking and climbing in Enhanced Versus.

These are visual observations, not a claim to have measured original detection ranges, camouflage limits, damage values or audio levels from the video. Weapon/gadget quantities visible in this PC match are not automatically our balance defaults.

## Locked project decisions

- Controller first: Y exclusively draws/holsters, X grabs, D-pad Up toggles goggles/night vision or flashlight. Preserve open-mic team voice and automatic grab-pair voice. Do not copy mouse/keyboard prompts from the recording.
- Hacking and objective expansion are deferred by the user. Keep work focused on movement, combat, gadgets, detection, animation and weapon presentation. Existing development objective code is not being expanded.
- Keep our daylight warehouse readable; night vision is primarily useful inside vents, as requested. This is an intentional lighting choice even when the reference is dark.
- Keep the user's original character designs and independent flip goggles with two lit lenses. Use reference gameplay for behavior and readability.

## Implemented in this revision

The new merc utility rifle has a broad rounded body, low sights, original amber ROF/SEMI display, functional weapon-mounted flashlight, skeletal recoil and separate first-person/world presentation. Its laser housing is visual equipment; no new laser detection mechanic is claimed. Firing remains the existing semi-auto prototype; the display says SEMI accordingly. Automatic fire, finite rifle magazines and reload remain separate work.

The support hand uses authored grip poses plus runtime two-bone IK, including crouch/falling/remote poses. Camera-only sleeves follow the forearm rather than rotating rigidly with the palm. The merc reticle uses larger amber broken double rings, a center point and fading directional movement arcs.

Crouching and low-speed analog movement no longer emit world footsteps or renew the merc's step-based direction cue. Running still produces distance/occlusion-limited cues. Rope/ledge traversal already avoids the grounded footstep path. This is a directional cue based on admitted footsteps, not a new always-visible enemy-position radar or wall-revealing vision mode.

Specialty hold-RT actions are described in SPECIALTY_TAKEDOWNS.md. They are original extensions requested by the user, not claims about finishers present in the reference game.

## Remaining gameplay priorities

1. **Camouflage:** slow concealed movement is required. Define depletion/recharge, running cancellation/lockout and action interruptions, then replicate the material state and movement restriction on the server. [Ubisoft's spy equipment description](https://static-wordpress.ubisoft.com/ubisoft.co.jp/static-files/splintercell3/equipment/multi/index2.html) confirms running defeats the camouflage effect. Camouflage is not implemented yet.
2. **Merc detection:** distinguish directional movement cues, minimap contacts, motion vision and electronic detection. Verify each mode's visibility, occlusion and speed rules before adding it. Current footsteps and Spy Bullet radar do not constitute the full detection suite.
3. **Merc mines:** start with the demonstrated proximity mine, finite supply independent of hand grenades, valid surface placement, arm delay, replicated feedback and tested spy counterplay. Mine placement is not implemented yet.
4. **Counterplay pairs:** alarm snares, smoke, flashbangs and gas-mask protection. Each needs real controller actions, finite stock or duration, geometry checks, feedback and remote-client validation. These are not implemented yet. Sticky-camera gas/distraction and Spy Bullets already exist.
5. **Rifle behavior:** finite magazine/reserve ammunition, reload and automatic fire with authoritative cadence; then decide which extra weapon modes and tools belong in the first controller playtest.
6. **Further animation polish:** tighten equipment contact through aim extremes, recoveries and damage reactions; review both participants' perspectives. Physical-controller feel remains a human playtest.

Do not add inert gadget-selection entries or advertise planned tools as working.
