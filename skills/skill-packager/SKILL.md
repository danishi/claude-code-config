---
name: skill-packager
description: >
  Package a skill directory into a distributable `.skill` archive placed on the Desktop.
  Use when the user asks to "package", "bundle", "zip up", "export", "distribute",
  or "ship" a skill, or mentions creating a `.skill` file from `~/.claude/skills/<skill-name>/`.
---

# skill-packager

Compresses `~/.claude/skills/<skill-name>/` into `~/Desktop/<skill-name>.skill` — a zip archive with a `.skill` extension, ready for sharing or installation via Claude Desktop.

## Steps

### Step 1 — Identify the target skill

Determine which skill to package from the user's request.

- If the skill name is explicit, use it directly.
- If the user was editing or testing a skill earlier in the conversation, assume that one is the target.
- If unclear, list the available skills and ask which one to package:

```bash
  ls ~/.claude/skills/
```

### Step 2 — Inspect the contents

List every file that will be included, so the user can spot anything unexpected before it ships:

```bash
cd ~/.claude/skills/<skill-name> && \
  find . -type f \
    -not -path '*/__pycache__/*' \
    -not -name '*.pyc' \
    -not -name '.DS_Store' \
  | sort
```

Confirm that caches (`__pycache__/`, `*.pyc`) and OS metadata (`.DS_Store`) are excluded. Flag anything suspicious before zipping — large binaries, credentials, `.env` files, local-only configs, personal data — and confirm with the user if in doubt.

### Step 3 — Create the `.skill` archive

```bash
cd ~/.claude/skills/<skill-name> && \
  zip -r ~/Desktop/<skill-name>.skill . \
    -x '__pycache__/*' '*/__pycache__/*' '*.pyc' '.DS_Store' '*/.DS_Store'
```

- **Output:** `~/Desktop/<skill-name>.skill`
- **Overwrites** any existing file at that path.
- **ASCII-safe filenames required.** Claude Desktop rejects archives containing non-ASCII filenames. If the skill directory contains Japanese or other non-ASCII filenames, rename them to ASCII equivalents *before* zipping — and update any references inside `SKILL.md` or supporting scripts accordingly.

### Step 4 — Verify and report

Confirm the archive exists and report its path and size:

```bash
ls -lh ~/Desktop/<skill-name>.skill
```

Tell the user the full output path and the file size. If the archive is unexpectedly large (e.g., >5 MB for a typical skill), suggest reviewing Step 2's file list for accidentally-bundled assets.
