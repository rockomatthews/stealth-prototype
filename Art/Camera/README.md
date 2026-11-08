# Original camera audio

CameraLure.wav is a synthesized mono electronic distraction; CameraGas.wav is a synthesized, filtered-noise gas burst. Both were generated locally by Scripts/import_camera_assets.py using deterministic standard-library code, with no external sound recordings.

The editor script imports them into Content/Prototype/Audio and creates the translucent M_CameraGas material. Runtime playback originates at the deployed camera with spatial attenuation. Each camera has one gas burst and noise has a two-second cooldown.
