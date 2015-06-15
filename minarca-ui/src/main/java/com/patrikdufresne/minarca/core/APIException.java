/*
 * Copyright (c) 2014, Patrik Dufresne Service Logiciel. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core;

import static com.patrikdufresne.minarca.Localized._;

public class APIException extends Exception {

    private static final long serialVersionUID = 1L;

    /**
     * Exception used to represent an application error. Message return in alert-danger.
     * 
     * @author Patrik Dufresne
     * 
     */
    public static class ApplicationException extends APIException {
        public ApplicationException(String message) {
            super(message);
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
     * Raised when plink.exe is missing.
     * 
     * @author Patrik Dufresne
     * 
     */
    public static class PlinkMissingException extends APIException {

        public PlinkMissingException() {
            super("plink is missing");
        }

    }

    public static class UntrustedHostKey extends APIException {

        // TODO Add mos arguments: fingerprint, hostname
        public UntrustedHostKey() {
            super("remote SSH host is not trusted");
        }

    }

    /**
     * Raised when the running OS is not supported.
     */
    public static class UnsupportedOS extends APIException {

        public UnsupportedOS() {
            super(_("Minarca doesn't support you OS. This application will close."));
        }

    }

    public static class UnsufficientPermissons extends APIException {

        public UnsufficientPermissons() {
            super(_("You don't have sufficient permissions to execute this application!"));
        }

    }

    public APIException(String message) {
        super(message);
    }

    public APIException(Exception cause) {
        super(cause);
    }

    public APIException(String message, Exception e) {
        super(message, e);
    }

}
