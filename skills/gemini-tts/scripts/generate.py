#!/usr/bin/env python3
"""
Gemini TTS - Text-to-Speech narration using Google Gemini.

Generates read-aloud audio that matches the input.  The mode is
**automatically detected** from the input text:

  - Single-speaker : plain text / narration              -> one voice
  - Multi-speaker   : a 2-person dialogue ("Name: ..."    -> two voices
                      lines with exactly two speakers)

Model: gemini-3.1-flash-tts-preview (single TTS model; no Pro variant).
Supports both Gemini Developer API and Vertex AI API platforms.

Usage:
    python generate.py "Have a wonderful day!" -o hello.wav
    python generate.py "Say cheerfully: Welcome aboard!" --voice Puck
    python generate.py -f dialogue.txt -o conversation.wav
    python generate.py -f dialogue.txt --speaker "Taro:Kore" --speaker "Hanako:Puck"

Environment Variables:
    Gemini Developer API:
        GEMINI_API_KEY - API key from https://aistudio.google.com/apikey

    Vertex AI API:
        GOOGLE_CLOUD_PROJECT  - GCP project ID
        GOOGLE_CLOUD_LOCATION - GCP region (default: us-central1)

    Common:
        TTS_MODEL         - Force a specific model (overrides the default)
        AUDIO_OUTPUT_DIR  - Default output directory (default: ./gemini-tts)
"""

import argparse
import json
import os
import re
import ssl
import struct
import sys
import warnings
from datetime import datetime
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: google-genai package not installed.", file=sys.stderr)
    print("Install with: pip install google-genai", file=sys.stderr)
    sys.exit(1)

MODEL_TTS = "gemini-3.1-flash-tts-preview"

# 30 prebuilt voices. See references/voices.md for characteristics.
VALID_VOICES = [
    "Achernar", "Achird", "Algenib", "Algieba", "Alnilam", "Aoede",
    "Autonoe", "Callirrhoe", "Charon", "Despina", "Enceladus", "Erinome",
    "Fenrir", "Gacrux", "Iapetus", "Kore", "Laomedeia", "Leda", "Orus",
    "Puck", "Pulcherrima", "Rasalgethi", "Sadachbia", "Sadaltager",
    "Schedar", "Sulafat", "Umbriel", "Vindemiatrix", "Zephyr",
    "Zubenelgenubi",
]

DEFAULT_VOICE = "Zephyr"
# Default voices assigned to detected speakers, in order, for multi-speaker.
DEFAULT_SPEAKER_VOICES = ["Kore", "Puck", "Charon", "Aoede"]

# Multi-speaker is a hard limit of 2 speakers.
MAX_SPEAKERS = 2

_ssl_verification_disabled = False


def disable_ssl_verification() -> None:
    """Disable SSL certificate verification globally.

    Useful for environments behind corporate proxies or with self-signed
    certificates.  Called once when --no-ssl-verify is passed or when the
    GEMINI_TTS_NO_SSL_VERIFY environment variable is set.
    """
    global _ssl_verification_disabled
    if _ssl_verification_disabled:
        return

    # Override the default HTTPS context so that stdlib and libraries that
    # rely on ssl.create_default_context() skip certificate verification.
    ssl._create_default_https_context = ssl._create_unverified_context

    # Suppress noisy warnings about unverified requests.
    warnings.filterwarnings("ignore", message=".*certificate verify failed.*")
    warnings.filterwarnings("ignore", message=".*Unverified HTTPS.*")

    try:
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except ImportError:
        pass

    # Monkey-patch httpx (used internally by google-genai) so that any
    # Client / AsyncClient instances created later default to verify=False.
    try:
        import httpx

        _original_client_init = httpx.Client.__init__

        def _patched_client_init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            kwargs.setdefault("verify", False)
            _original_client_init(self, *args, **kwargs)

        httpx.Client.__init__ = _patched_client_init  # type: ignore[method-assign]

        _original_async_init = httpx.AsyncClient.__init__

        def _patched_async_init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            kwargs.setdefault("verify", False)
            _original_async_init(self, *args, **kwargs)

        httpx.AsyncClient.__init__ = _patched_async_init  # type: ignore[method-assign]
    except ImportError:
        pass

    _ssl_verification_disabled = True


def create_client(no_ssl_verify: bool = False) -> genai.Client:
    """Create a GenAI client based on available environment variables.

    Priority:
        1. Vertex AI (if GOOGLE_CLOUD_PROJECT is set)
        2. Gemini Developer API (if GEMINI_API_KEY is set)

    Args:
        no_ssl_verify: If True, disable SSL certificate verification.
    """
    if no_ssl_verify or os.environ.get("GEMINI_TTS_NO_SSL_VERIFY", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        disable_ssl_verification()

    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    api_key = os.environ.get("GEMINI_API_KEY")

    if project:
        return genai.Client(
            vertexai=True,
            project=project,
            location=location,
        )

    if api_key:
        return genai.Client(api_key=api_key)

    print(
        "Error: No API credentials found.\n"
        "Set one of:\n"
        "  GEMINI_API_KEY           - for Gemini Developer API\n"
        "  GOOGLE_CLOUD_PROJECT     - for Vertex AI API\n",
        file=sys.stderr,
    )
    sys.exit(1)


# A speaker label line looks like "Name: text" (Latin or full-width colon).
# Labels are short and free of sentence-ending punctuation.
#   - Full-width colon "：" : no following space required (Japanese style)
#   - Half-width colon ":"  : a following space is required, so timestamps
#                             like "10:30" are not mistaken for speakers.
_SPEAKER_RE = re.compile(r"^\s*([^\n:：。．！？!?]{1,24})(?:：\s*|:\s+)\S")


def detect_speakers(text: str) -> list[str]:
    """Return the distinct speaker labels found in dialogue lines, in order.

    A line is treated as dialogue when it starts with a short label followed
    by a colon (e.g. "Taro: ...", "Jane: ...").  Duplicates are removed while
    preserving first-seen order.
    """
    speakers: list[str] = []
    for line in text.splitlines():
        m = _SPEAKER_RE.match(line)
        if m:
            name = m.group(1).strip()
            if name and name not in speakers:
                speakers.append(name)
    return speakers


def resolve_voice(name: str) -> str:
    """Validate / normalize a voice name (case-insensitive)."""
    for v in VALID_VOICES:
        if v.lower() == name.lower():
            return v
    print(
        f"Warning: '{name}' is not a known voice. Valid voices: "
        f"{', '.join(VALID_VOICES)}",
        file=sys.stderr,
    )
    return name


def parse_audio_mime_type(mime_type: str) -> dict:
    """Parse bits-per-sample and sample rate from an audio MIME type.

    Assumes bits per sample is encoded like "L16" and rate as "rate=xxxxx"
    (e.g. "audio/L16;rate=24000").  Falls back to 16-bit / 24000 Hz.
    """
    bits_per_sample = 16
    rate = 24000

    for param in mime_type.split(";"):
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate = int(param.split("=", 1)[1])
            except (ValueError, IndexError):
                pass
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass

    return {"bits_per_sample": bits_per_sample, "rate": rate}


def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """Wrap raw PCM audio data in a WAV (RIFF) header.

    Gemini TTS returns raw PCM (e.g. "audio/L16;rate=24000") which needs a
    WAV header to be playable as a .wav file.  http://soundfile.sapp.org/doc/WaveFormat/
    """
    params = parse_audio_mime_type(mime_type)
    bits_per_sample = params["bits_per_sample"]
    sample_rate = params["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", chunk_size, b"WAVE", b"fmt ", 16, 1,
        num_channels, sample_rate, byte_rate, block_align,
        bits_per_sample, b"data", data_size,
    )
    return header + audio_data


def generate_output_path(output_dir: str | None = None) -> str:
    """Generate a timestamped output file path."""
    if output_dir is None:
        output_dir = os.environ.get("AUDIO_OUTPUT_DIR", "./gemini-tts")

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return str(Path(output_dir) / f"tts_{ts}.wav")


def build_speech_config(
    text: str,
    voice: str,
    speaker_map: dict[str, str] | None,
    force_single: bool,
    force_multi: bool,
    verbose: bool,
) -> tuple["types.SpeechConfig", str]:
    """Build the SpeechConfig and return (config, mode).

    Mode is "single" or "multi".  Multi-speaker is auto-detected from the
    input unless overridden by force_single / force_multi.
    """
    speakers = detect_speakers(text)

    use_multi = False
    if force_multi:
        use_multi = True
    elif force_single:
        use_multi = False
    elif len(speakers) == MAX_SPEAKERS:
        use_multi = True
    elif len(speakers) > MAX_SPEAKERS:
        print(
            f"Warning: {len(speakers)} speakers detected but multi-speaker "
            f"supports at most {MAX_SPEAKERS}. Falling back to single-speaker "
            "narration.",
            file=sys.stderr,
        )

    if use_multi:
        if len(speakers) < 2:
            raise ValueError(
                "Multi-speaker mode requires 2 distinct 'Name:' speaker labels "
                "in the input."
            )
        speakers = speakers[:MAX_SPEAKERS]
        speaker_map = speaker_map or {}
        configs = []
        for i, name in enumerate(speakers):
            v = speaker_map.get(name) or DEFAULT_SPEAKER_VOICES[
                i % len(DEFAULT_SPEAKER_VOICES)
            ]
            v = resolve_voice(v)
            if verbose:
                print(f"Speaker '{name}' -> voice {v}")
            configs.append(
                types.SpeakerVoiceConfig(
                    speaker=name,
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=v
                        )
                    ),
                )
            )
        speech_config = types.SpeechConfig(
            multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                speaker_voice_configs=configs
            )
        )
        return speech_config, "multi"

    voice = resolve_voice(voice)
    if verbose:
        print(f"Voice: {voice}")
    speech_config = types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
        )
    )
    return speech_config, "single"


def generate_speech(
    text: str,
    output_path: str | None = None,
    voice: str = DEFAULT_VOICE,
    speaker_map: dict[str, str] | None = None,
    style: str | None = None,
    temperature: float = 1.0,
    force_single: bool = False,
    force_multi: bool = False,
    verbose: bool = False,
    no_ssl_verify: bool = False,
) -> dict:
    """Generate read-aloud audio from text using Gemini TTS.

    Args:
        text:           The text / transcript to read aloud.
        output_path:    Where to save the audio (.wav).
        voice:          Voice name for single-speaker mode.
        speaker_map:    {speaker_label: voice_name} for multi-speaker mode.
        style:          Optional style prefix (e.g. "cheerfully") for single
                        speaker; prepended as "Say {style}: ".
        temperature:    Sampling temperature (default 1.0).
        force_single:   Force single-speaker mode.
        force_multi:    Force multi-speaker mode.
        verbose:        Print progress information.
        no_ssl_verify:  Disable SSL certificate verification.

    Returns:
        dict with keys: success (bool), path (str|None), mode (str|None),
        text (str|None), error (str|None), metadata (dict|None).
    """
    if not text or not text.strip():
        return {
            "success": False,
            "error": "Input text is empty.",
            "path": None,
            "mode": None,
            "text": None,
            "metadata": None,
        }

    client = create_client(no_ssl_verify=no_ssl_verify)
    model = os.environ.get("TTS_MODEL", MODEL_TTS)

    try:
        speech_config, mode = build_speech_config(
            text=text,
            voice=voice,
            speaker_map=speaker_map,
            force_single=force_single,
            force_multi=force_multi,
            verbose=verbose,
        )
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "path": None,
            "mode": None,
            "text": None,
            "metadata": None,
        }

    prompt_text = text
    if style and mode == "single":
        prompt_text = f"Say {style}: {text}"

    contents = [
        types.Content(role="user", parts=[types.Part.from_text(text=prompt_text)]),
    ]

    generate_config = types.GenerateContentConfig(
        temperature=temperature,
        response_modalities=["AUDIO"],
        speech_config=speech_config,
    )

    if output_path is None:
        output_path = generate_output_path()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"Model: {model}")
        print(f"Mode: {mode}")
        print("Generating speech...")

    try:
        audio_chunks: list[bytes] = []
        mime_type: str | None = None
        text_response: str | None = None

        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_config,
        ):
            if chunk.parts is None:
                continue
            for part in chunk.parts:
                if part.inline_data and part.inline_data.data:
                    audio_chunks.append(part.inline_data.data)
                    if mime_type is None:
                        mime_type = part.inline_data.mime_type
                elif getattr(part, "text", None):
                    text_response = (text_response or "") + part.text

        if not audio_chunks:
            return {
                "success": False,
                "error": text_response
                or "No audio returned. The prompt may have been blocked by safety filters.",
                "path": None,
                "mode": mode,
                "text": text_response,
                "metadata": None,
            }

        raw = b"".join(audio_chunks)
        # Gemini TTS returns raw PCM (e.g. audio/L16;rate=24000); wrap in WAV.
        wav_bytes = convert_to_wav(raw, mime_type or "audio/L16;rate=24000")

        with open(output_path, "wb") as f:
            f.write(wav_bytes)

        if verbose:
            print(f"Saved: {output_path}")

        return {
            "success": True,
            "path": output_path,
            "mode": mode,
            "text": text_response,
            "error": None,
            "metadata": {
                "model": model,
                "mode": mode,
                "voice": voice if mode == "single" else None,
                "mime_type": mime_type,
                "timestamp": datetime.now().isoformat(),
            },
        }

    except Exception as e:
        msg = str(e)
        if "safety" in msg.lower():
            msg = "Content blocked by safety filters. Try rephrasing your input."
        elif "quota" in msg.lower() or "rate" in msg.lower():
            msg = "API rate limit reached. Wait a moment and retry."
        return {
            "success": False,
            "error": msg,
            "path": None,
            "mode": mode,
            "text": None,
            "metadata": None,
        }


def _parse_speaker_args(items: list[str] | None) -> dict[str, str]:
    """Parse repeated --speaker "Name:Voice" args into a mapping."""
    mapping: dict[str, str] = {}
    if not items:
        return mapping
    for item in items:
        if ":" not in item:
            print(
                f"Warning: ignoring --speaker '{item}' (expected 'Name:Voice').",
                file=sys.stderr,
            )
            continue
        name, voice = item.split(":", 1)
        name, voice = name.strip(), voice.strip()
        if name and voice:
            mapping[name] = voice
    return mapping


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate read-aloud audio using Gemini TTS (auto-detects single/multi-speaker)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s "Have a wonderful day!" -o hello.wav
  %(prog)s "Welcome aboard!" --voice Puck --style cheerfully
  %(prog)s -f dialogue.txt -o conversation.wav
  %(prog)s -f dialogue.txt --speaker "Taro:Kore" --speaker "Hanako:Puck"
""",
    )

    parser.add_argument("text", nargs="?", help="Text to read aloud (or use -f)")
    parser.add_argument("-f", "--file", help="Read input text from a file")
    parser.add_argument("-o", "--output", help="Output .wav file path")
    parser.add_argument(
        "--voice", default=DEFAULT_VOICE,
        help=f"Voice for single-speaker mode (default: {DEFAULT_VOICE})",
    )
    parser.add_argument(
        "--speaker", action="append", dest="speakers",
        help='Multi-speaker voice mapping "Name:Voice" (repeatable)',
    )
    parser.add_argument(
        "--style",
        help='Style prefix for single-speaker (e.g. "cheerfully", "in a calm voice")',
    )
    parser.add_argument(
        "--temperature", type=float, default=1.0,
        help="Sampling temperature (default: 1.0)",
    )
    parser.add_argument(
        "--single", action="store_true",
        help="Force single-speaker mode",
    )
    parser.add_argument(
        "--multi", action="store_true",
        help="Force multi-speaker mode (requires 2 'Name:' speakers)",
    )
    parser.add_argument(
        "--list-voices", action="store_true",
        help="List the available prebuilt voices and exit",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Show detailed output",
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Output result as JSON",
    )
    parser.add_argument(
        "--no-ssl-verify", action="store_true",
        help="Disable SSL certificate verification (for proxies or self-signed certs)",
    )

    args = parser.parse_args()

    if args.list_voices:
        print("\n".join(VALID_VOICES))
        sys.exit(0)

    if args.single and args.multi:
        print("Error: --single and --multi are mutually exclusive.", file=sys.stderr)
        sys.exit(2)

    # Resolve input text from positional arg or file.
    if args.file:
        try:
            text = Path(args.file).read_text(encoding="utf-8")
        except OSError as e:
            print(f"Error: cannot read file '{args.file}': {e}", file=sys.stderr)
            sys.exit(1)
    elif args.text:
        text = args.text
    else:
        print("Error: provide text as an argument or via -f/--file.", file=sys.stderr)
        sys.exit(2)

    result = generate_speech(
        text=text,
        output_path=args.output,
        voice=args.voice,
        speaker_map=_parse_speaker_args(args.speakers),
        style=args.style,
        temperature=args.temperature,
        force_single=args.single,
        force_multi=args.multi,
        verbose=args.verbose or (args.output is None and not args.json_output),
        no_ssl_verify=args.no_ssl_verify,
    )

    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["success"]:
        print(result["path"])
    else:
        print(f"Error: {result['error']}", file=sys.stderr)

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
