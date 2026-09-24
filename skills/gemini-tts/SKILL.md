---
name: gemini-tts
description: >
  Generate read-aloud audio (text-to-speech) using Google Gemini 3.8 TTS.
  Auto-selects the model by purpose: Gemini 3.8 Flash TTS for expressive
  narration and dialogue, Gemini 3.8 Flash-Lite TTS for long-form / bulk
  read-aloud. Automatically detects the mode from the input: single-speaker
  narration for plain text, and multi-speaker dialogue when the input has two
  "Name:" speaker labels. Supports 30 prebuilt voices, structured style
  control (speech_metadata) and inline vocal tags, text or file input, and
  WAV output. Works with both the Gemini Developer API and Vertex AI.
---

# Gemini TTS - Read-Aloud Speech Skill

Use the Python script in `scripts/` to turn text into natural read-aloud audio
via Google Gemini 3.8 TTS.

## Model Selection

The script **automatically selects** the model by purpose:

| Model | ID | When used |
|---|---|---|
| **Gemini 3.8 Flash TTS** | `gemini-3.8-flash-tts` | Expressive narration, dialogue, styled delivery, short text (default) |
| **Gemini 3.8 Flash-Lite TTS** | `gemini-3.8-flash-lite-tts` | Long-form / bulk read-aloud, drafts, cost-sensitive runs |

Selection rules (first match wins):

1. `TTS_MODEL` env var → that model
2. `--flash` / `--lite` → forced
3. Multi-speaker dialogue, a `--style`, or inline vocal tags (`<sigh>`) → **Flash**
4. Input of 2,000+ characters → **Flash-Lite**
5. Otherwise → **Flash**

> When choosing flags for the user: pass `--lite` for high-volume, real-time,
> or preview/draft narration; pass `--flash` when the best acting quality
> matters even for long input (e.g. an audiobook chapter).

| | Flash | Flash-Lite |
|---|---|---|
| Strength | Studio-grade fidelity, nuanced acting | Fast, cost-efficient |
| Languages | 130 | 101 |

## Speaker Mode

The mode is **automatically detected** from the input:

| Mode | When used | Voices |
|---|---|---|
| **Single-speaker** | Plain text / narration | One voice (`--voice`) |
| **Multi-speaker** | A 2-person dialogue: lines like `Name: ...` with exactly two distinct speakers | Two voices (`--speaker`) |

- Detected **2 speaker labels** → multi-speaker (2 is a hard limit)
- Detected **1 or 0** → single-speaker
- Detected **3+** → warns and falls back to single-speaker narration
- Override with `--single` / `--multi`

## Prerequisites

### 1. Install dependencies

```bash
pip install -U google-genai   # a recent version with SpeechMetadata support
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
| `TTS_MODEL` | _(auto)_ | Force a specific model (overrides auto-selection) |
| `AUDIO_OUTPUT_DIR` | `./gemini-tts` | Default output directory |
| `GEMINI_TTS_NO_SSL_VERIFY` | _(unset)_ | Set to `1` / `true` / `yes` to disable SSL certificate verification |

---

## Script

### `scripts/generate.py` - Text-to-speech generation

#### Basic narration (single voice)

```bash
python scripts/generate.py "Have a wonderful day!" -o hello.wav
```

#### Choose a voice and style

```bash
python scripts/generate.py "Welcome aboard!" --voice Puck --style "cheerful and friendly" -o welcome.wav
```

The text is read **verbatim** — do not embed directions like `Say cheerfully:`
in it. Put sustained delivery in `--style`, and point-in-time vocalizations
inline as angle-bracket tags, e.g. `<sigh>`, `<laughs>`, `<short pause>`.

#### Read text from a file (good for long input)

```bash
python scripts/generate.py -f article.txt -o article.wav
```

#### Multi-speaker dialogue (auto-detected)

Given `dialogue.txt`:

```
Taro: How's it going today, Hanako?
Hanako: Not too bad, how about you?
```

```bash
python scripts/generate.py -f dialogue.txt -o conversation.wav
```

The `Name:` labels are removed from the transcript and sent as
`speech_metadata.speaker`, so they are not read aloud. A label may also stand
alone on its line (`Taro:`) with the speech on the following lines. With a
half-width colon, put a space after it (`Taro: ...`); a full-width colon
(`太郎：...`) needs none. In single-speaker mode (including the 3+ speaker
fallback) the text, labels included, is read as-is.

#### Assign voices and styles to speakers explicitly

```bash
python scripts/generate.py -f dialogue.txt \
  --speaker "Taro:Kore" --speaker "Hanako:Puck" \
  --speaker-style "Taro:cheerful and friendly" --speaker-style "Hanako:calm and relaxed" \
  -o conversation.wav
```

`--style` applies to every speaker that has no `--speaker-style`.

#### Force a model

```bash
python scripts/generate.py -f article.txt --lite -o article.wav     # Flash-Lite
python scripts/generate.py -f chapter1.txt --flash -o chapter1.wav  # Flash
```

#### List available voices

```bash
python scripts/generate.py --list-voices
```

#### Disable SSL verification (for corporate proxies or self-signed certs)

```bash
python scripts/generate.py "hello" --no-ssl-verify -o hello.wav
```

#### JSON output (for programmatic use)

```bash
python scripts/generate.py "hello" --json -o hello.wav
```

#### Full options

```
usage: generate.py [-h] [-f FILE] [-o OUTPUT] [--voice VOICE]
                   [--speaker "Name:Voice"] [--speaker-style "Name:Style"]
                   [--style STYLE] [--temperature T] [--flash] [--lite]
                   [--single] [--multi] [--list-voices]
                   [-v] [--json] [--no-ssl-verify] [text]

Arguments:
  text                Text to read aloud (or use -f)

Options:
  -f, --file PATH     Read input text from a file
  -o, --output PATH   Output .wav file path (auto-generated if omitted)
  --voice VOICE       Voice for single-speaker mode (default: Zephyr)
  --speaker "N:V"     Multi-speaker voice mapping "Name:Voice" (repeatable)
  --speaker-style "N:S"  Multi-speaker style mapping "Name:Style" (repeatable)
  --style STYLE       Delivery style, sent as speech_metadata.style
                      (e.g. "cheerful and friendly")
  --temperature T     Sampling temperature (default: model default)
  --flash             Force Gemini 3.8 Flash TTS
  --lite              Force Gemini 3.8 Flash-Lite TTS
  --single            Force single-speaker mode
  --multi             Force multi-speaker mode (requires 2 "Name:" speakers)
  --list-voices       List the available prebuilt voices and exit
  -v, --verbose       Show detailed output
  --json              Output result as JSON
  --no-ssl-verify     Disable SSL certificate verification
```

> `--single` / `--multi` and `--flash` / `--lite` are each mutually exclusive.

---

## Output Format

The script streams the response, which arrives as headerless raw PCM
(`audio/l16`, 24 kHz, mono). It wraps it in a WAV header and saves a playable
**`.wav`** file (16-bit, 24 kHz, mono).

---

## Voices

30 prebuilt voices are available (e.g. **Zephyr** bright, **Puck** upbeat,
**Charon** informative, **Kore** firm, **Sulafat** warm, **Leda** youthful,
**Enceladus** breathy, **Achernar** soft). Flash supports 130 languages and
Flash-Lite 101 — the output language follows the input text's language.

Voice IDs from the Extended Voice Library or custom voice IDs (`voice_...` /
`voicekey_...`) can be passed to `--voice` as-is (single-speaker only;
multi-speaker uses prebuilt voices).

See `references/voices.md` for the full voice list with characteristics and a
style / audio-tag guide.

---

## Style & Delivery Control

Gemini 3.8 TTS treats the input text strictly as a **verbatim transcript**.

- **Sustained style**: `--style "calm and slow"` (or per speaker with
  `--speaker-style`) — sent as structured `speech_metadata.style`, not as text.
- **Inline vocal tags**: `<sigh>`, `<laughs>`, `<cough>`, `<short pause>`, etc.
  for point-in-time vocalizations. Use angle brackets for the best audio quality.
- **Multi-speaker**: label each line `Name: text`; the speaker names must match
  the `--speaker "Name:Voice"` / `--speaker-style` mappings exactly.
- **Do not** write stage directions (`Say cheerfully: ...`) in the text — they
  would be read aloud.

---

## Limitations

- **Supported models**: `gemini-3.8-flash-tts` and `gemini-3.8-flash-lite-tts`
  only. Older TTS models (`gemini-3.1-flash-tts-preview`, 2.5 previews) use a
  different prompt format and are not supported.
- **Input limit**: 8,192 input tokens per request — split very long text.
- **Multi-speaker cap**: at most **2** speakers per request.
- **No voice cloning**: requests to imitate a specific real person's voice are
  blocked by safety filters.

---

## Error Handling

| Error | Solution |
|---|---|
| `google-genai package not installed` | Run `pip install -U google-genai` |
| `SpeechMetadata` / `speech_metadata` errors | Upgrade: `pip install -U google-genai` |
| `No API credentials found` | Set `GEMINI_API_KEY` or `GOOGLE_CLOUD_PROJECT` |
| `Input text is empty` | Provide non-empty text via argument or `-f` |
| `Multi-speaker mode requires 2 ... speakers` | Use `Name:` labels for exactly 2 speakers, or drop `--multi` |
| `Content blocked by safety filters` | Rephrase the input (avoid impersonating real people) |
| `API rate limit reached` | Wait and retry |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Use `--no-ssl-verify` or set `GEMINI_TTS_NO_SSL_VERIFY=1` |
