---
name: video-composer
description: >
  Produce rich, finished video content with React Remotion by orchestrating the
  repository's media-generation skills (nanobanana for images, veo for video
  clips, lyria for BGM, gemini-tts for narration) and composing them on a
  data-driven Remotion timeline. Follows an approval-gated workflow: first
  return a video composition plan for the user to approve, then generate assets,
  compose, run a multimodal self-review loop, and deliver only when the result
  meets the quality bar. Use when the user wants to "create a video", "make a
  promo / explainer / social clip", or combine images, video, music, and
  voiceover into one polished video.
---

# Video Composer — orchestrated rich video production

This skill turns a request into a finished `.mp4` by combining four media
skills on a **Remotion** (React) timeline:

| Layer | Skill |
|---|---|
| Images / backgrounds | [nanobanana](https://github.com/danishi/claude-code-config/tree/main/skills/nanobanana) |
| Video clips | [veo](https://github.com/danishi/claude-code-config/tree/main/skills/veo) |
| Background music | [lyria](https://github.com/danishi/claude-code-config/tree/main/skills/lyria) |
| Narration / voiceover | [gemini-tts](https://github.com/danishi/claude-code-config/tree/main/skills/gemini-tts) |

It is an **orchestrator**: it does not generate media itself, it directs the
skills above and assembles their output.

---

## Workflow (must follow in order)

### Step 0 — Check prerequisites & sibling skills

Run the availability check first:

```bash
python scripts/check_skills.py
```

- **All present** → continue.
- **Some missing** → this typically means another user installed
  *video-composer* standalone (e.g. via `npx skills add`). **Prompt them to
  install** the missing skills using the commands the script prints (from the
  repo README), or **offer a documented fallback** (see
  `references/asset-pipeline.md` → "Missing skills"). Do not silently skip a
  requested asset type — surface the choice.

Also confirm tooling: **Node.js ≥ 18** (`node -v`) and `npx`. Remotion bundles
its own ffmpeg, so ffmpeg is not required. API access for the media skills needs
`GEMINI_API_KEY` (or Vertex AI). See `references/asset-pipeline.md`.

### Step 1 — Gather requirements

Interview the user (use AskUserQuestion for anything ambiguous) to pin down:

- **Purpose / message** and target audience
- **Duration** (e.g. 15s / 30s / 60s) and **orientation** (16:9 / 9:16 / 1:1)
- **Tone / style** (corporate, playful, cinematic, minimal…)
- **Must-haves**: narration? on-screen captions? BGM mood? brand colors/logo?
- **Language** (for narration & captions)
- Any **assets the user already has** vs. what should be generated

### Step 2 — Return a composition plan and GET APPROVAL (gate)

Produce a concise, structured **plan** and present it to the user. **Do not
generate anything or render until the user approves.** The plan must include:

- Overall spec: resolution, fps, total duration, orientation
- A **scene-by-scene table**: # · duration · visual (image/video + prompt
  summary) · narration text · on-screen caption · transition
- BGM mood and any logo/branding
- Which assets are **generated** (and by which skill) vs **fallback/user-supplied**

Iterate on the plan with the user until they explicitly approve. Only then
proceed.

### Step 3 — Scaffold the Remotion project

```bash
python scripts/scaffold.py <project-dir>
```

This writes a self-contained, data-driven Remotion project (see
`references/remotion-template.md` for the structure and the props schema). A
fresh project is scaffolded per video.

### Step 4 — Generate assets

Following the approved plan, call each sibling skill and place output under
`<project-dir>/public/{images,video,audio}/`. Exact commands and timing tips are
in `references/asset-pipeline.md`. Keep a consistent visual style across images.

> **BGM lives only in the lyria layer.** Veo clips keep their native audio (SE,
> ambience, dialogue) playing on the timeline, so when generating veo clips you
> must **always suppress embedded music** — pass
> `--negative-prompt "background music, soundtrack, musical score, BGM"` and
> never ask for music in the prompt. Otherwise a clip's own BGM would clash with
> the global lyria BGM. SE/ambience are kept; only music is suppressed. Details:
> `references/asset-pipeline.md` → "Never let veo clips carry their own BGM".

### Step 5 — Author the timeline (props.json)

Copy `props.sample.json` → `props.json` and fill in the scenes: reference assets
by path **relative to `public/`**, set each scene's `durationInFrames`
(`round(seconds * fps)`), captions, voiceover, transitions, and BGM. Schema and
timing rules: `references/remotion-template.md`.

### Step 6 — Render + multimodal self-review (autonomous loop)

```bash
python scripts/render_video.py --project <project-dir> \
  --props <project-dir>/props.json --install --review-frames 6
```

Then **read the exported review stills with vision** and score them against the
rubric in `references/self-review.md`. Iterate autonomously — fixing the cheapest
layer first (props → asset regen) — until all criteria pass or the iteration cap
(default 3) is reached.

### Step 7 — Deliver

When the result meets the bar, deliver the final `.mp4` to the user (use
SendUserFile for the artifact). If you stopped at the iteration cap with known
issues, deliver the best version and **list the remaining issues** plus
suggested next steps.

---

## Scripts

| Script | Purpose |
|---|---|
| `scripts/check_skills.py` | Detect sibling skills; print install guidance / fallbacks |
| `scripts/scaffold.py` | Scaffold a fresh data-driven Remotion project |
| `scripts/render_video.py` | `npm install` + render + export review stills |

## References

| File | Contents |
|---|---|
| `references/asset-pipeline.md` | Exact commands to drive each media skill; timing; missing-skill handling |
| `references/remotion-template.md` | Project structure & the `props.json` timeline schema |
| `references/self-review.md` | Multimodal review rubric & the autonomous iteration loop |

---

## Props schema (quick reference)

```jsonc
{
  "fps": 30, "width": 1920, "height": 1080,
  "bgm": { "src": "audio/bgm.mp3", "volume": 0.22 },
  "scenes": [
    {
      "durationInFrames": 150,
      "media": { "type": "image" | "video", "src": "images/x.png", "fit": "cover" },
      "kenBurns": true,
      "captions": [ { "text": "…", "fromFrame": 0, "toFrame": 140, "position": "bottom" } ],
      "voiceover": { "src": "audio/vo1.wav", "volume": 1.0, "delayInFrames": 6 },
      "transitionToNext": { "type": "fade" | "slide" | "wipe" | "none",
                             "durationInFrames": 18, "direction": "from-right" }
    }
  ]
}
```

- Asset `src` paths are **relative to `public/`** (http(s) URLs pass through).
- Total duration is computed automatically (sum of scene durations minus
  transition overlaps).

---

## Principles

- **Approval gate is mandatory** — never start generating/rendering before the
  user approves the plan.
- **Never deliver an unreviewed render** — always run the self-review loop.
- **Prefer this repo's skills**; when one is missing, prompt installation or use
  a documented fallback — and make the trade-off visible in the plan.
- **Fix cheap before expensive** — edit props before regenerating assets.
- **One BGM bed only** — music belongs to the lyria layer; always generate veo
  clips with music suppressed (negative prompt) so clip-embedded BGM can't clash
  with the global BGM. Keep the clips' SE/ambience.
