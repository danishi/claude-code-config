---
name: veo
description: >
  Generate videos using Google Veo 3.1 on Vertex AI. Defaults to the GA
  Veo 3.1 Fast model (veo-3.1-fast-generate-001); the premium Veo 3.1 and the
  cheaper Veo 3.1 Lite (Preview) models are used only when explicitly requested
  via --pro / --lite. Supports text-to-video and image-to-video (first frame +
  optional last frame), 16:9 / 9:16, 720p / 1080p (4k on Pro), 4-8s clips, and
  1-4 videos per request. Requires Vertex AI (GOOGLE_CLOUD_PROJECT); the Gemini
  Developer API no longer serves Veo.
---

# Veo - AI Video Generation Skill

Use the Python script in `scripts/` to generate videos via Google Veo 3.1 on Vertex AI.

> **Default model is the GA Fast model.** Pro and Lite are used **only when
> explicitly requested.**

| Flag | Model | Stage | When used |
|---|---|---|---|
| _(default)_ / `--fast` | `veo-3.1-fast-generate-001` | GA | Fast / balanced cost; used unless a flag says otherwise |
| `--pro` | `veo-3.1-generate-001` | GA | Premium / cinematic, 4k — explicit only |
| `--lite` | `veo-3.1-lite-generate-001` | Preview | Cheapest — explicit only |

`--pro`, `--fast` and `--lite` are mutually exclusive. The `VEO_MODEL` env var overrides everything.

> **Gemini Developer API is no longer supported.** The
> `veo-3.1-*-generate-preview` models were shut down on 2026-10-22, and the
> Gemini Developer API (`GEMINI_API_KEY`) no longer serves any Veo model. If
> only `GEMINI_API_KEY` is set, the script exits with migration guidance.
> To generate video with `GEMINI_API_KEY`, use the
> [gemini-omni](../gemini-omni/SKILL.md) skill (Gemini Omni Flash) instead.

## Prerequisites

### 1. Install dependencies

```bash
pip install google-genai
```

### 2. Configure Vertex AI credentials

Set `GOOGLE_CLOUD_PROJECT` and optionally `GOOGLE_CLOUD_LOCATION`.
Requires a GCP project with the Vertex AI API enabled and
Application Default Credentials configured (`gcloud auth application-default login`).

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"   # optional; Veo 3.1 is served only in us-central1
```

### 3. Optional environment variables

| Variable | Default | Description |
|---|---|---|
| `VEO_MODEL` | `veo-3.1-fast-generate-001` | Force a specific model (overrides flags) |
| `VIDEO_OUTPUT_DIR` | `./veo-videos` | Default output directory |
| `VEO_NO_SSL_VERIFY` | _(unset)_ | Set to `1` / `true` / `yes` to disable SSL certificate verification |

---

## Script

### `scripts/generate.py` - Video generation

Video generation is a long-running operation; the script submits the request
and polls until the video is ready, then downloads and saves the `.mp4`.

#### Text-to-video (default Fast model)

```bash
python scripts/generate.py "a cat surfing a wave, cinematic lighting" -o cat.mp4
```

#### Portrait, 6-second clip

```bash
python scripts/generate.py "slow zoom over a city at dawn" --ratio 9:16 --duration 6 -o city.mp4
```

#### Image-to-video (animate a starting frame)

```bash
python scripts/generate.py "gentle breeze, leaves drifting" -i start.jpg -o anim.mp4
```

#### First + last frame (constrain the ending)

```bash
python scripts/generate.py "morph from sunrise to sunset" -i sunrise.jpg --last-frame sunset.jpg -o morph.mp4
```

#### Premium model with 1080p (explicit opt-in)

```bash
python scripts/generate.py "epic drone shot over mountains" --pro --resolution 1080p -o drone.mp4
```

#### Cheapest model (explicit opt-in)

```bash
python scripts/generate.py "abstract liquid motion" --lite -o liquid.mp4
```

#### Multiple variations

```bash
python scripts/generate.py "abstract liquid motion" -n 4 -o liquid.mp4
# -> liquid_0.mp4, liquid_1.mp4, liquid_2.mp4, liquid_3.mp4
```

#### Disable SSL verification (for corporate proxies or self-signed certs)

```bash
python scripts/generate.py "ocean waves" --no-ssl-verify -o waves.mp4
```

#### JSON output (for programmatic use)

```bash
python scripts/generate.py "ocean waves" --json -o waves.mp4
```

#### Full options

```
usage: generate.py [-h] [-o OUTPUT] [-i IMAGE] [--last-frame PATH]
                   [-r {16:9,9:16}] [--resolution {720p,1080p,4k}]
                   [-d DURATION] [-n COUNT]
                   [--person-generation {auto,dont_allow,allow_adult,allow_all}]
                   [--negative-prompt TEXT] [--seed SEED]
                   [--pro | --fast | --lite]
                   [--poll-interval SECS] [--timeout SECS] [-v] [--json]
                   [--no-ssl-verify] prompt

Arguments:
  prompt                  Text prompt for video generation

Options:
  -o, --output PATH       Output .mp4 path (index suffix added if -n > 1)
  -i, --image PATH        Starting frame image (image-to-video)
  --last-frame PATH       Ending frame image (constraint)
  -r, --ratio RATIO       Aspect ratio: 16:9 or 9:16 (default: 16:9)
  --resolution RES        720p, 1080p, or 4k (4k requires --pro)
  -d, --duration SECS     Clip duration in seconds (default: 8)
  -n, --count N           Number of videos, 1-4 (default: 1)
  --person-generation P   auto / dont_allow / allow_adult / allow_all
                          (default: auto = allow_adult)
  --negative-prompt TEXT  Things to avoid in the video
  --seed SEED             Seed for improved consistency
  --pro                   Use the premium Veo 3.1 model (explicit)
  --fast                  Use the Veo 3.1 Fast model (default)
  --lite                  Use the Veo 3.1 Lite model (Preview, explicit)
  --poll-interval SECS    Seconds between status checks (default: 10)
  --timeout SECS          Max seconds to wait (default: no limit)
  -v, --verbose           Show detailed output
  --json                  Output result as JSON
  --no-ssl-verify         Disable SSL certificate verification
```

---

## Capabilities & Limits

| Capability | Fast (default) | Pro (`--pro`) | Lite (`--lite`) |
|---|---|---|---|
| Launch stage | GA | GA | Preview |
| Text-to-video | ✅ | ✅ | ✅ |
| Image-to-video (first / last frame) | ✅ | ✅ | ✅ |
| Aspect ratios | 16:9, 9:16 | 16:9, 9:16 | 16:9, 9:16 |
| Resolution | 720p, 1080p | 720p, 1080p, 4k | 720p, 1080p |
| Duration | 4 / 6 / 8 s | 4 / 6 / 8 s | 4 / 6 / 8 s |
| Reference images | ✅ | ✅ | ❌ |
| Video extension | ✅ | ✅ | ✅ |
| Native audio | ✅ | ✅ | ✅ |

Notes:
- **1080p** typically requires an **8-second** duration.
- **4k** is available **only on Pro** — use `--pro`.
- Veo 3.1 is served only in the **`us-central1`** region.
- Reference images and video extension are not exposed by `scripts/generate.py`.

### Person generation policy

The `--person-generation` policy controls whether people appear in the output.
Vertex AI accepts `dont_allow`, `allow_adult` and `allow_all`; the default
`auto` resolves to `allow_adult`.

---

## Prompting Tips

A strong video prompt describes motion and cinematography, not just a static scene:

1. **Subject & action** — what happens (`a fox leaps across a stream`)
2. **Camera** — shot type / movement (`slow dolly-in`, `aerial drone shot`, `handheld`)
3. **Setting & lighting** — (`misty forest at golden hour`)
4. **Style** — (`cinematic`, `anime`, `documentary`, `35mm film`)
5. **Pace** — (`slow motion`, `time-lapse`)

Use `--negative-prompt` to steer away from unwanted elements, and `--seed` to
keep results consistent across runs.

See `references/prompts.md` for category-specific templates.

---

## Error Handling

| Error | Solution |
|---|---|
| `google-genai package not installed` | Run `pip install google-genai` |
| `No API credentials found` | Set `GOOGLE_CLOUD_PROJECT` and run `gcloud auth application-default login` |
| `Veo is no longer available on the Gemini Developer API` | Only `GEMINI_API_KEY` is set. Switch to Vertex AI (`GOOGLE_CLOUD_PROJECT`), or use the gemini-omni skill |
| `only the premium Veo 3.1 model supports 4k` | Use `--pro` for 4k, or pick 720p/1080p |
| `404` / model not found | Check `GOOGLE_CLOUD_LOCATION` is `us-central1` and the model ID in `VEO_MODEL` |
| `No videos were generated` | Rephrase the prompt; it may have been blocked |
| `Content blocked by safety filters` | Rephrase; check `--person-generation` policy |
| `Timed out ... waiting` | Increase `--timeout` or omit it (no limit) |
| `API rate limit reached` | Wait and retry |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Use `--no-ssl-verify` or set `VEO_NO_SSL_VERIFY=1` |
