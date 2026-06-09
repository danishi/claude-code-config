# Veo 3.1 Prompt Reference

## Prompt Structure

A good video prompt describes **motion and cinematography**, not just a still scene:

1. **Subject & action** — who/what, and what they do (`a fox leaps across a stream`)
2. **Camera** — shot type and movement (`slow dolly-in`, `aerial drone shot`, `handheld`, `static wide shot`)
3. **Setting & lighting** — environment and time/quality of light (`misty forest at golden hour`)
4. **Style** — aesthetic (`cinematic`, `anime`, `documentary`, `35mm film`, `claymation`)
5. **Pace** — temporal feel (`slow motion`, `real time`, `time-lapse`)

> Default generation uses the cost-effective **Lite** model. Add `--pro` only
> when you explicitly need premium quality / 4k, or `--fast` for speed.

---

## Camera Movement Vocabulary

| Term | Effect |
|---|---|
| `static shot` | Locked-off, no camera motion |
| `slow pan left/right` | Horizontal sweep |
| `tilt up/down` | Vertical sweep |
| `dolly in/out` | Camera moves toward/away from subject |
| `tracking shot` | Camera follows the subject |
| `aerial / drone shot` | High overhead, sweeping |
| `crane shot` | Rising/falling vertical move |
| `handheld` | Subtle organic shake, documentary feel |
| `orbit / arc shot` | Camera circles the subject |
| `close-up / wide shot` | Framing scale |

---

## Categories

### Cinematic / Nature

```
{subject} in {setting}, {time of day} lighting, {camera move},
cinematic, shallow depth of field, film grain
```

**Examples:**
```
A lone wolf walking through a snowy pine forest, blue hour, slow tracking shot,
cinematic, shallow depth of field

Aerial drone shot flying over turquoise ocean waves crashing on black sand,
golden hour, smooth forward motion, 35mm film look

Time-lapse of storm clouds rolling over a mountain range, dramatic lighting,
static wide shot
```

### Urban / Lifestyle

```
{subject/action} in {urban setting}, {lighting}, {camera move}, {style}
```

**Examples:**
```
Neon-lit Tokyo street at night in the rain, reflections on wet asphalt,
slow dolly-in, cinematic, anamorphic

A barista pouring latte art in a cozy cafe, warm morning light, close-up,
handheld, documentary

Cyberpunk city skyline at dusk, flying cars, sweeping aerial shot, vibrant neon
```

### Animation / Stylized

```
{subject/action}, {animation style}, {camera move}, {mood}
```

**Examples:**
```
A cute round robot rolling across a sunny meadow, Pixar-style 3D animation,
tracking shot, cheerful

Hand-drawn anime of a girl watching cherry blossoms fall, soft pastel colors,
gentle pan up

Claymation of a snail racing a leaf down a hill, stop-motion feel, playful
```

### Abstract / Motion Design

```
{material/phenomenon} motion, {colors}, {camera}, {mood}
```

**Examples:**
```
Iridescent liquid metal flowing and swirling, macro close-up, slow motion,
hypnotic

Colorful ink diffusing in water, backlit, static shot, dreamy

Particles of light forming a galaxy, slow orbit, deep space, ethereal
```

---

## Image-to-Video

- **First frame** (`-i`): the generated video starts from this image.
- **Last frame** (`--last-frame`): constrains the final frame; the model
  interpolates motion between the two.

Describe the **motion** you want between the frames:

```bash
python scripts/generate.py "the camera slowly pushes in as petals drift down" \
  -i sunrise.jpg --last-frame sunset.jpg -o morph.mp4
```

---

## Tips

- **Lead with the action** — Veo prioritizes motion; put the verb early.
- **One clear camera move** — combining many moves in one short clip looks chaotic.
- **Use `--negative-prompt`** — e.g. `blurry, distorted, text, watermark`.
- **Use `--seed`** — reuse a seed to keep a look consistent across iterations.
- **Keep it short** — 4-8s clips; describe a single beat, not a whole scene.
