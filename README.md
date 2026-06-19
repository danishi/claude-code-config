# claude-code-config

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/danishi/claude-code-config)

Personal repository for managing Claude Code settings, plugins, and development customizations.

## Repository Structure

```
.
├── .claude/                    # Claude Code project settings
│   ├── CLAUDE.md              # Project guidelines & principles
│   └── settings.json          # Permissions, hooks, MCP servers
├── .claude-plugin/
│   └── marketplace.json       # Plugin marketplace definition
├── .github/workflows/         # GitHub Actions
│   ├── claude.yml             # @claude mention handler
│   └── claude-code-review.yml # Automated PR review
├── .mcp.json                  # MCP server configurations
├── plugins/
│   ├── danishi/               # Base toolkit plugin
│   └── pdf-editor/            # PDF manipulation plugin
└── skills/
    ├── codex-imagegen/        # AI image generation skill (Codex CLI)
    ├── nanobanana/            # AI image generation skill (Gemini)
    ├── lyria/                 # AI music generation skill
    ├── gemini-tts/            # AI text-to-speech (read-aloud) skill
    ├── veo/                   # AI video generation skill
    ├── video-composer/        # Remotion video orchestration skill
    ├── izakaya-search/        # Japanese restaurant search skill
    └── skill-packager/        # Skill packaging utility
```

## Plugins & Skills

This repository provides ten plugins via the Claude Code marketplace:

### danishi Plugin

Personal base toolkit with the following features:

| Feature | Description |
|---------|-------------|
| `/review-spec-doc` | Reviews system specification documents and outputs improvement suggestions in Markdown |
| Hooks | macOS notification integration (alerts on permission requests and task completion) |
| MCP Servers | Pre-configured integration with chrome-devtools and aws-knowledge |

### pdf-editor Plugin

PDF page manipulation toolkit with a specialized `pdf-operator` agent:

- **Delete** - Remove specific pages or page ranges
- **Reorder** - Rearrange page order
- **Insert** - Insert pages from another PDF
- **Rotate** - Rotate pages (90/180/270 degrees)
- **Split** - Split into multiple files (per-page, ranges, or chunks)
- **Merge** - Combine multiple PDFs into one

### codex-imagegen Skill

AI image generation using Codex CLI's built-in image_gen tool:

- **No API Key Required** - Uses Codex's built-in image generation (no `OPENAI_API_KEY` needed)
- **Style Control** - Specify style via `-s` (e.g. "watercolor", "anime", "photorealistic")
- **Aspect Ratios** - 1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3
- **Negative Prompts** - Exclude unwanted elements with `--negative`
- **Batch Generation** - Generate multiple images with `-n`
- **JSON Output** - Machine-readable output with `--json`

### nanobanana Skill

AI image generation using Google Gemini (Nano Banana Pro / Nano Banana 2):

- **Text-to-Image** - Generate images from text prompts
- **Image Editing** - Transform existing images with natural language instructions
- **Aspect Ratios** - 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9
- **High Resolution** - Standard, 2K, and 4K output
- **Batch Generation** - Generate multiple images with parallel execution support
- **Prompt Reference** - Built-in prompt templates and best practices

### lyria Skill

AI music generation using Google Gemini Lyria 3:

- **Auto Model Selection** - Picks Lyria 3 Pro or Clip based on the request / purpose
- **Lyria 3 Pro** - Full-length songs (≈ a couple of minutes) with verses, choruses, bridges, and lyrics
- **Lyria 3 Clip** - 30-second clips, loops, jingles, and quick previews (fast iteration)
- **Rich Prompting** - Genre, mood, instruments, tempo, vocals, and song-structure tags
- **Output Formats** - MP3 (default) and WAV (Pro), 48 kHz stereo
- **Prompt Reference** - Built-in prompt templates by genre and song structure

### gemini-tts Skill

AI text-to-speech (read-aloud) using Google Gemini TTS (`gemini-3.1-flash-tts-preview`):

- **Auto Mode Detection** - Single-speaker narration for plain text, multi-speaker for 2-person dialogue
- **30 Prebuilt Voices** - Choose by characteristic (bright, warm, firm, youthful, etc.)
- **Multi-speaker Dialogue** - Maps `Name:` labels to distinct voices (up to 2 speakers)
- **Style Control** - Natural-language prefixes (`Say cheerfully:`) and 200+ inline audio tags
- **Flexible Input** - Read from a command argument or a text file (`-f`)
- **WAV Output** - 16-bit, 24 kHz mono WAV (PCM auto-wrapped)
- **Voice Reference** - Built-in voice list and style / audio-tag guide

### veo Skill

AI video generation using Google Gemini Veo 3.1:

- **Cost-First Default** - Uses the cost-effective Veo 3.1 Lite model unless `--pro` / `--fast` is explicitly given
- **Text-to-Video** - Generate clips from a text prompt
- **Image-to-Video** - Animate a starting frame, with an optional last-frame constraint
- **Cinematic Control** - Aspect ratio (16:9 / 9:16), resolution (720p / 1080p, 4k on Pro), 4-8s duration
- **Batch** - Generate 1-4 video variations per request
- **Async Handling** - Submits the long-running job and polls until the `.mp4` is ready
- **Prompt Reference** - Built-in camera-movement vocabulary and prompt templates

### video-composer Skill

Orchestrated rich video production with React Remotion, combining the other media skills:

- **Skill Orchestration** - Drives nanobanana (images), veo (clips), lyria (BGM), and gemini-tts (narration) on one timeline
- **Approval Gate** - Returns a scene-by-scene composition plan and waits for approval before generating anything
- **Data-driven Remotion** - Scaffolds a fresh TypeScript Remotion project whose timeline is described entirely by `props.json` (scenes, Ken Burns, captions, transitions, voiceover, BGM)
- **Multimodal Self-Review** - Renders, extracts still frames, visually inspects them against a rubric, and iterates autonomously until the quality bar is met
- **Graceful Degradation** - Detects missing sibling skills and prompts installation (for standalone installs) or falls back to documented alternatives

### izakaya-search Skill

Search and recommend izakaya and restaurants for group dining:

- **Interactive Interview** - Asks about area, party size, budget, and preferences
- **Multi-site Search** - Searches Tabelog, Hot Pepper, Gurunavi, and Google Maps in parallel
- **Composite Ratings** - Weighted scores (Google Maps 45%, Tabelog 35%, Hot Pepper 20%)
- **Fake Review Detection** - Detects and penalizes suspected sakura reviews on Google Maps
- **Quick Booking** - Provides reservation links, course info, and Google Maps directions
- **Search Reference** - Built-in query templates by occasion, cuisine, and features

### skill-packager Skill

Package a skill directory into a distributable `.skill` archive:

- **One-shot Packaging** - Zips `~/.claude/skills/<skill-name>/` into `~/Desktop/<skill-name>.skill`
- **Pre-flight Inspection** - Lists every file to be included so users can spot credentials, large binaries, or local-only configs before shipping
- **Cache Exclusion** - Automatically excludes `__pycache__/`, `*.pyc`, and `.DS_Store`
- **ASCII-safe Check** - Reminds users to rename non-ASCII filenames (Claude Desktop rejects them)
- **Size Verification** - Reports the final archive path and size for sanity checking

## MCP Servers

Pre-configured MCP (Model Context Protocol) servers:

| Server | Description |
|--------|-------------|
| [chrome-devtools](https://www.npmjs.com/package/chrome-devtools-mcp) | Browser automation, screenshots, and DevTools interaction |
| [aws-knowledge](https://awslabs.github.io/mcp/) | AWS documentation search, regional availability, and API reference |
| [google-developer-knowledge](https://developers.google.com/) | Google APIs documentation |
| [context7](https://context7.com/) | Up-to-date library documentation lookup |
| [drawio](https://www.npmjs.com/package/@drawio/mcp) | Diagram creation and editing (draw.io) |
| [backlog](https://www.npmjs.com/package/backlog-mcp-server) | Backlog project management integration |

## GitHub Actions

### `@claude` Mention Handler (`claude.yml`)

Triggers Claude Code when `@claude` is mentioned in:
- Issue comments
- PR review comments
- PR reviews
- New issues

### Automated PR Review (`claude-code-review.yml`)

Automatically runs code review on every pull request using the official `code-review` plugin.

## Installation

### Adding the Marketplace

Add to your Claude Code settings file (`~/.config/claude/settings.json`):

```json
{
  "plugin_marketplaces": [
    "https://github.com/danishi/claude-code-config"
  ]
}
```

Or add directly via Claude Code command:

```bash
claude marketplace add https://github.com/danishi/claude-code-config
```

### Installing Plugins

List available plugins:
```bash
claude plugin list
```

Install a specific plugin:
```bash
claude plugin install danishi
claude plugin install pdf-editor
claude plugin install codex-imagegen
claude plugin install nanobanana
claude plugin install lyria
claude plugin install gemini-tts
claude plugin install veo
claude plugin install video-composer
claude plugin install izakaya-search
claude plugin install skill-packager
```

### Installing Skills Directly

You can also install individual skills using the `npx skills` command:

```bash
npx skills add danishi/claude-code-config --skill codex-imagegen
npx skills add danishi/claude-code-config --skill nanobanana
npx skills add danishi/claude-code-config --skill lyria
npx skills add danishi/claude-code-config --skill gemini-tts
npx skills add danishi/claude-code-config --skill veo
npx skills add danishi/claude-code-config --skill video-composer
npx skills add danishi/claude-code-config --skill izakaya-search
npx skills add danishi/claude-code-config --skill pdf-editor
npx skills add danishi/claude-code-config --skill skill-packager
```

## Usage

### danishi Plugin

**Document Review Command:**
```bash
/review-spec-doc <input-file-path> <output-file-path|auto>
```

Example:
```bash
/review-spec-doc ./docs/specification.md auto
```

### pdf-editor Plugin

**Using the Specialized Agent:**
```bash
# Start the pdf-operator agent interactively
claude agent start pdf-operator

# Or run a one-off PDF operation
claude agent run pdf-operator "Delete pages 2-4 from document.pdf and save as output.pdf"
```

**Direct Skill Usage:**
You can also use Claude Code's natural language interface to perform PDF operations:
```
"Delete pages 2-4 from document.pdf"
"Rotate all pages in file.pdf by 90 degrees"
"Merge file1.pdf and file2.pdf into combined.pdf"
"Split document.pdf into individual pages"
```

**Requirements:**
```bash
pip install pypdf
```

### codex-imagegen Skill

**Prerequisites:**
```bash
# Codex CLI must be installed
npm install -g @openai/codex
codex --version
```

**Generate an image:**
```bash
python3 <skill_dir>/scripts/generate.py "a cute golden retriever puppy" -o puppy.png
```

**With style and aspect ratio:**
```bash
python3 <skill_dir>/scripts/generate.py "Tokyo street at night" -s "anime style" -a 16:9 -o tokyo.png
```

**With negative prompt:**
```bash
python3 <skill_dir>/scripts/generate.py "a professional headshot" --negative "blurry, text, watermark" -o headshot.png
```

See [skills/codex-imagegen/SKILL.md](skills/codex-imagegen/SKILL.md) for full documentation and options.

### nanobanana Skill

**Prerequisites:**
```bash
pip install google-genai pillow
export GEMINI_API_KEY="your-api-key"  # Get from https://aistudio.google.com/apikey
```

**Generate an image:**
```bash
python3 <skill_dir>/scripts/generate.py "a cute robot mascot, pixel art style" -o robot.png
```

**Edit an existing image:**
```bash
python3 <skill_dir>/scripts/generate.py "make the background blue" -i input.jpg -o output.png
```

**Batch generation:**
```bash
python3 <skill_dir>/scripts/batch_generate.py "pixel art logo" -n 20 -d ./logos -p logo
```

See [skills/nanobanana/SKILL.md](skills/nanobanana/SKILL.md) for full documentation and options.

### lyria Skill

**Prerequisites:**
```bash
pip install google-genai
export GEMINI_API_KEY="your-api-key"  # Get from https://aistudio.google.com/apikey
```

**Generate music (auto-selects model):**
```bash
python3 <skill_dir>/scripts/generate.py "lofi hip hop, mellow piano, rainy night" -o track.mp3
```

**Force a short clip (loops / jingles):**
```bash
python3 <skill_dir>/scripts/generate.py "upbeat synthwave jingle, 80s, short loop" --clip -o jingle.mp3
```

**Force a full-length song (with structure tags and lyrics):**
```bash
python3 <skill_dir>/scripts/generate.py "[Verse] city lights fade [Chorus] we are still alive, full pop ballad" --pro -o song.mp3
```

See [skills/lyria/SKILL.md](skills/lyria/SKILL.md) for full documentation and options.

### gemini-tts Skill

**Prerequisites:**
```bash
pip install google-genai
export GEMINI_API_KEY="your-api-key"  # Get from https://aistudio.google.com/apikey
```

**Read text aloud (single voice):**
```bash
python3 <skill_dir>/scripts/generate.py "Have a wonderful day!" --voice Puck -o hello.wav
```

**Read a file with a style prefix:**
```bash
python3 <skill_dir>/scripts/generate.py -f article.txt --style "in a calm voice" -o article.wav
```

**Multi-speaker dialogue (auto-detected from `Name:` labels):**
```bash
python3 <skill_dir>/scripts/generate.py -f dialogue.txt --speaker "Taro:Kore" --speaker "Hanako:Puck" -o conversation.wav
```

See [skills/gemini-tts/SKILL.md](skills/gemini-tts/SKILL.md) for full documentation and options.

### veo Skill

**Prerequisites:**
```bash
pip install google-genai
export GEMINI_API_KEY="your-api-key"  # Get from https://aistudio.google.com/apikey
```

**Generate a video (cost-effective Lite model by default):**
```bash
python3 <skill_dir>/scripts/generate.py "a cat surfing a wave, cinematic lighting" -o cat.mp4
```

**Animate an image (image-to-video):**
```bash
python3 <skill_dir>/scripts/generate.py "gentle breeze, leaves drifting" -i start.jpg -o anim.mp4
```

**Use the premium model explicitly (1080p):**
```bash
python3 <skill_dir>/scripts/generate.py "epic drone shot over mountains" --pro --resolution 1080p -o drone.mp4
```

See [skills/veo/SKILL.md](skills/veo/SKILL.md) for full documentation and options.

### video-composer Skill

**Prerequisites:**
```bash
# Node.js >= 18 (Remotion bundles its own ffmpeg)
node -v
# Sibling media skills + API access (GEMINI_API_KEY or Vertex AI)
export GEMINI_API_KEY="your-api-key"
```

**Trigger with natural language:**
```
"Create a 30-second 16:9 promo video about our new app, with narration and upbeat BGM"
"Make a vertical social clip from these three points"
```

The skill first checks that the sibling skills (nanobanana / veo / lyria / gemini-tts) are installed (and prompts to install any that are missing), then returns a scene-by-scene composition plan for your approval. After approval it generates the assets, composes them in a scaffolded Remotion project, runs a multimodal self-review loop, and delivers the finished `.mp4`.

```bash
# Check sibling skill availability
python3 <skill_dir>/scripts/check_skills.py
```

See [skills/video-composer/SKILL.md](skills/video-composer/SKILL.md) for full documentation and the workflow.

### izakaya-search Skill

**Invoke the skill in Claude Code:**
```
/izakaya-search
```

Claude will interactively ask about area, party size, budget, and preferences, then search multiple gourmet sites and present restaurant recommendations with composite ratings and reservation links.

See [skills/izakaya-search/SKILL.md](skills/izakaya-search/SKILL.md) for full documentation and options.

### skill-packager Skill

**Trigger with natural language:**
```
"Package the nanobanana skill into a .skill file"
"Bundle my izakaya-search skill for distribution"
```

Claude will list the files to be included, exclude caches and OS metadata, and create `~/Desktop/<skill-name>.skill`. The resulting archive is ready to share or install via Claude Desktop.

See [skills/skill-packager/SKILL.md](skills/skill-packager/SKILL.md) for full documentation and options.

## Project Settings

This repository also serves as a reference for Claude Code project configuration:

- **CLAUDE.md** - Project principles (MCP-first approach, language settings, quality standards)
- **Permissions** - Allowlist/denylist based security model with deny rules for sensitive files and destructive commands
- **Hooks** - macOS notification hooks for permission requests and task completion
- **Status Line** - Custom status bar showing model, branch, context usage, cost, and line changes

## Related Resources

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [Claude Code Action](https://github.com/anthropics/claude-code-action)
- [Agent Plugins for AWS](https://github.com/awslabs/agent-plugins/tree/main)
- [Agent Skills for Google products and technologies](https://github.com/google/skills)
- [Databricks AI Dev Kit Skills](https://github.com/databricks-solutions/ai-dev-kit/tree/main/databricks-skills)

## License

This is a personal configuration repository. Feel free to reference or fork for your own use.
