# Glove, cloth, and paired-contact repair

Original Meshy scans and rigged sources are retained. Derived character meshes replace the fused scanned fingers with articulated glove geometry and reweight the sleeves to coherent arm segments. Glove UVs sample the original source; the runtime glove material is separate from uniform cloth.

Weapon placement uses palm landmarks shared by the world and camera meshes. Both merc shoulder poses reach the handguard. Absolute finger rotations avoid adding another curl to the already bent scanned bind pose. Forearm pronation is distributed below the elbow. World arms follow aiming pitch, with an inspection-camera guard.

The paired hold uses an under-chin clasp and an explicit elbow plane. Garment relaxation and surface-contact corrections are inverse-skinned into independent right/left morph targets. Separate spy launcher targets activate only with the drawn launcher. These shapes are pose-specific; source contact checks cover their reference poses, while gameplay captures must check the moving transitions.

## Rebuild order

Use the installed Blender binary in background mode. These scripts operate on derived assets and preserve original scans.

1. `fit_character_gloves.py` (rebuild missing contact snapshots with the existing `repair_contact_skin.py` after the hold animation snapshots exist).
2. `repair_spy_face.py`, `build_merc_utility.py`, `build_merc_utility_arms.py`.
3. `repair_merc_grips.py`, `repair_spy_grips.py`, `repair_throw_view.py`, `prepare_grab_animations.py`.
4. `finish_contact_correctives.py`, then `finish_launcher_contact.py`.
5. With PIE stopped, run native MCP `repair_character_presentation`, then `import_specialty_animations`, then save.

The recorded grip angle JSON files are art inputs; regenerating the experimental surface optimizer is optional and may replace deliberate finger closures. Keep the reviewed inputs for reproducible output.

Skeletal mesh import uses Interchange, explicitly verifies all required morph names, and sets skeletal/morph material usage before saving. A legacy FBX reimport can silently discard corrective targets even when its options request them. `Config/DefaultEditorPerProjectUserSettings.ini` enables morph import for the project.

## Verification

- Native editor build log: `Saved/HandContactQA/build.log`.
- Source geometry reports: `Art/FittedCharacters/contact-correctives.json` and `launcher-correctives.json`.
- Imported target names: `Saved/HandContactQA/imported-correctives.json`.
- Controller/weapon checks: `Scripts/run_utility_acceptance.py`.
- Paired mechanics/replication checks: `Scripts/run_specialty_acceptance.py`.
- Actual gameplay captures: `review_weapon_contacts.py` and `review_specialty_polish.py`.

Injected Xbox bindings exercise game input and replication; a physical controller session and Xbox hardware remain separate validation steps. Captured clips are silent actual Unreal viewports sampled against a slowed game clock, then encoded at 20 fps.

## Verified result, November 10, 2026

Mac Development editor build succeeded. All 13 weapon/controller checks and all 48 paired-takedown checks passed on the repaired assets, including the existing 100 ms latency / 2 percent packet-loss case. All required corrective morphs were read back from the imported Unreal meshes. The four source contact fixtures have zero sampled penetration deeper than 0.5 mm after correction. This is reference-pose evidence, not a guarantee for every possible moving interaction.

Fresh actual gameplay clips (silent, 20 fps):

- `Art/Actions/Review/weapon-hand-fit-v4-2026-11-10.mp4` — 5.25 s, first-person aim/fire and side/front-quarter world grips.
- `Art/Actions/Review/warehouse-choke-hand-fit-v4-2026-11-10.mp4` — 8.40 s, initial clasp through lethal ride and disengage.
- `Art/Actions/Review/warehouse-grenade-hand-fit-v4-2026-11-10.mp4` — 7.00 s, clasp through pin pull, plant, shove and detonation.

`Art/Actions/Review/hand-fit-v4-validation.json` records check names, imported shapes, contact measurements, durations, frame counts and clip hashes. The review capture session disabled the render thread after an engine Slate viewport teardown crash; it is not a performance benchmark. Physical controller feel and Xbox console validation remain pending.
