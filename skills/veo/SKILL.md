---
name: veo
description: >
  Generate videos using Google Gemini Veo 3.1. Defaults to the cost-effective
  Veo 3.1 Lite model; the premium (Veo 3.1) and Fast models are used only when
  explicitly requested via --pro / --fast. Supports text-to-video and
  image-to-video (first frame + optional last frame), 16:9 / 9:16, 720p / 1080p
  (4k on Pro), 4-8s clips, and 1-4 videos per request. Works with both the
  Gemini Developer API and Vertex AI.
---

# Veo - AI Video Generation Skill

Use the Python script in `scripts/` to generate videos via Google Gemini Veo 3.1.

> **Default model is the cheapest one.** The more expensive models are used
> **only when explicitly requested.**

| Flag | Model | When used |
|---|---|---|
| _(default)_ | `veo-3.1-lite-generate-preview` | Cost-effective; used unless a flag says otherwise |
| `--pro` | `veo-3.1-generate-preview` | Premium / cinematic, 4k, native audio — explicit only |
| `--fast` | `veo-3.1-fast-generate-preview` | Faster generation — explicit only |

`--pro` and `--fast` are mutually exclusive. The `VEO_MODEL` env var overrides everything.

## Prerequisites

### 1. Install dependencies

```bash
pip install google-genai
```

### 2. Configure API credentials (one of the following)

#### Option A: Gemini Developer API (recommended for personal use)

Set the `GEMINI_API_KEY` environment variable.
Get a key at https://aistudio.google.com/apikey

```bash
export GEMINI_API_KEY="your-api-key"
```

#### Option B: Vertex AI API (for Google Cloud users)

Set `GOOGLE_CLOUD_PROJECT` and optionally `GOOGLE_CLOUD_LOCATION`.
Requires a GCP project with the Vertex AI API enabled and
Application Default Credentials configured (`gcloud auth application-default login`).

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"   # optional, defaults to us-central1
```

> **Priority:** If both `GOOGLE_CLOUD_PROJECT` and `GEMINI_API_KEY` are set,
> Vertex AI is used.

### 3. Optional environment variables

| Variable | Default | Description |
|---|---|---|
| `VEO_MODEL` | `veo-3.1-lite-generate-preview` | Force a specific model (overrides flags) |
| `VIDEO_OUTPUT_DIR` | `./veo-videos` | Default output directory |
| `VEO_NO_SSL_VERIFY` | _(unset)_ | Set to `1` / `true` / `yes` to disable SSL certificate verification |

---

## Script

### `scripts/generate.py` - Video generation

Video generation is a long-running operation; the script submits the request
and polls until the video is ready, then downloads and saves the `.mp4`.

#### Text-to-video (default Lite model)

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
                   [--negative-prompt TEXT] [--seed SEED] [--pro] [--fast]
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
                          (default: auto = allow_all on Gemini Developer API,
                          allow_adult on Vertex AI)
  --negative-prompt TEXT  Things to avoid in the video
  --seed SEED             Seed for improved consistency
  --pro                   Use the premium Veo 3.1 model (explicit)
  --fast                  Use the Veo 3.1 Fast model (explicit)
  --poll-interval SECS    Seconds between status checks (default: 10)
  --timeout SECS          Max seconds to wait (default: no limit)
  -v, --verbose           Show detailed output
  --json                  Output result as JSON
  --no-ssl-verify         Disable SSL certificate verification
```

---

## Capabilities & Limits

| Capability | Lite (default) | Pro (`--pro`) / Fast (`--fast`) |
|---|---|---|
| Text-to-video | ✅ | ✅ |
| Image-to-video (first / last frame) | ✅ | ✅ |
| Aspect ratios | 16:9, 9:16 | 16:9, 9:16 |
| Resolution | 720p, 1080p (8s) | + 4k |
| Duration | 4 / 6 / 8 s | 4 / 6 / 8 s |
| Reference images, video extension | ❌ | ✅ (Pro / Fast) |

Notes:
- **1080p** typically requires an **8-second** duration.
- **4k** is **not** available on Lite — use `--pro`.

### Person generation policy

The `--person-generation` policy controls whether people appear in the output:

| Platform | Supported values | Default (`auto`) |
|---|---|---|
| **Gemini Developer API** (`GEMINI_API_KEY`) | **`allow_all` only** — `dont_allow` / `allow_adult` are currently **rejected** | `allow_all` |
| **Vertex AI** (`GOOGLE_CLOUD_PROJECT`) | `dont_allow`, `allow_adult`, `allow_all` | `allow_adult` |

- The default is **`auto`**, which picks a platform-safe value automatically.
- As a safety net, if the API rejects the chosen value with a
  `personGeneration ... not supported` error, the script **automatically
  retries once with `allow_all`** — so a single run succeeds without manual
  intervention.

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
| `No API credentials found` | Set `GEMINI_API_KEY` or `GOOGLE_CLOUD_PROJECT` |
| `Veo 3.1 Lite does not support 4k` | Use `--pro` for 4k, or pick 720p/1080p |
| `No videos were generated` | Rephrase the prompt; it may have been blocked |
| `personGeneration is currently not supported` | The Gemini Developer API only supports `allow_all`. The script auto-retries with `allow_all`; or pass `--person-generation allow_all` explicitly |
| `Content blocked by safety filters` | Rephrase; check `--person-generation` policy |
| `Timed out ... waiting` | Increase `--timeout` or omit it (no limit) |
| `API rate limit reached` | Wait and retry |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Use `--no-ssl-verify` or set `VEO_NO_SSL_VERIFY=1` |
