# Character and equipment playtest

Open `StealthPrototype.uproject`, open `/Game/Maps/Prototype`, and press Play with one player for solo practice. Connect the Xbox controller and click the game window. The spy is third person; the merc is first person. Temporary role switching and appearance view are restricted to practice.

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
| Taser / merc fire / unarmed spy takedown | Left click | Right trigger |
| Fire selected spy gadget | G | Right bumper |
| Aim equipped weapon | Right mouse | Left trigger |
| Hold to hack as spy | E | X |
| Enter / leave deployed camera | C | Left bumper |

The merc can jump normally. He cannot catch ledges, vault, hang or climb. Spy traversal retains the existing marked-ledge behavior. A successful spy traversal holsters the launcher.

Spy Y / Q toggles **hands ↔ taser launcher**. Gadget selection is independent; sticky camera is currently the selected gadget, fired with **RB / G** while the launcher is drawn. Drawing takes 0.7 seconds and the aiming reticle appears when the weapon is ready. The launcher moves from the shoulder holster into a two-handed pose. RT / click always fires the taser with the launcher drawn; RB / G launches the selected gadget without holstering or switching weapons. With empty hands, RT retains the rear-only takedown. The taser has a 12 m trace range measured from the aiming view and stuns a merc for three seconds without health damage. Sticky cameras attach to blocking geometry, last up to 60 seconds, and can be viewed with LB / C. Deploying a new camera replaces the previous one. Movement and firing are blocked while watching its feed; LB / C returns to the character.

Merc Y toggles between the carbine and holstered hands. The supplied carbine is now a 24,000-triangle skeletal weapon with grip/muzzle helper bones and a short recoil animation. Owner-only first-person arms share the merc body pose; other players see the world weapon. Aim adjusts field of view and viewmodel placement. Shooting and taser/camera traces use the aiming view with a second check from the weapon side to block shots through nearby cover. Prototype weapons do not yet have ammunition management or reload animations.

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
