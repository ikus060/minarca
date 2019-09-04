/*
 * Copyright (C) 2018, Patrik Dufresne Service Logiciel. inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.ui;

import static com.patrikdufresne.minarca.ui.Localized._;

import java.io.IOException;

import org.apache.commons.lang3.SystemUtils;
import org.eclipse.core.runtime.IStatus;
import org.eclipse.core.runtime.Status;
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
import com.patrikdufresne.minarca.core.internal.Compat;
import com.patrikdufresne.minarca.core.internal.MinarcaExecutable;
import com.patrikdufresne.minarca.core.internal.ProcessUtils;
import com.patrikdufresne.minarca.core.internal.ProcessUtils.NoSuchProcess;
import com.patrikdufresne.minarca.core.internal.ProcessUtils.ProcessInfo;

/**
 * This class is the main entry point to the software.
 * 
 * @author Patrik Dufresne
 * 
 */
public class Main {

    static final transient Logger LOGGER = LoggerFactory.getLogger(Main.class);

    /**
     * This function is the main entry point.
     * 
     * @param args
     */
    public static void main(final String[] args) {
        // Define PID for logging
        MDC.put("process_id", String.valueOf(ProcessUtils.pid()));

        // Process the arguments.
        for (String arg : args) {
            // TODO add arguments to link, unlink computer.
            if (arg.equals("--version") || arg.equals("-v")) {
                System.out.println("Minarca UI version " + API.getCurrentVersion());
                System.out.println(API.getCopyrightText());
                System.exit(0);
            } else if (arg.equals("--help") || arg.equals("-h")) {
                System.out.println("Minarca UI Usage:");
                System.out.println("    minarca-ui --help");
                System.out.println("    minarca-ui --version");
                System.exit(0);
            } else {
                System.err.println("Unknown options: " + arg);
            }
        }

        // Start the UI if not already running.
        try {

            try {
                ProcessInfo p = ProcessUtils.getPid(Compat.PID_FILE_GUI, Compat.MINARCAUI_EXE);
                LOGGER.info("minarca ui is already running as pid " + p.pid);
                System.err.println("minarca ui is already running as pid " + p.pid);
                System.exit(0);
                return;
            } catch (NoSuchProcess e) {
                // Pass
                ProcessUtils.writePidFile(Compat.PID_FILE_GUI);
                new Main().startui();
            }
        } catch (IOException e) {
            e.printStackTrace();
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
    private void startui() {
        Compat.logValues();
        LOGGER.info("starting minarca ui version [{}]", API.getCurrentVersion());

        Display.setAppName(_("Minarca"));
        Display.setAppVersion(API.getCurrentVersion());
        final Display display = new Display();

        // Sets default windows images
        Images.setDefaultImages();

        // Update logger
        updateJFacePolicy();

        // Check running environment.
        try {
            API.checkEnv();
        } catch (APIException e) {
            LOGGER.info("{} {} {}", SystemUtils.OS_NAME, SystemUtils.OS_VERSION, SystemUtils.OS_ARCH);
            LOGGER.info("{} (build {}, {})", SystemUtils.JAVA_VM_INFO, SystemUtils.JAVA_VM_VERSION, SystemUtils.JAVA_VM_INFO);
            LOGGER.info("invalid environment", e);
            MessageDialog.openError(null, Display.getAppName(), e.getMessage());
            System.exit(1);
        }

        WindowManager winManager = null;
        try {
            // If not configured open dialog to configure minarca.
            if (!API.instance().config().getConfigured()) {
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
