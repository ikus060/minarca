This folder contains few images used in the user interface.

# Generate Spin GIFs

    convert spin.gif -coalesce temporary.gif
    convert temporary.gif -resize 16x16 spin_16.gif
    convert temporary.gif -resize 24x24 spin_24.gif
    convert temporary.gif -resize 32x32 spin_32.gif
    rm temporary.gif

# Generate Minarca .ico

    convert -background none -density 300 minarca.svg -resize 16x16 minarca_16.png
    convert -background none -density 300 minarca.svg -resize 22x22 minarca_22.png
    convert -background none -density 300 minarca.svg -resize 32x32 minarca_32.png
    convert -background none minarca.svg -resize 48x48 minarca_48.png
    convert -background none minarca.svg -resize 128x128 minarca_128.png
    convert -background none minarca.svg -resize 256x256 minarca_256.png
    convert -background none minarca.svg -resize 512x512 minarca_512.png
    icotool -c -o minarca.ico minarca_16.png minarca_32.png minarca_48.png minarca_128.png

# Generate Minarca .icns

    convert -background none -density 300 minarca.svg -resize 16x16 minarca_16.png
    convert -background none -density 300 minarca.svg -resize 32x32 minarca_32.png
    convert -background none minarca.svg -resize 48x48 minarca_48.png
    convert -background none minarca.svg -resize 128x128 minarca_128.png
    convert -background none minarca.svg -resize 256x256 minarca_256.png
    png2icns minarca.icns minarca_{16,32,48,128,256}.png
