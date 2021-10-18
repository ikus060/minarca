# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import os
import tkinter
from ttkbootstrap import Style


def main():
    basedir = os.path.normpath(os.path.join(__file__, '../'))

    themes_file = os.path.join(basedir, 'themes.json')
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
        settings[f'H1.{i}.TLabel'] = {'configure': {'font': ["Helvetica", "36"]}}
        settings[f'small.{i}.TLabel'] = {'configure': {'font': ["Helvetica", "10"]}}
        settings[f'strong.{i}.TLabel'] = {'configure': {'font': ["Helvetica", "14", "bold"]}}
    settings['Tooltip.TLabel'] = {'configure': {'background': "#ffffe0"}}
    # Generate script.
    script = tkinter.ttk._script_from_settings(settings)

    # Loop on image to export them.
    with open(fn, 'w', encoding='utf-8') as f:
        for image in tkinter.image_names():
            if image.startswith("pyimage"):
                root.call(image, 'write', f'{basedir}/{image}.png')
                f.write(f'image create photo {theme_name}_{image} -file [file join [file dirname [info script]] {image}.png]\n')
        f.write(f'ttk::style theme create {theme_name} -parent clam -settings {{')
        f.write(script.replace('pyimage', f'{theme_name}_pyimage'))
        f.write('}')

    # Try loading the new theme for sanity check.
    root.destroy()
    root = tkinter.Tk()
    root.call('source', fn)


if __name__ == '__main__':
    main()
