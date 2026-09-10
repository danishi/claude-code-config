---
name: codex-imagegen
description: >
  Generate and edit images using Codex CLI's built-in image_gen tool. No API
  key required. Supports three modes: prompt-to-image, document-to-diagram,
  and image refinement. Requires the Codex CLI (`codex`) to be installed.
---

# Codex Image Generation Skill

Generate and edit images via `codex exec` with the built-in `image_gen` tool.
**No `OPENAI_API_KEY` required.**

## Prerequisites

### Codex CLI

```bash
# Mac / Linux (recommended)
curl -fsSL https://chatgpt.com/codex/install.sh | sh

# Homebrew
brew install --cask codex

# npm
npm install -g @openai/codex
```

Verify: `codex --version`

### A model 404 has THREE causes — try the cheap ones first

`404 ... The model 'gpt-5.x' does not exist or you do not have access to it`
is the error codex returns for several unrelated conditions. Work through
them in this order:

1. **The call set an isolated `CODEX_HOME`.** Per-job homes always fail
   this way, even with a freshly copied `auth.json` (Reliability rule 3).
   Drop `CODEX_HOME` and rerun.
2. **A transient upstream failure.** Every codex process on the machine
   starts 404ing at once — including runs that worked minutes earlier, and
   other Claude Code sessions — then recovers on its own with no re-login
   and no change to `~/.codex/auth.json`. Observed 2026-09-10: fine at
   08:26, dead from ~10:11 to ~10:22 across two sessions, working again at
   10:24 with `auth.json` untouched (mtime and `last_refresh` still two
   days old). **Wait a few minutes and retry with one cheap text call**
   before concluding anything:

   ```bash
   codex exec --skip-git-repo-check "Reply with exactly: OK" < /dev/null
   ```

3. **The stored login really is stale** — the case described below. Reach
   for this only after a retry gap has failed too, because the fix costs
   the user a browser round-trip.

Concurrency is NOT a cause. Two `codex exec` processes against the default
`~/.codex` do not break each other; a 404 that shows up while another job
is running is case 2, not contention.

**Do not report codex as broken, or switch to another image tool, on the
strength of a single 404.** Retry once after a few minutes first.

### Authentication

`codex` runs on the ChatGPT account login stored in `~/.codex/auth.json`.
The `id_token` expires roughly 10 hours after it is issued, and **an
expired token does not surface as an auth error** — it comes back as a
model 404:

```
ERROR: unexpected status 404 Not Found: The model `gpt-5.x` does not exist
or you do not have access to it.
```

Every *other* model then fails with `... is not supported when using Codex
with a ChatGPT account`, which makes it look like a plan/entitlement
problem. It is not. The token is simply stale.

**A past `exp` is not proof of breakage.** codex refreshes the token on
its own, and runs succeed with an `exp` that is days old while
`last_refresh` in `auth.json` stays unchanged. Judge by running, not by the
timestamp. Read the expiry only as one more clue after a real 404 with no
competing codex process:

```bash
python3 - <<'PY'
import json, base64, datetime, os
d = json.load(open(os.path.expanduser('~/.codex/auth.json')))
p = d['tokens']['id_token'].split('.')[1]; p += '=' * (-len(p) % 4)
c = json.loads(base64.urlsafe_b64decode(p))
print('exp:', datetime.datetime.fromtimestamp(c['exp']).isoformat())
print('now:', datetime.datetime.now().isoformat())
PY
```

A past `exp` alone does not justify a re-login — see case 2 above. When a
retry gap has failed as well, the fix is a re-login. It requires browser
auth, so Claude Code cannot run it — ask the user to run it themselves in
the prompt:

```
! codex login
```

Switching models (`-m gpt-5.4`, `-m gpt-5-codex`, …) does not work around
a stale token: older models are rejected outright for ChatGPT-account
logins. Upgrading the CLI (`codex update`) does not help either.
Re-login is the only fix.

---

## Invocation contract (MUST follow)

The exact shape of the `codex exec` call matters. Use this for every mode:

```bash
cd <OUTPUT_DIR>
codex exec --sandbox workspace-write --skip-git-repo-check "<INSTRUCTION>" < /dev/null
```

Four non-obvious requirements, each from a real failure:

- **`--sandbox workspace-write`, never `-s danger-full-access`.** Claude
  Code's auto-mode permission classifier blocks `danger-full-access`, so
  the call never runs at all. Do not retry it or try to route around the
  denial. `workspace-write` is sufficient — it grants write access to the
  working directory plus `/tmp` and `$TMPDIR`.
- **`cd` into the output directory and pass a RELATIVE filename** in the
  instruction (e.g. `hero.png`, not an absolute path). Under
  `workspace-write` only the cwd tree is writable, so the output must live
  inside it. Add "in the current working directory" to the instruction so
  Codex resolves the path the same way.
- **`--skip-git-repo-check`.** Without it, codex refuses to start:
  `Not inside a trusted directory and --skip-git-repo-check was not
  specified.` Scratchpad directories are not git repos.
- **`< /dev/null`.** Without it, codex blocks on
  `Reading additional input from stdin...` and never returns.

---

## Reliability rules (MUST follow)

These rules come from real production failures. Skipping them produces
silently wrong images.

1. **Delete a stale output file BEFORE generating** (except in-place
   refinement, Mode 3). If the output path already exists, Codex may skip
   generation entirely and report "already saved" while leaving the old
   image in place.

   ```bash
   rm -f <OUTPUT_PATH>
   ```

   Then phrase the instruction as:
   `"The file <OUTPUT_PATH> does not exist yet. You MUST generate a
   brand-new image using the built-in image_gen tool and save it to that
   exact path. Do not reuse or copy any previously generated image."`

2. **Verify the output is fresh after every run.** Compare the file's
   mtime against when the command started (`stat -f %m <OUTPUT_PATH>` on
   macOS). If the mtime is old, the run skipped generation: delete the file
   and rerun with the MUST-generate phrasing above.

3. **Never set `CODEX_HOME`; generate serially against the default home.**
   Per-job home isolation does NOT work: copying `auth.json` and
   `config.toml` into `<SCRATCHPAD>/codex-job-N` and running with
   `CODEX_HOME=` there fails every job with `The model ... does not exist
   or you do not have access to it`. Confirmed independently in two
   sessions. Since isolation is the only thing that made parallel runs
   safe, **generate images one at a time** (see "Serial Generation"
   below).

   The cost of sharing the default home is that
   `~/.codex/generated_images/` is shared across runs. A job whose
   generation fails may "recover" by copying the newest file there — which
   can be an image from an earlier job. Serial execution plus Reliability
   rules 2 and 4 (fresh mtime + visual check) is what catches that.

4. **Visually inspect every generated image before using it** (open/Read
   the PNG). Check for: garbled or misspelled text (especially Japanese),
   clipped labels, overlapping elements, broken or wobbly arrows and lines,
   pasted-on-looking text boxes. Regenerate until it passes; do not ship an
   image you have not looked at.

---

## Modes

This skill supports three modes. Claude Code constructs a `codex exec`
command directly — no wrapper script is needed.

### Mode 1: Prompt → Image

Generate an image from a text prompt.

```bash
cd <OUTPUT_DIR>
rm -f <OUTPUT_FILE>
codex exec --sandbox workspace-write --skip-git-repo-check \
  "The file <OUTPUT_FILE> in the current working directory does not exist yet. You MUST generate a brand-new image using the built-in image_gen tool and save it to that exact path. Do not reuse or copy any previously generated image. Image prompt: <PROMPT>" < /dev/null
```

#### Prompt construction

Build the prompt by combining these elements in order:

1. **Style** (optional): `Style: watercolor painting.`
2. **Subject**: the user's description
3. **Aspect ratio** (optional): `Use a wide landscape composition (16:9 aspect ratio).`
4. **Negative** (optional): `Avoid: blurry, text, watermark.`

Example:

```
Style: watercolor painting. A mountain landscape at sunset with dramatic clouds.
Use a wide landscape composition (16:9 aspect ratio). Avoid: text, watermark.
```

### Mode 2: Document → Diagram

Pass a large text, Markdown, or PDF file to Codex and have it generate an
information-rich infographic or diagram.

```bash
cd <OUTPUT_DIR>
rm -f <OUTPUT_FILE>
codex exec --sandbox workspace-write --skip-git-repo-check \
  "Read the file <INPUT_PATH>. Analyze its content thoroughly and create an information-rich infographic/diagram that visually summarizes the key points, structure, and relationships. The file <OUTPUT_FILE> in the current working directory does not exist yet. You MUST generate the image using the built-in image_gen tool and save it to that exact path. Additional instructions: <USER_INSTRUCTIONS>" < /dev/null
```

- Claude Code reads the document first with the Read tool to understand its
  content, then crafts a detailed instruction for Codex.
- For very large documents, Claude Code should summarize the key points and
  include them directly in the Codex instruction for better results.
- The user's instructions guide the diagram type (infographic, flowchart,
  mind map, concept map, timeline, etc.).
- Follow the "Diagram & infographic quality" section below.

### Mode 3: Image Refinement

Pass an existing image to Codex for modification.

```bash
cd <OUTPUT_DIR>
codex exec --sandbox workspace-write --skip-git-repo-check \
  "Look at the image at <INPUT_IMAGE_FILE> in the current working directory. Make the following modifications using the built-in image_gen tool: <MODIFICATION_INSTRUCTIONS>. Overwrite the existing file at <OUTPUT_FILE> with the modified image." < /dev/null
```

- Use for color adjustments, style changes, element additions/removals,
  composition tweaks, etc.
- Reference the original image path so Codex can analyze it.
- **Do NOT pre-delete the file when refining in place** (input == output);
  instead say "Overwrite the existing file". If input and output differ,
  apply Reliability rule 1 to the output path.

---

## Diagram & infographic quality

Diffusion-based generation breaks most often on **arrows and lines**. Design
the composition so there is nothing fragile to break.

### Composition rules

- **Straight, short arrows only.** Never request curved arrows, loop-back
  arrows, or long connector lines weaving between elements. Express cycles
  or bidirectional sync with a small pill label (e.g. 「双方向に同期 ⇄」)
  instead of a curved arrow.
- **No overlapping elements.** Give every label generous spacing; ask for
  "wide margins on every side" so nothing touches the canvas edge.
- **Prefer structures that are hard to break**: side-by-side panels, 2x2
  card grids, stacked horizontal bars, single-row card flows. Avoid dense
  networks, swimlanes, and diagrams that need many crossing connectors.
- Keep the element count low; split into two images rather than cramming.

### Style lines that work

- Flat diagram:
  `Crisp flat vector infographic, white background, styled like a clean
  professional presentation slide. Perfectly straight lines, uniform stroke
  width, sharp clean edges, generous spacing.`
- Graphic recording (grareco):
  `Warm hand-drawn graphic recording style, black ink pen and colored
  pencil accents on warm cream paper, rounded hand lettering.`
  Add `Avoid: digital flat vector look` so the style stays consistent
  across a series.

### Standard Avoid list for diagrams

```
Avoid: watermark, misspelled text, wobbly lines, blur, curved arrows,
overlapping elements, clipped text, stray marks, decorative dots,
sketchy style, 3D effects, photorealism.
```

### Text accuracy (especially Japanese)

- Quote every string that must appear verbatim (e.g. 「承認ゲート」) and add:
  `All Japanese text must be spelled exactly as given and legible.`
- After generation, zoom in and verify every label: tofu/garbled glyphs,
  swapped characters, and clipped endings are the most common failures.

---

## Generated Image Recovery

Codex may save images to `<CODEX_HOME>/generated_images/` instead of the
requested output path (`~/.codex/generated_images/` for a default-home
run; `$JOB/generated_images/` for an isolated parallel job). After
running `codex exec`:

1. Check if the output file exists at the requested path **and has a fresh
   mtime** (Reliability rule 2).
2. If not, look for the most recently created file in
   `~/.codex/generated_images/` and copy it to the requested output path.

```bash
# Find the latest generated image
ls -t ~/.codex/generated_images/*.png 2>/dev/null | head -1
```

> **Warning:** never blind-copy from `generated_images/` while multiple
> generations are running in parallel — the newest file may belong to a
> different job (Reliability rule 3). Visually confirm the content matches
> the requested prompt before accepting it.

---

## Multiple Images / Serial Generation

**Generate images one at a time, in a single background job.** Parallelism
is not available here: it requires per-job `CODEX_HOME` isolation, and an
isolated home fails with the model 404 (Reliability rule 3).
A 16:9 image takes roughly 1-2 minutes, so a 5-image batch is a ~10 minute
background run — write it as ONE script and let it work, rather than one
Bash call per image.

### Recipe

Write a script to the scratchpad and launch it with the Bash tool's
`run_in_background` (one call for the whole batch):

```bash
#!/bin/zsh
# Serial generation, default CODEX_HOME. Isolated homes hit the model 404.
run() {
  OUT="$1"; FILE="$2"; PROMPT="$3"
  cd "$OUT" && rm -f "$FILE"; START=$(date +%s)
  codex exec --sandbox workspace-write --skip-git-repo-check \
    "The file $FILE in the current working directory does not exist yet. You MUST generate a brand-new image using the built-in image_gen tool and save it to that exact path. Do not reuse or copy any previously generated image. Image prompt: $PROMPT" \
    < /dev/null > "$OUT/.gen-$FILE.log" 2>&1
  if [ -f "$OUT/$FILE" ] && [ $(stat -f %m "$OUT/$FILE") -ge $START ]; then
    echo "OK $OUT/$FILE"
  else
    echo "MISSING $OUT/$FILE"; tail -3 "$OUT/.gen-$FILE.log"
  fi
}
run <OUTPUT_DIR> <FILE_1> "<PROMPT_1>"
run <OUTPUT_DIR> <FILE_2> "<PROMPT_2>"
echo ALL-DONE
```

- Put the shared style, aspect-ratio, and negative-prompt strings in shell
  variables and interpolate them into each `run` call, so every image in a
  set shares one visual language.
- Each `run` reports `OK` or `MISSING` with a fresh-mtime check, so the
  final output tells you which images need a rerun without reading logs.
- After the batch, apply Reliability rule 4 to every output: open each PNG
  and look at it. Recovery lookups land in `~/.codex/generated_images/`,
  so a `MISSING` job may have left another job's image behind.
- Rerun any failed image alone.

---

## Aspect Ratios

| Ratio | Use case |
|---|---|
| 1:1 | Social media icons, thumbnails, profile pictures |
| 16:9 | Banners, hero images, desktop wallpapers |
| 9:16 | Mobile wallpapers, stories, vertical videos |
| 4:3 | Blog images, presentations |
| 3:4 | Portrait photos |
| 3:2 | Classic photography landscape |
| 2:3 | Classic photography portrait |

> The built-in `image_gen` tool does not accept explicit pixel dimensions.
> Aspect ratio and composition are controlled through prompt instructions.

---

## Style Examples

| Style | Description |
|---|---|
| `photorealistic` | Realistic photography look |
| `watercolor` | Watercolor painting style |
| `oil painting` | Classical oil painting style |
| `anime` | Japanese anime style |
| `3D render` | 3D computer graphics |
| `pencil sketch` | Hand-drawn pencil sketch |
| `flat design` | Modern flat design illustration |
| `pixel art` | Retro pixel art style |
| `concept art` | Professional concept art |
| `minimalist` | Clean, minimal design |

See `references/prompts.md` for detailed prompting guidance.

---

## Limitations

- **No explicit resolution control**: Use aspect ratio and composition
  prompts to influence output proportions.
- **Single image per call**: Each `codex exec` invocation generates one
  image.
- **Codex CLI required**: The `codex` command must be installed and
  authenticated with a non-expired token.
- **Output must live under the working directory**: `workspace-write`
  only permits writes to the cwd tree, `/tmp` and `$TMPDIR`, so every
  invocation `cd`s to the output directory first.
- **Document diagram quality**: Results depend on how well the instruction
  conveys the document's structure. For complex documents, Claude Code
  should pre-summarize key points in the instruction.
- **Fragile geometry**: curved arrows, long connectors, and dense overlaps
  frequently render broken. Design them out (see "Diagram & infographic
  quality").

---

## Error Handling

| Error | Solution |
|---|---|
| `codex CLI not found` | Install Codex CLI: `curl -fsSL https://chatgpt.com/codex/install.sh \| sh` |
| `404 Not Found: The model ... does not exist or you do not have access to it` | If the call set `CODEX_HOME`, drop it and rerun. Otherwise retry once after a few minutes — this error is often a transient upstream failure that clears on its own. Only if the retry also fails is the login stale: ask the user to run `! codex login`. It is not caused by another codex process running. Do not switch models or update the CLI — neither fixes it (see "A model 404 has THREE causes") |
| `The '<model>' model is not supported when using Codex with a ChatGPT account` | That model is not available to ChatGPT-account logins. Do not pass `-m`; let the configured default model apply |
| `Not inside a trusted directory and --skip-git-repo-check was not specified` | Add `--skip-git-repo-check` to the `codex exec` call |
| Command hangs on `Reading additional input from stdin...` | Append `< /dev/null` to the `codex exec` call |
| `-s danger-full-access` call is blocked / denied | Claude Code's permission classifier blocks it. Use `--sandbox workspace-write --skip-git-repo-check` with a relative output path under the cwd instead |
| Codex says it cannot write the output path | The path is outside the sandbox. `cd` to the output directory and pass a relative filename |
| `Codex timed out` | The default timeout is ~5 minutes. Retry or simplify the prompt |
| `No images were generated` | Rephrase the prompt; it may have been blocked by safety filters |
| `Image not at expected path` | Check `~/.codex/generated_images/` manually (see recovery warning) |
| Output file unchanged (old mtime) | Codex skipped generation because the file already existed. Delete the file and rerun with the "does not exist yet / MUST generate" phrasing |
| Output duplicates an earlier job's image | Recovery cross-contamination via the shared `~/.codex/generated_images/`. Delete the file and rerun that image alone. Do not reach for `CODEX_HOME` isolation — it 404s |
| Parallel job fails with auth error | The copied `auth.json` went stale. Re-copy a fresh `~/.codex/auth.json` into that job's home and rerun it alone |
| Broken arrows / wobbly lines in diagrams | Simplify the composition per "Diagram & infographic quality": straight short arrows only, no curves, generous spacing, then regenerate |
