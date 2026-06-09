---
name: lyria
description: >
  Generate music files using Google Gemini Lyria 3.
  Automatically selects the best model based on the request / purpose:
  Lyria 3 Pro for full-length, structured, lyric-bearing songs and
  Lyria 3 Clip for 30-second clips, loops, jingles, and quick previews.
  Supports genre / mood / instrument prompting, song-structure tags,
  custom lyrics, MP3 / WAV output, and works with both the Gemini
  Developer API and Vertex AI.
---

# Lyria - AI Music Generation Skill

Use the Python script in `scripts/` to generate music via Google Gemini Lyria 3.
The model is **automatically selected** based on the request / purpose:

| Model | ID | When used |
|---|---|---|
| **Lyria 3 Pro** | `lyria-3-pro-preview` | Full-length songs (≈ a couple of minutes), verses/choruses/bridges, lyrics, premium studio-quality output |
| **Lyria 3 Clip** | `lyria-3-clip-preview` | 30-second clips, loops, jingles, sound logos, quick previews / prompt iteration |

**Lyria 3 Pro is auto-selected when any of these conditions are met (OR):**

- `--pro` flag is specified
- Prompt contains full-song keywords (e.g. `歌詞`, `フル尺`, `楽曲`, `full-length`, `verse`, `chorus`, `lyrics`, `professional`)
- Prompt is 100+ characters long

**Lyria 3 Clip is selected when:**

- `--clip` flag is specified
- Prompt contains clip keywords (e.g. `ループ`, `ジングル`, `30秒`, `clip`, `loop`, `jingle`, `preview`)
- None of the Pro conditions are met (Clip is the default — fast and cheap, ideal for iterating on prompts)

> **Tip:** Iterate on your prompt with the faster `--clip` model first, then
> commit to a full-length generation with `--pro`.

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
| `LYRIA_MODEL` | _(auto)_ | Force a specific model (overrides auto-selection) |
| `AUDIO_OUTPUT_DIR` | `./lyria-music` | Default output directory |
| `LYRIA_NO_SSL_VERIFY` | _(unset)_ | Set to `1` / `true` / `yes` to disable SSL certificate verification |

---

## Script

### `scripts/generate.py` - Music generation

#### Basic generation (auto-selects model)

```bash
python scripts/generate.py "lofi hip hop, mellow piano, rainy night, relaxed beat"
```

#### Force a short clip (fast iteration / loops / jingles)

```bash
python scripts/generate.py "upbeat synthwave jingle, 80s, short loop" --clip -o jingle.mp3
```

#### Force a full-length song (with structure tags and lyrics)

```bash
python scripts/generate.py \
  "[Verse] city lights fade into the night [Chorus] we are still alive, dreaming, full pop ballad, female vocals" \
  --pro -o song.mp3
```

#### Request WAV output (Pro only; Clip outputs MP3)

```bash
python scripts/generate.py "epic orchestral cinematic, full-length, dramatic" --pro --wav -o cinematic.wav
```

#### Disable SSL verification (for corporate proxies or self-signed certs)

```bash
python scripts/generate.py "ambient pad, calm" --no-ssl-verify -o ambient.mp3
```

#### JSON output (for programmatic use)

```bash
python scripts/generate.py "jazz trio, walking bass" --json -o jazz.mp3
```

#### Full options

```
usage: generate.py [-h] [-o OUTPUT] [--pro] [--clip] [--wav] [-v]
                   [--json] [--no-ssl-verify] prompt

Arguments:
  prompt              Text prompt describing the music

Options:
  -o, --output PATH   Output file path (auto-generated if omitted; extension
                      derived from the returned audio MIME type)
  --pro               Force Lyria 3 Pro model (full-length songs)
  --clip              Force Lyria 3 Clip model (30s clips, loops, jingles)
  --wav               Request WAV output (Pro only; Clip outputs MP3)
  -v, --verbose       Show detailed output
  --json              Output result as JSON
  --no-ssl-verify     Disable SSL certificate verification
```

> `--pro` and `--clip` are mutually exclusive.

---

## Output Format

| Model | Default format | Notes |
|---|---|---|
| Lyria 3 Clip | MP3, 48 kHz stereo | Always ~30-second clips |
| Lyria 3 Pro | MP3 (or WAV with `--wav`), 48 kHz stereo | Full-length songs (≈ a couple of minutes) |

The output file extension is derived from the audio MIME type returned by the API.

---

## Prompting Tips

A good music prompt combines several dimensions:

1. **Genre / style** — `lofi hip hop`, `synthwave`, `orchestral`, `jazz`, `EDM`
2. **Mood / atmosphere** — `melancholic`, `uplifting`, `tense`, `dreamy`
3. **Instruments / arrangement** — `mellow piano`, `driving bass`, `string section`
4. **Tempo / rhythm** — `slow 70 BPM`, `fast four-on-the-floor`, `swing`
5. **Vocals** (Pro) — `female vocals, warm timbre`, `male rap`, or `instrumental`

**Song structure** (Pro): use section tags so the model builds verses, choruses,
and bridges:

```
[Verse] ... lyrics ...
[Chorus] ... lyrics ...
[Bridge] ... lyrics ...
```

You can also add **timestamps** for precise timing, e.g. `[0:00 - 0:10] soft intro`.
The prompt language determines the sung language.

See `references/prompts.md` for a comprehensive prompt reference with
category-specific templates.

---

## Limitations

- **Single-turn**: each call is independent; there is no multi-turn editing of a
  previously generated track.
- **No artist voice cloning**: prompts that request a specific real artist's
  voice are blocked by safety filters.
- **No negative prompts / seed**: describe what you want directly in the prompt.

---

## Error Handling

| Error | Solution |
|---|---|
| `google-genai package not installed` | Run `pip install google-genai` |
| `No API credentials found` | Set `GEMINI_API_KEY` or `GOOGLE_CLOUD_PROJECT` |
| `Content blocked by safety filters` | Rephrase the prompt (avoid named artists / restricted content) |
| `API rate limit reached` | Wait and retry |
| `No audio returned` | Make the prompt more concrete (genre, mood, instruments) |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Use `--no-ssl-verify` or set `LYRIA_NO_SSL_VERIFY=1` |
