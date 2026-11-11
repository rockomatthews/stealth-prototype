# Warden utility bullpup — art revision

The user rejected the first block-built rifle. Gameplay testing is paused while the weapon appearance is rebuilt using the supplied bullpup reference. The original replacement is approximately 77,000 triangles with nine rig anchors and UVs. It has a shaped receiver and stock, open thumbhole and trigger guard, recessed vents and ejection channel, shaped handguard, machined muzzle ports, fasteners, markings, and a compact integrated amber display. The Blender source and FBX are in Art/UtilityRifle; studio previews show the actual modeled geometry.

This revision is visual work. Earlier controller and network results below apply to the previous mesh revision and do not verify the new mesh. No new gameplay tests were run after the user's request to pause them. Final in-engine appearance and hand contact must be reviewed before resuming the test suites.

# Original merc utility rifle

Built from original geometry in `Scripts/build_merc_utility.py`, guided by the user's two supplied merc-view screenshots. The supplied Meshy carbine is preserved as the fallback/source asset.

The replacement is approximately 91 cm long with a broad receiver, shoulder stock, low iron sights, horizontal support fore-end, light/laser housings, cooling slots, charging handle and a canted rear status panel. Six material slots and approximately 15,000 triangles keep the first prototype manageable. The panel is actual 3D geometry, with exposure-compensated amber ROF bars and SEMI text. It reflects the current firing behavior; no automatic-fire or ammunition system is implied.

`MercUtilityEquip` and `MercUtilityEquipView` align the palms using anatomical wrist-to-knuckle directions. Runtime two-bone IK keeps the left hand at the support anchor during differing locomotion and replicated poses. The first-person sleeves are separately derived by `Scripts/build_merc_utility_arms.py`; they follow the forearms so a changed palm orientation cannot rotate a sleeve across the reticle. Original full-body and arm source assets remain available.

The rifle retains the existing server weapon rules, draw/holster, aiming, grenade throw and flashlight controls. D-pad Up illuminates from the rifle's light anchor while equipped. The cosmetic laser housing has no new gameplay function. The larger amber reticle uses broken double rings and a center dot; directional arcs indicate admitted nearby fast spy footsteps and expire instead of retaining a permanent position marker.

Rebuild the FBXs with local Blender, then run `Scripts/import_merc_utility.py` in the full editor with PIE stopped, or use the project's fixed `import_merc_utility` MCP operation. Run `Scripts/run_utility_acceptance.py` and `Scripts/run_quiet_movement_acceptance.py` for the focused checks. These are Mac PIE/controller-binding checks, not Xbox hardware or human controller-feel certification.

## Visual limitations

This is an original functional prototype mesh, not finished production art. Sleeves now clear the reticle, but the first-person sleeve ends, material detail, finger contact through extreme aim angles, and animation transitions still need refinement. The specialty explosion remains a simple flash and equipment debris, not a finished gore effect.
