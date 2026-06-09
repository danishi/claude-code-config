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
> by the prompt, style prefix, and audio tags.

---

## Style Control

### Natural-language prefix

Prepend an instruction describing the desired delivery:

```
Say cheerfully: Have a wonderful day!
Read this slowly and calmly: Take a deep breath, and relax.
Announce dramatically: And the winner is...
```

The `--style` flag is a shortcut that prepends `Say <style>: ` for
single-speaker mode:

```bash
python scripts/generate.py "Welcome aboard!" --style cheerfully
```

### Audio tags (inline)

Insert bracketed tags directly into the text to steer delivery mid-sentence
(200+ supported). Common examples:

```
[whispers]      [shouting]     [excitedly]    [sarcastically]
[laughs]        [sighs]        [nervously]    [slowly]
```

Example:

```
[whispers] I have a secret... [excitedly] and I can finally tell you!
```

### Advanced structured prompting

For fine-grained control, structure the prompt with directorial notes:

```
Audio Profile: a seasoned documentary narrator, deep and measured.
Scene: a quiet nature reserve at dawn.
Director's Notes: Style = contemplative; Pacing = slow; Accent = neutral British.

Transcript:
The first light touches the canopy, and the forest begins to wake.
```

---

## Multi-Speaker Dialogue

- Label each line `Name: text`.
- Use **exactly 2** distinct speakers (hard limit).
- Speaker names in the text must match the `--speaker "Name:Voice"` mappings.
- If you omit `--speaker`, default voices are assigned in first-seen order
  (`Kore`, then `Puck`).

Example `dialogue.txt`:

```
Taro: How's it going today, Hanako?
Hanako: Not too bad, how about you?
Taro: Pretty good — excited for the trip!
```

```bash
python scripts/generate.py -f dialogue.txt \
  --speaker "Taro:Charon" --speaker "Hanako:Leda" -o conversation.wav
```

You can still apply audio tags per line:

```
Taro: [excitedly] We're finally going!
Hanako: [laughs] I can't wait.
```

---

## Tips

- **Match language to text** — write the transcript in the language you want
  spoken (70+ languages supported).
- **Pick voice by role** — informative narration (`Charon`, `Rasalgethi`),
  warm/friendly (`Sulafat`, `Achird`), youthful (`Leda`), firm/authoritative
  (`Kore`, `Alnilam`).
- **Long text** — read from a file with `-f` to avoid shell-escaping issues.
- **Avoid impersonation** — describe a voice style rather than naming a real
  person; voice-cloning requests are blocked.
