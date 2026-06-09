# Remotion Template & Props Schema

`scripts/scaffold.py` writes a self-contained, data-driven Remotion v4
(TypeScript) project. A single composition (`MainVideo`) renders a timeline that
is described entirely by `props.json` — you normally never edit the `.tsx`.

## Project structure

```
<project>/
├── package.json            remotion, @remotion/cli, @remotion/transitions, react
├── tsconfig.json
├── remotion.config.ts      jpeg stills, overwrite output
├── props.sample.json       sample timeline (copy to props.json)
├── public/                 assets resolved via staticFile()
│   ├── images/             nanobanana output
│   ├── video/              veo output
│   └── audio/              lyria BGM + gemini-tts voiceovers
└── src/
    ├── index.ts            registerRoot
    ├── types.ts            VideoProps / Scene / … types
    ├── utils.ts            resolveSrc(), total-duration math
    ├── Root.tsx            <Composition id="MainVideo"> + calculateMetadata
    ├── Scene.tsx           one scene: backdrop + Ken Burns + captions + VO
    └── Video.tsx           TransitionSeries over scenes + global BGM
```

### How it renders

- **`Root.tsx`** registers `MainVideo` and uses `calculateMetadata` to derive
  `durationInFrames`, `fps`, `width`, `height` from the props — so changing the
  timeline JSON is enough; no code edits.
- **`Video.tsx`** lays scenes out with `@remotion/transitions` `TransitionSeries`
  (so transitions overlap adjacent scenes) and plays the optional BGM as a
  looping `<Audio>` spanning the whole video.
- **`Scene.tsx`** draws the media backdrop (`<Img>` with Ken Burns, or
  `<OffthreadVideo>`), overlays timed captions, and plays the scene's voiceover
  as an `<Audio>` inside a `<Sequence from={delayInFrames}>`.
- **`utils.ts → resolveSrc`** wraps bare paths with `staticFile()` (so
  `"images/x.png"` resolves to `public/images/x.png`); http(s)/data/absolute
  URLs pass through unchanged.

## Props schema

```jsonc
{
  "fps": 30,                 // frames per second
  "width": 1920,             // composition width  (1080 for 9:16, 1080 for 1:1)
  "height": 1080,            // composition height (1920 for 9:16, 1080 for 1:1)
  "bgm": {                   // optional background music (whole video)
    "src": "audio/bgm.mp3",
    "volume": 0.22           // keep low under narration
  },
  "scenes": [
    {
      "durationInFrames": 150,            // round(seconds * fps)
      "media": {
        "type": "image" | "video",
        "src": "images/scene1.png",       // relative to public/
        "fit": "cover" | "contain"        // default cover
      },
      "kenBurns": true,                   // slow zoom/drift (images)
      "captions": [
        {
          "text": "On-screen text",
          "fromFrame": 0,                 // default 0
          "toFrame": 140,                 // default scene end
          "position": "top" | "center" | "bottom"   // default bottom
        }
      ],
      "voiceover": {
        "src": "audio/vo1.wav",
        "volume": 1.0,                    // default 1.0
        "delayInFrames": 6                // default 0
      },
      "transitionToNext": {
        "type": "fade" | "slide" | "wipe" | "none",  // default none if omitted
        "durationInFrames": 18,           // stolen from adjacent scenes
        "direction": "from-left" | "from-right" | "from-top" | "from-bottom"
      }
    }
  ]
}
```

### Orientation presets

| Orientation | width | height |
|---|---|---|
| 16:9 landscape | 1920 | 1080 |
| 9:16 portrait | 1080 | 1920 |
| 1:1 square | 1080 | 1080 |

### Timing rules

- `durationInFrames = round(seconds * fps)`.
- A transition's `durationInFrames` overlaps (is subtracted from) the two
  scenes it joins — keep it small (12-24) vs. scene length.
- For narrated scenes, make the scene ≥ voiceover length + a ~10-15 frame tail.
- Total composition length is computed automatically (see `utils.ts`); the same
  math is mirrored in `render_video.py` for review-frame spacing.

## Manual commands (the helper scripts wrap these)

```bash
# install deps
npm install

# interactive preview
npx remotion studio

# render
npx remotion render src/index.ts MainVideo out/video.mp4 --props props.json

# single still (review)
npx remotion still src/index.ts MainVideo review/f.png --frame 60 --props props.json
```

## Customization notes

- Caption styling (font, size, background) lives in `Scene.tsx` — adjust there
  for brand fonts/colors if requested.
- To add a logo overlay, drop it in `public/` and add an `<Img>` in `Video.tsx`
  inside the outer `AbsoluteFill` (renders above all scenes).
- Pinned to Remotion `4.0.0`; bump all `@remotion/*` + `remotion` together if a
  newer version is needed.
