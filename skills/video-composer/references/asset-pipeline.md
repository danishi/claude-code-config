# Asset Pipeline — generating media for the timeline

video-composer does not generate media itself. It orchestrates the sibling
skills in this repository and places their output under the Remotion project's
`public/` directory.

| Asset | Skill | Script | Output dir |
|---|---|---|---|
| Images / backgrounds | **nanobanana** | `scripts/generate.py` | `public/images/` |
| Video clips | **veo** | `scripts/generate.py` | `public/video/` |
| Background music (BGM) | **lyria** | `scripts/generate.py` | `public/audio/` |
| Narration / voiceover | **gemini-tts** | `scripts/generate.py` | `public/audio/` |

> All sibling skills share the same env (`GEMINI_API_KEY` or Vertex AI), output
> MP4/PNG/WAV/MP3, and support `--no-ssl-verify`.

## 0. Check availability first

Always run the availability check before generating, and act on missing skills
(see "Missing skills" below):

```bash
python scripts/check_skills.py
```

## 1. Images (nanobanana)

```bash
python <nanobanana>/scripts/generate.py \
  "cinematic wide shot of a misty forest at dawn, volumetric light" \
  --ratio 16:9 -o <project>/public/images/scene1.png
```

- Match `--ratio` to the video orientation (16:9 landscape, 9:16 portrait).
- Generate one image per still scene; reuse the prompt style for visual cohesion.

## 2. Video clips (veo)

```bash
python <veo>/scripts/generate.py \
  "slow dolly-in over the forest canopy, golden light" \
  --ratio 16:9 --duration 6 \
  --negative-prompt "background music, soundtrack, musical score, BGM" \
  -o <project>/public/video/scene2.mp4
```

- Defaults to the cost-effective Veo 3.1 Lite model (add `--pro` only if asked).
- Veo clips are 4-8s; size each scene's `durationInFrames` to the clip length
  (`seconds * fps`).

### ⚠️ Never let veo clips carry their own BGM (music goes only in the lyria layer)

Veo 3.1 generates native audio, and left unguided it may **bake background music
into the clip**. The clip's audio track keeps playing on the timeline
(`<OffthreadVideo>`), so any embedded music would stack on top of the global
lyria BGM and the two soundtracks would clash. To keep a single, coherent music
bed, **always suppress music when generating veo clips** — regardless of whether
this video has BGM:

- **Always pass** `--negative-prompt "background music, soundtrack, musical score, BGM"`
  (merge with any other negatives you need).
- **Do not request music** in the positive prompt — describe motion, camera,
  setting, lighting, and **diegetic sound only** (e.g. "wind through leaves",
  "footsteps on gravel", "ambient city hum"). Avoid words like "music",
  "song", "score", "soundtrack".
- **Keep sound effects / ambience / dialogue.** SE and environmental audio are
  wanted — do **not** mute the clip. Suppression is music-only, done at
  generation time via the prompt; the timeline plays the clip's audio as-is
  (the music suppression is what keeps it from fighting the BGM).
- Audio is generative, so suppression is best-effort. If a delivered clip still
  has audible music, regenerate it (tweak the prompt / add a `--seed`) rather
  than muting the whole track, which would also kill the SE.

## 3. Background music (lyria)

```bash
python <lyria>/scripts/generate.py \
  "calm ambient piano, gentle pads, hopeful, instrumental" \
  --pro -o <project>/public/audio/bgm.mp3
```

- Use `--pro` for a full-length track that covers the whole video; `--clip` for
  short loops. Keep BGM `volume` low (≈0.2) so narration stays intelligible.

## 4. Narration / voiceover (gemini-tts)

```bash
python <gemini-tts>/scripts/generate.py \
  "Welcome. Today we explore the quiet beauty of the forest at dawn." \
  --voice Charon -o <project>/public/audio/vo1.wav
```

- One file per narrated scene; set the scene's `durationInFrames` to comfortably
  fit the narration (measure the WAV length, then `frames = ceil(seconds*fps)`).
- For dialogue, gemini-tts auto-detects multi-speaker from `Name:` lines.

## Wiring assets into props.json

Reference assets by their path **relative to `public/`** (the template wraps
them with `staticFile()` automatically):

```json
{
  "media":     { "type": "image", "src": "images/scene1.png" },
  "voiceover": { "src": "audio/vo1.wav" },
  "bgm":       { "src": "audio/bgm.mp3", "volume": 0.22 }
}
```

## Timing tips

- `durationInFrames = round(seconds * fps)` (e.g. 5s @ 30fps = 150 frames).
- For narrated scenes, make the scene at least as long as the voiceover plus a
  short tail (≈10-15 frames).
- Transition `durationInFrames` is *stolen* from the two adjacent scenes — keep
  it small (12-24 frames) relative to scene length.

## Missing skills — install prompt / fallback

`check_skills.py` reports any sibling skill that is not installed. This commonly
happens when **another user installed video-composer standalone** (e.g. via
`npx skills add`). In that case:

1. **Prompt the user to install** the missing skills (commands come straight
   from the repo README):

   ```bash
   # add the marketplace once, then install the plugins
   claude marketplace add https://github.com/danishi/claude-code-config
   claude plugin install nanobanana
   claude plugin install veo
   claude plugin install lyria
   claude plugin install gemini-tts

   # …or install individual skills directly
   npx skills add danishi/claude-code-config --skill nanobanana
   ```

2. **Offer a fallback** when the user does not want to install a skill:

   | Missing | Fallback |
   |---|---|
   | nanobanana | Solid-color / CSS-gradient scene backgrounds, or user-supplied images |
   | veo | Use still images with Ken Burns instead of video clips |
   | lyria | Omit BGM (silent), or a user-supplied music file in `public/audio/` |
   | gemini-tts | On-screen captions only (no voiceover), or user-supplied audio |

State clearly in the plan which assets are generated vs. fallback, so the user
can decide before approving.
