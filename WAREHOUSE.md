# Warehouse prototype — November 7, 2026

The supplied warehouse images guide the layout: tall industrial hall, pitched skylit roof, perimeter catwalks, stacked wooden freight, central safe and overhead ventilation. The environment is original modular geometry and procedural textures, built locally in Blender. The reference PNGs are copied under `Art/Warehouse/References`; no downloaded environment pack is required.

The current arrangement has 375 crate instances, low step-up routes, elevated crate bridges, six climbable rope entrances and four connected duct runs. The main floor uses daylight and warm fill. The enclosed ducts retain darkness suitable for the spy's night vision. Mercs spawn in the small vestibule and use one automatic sliding entrance. The closed north facade reserves a future office transition; there is no office level yet.

## Controller actions

- Spy: A near a rope attaches; left stick up/down climbs, centered stick holds, B drops. At the top a 3.2-second supported mantle plants both palms, pulls the chest above the lip, places the right knee, transfers weight and brings the trailing leg inside. It hands off to matching four-point crawl/idle poses. Crouch clearance is enforced; mercs cannot attach to ropes or fit through ducts. Merc A still jumps normally.
- A falling spy landing directly on a merc knocks them unconscious for six seconds, with health preserved. It requires downward speed, overhead contact, close horizontal alignment and a real server CharacterMovement landing/impact collision. Detection runs inside movement simulation so a long render frame cannot skip a narrow height window. Misses and solid cover fail. The merc's movement, shooting and equipment are disabled until recovery; a low body hitbox remains shootable. Death/reset clears the state. Getting up now grants an electrical recovery shield: three seconds from the get-up start, blocking repeat drop knockouts and rear grabs while pushing landing spies away. Ordinary damage still applies. See `RECOVERY_SHIELD.md`.
- Merc: RB/G performs an overhand grenade throw. The prop appears in the animated right hand during the windup, releases at 0.42 seconds and consumes one grenade from the same stock a captive spy can steal. The action recovers at about 0.97 seconds and has a one-second request cooldown. Interrupting before release spends nothing. First-person arms and remote third-person body use the same release timeline.
- Y remains draw/holster. D-pad Up remains night vision/flashlight. Other grab, voice and gadget controls retain their existing assignments.

## Merc view research

The original Ubisoft Chaos Theory Xbox manual describes a merc aiming reticle with a sound-bearing indicator and arrows for relative sound height (printed page 23): [publisher-authored manual PDF](https://www.mogelpower.de/manuals/Splinter_Cell_Chaos_Theory_Manual_Deutsch.pdf). The [English manual merc-screen page](https://www.manualslib.com/manual/379207/Ubisoft-Splinter-Cell-Chaos-Theory.html?page=39) provides another view of the original screen layout.

Our HUD uses original artwork: outlined segmented aiming arcs, a center point, aim/spread/recoil response, brief hit feedback and compact edge information for health, ammo, grenades and objective time. Audible spy footsteps briefly drive an eight-direction cue with above/below arrows; range is reduced by cover. It does not reveal silent enemies. This is an interpretation of the tactical information, not a copied HUD image.

## Repeatable content build

1. Build native code against the installed `/Users/rob/Games/UE_5.8` engine.
2. Run Blender headless with `Scripts/build_warehouse_art.py` to regenerate the modules and tileable textures, `Scripts/build_first_person_arms.py` for the derived camera-only forearms, and `Scripts/build_action_animations.py` to regenerate throw, rope, vent entry, knockdown clips and the synthesized drop-impact sound.
3. With PIE stopped, call the local MCP tool `stealth_tools.StealthProjectTools.prepare_warehouse`. It imports assets, rebuilds the saved preview, configures lighting/exposure and saves `/Game/Maps/Warehouse`. Source hashes skip unchanged FBX/audio imports. No user source models are removed.
4. Run `python3 Scripts/run_warehouse_acceptance.py`. Its recorded observations are under `Saved/WarehouseQA/`. It uses actual controller input injection and four local network worlds, including 100 ms latency and 2% packet loss on traversal.

## Human review still matters

Review rope contact from the side, both directions, pauses and drops; check knees and hands at each vent mouth. Judge merc grenade windup, release and recovery at normal speed and while moving, both from the first-person camera and another player's view. Test the drop attack from crates and catwalks, including edge landings and recovery under obstruction. The clips are authored prototype animation, not motion capture. Multiplayer PIE on this Mac does not establish physical Xbox hardware, internet-session or two-person microphone validation.

## Local performance observations

During the final passing warehouse run, 19 solo report samples had median frame time 12.07 ms (maximum 15.62 ms). Twenty-seven four-world samples had median 27.42 ms (maximum 30.34 ms). These are sparse editor observations at the test window sizes (960×540 solo, 640×360 clients), not a sustained benchmark or console performance claim. Hierarchical instancing groups the repeated warehouse modules; fill lights avoid extra shadow passes.

The camera-only merc arms evaluate dedicated view poses on the same release timeline independently of the full-body mesh. They combine preserved textured gloves with original closed navy sleeves shaped to exit below the view; the source full-body merc is preserved. `FirstPersonViewOffset` exposes framing for playtesting. Rebuilding all equipment invokes the dedicated forearm builder automatically.

Knockout replication updates CharacterMovement's cached mesh offset when shrinking/restoring the capsule. This prevents network smoothing from pushing the prone body below the floor. The acceptance suite checks the animated head/pelvis positions on every client after the collapse completes.

The Mac reported memory pressure during the later four-client visual review after repeated imports. The editor was restarted and a single practice client restored; other applications were left untouched. Four-client testing remains appropriate in short, small-window sessions, with memory pressure monitored.

Throw framing keeps the view arms independent of the holstered gun offset. First-person hand trajectories were measured inside a 16:9 view and captured in the full editor viewport. Hand grip detail, close-wall weapon clipping and final animation polish still require human review.

## Supported vent-entry animation

`Scripts/build_vent_entry.py` authors the mantle and matching crawl/idle against the existing spy rig. The rope stands 60 cm from the duct lip so the hands can physically reach it. Five replicated CharacterMovement root-motion phases follow the authored reach, pull, knee plant, weight transfer and trailing-leg timing. Crouch remains valid while flying on the rope; stale saved movement cannot cancel mantle posture, and the stationary reach refreshes the mesh transform after capsule shrink. Pulling poses sample rendered root progress after movement/network smoothing to preserve contacts during corrections. Rope-motion exit velocity is zeroed to prevent low-frame-rate drift after mounting and an unwanted crawl step. A capsule straddling the supported duct lip can still remount the rope. Camera height eases into the duct.

For animation-only updates, stop PIE and call `stealth_tools.StealthProjectTools.prepare_vent_entry`; it imports only these three clips and saves the warehouse preview. `Scripts/validate_vent_entry_art.py` checks evaluated bone contacts, ceiling clearance and exact entry-to-crawl pose continuity. `Scripts/run_vent_entry_acceptance.py` checks actual live support positions, crouch, neutral-stick handoff, interruption and four-client behavior at 100 ms lag / 2% loss. `Scripts/record_vent_entry_review.py` records actual Unreal gameplay into `Art/Actions/Review/vent-entry-preview.mp4`. Review camera/time-dilation helpers exist only in editor diagnostics.
