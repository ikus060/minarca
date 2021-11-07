# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import os
import tkinter
from ttkbootstrap import Style
import subprocess

IMAGES = [
    # 24px
    ('error-24', 'error.svg', 24, True, '#d02b27'),
    ('info-24', 'info.svg', 24, True, '#5bc0de'),
    ('success-24', 'success.svg', 24, True, '#43ac6a'),
    # 16px
    ('help-16', 'help.svg', 16, True, 'white'),
    ('patterns-16', 'patterns.svg', 16, True, 'white'),
    ('schedule-16', 'schedule.svg', 16, True, 'white'),
    ('status-16', 'status.svg', 16, True, 'white'),
    ('trash-16', 'trash.svg', 16, True, 'white'),
    # icons
    ('minarca-16', 'minarca.svg', 16, False),
    ('minarca-22', 'minarca.svg', 22, False),
    ('minarca-32', 'minarca.svg', 32, False),
    ('minarca-48', 'minarca.svg', 48, False),
    ('minarca-128', 'minarca.svg', 128, False),
    ('minarca-256', 'minarca.svg', 256, False),
]

basedir = os.path.normpath(os.path.join(__file__, '../'))


def create_image(name, svgfile, size=16, glyph=False, color='white'):
    """
    Create PNG image from a SVG file with the required size.

    This function apply a little trick to generate the image with
    a bottom margin to visually align the image with text if `glyph` is set.
    """
    svgfile = os.path.join(basedir, 'src', svgfile)
    assert os.path.isfile(svgfile), 'svgfile must be a file: %s' % svgfile
    # TODO Convert those image magic command line into Pillow.
    if glyph:
        real_size = round(size * 0.8)
        cmd = ['convert', '-background', 'none', '-density', '300', svgfile, '-alpha', 'off', '-fill', color, '-opaque', 'black',
               '-alpha', 'on', '-resize', f'{real_size}x{real_size}', '-gravity', 'north', '-extent', f'{real_size}x{size}', f'{name}.png']
    else:
        cmd = ['convert', '-background', 'none', '-density', '300', svgfile, '-resize', f'{size}x{size}', f'{name}.png']
    subprocess.check_call(cmd, cwd=basedir)
    return name, f'{name}.png'


def create_spinner(name, svgfile, size, color):
    """
    Create spinning wheel.
    """
    svgfile = os.path.join(basedir, 'src', svgfile)
    assert os.path.isfile(svgfile), 'svgfile must be a file: %s' % svgfile

    i = 0
    for r in range(0, 360, 45):
        cmd = ['convert',
               '-gravity', 'center', '-resize', f'{size}x{size}', '-extent', f'{size+2}x{size+2}',
               '-background', 'none', '-density', '300', svgfile, '-alpha', 'off', '-fill', color,
               '-opaque', 'black', '-alpha', 'on', '-distort', 'SRT', str(r), '-resize', f'{size}x{size}', f'{name}_{i:02d}.png']
        subprocess.check_call(cmd, cwd=basedir)
        yield f'{name}_{i:02d}', f'{name}_{i:02d}.png'
        i = i + 1


def create_ico(name, images):
    """
    Create a compatible Windows icon
    """
    cmd = ['icotool', '-c', '-o', f'{name}.ico'] + images
    subprocess.check_call(cmd, cwd=basedir)


def create_icns(name, images):
    cmd = ['png2icns', f'{name}.icns'] + images
    subprocess.check_call(cmd, cwd=basedir)


def main():
    """
    Create TTK Theme for minarca.
    """

    themes_file = os.path.join(basedir, 'src', 'themes.json')
    assert os.path.isfile(themes_file)
    theme_name = 'minarca'

    # Create output directory
    fn = f'{basedir}/{theme_name}.tcl'

    # Open our theme
    root = tkinter.Tk()
    s = Style(theme_name, themes_file=themes_file, master=root)

    # Export settings
    settings = s._theme_objects[theme_name].settings
    # Add few fixes.
    for i in ['primary', 'secondary', 'success', 'info', 'warning', 'danger']:
        settings[f'H1.{i}.TLabel'] = {'configure': {'font': ["Helvetica", "-24", "bold"]}}
        settings[f'navbar.{i}.Inverse.TLabel'] = {'configure': {'font': ["Helvetica", "-20"]}}
        settings[f'small.{i}.TLabel'] = {'configure': {'font': ["Helvetica", "-10"]}}
        settings[f'strong.{i}.TLabel'] = {'configure': {'font': ["Helvetica", "-14", "bold"]}}
    settings['tooltip.TLabel'] = {'configure': {'background': "#ffffe0"}}
    # Generate script.
    script = tkinter.ttk._script_from_settings(settings)
    with open(fn, 'w', encoding='utf-8') as f:

        # Create application image.
        for args in IMAGES:
            name, file = create_image(*args)
            f.write(f'image create photo {name} -file [file join [file dirname [info script]] {file}]\n')

        # Create spinner
        items = create_spinner('spinner-24', 'spinner.svg', size=24, color='#212529')
        for name, file in items:
            f.write(f'image create photo {name} -file [file join [file dirname [info script]] {file}]\n')

        # Loop on image to export them.
        for image in tkinter.image_names():
            if image.startswith("pyimage"):
                root.call(image, 'write', f'{basedir}/{image}.png')
                f.write(f'image create photo {theme_name}_{image} -file [file join [file dirname [info script]] {image}.png]\n')

        # Write theme script.
        f.write(f'ttk::style theme create {theme_name} -parent clam -settings {{')
        f.write(script.replace('pyimage', f'{theme_name}_pyimage'))
        f.write('}')

    # Create icons
    create_ico('minarca', [f'minarca-{x}.png' for x in [16, 32, 48, 128, 256]])
    create_icns('minarca', [f'minarca-{x}.png' for x in [16, 32, 48, 128, 256]])

    # Try loading the new theme for sanity check.
    root.destroy()
    root = tkinter.Tk()
    root.call('source', fn)


if __name__ == '__main__':
    main()
