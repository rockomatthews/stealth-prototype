# Checkpoint — October 19, 2026

Stopped at the user's request. No further feature work should start until resumed.

## Verified

- Unreal 5.8.3 Editor target compiled successfully on this Mac with full Xcode and the Metal Toolchain.
- Latest build uses `-NoHotReloadFromIDE`; `Binaries/Mac/UnrealEditor.modules` now names `libUnrealEditor-StealthPrototype.dylib`. Use this flag while any other Unreal editor is open, otherwise UBT may produce a numbered module without updating the launch manifest.
- Project/map identity and selection were read through native Unreal MCP. Assets saved through the editor. The local endpoint is restricted to loopback.
- Imported mannequin and eight animation clips are project assets. Skeletal-material usage and root locking were saved.
- Earlier runtime tests passed solo practice, role switching, skeletal mesh presence, ledge catching, dropping, low vaulting, timer victory and round reset. These observations precede the final source fixes and do not establish a complete playable match.

## Implemented, awaiting complete validation

Enhanced Input; role cameras; temporary character animations and gear; warehouse blockout; server match rules; footsteps/shots; replicated flashlight/night vision; CharacterMovement root-motion traversal; editor-only acceptance fixtures.

The spy design now uses binocular goggles on a flip-up mount. N toggles night vision and animates the proxy hinge. Current references are `Art/Concepts/spy-v2-flip-up-goggles.png` and `spy-apose-v2-flip-up-goggles.png`. Historical v1 references remain for provenance. These are modeling references, not finished rigged characters.

## Resume here

1. Verify the opened project is `StealthPrototype` and that runtime reports include `motionDuration` (confirms the rebuilt module is loaded).
2. Run `python3 Scripts/run_acceptance.py` with the editor open. The latest attempted run used a stale hot-reload module and was stopped; its partial `Saved/acceptance.json` must not be treated as a final result.
3. Recheck four *possessed pawns*, one local pawn per PIE world, plus 2v2 teams. Earlier four-client sessions had only two pawns. Source now assigns teams before Super::PostLogin, clears the cached start spot, and moves spawns away from platform collision; these fixes compile but have not been runtime verified.
4. Check ledge hanging settles with motionDuration zero, then climb. Solo climb passed in the stale-module run after background throttling was disabled, but remote traversal still needs verification.
5. Test goggle orientation/visibility on the animated head, N down/up replication, first-person clipping, flashlight, blocked shots/hacks, rear-only takedowns, death during climbing, disconnect/rejoin, latency/loss and Mac performance.
6. Inspect rendered gameplay before claiming visual QA. Use small low-scalability windows for four clients.

No final custom character meshes, skinning, polished traversal animation or first-person arms have been produced. Gameplay feel still needs the user's playtest. Milestones C–E are not complete.

## Rebuild

Close only this project's editor after saving, then:

```sh
bash /Users/rob/Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh StealthPrototypeEditor Mac Development /Users/rob/Documents/ChatGPT/rocketship.codes/stealth-prototype/StealthPrototype.uproject -WaitMutex -MaxParallelActions=3 -NoHotReloadFromIDE
```

Keep unrelated editor sessions and unrelated repository files intact. No user-file cleanup, purchases, optional large content downloads or internet hosting are part of this work.
