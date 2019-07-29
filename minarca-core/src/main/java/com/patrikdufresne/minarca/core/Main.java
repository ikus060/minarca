/*
 * Copyright (C) 2018, Patrik Dufresne Service Logiciel. inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core;

import java.io.IOException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;

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

        // Check if backup should be stop.
        if (stop) {
            // single.stop();
            return;
        }

        try {

            if (backup) {
                try {
                    ProcessInfo p = ProcessUtils.getPid(Compat.PID_FILE_BACKUP, MinarcaExecutable.MINARCA_EXE);
                    LOGGER.info("minarca backup is already running as pid " + p.pid);
                    System.err.println("minarca backup is already running as pid " + p.pid);
                    System.exit(1);
                    return;
                } catch (NoSuchProcess e) {
                    // Continue
                }
                ProcessUtils.writePidFile(Compat.PID_FILE_BACKUP);
                new Main().backup(force);
            }
        } catch (IOException e) {
            // TODO
        }

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
        System.out.println("Minarca version " + API.getCurrentVersion());
        System.out.println(API.getCopyrightText());
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

}
