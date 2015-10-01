/*
 * Copyright (C) 2015, Patrik Dufresne Service Logiciel. inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca;

import static com.patrikdufresne.minarca.Localized._;

import org.eclipse.core.runtime.IStatus;
import org.eclipse.core.runtime.Status;
import org.eclipse.jface.dialogs.IDialogConstants;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.util.ILogger;
import org.eclipse.jface.util.Policy;
import org.eclipse.jface.window.WindowManager;
import org.eclipse.swt.widgets.Display;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.API;
import com.patrikdufresne.minarca.core.APIException;
import com.patrikdufresne.minarca.core.APIException.MissConfiguredException;
import com.patrikdufresne.minarca.core.APIException.NotConfiguredException;
import com.patrikdufresne.minarca.ui.DetailMessageDialog;
import com.patrikdufresne.minarca.ui.Images;
import com.patrikdufresne.minarca.ui.SettingsDialog;
import com.patrikdufresne.minarca.ui.SetupDialog;

/**
 * This class is the main entry point to the software.
 * 
 * @author Patrik Dufresne
 * 
 */
public class Main {

    static final transient Logger LOGGER = LoggerFactory.getLogger(Main.class);

    /**
     * Return the current version.
     * 
     * @return
     */
    public static String getCurrentVersion() {
        // Get the version from the package manifest
        String version = Main.class.getPackage().getImplementationVersion();
        if (version == null) {
            return "DEV";
        }
        return version;
    }

    /**
     * This function is the main entry point.
     * 
     * @param args
     */
    public static void main(String[] args) {
        // Process the arguments.
        boolean backup = false;
        for (String arg : args) {
            // TODO add arguments to link, unlink computer.
            if (arg.equals("--backup") || arg.equals("-b")) {
                backup = true;
            } else if (arg.equals("--version") || arg.equals("-v")) {
                printVersion();
                System.exit(0);
            } else if (arg.equals("--help") || arg.equals("-h")) {
                printUsage();
                System.exit(0);
            } else {
                System.err.println("Unknown options: " + arg);
            }
        }

        // Start minarca.
        Main main = new Main();
        if (backup) {
            main.backup();
        } else {
            main.startui(args);
        }

    }

    /**
     * Called when minarca executable is start with <code>--help</code> or <code>-h</code> arguments.
     */
    private static void printUsage() {
        System.out.println("Usage:");
        System.out.println("    minarca --backup");
        System.out.println("    minarca --help");
        System.out.println("    minarca --version");
        System.out.println("");
        System.out.println("    --backup  used to run the minarca backup.");
        System.out.println("    --help    display this help message.");
        System.out.println("    --version show minarca version.");
    }

    /**
     * Called when minarca executable is start with <code>--version</code> or <code>-v</code> arguments.
     */
    private static void printVersion() {
        System.out.println("Minarca version " + getCurrentVersion());
        System.out.println("Copyright (C) 2015 Patrik Dufresne Service Logiciel Inc.");
    }

    /**
     * This if the main function being called when minarca application is called with --backup or -b arguments.
     */
    private void backup() {

        LOGGER.info("starting backup");

        // Check if current OS and running environment is valid.
        try {
            API.checkEnv();
        } catch (APIException e) {
            LOGGER.info("invalid env", e);
            System.err.println(e.getMessage());
            System.exit(1);
        }

        // Check if minarca is properly configure (from our point of view).
        try {
            API.instance().checkConfig();
        } catch (APIException e) {
            // Show error message (usually localized).
            LOGGER.info("invalid config", e);
            System.err.println(e.getMessage());
            System.exit(2);
        }

        // Run the backup.
        try {
            API.instance().backup();
            LOGGER.info("backup SUCCESS");
        } catch (APIException e) {
            LOGGER.info("backup FAILED", e);
            System.exit(3);
        }

    }

    /**
     * This function is updating the JFace Policy error handler.
     */
    protected static void updateJFacePolicy() {
        Policy.setLog(new ILogger() {

            @Override
            public void log(IStatus status) {
                switch (status.getSeverity()) {
                case IStatus.OK:
                case IStatus.INFO:
                    if (status.getException() == null) {
                        LOGGER.info(status.getMessage());
                    } else {
                        LOGGER.info(status.getMessage(), status.getException());
                    }
                    break;
                case IStatus.WARNING:
                    if (status.getException() == null) {
                        LOGGER.warn(status.getMessage());
                    } else {
                        LOGGER.warn(status.getMessage(), status.getException());
                    }
                    break;
                case IStatus.ERROR:
                    if (status.getException() == null) {
                        LOGGER.error(status.getMessage());
                    } else {
                        LOGGER.error(status.getMessage(), status.getException());
                    }
                    break;
                }
                System.err.println(status.getMessage());
                if (status.getException() != null) {
                    status.getException().printStackTrace(System.err);
                }
            }
        });
    }

    /**
     * This function start the application.
     * 
     * @param args
     */
    private void startui(String[] args) {

        LOGGER.info("starting ui");

        Display.setAppName(_("Minarca"));
        Display.setAppVersion(getCurrentVersion());
        final Display display = new Display();

        // Sets default windows images
        Images.setDefaultImages();

        // Update logger
        updateJFacePolicy();

        // Check running environment.
        try {
            API.checkEnv();
        } catch (APIException e) {
            MessageDialog.openError(null, Display.getAppName(), e.getMessage());
            System.exit(1);
        }

        WindowManager winManager = null;
        try {
            // Check configuration or re-configured
            if (!configure()) {
                return;
            }

            winManager = new WindowManager();
            // Open Main Window
            SettingsDialog win = new SettingsDialog();
            win.setWindowManager(winManager);
            win.open();
            // Event loop
            while (winManager.getWindowCount() > 0) {
                try {
                    if (!display.readAndDispatch()) display.sleep();
                } catch (RuntimeException e) {
                    Policy.getStatusHandler().show(new Status(IStatus.ERROR, Display.getAppName(), e.getMessage(), e), null);
                }
            }
        } catch (Exception e) {
            LOGGER.error("unknown error", e);
            MessageDialog.openWarning(null, Display.getAppName(), e.getMessage());
        } finally {
            if (winManager != null) {
                winManager.close();
            }
            display.dispose();
            LOGGER.info("closing");
        }

    }

    /**
     * Check if the application is configured. If not show a setup dialog. If miss configured try to repair.
     * 
     * @return True if configured or miss configured. False if not configured and user cancel configuration.
     */
    private boolean configure() {
        // Check if configured.
        try {
            LOGGER.debug("checking minarca configuration");
            API.instance().checkConfig();
            API.instance().getSchedulerTask();
            LOGGER.debug("configuration is OK");
        } catch (NotConfiguredException e) {
            // If not configured, show wizard.
            LOGGER.debug("not configured -- show setup dialog");
            if (!SetupDialog.open(null)) {
                // If user cancel, lose application.
                return false;
            }
        } catch (MissConfiguredException e) {
            // The configuration is broken. Ask use if we can fix it.
            LOGGER.debug("miss-configured -- ask to repair", e);
            if (DetailMessageDialog.openYesNoQuestion(
                    null,
                    Display.getAppName(),
                    _("Do you want to restore default configuration ?"),
                    _("Your Minarca installation seams broken. "
                            + "If you answer Yes, all your personal configuration will be lost. "
                            + "If you answer no, this application may misbehave."),
                    null).getReturnCode() == IDialogConstants.YES_ID) {
                try {
                    LOGGER.debug("repair configuration");
                    API.instance().defaultConfig(false);
                } catch (APIException e1) {
                    LOGGER.warn("fail to repair configuration", e1);
                    DetailMessageDialog.openWarning(
                            null,
                            Display.getAppName(),
                            _("Can't repair Minarca's configuration!"),
                            _("This application may misbehave. If the problem persist, you may try to reinstall Minarca."),
                            e1);
                }
            } else {
                return true;
            }
        } catch (APIException e) {
            return false;
        }
        return true;
    }
}
