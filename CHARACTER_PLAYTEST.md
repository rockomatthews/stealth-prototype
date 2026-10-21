# Rigged character practice

The Meshy spy and masked merc now have separate skeletal meshes using the existing prototype animation skeleton. Both derived meshes contain 80,000 triangles, down from 1,767,257 and 2,101,917 respectively. Skin weights are limited to four influences per vertex. Original static models and source archives are preserved locally; the public repository includes the optimized rigged sources and runtime assets.

Open `StealthPrototype.uproject`, open `/Game/Maps/Prototype`, and press Play with one player. This starts practice mode.

| Action | Keyboard and mouse | Xbox controller |
| --- | --- | --- |
| Choose spy | 1 | D-pad Right switches roles |
| Choose merc | 2 | D-pad Right switches roles |
| Switch roles | Tab | D-pad Right |
| Toggle appearance view | V | D-pad Up |
| Move and look | WASD and mouse | Left and right sticks |
| Crouch or stand | Left Ctrl | B |
| Jump or traverse as spy | Space | A |
| Spy night vision | N | Y |
| Merc flashlight | F | Y |
| Aim as merc | Right mouse | Left trigger |

The merc normally uses first person. Appearance view moves the camera behind the body and adds a local inspection light so you can judge its silhouette, materials and movement. While standing still, move the mouse or right stick to orbit around either character. Toggle it off to return to the role's normal camera. This view, its light and role switching are restricted to practice mode. Movement speeds and the existing spy third-person camera remain independently tuned.

Check idle, walking, crouching, jumping, landing, vaulting and climbing. Watch the shoulders, elbows, hips, knees, wrists and equipment while moving. These are prototype skin weights transferred from a fitted mannequin; close-up finger articulation and production deformation cleanup remain art work. The source spy's goggles and back equipment are currently part of the skinned body, so the original separate proxy goggles are hidden to avoid duplicate equipment. The night-vision screen effect still works; independently hinged goggles and state-controlled lens emission require separating those accessories.

## Assets and rebuild

- Spy: `/Game/Characters/Meshy/Spy/SK_Spy`
- Merc: `/Game/Characters/Meshy/Merc/SK_Merc`
- Textures: original imported 2048 pixel maps under `/Game/Meshy/Imported_20261020`
- Blender and FBX sources: `Art/RiggedCharacters`
- Preparation: `Scripts/prepare_meshy_characters.py` in Blender 4.5 background mode
- Skinning and FBX export: `Scripts/rig_meshy_characters.py` in Blender
- Unreal import: `Scripts/import_rigged_characters.py` in a full editor session

For a fresh public checkout, first migrate the licensed mannequin skeleton and animation clips as described in README.md. Raw Meshy source files and high-poly character static imports remain local, so preparation scripts require those original sources; the included rigged FBX files and runtime assets do not require re-running preparation. The imported merc carbine is included as an art asset but is not yet equipped in gameplay.

The import script rebuilds only the derived skeletal meshes and checks for a shared skeleton and human-scale bounds. It does not replace the original static imports. Preparation requires the mannequin export at `Saved/ArtMigration/Prototype.fbx`, produced by the existing mannequin migration workflow.

## Verified on this Mac

The Development Editor build passed and the updated acceptance suite passed 50 of 50 checks. Coverage includes both actual runtime mesh paths, animated head scale and position, role switching, controller appearance view, normal role cameras, movement, crouching, traversal, four-client replication, combat, hacking, respawns and round reset. Controller checks inject Xbox inputs through Enhanced Input; they do not establish physical controller or Xbox console validation.

The final visual pass checked the textured spy standing, the textured merc standing and the merc crouching. Material slot assignments were read back and saved after correcting the initial empty slots. A live pose check caught and fixed a 100-fold animated root scale mismatch that asset bounds alone did not detect. The final suite includes regression checks for that failure.

Evidence is saved under `Saved/RiggingQA`: `build-verified.log`, `acceptance-final.log`, `final_appearance_check.json`, and `unreal_rig_import.json`. At the end-of-day checkpoint, ordinary input is restored, play is stopped and the editor project is saved. Press Play tomorrow to start solo practice. Independently hinged goggles, the drawn spy launcher and production weight cleanup remain separate art integration work.
