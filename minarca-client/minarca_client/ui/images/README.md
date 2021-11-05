# Images

This folder contains few images used in the user interface.

## Generate Spin GIFs

    convert spin.gif -coalesce temporary.gif
    convert temporary.gif -resize 16x16 spin_16.gif
    convert temporary.gif -resize 24x24 spin_24.gif
    convert temporary.gif -resize 32x32 spin_32.gif
    rm temporary.gif

## Generate Minarca .ico

    convert -background none -density 300 minarca.svg -resize 16x16 minarca_16.png
    convert -background none -density 300 minarca.svg -resize 22x22 minarca_22.png
    convert -background none -density 300 minarca.svg -resize 32x32 minarca_32.png
    convert -background none minarca.svg -resize 48x48 minarca_48.png
    convert -background none minarca.svg -resize 128x128 minarca_128.png
    convert -background none minarca.svg -resize 256x256 minarca_256.png
    convert -background none minarca.svg -resize 512x512 minarca_512.png
    icotool -c -o minarca.ico minarca_16.png minarca_32.png minarca_48.png minarca_128.png

## Generate Minarca .icns

    convert -background none -density 300 minarca.svg -resize 16x16 minarca_16.png
    convert -background none -density 300 minarca.svg -resize 32x32 minarca_32.png
    convert -background none minarca.svg -resize 48x48 minarca_48.png
    convert -background none minarca.svg -resize 128x128 minarca_128.png
    convert -background none minarca.svg -resize 256x256 minarca_256.png
    png2icns minarca.icns minarca_{16,32,48,128,256}.png

## Generate Application icons

    convert -background none -density 300 status.svg   -alpha off -fill white -opaque black -alpha on -resize 14x14 -gravity north -extent 14x16 status_16.png
    convert -background none -density 300 patterns.svg -alpha off -fill white -opaque black -alpha on -resize 14x14 -gravity north -extent 14x16 patterns_16.png
    convert -background none -density 300 schedule.svg -alpha off -fill white -opaque black -alpha on -resize 14x14 -gravity north -extent 14x16 schedule_16.png
    convert -background none -density 300 trash.svg    -alpha off -fill white -opaque black -alpha on -resize 14x14 -gravity north -extent 14x16 trash_16.png
    convert -background none -density 300 help.svg     -alpha off -fill white -opaque black -alpha on -resize 14x14 -gravity north -extent 14x16 help_16.png

    convert -background none -density 300 error.svg    -alpha off -fill "#d02b27" -opaque black -alpha on -resize 20x20 -gravity north -extent 20x24 error_24.png
    convert -background none -density 300 info.svg     -alpha off -fill "#5bc0de" -opaque black -alpha on -resize 20x20 -gravity north -extent 20x24 info_24.png
    convert -background none -density 300 success.svg  -alpha off -fill "#43ac6a" -opaque black -alpha on -resize 20x20 -gravity north -extent 20x24 success_24.png
