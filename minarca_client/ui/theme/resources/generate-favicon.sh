#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  generate-favicon.sh /path/to/icon.svg
  generate-favicon.sh /path/to/icon.png

Description:
  Generates two icon files next to the input:
    - favicon.icns (macOS, multiple resolutions)
    - favicon.ico  (Windows, multiple resolutions)
  - Intermediate PNGs are created in /tmp and deleted afterwards.
  - Accepts SVG or PNG as input.

Requirements:
  - ImageMagick ("magick" CLI)
  - png2icns (from libicns on macOS, icnsutils on Debian/Ubuntu)
EOF
}

# If an input file is not provided, show usage info.
if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

INPUT="$1"

# Basic input validation
if [[ ! -f "$INPUT" ]]; then
  echo "Error: input file not found: $INPUT" >&2
  exit 1
fi

# Verify if magick (ImageMagick) is available.
if ! command -v magick >/dev/null 2>&1; then
  echo "Error: 'magick' (ImageMagick) not found." >&2
  exit 1
fi

# Verify if png2icns is available.
if ! command -v png2icns >/dev/null 2>&1; then
  echo "Error: 'png2icns' not found." >&2
  exit 1
fi

# Resolve output directory (same folder as the input)
OUT_DIR="$(cd "$(dirname "$INPUT")" && pwd)"
OUTPUT_ICNS="$OUT_DIR/favicon.icns"
OUTPUT_ICO="$OUT_DIR/favicon.ico"
OUTPUT_PNG="$OUT_DIR/favicon.png"

# Create PNGs in /tmp and delete after processing.
TEMP_DIR="$(mktemp -d /tmp/icns.XXXXXXXX)"
cleanup() {
  rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# macOS icns needs up to 1024; Windows ico uses up to 256.
SIZES_ALL=(16 24 32 48 64 128 256 512 1024)

# Optional: remove existing outputs to avoid confusion.
for f in "$OUTPUT_ICNS" "$OUTPUT_ICO"; do
  if [[ -f "$f" ]]; then
    echo "Note: removing existing $f"
    rm -f "$f"
  fi
done

echo "Generating intermediate PNGs in $TEMP_DIR ..."
for s in "${SIZES_ALL[@]}"; do
  # -density helps for vector inputs; harmless for raster.
  magick -background none -density 384 "$INPUT" -resize "${s}x${s}" \
    -define png:color-type=6 -strip \
    "$TEMP_DIR/icon_${s}.png"
done

# Create favicon.icns (macOS)
echo "Packing icns -> $OUTPUT_ICNS"
png2icns "$OUTPUT_ICNS" "$TEMP_DIR"/icon_16.png "$TEMP_DIR"/icon_32.png "$TEMP_DIR"/icon_64.png \
  "$TEMP_DIR"/icon_128.png "$TEMP_DIR"/icon_256.png "$TEMP_DIR"/icon_512.png "$TEMP_DIR"/icon_1024.png

# Create favicon.ico (Windows)
# Note: 32-bit RGBA PNGs are fine; Windows will pick the best size automatically.
echo "Packing ico  -> $OUTPUT_ICO"
magick "$TEMP_DIR"/icon_16.png  "$TEMP_DIR"/icon_24.png  "$TEMP_DIR"/icon_32.png \
       "$TEMP_DIR"/icon_48.png  "$TEMP_DIR"/icon_64.png  "$TEMP_DIR"/icon_128.png \
       "$TEMP_DIR"/icon_256.png -strip "$OUTPUT_ICO"

cp "$TEMP_DIR/icon_1024.png" "$OUTPUT_PNG"

echo "Success:"
echo "  $OUTPUT_ICNS"
echo "  $OUTPUT_ICO"
echo "  $OUTPUT_PNG"
