# -*- mode: python ; coding: utf-8 -*-
#
# Copyright (C) 2023 IKUS Software. All rights reserved.
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
import subprocess
import tempfile
from email import message_from_string
import pkg_resources
from PyInstaller.utils.hooks import collect_submodules, copy_metadata

# Use Mock OpenGL to avoid issue on headless
os.environ['KIVY_GL_BACKEND'] = 'mock'
# Disable Kivy config file.
os.environ['KIVY_NO_CONFIG'] = '1'
# Disable Kivy logging
os.environ['KIVY_NO_FILELOG'] = '1'
os.environ['KIVY_LOG_MODE'] = 'PYTHON'

from kivy.tools.packaging.pyinstaller_hooks import hookspath, get_deps_minimal

#
# Common values
#
icon = 'minarca_client/ui/theme/resources/minarca.ico'
macos_icon = 'minarca_client/ui/theme/resources/minarca.icns'

# Read pacakage info
pkg = pkg_resources.get_distribution("minarca_client")
version = pkg.version
try:
    _metadata = message_from_string(pkg.get_metadata('METADATA'))
except IOError:
    _metadata = message_from_string(pkg.get_metadata('PKG-INFO'))
pkg_info = dict(_metadata.items())
long_description = _metadata._payload
block_cipher = None


# Include openssh client for windows
if platform.system() == "Windows":
    openssh = [('minarca_client/core/openssh', 'minarca_client/core/openssh')]
else:
    openssh = []

extras = get_deps_minimal(video=None, audio=None, spelling=None, camera=None)

extras['hiddenimports'].extend(collect_submodules("rdiffbackup"))

extras['hiddenimports'].extend(collect_submodules("kivymd"))

a = Analysis(
    ['minarca_client/main.py'],
    pathex=[],
    datas=copy_metadata('minarca_client')
    + copy_metadata('rdiff-backup')
    + openssh
    + [
        ('../README.md', '.'),
        ('LICENSE', '.'),
        ('minarca_client/ui/theme/resources', 'minarca_client/ui/theme/resources'),
        ('minarca_client/locales', 'minarca_client/locales'),
    ],
    hookspath=[],
    runtime_hooks=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    **extras,
)

# To avoid issue on Linux with mixed version, make sure to exclude libstdc++ to use the one provided by the system.
if platform.system() == 'Linux':
    a.binaries = [entry for entry in a.binaries if 'libstdc++' not in entry[0]]

pyz = PYZ(a.pure, cipher=block_cipher)

# First executable for windowed mode.
exe_w = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='minarcaw',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    icon=icon,
    console=False,
)

# Another executable on for console mode.
exe_c = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='minarca',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    icon=icon,
    console=True,
)

extras = []
if platform.system() == "Windows":
    # On Windows extra dependencies must be collected.
    from kivy_deps import sdl2, glew, angle

    extras = [Tree(p) for p in (sdl2.dep_bins + glew.dep_bins + angle.dep_bins)]

coll = COLLECT(
    exe_w,
    exe_c,
    a.binaries,
    a.zipfiles,
    a.datas,
    a.zipped_data,
    *extras,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='minarca',
)

# Extract certificate from environment variable.
cert_file = tempfile.mktemp(suffix='.key')
key_file = tempfile.mktemp(suffix='.pem')
passphrase = os.environ.get('AUTHENTICODE_PASSPHRASE')
if os.environ.get('AUTHENTICODE_CERT'):
    # Write cert to file
    with open(cert_file, 'w') as f:
        f.write(os.environ['AUTHENTICODE_CERT'])
    # Write key to file
    with open(key_file, 'w') as f:
        f.write(os.environ['AUTHENTICODE_KEY'])
    # Get Common Name from certificate subject
    cert_subject = subprocess.check_output(
        ['openssl', 'x509', '-noout', '-subject', '-in', cert_file], text=True
    ).strip()
    cert_cn = cert_subject.partition('/CN=')[2]
    # Code signing on Windows required pfx file.
    pfx_file = tempfile.mktemp(suffix='.pfx')
    subprocess.check_call(
        [
            'openssl',
            'pkcs12',
            '-inkey',
            key_file,
            '-in',
            cert_file,
            '-passin',
            'pass:%s' % passphrase,
            '-passout',
            'pass:%s' % passphrase,
            '-export',
            '-out',
            pfx_file,
        ]
    )
else:
    print('AUTHENTICODE_CERT is missing, skip signing')

#
# Packaging
#
if platform.system() == "Darwin":
    if os.environ.get('AUTHENTICODE_CERT'):
        # Add certificate to login keychain
        keychain = os.path.expanduser('~/Library/Keychains/login.keychain')
        subprocess.check_call(['security', 'import', pfx_file, '-k', keychain, '-P', passphrase])

    # Create app bundle
    app = BUNDLE(
        coll,
        name='Minarca.app',
        icon=macos_icon,
        bundle_identifier='com.ikus-soft.minarca',
        version=version,
        codesign_identity=cert_cn,
    )
    app_file = os.path.abspath('dist/Minarca.app')

    # Binary smoke test
    subprocess.check_call(['dist/minarca.app/Contents/MacOS/minarca', '--version'])

    # Generate dmg image
    dmg_file = os.path.abspath('dist/minarca-client_%s.dmg' % version)
    subprocess.check_call(['dmgbuild', '-s', 'minarca.dmgbuild', '-D', 'app=' + app_file, 'Minarca', dmg_file])

elif platform.system() == "Windows":

    def sign_exe(path):
        if not os.path.isfile(path):
            raise Exception('fail to sign executable: file not found: %s' % path)
        if not os.environ.get('AUTHENTICODE_CERT'):
            return
        # Sign executable.
        unsigned = tempfile.mktemp(suffix='.exe')
        os.rename(path, unsigned)
        subprocess.check_call(
            [
                'osslsigncode.exe',
                'sign',
                '-certs',
                cert_file,
                '-key',
                key_file,
                '-pass',
                passphrase,
                '-n',
                'Minarca',
                '-i',
                'https://minarca.org',
                '-h',
                'sha2',
                '-t',
                'http://timestamp.digicert.com',
                '-in',
                unsigned,
                '-out',
                path,
            ]
        )
        if not os.path.isfile(path):
            raise Exception('fail to sign executable: output file found: %s' % path)

    # Sign executable
    sign_exe('dist/minarca/minarca.exe')

    # For NSIS, we need to convert the license encoding
    with open('dist/minarca/LICENSE', 'r', encoding='UTF-8') as input:
        with open('dist/minarca/LICENSE.txt', 'w', encoding='ISO-8859-1') as out:
            out.write(input.read())

    # Create installer using NSIS
    exe_version = re.search('.*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', '0.0.0.' + version).group(1)
    nsi_file = os.path.abspath('minarca.nsi')
    setup_file = os.path.abspath('dist/minarca-client_%s.exe' % version)
    subprocess.check_call(
        [
            'makensis',
            '-NOCD',
            '-INPUTCHARSET',
            'UTF8',
            '-DAppVersion=' + exe_version,
            '-DOutFile=' + setup_file,
            nsi_file,
        ],
        cwd='dist/minarca',
    )

    # Sign installer
    sign_exe(setup_file)

    # Binary smoke test
    subprocess.check_call(['dist/minarca/minarca.exe', '--version'])

else:
    from debbuild import debbuild

    # For linux simply create a tar.gz with the folder
    targz_file = os.path.abspath('dist/minarca-client_%s.tar.gz' % version)
    subprocess.check_call(['tar', '-zcvf', targz_file, 'minarca'], cwd=os.path.abspath('./dist'))

    # Also create a Debian package
    debbuild(
        name='minarca-client',
        version=version,
        architecture='amd64',
        data_src=[
            ('/opt/minarca', './dist/minarca'),
            ('/usr/share/applications/minarca-client.desktop', './minarca.desktop'),
            ('/opt/minarca/minarca.svg', './minarca_client/ui/theme/resources/minarca.svg'),
            ('/usr/share/doc/minarca-client/copyright', './LICENSE'),
        ],
        description=pkg_info['Summary'],
        long_description=long_description,
        url=pkg_info['Home-page'],
        maintainer="%s <%s>" % (pkg_info['Maintainer'], pkg_info['Maintainer-email']),
        output='./dist',
        postinst="./minarca.postinst",
        symlink=[
            ("/usr/bin/minarca", "/opt/minarca/minarca"),
            ("/opt/minarca/bin/minarca", "../minarca"),
        ],
        depends=[
            'cron',
            'libc6',
            'libstdc++6',
            'libxcb1',
        ],
    )
