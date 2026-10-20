# Controller and multiplayer validation — October 19, 2026

44/44 automated checks passed. Unreal 5.8.3, Development Editor build, Apple Silicon Mac. The final run used editor-only input isolation; normal input was restored afterward.

Synthetic Xbox key events went through PlayerController and Enhanced Input, then normal gameplay RPCs. Four PIE worlds ran in one process: one listen server and three remote clients, 640×360 each. Solo practice uses 960×540. These results do not establish physical-controller compatibility, separate-machine networking or Xbox console performance.

Sampled editor frame intervals across 23 successful four-client observations: median 29.7 ms, range 20.3–343.7 ms. This is a functional-run sample, not a controlled GPU benchmark.

Actual spy camera displacement, merc first-person offset and HUD draw activity were checked on every local client. Spy third person, night vision, merc first person, flashlight and controller hints were also inspected visually in the running Mac editor. Art and weapon meshes remain placeholders.

| Check | Result |
| --- | --- |
| project identity | PASS |
| solo practice and skeletal character | PASS |
| spy camera is actually third person and HUD draws | PASS |
| controller bindings installed | PASS |
| stick dead zone prevents drift | PASS |
| left stick moves character | PASS |
| right stick turns camera | PASS |
| controller Y lowers spy goggles | PASS |
| controller Y raises spy goggles | PASS |
| controller B crouches | PASS |
| controller practice role and first-person camera | PASS |
| controller LT aims merc | PASS |
| releasing LT restores camera | PASS |
| controller Y toggles merc flashlight | PASS |
| practice switches to merc | PASS |
| practice switches back to spy | PASS |
| spy catches ledge | PASS |
| spy climbs onto platform | PASS |
| spy drops from hanging | PASS |
| low vault completes | PASS |
| unmarked space does not create traversal | PASS |
| four networked worlds with 2v2 | PASS |
| correct local camera and HUD on all clients | PASS |
| remote controller goggles replicate | PASS |
| remote spy hanging replicates | PASS |
| remote climb completes on all clients | PASS |
| 100ms lag and 2 percent loss enabled | PASS |
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

The latency run verified 100 ms packet lag and 2% loss in every PIE net driver. At the end of the remote climb, client positions agreed with the server within 25 cm. This does not prove absence of transient corrections. Full raw observations remain local in Saved/acceptance.json.
