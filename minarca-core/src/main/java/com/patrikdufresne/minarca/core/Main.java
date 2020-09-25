/*
 * Copyright (C) 2020, IKUS Software inc. All rights reserved.
 * IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core;

import static com.patrikdufresne.minarca.core.Localized._;

import java.io.Console;
import java.io.IOException;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.SystemUtils;
import org.apache.commons.lang3.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;

import com.patrikdufresne.minarca.core.internal.Compat;
import com.patrikdufresne.minarca.core.internal.ProcessUtils;
import com.patrikdufresne.minarca.core.internal.ProcessUtils.NoSuchProcess;
import com.patrikdufresne.minarca.core.internal.ProcessUtils.ProcessInfo;
import com.patrikdufresne.minarca.core.internal.Scheduler;

/**
 * This class is the main entry point to the software.
 * 
 * @author Patrik Dufresne
 * 
 */
public class Main {

    static final transient Logger LOGGER = LoggerFactory.getLogger(Main.class);

    /**
     * This if the main function being called when minarca application is called with --backup or -b arguments.
     */
    private static void backup(boolean force) {
        Compat.logValues();

        try {
            try {
                ProcessInfo p = ProcessUtils.getPid(Compat.PID_FILE_BACKUP, Compat.MINARCA_EXE);
                if (p.pid != ProcessUtils.pid()) {
                    LOGGER.info("minarca backup is already running as pid " + p.pid);
                    System.err.println("minarca backup is already running as pid " + p.pid);
                    System.exit(1);
                    return;
                }
            } catch (NoSuchProcess e) {
                // Continue
            }
            ProcessUtils.writePidFile(Compat.PID_FILE_BACKUP);
        } catch (IOException e) {
            System.err.println("fail to verify if another process is running: " + e.getMessage());
            System.exit(1);
            return;
        }

        LOGGER.info("starting backup");
        // Run the backup.
        try {
            API.instance().backup(force);
        } catch (Exception e) {
            System.err.println("error during backup: " + e.getMessage());
            System.exit(2);
            return;
        }

    }

    /**
     * Called for action "link".
     * 
     * @param remoteurl
     * @param username
     * @param password
     * @param repositoryname
     */
    private static void link(String remoteurl, String username, String password, String repositoryname, boolean force) {
        Validate.notBlank(remoteurl);
        Validate.notBlank(username);
        Validate.notBlank(repositoryname);
        Validate.notBlank(password);

        // Connect to web server
        Client client;
        try {
            client = API.instance().connect(remoteurl, username, password);
        } catch (APIException e) {
            System.err.println(e.getMessage());
            System.exit(1);
            return;
        }
        // Link
        try {
            API.instance().link(repositoryname, client, force);
            System.out.println("link sucessful");
        } catch (APIException e) {
            System.err.println(e.getMessage());
            System.exit(1);
            return;
        } catch (Exception e) {
            System.err
                    .println(_("Unexpected error happened during the linking process with the server. Verify connectivity with the server and try again later."));
            System.exit(1);
            return;
        }

    }

    /**
     * This function is the main entry point.
     * 
     * @param args
     */
    public static void main(final String[] args) {
        // Define PID for logging
        MDC.put("process_id", String.valueOf(ProcessUtils.pid()));

        // Process the arguments.
        String action = args.length > 0 ? args[0] : "";
        switch (action) {
        case "backup":
        case "--backup":
            boolean force = parseBoolArgument(args, "--force", "-f");
            checkEnv();
            printContinueLogging();
            backup(force);
            break;
        case "crontab":
        case "scheduler":
            checkEnv();
            createScheduledTask();
            break;
        case "link":
            force = parseBoolArgument(args, "--force", "-f");
            String remoteurl = parseArgument(args, true, null, "--remoteurl", "-r");
            String username = parseArgument(args, true, null, "--username", "-u");
            String repositoryname = parseArgument(args, true, null, "--name", "-n");
            String password = parseArgument(args, false, null, "--password", "-p");
            if (password == null) {
                password = promptPassword();
            }
            checkEnv();
            link(remoteurl, username, password, repositoryname, force);
            break;
        case "unlink":
            checkEnv();
            unlink();
            break;
        case "include":
        case "exclude":
            checkEnv();
            boolean include = action.equals("include");
            List<GlobPattern> list = API.instance().config().getGlobPatterns();
            for (int i = 1; i < args.length; i++) {
                if (include) {
                    list.add(new GlobPattern(true, args[i]));
                } else {
                    list.remove(new GlobPattern(true, args[i]));
                    list.add(new GlobPattern(false, args[i]));
                }
            }
            // Save the patterns.
            try {
                API.instance().config().setGlobPatterns(list, true);
            } catch (APIException e) {
                System.err.println(e.getMessage());
                System.exit(1);
            }
            break;
        case "patterns":
            checkEnv();
            boolean clear = parseBoolArgument(args, "--clear");
            if (clear) {
                try {
                    API.instance().config().setGlobPatterns(Collections.emptyList(), true);
                } catch (APIException e) {
                    System.err.println(e.getMessage());
                    System.exit(1);
                }
            }
            printPatterns();
            break;
        case "stop":
        case "--stop":
            checkEnv();
            force = parseBoolArgument(args, "--force", "-f");
            stopBackup(force);
            break;
        case "status":
        case "--status":
            checkEnv();
            printStatus();
            break;
        case "--version":
        case "-v":
            printVersion();
            break;
        case "--help":
        case "-h":
            printVersion();
            printUsage();
            break;
        default:
            System.err.println("Unknown action: " + action);
            printUsage();
            System.exit(1);
            break;
        }

    }

    /**
     * Create a scheduled task.
     */
    private static void createScheduledTask() {
        try {
            Scheduler.instance().create();
        } catch (APIException e) {
            System.err.println(e.getMessage());
            System.exit(1);
            return;
        }
    }

    /**
     * Parse the arguments list.
     * 
     * @param args
     *            list of arguments
     * @param required
     *            True if the argument is required.
     * @param defaultValue
     *            Default value
     * @param names
     *            Name of the arguments.
     * @return The arguments value.
     */
    protected static String parseArgument(String[] args, boolean required, String defaultValue, String... names) {
        for (int i = 0; i < args.length - 1; i++) {
            if (Arrays.asList(names).contains(args[i])) {
                i++;
                return args[i];
            }
        }
        // If the arguments is required, validate and exit.
        if (required) {
            System.err.println(StringUtils.join(names, ", ") + " " + _("arguments is required"));
            System.exit(1);
        }
        return defaultValue;
    }

    /**
     * Used to parse arguments
     * 
     * @param args
     *            list of args
     * @param names
     *            the name of the arguments to be parsed e.g.: "--force", "-f"
     * @return True if the argument exists.
     */
    private static boolean parseBoolArgument(String[] args, String... names) {
        for (int i = 0; i < args.length; i++) {
            if (Arrays.asList(names).contains(args[i])) {
                return true;
            }
        }
        return false;
    }

    /**
     * Print a message as a hint to the user to tell him we are logging to a file.
     */
    private static void printContinueLogging() {
        // Do not print anything to stdout when running in cron.
        if (System.console() == null) {
            return;
        }
        System.out.println(_("Continue logging to ") + Compat.LOG_FOLDER + "/minarca.log");
    }

    /**
     * Print list of include exclude patterns.
     */
    private static void printPatterns() {
        for (GlobPattern p : API.instance().config().getGlobPatterns()) {
            System.out.println((p.isInclude() ? "include " : "exclude ") + p.toString());
        }
    }

    /**
     * Print minarca client status.
     */
    private static void printStatus() {
        // Last Backup
        System.out.println(_("Last backup: ") + API.instance().status().getLocalized());
        // Connectivity status
        String status;
        if (API.instance().config().getConfigured()) {
            try {
                API.instance().testServer();
                status = _("Connected");
            } catch (Exception e) {
                status = _("Not connected") + e.getMessage();
            }
        } else {
            status = _("Not configured");
        }
        System.out.println(_("Connectivity status: ") + status);
    }

    /**
     * Called when minarca executable is start with <code>--help</code> or <code>-h</code> arguments.
     */
    private static void printUsage() {
        System.out.println("");
        System.out.println("Usage:");
        System.out.println("    minarca backup [--force]");
        System.out.println("    minarca stop [--force]");
        System.out.println("    minarca status");
        System.out.println("    minarca link --remoteurl URL --username USERNAME [--password PASSWORD] --name REPOSITORYNAME");
        System.out.println("    minarca unlink");
        System.out.println("    minarca include <FILES>");
        System.out.println("    minarca exclude <FILES>");
        System.out.println("    minarca patterns");
        System.out.println("    minarca --help");
        System.out.println("    minarca --version");
        System.out.println("");
        System.out.println("    --help           display this help message.");
        System.out.println("    --version        show minarca version.");
        System.out.println("");
        System.out.println("backup");
        System.out.println("    Used to start the minarca backup.");
        System.out.println("    --force | -f     force execution of a backup even if it's not time to run.");
        System.out.println("");
        System.out.println("stop: stop the backup");
        System.out.println("    --force | -f     doesn't fail if the backup is not running.");
        System.out.println("");
        System.out.println("status: return the current minarca status");
        System.out.println("    no options");
        System.out.println("");
        System.out.println("link: Link this minarca client with a minarca server.");
        System.out.println("    --remoteurl | -r URL to the remove mianrca server. e.g.: http://example.com:8080/");
        System.out.println("    --username | -u  The user name to be used for authentication");
        System.out.println("    --password | -p  The password to use for authentication. Will prompt if not provided.");
        System.out.println("    --name | -n      The repository name to be used.");
        System.out.println("    --force | -f     Force the link even if the repository name already exists.");
        System.out.println("");
        System.out.println("unlink: unlink this minarca client from server");
        System.out.println("    no options");
        System.out.println("");
        System.out.println("include/exclude: Add or remove files to be backuped");
        System.out.println("    FILES            List of files pattern to be include or exclude. ? and * might be used as wildcard operators");
        System.out.println("");
        System.out.println("patterns: List the includes / excludes patterns");
        System.out.println("    no options");

    }

    /**
     * Called when minarca executable is start with <code>--version</code> or <code>-v</code> arguments.
     */
    private static void printVersion() {
        System.out.println("Minarca version " + API.getCurrentVersion());
        System.out.println(API.getCopyrightText());
    }

    /**
     * Prompt user for password.
     * 
     * @return
     */
    private static String promptPassword() {
        Console console = System.console();
        if (console == null) {
            System.out.println("Failed get console instance");
            System.exit(1);
        }
        char[] passwordArray = console.readPassword("password: ");
        return new String(passwordArray);
    }

    /**
     * Called to stop a running backup. Called force with true to swallow exception.
     * 
     * @param force
     *            True to ignore error.
     */
    private static void stopBackup(boolean force) {

        try {
            try {
                ProcessInfo p = ProcessUtils.getPid(Compat.PID_FILE_BACKUP, Compat.MINARCA_EXE);
                ProcessUtils.kill(p.pid);
                return;
            } catch (NoSuchProcess e) {
                LOGGER.info("minarca backup is not running");
                System.err.println("minarca backup is not running");
                if (!force) {
                    System.exit(1);
                }
            }
        } catch (IOException e) {
            System.err.println("fail to verify if another minarca process is running: " + e.getMessage());
            System.exit(1);
            return;
        }

    }

    /**
     * Unlink
     */
    private static void unlink() {
        try {
            API.instance().unlink();
            System.out.println("unlink sucessful");
        } catch (APIException e) {
            System.err.println(e.getMessage());
            System.exit(1);
            return;
        }
    }

    private static void checkEnv() {
        // Check if current OS and running environment is valid.
        try {
            API.checkEnv();
        } catch (APIException e) {
            LOGGER.info("{} {} {}", SystemUtils.OS_NAME, SystemUtils.OS_VERSION, SystemUtils.OS_ARCH);
            LOGGER.info("{} (build {}, {})", SystemUtils.JAVA_VM_INFO, SystemUtils.JAVA_VM_VERSION, SystemUtils.JAVA_VM_INFO);
            LOGGER.info("invalid environment", e);
            System.err.println(e.getMessage());
            System.exit(1);
        }
    }

}
