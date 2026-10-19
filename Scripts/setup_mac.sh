#!/bin/bash
# Usage: bash Scripts/setup_mac.sh '/Users/Shared/Epic Games/UE_5.x'
set -euo pipefail
project_dir="$(cd "$(dirname "$0")/.." && pwd)"
engine_root="${1:-/Users/rob/Games/UE_5.8}"
if [[ -z "$engine_root" ]]; then
    echo "Pass your installed engine folder, containing the Engine directory."
    exit 2
fi
build_script="$engine_root/Engine/Build/BatchFiles/Mac/Build.sh"
editor="$engine_root/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
if [[ ! -f "$build_script" || ! -x "$editor" ]]; then
    echo "No complete Unreal Engine installation found at the supplied path."
    exit 2
fi
if ! xcode-select -p >/dev/null 2>&1; then
    echo "Install and select the full Xcode application before building."
    exit 2
fi
bash "$build_script" StealthPrototypeEditor Mac Development \
    "$project_dir/StealthPrototype.uproject" -WaitMutex -MaxParallelActions=3 -NoHotReloadFromIDE
"$editor" "$project_dir/StealthPrototype.uproject" /Engine/Maps/Entry \
    "-ExecutePythonScript=$project_dir/Scripts/bootstrap_editor.py" -unattended -NoSplash
if [[ ! -f "$project_dir/Content/Maps/Prototype.umap" \
   || ! -f "$project_dir/Content/Prototype/M_Spy.uasset" \
   || ! -f "$project_dir/Content/Prototype/M_Merc.uasset" ]]; then
    echo "Editor setup did not create all expected assets; inspect Saved/Logs."
    exit 1
fi
echo "Build and asset generation finished. Opening the prototype map."
open -a "$engine_root/Engine/Binaries/Mac/UnrealEditor.app" \
    --args "$project_dir/StealthPrototype.uproject" /Game/Maps/Prototype
