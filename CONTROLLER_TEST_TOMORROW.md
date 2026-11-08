# Controller playtest — November 8, 2026

Open `StealthPrototype.uproject` with the installed Unreal 5.8 editor, connect the Xbox controller and press Play. One-player standalone practice is configured. Click the game view to give it input focus; Shift+F1 releases mouse focus.

1. Test the spy's analog movement, turning, jump and crouch. Press A near a rope, hold left stick up and watch the supported climb into the vent. B drops during traversal.
2. D-pad Right switches roles in solo practice; this remains a temporary development control. Test merc first-person look, movement and ordinary jumping. Mercs cannot climb ropes or grab ledges.
3. Y draws/holsters. D-pad Up controls spy goggles/night vision or the merc flashlight. Merc RB throws a grenade from the shared supply. Check hand/weapon placement and controller responsiveness.
4. Judge camera comfort, spy foot placement on ropes, vent entry, turning sensitivity and which sounds need replacing. The current sounds are procedural placeholders; `SOUND_SOURCING.md` lists free candidates to audition.

Rear grabs, drop knockouts and recovery shields need multiplayer PIE participants or our scripted editor fixtures. Solo role switching does not create opponents. X is rear grab; the merc's recovery current blocks repeat grabs and drop knockouts, then gives about 2.2 seconds of protected movement/fire after the 0.8-second get-up. Ordinary damage still applies.

Latest verified results: 29 recovery-shield checks, 80 knockout checks and 46 warehouse checks passed in local Mac PIE, including six-FPS and simulated-latency cases. `TEST_RESULTS.md` and `Validation/recovery-shield.json` retain the evidence. Controller feel and Xbox hardware validation remain playtest work.

Visuals: `Art/Actions/Review/vent-entry-preview.mp4` and `Art/Actions/Review/merc-recovery-shield.png`. Full controls: `XBOX.md`. No new third-party audio was downloaded or installed today.
