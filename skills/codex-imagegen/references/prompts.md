# Prompting Guide

Codex's built-in `image_gen` tool is prompt-driven. Resolution, aspect ratio,
and style are controlled through natural-language instructions in the prompt.

## Aspect Ratio Control

Include aspect ratio instructions directly in the prompt:

| Ratio | Use case | Prompt hint |
|---|---|---|
| 1:1 | Social media icons, thumbnails | "square composition" |
| 16:9 | Banners, hero images, desktop wallpapers | "wide landscape composition (16:9)" |
| 9:16 | Mobile wallpapers, stories | "tall portrait composition (9:16)" |
| 4:3 | Blog images, presentations | "standard landscape composition (4:3)" |
| 3:2 | Classic photography | "classic landscape composition (3:2)" |

## Style Keywords

| Category | Examples |
|---|---|
| Photography | photorealistic, studio photography, editorial, candid, macro |
| Illustration | watercolor, oil painting, pencil sketch, digital art, vector |
| 3D/CG | 3D render, isometric, low-poly, clay render, voxel art |
| Anime/Manga | anime style, manga, chibi, cel-shaded |
| Design | flat design, minimalist, retro, vintage, art deco |
| Concept | concept art, matte painting, storyboard |

## Composition Keywords

- Camera: close-up, wide shot, bird's eye view, worm's eye view, over-the-shoulder
- Framing: centered, rule of thirds, symmetrical, negative space
- Depth: shallow depth of field, bokeh, tilt-shift

## Lighting Keywords

- soft studio lighting, golden hour, dramatic side lighting
- neon glow, backlit, silhouette, rim lighting
- overcast, high-key, low-key, chiaroscuro

## Prompt Structure

Best results follow this order:

1. **Style/medium** — "watercolor illustration of"
2. **Subject** — "a golden retriever puppy"
3. **Action/pose** — "sitting on a park bench"
4. **Setting** — "in a sunny autumn park"
5. **Composition** — "wide shot, rule of thirds"
6. **Lighting/mood** — "warm golden hour lighting"
7. **Constraints** — "no text, no watermark"

### Example

```
Photorealistic close-up of a freshly baked croissant on a marble
countertop, soft morning light from a window, shallow depth of field,
warm tones, no text, no watermark
```

## Negative Prompts

Use `--negative` to specify what to avoid:

```bash
python scripts/generate.py "a cute cat" --negative "text, watermark, blurry, low quality"
```
