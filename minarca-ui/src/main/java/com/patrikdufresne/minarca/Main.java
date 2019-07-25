/*
 * Copyright (C) 2018, Patrik Dufresne Service Logiciel. inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca;

import static com.patrikdufresne.minarca.Localized._;

import java.lang.management.ManagementFactory;
import java.util.Calendar;

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
import org.slf4j.MDC;

import com.patrikdufresne.minarca.core.API;
import com.patrikdufresne.minarca.core.APIException;
import com.patrikdufresne.minarca.core.APIException.MissConfiguredException;
import com.patrikdufresne.minarca.core.APIException.ScheduleNotFoundException;
import com.patrikdufresne.minarca.core.internal.Compat;
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
     * Port to be used to verify single instance of backup.
     */
    static final int SINGLE_INSTANCE_PORT_BACKUP = Integer.getInteger("minarca.singleinstance.backup.port", 52356);

    /**
     * Port to be used to verify single instance of UI.
     */
    static final int SINGLE_INSTANCE_PORT_UI = Integer.getInteger("minarca.singleinstance.backup.port", 60820);

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
     * Return the copyright text to be displayed.
     * 
     * @return
     */
    public static String getCopyrightText() {
        int year = Calendar.getInstance().get(java.util.Calendar.YEAR);
        return _("Copyright © {0,number,#} - Patrik Dufresne Service Logiciel inc.", year);
    }

    /**
     * This function is the main entry point.
     * 
     * @param args
     */
    public static void main(final String[] args) {
        // Define PID for logging
        MDC.put("process_id", getPid());

        // Process the arguments.
        boolean backup = false;
        boolean force = false;
        boolean stop = false;
        for (String arg : args) {
            // TODO add arguments to link, unlink computer.
            if (arg.equals("--backup") || arg.equals("-b")) {
                backup = true;
            } else if (arg.equals("--force") || arg.equals("-f")) {
                force = true;
            } else if (arg.equals("--stop") || arg.equals("-s")) {
                stop = true;
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
        final Thread mainThread = Thread.currentThread();
        final boolean fBackup = backup;
        final boolean fForce = force;
        SingleInstanceManager single = new SingleInstanceManager(
                fBackup ? SINGLE_INSTANCE_PORT_BACKUP : SINGLE_INSTANCE_PORT_UI,
                new SingleInstanceManager.SingleInstanceListener() {
                    @Override
                    public void stopInstance() {
                        LOGGER.info("requested to stop");
                        mainThread.interrupt();
                    }

                    @Override
                    public void newInstanceCreated() {
                        LOGGER.info("new instance created");
                    }
                });

        // Check if backup should be stop.
        if (stop) {
            single.stop();
            return;
        }

        // Check if single instance of application is running.
        single.run(new Runnable() {
            @Override
            public void run() {
                Main main = new Main();
                if (fBackup) {
                    main.backup(fForce);
                } else {
                    main.startui(args);
                }
            }
        });

    }

    /**
     * Return the process Id.
     * 
     * @return
     */
    private static String getPid() {
        // Should return something like pid@hostname
        String value = ManagementFactory.getRuntimeMXBean().getName();
        if (value.contains("@")) {
            return value.split("@")[0];
        }
        return value;
    }

    /**
     * Called when minarca executable is start with <code>--help</code> or <code>-h</code> arguments.
     */
    private static void printUsage() {
        System.out.println("Usage:");
        System.out.println("    minarca --backup [--force] [--stop]");
        System.out.println("    minarca --help");
        System.out.println("    minarca --version");
        System.out.println("");
        System.out.println("    --backup  used to run the minarca backup.");
        System.out.println("    --stop    stop the backup (when used with --backup) or stop the UI.");
        System.out.println("    --force   force execution of a backup.");
        System.out.println("    --help    display this help message.");
        System.out.println("    --version show minarca version.");
    }

    /**
     * Called when minarca executable is start with <code>--version</code> or <code>-v</code> arguments.
     */
    private static void printVersion() {
        System.out.println("Minarca version " + getCurrentVersion());
        System.out.println(getCopyrightText());
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
     * This if the main function being called when minarca application is called with --backup or -b arguments.
     */
    private void backup(boolean force) {
        Compat.logValues();
        LOGGER.info("starting backup");

        // Check if current OS and running environment is valid.
        try {
            API.checkEnv();
        } catch (APIException e) {
            LOGGER.info("invalid env", e);
            System.err.println(e.getMessage());
            System.exit(1);
        }

        // Run the backup.
        try {
            API.instance().backup(false, force);
        } catch (Exception e) {
            System.exit(2);
        }

    }

    /**
     * This function start the application.
     * 
     * @param args
     */
    private void startui(String[] args) {
        Compat.logValues();
        LOGGER.info("starting minarca ui version [{}]", getCurrentVersion());

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
            // If not configured open dialog to configure minarca.
            if (!API.config().getConfigured()) {
                if (!SetupDialog.open(null)) {
                    // If user cancel, close application.
                    return;
                }
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
}
