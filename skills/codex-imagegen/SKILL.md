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

3. **Beware cross-contamination between concurrent runs.** Parallel
   `codex exec` jobs share `~/.codex/generated_images/`. A job whose
   generation fails may "recover" by copying the newest file there, which
   can be ANOTHER job's image, silently writing the wrong picture to the
   requested path. When running generations in parallel, always visually
   verify each output. If an output duplicates another job's image, delete
   it and rerun that one image alone.

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
rm -f <OUTPUT_PATH>
codex exec \
  -s danger-full-access \
  "The file <OUTPUT_PATH> does not exist yet. You MUST generate a brand-new image using the built-in image_gen tool and save it to that exact path. Do not reuse or copy any previously generated image. Image prompt: <PROMPT>"
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
rm -f <OUTPUT_PATH>
codex exec \
  -s danger-full-access \
  "Read the file <INPUT_PATH>. Analyze its content thoroughly and create an information-rich infographic/diagram that visually summarizes the key points, structure, and relationships. The file <OUTPUT_PATH> does not exist yet. You MUST generate the image using the built-in image_gen tool and save it to that exact path. Additional instructions: <USER_INSTRUCTIONS>"
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
codex exec \
  -s danger-full-access \
  "Look at the image at <INPUT_IMAGE_PATH>. Make the following modifications using the built-in image_gen tool: <MODIFICATION_INSTRUCTIONS>. Overwrite the existing file at <OUTPUT_PATH> with the modified image."
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

Codex may save images to `~/.codex/generated_images/` instead of the
requested output path. After running `codex exec`:

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

## Multiple Images

To generate multiple variations, run `codex exec` multiple times with
numbered output paths (e.g. `image_0.png`, `image_1.png`, `image_2.png`).

Parallel background runs are fine for throughput, but they raise the
cross-contamination risk described in Reliability rule 3: verify each
output's mtime and content individually, and rerun any suspect image
**solo** after deleting it.

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
  authenticated.
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
| `Codex timed out` | The default timeout is ~5 minutes. Retry or simplify the prompt |
| `No images were generated` | Rephrase the prompt; it may have been blocked by safety filters |
| `Image not at expected path` | Check `~/.codex/generated_images/` manually (see recovery warning) |
| Output file unchanged (old mtime) | Codex skipped generation because the file already existed. Delete the file and rerun with the "does not exist yet / MUST generate" phrasing |
| Output duplicates another parallel job's image | Cross-contamination via `generated_images/`. Delete the file and rerun that image alone |
| Broken arrows / wobbly lines in diagrams | Simplify the composition per "Diagram & infographic quality": straight short arrows only, no curves, generous spacing, then regenerate |
