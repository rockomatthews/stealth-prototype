# Specialty takedowns

X establishes the normal rear hold. Tap RT for the quick lethal neck snap. Hold RT for 0.5 seconds to select the specialty from the merc's actual grenade stock. Y remains exclusively draw/holster.

## Grenade available

The spy steals one grenade at 0.55 seconds, pulls the pin at 1.05, conceals it inside the waistband at 1.90, shoves the merc and releases the hold at 2.80. The original 2.9-second fuse runs from pin pull: detonation is at 3.95 seconds after the sequence starts, leaving approximately 1.15 seconds of player-controlled escape. The merc then panics and tries to retrieve it; no input removes the grenade. The blast follows his animated pelvis/waist and kills him. Nearby players, including the spy, can take blast damage; solid cover blocks ordinary radial damage.

An interruption before the pin is pulled cancels that grenade. After pin pull but before insertion, an interrupted hold drops a live grenade. After insertion, it remains in the merc's waistband even if the spy releases, takes damage or dies. Round reset invalidates old explosives. Cosmetic flash and flying equipment fragments are original prototype effects, not a finished gore system.

## No grenades available

Both specialties begin in the same close rear neck hold. The spy makes a small hop onto the merc's back and crosses his ankles around the waist and holds the choke for five seconds before lethal strangulation. The merc retains ordinary predicted movement, turning, first-person aiming, shooting, weapon switching and RB grenade throwing (if ammunition becomes available). The supply check chooses the move once; it does not continually change during a choke. Ordinary rear holds still prevent combat.

At five seconds strangulation kills the merc. A paired forward collapse starts at that moment: the spy opens the leg lock, braces and gets up while the merc falls. The merc remains visibly down until the normal five-second respawn; the drop-attack knockout and recovery shield remain separate mechanics. Another merc can damage the spy to interrupt the choke; no delayed knockout is scheduled after interruption. B lets the spy release. Geometry can interrupt the rider's movement instead of pushing him through a wall. Grab-partner voice remains automatic until the hold ends; private team voice returns afterward.

## Review and verification

Run `python3 Scripts/run_specialty_acceptance.py` with the project open and local MCP enabled. The current suite stages its players in the Warehouse. `run_finisher_acceptance.py` delegates to that suite, replacing obsolete kick-finisher expectations. Source assets and reproducible original animation authoring are in `Art/Grab` and `Scripts/prepare_grab_animations.py`.

`Scripts/review_specialty.py choke --setup --record` and the equivalent `grenade` command capture actual four-client warehouse gameplay from a fixed side camera. These are rendered gameplay previews, not concept art. Physical-controller feel and console hardware still require a human playtest.

## Presentation revision, November 10, 2026

The merc rifle uses a 0.75 body scale (about 66 cm overall) and physical palm contacts on the pistol grip and underside of the handguard. The choke's automatic transitions preserve the drawn rifle through the collapse. Controller Y remains draw/holster; X grabs and tap/hold RT selects the finisher. Source poses include finger/thumb closures.

The derived spy mesh replaces the irregular planar goggle-hole cap with fitted cloth geometry. Original imported character files remain intact. This remains prototype character art, with automatic skinning and limited facial detail.

The planted explosion replaces the glowing sphere and cubes with 11 textured fragments derived from the existing merc, closed cut surfaces, a short flash, soft smoke/dust and cosmetic physics. Fragments never collide with pawns or weapon traces. The explosive's original fuse and authoritative damage rules remain. Effects clear on round epoch changes and expire after eight seconds.

Updated recordings use `Scripts/review_specialty_polish.py`, including the initial neck hold and complete follow-through. Four-client captures use a 960x540 host and 320x180 supporting client windows. Solo inspection is required before capture; `Scripts/review_presentation.py` verifies controller inspection mode so an observer camera does not rotate the displayed rifle.

## Contact repair, evening revision

Pose generation now uses repaired derived body meshes from `Art/ContactCharacters`. `Scripts/repair_contact_skin.py` detects extreme deformed-edge stretch from the original character meshes, separates the fused bridges, and seals the resulting local boundaries. `Scripts/review_pair_geometry.py` renders diagnostic source poses from multiple angles; these offline renders are not gameplay evidence.

The forearm hold reaches around the front of the merc neck. The collapse preserves the rotated leg chain rather than resetting the feet to standing orientation, and the spy's bracing targets are outside the fallen merc. Rifle support fingers wrap across the handguard; the dedicated first-person shoulder pose keeps sleeve ends outside the visible view and retains reachable hand targets.

The independent goggle assembly now uses clean binocular housings instead of the jagged region extracted from the fused scan. The full cloth covering has actual eye openings. Blast presentation adds a short emissive fire burst and ballistic blood spray with surface deposits; cosmetic particles do not block gameplay collision. Original source imports remain unchanged.
