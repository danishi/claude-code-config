#!/bin/bash
# Turn any video into an iPhone Live Photo pair (HEIC + MOV) that works as a moving lock screen wallpaper.
# Requires macOS 15.4+ (frame interpolation), ffmpeg, and the Swift toolchain (Xcode Command Line Tools).
set -euo pipefail

usage() {
  cat <<'EOF'
usage: make_live_photo.sh -i VIDEO [options]

  -i, --input PATH     Source video (any format ffmpeg reads)
  -o, --outdir DIR     Output directory (default: ~/Desktop/LivePhoto_<name>)
  -n, --name NAME      Base name; files become IMG_<NAME>.HEIC / IMG_<NAME>.MOV (default: source file name)
  -s, --start SEC      Where the clip starts in the source (default: 0)
  -d, --duration SEC   Clip length, 1.5-3 (default: 2.5)
  -k, --key SEC        Key photo time, counted from the clip start (default: 40% into the clip)
      --portrait       Center-crop and scale to 1080x1920 (9:16) for lock screens
      --mute           Drop the audio track
      --no-interp      Repeat frames instead of interpolating them when converting to 60 fps
EOF
  exit 2
}

IN="" OUTDIR="" NAME="" START=0 DUR=2.5 KEY="" PORTRAIT=0 MUTE=0 INTERP=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -i|--input) IN="$2"; shift 2 ;;
    -o|--outdir) OUTDIR="$2"; shift 2 ;;
    -n|--name) NAME="$2"; shift 2 ;;
    -s|--start) START="$2"; shift 2 ;;
    -d|--duration) DUR="$2"; shift 2 ;;
    -k|--key) KEY="$2"; shift 2 ;;
    --portrait) PORTRAIT=1; shift ;;
    --mute) MUTE=1; shift ;;
    --no-interp) INTERP=--no-interp; shift ;;
    *) usage ;;
  esac
done
[[ -n "$IN" && -f "$IN" ]] || usage
command -v ffmpeg >/dev/null || { echo "ffmpeg not found (brew install ffmpeg)" >&2; exit 1; }
command -v swift >/dev/null || { echo "swift not found (xcode-select --install)" >&2; exit 1; }

if [[ -z "$NAME" ]]; then NAME="$(basename "${IN%.*}")"; fi
NAME="$(printf '%s' "$NAME" | LC_ALL=C tr -c 'A-Za-z0-9_-' '_')"
[[ -n "$OUTDIR" ]] || OUTDIR="$HOME/Desktop/LivePhoto_$NAME"
awk -v d="$DUR" 'BEGIN{exit !(d>=1.5 && d<=3)}' || { echo "--duration must be between 1.5 and 3 seconds" >&2; exit 1; }
[[ -n "$KEY" ]] || KEY="$(awk -v d="$DUR" 'BEGIN{printf "%.3f", d*0.4}')"
awk -v k="$KEY" -v d="$DUR" 'BEGIN{exit !(k>=0 && k<d)}' || { echo "--key must be inside the clip (0 <= key < duration)" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
mkdir -p "$OUTDIR"

VF="format=yuv420p"
[[ $PORTRAIT -eq 1 ]] && VF="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=yuv420p"
AUDIO=(-c:a aac -b:a 128k)
[[ $MUTE -eq 1 ]] && AUDIO=(-an)

# 1. Trim (and optionally crop) to an intermediate clip.
ffmpeg -v error -y -ss "$START" -t "$DUR" -i "$IN" -vf "$VF" \
  -c:v libx264 -crf 12 -preset slow "${AUDIO[@]}" "$TMP/clip.mov"
# 2. Re-encode to 60 fps HEVC with the Live Photo metadata, and take the cover from the same frames.
swift "$SCRIPT_DIR/pair_live_photo.swift" "$TMP/clip.mov" "$OUTDIR/IMG_$NAME" "$KEY" $INTERP 2>"$TMP/swift.log" \
  || { cat "$TMP/swift.log" >&2; exit 1; }

echo "$OUTDIR/IMG_$NAME.HEIC"
echo "$OUTDIR/IMG_$NAME.MOV"
