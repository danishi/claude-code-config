# Asset Pipeline — generating media for the timeline

video-composer does not generate media itself. It orchestrates the sibling
skills in this repository and places their output under the Remotion project's
`public/` directory.

| Asset | Skill | Script | Output dir |
|---|---|---|---|
| Images / backgrounds | **nanobanana** | `scripts/generate.py` | `public/images/` |
| Video clips | **gemini-omni** (primary) / **veo** (fallback) | `scripts/generate.py` | `public/video/` |
| Background music (BGM) | **lyria** | `scripts/generate.py` | `public/audio/` |
| Narration / voiceover | **gemini-tts** | `scripts/generate.py` | `public/audio/` |

> All sibling skills share the same env (`GEMINI_API_KEY` or Vertex AI; the veo
> fallback **requires Vertex AI** — `GOOGLE_CLOUD_PROJECT`), output
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

## 2. Video clips (gemini-omni, veo as fallback)

### 2a. gemini-omni (primary)

```bash
python <gemini-omni>/scripts/generate.py \
  "Continuous single shot, no scene cuts. Slow dolly-in over the forest canopy, golden morning light. Sound design: wind through leaves, distant birds. No dialogue. No background music, no soundtrack, no musical score." \
  --ratio 16:9 -o <project>/public/video/scene2.mp4
```

- Works with `GEMINI_API_KEY` or Vertex AI (`GOOGLE_CLOUD_PROJECT`, location `global`).
- The mode follows the inputs: prompt only → text-to-video; `-i start.png` →
  image-to-video (e.g. animate a nanobanana still for visual continuity);
  `-i first.png -i last.png` → first/last frame; several `-i` → subject
  reference (keep a product / character consistent across scenes, up to 10).
- **Clip length is ~10s** (`--duration` is not guaranteed). Plan scenes of
  ≤10s per clip and set `durationInFrames` to what the scene needs — the clip is
  cut at the scene end. Need longer? Extend with
  `--previous scene2.mp4 "Extend this video: ..."` (returns the whole clip,
  +~10s per turn, up to 40s).
- **Ask for one take**: Omni cuts between several shots by default. Start the
  prompt with `Continuous single shot, no scene cuts.` unless you want cuts.
- **Image-to-video may show the source image for ~1s.** Skip it on the timeline
  with `"media": { ..., "trimStartFrames": 30 }` (30 frames = 1s @ 30fps)
  instead of re-encoding.
- **Fix a clip by editing it, not regenerating.** Every run writes
  `<clip>.mp4.json`; refine with short instructions:
  `--previous scene2.mp4 "Make the light warmer. Keep everything else the same."`
  Do not pass `--no-store` for timeline clips — that breaks `--previous`.
- Write prompts in **English**; quote any Japanese dialogue / on-screen text.
  Prefer Remotion captions over in-clip text for anything the user may want to
  re-word later.
- 720p is the default; use `--resolution 1080p` for a 1080p timeline
  (1080p / 4k are upscaled and use URI delivery automatically).
- Prompt guide: `<gemini-omni>/references/prompts.md`.

### 2b. veo (fallback)

Use veo only when gemini-omni is not installed / not available, or the user
explicitly asks for Veo (e.g. for `--seed`, `-n` variations, or an exact
4-8s clip).

```bash
python <veo>/scripts/generate.py \
  "slow dolly-in over the forest canopy, golden light" \
  --ratio 16:9 --duration 6 \
  --negative-prompt "background music, soundtrack, musical score, BGM" \
  -o <project>/public/video/scene2.mp4
```

- Defaults to the GA Veo 3.1 Fast model (add `--pro` / `--lite` only if asked).
- Requires Vertex AI (`GOOGLE_CLOUD_PROJECT`); `GEMINI_API_KEY` alone cannot run veo.
- Veo clips are 4-8s; size each scene's `durationInFrames` to the clip length
  (`seconds * fps`).

### ⚠️ Never let video clips carry their own BGM (music goes only in the lyria layer)

Both gemini-omni and veo generate native audio, and left unguided they may
**bake background music into the clip** (Omni picks its own soundtrack when the
prompt doesn't describe one). The clip's audio track keeps playing on the
timeline (`<OffthreadVideo>`), so any embedded music would stack on top of the
global lyria BGM and the two soundtracks would clash. To keep a single, coherent
music bed, **always suppress music when generating clips** — regardless of
whether this video has BGM:

- **gemini-omni**: there is no negative-prompt parameter. Describe the audio
  explicitly and end the prompt with
  `Sound design: <diegetic sounds>. No background music, no soundtrack, no musical score.`
- **veo**: always pass
  `--negative-prompt "background music, soundtrack, musical score, BGM"`
  (merge with any other negatives you need).
- **Do not request music** in the positive prompt — describe motion, camera,
  setting, lighting, and **diegetic sound only** (e.g. "wind through leaves",
  "footsteps on gravel", "ambient city hum"). Avoid asking for "music",
  "song", "score", "soundtrack".
- **Keep sound effects / ambience / dialogue.** SE and environmental audio are
  wanted — do **not** mute the clip. Suppression is music-only, done at
  generation time; the timeline plays the clip's audio as-is (the music
  suppression is what keeps it from fighting the BGM).
- Audio is generative, so suppression is best-effort. If a delivered clip still
  has audible music, fix that clip rather than muting the whole track, which
  would also kill the SE — gemini-omni:
  `--previous clip.mp4 "Remove the background music. Keep everything else the same."`;
  veo: regenerate (tweak the prompt / add a `--seed`).

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
- The text is read verbatim: put delivery direction in `--style` (not in the
  text), and use `<sigh>`-style tags for momentary vocalizations.

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
   claude plugin install gemini-omni
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
   | gemini-omni | Use veo for clips (needs Vertex AI); if neither is available, still images with Ken Burns |
   | veo | Not needed when gemini-omni is installed |
   | gemini-omni **and** veo | Still images with Ken Burns instead of video clips |
   | lyria | Omit BGM (silent), or a user-supplied music file in `public/audio/` |
   | gemini-tts | On-screen captions only (no voiceover), or user-supplied audio |

State clearly in the plan which assets are generated vs. fallback, so the user
can decide before approving.
