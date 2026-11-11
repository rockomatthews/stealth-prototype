# Sound sourcing — Sonniss selected November 10, 2026

Current game effects are procedural placeholders: Step/Shot (recorded in Scripts/export_public.py asset notes), CameraLure/CameraGas (Scripts/import_camera_assets.py), GrenadeBlast (Scripts/import_grab_animations.py) and DropImpact (Scripts/build_action_animations.py). No external replacement audio has been downloaded or auditioned in this research pass.

## Selected source: Sonniss GameAudioGDC

User decision: use [Sonniss GameAudioGDC](https://sonniss.com/gameaudiogdc/) for game sounds. The older shortlist below remains reference material; Sonniss is the primary source for the next audio pass.

Priority order:
1. Merc rifle shots and weapon handling; grenade pin, throw, bounce and blast.
2. Spy fabric/harness and merc equipment movement; concrete and metal footsteps.
3. Goggles hinge, flashlight switch, rope friction, vent movement and landing impacts.
4. Taser, sticky-camera launch/stick, camera controls and warehouse ambience.

Audition selected files and relevant archives before downloading large collections. Preserve each original filename, collection/year, supplier, source URL, download date and applicable license. Import chosen effects as local production assets and synchronize them with actual gameplay/animation events. No Sonniss audio has been downloaded or imported by this decision update; existing procedural placeholders remain.

[License verified November 10, 2026](https://sonniss.com/gdc-bundle-license/): version 2.0, effective August 27, 2026. Commercial game use and modification are permitted without attribution. The license restricts supplying the sound effects themselves, including modified versions. Keep original WAVs, edited source sounds and their Unreal sound assets out of the public GitHub export; share finished game builds normally. Establish the private-audio storage/export exclusion before the first import. Preserve the license applicable when downloading.

## Earlier alternatives — reference only

| Need | Candidate | Verified listing / practical notes |
| --- | --- | --- |
| Merc gear and spy harness movement | [gear-friction.wav — isbeorn](https://freesound.org/people/isbeorn/sounds/517150/) | CC0; 33.6 seconds, 6.2 MB, 48 kHz/16-bit stereo. Creator describes police-operator equipment movement. Cut into short separate movement variations. |
| Merc gunfire candidate | [M4 Assault rifle firing.wav — mnslugger20](https://freesound.org/people/mnslugger20/sounds/259758/) | CC0 listing; 11.6 seconds, 2 MB, WAV. Designed short bursts with added bass, shells and echo; audition before adopting. Already mixed layers limit independent control. |
| Alternate rifle recording | [M16 Rifle Shots — qubodup](https://freesound.org/people/qubodup/sounds/187677/) | CC0/public-domain listing; 7.9 seconds, 522 KB, 48 kHz FLAC. Uploader identifies US government video provenance. Keep its source link; audition and convert losslessly for import. |
| Magazine / mechanism parts | [Gun Reload Sound Effects — Brian MacIntosh](https://opengameart.org/content/gun-reload-sound-effects) | CC0; three small WAV files. Optional credit requested. Candidates for draw/holster and future reload layers. |
| Empty-trigger mechanical click | [Rifle clip empty — michorvath](https://freesound.org/people/michorvath/sounds/427603/) | CC0; mono 16-bit WAV, about 73 KB. Future ammunition/reload feedback; does not imply those gameplay rules are implemented. |
| Physical impacts / foley | [Kenney Impact Sounds](https://kenney.nl/assets/impact-sounds) | 130 files, CC0. Candidate for crate/metal contact, landing and equipment layers. |
| Gadget / menu feedback | [Kenney Interface Sounds](https://kenney.nl/assets/interface-sounds) | 100 files, CC0. Candidate clicks for selection, camera interaction, goggles controls. Ground mechanical goggles with a real hinge/click layer. |

Freesound downloads require a free account. Licenses are per sound: keep the exact listing and author with every selection. Prefer CC0 for the public source repository; CC BY is another option with compliant attribution. Avoid CC BY-NC for the intended commercial game. Listing verification is not an audio-quality audition or a guarantee of an uploader's ownership.

## Broader free libraries

- [Sonniss GameAudioGDC archive](https://sonniss.com/gameaudiogdc/): broad professional library to search for weapons, mechanical foley and industrial ambience. Bundles can be large, so select only relevant archives rather than downloading everything. [Current bundle license](https://sonniss.com/gdc-bundle-license/) permits commercial games without attribution but restricts distribution of the sounds themselves, including modified sounds. Keep licensed source audio out of the public GitHub export. Save the license published on the download date; the site says that version governs, even if a bundled copy is older. The license also prohibits AI training/development use.
- [ZapSplat](https://www.zapsplat.com/): useful search terms include tactical gear, nylon, buckle, magazine, gun cock, grenade pin, rope creak, metal duct, boot concrete and fluorescent hum. [Free Basic license](https://www.zapsplat.com/license-type/standard-license/) permits commercial games with credit, download limits and MP3-only access. Raw source redistribution is restricted. Prefer CC0/WAV candidates first.
- [Mixkit](https://mixkit.co/free-sound-effects/): commercial game use is allowed under the [Sound Effects Free License](https://mixkit.co/license/modal/sfxFree/). Standalone/source-file redistribution is prohibited; keep these out of the public asset export too.

## First audition batch and implementation handoff

1. Pick 3–5 Sonniss merc single-shot variations, dry where possible; compare close and distant layers.
2. Select small mechanism layers for weapon draw/holster, goggles flip and flashlight switch.
3. Select 6–10 short Sonniss gear rustles; keep spy fabric quieter/lighter and merc equipment heavier.
4. Add concrete boots, metal catwalk steps, vent crawl scrapes, rope friction and landing impacts.
5. Follow with taser discharge, sticky-camera launch/stick, camera rotation/zoom, grenade pin/throw/bounce/blast and warehouse ambience.

For each chosen file preserve original name, author, exact source URL, license/version, download date and edits. Listen for clipped peaks, baked room echo and background noise. Keep original WAV/FLAC rather than an MP3 preview when available. Suggested working delivery: PCM WAV, 48 kHz, mono for point-source weapon/gear effects; retain stereo originals and stereo ambience. Conversion does not improve a lossy source.

Integration plan: trim and level-match, create non-repeating variations, attach foley to animation timing, configure spatial attenuation/occlusion, then audition as both spy and merc with a controller. Keep the merc's local weapon detail distinct from the spatial sound heard by everyone else, with one world event per shot. Test gameplay readability: footsteps and gear should communicate movement without drowning team voice or objective feedback.
