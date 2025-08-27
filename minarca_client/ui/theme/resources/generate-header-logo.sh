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

# Application Header Logo
svg_to_png "header-logo.svg" "x32"   "header-logo-32.png"
