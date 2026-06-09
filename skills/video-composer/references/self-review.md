# Multimodal Self-Review

After each render, video-composer inspects the result **before** showing it to
the user, and iterates autonomously until it meets the quality bar (or a hard
iteration cap is reached).

## How to review

`render_video.py` exports evenly spaced still frames to `<project>/review/`.
**Read those PNGs back with vision** (the Read tool renders images) and judge
them against the rubric below. For audio/timing issues that stills can't show,
reason from the props (durations, voiceover lengths, BGM volume) and, when
needed, render a short range or open `npx remotion studio` to scrub.

```bash
python scripts/render_video.py --project <dir> --props <dir>/props.json \
  --install --review-frames 6
# -> writes review/frame_00_atNN.png ... and prints their paths
# Then Read each frame image and evaluate it.
```

## Review rubric (score each, note concrete fixes)

### Visual
- [ ] **Framing & safety** — subject not awkwardly cropped; nothing important in
      the outer ~5% (title/action safe area).
- [ ] **Legibility** — captions readable over the background (contrast, size,
      not overlapping faces/focal points); not clipped at edges.
- [ ] **Aspect / fit** — no letterboxing or distortion from a fit mismatch
      (`cover` vs `contain`); image ratio matches the composition.
- [ ] **Cohesion** — consistent visual style/palette across scenes.
- [ ] **Artifacts** — no obvious generation glitches (warped hands/text, seams).

### Motion & pacing
- [ ] **Ken Burns** — subtle, not nauseating; doesn't reveal empty edges.
- [ ] **Transitions** — duration suits the cut; not so long it eats the scene.
- [ ] **Scene length** — each scene long enough to read captions / hear VO, not
      so long it drags.

### Audio (reason from props + a scrub if needed)
- [ ] **Narration fits** — voiceover finishes within its scene (+ small tail).
- [ ] **BGM balance** — music volume low enough (~0.2) under narration.
- [ ] **No clashing BGM** — veo clips carry no embedded background music that
      fights the global lyria BGM. Scrub any video scene: SE/ambience/dialogue is
      fine, but if you hear a second musical bed, regenerate that clip with music
      suppressed (`--negative-prompt "background music, soundtrack, …"`) — do NOT
      mute the clip, which would also remove its SE.
- [ ] **Sync** — captions appear while the matching narration plays.

### Requirements
- [ ] Matches the **approved plan** (message, scene order, tone, duration,
      orientation, branding).

## Iteration loop (autonomous)

```
render -> extract stills -> read & score against rubric
   |                                   |
   |          all criteria pass?  -----+--- yes --> deliver to user
   |                                   |
   +<--- fix (edit props / regenerate an asset / adjust timing) <-- no
```

- **Fix at the cheapest level first**: prefer editing `props.json` (timing,
  caption text/position, transition, fit, volume) before regenerating an asset.
- Regenerate a specific asset (e.g. a weak image via nanobanana) only when the
  problem is the asset itself.
- **Stop conditions**: all rubric items pass, OR `MAX_REVIEW_ITERS` reached
  (default **3**), OR two consecutive iterations yield no meaningful improvement.
- When stopping at the cap without full pass, deliver the best version and
  **explicitly list the remaining known issues** for the user.

## What NOT to do

- Don't show the user a render you haven't reviewed.
- Don't loop forever chasing diminishing returns — respect the cap.
- Don't silently drop a requirement from the approved plan; flag it instead.
