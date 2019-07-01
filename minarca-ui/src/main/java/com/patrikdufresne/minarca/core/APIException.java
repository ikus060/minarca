/*
 * Copyright (C) 2018, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core;

import static com.patrikdufresne.minarca.Localized._;

import java.io.File;

public class APIException extends Exception {

    /**
     * Raised when the client fail to authenticate with the server. (Map to HTTP status code 401)
     * 
     * @author Patrik Dufresne
     * 
     */
    public static class AuthenticationException extends APIException {

        public AuthenticationException(Exception cause) {
            super(_("Wrong username or password."), cause);
        }

    }

    /**
     * Raised when we failed to establish connectivity with the remote url or remote host.
     * 
     * @author Patrik Dufresne
     * 
     */
    public static class ConnectivityException extends APIException {

        public ConnectivityException(Exception cause) {
            super(_("Failed to establish connectivity with the server. Verfy if the URL provided is valid and responding."), cause);
        }

    }

    /**
     * Raised when the client failed to exchange the public key with remote server.
     * 
     * @author Patrik Dufresne
     * 
     */
    public static class ExchangeSshKeyException extends APIException {

        public ExchangeSshKeyException(Exception cause) {
            super(_("Fail to send SSH key to Minarca."), cause);
        }

    }

    /**
     * Raised when the creation of public private key failed.
     * 
     * @author Patrik Dufresne
     * 
     */
    public static class GenerateKeyException extends APIException {

        public GenerateKeyException(Exception cause) {
            super(_("Fail to generate the security keys."), cause);
        }

    }

    /**
     * Raised when the identify file is invalid or missing.
     * 
     * @author Patrik Dufresne
     * 
     */
    public static class IdentityMissingException extends APIException {

        public IdentityMissingException(File file) {
            super(_("identity file %s is missing", file.toString()));
        }
    }

    /**
     * Raise when the first backup (during link) failed to run.
     * 
     * @author Patrik Dufresne
     * 
     */
    public static class InitialBackupFailedException extends APIException {

        public InitialBackupFailedException(Exception cause) {
            super(_("Initial backup did not complete successfully."), cause);
        }

    }

    /**
     * Raised when the initial backup never ran.
     * 
     * @author Patrik Dufresne
     * 
     */
    public static class InitialBackupHasNotRunException extends APIException {

        public InitialBackupHasNotRunException(Exception cause) {
            super(_("Initial backup didn't run."), cause);
        }

    }

    /**
     * Raise when the first backup is running for too long.
     * 
     * @author Patrik Dufresne
     * 
     */
    public static class InitialBackupRunningException extends APIException {

        public InitialBackupRunningException(Exception cause) {
            super(_("Initial backup is still running."), cause);
        }

    }

    /**
     * Raised when link with minarca failed.
     * 
     * @author Patrik Dufresne
     * 
     */
    public static class LinkComputerException extends APIException {

        public LinkComputerException(Exception cause) {
            super(_("Fail to link computer."), cause);
        }

    }

    /**
     * Minarca executable cannot be found.
     * 
     * @author Patrik Dufresne
     * 
     */
    public static class MinarcaMissingException extends APIException {

        // TODO Add mos arguments: fingerprint, hostname
        public MinarcaMissingException() {
            super(_("minarca is missing"));
        }

    }

    /**
     * Thrown when the application is miss configured
     * 
     * @author Patrik Dufresne
     * 
     */
    public static class MissConfiguredException extends APIException {
        public MissConfiguredException(String message) {
            super(message);
        }

        public MissConfiguredException(String message, Exception cause) {
            super(message, cause);
        }
    }

    /**
     * Thrown when the application is not configured.
     * 
     * @author Patrik Dufresne
     * 
     */
    public static class NotConfiguredException extends APIException {
        public NotConfiguredException(String message) {
            super(message);
        }
    }

    /**
     * Raised when trying to link a computer with a name already in use in minarca.
     * 
     * @author Patrik Dufresne
     * 
     */
    public static class RepositoryNameAlreadyInUseException extends APIException {
        public RepositoryNameAlreadyInUseException(String name) {
            super(_("Repository name {0} already in use", name));
        }
    }

    /**
     * Raised when the task is not found.
     * 
     * @author Patrik Dufresne
     * 
     */
    public static class ScheduleNotFoundException extends APIException {

        public ScheduleNotFoundException() {
            super(_("Scheduled task not found"));
        }

    }

    /**
     * Raised when ssh is missing.
     * 
     * @author Patrik Dufresne
     * 
     */
    public static class SshMissingException extends APIException {

        public SshMissingException() {
            super(_("ssh is missing"));
        }

    }

    public static class UnsufficientPermissons extends APIException {

        public UnsufficientPermissons() {
            super(_("You don't have sufficient permissions to execute this application!"));
        }

    }

    /**
     * Raised when the running OS is not supported.
     */
    public static class UnsupportedOS extends APIException {

        public UnsupportedOS() {
            super(_("Minarca doesn't support your operating system. This application will close."));
        }

    }

    public static class UntrustedHostKey extends APIException {

        // TODO Add mos arguments: fingerprint, hostname
        public UntrustedHostKey() {
            super(_("Remote SSH host is not trusted"));
        }

    }

    private static final long serialVersionUID = 1L;

    public APIException(Exception cause) {
        super(cause);
    }

    public APIException(String message) {
        super(message);
    }

    public APIException(String message, Exception e) {
        super(message, e);
    }

}
