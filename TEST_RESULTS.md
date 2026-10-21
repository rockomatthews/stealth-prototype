# Character and controller validation — October 20, 2026

50/50 automated checks passed on Unreal 5.8.3, Development Editor, Apple Silicon Mac. The final build passed. Ordinary input was restored after test isolation. The end-of-day checkpoint has PIE stopped and editor assets saved.

The spy and merc now use separate 80,000-triangle skeletal meshes, sharing the prototype animation skeleton. Both textured characters were visually inspected standing, and the merc was inspected crouching. Material assignments were read back. Animated head scale and location checks cover the corrected FBX root-scale problem. See [CHARACTER_PLAYTEST.md](CHARACTER_PLAYTEST.md) for controls and remaining art work.

Synthetic Xbox events went through Enhanced Input and normal gameplay RPCs. Four PIE worlds ran in one process: one listen server and three remote clients. This does not establish physical-controller compatibility, separate-machine internet play or Xbox console performance. Internet Host/Join remains deferred.

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
| controller Y lowers spy goggles | PASS |
| controller Y raises spy goggles | PASS |
| controller B crouches | PASS |
| controller practice role and first-person camera | PASS |
| practice uses the rigged merc appearance | PASS |
| animated merc keeps human scale | PASS |
| controller appearance view shows merc in third person | PASS |
| controller appearance view returns to first person | PASS |
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

Traversal includes simulated 100 ms lag and 2% packet loss. Final remote climb positions agree within 25 cm; this does not establish absence of transient corrections. Raw observations, build logs and final material/pose readback remain local under Saved/.

Goggles and back equipment are still part of the skinned spy body; independent goggle hinges, state-controlled lens emission and drawn launcher animations remain unfinished. Prototype weight cleanup, first-person arms, physical controller testing and prolonged playtesting remain outstanding.
