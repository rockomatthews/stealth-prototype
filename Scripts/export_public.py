"""Export tracked project files to a separate public checkout without engine art.

Usage: python3 Scripts/export_public.py /path/to/stealth-prototype-public-checkout
Does not commit, push, delete files, or copy build products/private configuration.
"""
from pathlib import Path
import argparse
import re
import subprocess

project = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('destination', type=Path)
args = parser.parse_args()
destination = args.destination.resolve()
if destination == project or project in destination.parents or destination in project.parents:
    raise SystemExit('Choose a separate export directory outside the working project.')
if (destination / 'Content/Prototype/Mannequin').exists():
    raise SystemExit('Destination contains excluded engine art; choose a clean checkout.')
destination.mkdir(parents=True, exist_ok=True)
files = subprocess.check_output(['git', 'ls-files', '-z', '--', '.'], cwd=project).decode().split('\0')
for filename in filter(None, files):
    if filename.startswith('Content/Prototype/Mannequin/'):
        continue
    source = project / filename
    target = destination / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())

config = destination / 'Config/DefaultEngine.ini'
text = re.sub(r'(?ms)^\[/Script/AndroidFileServerEditor\.AndroidFileServerRuntimeSettings\]\n.*?(?=^\[|\Z)', '', config.read_text())
config.write_text(text)
readme = destination / 'README.md'
text = readme.read_text().replace(
    'The committed map, mannequin, clips, materials, sounds and Blueprint child need no additional content download. `Scripts/migrate_mannequin.py` documents the one-time migration; do not run it during ordinary setup. Runtime gameplay does not use Mover.',
    'The public repository includes the map, materials, sounds and Blueprint child. Epic-derived mannequin mesh and animation binaries remain outside this public repository. In your licensed Unreal 5.8 installation, enable the MoverExamples editor plugin, restart, and execute `Scripts/migrate_mannequin.py` through Tools > Execute Python Script with normal rendering enabled. This imports the installed example mannequin and eight clips into `Content/Prototype/Mannequin/`. Then disable MoverExamples, restart, and run `Scripts/bootstrap_editor.py`. Runtime gameplay does not use Mover. Until migration, primitive fallback characters are available; missing-asset messages are expected.'
)
readme.write_text(text)
ignore = destination / '.gitignore'
ignore.write_text(ignore.read_text() + '\n# Recreate Epic example content from your own Unreal installation.\n/Content/Prototype/Mannequin/\n')
(destination / 'ASSET_NOTES.md').write_text(
    '# Asset provenance\n\nOriginal character concept sheets were generated with AI as modeling references. '
    'Step and shot WAV files were generated procedurally. Game source, map, materials and proxy geometry are included.\n\n'
    'Epic mannequin meshes and animation clips imported from MoverExamples are excluded. Recreate them locally with '
    'Scripts/migrate_mannequin.py using your Unreal installation, subject to Epic\'s applicable terms. Unreal Engine is not included. '
    'No third-party asset rights are granted by this repository.\n\n'
    'This original stealth prototype is unaffiliated with Splinter Cell or Halo. No project-wide open-source license has been selected.\n'
)
print('Project source export prepared at', destination)
