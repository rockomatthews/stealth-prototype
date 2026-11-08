# Merc recovery electricity

After a drop knockout, a merc gets a visible, server-owned recovery window. The current starts charging during the last 0.8 seconds on the floor. When standing clearance is available, a 0.8-second get-up transition begins and the shield lasts three seconds from that point. This leaves roughly 2.2 seconds to move, jump, aim and fire while protected from another drop knockout or rear grab.

The current is cyan/white and follows the animated body. The first-person owner receives a shield countdown and get-up message instead of arcs crossing the camera. A protected landing pushes the spy away without dealing health damage. Spies standing in the recovery capsule are pushed clear before the standing-space check, preventing ordinary head-camping from indefinitely delaying recovery. Physics handles walls; no attacker is teleported through geometry.

The shield blocks drop knockouts and rear grabs. Ordinary damage and other existing combat effects keep their existing rules. It does not open the grab voice channel on a rejected grab. Once the server deadline passes, both attacks work normally again. Death, role changes and round transitions remove protection and its effect. Respawn does not grant this shield.

## Implementation

- `FSPRecoveryShield` replicates start, get-up and expiry times. The server decides eligibility in both the impact path and the grab path, including the direct knockout entry point.
- `RecoveryShieldSeconds` defaults to 3; `MercGetUpSeconds` defaults to 0.8. They are exposed in native Blueprint defaults for combat tuning. The existing merc knockout clip is sampled in reverse for the prototype get-up, with an eased first-person camera and controls locked during that transition.
- `USPRecoveryFX` uses one instanced primitive component with 48 small segments, following skeletal contacts after bone updates. Arc jitter follows server time; segment transforms are generated locally, rather than replicated every frame. The material is unlit, supports instancing and compensates for camera exposure so daylight does not hide the effect.
- `Scripts/import_recovery_fx.py` creates the original material through the scoped MCP `prepare_recovery_fx` tool. No downloaded effects, paid package or Niagara dependency is needed.

## Validation

`Scripts/run_recovery_acceptance.py` exercises real drop contacts, pre-wake effect, anti-camping push, protected movement/fire, ordinary damage, rear-grab rejection and voice isolation, protected head landings, expiry, death/respawn and round cleanup. It includes four local clients at a 6 FPS cap with 100 ms lag and 2% packet loss. A real editor capture is saved to `Saved/RecoveryQA/get-up-shield.png`.

Existing repeat-knockout tests now wait for the intended shield expiry before expecting another successful attack. Each frame-cap group starts a fresh competitive round so the longer recovery windows do not exhaust the three-minute round timer. This does not change the production round timer.

Mac PIE checks and screenshots do not establish Xbox hardware performance, physical-controller feel or final get-up animation quality. Those remain playtest items.
