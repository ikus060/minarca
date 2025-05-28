# -*- mode: python ; coding: utf-8 -*-
#
# Copyright (C) 2025 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
#
# This script is used by pyinstaller to freeze the python code into an
# executable for all supported platform.
#
# For Windows, it creates the required installation package and sign the
# executable when available.
#
# For MacOS, it creates a redistributable .app archived into a .dgm file.
#
import os
import platform
import re
import shutil
import subprocess
from importlib.metadata import distribution as get_distribution
from importlib.resources import files
from os.path import join

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Use Mock OpenGL to avoid issue on headless
os.environ['KIVY_GL_BACKEND'] = 'mock'
# Disable Kivy config file.
os.environ['KIVY_NO_CONFIG'] = '1'
# Disable Kivy logging
os.environ['KIVY_NO_FILELOG'] = '1'
os.environ['KIVY_LOG_MODE'] = 'PYTHON'

#
# Common values
#
minarca_client_pkg = files('minarca_client')
icon = str(minarca_client_pkg / 'ui/theme/resources/minarca.ico')
macos_icon = str(minarca_client_pkg / 'ui/theme/resources/minarca.icns')

#
# Read package info
#
pkg = get_distribution('minarca_client')
version = pkg.version
pkg_info = pkg.metadata
assert pkg_info['License']
assert pkg_info['Summary']
assert pkg_info['Author-email']
# Get Project URL
project_url = [v.split(', ')[1] for k, v in pkg_info.items() if k == 'Project-URL' and v.startswith('Homepage, ')][0]
assert project_url

block_cipher = None

# Include theme resources and locales
datas = collect_data_files('minarca_client')

# Keep openssh client only for windows
if platform.system() != "Windows":
    datas = [(src, dest) for src, dest in datas if '/minarca_client/core/openssh/' not in src]

hiddenimports = []

# Collect all lazy loaded view in Minarca, but exclude tests.
hiddenimports.extend(collect_submodules("minarca_client", lambda name: '.tests' not in name))

# Make sure to collect all the files from rdiffbackup (namely the actions)
hiddenimports.extend(collect_submodules("rdiffbackup"))

# Do the same for Kivymd
hiddenimports.extend(collect_submodules("kivymd"))

# To work arround a bug with setuptools>=70.0.0 and pyinstaller<6
# See https://github.com/pyinstaller/pyinstaller/issues/8554
hiddenimports.append('pkg_resources.extern')

# On MacOS, make sure to include librsync.2.dylib because @rpath is not working properly in PyInstaller<6
binaries = []
if platform.system() == "Darwin":
    librsync_path = shutil.which(
        'librsync.2.dylib', path='/usr/lib:/usr/local/lib:/System/Library/Frameworks:/Library/Frameworks'
    )
    binaries.append((librsync_path, '.'))

exes = []
analyses = []
executables = [
    ("minarcaw", minarca_client_pkg / 'main.py'),
    ("minarca", minarca_client_pkg / 'main.py'),
]
for exe_name, script in executables:
    a = Analysis(
        [script],
        hiddenimports=hiddenimports,
        datas=datas,
        binaries=binaries,
        win_no_prefer_redirects=False,
        win_private_assemblies=False,
        cipher=block_cipher,
        noarchive=False,
    )
    # To avoid issue on Linux with mixed version, make sure to exclude libstdc++ to use the one provided by the system.
    if platform.system() == 'Linux':
        a.binaries = [entry for entry in a.binaries if 'libstdc++' not in entry[0]]
    pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=exe_name,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        icon=icon,
        options=[
            # Suppress warnings
            ('W ignore', None, 'OPTION'),
        ],
        console=exe_name != 'minarcaw',
    )
    analyses.append(a)
    exes.append(exe)

# On Windows, extra dependencies are required for SDL2 & Angle
kivy_extras = []
if platform.system() == "Windows":
    from kivy_deps import angle, sdl2

    kivy_extras = [Tree(p) for p in (sdl2.dep_bins + angle.dep_bins)]

coll = COLLECT(
    *exes,
    *[a.binaries for a in analyses],
    *[a.zipfiles for a in analyses],
    *[a.datas for a in analyses],
    *kivy_extras,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='minarca',
)

if platform.system() == "Darwin":

    # Create app bundle
    app = BUNDLE(
        coll,
        name='Minarca.app',
        icon=macos_icon,
        bundle_identifier='com.ikus-soft.minarca',
        version=version,
    )
    app_file = join(DISTPATH, 'Minarca.app')

    # Binary smoke test
    subprocess.check_call([join(DISTPATH, 'minarca.app/Contents/MacOS/minarca'), '--version'], stderr=subprocess.STDOUT)

    # Generate dmg image
    dmg_file = join(DISTPATH, 'minarca-client_%s.dmg' % version)
    subprocess.check_call(
        ['dmgbuild', '-s', join(SPECPATH, 'minarca.dmgbuild'), '-D', 'app=' + app_file, 'Minarca', dmg_file],
        stderr=subprocess.STDOUT,
    )

elif platform.system() == "Windows":

    from exebuild import makensis, signexe

    # For NSIS, we need to create a license file with Windows encoding.
    with open(join(DISTPATH, 'minarca/LICENSE.txt'), 'w', encoding='ISO-8859-1') as out:
        out.write(pkg_info['License'])

    # Sign Minarca executables
    signexe(join(DISTPATH, 'minarca/minarca.exe'))
    signexe(join(DISTPATH, 'minarca/minarcaw.exe'))

    # Create installer using NSIS
    exe_version = re.search(r'.*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', '0.0.0.' + version).group(1)
    nsi_file = join(SPECPATH, 'minarca.nsi')
    setup_file = join(DISTPATH, 'minarca-client_%s.exe' % version)
    makensis(
        [
            '-NOCD',
            '-INPUTCHARSET',
            'UTF8',
            '-DAppVersion=' + exe_version,
            '-DOutFile=' + setup_file,
            nsi_file,
        ],
        cwd=join(DISTPATH, 'minarca'),
        stderr=subprocess.STDOUT,
    )

    # Sign installer
    signexe(setup_file)

    # Binary smoke test
    subprocess.check_call([join(DISTPATH, 'minarca/minarca.exe'), '--version'], stderr=subprocess.STDOUT)

else:
    from debbuild import debbuild

    # For linux simply create a tar.gz with the folder
    targz_file = join(DISTPATH, 'minarca-client_%s.tar.gz' % version)
    subprocess.check_call(['tar', '-zcvf', targz_file, 'minarca'], cwd=DISTPATH, stderr=subprocess.STDOUT)

    # Also create a Debian package
    debbuild(
        name='minarca-client',
        version=version,
        architecture='amd64',
        data_src=[
            ('/opt/minarca', join(DISTPATH, 'minarca')),
            # For GUI
            ('/usr/share/applications/minarca-client.desktop', join(SPECPATH, 'minarca.desktop')),
            ('/opt/minarca/minarca.svg', join(DISTPATH, 'minarca/minarca_client/ui/theme/resources/minarca.svg')),
        ],
        description="Secure, self-hosted and automated backup solution",
        long_description=pkg_info['Summary'],
        url=project_url,
        maintainer=pkg_info['Author-email'],
        output=DISTPATH,
        postinst=join(SPECPATH, "minarca.postinst"),
        symlink=[
            ("/usr/bin/minarca", "/opt/minarca/minarca"),
            ("/opt/minarca/bin/minarca", "../minarca"),
        ],
        depends=[
            'ca-certificates',
            'cron',
            'libc6',
            'libstdc++6',
            'openssh-client',
        ],
        # For GUI
        recommends=[
            'libxcb1',
            'xdg-utils',
            'zenity|kdialog',
        ],
    )
