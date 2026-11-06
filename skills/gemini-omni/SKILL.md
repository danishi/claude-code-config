---
name: gemini-omni
description: >
  Generate, edit, and extend videos with audio using Google Gemini Omni Flash
  (gemini-omni-1.1-flash) via the Interactions API. One model covers
  text-to-video, image-to-video, first/last frame interpolation, subject
  reference, editing uploaded videos, video extension, and multi-turn
  conversational editing ("make it anime", "keep everything else the same").
  Native audio (speech, music, SFX) and readable on-screen text. 16:9 / 9:16,
  360p-4k. Works with both the Gemini Developer API and Vertex AI. Use when
  the user asks for "Omni", "Gemini Omni", a video with sound, or to edit /
  extend / iterate on a video conversationally. Veo 3.1 Preview on the Gemini
  API was shut down on 2026-10-22, so prefer this skill for video generation
  with GEMINI_API_KEY.
---

# Gemini Omni - Multimodal Video Generation & Editing Skill

Use `scripts/generate.py` to generate and edit videos with **Gemini Omni Flash**.
It returns a video **with an audio track** (speech, music, sound effects).

| Platform | Model ID |
|---|---|
| Gemini Developer API (`GEMINI_API_KEY`) | `gemini-omni-1.1-flash` |
| Vertex AI (`GOOGLE_CLOUD_PROJECT`, location `global`) | `gemini-omni-1.1-flash-preview` |

`OMNI_MODEL` overrides the model ID.

## Mode is inferred from the inputs

There is no mode flag to pick. The model reads the prompt and the attached media:

| What you pass | Mode |
|---|---|
| prompt only | Text-to-video |
| `-i start.png` + prompt | Image-to-video (bring a photo / drawing to life) |
| `-i first.jpg -i last.jpg` + "transition from ... to ..." | First / last frame interpolation |
| `-i cat.png -i yarn.png` + "a cat plays with yarn" | Subject reference (up to 10 images) |
| `--video clip.mp4` + "make it anime" | Edit an uploaded video (≤10s) |
| `--video clip.mp4` + "Continue the scene" | Extend an uploaded video (+3-10s) |
| `--previous out.mp4` + instruction | Multi-turn edit / extend of a generated video |

`--task {text_to_video,image_to_video,reference_to_video,edit,extend}` forces a
mode, but use it **only as a fallback** when the prompt alone picks the wrong mode.

## Multi-turn editing (the main Omni feature)

Every run writes a sidecar `<output>.mp4.json` holding the `interaction_id`.
Pass the previous `.mp4` (or the ID) with `--previous` to keep editing without
re-uploading:

```bash
python scripts/generate.py "A woman playing violin outdoors, golden hour" -o v1.mp4
python scripts/generate.py "Make the violin invisible. Keep everything else the same." --previous v1.mp4 -o v2.mp4
python scripts/generate.py "Extend this video: she bows to the audience" --previous v2.mp4 -o v3.mp4
```

- `--no-store` speeds up a one-shot generation, but that result can't be used as `--previous`.
- Multi-turn extension can add dialogue; extending an *uploaded* video can't add new speech.
- Extension adds about 10s per turn, up to 40s total.

## Prerequisites

```bash
pip install -U google-genai   # needs a version with client.interactions (2.x)
```

Credentials (Vertex AI wins when both are set):

```bash
export GEMINI_API_KEY="your-api-key"          # Gemini Developer API
# or
export GOOGLE_CLOUD_PROJECT="your-project-id"  # Vertex AI (ADC required)
export GOOGLE_CLOUD_LOCATION="global"          # optional, default global
```

| Variable | Default | Description |
|---|---|---|
| `OMNI_MODEL` | _(per platform)_ | Force a model ID |
| `OMNI_OUTPUT_DIR` | `./gemini-omni` | Output dir when `-o` is omitted |
| `OMNI_NO_SSL_VERIFY` | _(unset)_ | `1` / `true` / `yes` disables SSL verification |

---

## Script usage

```bash
# Text-to-video (720p, 16:9)
python scripts/generate.py "Continuous single shot of a cat on a sunny windowsill. Sound: birds. No dialogue." -o cat.mp4

# Portrait 1080p (1080p / 4k automatically switch to URI delivery)
python scripts/generate.py "Neon cyberpunk street, rain" --ratio 9:16 --resolution 1080p -o city.mp4

# Image-to-video
python scripts/generate.py "Turn this drawing into realistic footage, use it only as a motion guide, do not show the drawing" -i fish.png -o fish.mp4

# Edit your own video (uploaded through the Files API)
python scripts/generate.py "When she touches the mirror, it ripples like liquid" --video mirror.mp4 -o mirror_edit.mp4

# Prompt from a file, JSON result
python scripts/generate.py -f prompt.txt --json -o out.mp4
```

```
usage: generate.py [-h] [-f FILE] [-o OUTPUT] [-i IMAGE] [--video VIDEO]
                   [-p PREVIOUS] [-r {16:9,9:16}]
                   [--resolution {360p,720p,1080p,4k}] [-d DURATION]
                   [--task {text_to_video,image_to_video,reference_to_video,edit,extend}]
                   [--delivery {inline,uri}] [--gcs-uri GCS_URI] [--no-store]
                   [-v] [--json] [--no-ssl-verify] [prompt]

  -i, --image       Input image, repeatable (max 10)
  --video           Video to edit / extend (≤10s, uploaded via Files API)
  -p, --previous    Interaction ID, a generated .mp4 (reads its sidecar), or the sidecar .json
  -r, --ratio       16:9 (default) or 9:16
  --resolution      360p / 720p (default) / 1080p / 4k  (1080p, 4k are upscaled)
  -d, --duration    e.g. "8s" — a response_format field the guide doesn't document; may be ignored
  --task            Force the mode (fallback only)
  --delivery        inline / uri (auto: uri for 1080p and 4k on the Gemini API)
  --gcs-uri         Vertex AI: gs:// destination required for URI delivery
  --no-store        store=false; faster, but not editable later
```

Output: the `.mp4` path on stdout (or JSON with `--json`), plus `<output>.mp4.json`.

---

## Prompting essentials (details in `references/prompts.md`)

1. **Want one shot? Say so.** By default Omni cuts between several shots to tell a
   story. Add `Continuous single shot, no scene cuts.`
2. **Describe the audio.** `Sound design: ...`, `calm background music`, `No dialogue.`
   Otherwise the model picks its own track.
3. **Negatives go in the prompt.** There is no negative-prompt / temperature /
   system instruction. Write `No dialogue. No extra sound effects.`
4. **Timing** in plain words or timecodes: `After 3 seconds, ...` / `[0-3s] ... [3-6s] ...`
5. **On-screen text renders correctly** — quote it: `a sign that says "OPEN"`.
6. **Edits: keep them short** and end with `Keep everything else the same.`
7. **English is the evaluated language.** Japanese prompts may work, but write the
   prompt in English and quote any Japanese dialogue or on-screen text.
8. Do not use `<FIRST_FRAME>` / `<IMAGE_REF_0>`-style control tags (deprecated);
   describe each image's role in words.

## Observed behavior (trial run, 2026-11-06, Gemini Developer API)

- Requests run with `background=True` and are polled, because a synchronous call
  can exceed the SDK's default HTTP timeout. Typical wall time: 40-75s per clip.
- Default output: 10s, 1280x720 (720x1280 with `--ratio 9:16`), H.264 + AAC audio, ~4MB.
- Extending returns the **whole** video (original 10s + extension = 20s), not just the new part.
- Image-to-video may show the input image itself in the first second even when
  told not to; trim with `ffmpeg -ss 1` if needed.
- Short edits ("make it claymation") change texture and style while keeping the
  composition and on-screen text.
- Subject reference (2 images: a toy robot + an umbrella) kept both designs faithfully.
- Uploaded-video edit / extend work through the Files API (upload is automatic).
  Keep input clips under 10s; trim first: `ffmpeg -i in.mp4 -t 9 clip.mp4`.
  An edit returns the same length as the input (9s in → 9s out). An extension
  returns input + ~10s (9s in → 19s out), and a reference image passed with
  `-i` brings that character into the extension.
- Status polls occasionally time out on the client (the finished response holds
  the video inline, several MB). Polls are retried automatically. If the script
  still dies after printing `Interaction ID: ...`, the video is safe on the server:
  `client.interactions.get(id=ID).output_video.data` holds it as base64.

## Limitations

- Input videos for edit / extend: ≤10s (multi-turn extension of generated videos is exempt). Max 3 videos per prompt.
- Extension only appends to the end. Voice editing is not supported. Audio references are not supported.
- Recognizable real people and (in EEA/CH/UK) minors can't be uploaded or edited.
  Editing / extending uploaded videos is unavailable in EEA/CH/UK.
- YouTube URLs can't be used as input.
- Every output carries an invisible SynthID watermark (plus C2PA on Vertex AI).

## Error handling

| Error | Fix |
|---|---|
| `google-genai package not installed` / no `interactions` attribute | `pip install -U google-genai` |
| `No API credentials found` | Set `GEMINI_API_KEY` or `GOOGLE_CLOUD_PROJECT` |
| `No video returned` | Probably blocked by safety filters; rephrase. The model's text, if any, is shown |
| Payload too large on 1080p / 4k | `--delivery uri` (automatic on the Gemini API); on Vertex add `--gcs-uri gs://...` |
| `No sidecar JSON found` for `--previous` | Pass the interaction ID directly |
| Edit of `--previous` fails | The earlier run used `--no-store`; regenerate without it |
| `SSL: CERTIFICATE_VERIFY_FAILED` | `--no-ssl-verify` or `OMNI_NO_SSL_VERIFY=1` |
| rate limit / quota | Wait and retry |
