# Character and equipment playtest

Open `StealthPrototype.uproject`, open `/Game/Maps/Warehouse`, and press Play with one player for solo practice. Connect the Xbox controller and click the game window. The spy is third person; the merc is first person. Temporary role switching and appearance view are restricted to practice.

| Action | Keyboard / mouse | Xbox controller |
| --- | --- | --- |
| Select spy / merc | 1 / 2 | D-pad Right cycles roles |
| Switch role | Tab | D-pad Right |
| Appearance view | V | D-pad Left |
| Move / look | WASD / mouse | Left / right stick |
| Jump | Space | A |
| Crouch / spy drop | Left Ctrl | B |
| Switch weapon | Q | Y |
| Night vision as spy | N | D-pad Up |
| Flashlight as merc | F | D-pad Up |
| Attack / tap snap / hold extended finish | Left click | Right trigger |
| Fire spy gadget / throw merc grenade | G | Right bumper |
| Select spy gadget | R | D-pad Down |
| Aim equipped weapon | Right mouse | Left trigger |
| Rear grab / hold to hack as spy | E | X |
| Enter / leave deployed camera | C | Left bumper |

The merc can jump normally. He cannot catch ledges, vault, hang or climb. Spy traversal retains the existing marked-ledge behavior. A successful spy traversal holsters the launcher.

Spy Y / Q toggles **hands ↔ taser launcher**. Gadget selection is independent; D-pad Down / R cycles sticky camera and Spy Bullet, fired with **RB / G** while the launcher is drawn. Drawing takes 0.7 seconds and the aiming reticle appears when the weapon is ready. The launcher moves from the shoulder holster into a two-handed pose. RT / click always fires the taser with the launcher drawn; RB / G launches the selected gadget without holstering or switching weapons. With empty hands, X/E is the rear-grab input. Once holding, tap RT/left click for a quick neck snap, hold it for 0.5 seconds to commit to the longer inventory-dependent finisher, or press B/Ctrl to release alive. The taser has a 12 m trace range measured from the aiming view and stuns a merc for three seconds without health damage. Sticky cameras attach to blocking geometry, last up to 60 seconds, and can be viewed with LB / C. Deploying a new camera replaces the previous one. Movement and firing are blocked while watching its feed; LB / C returns to the character.

Merc Y toggles between the carbine and holstered hands. The supplied carbine is now a 24,000-triangle skeletal weapon with grip/muzzle helper bones and a short recoil animation. Owner-only first-person arms share the merc body pose; other players see the world weapon. Aim adjusts field of view and viewmodel placement. Shooting and taser/gadget traces use the aiming view with a second check from the weapon side to block shots through nearby cover. Prototype weapons do not yet have ammunition management or reload animations.

The spy's original binocular geometry is separate from the body. D-pad Up / N rotates it about a head-following hinge, enables both green emissive lenses when lowered, and enables night vision. Raised goggles have dark lenses. Goggle state and equipped weapon selection replicate to the other PIE clients. The launcher and goggles are separate derived assets; original Meshy sources and previous character rigs remain untouched.

Appearance view adds a local light and permits orbiting while idle. Toggle it off to judge the normal camera and reticle. Check movement, crouching, jump/landing, spy traversal, weapon draw/holster, merc aim, and goggles in both states. Look closely at shoulders, elbows, wrists, equipment intersections and camera comfort. These remain prototype skin weights and authored equipment poses; production hand/finger cleanup and animation polish are ongoing art work.

## Assets and rebuild

- Character rigs: `Content/Characters/Meshy`, plus derived spy `Content/Characters/Equipment/SK_SpyEquipment`
- Equipment, arms, draw and recoil animations: `Content/Characters/Equipment`
- Original rig sources: `Art/RiggedCharacters`
- Derived equipment sources: `Art/Equipment`
- Blender equipment build: `Scripts/prepare_equipment.py` (Blender 4.5)
- Full editor equipment import: `Scripts/import_equipment.py` or project MCP `import_equipment`

A fresh public checkout needs the licensed mannequin skeleton and animation clips migrated as described in README.md. Rebuilding the carbine from scratch needs the original local Meshy source; the derived FBX and runtime assets are included. Gameplay does not use Mover.

## Validation

See TEST_RESULTS.md for the dated final result. Evidence and actual runtime observations are local under `Saved/EquipmentQA` and `Saved/acceptance.json`. Controller automation injects Xbox events through Enhanced Input and gameplay RPCs. It does not replace physical-controller testing, separate-machine internet testing or Xbox console validation. Internet Host/Join remains deferred.

## Gadget selection and supplies — November 5

- D-pad Down / R cycles sticky camera and Spy Bullet. Select with the launcher drawn or holstered; Y/Q only draws or holsters it.
- RB / G fires the selected gadget while drawn. RT / left click remains the taser.
- Start each life with three cameras and four Spy Bullets. Supplies appear on the HUD; empty gadgets cannot fire. Holstering and practice role switching preserve remaining supplies.
- Cameras consume a charge only on attachment; each new attachment replaces the previous camera. LB/C still opens/closes its feed.
- Spy Bullet shots spend a round. A merc hit marks the target on the spy team radar for 12 seconds; a wall hit creates a 10 m area sensor for up to 45 seconds. No damage or stun is applied.
- Check selection, empty feedback, role switching, and Y draw/holster with your physical controller. Multiplayer automation does not establish physical controller feel or internet readiness.

## Sticky camera controller controls

Press LB / C to enter or leave the last deployed camera. While viewing it:

| Action | Xbox | Keyboard / mouse |
| --- | --- | --- |
| Pan / tilt | Right stick | Mouse |
| Zoom in / out | Hold LT / RT | Hold right / left mouse |
| Distraction noise | X | E |
| Release gas | B | Ctrl |
| Camera night vision | D-pad Up | N |
| Exit camera | LB | C |

Camera pan is limited to 85 degrees either side of its mount and tilt to 60 degrees. Zoom ranges from an 85 to 30 degree field of view. Noise is spatial sound emitted at the camera, with a two-second cooldown. Each deployed camera has one gas burst: mercs within 3 m and not behind solid cover are incapacitated for five seconds without health damage; spies are unaffected. Gas has a visible puff and audio cue. The camera HUD shows zoom and gas status. These are prototype tuning values, not claimed original-game statistics.

Movement, hacking and launcher firing are blocked in the feed. Y/Q only draws/holsters the launcher and returns to the character view. Camera expiry, replacement, death or stun restores the normal view. A fresh deployment costs one camera charge and includes a fresh gas charge.

## Sustained rear grab and private voice

Team voice defaults to **open microphone** and is delivered only to your teammate. A successful grab automatically switches outgoing speech for both participants to the private grab pair; no stick-click or talk button is used. Release, death, interruption, disconnect or round reset closes the pair and restores team speech. **View / M** is a master microphone mute, including during a grab. Delayed team packets from restrained players are rejected server-side. Incoming teammate speech may still be heard during a grab.

Approach a standing merc from behind with empty hands and press **X/E**. The server checks 1.5 m reach, rear angle, ground, sight and capsule clearance. A crouched spy stands only with headroom. The spy can **slowly move with LS/WASD (85 cm/s) and turn with RS/mouse**, dragging the merc; wall and floor checks constrain the pair. The victim cannot move, shoot, jump or draw. **B/Ctrl releases** alive; **Y/Q remains exclusively draw/holster** and cannot switch during a hold.

**Tap RT/left click:** an approximately 0.85-second classic neck snap. **Hold RT/left click for 0.5 seconds:** commit to the longer finisher. With grenades available, the spy takes one from the merc, pulls its pin, plants it at the waistband, then shoves the merc clear before the blast (approximately 3.8 seconds). With zero grenades, the merc is knocked onto hands and knees and kicked (approximately 3.1 seconds). These are original prototype paired animations, synchronized by server time; visual polish and contact alignment still need human review.

Mercs spawn with two grenades in replicated inventory. Theft consumes one at the pin-pull event; it is never free or refunded after arming. The grenade continues its fuse if a teammate damages or kills the spy, and can injure either team. Blast damage checks cover. Merc **RB / G throws immediately** along the aiming direction, with gravity and bounces and a 2.9-second fuse. Holding the button throws once; tap again after the 0.65-second cooldown to throw another. Throwing and spy theft spend this same count. Throwing works with the carbine drawn or holstered; Y never throws or replenishes grenades. Empty, grabbed, stunned and dead mercs cannot throw; obstructed release spends nothing. The rest of the merc gadget kit remains a later milestone. Spawn and round reset restore supply. Extended finishers require a clear, grounded landing corridor.

The spy stays vulnerable throughout every finisher, and cannot move while committed. B/Ctrl can abort before impact, releasing the merc alive; it never refunds an armed grenade. Positive damage to either participant breaks the hold. Before the final impact, this prevents a neck-snap/kick kill. An already armed grenade remains dangerous after interruption. Death, disconnect, pawn recreation and round end also clean up paired movement and voice; a round reset safely removes old-round grenades. Released characters recover their previous weapon with its normal draw delay. Front strikes and merc gun-butt/charge attacks remain separate pending work.

Live microphone input uses the Mac's default input; allow Unreal microphone access when macOS asks. Mute/unmute reopens the default device after a change. Voice packets use the existing game connection, Unreal's Opus codec and per-recipient playback; no extra voice account is needed. Headphones are recommended for open-mic testing because this prototype has no dedicated echo-cancellation layer. No speech is recorded to disk.

Normal live capture is disabled in automated and multi-client PIE sessions. A separate device-open check briefly opens/closes the microphone without reading or transmitting samples. Their routing tests inject generated tones through the real codec, network RPCs and playback queue. Current competitive rules require four clients. Test actual conversation using standalone instances on separate Macs; live speech, device behavior and internet quality need that human playtest. Internet Host/Join setup is still separate work. Xbox audio-provider integration, communications permissions and console validation remain pending.

## Warehouse actions

As spy, A near a rope mounts it; left stick up/down climbs and B drops. Hold neutral to hang. The top automatically crouches into the vent. Drop directly onto a merc from above for a six-second nonlethal knockout; it requires a clear landing, not merely falling nearby. Mercs can jump but cannot climb ropes. RB/G animates the merc grenade throw in both views; release occurs 0.42 seconds after starting, recovery at about 0.97 seconds. Y continues to draw/holster. See [WAREHOUSE.md](WAREHOUSE.md).

## Vent mantle review

As the spy, press A near a rope and hold left stick up. At the lip, watch for hands planting before the chest rises, right knee supporting the body, weight shifting forward and the trailing leg coming inside. The full mantle lasts 3.2 seconds and ends in matching four-point crawl idle. Center the stick to check there is no extra step; B should interrupt safely before entry finishes. Test a remote spy too. Judge contact, weight and camera comfort with the physical controller; automated checks do not establish finished animation quality.
