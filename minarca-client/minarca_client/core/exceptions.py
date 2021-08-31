'''
Created on Jun. 27, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
from minarca_client.locale import _


class RepositoryNameExistsError(Exception):
    """
    This exception is raised during the linking process when the repository
    name already exists on the remote server.
    """
    pass


class BackupError(Exception):
    """
    This exception is raised when the backup process failed.
    """
    message = None  # should be updated by subclasses.

    def __str__(self):
        return self.message


class InvalidFileSpecificationError(BackupError):
    """
    Raised when a pattern is invalid.
    """

    def __init__(self, file_spec):
        assert file_spec
        # Try to remove 'b'pattern''
        file_spec = file_spec.strip().strip("'").strip("b").strip("'")
        self.message = _(
            "your file specification [%s] doesn't matches any of the base directory of your system") % file_spec


class RdiffBackupError(BackupError):
    """
    This exception is raised when rdiff-backup process return an error.
    """

    def __init__(self, return_code):
        assert return_code
        self.message = _(
            'backup process returned non-zero exit status %s, check logs for more details') % return_code


class NoPatternsError(BackupError):
    """
    This exception is raised when a backup is started without any valid patterns.
    """
    message = _('include patterns are missing')


class NotRunningError(Exception):
    """
    Raised when trying to stop a backup when it's not running.
    """
    message = _("cannot stop backup when it's not running")


class RunningError(BackupError):
    """
    Raised when a backup is already running.
    """
    message = _("cannot start backup when it's already running")


class NotConfiguredError(BackupError):
    """
    Raised when the backup is not configured
    """
    message = _('not configured, use `minarca link` to configure remote host')


class NotScheduleError(BackupError):
    """
    Raised when it's not time to run a backup.
    """
    message = _(
        "backup not yet scheduled to run, you may force execution using `--force`")


class HttpConnectionError(BackupError):
    """
    Raised if the HTTP connection failed.
    """

    def __init__(self, url):
        self.message = _(
            'cannot establish connection to `%s`, verify if the URL is valid') % url


class HttpInvalidUrlError(BackupError):
    """
    Raised when the URL is not valid.
    """

    def __init__(self, url):
        self.message = _(
            'the given URL `%s` is not properly formated, verify if the URL is valid. It must start with either https:// or http://') % url


class HttpAuthenticationError(BackupError):
    """
    Raised for HTTP status code 401 or 403.
    """
    message = _('authentication refused, verify your username and password')


class HttpServerError(BackupError):
    """
    Raised for HTTP status code 5xx.
    """
    message = _('remote server return an error, check remote server log with your administrator')


class SshConnectionError(BackupError):
    """
    Raise if the ssh connection failed.
    """
    pass
