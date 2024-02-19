#!/bin/bash
function svg_to_png() {
    convert \
        -define png:include-chunk=none \
        -background none \
        -density 300 \
        "$1" \
        -resize "$2" \
        -gravity center \
        -extent "$2" \
        "$3"
}

function svg_color_to_png() {
    convert \
        -define png:include-chunk=none \
        -background none \
        -density 300 \
        "$1" \
        -alpha off \
        -fill "$3" \
        -opaque black \
        -alpha on \
        -resize "$2" \
        -gravity center \
        -extent "$2" \
        "$4"
}

# Android icons
svg_to_png "minarca.svg" "48x48"   minarca-48.png
svg_to_png "minarca.svg" "72x72"   minarca-72.png
svg_to_png "minarca.svg" "96x96"   minarca-96.png
svg_to_png "minarca.svg" "144x144" minarca-144.png
svg_to_png "minarca.svg" "192x192" minarca-192.png

# Application Header Logo
svg_to_png "header-logo.svg" "x30"   "header-logo-30.png"

# Application images
svg_to_png "local-backup.svg" "64x64"   "local-backup-64.png"
svg_to_png "local-backup.svg" "128x128" "local-backup-128.png"
svg_to_png "local-backup.svg" "256x256" "local-backup-256.png"
svg_to_png "remote-backup.svg" "64x64"   "remote-backup-64.png"
svg_to_png "remote-backup.svg" "128x128" "remote-backup-128.png"
svg_to_png "remote-backup.svg" "256x256" "remote-backup-256.png"

DARK_COLOR="#0E2933"
WARNING_COLOR="#D88C46"
DANGER_COLOR="#CA393C"
SUCCESS_COLOR="#50A254"

# Application images
svg_color_to_png "check-circle-fill.svg" "x14" $SUCCESS_COLOR "check-circle-fill-success.png"
svg_color_to_png "chevron-right.svg" "x14" $DARK_COLOR "chevron-right.png"
svg_color_to_png "exclamation-triangle-fill.svg" "x14" $WARNING_COLOR "exclamation-triangle-fill-warning.png"
svg_color_to_png "play-circle.svg" "x14" $DARK_COLOR "play-circle.png"
svg_color_to_png "play-circle-fill.svg" "x14" $DARK_COLOR "play-circle-fill.png"
svg_color_to_png "question-circle-fill.svg" "x14" $DARK_COLOR "question-circle-fill.png"
svg_color_to_png "stop-circle.svg" "x14" $DARK_COLOR "stop-circle.png"
svg_color_to_png "trash.svg" "x14" $DARK_COLOR "trash.png"
svg_color_to_png "trash.svg" "x14" $DANGER_COLOR "trash-danger.png"
svg_color_to_png "x-circle-fill.svg" "x14" $DANGER_COLOR "x-circle-fill-danger.png"