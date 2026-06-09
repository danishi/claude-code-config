# Lyria 3 Prompt Reference

## Prompt Structure

A good music prompt typically combines these dimensions:

1. **Genre / style** — the musical genre or aesthetic
2. **Mood / atmosphere** — the emotional tone
3. **Instruments / arrangement** — what plays, and how it's layered
4. **Tempo / rhythm** — speed and groove (BPM, feel)
5. **Vocals** — voice type and timbre, or `instrumental` (Pro)
6. **Structure** — section tags for full songs (Pro)

The prompt language determines the sung language.

## Model Choice by Purpose

| Purpose | Model | Why |
|---|---|---|
| Loop, jingle, sound logo, SFX, 30s clip | **Clip** (`--clip`) | Fast, fixed 30s, cheap |
| Prompt experimentation / iteration | **Clip** (`--clip`) | Quick feedback loop |
| Full song with verses/choruses, lyrics | **Pro** (`--pro`) | Structural coherence, longer |
| Premium / studio-quality final render | **Pro** (`--pro`) | Highest fidelity |

---

## Categories

### Lo-fi / Chill

```
Lo-fi hip hop, mellow {instrument}, {mood} atmosphere,
relaxed boom-bap beat, vinyl crackle, warm and cozy
```

**Examples:**
```
Lo-fi hip hop, mellow electric piano, rainy night, relaxed beat, vinyl crackle

Chillhop, soft jazzy guitar, late-night study vibe, mellow drums, 75 BPM

Ambient lo-fi, dreamy pads, gentle rain, calm and introspective, instrumental
```

### Electronic / Synthwave / EDM

```
{subgenre}, {synth descriptors}, {tempo}, driving bass,
{mood}, retro/modern aesthetic
```

**Examples:**
```
Synthwave, neon arpeggios, 80s drum machine, driving bass, nostalgic, 110 BPM

Future bass, lush supersaw chords, punchy drops, energetic and uplifting

Deep house, four-on-the-floor, warm sub bass, hypnotic groove, late-night club
```

### Cinematic / Orchestral

```
Epic orchestral, {instrument sections}, {dynamics}, {mood},
cinematic film score, full-length
```

**Examples:**
```
Epic orchestral cinematic, soaring strings, powerful brass, timpani, dramatic and heroic

Tense thriller score, low pulsing strings, percussion hits, suspenseful, building tension

Emotional film score, solo piano with string section, melancholic, slow and intimate
```

### Jazz / Acoustic

```
{jazz style}, {instruments}, {feel}, {tempo}, {mood}
```

**Examples:**
```
Jazz trio, walking upright bass, brushed drums, smooth piano, late-night lounge, swing

Bossa nova, nylon guitar, soft shaker, warm and breezy, relaxed tempo

Acoustic folk, fingerpicked guitar, gentle harmonica, warm and nostalgic
```

### Jingle / Loop / Sound Logo (use `--clip`)

```
Short {genre} jingle, {instruments}, {mood}, catchy hook, loopable
```

**Examples:**
```
Upbeat synthwave jingle, bright arpeggio, punchy drums, catchy, short loop

Corporate sound logo, clean piano motif, optimistic, 5-second sting

Game level loop, chiptune, energetic 8-bit melody, seamless loop
```

---

## Full Song Structure (Pro)

Use section tags so the model builds a coherent song. Add lyrics under each tag,
and optionally timestamps for precise timing.

```
[0:00 - 0:08] [Intro] soft synth pad, building anticipation

[Verse]
city lights fade into the night
chasing shadows out of sight

[Chorus]
we are still alive, dreaming
holding on to the feeling

[Bridge]
slowing down, letting go

Full pop ballad, female vocals with warm timbre, emotional, mid-tempo
```

### Vocal descriptors (Pro)

- `female vocals, warm timbre`
- `male vocals, raspy and powerful`
- `soft whispered vocals`
- `choir, layered harmonies`
- `instrumental` (no vocals)

---

## Tips

- **Be specific but not contradictory** — combine genre + mood + instruments +
  tempo; avoid mixing incompatible styles in one prompt.
- **Iterate cheaply** — refine with `--clip`, then render the final with `--pro`.
- **Tempo helps** — adding a BPM or feel (`swing`, `four-on-the-floor`) stabilizes
  the groove.
- **Lyrics language = sung language** — write lyrics in the language you want sung.
- **Avoid named artists** — describe the sound instead; artist-voice requests are
  blocked by safety filters.
