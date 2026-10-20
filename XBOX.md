# Xbox target and controller workflow

The current console target is Xbox Series X|S. Keep portable gameplay and Enhanced Input on Mac; build and validate console releases through an approved Windows/Xbox development environment. A next-generation Xbox target requires its actual available SDK and Epic support; no unreleased hardware compatibility is claimed.

## Prototype controller layout

| Xbox control | Spy | Merc |
| --- | --- | --- |
| Left stick | Analog movement | Analog movement |
| Right stick | Third-person look | First-person look |
| A | Jump, catch marked ledge, vault, climb from hanging | Unused |
| B | Toggle crouch; drop during traversal | Toggle crouch |
| Hold X | Hack nearby visible terminal; release stops | Unused |
| RT press | Rear takedown | One shot per press |
| Hold LT | Unused | Aim: narrower FOV and reduced look sensitivity |
| Y | Flip binocular goggles down/up; night vision follows | Toggle flashlight |
| D-pad Right | Switch role in solo practice only | Switch role in solo practice only |

Both sticks use a radial dead zone (default 0.18; full response at 0.95). Look uses degrees per second, independent of frame rate. Blueprint defaults expose yaw/pitch rate, dead zone, invert Y and aim sensitivity. Keyboard/mouse remain supported; HUD hints follow the most recent active input.

Connect a compatible Xbox controller to macOS by Bluetooth or USB. Start one-player PIE, click its game window, and move a stick. Shift+F1 releases mouse focus. The controller drives the focused PIE participant; four PIE clients do not establish four physical-controller routing or split-screen support.

## Console work still required

- Approved Xbox developer status, Epic console access, appropriate Xbox development hardware, and a supported Windows development machine.
- Install compatible Xbox console GDK extensions and Unreal console platform support through the authorized channels. Public Xbox-on-PC plugins alone do not produce an Xbox console build.
- Validate console packaging, performance on both Series S and Series X, user/device pairing, controller disconnect/reconnect, suspend/resume, safe-area UI, online/session services and certification requirements on actual hardware.
- Keep restricted platform code, SDKs and credentials outside the public repository. No console build, enrollment, purchase or certification has occurred in this milestone.

Official references checked October 19, 2026:

- [Epic Xbox console access](https://dev.epicgames.com/documentation/unreal-engine/xbox-development-in-unreal-engine?lang=en-US)
- [Microsoft development-PC requirements](https://learn.microsoft.com/gaming/gdk/docs/gdk-dev/get-started/overviews/set-up-dev-pc)
- [Unreal 5.8 public Xbox-on-PC plugins](https://developer.microsoft.com/en-us/games/articles/2026/06/building-xbox-games-with-unreal-engines-new-gdk-plug-ins/)
