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
svg_to_png "minarca.svg" "72x72"   minarca-72.png

# Application Header Logo
svg_to_png "header-logo.svg" "x30"   "header-logo-30.png"

# Application images
svg_to_png "local-backup.svg" "64x64"   "local-backup-64.png"
svg_to_png "local-backup.svg" "128x128" "local-backup-128.png"
svg_to_png "local-backup.svg" "256x256" "local-backup-256.png"
svg_to_png "remote-backup.svg" "64x64"   "remote-backup-64.png"
svg_to_png "remote-backup.svg" "128x128" "remote-backup-128.png"
svg_to_png "remote-backup.svg" "256x256" "remote-backup-256.png"
