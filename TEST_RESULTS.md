# Equipment and controller validation — October 30, 2026

**77/77 automated checks passed** on the final Unreal 5.8.3 Development Editor build, Apple Silicon Mac. The build succeeded after the final code change. Ordinary input is restored and solo practice is left ready for a physical-controller playtest.

Implemented: merc jumping with server-rejected ledge traversal; separate hinged spy goggles and two switched emissive optics; Y hands/taser toggle and separate RB gadget firing; D-pad Up night vision/flashlight; D-pad Left practice appearance view; shoulder launcher draw/holster and reticle; taser stun; sticky-camera deployment/viewing; skeletal merc carbine, recoil and owner-only first-person arms. The hidden merc body continues refreshing its bones for hand alignment and weapon traces. Authored support-hand placement is within 0.52 cm of its target in the source rig.

Sticky camera is the selected gadget, not a third weapon: Y toggles hands and taser, RT fires the taser, and RB launches the camera while the launcher is drawn. The camera feed remains on LB.

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
| rear controller takedown succeeds | PASS |
| merc respawns after takedown | PASS |
| remote hacking replicates | PASS |
| merc timer victory replicates | PASS |
| round resets | PASS |
| spy hack victory replicates | PASS |

Evidence remains local in `Saved/EquipmentQA`: `build-gadget-separation.log`, `acceptance-gadget-separation.log`, `focused.log`, `focused.json`, `import.json`; full observations are in `Saved/acceptance.json`. Blender sources and the grip validation report are in `Art/Equipment`.

These remain prototype skin weights and equipment poses. Finger placement, draw/recoil polish, ammunition/reload systems and physical controller feel still require further work and human evaluation. See [CHARACTER_PLAYTEST.md](CHARACTER_PLAYTEST.md) for the controls and focused playtest checklist.
