# Python script used to apply the patches

import glob
import os
import subprocess
import sys
import sysconfig

import patch  # noqa

# Get location of all the patch file
patches_dir = os.path.dirname(os.path.realpath(__file__))
# Get location of site-packages
site_packages = sysconfig.get_paths()["purelib"]

print('applying patches...')

# Loop on each patch
for fn in glob.glob(os.path.join(patches_dir, '*.patch')):
    subprocess.check_call([sys.executable, '-m', 'patch', '--verbose', '-p2', '-d', site_packages, fn])

print('apply patches: done')
