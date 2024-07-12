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
import shutil
import subprocess
import tempfile
from email import message_from_string
from importlib.metadata import distribution as get_distribution
from importlib.resources import files
from os.path import join

from PyInstaller.utils.hooks import collect_submodules, copy_metadata

# Use Mock OpenGL to avoid issue on headless
os.environ['KIVY_GL_BACKEND'] = 'mock'
# Disable Kivy config file.
os.environ['KIVY_NO_CONFIG'] = '1'
# Disable Kivy logging
os.environ['KIVY_NO_FILELOG'] = '1'
os.environ['KIVY_LOG_MODE'] = 'PYTHON'

from kivy.tools.packaging.pyinstaller_hooks import get_deps_minimal, hookspath  # noqa

#
# Common values
#
minarca_client_pkg = files('minarca_client')
icon = str(minarca_client_pkg / 'ui/theme/resources/minarca.ico')
macos_icon = str(minarca_client_pkg / 'ui/theme/resources/minarca.icns')

# Read pacakage info
pkg = get_distribution('minarca_client')
version = pkg.version
# Get License file's data
license = pkg.read_text('LICENSE')
_metadata = message_from_string(pkg.read_text('PKG-INFO') or pkg.read_text('METADATA'))
pkg_info = dict(_metadata.items())
long_description = _metadata._payload
block_cipher = None

# Include theme resources and locales
datas = (
    copy_metadata('minarca_client')
    + copy_metadata('rdiff-backup')
    + [
        (minarca_client_pkg / 'ui/theme/resources', 'minarca_client/ui/theme/resources'),
        (minarca_client_pkg / 'locales', 'minarca_client/locales'),
    ]
)
# Include openssh client for windows
if platform.system() == "Windows":
    datas.append((minarca_client_pkg / 'core/openssh', 'minarca_client/core/openssh'))

extras = get_deps_minimal(video=None, audio=None, spelling=None, camera=None)

# Make sure to collect all the files from rdiffbackup (namely the actions)
extras['hiddenimports'].extend(collect_submodules("rdiffbackup"))

# Do the same for Kivymd
extras['hiddenimports'].extend(collect_submodules("kivymd"))

# To work arround a bug with setuptools>=70.0.0 and pyinstaller<6
# See https://github.com/pyinstaller/pyinstaller/issues/8554
extras['hiddenimports'].append('pkg_resources.extern')

# On MacOS, make sure to include librsync.2.dylib because @rpath is not working properly in PyInstaller<6
if platform.system() == "Darwin":
    librsync_path = shutil.which(
        'librsync.2.dylib', path='/usr/lib:/usr/local/lib:/System/Library/Frameworks:/Library/Frameworks'
    )
    extras['binaries'].append((librsync_path, '.'))

main_py = minarca_client_pkg / 'main.py'
a = Analysis(
    [main_py],
    pathex=[],
    datas=datas,
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
    from kivy_deps import angle, glew, sdl2

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
        ],
        stderr=subprocess.STDOUT,
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
        subprocess.check_call(
            ['security', 'import', pfx_file, '-k', keychain, '-P', passphrase], stderr=subprocess.STDOUT
        )

    # Create app bundle
    app = BUNDLE(
        coll,
        name='Minarca.app',
        icon=macos_icon,
        bundle_identifier='com.ikus-soft.minarca',
        version=version,
        codesign_identity=cert_cn,
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
            ],
            stderr=subprocess.STDOUT,
        )
        if not os.path.isfile(path):
            raise Exception('fail to sign executable: output file found: %s' % path)

    # Sign executable
    sign_exe(join(DISTPATH, 'minarca/minarca.exe'))

    # For NSIS, we need to create a license file with Windows encoding.
    with open(join(DISTPATH, 'minarca/LICENSE.txt'), 'w', encoding='ISO-8859-1') as out:
        out.write(license)

    # Create installer using NSIS
    exe_version = re.search(r'.*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', '0.0.0.' + version).group(1)
    nsi_file = join(SPECPATH, 'minarca.nsi')
    setup_file = join(DISTPATH, 'minarca-client_%s.exe' % version)
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
        cwd=join(DISTPATH, 'minarca'),
        stderr=subprocess.STDOUT,
    )

    # Sign installer
    sign_exe(setup_file)

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
            ('/usr/share/applications/minarca-client.desktop', join(SPECPATH, 'minarca.desktop')),
            ('/opt/minarca/minarca.svg', join(DISTPATH, 'minarca/minarca_client/ui/theme/resources/minarca.svg')),
        ],
        description=pkg_info['Summary'],
        long_description=long_description,
        url=pkg_info['Home-page'],
        maintainer="%s <%s>" % (pkg_info['Maintainer'], pkg_info['Maintainer-email']),
        output=DISTPATH,
        postinst=join(SPECPATH, "minarca.postinst"),
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
