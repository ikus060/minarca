# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

import base64
import os
import re
import subprocess
import tkinter

import jinja2

basedir = os.path.normpath(os.path.join(__file__, "../"))


CONVERT = [
    "convert",
    "-define",
    "png:include-chunk=none",
    "-background",
    "none",
    "-density",
    "300",
]


def svg_to_base64(svgfile, size, color=None, rotate=None):
    """
    Create PNG image from a SVG file with the required size.

    This function apply a little trick to generate the image with
    a bottom margin to visually align the image with text if `glyph` is set.
    """
    assert os.path.isfile(svgfile), "svgfile must be a file: %s" % svgfile
    cmd = CONVERT + [svgfile]
    if color:
        cmd += [
            "-alpha",
            "off",
            "-fill",
            color,
            "-opaque",
            "black",
            "-alpha",
            "on",
        ]
    if rotate:
        assert rotate >= 0
        cmd += [
            "-resize",
            str(size),
            "-distort",
            "SRT",
            str(rotate),
        ]
    cmd += [
        "-resize",
        str(size),
        "PNG:-",
    ]
    # Execute the conversion.
    data = subprocess.check_output(cmd, cwd=basedir)
    return base64.b64encode(data).decode('ascii')


def create_spinner(name, svgfile, size, color):
    """
    Create spinning wheel.
    """
    svgfile = os.path.join(basedir, "src", svgfile)
    assert os.path.isfile(svgfile), "svgfile must be a file: %s" % svgfile

    i = 0
    for r in range(0, 360, 45):
        cmd = CONVERT + [
            "-gravity",
            "center",
            "-resize",
            f"{size}x{size}",
            "-extent",
            f"{size+2}x{size+2}",
            svgfile,
            "-alpha",
            "off",
            "-fill",
            color,
            "-opaque",
            "black",
            "-alpha",
            "on",
            "-distort",
            "SRT",
            str(r),
            "-resize",
            f"{size}x{size}",
            f"{name}_{i:02d}.png",
        ]
        subprocess.check_call(cmd, cwd=basedir)
        yield f"{name}_{i:02d}", f"{name}_{i:02d}.png"
        i = i + 1


def create_ico(name, images):
    """
    Create a compatible Windows icon
    """
    cmd = ["icotool", "-c", "-o", f"{name}.ico"] + images
    subprocess.check_call(cmd, cwd=basedir)


def create_icns(name, images):
    cmd = ["png2icns", f"{name}.icns"] + images
    subprocess.check_call(cmd, cwd=basedir)


def hex_to_rgb(value):
    if not re.match('^#(?:[0-9a-fA-F]{3}){1,2}$', value):
        raise ValueError(value)
    return (int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16))


def rgb_to_hex(value):
    assert len(value) == 3
    return ('#{:02X}{:02X}{:02X}').format(value[0], value[1], value[2])


def lightness(color):
    """
    Return the lightness value
    """
    color = hex_to_rgb(color)
    return (0.212 * color[0] + 0.701 * color[1] + 0.087 * color[2]) / 255


def interpolate(color_a, color_b, t):
    assert t >= 0.0 and t <= 1.0
    color_a = hex_to_rgb(color_a)
    color_b = hex_to_rgb(color_b)
    new_color = tuple(int(a + (b - a) * t) for a, b in zip(color_a, color_b))
    return rgb_to_hex(new_color)


def darker(value, t=0.15):
    return interpolate(value, '#000000', t)


def lighter(value, t=0.15):
    return interpolate(value, '#ffffff', t)


def compile(input, output):
    """
    Generate theme using Jinja2 templating
    """
    searchpath = os.path.dirname(input)
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(searchpath),
        autoescape=jinja2.select_autoescape(),
    )
    env.globals['svg_to_base64'] = lambda file, *args, **kwargs: svg_to_base64(
        os.path.join(searchpath, file), *args, **kwargs
    )
    env.globals['lightness'] = lightness
    env.globals['darker'] = darker
    env.globals['lighter'] = lighter
    env.globals['interpolate'] = interpolate
    template = env.get_template(os.path.basename(input))

    data = template.render(the="variables", go="here")
    with open(output, 'w') as f:
        f.write(data)


def test(theme_filename):
    """
    Verify the theme using tkinter.
    """
    # Try loading the new theme for sanity check.
    root = tkinter.Tk()
    root.call("source", theme_filename)


def main():
    input = f"{basedir}/src/theme.tcl.j2"
    output = f"{basedir}/minarca.tcl"
    compile(input, output)
    test(output)


if __name__ == "__main__":
    main()
