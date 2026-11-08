# Derived character equipment

Generated locally with `Scripts/prepare_equipment.py` from the user's Meshy character/carbine sources and existing mannequin-compatible character rigs. Original sources are preserved.

- SpyEquipment: body with moving binocular geometry and the old fused launcher grip removed; fixed head strap and back holster retained; the rear eyecups are cleared so the raised unit exposes the eyes.
- Goggles: original binocular housing, centered at a hinge authored in character reference space. Front caps use dark glass; Unreal adds two independently switched emissive optics.
- Launcher: original compact nonlethal prop geometry, independently rigged for attachment and recoil.
- Carbine: supplied Meshy carbine reduced to 24,000 triangles, grip origin normalized, rigid weapon skeleton and recoil keys added.
- MercArms: arm-only mesh derived from the merc, using the same mannequin-compatible skeleton and weights.
- SpyEquip / MercEquip: authored upper-body equipment poses, with a validated support-hand target, layered over locomotion by SPEquipmentAnimInstance.

Coordinates are centimeters. Character FBX skeletons reuse the existing prototype skeleton without changing its bind pose. Equipment FBX files have their own weapon skeletons. Named muzzle/grip/bolt/trigger/magazine helpers are available for future work; current animation is a short recoil rather than a complete reload system. Rebuild/import reports live under Saved/EquipmentQA and are not public build products.

These are prototype meshes/poses. No project-wide asset license is granted; see ASSET_NOTES.md in the public export and PUBLICATION.md for source and Epic-content exclusions.

## Camera-only merc sleeves

`Scripts/build_first_person_arms.py` preserves the textured source gloves and creates original closed sleeves for the first-person perspective. The full-body merc is unchanged. Dedicated `MercEquipView` and `MercThrowView` clips share equipment/release timing with the world pose. `FirstPersonViewOffset` exposes camera framing for controller tuning. `prepare_equipment.py` calls the forearm builder; both equipment and warehouse importers preserve the sleeve material slot.
