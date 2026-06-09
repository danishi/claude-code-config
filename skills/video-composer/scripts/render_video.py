#!/usr/bin/env python3
"""
Render a video-composer Remotion project and extract still frames for the
multimodal self-review step.

This wraps the Remotion CLI:
  - `npm install` (once, unless node_modules already present)
  - `npx remotion render ... --props props.json` to produce the .mp4
  - `npx remotion still ... --frame N --props props.json` to export evenly
    spaced review stills (so the agent can visually inspect the result without
    requiring ffmpeg)

Usage:
    python render_video.py --project ./my-video --props ./my-video/props.json \\
        --output ./my-video/out/video.mp4 --install --review-frames 6

The review stills are written to <project>/review/frame_XX.png and their paths
are printed (and returned in --json mode) so they can be read back with vision.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ENTRY = "src/index.ts"
COMPOSITION = "MainVideo"


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run a command, streaming output, and return the completed process."""
    print(f"$ {' '.join(cmd)}  (cwd={cwd})", flush=True)
    return subprocess.run(cmd, cwd=str(cwd))


def load_total_frames(props_path: Path) -> int:
    """Compute total composition frames from the props, mirroring utils.ts."""
    data = json.loads(props_path.read_text(encoding="utf-8"))
    scenes = data.get("scenes", [])
    total = sum(max(1, int(s.get("durationInFrames", 1))) for s in scenes)
    overlap = 0
    for s in scenes[:-1]:
        t = s.get("transitionToNext") or {}
        if t.get("type") and t.get("type") != "none":
            overlap += max(0, int(t.get("durationInFrames", 15)))
    return max(1, total - overlap)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a video-composer Remotion project")
    parser.add_argument("--project", required=True, help="Remotion project directory")
    parser.add_argument("--props", help="Props JSON (default: <project>/props.json)")
    parser.add_argument("--output", help="Output .mp4 (default: <project>/out/video.mp4)")
    parser.add_argument("--composition", default=COMPOSITION, help="Composition id")
    parser.add_argument("--install", action="store_true", help="Run npm install first")
    parser.add_argument(
        "--review-frames", type=int, default=6,
        help="Number of still frames to extract for review (0 to skip)",
    )
    parser.add_argument("--concurrency", type=int, help="Remotion render concurrency")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output JSON summary")
    args = parser.parse_args()

    project = Path(args.project).expanduser().resolve()
    if not (project / ENTRY).exists():
        print(f"Error: {project/ENTRY} not found. Run scaffold.py first.", file=sys.stderr)
        sys.exit(1)

    props = Path(args.props).expanduser() if args.props else project / "props.json"
    if not props.exists():
        print(
            f"Error: props file not found: {props}\n"
            f"Copy {project/'props.sample.json'} to {props} and edit it.",
            file=sys.stderr,
        )
        sys.exit(1)

    output = Path(args.output).expanduser() if args.output else project / "out" / "video.mp4"
    output.parent.mkdir(parents=True, exist_ok=True)

    npx = shutil.which("npx")
    npm = shutil.which("npm")
    if not npx or not npm:
        print("Error: node/npm/npx not found. Install Node.js (>=18).", file=sys.stderr)
        sys.exit(1)

    if args.install or not (project / "node_modules").is_dir():
        r = run([npm, "install"], cwd=project)
        if r.returncode != 0:
            print("Error: npm install failed.", file=sys.stderr)
            sys.exit(r.returncode)

    # Render the video.
    render_cmd = [npx, "remotion", "render", ENTRY, args.composition, str(output),
                  "--props", str(props)]
    if args.concurrency:
        render_cmd += ["--concurrency", str(args.concurrency)]
    r = run(render_cmd, cwd=project)
    if r.returncode != 0:
        print("Error: remotion render failed.", file=sys.stderr)
        sys.exit(r.returncode)

    # Extract review stills (evenly spaced, avoiding the very first/last frame).
    review_paths: list[str] = []
    n = max(0, args.review_frames)
    if n > 0:
        total = load_total_frames(props)
        review_dir = project / "review"
        review_dir.mkdir(parents=True, exist_ok=True)
        for i in range(n):
            # Spread frames across (5% .. 95%) of the timeline.
            frac = (i + 0.5) / n
            frame = int(total * (0.05 + 0.9 * frac))
            frame = max(0, min(total - 1, frame))
            still = review_dir / f"frame_{i:02d}_at{frame}.png"
            still_cmd = [npx, "remotion", "still", ENTRY, args.composition, str(still),
                         "--frame", str(frame), "--props", str(props)]
            rs = run(still_cmd, cwd=project)
            if rs.returncode == 0 and still.exists():
                review_paths.append(str(still))
            else:
                print(f"Warning: failed to render review still at frame {frame}", file=sys.stderr)

    summary = {
        "success": True,
        "output": str(output),
        "review_frames": review_paths,
    }
    if args.as_json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"\nRendered: {output}")
        if review_paths:
            print("Review stills (read these back to self-review):")
            for p in review_paths:
                print(f"  {p}")


if __name__ == "__main__":
    main()
