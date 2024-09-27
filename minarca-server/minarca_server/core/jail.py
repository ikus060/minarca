import operator
import os
import shutil
import tempfile
from functools import reduce

from snakeoil.contexts import SplitExec
from snakeoil.osutils.mount import MS_BIND, MS_RDONLY, MS_REC, mount
from snakeoil.process.namespaces import simple_unshare


class Jail(SplitExec):
    """
    Responsible to provide a context manager to split execution into a separate
    process, then using user namespace and chroot isolate the execution
    into a sandbox.

    path will be the only writable folder. Everything else is read-only.

    Only part of the filesystem is available: /bin, /lib, /lib64, /opt, /usr

    See https://lwn.net/Articles/531114/ about Linux User Namespace.
    """

    def __init__(self, path=None):
        SplitExec.__init__(self)
        self.root = tempfile.mkdtemp(prefix='minarca-jail-')
        self.path = path
        if self.path:
            self.path = os.path.abspath(self.path)

    def _child_setup(self):
        # Create a user namespace for isolation.
        simple_unshare(user=True, mount=True, uts=False, net=True, pid=False)

        # Mount proc
        os.mkdir(os.path.join(self.root, 'proc'))
        mount(source='/proc', target=os.path.join(self.root, 'proc'), fstype=None, flags=MS_BIND | MS_REC)
        # Mount /dev/null
        os.mkdir(os.path.join(self.root, 'dev'))
        os.mknod(os.path.join(self.root, 'dev/null'), 0o0666, device=os.makedev(1, 3))
        # Create default mountpoint to run executables.
        for mountpoint in ['/bin', '/lib', '/lib64', '/usr', '/opt']:
            if not os.path.exists(mountpoint):
                continue
            dest = os.path.join(self.root, mountpoint[1:])
            os.mkdir(dest)
            mount(
                source=mountpoint, target=dest, fstype=None, flags=reduce(operator.or_, [MS_BIND, MS_REC, MS_RDONLY], 0)
            )
        # Create custom mount point
        if self.path:
            dest = os.path.join(self.root, self.path[1:])
            os.makedirs(dest)
            mount(source=self.path, target=dest, fstype=None, flags=reduce(operator.or_, [MS_BIND, MS_REC], 0))
        # chroot
        os.chmod(self.root, 0o700)
        os.chroot(self.root)
        os.chdir('/')

    def _cleanup(self):
        shutil.rmtree(self.root)
