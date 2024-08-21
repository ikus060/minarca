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

    def parse(self, line):
        for cls in [
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
        ]:
            if cls._matches(line):
                self.exception = cls()


# TODO Need to split exceptions.
# RuntimeBackupError
# ConfigureBackupError


class BackupError(Exception):
    """
    This exception is raised when the backup process failed.
    """

    message = None  # should be updated by subclasses.
    detail = None

    def __str__(self):
        return self.message


class ConfigureBackupError(BackupError):
    """
    These exception are raise during configuration of backup.
    """


class RuntimeBackupError(BackupError):
    """
    These exception are raise during execution of backup or restore operation.
    """


class InstanceNotFoundError(BackupError):
    """
    This exception is raised whenever a backup[foo] return nothing
    """

    def __init__(self, instance_id):
        self.instance_id = instance_id
        self.message = _('No backup instances match: %s') % instance_id


class RepositoryNameExistsError(ConfigureBackupError):
    """
    This exception is raised during the configuration process when the repository
    name already exists on the destination server.
    """

    def __init__(self, name):
        self.name = name
        self.message = _('Destination `%s` already exists.') % name


class DuplicateSettingsError(ConfigureBackupError):
    """
    This exception is raised when trying to configure a new backup instance with similar settings to an existing one.
    """

    def __init__(self, other_instance):
        self.other = other_instance
        self.message = _('These settings conflict with an existing backup and therefore cannot be created.')
        self.detail = _(
            "It is not possible to create two backups with the same destination settings. These will conflict during backup. Be sure to define a different destination for this backup."
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
            _("your file specification [%s] doesn't match any of the base directories of your system") % file_spec
        )


class RdiffBackupException(BackupError):
    """
    Raise whenever rdiff-backup raise an exception.
    """

    def __init__(self, msg) -> None:
        self.message = _('process terminated with an exception. Check logs for more details: %s') % msg


class RdiffBackupExitError(BackupError):
    """
    This exception is raised when rdiff-backup process return an error.
    """

    message = _('process returned a non-zero exit status. Check logs for more details')


class NoPatternsError(BackupError):
    """
    This exception is raised when a backup is started without any valid patterns.
    """

    message = _('No files included in backup. Check configuration.')


class NotRunningError(Exception):
    """
    Raised when trying to stop a backup when it's not running.
    """

    message = _("cannot stop process when it's not running.")


class RunningError(BackupError):
    """
    Raised when a backup is already running.
    """

    message = _("cannot start process when it's already running.")


class NotConfiguredError(BackupError):
    """
    Raised when the backup is not configured
    """

    message = _('not configured, use `minarca configure` to configure remote host')


class NotScheduleError(BackupError):
    """
    Raised when it's not time to run a backup.
    """

    message = _("backup not yet scheduled to run. You may force execution using `--force`")


class HttpConnectionError(ConfigureBackupError):
    """
    Raised if the HTTP connection failed.
    """

    def __init__(self, url):
        self.message = _('Cannot establish connection to remote server.')
        self.detail = (
            _(
                "Your computer cannot establish a connection to the remote server. Make sure your Internet connection is working and that the following URL is accessible with a Web browser: %s"
            )
            % url
        )


class HttpInvalidUrlError(ConfigureBackupError):
    """
    Raised when the URL is not valid.
    """

    def __init__(self, url):
        self.message = _('Invalid remote server URL!')
        self.detail = _(
            "The remote server URL you entered for the connection is not valid. Check that you have entered the correct value. The URL must begin with `http://` or `https://` followed by a domain name."
        )


class HttpAuthenticationError(ConfigureBackupError):
    """
    Raised for HTTP status code 401 or 403.
    """

    def __init__(self, server_message=None):
        self.server_message = server_message
        self.message = _('Invalid username or password')
        self.detail = _(
            "The username or password you entered to connect to the remote server is not valid. If you have enabled multi-factor authentication, you need to use an access token."
        )

    def __str__(self):
        # Print original error in logs.
        return self.message + " " + str(self.server_message)


class HttpServerError(ConfigureBackupError):
    """
    Raised for HTTP status code 5xx.
    """

    def __init__(self, server_error) -> None:
        self.message = _('The remote server returned an error. You may try again later.')
        self.detail = str(server_error)


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
        'The connection to the remote server failed because our identity was refused. The problem may lie with the remote server. If the problem persists, contact your system administrator to check your SSH identity.'
    )

    @staticmethod
    def _matches(line):
        return 'Permission denied (publickey)' in line


class UnknownHostKeyError(BackupError):
    """
    Raised by SSH when remote server is unknown.
    """

    message = _(
        "The connection to the remote server cannot be established securely because the server's identity has changed. If the problem persists, contact your system administrator to verify the server's identity."
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

    message = _('Backup failed due to disk being full. Please clear space on the disk to proceed with the backup.')

    @staticmethod
    def _matches(line):
        return 'OSError: [Errno 28] No space left on device' in line


class UnknownHostException(BackupError):
    """
    Raised by rdiff-backup when remote host name could not be resolved.
    """

    message = _(
        'The connection to the remote server has failed due to an unresolvable host name. Please check your network connection and ensure that the host name is still valid. If the problem persists, contact your system administrator to check the host name.'
    )

    @staticmethod
    def _matches(line):
        return 'ssh: Could not resolve hostname' in line


class UnsuportedVersionError(BackupError):
    """
    Raised by rdiff-backup when remote server is not compatible with our client version.
    """

    message = _(
        'The connection to the remote server has failed due to an unsupported version of the Minarca agent on the remote server. Consider updating your agent or server.'
    )

    @staticmethod
    def _matches(line):
        return 'ERROR unsupported version:' in line or 'ERROR: unsupported version:' in line


class RestoreFileNotFound(BackupError):
    message = _('The path you are trying to restore from backup does not exist.')

    @staticmethod
    def _matches(line):
        return "couldn't be identified as being within an existing backup repository" in line


class RepositoryLocked(BackupError):
    message = _('Another backup session is currently in progress on the remote server.')

    @staticmethod
    def _matches(line):
        return "Fatal Error: It appears that a previous rdiff-backup session" in line


class UnrecognizedArguments(BackupError):
    message = _('An internal error was raised by an unknown operation sent to the background process.')

    @staticmethod
    def _matches(line):
        return "error: unrecognized arguments: " in line


class LocalDestinationNotEmptyError(ConfigureBackupError):
    """
    Raised when the location defined by the user for a local backup is not empty and doesn't contains rdiff-backup-data.
    """

    message = _('Backup Destination Occupied')
    detail = _(
        'Unable to proceed with the selected destination as it contains existing data. If you intend to use this location, kindly empty the directory of any files and folders.'
    )


class InitDestinationError(ConfigureBackupError):
    """
    Raised when a problem occured during the initialisation process of a local destination. e.g.: fail to create file or folder.
    """

    message = _("Destination Not Suitable")
    detail = _(
        'Unable to proceed with the selected destination as it cannot be initialized. Make sure the external device is connected and operational.'
    )


class LocalDestinationNotFound(RuntimeBackupError):
    """
    Raised whenever we are looking for a local destination, but external disk is not found or nout mounted.
    """

    message = _(
        "Backup Destination Not Found. Please ensure that your external disk or network share is properly connected and accessible."
    )


class DiskDisconnectedError(BackupError):
    message = _(
        "Backup unsuccessful due to a copy operation encountering an issue, potentially because the device is disconnected. Ensure your device is properly connected."
    )

    @staticmethod
    def _matches(line):
        return 'OSError: [Errno 5] Input/output error' in line


class RemoteRepositoryNotFound(BackupError):
    """
    This exception is raised when the repository is expected to exists but cannot be found.
    """

    message = _('Repository cannot be found on remote server')

    def __init__(self, name=None):
        self.name = name
        if name:
            self.message = _('Repository `%s` cannot be found on remote server') % name

    @staticmethod
    def _matches(line):
        # ERROR:   Path 'pop-os' couldn't be identified as being within an existing
        #          backup repository
        return "couldn't be identified as being within an existing" in line


class InvalidRepositoryName(ConfigureBackupError):
    """
    This exception is raised when repository name is not valid.
    """

    def __init__(self, name):
        self.name = name
        self.message = _("Repository name must contain only letters, numbers, dashes (-), and dots (.)")
