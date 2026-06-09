# Android ARM64 Termux Standard

This workflow supports Android ARM64 Termux plus optional Ubuntu proot.

## Rules

- Do not assume x86_64.
- Do not assume Docker works.
- Do not assume systemd.
- Do not assume browser popups work normally.
- Prefer portable shell, Python, git, tar, curl, node, npm, uv, and gcloud when installed.
- Avoid heredocs in user-facing commands.
- Avoid giant pasted quoted blocks.
- Prefer checked-in scripts.
- Prefer small generated files using printf when necessary.

## Common paths

- Termux home: $HOME
- Workspaces: $HOME/Workspaces
- Downloads: $HOME/storage/downloads
- Ubuntu bind: /workspaces
- Downloads bind: /downloads
