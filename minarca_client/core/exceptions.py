# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 27, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''

from minarca_client.locale import _


class CaptureException:
    exception = None

    def __init__(self, logger) -> None:
        self.logger = logger

    def __call__(self, line):
        self.logger.debug(line)
        for cls in [
            ConnectException,
            DiskFullError,
            DiskQuotaExceededError,
            UnknownHostException,
            UnknownHostKeyError,
            PermissionDeniedError,
        ]:
            if cls._matches(line):
                self.exception = cls()


class BackupError(Exception):
    """
    This exception is raised when the backup process failed.
    """

    message = None  # should be updated by subclasses.

    def __str__(self):
        return self.message


class RepositoryNameExistsError(BackupError):
    """
    This exception is raised during the linking process when the repository
    name already exists on the remote server.
    """

    def __init__(self, name):
        self.name = name
        self.message = (
            _(
                'Fail to link because repository with name `%s` already exists on remote server. You may force the operation by using `--force` on command line.'
            )
            % name
        )


class InvalidFileSpecificationError(BackupError):
    """
    Raised when a pattern is invalid.
    """

    def __init__(self, file_spec):
        assert file_spec
        # Try to remove 'b'pattern''
        file_spec = file_spec.strip().strip("'").strip("b").strip("'")
        self.message = (
            _("your file specification [%s] doesn't matches any of the base directory of your system") % file_spec
        )


class RdiffBackupException(BackupError):
    """
    Raise whenever rdiff-backup raise an exception.
    """

    def __init__(self, msg) -> None:
        self.message = _('backup process terminated with an exception, check logs for more details: %s') % msg


class RdiffBackupExitError(BackupError):
    """
    This exception is raised when rdiff-backup process return an error.
    """

    message = _('backup process returned non-zero exit status, check logs for more details')


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

    message = _("backup not yet scheduled to run, you may force execution using `--force`")


class HttpConnectionError(BackupError):
    """
    Raised if the HTTP connection failed.
    """

    def __init__(self, url):
        super().__init__(url)
        self.message = _('cannot establish connection to `%s`, verify if the URL is valid') % url


class HttpInvalidUrlError(BackupError):
    """
    Raised when the URL is not valid.
    """

    def __init__(self, url):
        super().__init__(url)
        self.message = (
            _(
                'the given URL `%s` is not properly formated, verify if the URL is valid. It must start with either https:// or http://'
            )
            % url
        )


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


class ConnectException(BackupError):
    """
    Raised when rdiff-backup fail to establish SSH connection with remove host.
    """

    message = _(
        'Unable to connect to the remote server. The problem may be with the remote server. If the problem persists, contact your system administrator to check the SSH server configuration and a possible firewall blocking the connection.'
    )

    @staticmethod
    def _matches(line):
        # ssh: connect to host test.minarca.net port 8976: Connection refused
        return 'ssh: connect to host' in line and 'Connection refused' in line


class PermissionDeniedError(BackupError):
    """
    Raised by SSH when remote server refused our identity.
    """

    message = _(
        'Backup failed due to our identity being refused by remote server. The problem may be with the remote server. If the problem persists, contact your system administrator to review your SSH identity.'
    )

    @staticmethod
    def _matches(line):
        return 'Permission denied (publickey)' in line


class UnknownHostKeyError(BackupError):
    """
    Raised by SSH when remote server is unknown.
    """

    message = _(
        'Backup failed due to unknown remote server identity. If the problem persists, contact your system administrator to review the server identity.'
    )

    @staticmethod
    def _matches(line):
        return 'Host key verification failed.' in line


class DiskQuotaExceededError(BackupError):
    """
    Raised by rdiff-backup remote server when the disk quota is reached.
    """

    message = _('Backup failed due to disk quota exceeded. Please free up disk space to ensure successful backup.')

    @staticmethod
    def _matches(line):
        return 'OSError: [Errno 122] Disk quota exceeded' in line


class DiskFullError(BackupError):
    """
    Raised by rdiff-backup remote server when the disk is full"
    """

    message = _('Backup failed due disk is full. Please clear space on the disk to proceed with the backup.')

    @staticmethod
    def _matches(line):
        return 'OSError: [Errno 28] No space left on device' in line


class UnknownHostException(BackupError):
    """
    Raised by rdiff-backup when remote host name could not be resolved.
    """

    message = _(
        'Backup failed due unresolvable hostname. Please check your network connection and ensure the hostname is valid.'
    )

    @staticmethod
    def _matches(line):
        return 'ssh: Could not resolve hostname' in line
