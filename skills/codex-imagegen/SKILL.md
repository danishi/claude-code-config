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

## Modes

This skill supports three modes. Claude Code constructs a `codex exec`
command directly — no wrapper script is needed.

### Mode 1: Prompt → Image

Generate an image from a text prompt.

```bash
codex exec \
  -s danger-full-access \
  "Generate an image using the built-in image_gen tool. Save the result to <OUTPUT_PATH>. Image prompt: <PROMPT>"
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
codex exec \
  -s danger-full-access \
  "Read the file <INPUT_PATH>. Analyze its content thoroughly and create an information-rich infographic/diagram that visually summarizes the key points, structure, and relationships. Generate the image using the built-in image_gen tool. Save the result to <OUTPUT_PATH>. Additional instructions: <USER_INSTRUCTIONS>"
```

- Claude Code reads the document first with the Read tool to understand its
  content, then crafts a detailed instruction for Codex.
- For very large documents, Claude Code should summarize the key points and
  include them directly in the Codex instruction for better results.
- The user's instructions guide the diagram type (infographic, flowchart,
  mind map, concept map, timeline, etc.).

### Mode 3: Image Refinement

Pass an existing image to Codex for modification.

```bash
codex exec \
  -s danger-full-access \
  "Look at the image at <INPUT_IMAGE_PATH>. Make the following modifications using the built-in image_gen tool: <MODIFICATION_INSTRUCTIONS>. Save the result to <OUTPUT_PATH>."
```

- Use for color adjustments, style changes, element additions/removals,
  composition tweaks, etc.
- Reference the original image path so Codex can analyze it.

---

## Generated Image Recovery

Codex may save images to `~/.codex/generated_images/` instead of the
requested output path. After running `codex exec`:

1. Check if the output file exists at the requested path.
2. If not, look for the most recently created file in
   `~/.codex/generated_images/` and copy it to the requested output path.

```bash
# Find the latest generated image
ls -t ~/.codex/generated_images/*.png 2>/dev/null | head -1
```

---

## Multiple Images

To generate multiple variations, run `codex exec` multiple times with
numbered output paths (e.g., `image_0.png`, `image_1.png`, `image_2.png`).

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

---

## Error Handling

| Error | Solution |
|---|---|
| `codex CLI not found` | Install Codex CLI: `curl -fsSL https://chatgpt.com/codex/install.sh \| sh` |
| `Codex timed out` | The default timeout is ~5 minutes. Retry or simplify the prompt |
| `No images were generated` | Rephrase the prompt; it may have been blocked by safety filters |
| `Image not at expected path` | Check `~/.codex/generated_images/` manually |
