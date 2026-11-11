# Contact and deformation repair — November 10, 2026, evening

The earlier visual presentation was rejected: hands penetrated the merc, the support grip was wrong, the face covering looked like an added plate, and the collapse forced incompatible body/foot orientations. Earlier gameplay pass counts did not establish visual quality.

The current Mac Development Editor build succeeds. The focused gameplay suites pass **48/48 specialty checks and 13/13 rifle checks**. The rifle suite initially found a 7.8 cm first-person support-hand gap; the corrected camera shoulder pose passes the original distance thresholds. These checks use injected controller inputs, including four local worlds and selected 100 ms latency / 2% loss cases. They do not certify human controller feel or final character-art quality.

Derived meshes separate the worst fused torso/arm scan bridges; source imports are preserved. The neck hold uses forward shoulder reach and an outside forearm target. The prone fall preserves the hip/knee/ankle chain, and the spy braces and steps to the side of the corpse. Camera arms now use textured source geometry with a dedicated view pose. The spy has a full rounded cloth covering with actual eye openings and a clean independent binocular housing.

The blast adds 14 short-lived emissive fire sprites and, for the planted takedown, 64 ballistic blood particles that deposit on static surfaces. Original authoritative fuse, damage, shared grenade stock, and cleanup rules remain. The source still uses automatic skinning and procedural animation; frame-by-frame visual review is separate from mechanics acceptance.

Evidence: `Saved/SpecialtyQA/contact-build.log`, `Saved/ContactQA/acceptance-specialty.log`, `Saved/ContactQA/acceptance-rifle-fixed.log`, and the dated contact-v3 gameplay recordings under `Art/Actions/Review`.

---

> Art revision in progress: the user rejected the first utility-rifle appearance and paused gameplay testing. The Warden replacement mesh is newer than the rifle checks below; those results do not validate its final appearance or hand contact.

# Utility rifle, specialty holds and quiet movement — November 9, 2026

Unreal 5.8.3 Mac Development Editor build succeeded. **45/45 specialty, 13/13 utility-rifle and 9/9 quiet-movement checks passed** in Warehouse. Tests use simulated Xbox inputs and four local network worlds, including selected checks at 100 ms lag and 2% loss. Physical controller feel and Xbox console execution remain unverified.

Hold RT during an X grab plants a stolen shared-supply grenade or, at zero stock, starts a five-second back choke. The choked merc can move, turn and fire; damage can interrupt the spy. The grenade fuse continues after release or spy death. Tap RT retains the quick finish. See [SPECIALTY_TAKEDOWNS.md](SPECIALTY_TAKEDOWNS.md).

The original larger merc rifle has skeletal recoil, support-hand IK, forearm-weighted first-person sleeves, a weapon-mounted flashlight and an amber broken-ring reticle. Crouch and gentle analog movement are silent; fast steps produce directional client cues. See [UTILITY_RIFLE.md](UTILITY_RIFLE.md). First-person arms/materials and animation contact remain prototype quality, not finished character art.

The supplied video is a PC Enhanced match. Preserve Xbox bindings and prompts: Y draw/holster only, X grab, D-pad Up goggles/flashlight. Hacking expansion is deferred. Camouflage, mines, full detection modes and finite rifle ammunition/reload remain pending; see [REFERENCE_GAMEPLAY.md](REFERENCE_GAMEPLAY.md). Compact test evidence is in Validation/specialty-takedowns.json, utility-rifle.json and quiet-movement.json.

# Merc recovery electricity — November 7, 2026

The Unreal 5.8.3 Mac Development Editor build succeeded. **29/29 recovery-shield, 80/80 knockout regression and 46/46 warehouse checks passed.** The current appears near the end of unconsciousness; a 0.8-second get-up transition then starts a three-second shield window, leaving about 2.2 seconds of protected movement and firing. Repeat drop knockouts and rear grabs are rejected on the server. Landing spies are pushed away without health damage; ordinary damage still applies.

Verified in four local clients: visible pre-wake arcs, clearing a camping spy, protected get-up, actual merc movement and carbine fire during protection, ordinary damage, rear-grab rejection without pair voice, the same grab succeeding after expiry, a real protected head landing rejected at a 6 FPS cap with 100 ms lag / 2% loss, post-expiry landing succeeding, death/respawn and round reset. Visual inspection caught a gray fallback shader and exposure-darkened arcs; the final material supports instancing and compensates exposure. The actual blue-white current was then verified in `Art/Actions/Review/merc-recovery-shield.png`.

Repeat-knockout regression now waits for the intended immunity to expire and starts a fresh round per frame-cap group. Stress testing also exposed incomplete cleanup in the editor-only cover fixture: it now resets the autonomous owner as well as the server before deleting support, and the test waits for that reset. The rope input smoke test now holds the stick until observed travel (bounded to four seconds), rather than treating a fixed 1.2-second editor sleep as a speed benchmark; an earlier hitch left the spy 86 cm up and still on the rope. No production rope movement logic was changed here.

Evidence: `Saved/RecoveryQA/build.log`, `acceptance.log`, `summary.json`, `knockout-regression.log`, `warehouse-regression.log` and the game capture. Compact versioned evidence is `Validation/recovery-shield.json`. Run `Scripts/run_recovery_acceptance.py`, `Scripts/run_knockout_acceptance.py` and `Scripts/run_warehouse_acceptance.py` sequentially. All caps, network simulation and review time dilation are restored afterward. Xbox hardware, physical-controller feel and finished get-up animation quality remain unverified.

# Collision-based aerial knockout fix — November 7, 2026

The Unreal 5.8.3 Mac Development Editor build succeeded. **73/73 focused knockout checks and 46/46 unchanged warehouse regression checks passed.** The matrix requested 60/30/15/6 FPS caps and measured approximately 30.4–166.9 ms/frame; the slowest cases ran at 6 FPS. A 60 FPS cap is an upper bound, not evidence that four local clients sustained 60 FPS.

The old once-per-actor-tick height window could miss a contact after movement simulation had already landed or slid the spy. Aerial knockouts now resolve from server CharacterMovement `ProcessLanded` / `HandleImpact` callbacks before the falling velocity is lost. Real blocking upper-capsule contact, falling speed, role, round/life state, horizontal alignment and restraint/stun rules determine eligibility. Solid geometry blocks the movement sweep before it reaches a merc. The active knockout state and attacker cooldown prevent duplicate awards; the previous aimed fallback sweep and frame-history bookkeeping were removed.

Verified: repeated knockouts after recovery and high-speed falls at every requested frame cap; near misses and cover rejection; host and remote spies; exactly one award per landing; replicated capsule/body placement; six-second recovery with weapon/controls restored; unconscious controller inputs rejected; death/respawn cleanup; and repeated remote knockouts at 6 FPS with 100 ms lag / 2% packet loss. The test restores the previous frame cap and network conditions, then leaves ordinary solo practice open.

The previously failing second knockout after recovery now passes in the unchanged warehouse suite, alongside rope/vent traversal, shared grenade throws and respawn checks. Versioned results: `Validation/knockouts.json`.

Evidence: `Saved/KnockoutQA/build.log`, `acceptance.log`, `acceptance.json`, `summary.json` and per-drop trajectories. Reproduce with `Scripts/run_knockout_acceptance.py`. This is Mac/editor validation of portable gameplay code. Approved Xbox builds, physical-controller feel, moving/crouched-target tuning and real console/network performance still need Xbox hardware testing.

# Supported vent mantle — November 7, 2026

The Unreal 5.8.3 Mac Development Editor build succeeded. **24/24 focused mantle checks passed**, including an actual remote spy at 100 ms lag / 2% packet loss. The animation now reaches and plants hands, pulls the chest over the lip, braces the right knee, transfers weight and brings the trailing leg inside across a 3.2-second clip. Dedicated crawl/idle clips share the exact final pose.

Source FK validation found a maximum planted-hand error of 1.83 cm, a supported knee, ceiling clearance and zero bone-position/rotation difference at the entry-to-crawl handoff. Live solo planted palms stayed within 0.02 cm of their targets; the remote owner's rendered palms stayed within 0.02 cm during the sampled latency run. Four-client contact checks inspect the rendered owning-client mesh; the server can process movement packets between animation refreshes. This does not establish physical-controller feel or finished animation polish.

The checks caught and fixed a stale mesh transform after capsule shrink, unsupported crouching during rope flight, stale saved moves cancelling mantle posture, and clock-only pose sampling drifting from the rendered root under corrections. Neutral stick now settles without inherited exit velocity. B interruption, death during knee plant and normal respawn all passed on every client.

At the earlier vent-only checkpoint, the broad warehouse run passed 29 checks, including neutral rope holds, vent entry, vent-to-rope remount and descent, before stopping on the second aerial knockout after recovery. That run measured about 159 ms/frame (6.3 FPS) with four local clients. That earlier run stopped here; the collision-based fix and fresh results are documented above. Failure evidence is `Saved/WarehouseQA/failure.txt` and `Saved/VentEntryQA/warehouse-regression.log`.

Evidence: `Saved/VentEntryQA/build.log`, `acceptance.log`, `acceptance.json`, `solo-samples.json`, `remote-samples.json`; source validation is versioned in `Art/Actions/vent-entry-validation.json`. Reproduce with `Scripts/validate_vent_entry_art.py` and `Scripts/run_vent_entry_acceptance.py`. The compact versioned evidence is `Art/Actions/Review/validation.json`. The actual Unreal gameplay preview is `Art/Actions/Review/vent-entry-preview.mp4`; it is recorded by `Scripts/record_vent_entry_review.py`.

# Merc grenade throwing — November 6, 2026

The Mac Unreal 5.8.3 Development Editor build succeeded. **48/48 focused merc-grenade, 46/46 finisher regression, and 78/78 gameplay regression checks passed** on the final build. Solo practice is left on the merc, with two grenades and ordinary input restored.

Merc RB/G throws immediately along the aiming direction. The server validates release clearance, round/life state, restraint, stun, shared supply and cooldown before spawning. The projectile uses a swept sphere, gravity, substeps and bounces; its 2.9-second fuse and cover-tested blast run on the server. Holding RB throws once; another tap is accepted after 0.65 seconds. Throwing works with the carbine drawn or holstered and does not change Y's role.

Both throwing and theft decrement the existing `MercGrenades` property. Tests verify two throws leave the spy's kick fallback, one throw leaves one theft charge, and theft consumes that last charge. Other checks cover independent merc inventories, no negative ammo, blocked release preserving ammo, actual flight/bounces, exposed and covered blast damage, empty/dead/stunned/grabbed rejection, role-switch preservation, death/respawn, a live grenade surviving its owner's death, round reset, and four-client replication at 100 ms lag / 2% loss. Blast fixtures settle an existing thrown projectile at known positions while preserving its fuse, to isolate damage/cover checks from landing variation.

Evidence: `Saved/EquipmentQA/build-merc-throw.log`, `acceptance-merc-throw.log`, `merc-grenades.json`, `grenade-flight-readback.json`, `finishers-after-throw.log`, `finishers.json`, `gameplay-after-throw.log`, and `Saved/acceptance.json`. Reproduce with `Scripts/run_merc_grenade_acceptance.py`, `Scripts/run_finisher_acceptance.py`, then `Scripts/run_acceptance.py`, sequentially. Controller checks inject real Enhanced Input key events; physical controller feel and a polished arm-throw animation still require human/art review. No new art download was needed.

## Earlier grab, voice and finisher checkpoint — November 6, 2026

The final Unreal 5.8.3 Mac Development Editor build succeeded. **46/46 focused finisher, 61/61 grab/voice, and 78/78 gameplay regression checks passed** on the final build. Network checks used four PIE worlds (listen server plus three remote clients); solo practice was restored afterward.

Verified: X-only rear grab; slow paired movement and turning; collision stopping at walls; blocked finisher corridors preserving ammunition; tap-RT neck snap; hold-RT grenade and no-grenade kick branches; eight loaded original paired clips; actual kick-to-head bone alignment near impact; grenade stock depletion and respawn supply; live carbine fire from the other merc killing the spy and rescuing the captive; damage interruption with no delayed kick kill; armed grenades surviving interruption; round cleanup; pending trigger state cleared before another grab; and convergence under simulated 100 ms latency / 2% loss. The sampled ankle-to-head distance near the final kick was approximately 18.7 cm across all four worlds (the rendered foot extends beyond that bone).

The grenade body and removable pin are original procedural meshes. The blast sound is original synthesized audio. Animation generation leaves the supplied rigs unchanged; FBX clips and runtime assets are versioned, and reproducible Blender snapshots remain locally. The longer moves remain prototype animation and need human review of weight, contacts, camera comfort and fun. Ordinary merc grenade throwing, front melee attacks and production cinematic polish remain pending.

Evidence: `Saved/EquipmentQA/build-paired-finishers.log`, `acceptance-finishers.log`, `finishers.json`, `grab-animation-import.json`, `acceptance-drag-voice.log`, `grab-voice.json`, `regression-finishers.log`, and `Saved/acceptance.json`. Run `Scripts/run_finisher_acceptance.py`, `Scripts/run_grab_voice_acceptance.py`, then `Scripts/run_acceptance.py` sequentially. Each suite stops previous PIE and restores solo practice; normal gameplay input is re-enabled afterward.

Physical Xbox-controller feel, live speech between separate Macs, internet Host/Join and Xbox console integration remain unverified. Automated voice checks use generated tones and do not capture human speech.

## Earlier equipment and controller checkpoint — November 5, 2026

**78/78 gameplay, 56/56 grab/voice and 37/37 camera checks passed** on the final Unreal 5.8.3 Development Editor build, Apple Silicon Mac. The build succeeded after the final code change. Ordinary input is restored and solo practice is left ready for a physical-controller playtest.

Implemented: merc jumping with server-rejected ledge traversal; separate hinged spy goggles and two switched emissive optics; Y hands/taser toggle and separate RB gadget firing; D-pad Up night vision/flashlight; D-pad Left practice appearance view; shoulder launcher draw/holster and reticle; taser stun; sticky-camera deployment/viewing; skeletal merc carbine, recoil and owner-only first-person arms. The hidden merc body continues refreshing its bones for hand alignment and weapon traces. Authored support-hand placement is within 0.52 cm of its target in the source rig.

Y toggles hands and taser; D-pad Down selects camera or Spy Bullet; RB fires the selected gadget. RT fires the taser outside the feed. Inside the camera feed, LT/RT zoom, X makes noise, B releases gas, Up toggles camera NV and LB exits.

The full run uses injected Xbox inputs through Enhanced Input and gameplay RPCs. Four PIE worlds run in one process: a listen server and three remote clients. Traversal and weapon selection were checked with simulated 100 ms lag and 2% packet loss. This does not replace physical controller, separate-machine internet or Xbox console tests. Internet Host/Join remains deferred.

A separate 13/13 focused equipment run passed in the preceding equipment milestone after the support-hand adjustment, covering arm/grip alignment, merc jumping, goggles, cover-blocked taser and carbine damage. The full suite passed with continuous bone refresh enabled; the focused checks were rerun after the last cosmetic face-material repair.

| Check | Result |
| --- | --- |
| project identity | PASS |
| solo practice and skeletal character | PASS |
| practice uses the rigged spy appearance | PASS |
| animated spy keeps human scale | PASS |
| spy camera is actually third person and HUD draws | PASS |
| controller bindings installed | PASS |
| stick dead zone prevents drift | PASS |
| left stick moves character | PASS |
| right stick turns camera | PASS |
| D-pad Up lowers independent spy goggles | PASS |
| D-pad Up raises spy goggles | PASS |
| goggle lenses turn off when raised | PASS |
| RB does not draw a separate camera weapon from hands | PASS |
| Y draws taser launcher without enabling night vision | PASS |
| launcher is an equipped skeletal asset | PASS |
| RB fires gadget without changing taser selection | PASS |
| sticky camera attaches to geometry | PASS |
| LB enters sticky camera view | PASS |
| LB returns to spy camera | PASS |
| Y holsters launcher and hides reticle | PASS |
| controller B crouches | PASS |
| controller practice role and first-person camera | PASS |
| practice uses the rigged merc appearance | PASS |
| animated merc keeps human scale | PASS |
| controller A makes merc jump | PASS |
| merc lands after ordinary jump | PASS |
| merc server rejects ledge traversal | PASS |
| merc uses rigged first-person carbine | PASS |
| merc Y holsters carbine without toggling flashlight | PASS |
| merc Y re-equips carbine | PASS |
| controller appearance view shows merc in third person | PASS |
| controller appearance view returns to first person | PASS |
| controller LT aims merc | PASS |
| releasing LT restores camera | PASS |
| D-pad Up toggles merc flashlight | PASS |
| practice switches to merc | PASS |
| practice switches back to spy | PASS |
| spy catches ledge | PASS |
| spy climbs onto platform | PASS |
| spy drops from hanging | PASS |
| low vault completes | PASS |
| unmarked space does not create traversal | PASS |
| four networked worlds with 2v2 | PASS |
| correct local camera and HUD on all clients | PASS |
| remote D-pad Up goggles replicate | PASS |
| remote spy launcher selection replicates | PASS |
| remote goggles have both visible lenses | PASS |
| cover blocks taser | PASS |
| spy taser stuns merc without damage | PASS |
| tased merc cannot fire or jump | PASS |
| merc recovers from taser | PASS |
| remote RB camera deployment replicates without switching weapons | PASS |
| remote spy returns to hands | PASS |
| remote merc jump replicates without grappling | PASS |
| remote merc lands | PASS |
| remote spy hanging replicates | PASS |
| remote climb completes on all clients | PASS |
| 100ms lag and 2 percent loss enabled | PASS |
| weapon selection replicates under latency | PASS |
| traversal holsters remote launcher | PASS |
| remote ledge catch under latency | PASS |
| remote climb agrees under latency | PASS |
| remote hangs before interrupted climb | PASS |
| death cancels remote traversal | PASS |
| death and respawn restore remote player | PASS |
| network emulation restored | PASS |
| cover blocks controller shooting | PASS |
| controller RT damages enemy | PASS |
| three merc shots down spy | PASS |
| combat victim respawns | PASS |
| front takedown rejected | PASS |
| rear controller action holds merc alive | PASS |
| rear controller takedown succeeds | PASS |
| merc respawns after takedown | PASS |
| remote hacking replicates | PASS |
| merc timer victory replicates | PASS |
| round resets | PASS |
| spy hack victory replicates | PASS |

Evidence remains local in `Saved/EquipmentQA`: `build-gadget-separation.log`, `acceptance-gadget-separation.log`, `focused.log`, `focused.json`, `import.json`; full observations are in `Saved/acceptance.json`. Blender sources and the grip validation report are in `Art/Equipment`.

These remain prototype skin weights and equipment poses. Finger placement, draw/recoil polish, ammunition/reload systems and physical controller feel still require further work and human evaluation. See [CHARACTER_PLAYTEST.md](CHARACTER_PLAYTEST.md) for the controls and focused playtest checklist.

## Gadget inventory — November 5, 2026

The existing 77/77 gameplay regression checks also passed on this build (`Saved/EquipmentQA/regression-gadget-inventory.log`). The inventory-focused suite now passes **46/46** checks on the rebuilt Unreal 5.8.3 Editor target. It drives the actual Enhanced Input controller bindings and server RPCs, with solo practice and four networked PIE worlds. Camera selection, counts and placement were also checked with 100 ms simulated lag and 2% packet loss.

Y/Q remains exclusively draw/holster. D-pad Down/R cycles camera and tracking dart; RB/G fires the selected gadget while drawn. Supplies start at three cameras and four darts per life. Counts and selection replicate together. Invalid camera surfaces do not spend a charge; fired darts spend ammunition even when blocked or missed. Zero supplies reject fire and display EMPTY. Holstering, appearance setup and practice switching cannot replenish supplies. Respawn and round reset restore them.

A direct Spy Bullet hit marks the merc on the spy radar for 12 seconds, with a warning on the affected merc; wall hits create area radar sensors. No damage or stun occurs. Geometry blocks the hit. Expiry and target death clear the readout; RT continues firing the taser. The test waits for the respawn equip delay before drawing a new pawn's launcher.

| Inventory check | Result |
| --- | --- |
| new spy has three cameras and four darts | PASS |
| HUD shows both supplies and selection hint | PASS |
| selector has keyboard and Xbox bindings | PASS |
| Down selects dart while leaving hands empty | PASS |
| holstered gadget attempt spends nothing | PASS |
| Y draws launcher without changing camera selection | PASS |
| successful camera deployment spends one camera only | PASS |
| rapid repeated RB does not spend a second camera | PASS |
| deployed camera view enters | PASS |
| camera viewing blocks selector and gadget fire | PASS |
| replacement camera spends one charge | PASS |
| last camera charge reaches zero | PASS |
| empty camera cannot spawn or replace and HUD says empty | PASS |
| Y holsters without refilling inventory | PASS |
| Y draws without refilling inventory | PASS |
| Down selects available dart without changing weapon | PASS |
| dart shot spends one round including misses: 3 | PASS |
| dart shot spends one round including misses: 2 | PASS |
| dart shot spends one round including misses: 1 | PASS |
| dart shot spends one round including misses: 0 | PASS |
| empty darts stay at zero | PASS |
| practice switches to merc | PASS |
| merc cannot change or fire spy inventory | PASS |
| practice switching does not refill spy supplies | PASS |
| spy death accepted | PASS |
| respawn restores supplies and default selection | PASS |
| network round is active | PASS |
| remote selector and ammo replicate with weapon still drawn | PASS |
| cover blocks tracking but fired round is spent | PASS |
| blocked Spy Bullet becomes a wall radar sensor | PASS |
| expired area sensor clears before direct-tag test | PASS |
| tracking hit replicates without damage or stun | PASS |
| both spies get contact readouts and mercs do not | PASS |
| tracking expires and all contact readouts clear | PASS |
| RT remains taser and does not spend gadget rounds | PASS |
| stun wears off | PASS |
| camera selection replicates under lag and packet loss | PASS |
| remote camera charge and placement agree under lag | PASS |
| camera cannot attach to player or consume ammo for invalid surface | PASS |
| dart marks target before death cleanup | PASS |
| dead merc stops exposing tracking contact | PASS |
| remote respawn restores ammo and clears deployed camera | PASS |
| respawned launcher finishes drawing | PASS |
| camera spent before round reset | PASS |
| round reaches results | PASS |
| round restart replenishes every spy | PASS |

Evidence: `Saved/EquipmentQA/build-gadget-inventory.log`, `acceptance-gadget-inventory.log`, `gadget-inventory.json` and `editor-gadget-inventory.log`. The script is `Scripts/run_gadget_acceptance.py`. Physical controller feel, internet/multi-machine play, thermal camera vision, taser recharge, other payloads and merc magazines/reload remain unverified or pending implementation.

## Manual correction before camera work

Before implementing camera controls, the retail Chaos Theory Xbox Versus manual was checked directly. Spy Bullets have direct merc-tag and wall-area-sensor modes. The missing wall mode and spy radar were implemented and passed **15/15** network checks before camera work began. Tagged-enemy voice interception is not implemented; the game has no voice chat. Original balance statistics were not inferred: tag/sensor ranges and durations are explicitly prototype values in XBOX.md.

Evidence: `Saved/EquipmentQA/build-spy-bullet.log`, `acceptance-spy-bullet.log`, `spy-bullet.json`; source: `Scripts/run_sensor_acceptance.py`.

## Sticky camera controls

The final camera build passed **37/37** focused checks, including actual controller routing, camera transforms/FOV, all-client noise/gas events, ownership rejection, cooldown/one-use state, solid cover, spy immunity, merc stun/recovery, latency/loss, expiry, death and respawn. Look and zoom are local to the viewer. Noise and gas actions are server-authorized. The mono lure/hiss audio and translucent gas material were generated by the project script and imported successfully. Automated cue/asset checks establish emission and replication; audibility, comfort and controller feel still require a human playtest.

| Camera check | Result |
| --- | --- |
| network round ready | PASS |
| launcher drawn | PASS |
| remote camera placed with original audio ready | PASS |
| server rejects camera actions outside camera viewing | PASS |
| merc cannot view or gas from another players camera | PASS |
| LB opens feed and server records owned camera view | PASS |
| right stick pans camera without turning body | PASS |
| camera pan clamps at mount limit | PASS |
| camera tilt clamps at mount limit | PASS |
| LT zooms to narrow field of view | PASS |
| RT zooms out without firing or spending ammo | PASS |
| camera view blocks character movement | PASS |
| Up toggles camera NV without lowering body goggles | PASS |
| camera NV toggles off | PASS |
| X emits camera distraction cue on all clients | PASS |
| speaker cooldown rejects repeated noise | PASS |
| camera noise does not hack terminal or spend gadget rounds | PASS |
| B releases replicated visible single-use gas | PASS |
| solid cover protects nearby merc from gas | PASS |
| gas does not harm spies near the camera | PASS |
| empty gas cannot fire twice | PASS |
| LB returns to player and clears server view state | PASS |
| remote camera placed with original audio ready | PASS |
| replacement camera has fresh one-shot gas | PASS |
| noise replicates under latency and packet loss | PASS |
| camera gas stuns exposed merc under latency without damage | PASS |
| gas state agrees on all clients under latency | PASS |
| gassed merc cannot shoot or jump | PASS |
| merc recovers from camera gas | PASS |
| Y only holsters launcher and exits camera feed | PASS |
| Y redraws launcher | PASS |
| camera feed can reopen | PASS |
| camera expiry safely exits view | PASS |
| remote camera placed with original audio ready | PASS |
| last camera can be viewed before death | PASS |
| death exits camera and destroys owned equipment | PASS |
| respawn restores camera supplies after view cleanup | PASS |

Evidence: `Saved/EquipmentQA/build-camera-controls.log`, `acceptance-camera-controls.log`, `camera-controls.json`, `editor-camera-controls-final.log`, `inventory-camera-controls.log` and `regression-camera-controls.log`. Original camera audio sources are under `Art/Camera`; repeatable asset preparation is `Scripts/import_camera_assets.py`. Camera thermal vision, voice interception and merc gas masks remain pending.

Final visual inspection confirmed that camera mode replaces the body-control hints with look/zoom/noise/gas controls, and shows zoom, gas readiness and camera NV status. The final HUD build passed the 37 camera and 77 gameplay checks again. Solo practice is restored with full supplies and ordinary input.

## Sustained rear hold and private voice — November 5

The final implementation passed **56/56** focused checks and **78/78** gameplay regression checks. The spy now holds a living merc, explicitly releases them or finishes after the initial guard; the grab is server validated and replicated. Rear reach, angle, geometry, crouch-to-standing pose, restraint input blocking, taser-to-grab behavior and weapon recovery were tested. Placeholder upper-body poses remain; these are not final grab/struggle animations.

Team voice uses the user's open-microphone preference. RS/H selects the held pair channel; View/M mutes the local microphone. Tests exercise real Opus encode/decode, nonzero PCM, procedural audio playback creation and per-controller network RPCs. Packet-receipt counters run before local authorization/filtering, so isolation checks establish that unauthorized participants received no voice payloads. Forged/stale pair packets and prior-round packets were rejected. Capture buffers and playback are cleared on transitions; death, nonlethal captor damage, pawn recreation, round end and actual remote-connection close remove the pair. Normal mic capture stays off in automated/multi-client PIE.

A separate local device-only probe successfully opened and closed the Mac's default microphone; it did not call GetVoiceData, transmit audio or save speech. That verifies device-open support, not a real microphone-to-speaker conversation. Two-Mac live speech, headset/device behavior, echo/latency and internet play remain human acceptance requirements. Current competitive rules still require four clients; the earlier 1v1 Host/Join flow and Xbox voice provider/privilege validation remain separate pending work.

| Grab/voice check | Result |
| --- | --- |
| four players and private voice components ready | PASS |
| team microphone defaults open but automated PIE never captures mic | PASS |
| spy team audio encodes, relays and decodes only on spy teammate | PASS |
| merc team audio reaches only merc teammate | PASS |
| View button mutes microphone | PASS |
| muted microphone cannot transmit even generated frames | PASS |
| View button unmutes microphone | PASS |
| frontal grab rejected | PASS |
| distant grab through cover rejected | PASS |
| rear grab beyond 1.5 metres rejected | PASS |
| merc crouches for stance test | PASS |
| crouching merc cannot enter invalid standing hold | PASS |
| spy crouches before rear approach | PASS |
| spy safely stands into valid rear hold | PASS |
| stance-test release succeeds | PASS |
| rear interaction establishes replicated grab without killing | PASS |
| both held players keep weapons holstered | PASS |
| grab voice pair granted to exactly captor and victim | PASS |
| uninvolved players cannot inject audio into grab pair | PASS |
| held merc cannot move, jump, fire or draw a weapon | PASS |
| right-stick click binds grab talk | PASS |
| holding RS activates grab microphone route | PASS |
| spy grab voice reaches captive and does not leak to teammate | PASS |
| merc can answer captor without leaking to merc teammate | PASS |
| held merc cannot release captors grab | PASS |
| B releases both living players and closes pair route | PASS |
| released and stale grab packets are rejected | PASS |
| holding grab-talk after release does not leak into team radio | PASS |
| release restores merc weapon | PASS |
| team radio still works after releasing grab | PASS |
| rear interaction establishes replicated grab without killing | PASS |
| nonlethal damage to captor releases merc and closes voice pair | PASS |
| rear interaction establishes replicated grab without killing | PASS |
| victim death releases captor and closes voice pair | PASS |
| victim recovers for next grab | PASS |
| rear interaction establishes replicated grab without killing | PASS |
| pawn recreation clears hold and preserves controller voice | PASS |
| launcher ready for taser-to-grab test | PASS |
| merc tased before grab | PASS |
| rear interaction establishes replicated grab without killing | PASS |
| tased merc remains held while stun wears off | PASS |
| taser-grab release succeeds | PASS |
| rear interaction establishes replicated grab without killing | PASS |
| RT explicitly finishes held merc and clears both grab states | PASS |
| merc respawns after finished grab | PASS |
| rear interaction establishes replicated grab without killing | PASS |
| pair voice link agrees under latency and loss | PASS |
| grab voice decodes under simulated lag and packet loss | PASS |
| captor death releases merc and closes pair voice | PASS |
| captor respawns with no held victim | PASS |
| rear interaction establishes replicated grab without killing | PASS |
| round end immediately cancels grab and pair voice | PASS |
| round reset advances voice epoch and removes stale streams | PASS |
| old round voice packets rejected after reset | PASS |
| rear interaction establishes replicated grab without killing | PASS |
| remote disconnect clears surviving merc grab and pair voice | PASS |

Evidence: `Saved/EquipmentQA/build-grab-voice.log`, `acceptance-grab-voice.log`, `grab-voice.json`, `regression-grab-voice.log`, `editor-grab-voice-final.log` and `microphone-device-probe.json`. No captured speech is in the evidence files. Tests: `Scripts/run_grab_voice_acceptance.py` and `Scripts/run_acceptance.py`.

The camera regression suite also passed 37/37 after grab/voice integration (`Saved/EquipmentQA/camera-grab-voice-regression.log`). Visual inspection covered both the spy and captive merc viewpoints, including contextual release/finish/voice hints and the disabled movement/weapon state. The hold uses a placeholder upper-body pose and is not a final authored two-character animation. Ordinary solo practice was restored afterward.


## Warehouse, controller throws and aerial knockouts — November 7, 2026

The expanded warehouse-focused run passed 46/46 checks, including a second aerial knockout, death/respawn while unconscious, and animated head/pelvis heights above the floor on all four clients. The final body-height observation was head 33.8 cm / pelvis 25.9 cm in every world. Checks run through actual Enhanced Input injection, server collision and four PIE worlds; no success is inferred solely from source code.

- Grenade regression: 48/48 passed, including real travel/bounce/fuse, geometry rejection after the new windup, shared theft supply, cooldown, depletion, cover, death/reset and simulated latency.
- Grab/finisher regression: 46/46 passed, including drag/turn, paired animation, grenade theft, rescue gunfire, interruption, voice-link cleanup and packet-loss convergence.
- Core gameplay regression: 78/78 passed, including role switching, both cameras, ordinary merc jumping, traversal, controller combat, hacking, both win conditions and reset.

Logs: `Saved/WarehouseQA/{acceptance,grenade-regression,finisher-regression,core-regression}.log`; warehouse observations: `Saved/WarehouseQA/acceptance.json`. The legacy suites explicitly open `/Game/Maps/Prototype` to keep their known collision fixtures independent of the new user-facing map. The final editor is restored to Warehouse practice after verification.

No physical controller, real second person, internet session or Xbox console hardware is represented by these automated results. Sparse frame-time observations and visual-review limitations are documented in WAREHOUSE.md.

Visual review confirmed the corrected prone body in a remote merc view and boot placement near the vent. Camera-only sleeves and separate view poses avoid the previous near-camera sleeve sheets. Captured owner/observer throw frames and their runtime timestamps are under `Saved/WarehouseQA/throw-*.png` / `throw-*.json`. These remain prototype animations requiring human movement/appearance review. A Mac memory-pressure notice occurred during the later four-client review; the editor was restarted before returning to one client.

The final first-person visibility correction keeps the throwing arms raised independently of gun lowering. Full-viewport captures at 0.13, 0.19 and 0.42 seconds show the grenade/hand trajectory; all three sampled hand positions pass a conservative 16:9 framing check with a 5 cm margin. Release still spends one shared grenade and recovery restores the carbine view. The owner-only mesh uses expanded bounds to prevent near-camera animation culling.

## November 10, 2026 — takedown presentation and lethal choke

Mac Development Editor build succeeded. Final compiled build passed 48 specialty checks, 3 late-rescue checks and 13 rifle/controller regression checks (64 total). Rescue damage at 4.967 seconds prevented death and a false dismount, and both owned voice-pair tokens were cleared.

The five-second ride now kills by strangulation. A visible merc corpse falls while the spy disengages; automatic transitions preserve the drawn, reduced-scale rifle. First-person collapse camera follows the fall. Grenade pin-pull timing, shared inventory, cover/damage, interruptions, round cleanup and 100 ms / 2% network emulation were checked. The blast now uses 11 textured cosmetic body fragments with pawn/trace collision disabled.

Actual silent gameplay recordings and hashes: `Validation/takedown-polish-2026-11-10.json`. Character deformation and facial detail remain prototype quality; hardware controller feel and Xbox console/internet play are not established by these tests. No external sounds or models downloaded.
