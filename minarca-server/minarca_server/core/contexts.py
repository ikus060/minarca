# Ideas and code for SplitExec have been borrowed from withhacks
# (https://pypi.python.org/pypi/withhacks) governed by the MIT license found
# below.
#
# Copyright (c) 2010 Ryan Kelly
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import errno
import inspect
import os
import pickle
import signal
import sys
import threading
import traceback
from multiprocessing.connection import Pipe


class SplitExec:
    """Context manager separating code execution across parent/child processes.

    This is done by forking and doing some magic on the stack so the contents
    of the context are executed only on the forked child. Exceptions are
    pickled and passed back to the parent.
    """

    def __init__(self):
        self.__trace_lock = threading.Lock()
        self.__orig_sys_trace = None
        self.__orig_trace_funcs = {}
        self.__injected_trace_funcs = {}
        self.__pipe = None
        self.childpid = None
        self.exit_status = -1
        self.locals = {}

    def _parent_handler(self, signum, frame):
        """Signal handler for the parent process.

        By default this runs the parent cleanup and then resends the original
        signal to the parent process.
        """
        self._cleanup()
        signal.signal(signum, signal.SIG_DFL)
        os.kill(os.getpid(), signum)

    def _parent_setup(self):
        """Initialization for parent process."""
        try:
            signal.signal(signal.SIGINT, self._parent_handler)
            signal.signal(signal.SIGTERM, self._parent_handler)
        except ValueError:
            # skip if we're not in the main thread
            pass

    def _child_setup(self):
        """Initialization for child process."""

    def _cleanup(self):
        """Parent process clean up on termination of the child."""

    def _exception_cleanup(self):
        """Parent process clean up after the child throws an exception."""
        self._cleanup()

    def _child_exit(self, exc):
        # pass back changed local scope vars from the child that can be pickled
        frame = self.__get_context_frame()
        local_vars = {}
        for k, v in frame.f_locals.items():
            if k not in self.__child_orig_locals or v != self.__child_orig_locals[k]:
                try:
                    pickle.dumps(v)
                    local_vars[k] = v
                except (AttributeError, TypeError, pickle.PicklingError):
                    continue
        exc._locals = local_vars

        try:
            self.__pipe.send(exc)
        except BrokenPipeError as e:
            if e.errno in (errno.EPIPE, errno.ESHUTDOWN):
                pass
            else:
                raise

        if isinstance(exc, SystemExit) and exc.code is not None:
            code = exc.code
        else:
            code = 0
        os._exit(code)  # pylint: disable=W0212

    def __enter__(self):
        parent_pipe, child_pipe = Pipe()
        childpid = os.fork()
        if childpid:
            self.childpid = childpid
            self._parent_setup()
            self.__pipe = parent_pipe
            frame = self.__get_context_frame()
            self.__inject_trace_func(frame, self.__exit_context)
            return self
        else:
            frame = self.__get_context_frame()
            self.__child_orig_locals = dict(frame.f_locals)
            self.__pipe = child_pipe

            try:
                self._child_setup()
            # pylint: disable=W0703
            # need to catch all exceptions here since we are passing them to
            # the parent process
            except Exception as exc:
                exc.__traceback_list__ = traceback.format_exc()
                self._child_exit(exc)

            return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.childpid is not None:
            # make sure system tracing function is reset
            self.__revert_tracing(inspect.currentframe())
            # re-raise unknown exceptions from the parent
            if exc_type is not self.ParentException:
                raise exc_value

            # get exception from the child
            try:
                exc = self.__pipe.recv()
                self.locals = exc._locals
            except EOFError as e:
                exc = SystemExit(e)

            # handle child exiting abnormally
            if not isinstance(exc, SystemExit):
                os.waitpid(self.childpid, 0)
                self._exception_cleanup()
                sys.excepthook = self.__excepthook
                raise exc
        else:
            if exc_value is not None:
                exc = exc_value
                # Unfortunately, traceback objects can't be pickled so the relevant
                # traceback from the code executing within the chroot context is
                # placed in the __traceback_list__ attribute and printed by a
                # custom exception hook.
                exc.__traceback_list__ = traceback.format_exc()
            else:
                exc = SystemExit()

            self._child_exit(exc)

        # wait for child process to exit
        _pid, exit_status = os.waitpid(self.childpid, 0)
        self.exit_status = exit_status >> 8
        self._cleanup()

        return True

    @staticmethod
    def __excepthook(_exc_type, exc_value, exc_traceback):
        """Output the proper traceback information from the chroot context."""
        if hasattr(exc_value, '__traceback_list__'):
            sys.stderr.write(exc_value.__traceback_list__)
        else:
            traceback.print_tb(exc_traceback)

    @staticmethod
    def __dummy_sys_trace(frame, event, arg):
        """Dummy trace function used to enable tracing."""

    class ParentException(Exception):
        """Exception used to detect when the child terminates."""

    def __enable_tracing(self):
        """Enable system-wide tracing via a dummy method."""
        self.__orig_sys_trace = sys.gettrace()
        sys.settrace(self.__dummy_sys_trace)

    def __revert_tracing(self, frame=None):
        """Revert to previous system trace setting."""
        sys.settrace(self.__orig_sys_trace)
        if frame is not None:
            frame.f_trace = self.__orig_sys_trace

    def __exit_context(self, frame, event, arg):
        """Simple function to throw a ParentException."""
        raise self.ParentException()

    def __inject_trace_func(self, frame, func):
        """Inject a trace function for a frame.

        The given trace function will be executed immediately when the frame's
        execution resumes.
        """
        with self.__trace_lock:
            if frame.f_trace is not self.__invoke_trace_funcs:
                self.__orig_trace_funcs[frame] = frame.f_trace
                frame.f_trace = self.__invoke_trace_funcs
                self.__injected_trace_funcs[frame] = []
                if len(self.__orig_trace_funcs) == 1:
                    self.__enable_tracing()
        self.__injected_trace_funcs[frame].append(func)

    def __invoke_trace_funcs(self, frame, event, arg):
        """Invoke all trace funcs that have been injected.

        Once the injected functions have been executed all trace hooks are
        removed in order to minimize overhead.
        """
        try:
            for func in self.__injected_trace_funcs[frame]:
                func(frame, event, arg)
        finally:
            del self.__injected_trace_funcs[frame]
            with self.__trace_lock:
                if len(self.__orig_trace_funcs) == 1:
                    self.__revert_tracing()
                frame.f_trace = self.__orig_trace_funcs.pop(frame)

    def __get_context_frame(self):
        """Get the frame object for the with-statement context.

        This is designed to work from within superclass method call. It finds
        the first frame where the local variable "self" doesn't exist.
        """
        try:
            return self.__frame
        except AttributeError:
            # an offset of two accounts for this method and its caller
            frame = inspect.stack(0)[2][0]
            while frame.f_locals.get('self') is self:
                frame = frame.f_back
            self.__frame = frame  # pylint: disable=W0201
            return frame
