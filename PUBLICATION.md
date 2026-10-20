# Public source repository

https://github.com/rockomatthews/stealth-prototype

The working project lives inside a larger local repository. The public repository uses the project itself as its root and intentionally excludes Epic-derived mannequin meshes/animations, generated build products, local logs/settings and the unused Android file-server configuration.

To update it, clone the public repository into a separate checkout, commit the intended local project changes, then run `python3 Scripts/export_public.py /path/to/public-checkout`. Review the diff and credential scan before committing/pushing that checkout. The exporter copies tracked project files only and never deletes destination files. It does not publish anything automatically.

Keep Epic content local and recreate it from a licensed Unreal installation using the included migration script. Do not push the larger parent repository directly to this game's public remote.
