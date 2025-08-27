# Copyright (C) 2025 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 27, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''

#
# Exit Code
#
# 0,1,2: Reserved for Rdiff-Backup Success, Error, Warning
#
# 10-...: Minarca Client exit code.
#
# 101-111: Exitcode defined in v6.0.0. Kept for backward compatibility.
#
# 126-130: Reserved for system exit code
#
# 141: Reserved for Broken pipe
#
# 200-205: Reserved for Minaca shell
#

import re

from minarca_client.locale import _


def _find_exception_with(exc, attrname):
    """
    Recursively search through the exception's __cause__ and __context__
    to find an exception that has a the given attribute name.

    :param exc: The exception to start the search from.
    :param attrname: The attribute name to search for..
    :return: The first exception found that has a 'reason' attribute, or None if not found.
    """
    visited = set()

    def _search(e):
        if e in visited or e is None:
            return None
        visited.add(e)
        if getattr(e, attrname, False):
            return e
        return _search(getattr(e, '__cause__', None)) or _search(getattr(e, '__context__', None))

    return _search(exc)


def handle_http_errors(func):
    """
    Decorator to handle HTTP exception raised when calling rdiffweb server.
    """

    async def wrapper(self, *args, **kwargs):
        from requests.exceptions import ConnectionError, HTTPError, InvalidSchema, MissingSchema

        try:
            return await func(self, *args, **kwargs)
        except ConnectionError as e:
            cause = _find_exception_with(e, 'strerror')
            raise HttpConnectionError(cause or str(e)) from e
        except (MissingSchema, InvalidSchema) as e:
            raise HttpInvalidUrlError(str(e)) from e
        except HTTPError as e:
            # Raise for invalid status code.
            if e.response.status_code in [401, 403]:
                raise HttpAuthenticationError(e)
            # Special case to extract error message from HTML body.
            server_error = HttpServerError(e)
            if e.response.status_code == 400 and e.response.text.startswith('<'):
                m = re.search(r'<p>(.*)</p>', e.response.text)
                if m and m[1]:
                    server_error.message = m[1]
            raise server_error

    return wrapper


class BackupError(Exception):
    """
    Generic error code for unknown or unhandled backup errors.
    """

    message = None  # Updated by subclass
    detail = None
    error_code = 101

    def __str__(self):
        if self.error_code:
            return _(f"{self.message} (Error: {self.error_code})")
        return self.message


class ConfigureBackupError(BackupError):
    """
    Generic error code for unknown or unhandled configuration errors.
    """

    error_code = 102


class InstanceNotFoundError(BackupError):
    """
    Raised when backup instances (--instance) returns no data.

    Double check your command line and make sure the instance number provided on command line exists.
    """

    error_code = 103
    message = _('No backup instances match: %s')

    def __init__(self, instance_id):
        self.instance_id = instance_id
        self.message = InstanceNotFoundError.message % instance_id


class RepositoryNameExistsError(ConfigureBackupError):
    """
    Raised during the configuration process when the repository name already exists on the destination server.

    The name of the repository you are trying to created already exists on the destination. You have the option
    of using a different name for your destination or to override and replace the existing repository name.
    To replace it, you will need to "--force" the operation.
    """

    error_code = 104
    message = _('Destination `%s` already exists.')

    def __init__(self, name):
        self.name = name
        self.message = RepositoryNameExistsError.message % name


class NotRunningError(BackupError):
    """
    Raised when attempting to stop a backup that is not running.
    """

    error_code = 105
    message = _("cannot stop process when it's not running.")


class LinkError(BackupError):
    """
    Reserved for future use.
    """

    error_code = 106


class ScheduleError(ConfigureBackupError):
    """
    Reserved for future use.
    """

    error_code = 107


class KivyError(Exception):
    """
    Raised when the Graphical User Interface (GUI) fails to load.
    """

    error_code = 108


class RestoreFail(BackupError):
    """
    Reserved for future use.
    """

    error_code = 109


class InterruptedError(Exception):
    """
    Raised when interupted by user. DEPRECATED replace by generic status code 130.
    """

    error_code = 110


class NoStdoutError(Exception):
    """
    Raised when terminal output is not available.DEPRECATED replace by generic status code 141 Broken Pipe.
    """

    error_code = 111


class RdiffBackupException(BackupError):
    """
    Raised when backup execution encounters an unexpected exception.

    The internal backup process execution raised an unexpected exception.
    To get more details about the problem you need to verify the logs.
    """

    error_code = 10
    message = _('process terminated with an exception. Check logs for more details: %s')

    def __init__(self, msg) -> None:
        self.message = RdiffBackupException.message % msg


class RdiffBackupExitError(BackupError):
    """
    Generic error raised when the backup process return a non-zero exit status.

    The internal backup process return an unexpected error.
    To get more details about the problem you need to verify the logs.
    """

    error_code = 11
    message = _('process returned a non-zero exit status (%s). Check logs for more details')

    def __init__(self, exit_code) -> None:
        self.message = RdiffBackupExitError.message % exit_code


class RunningError(BackupError):
    """
    Raised when a backup is already running.

    You cannot start a backup when another instance of the backup is already running.
    If you want to restart the backup, you must first stop the previous backup process
    to start a new one.

    """

    error_code = 12

    message = _("cannot start process when it's already running.")


class NotScheduleError(BackupError):
    """
    Raised when it's not yet time to run a backup.

    The application determined it's not required to executed a backup according to the previous backup status and the configure frequency.
    """

    error_code = 13

    message = _("backup not yet scheduled to run. You may force execution using `--force`")


class ConnectException(BackupError):
    """
    Triggered when backup fails to establish an SSH connection with the remote host.

    Connection to the remote server trought SSH protocol was refused. Make sure it's possible to
    establish a connection with the server trough the SSH port. You may need to verify is Port-Forwarding
    are properly configure for SSH. Make sure a firewall is not blocking the communication. Some
    Internet provider are blocking traffic when using default SSH port 22. You may need to configure
    your server to use an alternate port.
    """

    error_code = 14

    message = _(
        'Unable to connect to the remote server. The problem may be with the remote server. If the problem persists, contact your system administrator to check the SSH server configuration and a possible firewall blocking the connection.'
    )

    @staticmethod
    def _matches(line):
        # ssh: connect to host test.minarca.net port 8976: Connection refused
        return b'ssh: connect to host' in line and b'Connection refused' in line


class PermissionDeniedError(BackupError):
    """
    Raised by SSH when the remote server refuses the identity.

    The remove server refused our identity. This usually indicate an issue with the remove server
    configuration. Double check the server log. Check server logs, to make sure the public
    key get writte to the `/backup/.ssh/authorized_keys` and also check the SSH server
    authentication logs `/var/log/auth.log` to verify why the SSH server is refusing our
    identity.
    """

    error_code = 15

    message = _(
        'The connection to the remote server failed because our identity was refused. The problem may lie with the remote server. If the problem persists, contact your system administrator to check your SSH identity.'
    )

    @staticmethod
    def _matches(line):
        return b'Permission denied (publickey)' in line


class UnknownHostKeyError(BackupError):
    """
    Raised by SSH when the remote server is unknown.

    The remote server's host keys do not match the expected values. This could mean that the server's host keys (/etc/ssh/ssh_host_*) have been changed, or you may be connecting to a different server than intended. To protect against potential security risks, the connection has been blocked.
    """

    error_code = 16

    message = _(
        "The connection to the remote server cannot be established securely because the server's identity has changed. If the problem persists, contact your system administrator to verify the server's identity."
    )

    @staticmethod
    def _matches(line):
        return b'Host key verification failed.' in line


class DiskQuotaExceededError(BackupError):
    """
    Raised when the disk quota on the remote server is reached.
    """

    error_code = 17

    message = _('Backup failed due to disk quota exceeded. Please free up disk space to ensure successful backup.')

    @staticmethod
    def _matches(line):
        return b'OSError: [Errno 122] Disk quota exceeded' in line


class DiskFullError(BackupError):
    """
    Raised when the disk on the remote server is full.
    """

    message = _('Backup failed due to disk being full. Please clear space on the disk to proceed with the backup.')
    error_code = 18

    @staticmethod
    def _matches(line):
        return b'OSError: [Errno 28] No space left on device' in line


class UnknownHostException(BackupError):
    """
    Raised by rdiff-backup when the remote host name cannot be resolved.
    """

    message = _(
        'The connection to the remote server has failed due to an unresolvable host name. Please check your network connection and ensure that the host name is still valid. If the problem persists, contact your system administrator to check the host name.'
    )
    error_code = 19

    @staticmethod
    def _matches(line):
        return b'ssh: Could not resolve hostname' in line


class UnsuportedVersionError(BackupError):
    """
    Raised by backup process when the remote server is not compatible with the client version.
    """

    error_code = 20

    message = _(
        'The connection to the remote server failed because your agent version isn’t supported. Please update your client or server.'
    )

    @staticmethod
    def _matches(line):
        return b'ERROR unsupported version:' in line or b'ERROR: unsupported version:' in line


class RestoreFileNotFound(BackupError):
    """
    Raised when the selected path to restore does not exist in the backup.
    """

    message = _('The path you are trying to restore from backup does not exist.')
    error_code = 21

    @staticmethod
    def _matches(line):
        return b"couldn't be identified as being within an existing backup repository" in line


class RepositoryLocked(BackupError):
    """
    Raised when the backup destination is locked, likely by another backup process.
    """

    message = _('Another backup session is currently in progress on the remote server.')
    error_code = 22

    @staticmethod
    def _matches(line):
        return b"Fatal Error: It appears that a previous rdiff-backup session" in line


class UnrecognizedArguments(BackupError):
    """
    Raised when an unknown operation is sent to the backup process.
    """

    message = _('An internal error was raised by an unknown operation sent to the background process.')
    error_code = 23

    @staticmethod
    def _matches(line):
        return b"error: unrecognized arguments: " in line


class LocalDestinationNotFound(BackupError):
    """
    Raised when an external disk for a local backup is not found or not mounted.
    """

    message = _(
        "Backup Destination Not Found. Please ensure that your external disk or network share is properly connected and accessible."
    )
    error_code = 24


class DiskDisconnectedError(BackupError):
    message = _(
        "Backup unsuccessful due to a copy operation encountering an issue, potentially because the device is disconnected. Ensure your device is properly connected."
    )
    error_code = 25

    @staticmethod
    def _matches(line):
        return b'OSError: [Errno 5] Input/output error' in line


class RemoteRepositoryNotFound(BackupError):
    """
    Raised when the expected repository cannot be found.
    """

    message = _('Repository cannot be found on remote server')
    error_code = 26

    def __init__(self, name=None):
        self.name = name
        if name:
            self.message = _('Repository `%s` cannot be found on remote server') % name

    @staticmethod
    def _matches(line):
        # ERROR:   Path 'pop-os' couldn't be identified as being within an existing
        #          backup repository
        return b"couldn't be identified as being within an existing" in line


class RemoteServerTruncatedHeader(BackupError):
    """
    This error occurs when the remote server terminates the connection unexpectedly.

    During a backup, this may happen occasionally if the connection is interrupted. However,
    if the issue occurs while configuring a new connection, it likely indicates a problem
    with the remote server.

    To troubleshoot, check the server logs:

    1. Verify SSH authentication in `/var/log/auth.log.`

    2. Verify connection is successful in `/var/log/minarca/shell.log`.
    """

    message = _(
        "The connection was terminated unexpectedly, which may indicate an issue with the remote server. If the problem persists, contact your system administrator to review the server logs and diagnose the cause."
    )
    error_code = 27

    @staticmethod
    def _matches(line):
        # due to exception 'Truncated header <b''> (problem probably originated remotely)'.
        return b"due to exception 'Truncated header <b''> (problem probably originated remotely)'." in line


class InvalidFileSpecificationError(ConfigureBackupError):
    """
    Raised when an invalid pattern is specified.
    """

    error_code = 28
    message = _("your file specification [%s] doesn't match any of the base directories of your system")

    def __init__(self, file_spec):
        assert file_spec
        # Try to remove 'b'pattern''
        file_spec = file_spec.strip().strip("'").strip("b").strip("'")
        self.message = InvalidFileSpecificationError.message % file_spec


class NoPatternsError(ConfigureBackupError):
    """
    Raised when a backup is started without valid patterns.

    Your trying to start a backup while you have not configure file and folder to
    be backup. Using the graphical interface, you need to add folder or file to
    backup in "File Selection". Using the command line, you need to add file or
    folder using "minarca include <path>".
    """

    error_code = 29

    message = _('No files included in backup. Check configuration.')


class NotConfiguredError(ConfigureBackupError):
    """
    Raised when the backup is not properly configured.

    You cannot star a backup process if you have not properly configure it first. Use the
    graphical user interface to configure a backup destination or use command line interface
    "minarca configure ...".
    """

    error_code = 30

    message = _('not configured, use `minarca configure` to configure remote host')


class HttpConnectionError(ConfigureBackupError):
    """
    Raised when a secure (HTTPS) or regular HTTP connection fails.

    This exception generalizes connection errors, including plain HTTP errors
    and SSL/TLS handshake failures. The specific cause is indicated by the
    'connection_type' parameter and can be 'http' or 'ssl'.

    Suggested actions include verifying the URL, checking your Internet connection,
    or ensuring that SSL certificates are valid and trusted.
    """

    error_code = 31
    message = _('Cannot connect to the server.')
    detail = _(
        "Your computer cannot establish a connection to the remote server. Make sure your Internet connection is working and that the following URL is accessible with a Web browser:\n%s"
    )

    def __init__(self, reason):
        self.detail = HttpConnectionError.detail % reason


class HttpInvalidUrlError(ConfigureBackupError):
    """
    Raised when the provided URL is invalid.

    The URL provided is not valid. Double check the syntaxe of the URL. Make sure it start with 'http://' or 'https://'.
    """

    error_code = 32
    message = _('Invalid URL')
    detail = _(
        "The remote server URL you entered for the connection is not valid. Check that you have entered the correct value. The URL must begin with `http://` or `https://` followed by a domain name.\n%s"
    )

    def __init__(self, url):
        self.message = HttpInvalidUrlError.detail % url


class HttpAuthenticationError(ConfigureBackupError):
    """
    Raised for HTTP status codes 401 (Unauthorized) or 403 (Forbidden).

    "The username or password you entered to connect to the remote server is not valid.
    If you have enabled multi-factor authentication, you need to use an access token."
    """

    error_code = 33
    message = _('Invalid username or password')
    detail = _(
        "The username or password you entered to connect to the remote server is not valid. If you have enabled multi-factor authentication, you need to use an access token."
    )

    def __init__(self, server_message=None):
        self.server_message = server_message


class HttpServerError(ConfigureBackupError):
    """
    Raised for HTTP status codes in the 5xx range (server errors).

    The remove server return a unexpected server error. Check the remote server logs
    to get more details about the problem.
    """

    error_code = 34
    message = _('The remote server returned an error. You may try again later.')

    def __init__(self, server_error) -> None:
        self.detail = str(server_error)


class LocalDestinationNotEmptyError(ConfigureBackupError):
    """
    Raised when the specified local backup destination is not empty and does not contain rdiff-backup-data.
    """

    error_code = 35
    message = _('Backup Destination Occupied')
    detail = _(
        'Unable to proceed with the selected destination as it contains existing data. If you intend to use this location, kindly empty the directory of any files and folders.'
    )


class InitDestinationError(ConfigureBackupError):
    """
    Raised during the initialization process of a local backup destination, e.g., failure to create a file or folder.
    """

    error_code = 36
    message = _("Destination Not Suitable")
    detail = _(
        'Unable to proceed with the selected destination as it cannot be initialized. Make sure the external device is connected and operational.'
    )


class InvalidRepositoryName(ConfigureBackupError):
    """
    Raised when the repository name is invalid.
    """

    error_code = 37
    message = _("Repository name must contain only letters, numbers, dashes (-), and dots (.)")

    def __init__(self, name):
        self.name = name


class DuplicateSettingsError(ConfigureBackupError):
    """
    Raised when attempting to configure a new backup instance with settings that already exist.

    The configure you provided already exists and will conflict with another configured backup.
    """

    error_code = 38
    message = _('These settings conflict with an existing backup and therefore cannot be created.')
    detail = _(
        "It is not possible to create two backups with the same destination settings. These will conflict during backup. Be sure to define a different destination for this backup."
    )

    def __init__(self, other_instance):
        self.other = other_instance


class JailCreationError(BackupError):
    """
    Raised when the remote server fail to create the unpriviledge user namespace.

    This error is raised when the server is not properly configure to create a user namespace (a jail) to run the backup process.

    Read more about it:

    * [How to enable Unprivileged User Namespace](installation.md#enable-unprivileged-user-namespace-for-containers)
    """

    error_code = 39

    message = _(
        "The remote server could not create the necessary security context, which may indicate an issue with the server. If the problem persists, please contact your system administrator to review the server logs and diagnose the cause."
    )

    @staticmethod
    def _matches(line):
        return b'ERROR: fail to create rdiff-backup jail' in line


class IMAPListFolderError(BackupError):
    """
    Raised by `minarca imap-backup ...` when IMAP error occur during backup.
    """

    error_code = 40

    message = _("Fail to list IMAP folders.")

    @staticmethod
    def _matches(line):
        return b'ERROR: fail to create rdiff-backup jail' in line


class CaptureException:
    """
    Parse log line to search for known exception.
    """

    _error_priorities = [
        RemoteServerTruncatedHeader,
        ConnectException,
        DiskFullError,
        DiskQuotaExceededError,
        UnknownHostException,
        UnknownHostKeyError,
        PermissionDeniedError,
        UnsuportedVersionError,
        RepositoryLocked,
        RestoreFileNotFound,
        UnrecognizedArguments,
        DiskDisconnectedError,
        RemoteRepositoryNotFound,
        JailCreationError,
    ]
    exception = None
    _priority = -1

    def parse(self, line):
        """
        Search for error in given log line. If an error is found, an exception is created in `self.exception`.
        """
        assert isinstance(line, bytes)
        for priority, cls in enumerate(self._error_priorities):
            if cls._matches(line) and priority > self._priority:
                self.exception = cls()
                self._priority = priority
