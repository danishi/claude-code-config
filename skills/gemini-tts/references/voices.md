# Gemini TTS Voice & Style Reference

## Prebuilt Voices (30)

Voices are named after stars and moons. Pick one with `--voice <Name>` for
single-speaker, or map per speaker with `--speaker "Name:Voice"` for dialogue.
Voice names are case-insensitive in the script.

| Voice | Characteristic |
|---|---|
| Zephyr | Bright |
| Puck | Upbeat |
| Charon | Informative |
| Kore | Firm |
| Fenrir | Excitable |
| Leda | Youthful |
| Enceladus | Breathy |
| Achernar | Soft |
| Sulafat | Warm |
| Aoede | Breezy |
| Callirrhoe | Easygoing |
| Autonoe | Bright |
| Despina | Smooth |
| Erinome | Clear |
| Algenib | Gravelly |
| Rasalgethi | Informative |
| Laomedeia | Upbeat |
| Achird | Friendly |
| Algieba | Smooth |
| Alnilam | Firm |
| Schedar | Even |
| Gacrux | Mature |
| Pulcherrima | Forward |
| Umbriel | Easygoing |
| Vindemiatrix | Gentle |
| Sadachbia | Lively |
| Sadaltager | Knowledgeable |
| Iapetus | Clear |
| Orus | Firm |
| Zubenelgenubi | Casual |

> The characteristic labels are baseline guides; actual delivery is also shaped
> by the style and inline vocal tags.

Beyond these 30, voice IDs from the Extended Voice Library and custom voice IDs
(`voice_...` / `voicekey_...`) can be passed to `--voice` as-is
(single-speaker only).

---

## Style Control

Gemini 3.8 TTS treats the input text strictly as a **verbatim transcript** —
everything in the text is read aloud. Direction goes in two places instead.

### Sustained style (`speech_metadata.style`)

Describe the overall delivery with `--style`. The script sends it as
structured metadata, not as text:

```bash
python scripts/generate.py "Have a wonderful day!" --style "cheerful and friendly"
python scripts/generate.py -f story.txt --style "calm, slow, documentary narrator"
```

Do **not** write `Say cheerfully: ...` in the text; it would be spoken.

### Inline vocal tags (point-in-time)

Insert angle-bracket tags directly into the text for momentary vocalizations
(angle brackets give the highest audio quality):

```
<sigh>      <laughs>      <cough>      <short pause>
```

Example:

```
I have a secret... <short pause> and I can finally tell you! <laughs>
```

---

## Multi-Speaker Dialogue

- Label each line `Name: text` (the label is not read aloud).
- Use **exactly 2** distinct speakers (hard limit).
- Speaker names in the text must match the `--speaker "Name:Voice"` and
  `--speaker-style "Name:Style"` mappings.
- If you omit `--speaker`, default voices are assigned in first-seen order
  (`Kore`, then `Puck`).
- `--style` applies to speakers without their own `--speaker-style`.

Example `dialogue.txt`:

```
Taro: How's it going today, Hanako?
Hanako: Not too bad, how about you?
Taro: Pretty good — excited for the trip!
```

```bash
python scripts/generate.py -f dialogue.txt \
  --speaker "Taro:Charon" --speaker "Hanako:Leda" \
  --speaker-style "Taro:excited" --speaker-style "Hanako:calm and relaxed" \
  -o conversation.wav
```

You can still apply vocal tags per line:

```
Taro: We're finally going! <laughs>
Hanako: <sigh> I can't wait.
```

---

## Tips

- **Match language to text** — write the transcript in the language you want
  spoken (Flash: 130 languages, Flash-Lite: 101).
- **Pick voice by role** — informative narration (`Charon`, `Rasalgethi`),
  warm/friendly (`Sulafat`, `Achird`), youthful (`Leda`), firm/authoritative
  (`Kore`, `Alnilam`).
- **Long text** — read from a file with `-f` to avoid shell-escaping issues;
  2,000+ characters with no style or vocal tags auto-selects Flash-Lite
  (`--flash` to override).
- **Avoid impersonation** — describe a voice style rather than naming a real
  person; voice-cloning requests are blocked.
