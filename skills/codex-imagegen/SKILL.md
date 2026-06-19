---
name: codex-imagegen
description: >
  Generate images using Codex CLI's built-in image_gen tool. No API key
  required. Supports prompt-driven control of style, composition, and
  aspect ratio via natural-language instructions. Outputs PNG files to a
  specified path. Requires the Codex CLI (`codex`) to be installed.
---

# Codex Image Generation Skill

Use the Python script in `scripts/` to generate images via Codex CLI's
built-in `image_gen` tool. **No `OPENAI_API_KEY` required** — the built-in
tool handles authentication internally.

## Prerequisites

### 1. Install Codex CLI

Any one of the following:

```bash
# Mac / Linux (recommended)
curl -fsSL https://chatgpt.com/codex/install.sh | sh

# Homebrew
brew install --cask codex

# npm
npm install -g @openai/codex
```

Verify installation:

```bash
codex --version
```

### 2. Python 3.10+

No additional Python packages are required.

---

## Script

### `scripts/generate.py` - Image generation

#### Basic usage

```bash
python scripts/generate.py "a cute golden retriever puppy" -o puppy.png
```

#### With style

```bash
python scripts/generate.py "a mountain landscape at sunset" -s "watercolor painting" -o landscape.png
```

#### With aspect ratio

```bash
python scripts/generate.py "a city skyline at night" -a 16:9 -o skyline.png
```

#### With negative prompt

```bash
python scripts/generate.py "a professional headshot" --negative "blurry, low quality, text" -o headshot.png
```

#### Multiple images

```bash
python scripts/generate.py "abstract geometric pattern" -n 3 -o patterns.png
# -> patterns_0.png, patterns_1.png, patterns_2.png
```

#### JSON output (for programmatic use)

```bash
python scripts/generate.py "a cat" --json -o cat.png
```

#### Full options

```
usage: generate.py [-h] [-o OUTPUT] [-a ASPECT] [-s STYLE]
                   [--negative TEXT] [-n COUNT] [--timeout SECS]
                   [-v] [--json] prompt

Arguments:
  prompt                Text prompt describing the image to generate

Options:
  -o, --output PATH     Output file path (default: ./codex-images/image.png)
  -a, --aspect RATIO    Aspect ratio: 1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3
  -s, --style STYLE     Style description (e.g. "watercolor", "photorealistic")
  --negative TEXT        Things to avoid in the image
  -n, --count N         Number of images to generate (default: 1)
  --timeout SECS        Timeout per image in seconds (default: 300)
  -v, --verbose         Show codex output
  --json                Output result as JSON
```

---

## How It Works

1. The script builds an augmented prompt incorporating style, aspect ratio,
   and negative constraints
2. Calls `codex exec` with the built-in `image_gen` tool (no API key needed)
3. Codex generates the image and saves it to the specified path
4. If Codex saves to its default location (`~/.codex/generated_images/`),
   the script copies it to the requested output path

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

- **No explicit resolution control**: The built-in `image_gen` tool does
  not accept pixel dimensions. Use aspect ratio and composition prompts
  to influence output proportions.
- **Single image per call**: Each `codex exec` invocation generates one
  image. The `-n` flag runs multiple sequential calls.
- **Codex CLI required**: The `codex` command must be installed and
  authenticated.
- **No edit/inpainting**: This skill is for generation only. For image
  editing, use Codex interactively.

---

## Error Handling

| Error | Solution |
|---|---|
| `codex CLI not found` | Install Codex CLI: `curl -fsSL https://chatgpt.com/codex/install.sh \| sh` |
| `Codex timed out` | Increase `--timeout` value |
| `No images were generated` | Rephrase the prompt; it may have been blocked by safety filters |
| `Codex reported success but no image found` | Check `~/.codex/generated_images/` manually |
