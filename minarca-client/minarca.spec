# -*- mode: python ; coding: utf-8 -*-
#
# Copyright (C) 2021 IKUS Software inc. All rights reserved.
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
import subprocess
import tempfile
import pkg_resources
import re
from PyInstaller.utils.hooks import copy_metadata

#
# Common values
#
icon = 'minarca_client/ui/theme/minarca.ico'
macos_icon = 'minarca_client/ui/theme/minarca.icns'
version = pkg_resources.get_distribution("minarca_client").version
block_cipher = None


# Include openssh client for windows
if platform.system() == "Windows":
    openssh = [('minarca_client/core/openssh', 'minarca_client/core/openssh')]
else:
    openssh = []

a = Analysis(
    ['minarca_client/main.py'],
    pathex=[],
    binaries=[],
    datas=copy_metadata('minarca_client') + copy_metadata('rdiff-backup') + openssh + [
        ('README.md', '.'),
        ('LICENSE', '.'),
        ('minarca_client/ui/templates', 'minarca_client/ui/templates'),
        ('minarca_client/ui/theme', 'minarca_client/ui/theme'),
        ('minarca_client/locales', 'minarca_client/locales'),
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False)

pyz = PYZ(
    a.pure, a.zipped_data,
    cipher=block_cipher)

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
    console=False)
all_exe = [exe_w]

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
    console=True)
all_exe += [exe_c]

coll = COLLECT(
    *all_exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='minarca')

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
        ['openssl', 'x509', '-noout', '-subject', '-in', cert_file],
        text=True).strip()
    cert_cn = cert_subject.partition('/CN=')[2]
    # Code signing on Windows required pfx file.
    pfx_file = tempfile.mktemp(suffix='.pfx')
    subprocess.check_call(
        ['openssl', 'pkcs12', '-inkey', key_file, '-in', cert_file, '-passin',
         'pass:%s' % passphrase, '-passout', 'pass:%s' % passphrase, '-export', '-out', pfx_file])
else:
    print('AUTHENTICODE_CERT is missing, skip signing')

#
# Packaging
#
if platform.system() == "Darwin":

    # Create app bundle
    app = BUNDLE(
        coll,
        name='Minarca.app',
        icon=macos_icon,
        bundle_identifier='com.ikus-soft.minarca',
        version=version,
    )
    app_file = os.path.abspath('dist/Minarca.app')

    # Binary smoke test
    subprocess.check_call(
        ['dist/minarca.app/Contents/MacOS/minarca', '--version'])

    # Sign Application Bundle
    if os.environ.get('AUTHENTICODE_CERT'):
        # Add certificate to loging keychain
        keychain = os.path.expanduser('~/Library/Keychains/login.keychain')
        subprocess.check_call(
            ['security', 'import', pfx_file, '-k', keychain, '-P', passphrase])
        # Sign MacOS X App bundle
        # --deep to sign subcomponents
        # --keychain to limit keychain lookup
        # See https://www.unix.com/man-page/osx/1/codesign/
        subprocess.check_call(
            ['codesign', '--deep', '--keychain', keychain, '--sign', cert_cn, app_file])

    # Generate dmg image
    dmg_file = os.path.abspath('dist/minarca-client_%s.dmg' % version)
    subprocess.check_call([
        'dmgbuild',
        '-s', 'minarca.dmgbuild',
        '-D', 'app=' + app_file,
        'Minarca',
        dmg_file])

elif platform.system() == "Windows":

    def sign_exe(path):
        if not os.environ.get('AUTHENTICODE_CERT'):
            return
        # Sign executable.
        unsigned = tempfile.mktemp(suffix='.exe')
        os.rename(path, unsigned)
        subprocess.check_call([
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
            path])

    # Sign executable
    sign_exe('dist/minarca/minarca.exe')

    # For NSIS, we need to convert the license encoding
    with open('dist/minarca/LICENSE', 'r', encoding='UTF-8') as input:
        with open('dist/minarca/LICENSE.txt', 'w', encoding='ISO-8859-1') as out:
            out.write(input.read())

    # Create installer using NSIS
    exe_version = re.search(
        '.*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', '0.0.0.' + version).group(1)
    nsi_file = os.path.abspath('minarca.nsi')
    setup_file = os.path.abspath('dist/minarca-client_%s.exe' % version)
    subprocess.check_call([
        'makensis',
        '-NOCD',
        '-INPUTCHARSET',
        'UTF8',
        '-DAppVersion=' + exe_version,
        '-DOutFile=' + setup_file,
        nsi_file],
        cwd='dist/minarca')

    # Sign installer
    sign_exe(setup_file)

    # Binary smoke test
    subprocess.check_call(['dist/minarca/minarca.exe', '--version'])

else:

    # For linux simply create a tar.gz with the folder
    targz_file = os.path.abspath('dist/minarca-client_%s.tar.gz' % version)
    subprocess.check_call([
        'tar',
        '-zcvf',
        targz_file,
        'minarca'],
        cwd=os.path.abspath('./dist'))
