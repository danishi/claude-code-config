#!/usr/bin/env python3
"""
Check whether the sibling media-generation skills used by video-composer are
available locally, and print install guidance for any that are missing.

video-composer orchestrates these skills:
    nanobanana   - AI image generation
    lyria        - AI music (BGM) generation
    gemini-tts   - text-to-speech narration
    gemini-omni  - AI video generation / editing (primary video skill)
    veo          - AI video generation (fallback when gemini-omni is missing)

The video layer is satisfied when either gemini-omni or veo is installed;
gemini-omni is preferred, so its absence is reported as a recommendation even
when veo is present.

When this skill is installed standalone (e.g. by another user via
`npx skills add ...`), the sibling skills may not be present. This script
locates each one and, for any that are missing, prints the install commands
from the danishi/claude-code-config repository so the user can add them.

Usage:
    python check_skills.py            # human-readable report
    python check_skills.py --json     # machine-readable JSON

Exit code is 0 if every asset layer has at least one skill, 1 otherwise.
"""

import argparse
import json
import os
import sys
from pathlib import Path

REPO = "danishi/claude-code-config"

# Sibling skills this orchestrator relies on, with the asset type each provides.
SIBLING_SKILLS = {
    "nanobanana": "images (text-to-image, editing)",
    "lyria": "music / BGM",
    "gemini-tts": "narration (text-to-speech)",
    "gemini-omni": "video clips (generate / edit / extend) - primary",
    "veo": "video clips (text/image-to-video) - fallback",
}

# Asset layers -> skills that can fill them, preferred first. A layer is
# covered when any of its skills is installed.
LAYERS = {
    "images": ["nanobanana"],
    "video": ["gemini-omni", "veo"],
    "bgm": ["lyria"],
    "narration": ["gemini-tts"],
}

# Each skill is considered "found" when a directory containing SKILL.md exists.
SKILL_MARKER = "SKILL.md"


def candidate_roots() -> list[Path]:
    """Directories that may contain installed skills, most-specific first."""
    roots: list[Path] = []

    # 1. Sibling directory of this skill (repo layout: skills/<name>/).
    here = Path(__file__).resolve()
    # .../skills/video-composer/scripts/check_skills.py -> .../skills
    roots.append(here.parent.parent.parent)

    # 2. Explicit override.
    env_root = os.environ.get("VIDEO_COMPOSER_SKILLS_DIR")
    if env_root:
        roots.append(Path(env_root).expanduser())

    # 3. Common Claude Code skill install locations.
    home = Path.home()
    roots += [
        home / ".claude" / "skills",
        home / ".config" / "claude" / "skills",
    ]

    # 4. Plugin marketplace caches (search a couple of levels for skill dirs).
    plugin_roots = [
        home / ".claude" / "plugins",
        home / ".config" / "claude" / "plugins",
    ]
    for proot in plugin_roots:
        if proot.is_dir():
            roots.append(proot)

    # De-duplicate while preserving order.
    seen: set[str] = set()
    uniq: list[Path] = []
    for r in roots:
        key = str(r)
        if key not in seen:
            seen.add(key)
            uniq.append(r)
    return uniq


def find_skill(name: str) -> str | None:
    """Return the path to an installed skill directory, or None if missing."""
    for root in candidate_roots():
        # Direct: <root>/<name>/SKILL.md
        direct = root / name / SKILL_MARKER
        if direct.is_file():
            return str(direct.parent)
        # Shallow recursive search under plugin caches: **/<name>/SKILL.md
        if root.is_dir() and root.name in ("plugins",):
            for marker in root.glob(f"*/**/{name}/{SKILL_MARKER}"):
                return str(marker.parent)
    return None


def install_commands(name: str) -> dict:
    """Install guidance for a missing sibling skill."""
    return {
        "npx_skills": f"npx skills add {REPO} --skill {name}",
        "claude_plugin": f"claude plugin install {name}",
        "marketplace_add": f"claude marketplace add https://github.com/{REPO}",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check sibling media skills for video-composer")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output JSON")
    args = parser.parse_args()

    results = {}
    for name, role in SIBLING_SKILLS.items():
        path = find_skill(name)
        results[name] = {
            "role": role,
            "found": path is not None,
            "path": path,
            "install": None if path else install_commands(name),
        }

    # Layers with no installed skill, reported by their preferred skill name.
    missing = [
        skills[0]
        for skills in LAYERS.values()
        if not any(results[n]["found"] for n in skills)
    ]
    # Preferred skills that are absent although a fallback covers the layer.
    recommended = [
        skills[0]
        for skills in LAYERS.values()
        if not results[skills[0]]["found"]
        and any(results[n]["found"] for n in skills[1:])
    ]

    if args.as_json:
        print(json.dumps(
            {"results": results, "missing": missing, "recommended": recommended},
            ensure_ascii=False, indent=2,
        ))
        sys.exit(0 if not missing else 1)

    print("Sibling media-generation skills for video-composer:\n")
    for name, r in results.items():
        status = "OK " if r["found"] else "MISSING"
        loc = r["path"] or "(not installed)"
        print(f"  [{status}] {name:12} - {r['role']}")
        print(f"           {loc}")

    if not results["gemini-omni"]["found"] and results["veo"]["found"]:
        print(
            "\nVideo clips will fall back to veo (Vertex AI only). Installing "
            "gemini-omni is recommended: it also edits / extends clips and works "
            "with GEMINI_API_KEY."
        )
    elif results["gemini-omni"]["found"] and not results["veo"]["found"]:
        print("\nveo is not installed; that's fine - gemini-omni covers the video layer.")

    to_install = missing + recommended
    if to_install:
        print("\nTo add the missing / recommended skills, either:\n")
        print(f"  # 1) Add the marketplace once, then install plugins:")
        print(f"  claude marketplace add https://github.com/{REPO}")
        for name in to_install:
            print(f"  claude plugin install {name}")
        print(f"\n  # 2) Or install individual skills directly:")
        for name in to_install:
            print(f"  npx skills add {REPO} --skill {name}")

    if missing:
        print(
            "\nIf you prefer not to install them, video-composer can fall back to "
            "alternatives (e.g. solid-color / gradient backgrounds, silent or "
            "stock audio, static images instead of video) — but quality will be reduced."
        )
        sys.exit(1)

    print("\nEvery asset layer has an available skill.")
    sys.exit(0)


if __name__ == "__main__":
    main()
