/*
 * Copyright (C) 2019, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.internal;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.SystemUtils;
import org.apache.commons.lang3.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.APIException;
import com.patrikdufresne.minarca.core.APIException.IdentityMissingException;
import com.patrikdufresne.minarca.core.APIException.SshMissingException;
import com.patrikdufresne.minarca.core.APIException.UntrustedHostKey;
import com.patrikdufresne.minarca.core.GlobPattern;
import com.patrikdufresne.minarca.core.internal.StreamHandler.PromptHandler;

/**
 * Utility class to run rdiffbackup command line.
 * 
 * @author Patrik Dufresne
 * 
 */
public class RdiffBackup {

    private static final transient Logger LOGGER = LoggerFactory.getLogger(RdiffBackup.class);

    /**
     * True to accept any host key.
     */
    private static final String PROPERTY_ACCEPT_HOST_KEY = "minarca.accepthostkey";

    /**
     * Property used to define the location of rdiff-backup.
     */
    private static final String PROPERTY_RDIFF_BACKUP_LOCATION = "rdiffbackup.location";

    /**
     * Property used to define the location of ssh. Mainly used for development.
     */
    private static final String PROPERTY_SSH_LOCATION = "ssh.location";

    /**
     * Executable name to launch rdiff-backup (for current platform)
     */
    private static final String RDIFF_BACKUP;
    /**
     * SSH executable name.
     */
    private static final String SSH;

    static {
        if (SystemUtils.IS_OS_WINDOWS) {
            RDIFF_BACKUP = "rdiff-backup.exe";
            SSH = "ssh.exe";
        } else {
            // Otherwise Linux
            RDIFF_BACKUP = "rdiff-backup";
            SSH = "ssh";
        }
    }

    /**
     * True to accept any host key.
     * 
     * @return
     */
    private static boolean getAcceptHostKey() {
        return Boolean.getBoolean(PROPERTY_ACCEPT_HOST_KEY);
    }

    /**
     * Identify the list of active root (C:, D:, etc.) in the given pattern list.
     * 
     * @param patternsa
     *            list of patterns
     * @return the list of active Root device part of the patterns
     */
    private static List<File> getActiveRoots(List<GlobPattern> patterns) {
        List<File> activeRoots = new ArrayList<File>();
        for (File root : Compat.getRootsPath()) {
            for (GlobPattern p : patterns) {
                if (p.isInRoot(root)) {
                    activeRoots.add(root);
                    break;
                }
            }
        }
        return activeRoots;
    }

    /**
     * Determine the location of rdiff-backup executable.
     * 
     * @return
     */
    private static File getRdiffbackupLocation() {
        return Compat.searchFile(RDIFF_BACKUP, System.getProperty(PROPERTY_RDIFF_BACKUP_LOCATION), "./rdiff-backup-1.2.8/", "./bin/");
    }

    /**
     * Determine the location of ssh executable.
     * 
     * @return ssh location
     */
    private static File getSshLocation() {
        if (SystemUtils.IS_OS_WINDOWS) {
            return Compat.searchFile(SSH, System.getProperty(PROPERTY_SSH_LOCATION), "./openssh-7.6p1-1/", "./bin/");
        }
        // Linux: use system ssh
        return Compat.searchFile(SSH, System.getProperty(PROPERTY_SSH_LOCATION), "/usr/bin/");
    }

    /**
     * The identify file (private key).
     */
    private final File identityFile;

    /**
     * The remote identity.
     */
    private File knownHostsFile;

    /**
     * The remote host (minarca.net)
     */
    private final String remotehost;

    /**
     * Create a new instance of rdiffbackup.
     * 
     * @param remotehost
     *            the remote host (usually minarca.)
     * @param knownHostsFile
     *            the remote identity file (known_hosts file).
     * @param identityPath
     *            location where the identify is stored (should contain id_rsa)
     * @throws APIException
     */
    public RdiffBackup(String remotehost, File knownHostsFile, File identityFile) throws APIException {
        Validate.notEmpty(this.remotehost = remotehost);
        Validate.notNull(this.knownHostsFile = knownHostsFile);
        if (!knownHostsFile.isFile() || !knownHostsFile.canRead()) {
            throw new IdentityMissingException(knownHostsFile);
        }
        Validate.notNull(this.identityFile = identityFile);
        if (!identityFile.isFile() || !identityFile.canRead()) {
            throw new IdentityMissingException(identityFile);
        }
    }

    /**
     * Run the backup with rdiff-backup.
     * 
     * @param patterns
     *            list of include exclude patterns,
     * @param path
     *            the repository name where to backup. aka the computer name.
     * 
     * @throws APIException
     */
    public void backup(List<GlobPattern> patterns, String path) throws APIException, InterruptedException {
        // On Windows operating system, the computer may have multiple Root
        // (C:\, D:\, etc). To support this scenario, we need to run
        // rdiff-backup multiple time on the same computer. Once for each Root
        // to be backuped (if required).
        for (File root : getActiveRoots(patterns)) {
            // Construct the command line.
            List<String> args = new ArrayList<String>();
            if (SystemUtils.IS_OS_WINDOWS) {
                args.add("--no-hard-links");
                args.add("--exclude-symbolic-links");
                args.add("--create-full-path");
            } else {
                args.add("--exclude-sockets");
            }
            // We are using ZFS compression. No need to compress data ourself.
            args.add("--no-compression");
            for (GlobPattern p : patterns) {
                // Skip the patterns if not matching the given root.
                if (p.isGlobbing() || p.isInRoot(root)) {
                    if (p.isInclude()) {
                        args.add("--include");
                    } else {
                        args.add("--exclude");
                    }
                    args.add(p.value());
                }
            }
            if (SystemUtils.IS_OS_WINDOWS) {
                args.add("--exclude");
                // C:/**
                args.add(root.toString().replace("\\", "/") + "**");
                // Source C:/
                args.add(root.toString().replace("\\", "/"));
            } else {
                args.add("--exclude");
                args.add("/*");
                // Source
                args.add("/");
            }
            // Define the destination
            String dest = path;
            if (SystemUtils.IS_OS_WINDOWS) {
                dest = path + "/" + root.toString().replace("\\", "").replace(":", "");
            }
            // Run command.
            LOGGER.info("start backup");
            rdiffbackup(root, args, dest);
        }
    }

    /**
     * Call the rdiff-backup executable with the given arguments.
     * 
     * @param args
     *            the arguments list.
     * @throws APIException
     */
    private void execute(List<String> command, File workingDir, PromptHandler handler) throws APIException, InterruptedException {
        Validate.notNull(command);
        Validate.isTrue(command.size() > 0);
        LOGGER.debug("executing {}", StringUtils.join(command, " "));
        Process p;
        try {
            // Execute the process.
            ProcessBuilder builder = new ProcessBuilder();
            if (workingDir != null) {
                builder.directory(workingDir);
            }
            p = builder.command(command).redirectErrorStream(true).start();
        } catch (IOException e) {
            LOGGER.warn("fail to create subprocess");
            throw new APIException("fail to create subprocess", e);
        }
        try {
            // Attach stream handle to answer a password when prompted
            StreamHandler sh = new StreamHandler(p, Compat.CHARSET_PROCESS, handler, true);
            // Wait for process to complete
            int returnCode = p.waitFor();
            String output = sh.getOutput();
            // Check for error message.
            if (output.contains("Host key verification failed.")) {
                // OpenSSH error.
                throw new UntrustedHostKey();
            } else if (output.contains("Connection abandoned.")) {
                throw new APIException(sh.getOutput());
            }
            // Check return code,
            if (returnCode != 0) {
                throw new APIException(sh.getOutput());
            }
        } catch (InterruptedException e) {
            LOGGER.warn("rdiff-backup process interrupted", e);
            p.destroy();
            throw new InterruptedException("rdiff-backup process interrupted");
        }
    }

    /**
     * Utility method to start a rdiff-backup process.
     * 
     * @param extraArgs
     * @throws APIException
     */
    private void rdiffbackup(File workingDir, List<String> extraArgs, String path) throws APIException, InterruptedException {
        // Get location of rdiff-backup.
        File rdiffbackup = getRdiffbackupLocation();
        if (rdiffbackup == null) {
            throw new APIException("missing rdiff-backup");
        }
        // Construct the command line.
        List<String> args = new ArrayList<String>();
        args.add(rdiffbackup.toString());
        args.add("-v");
        if (LOGGER.isTraceEnabled()) {
            args.add("9");
        } else if (LOGGER.isDebugEnabled()) {
            args.add("5");
        } else if (LOGGER.isInfoEnabled()) {
            args.add("3");
        } else {
            args.add("0");
        }
        // Define the remote schema for each platform.
        args.add("--remote-schema");
        File ssh = getSshLocation();
        if (ssh == null) throw new SshMissingException();
        String extraOptions = "";
        if (getAcceptHostKey()) extraOptions = "-oStrictHostKeyChecking=no";
        // TASK-1028 make sure to use `-oIdentitiesOnly=yes` to enforce private key authentication.
        // Otherwise if way use keychain or keberos authentication and prompt user for password.
        // Last argument is the command line to be executed. This should be the repository name.
        // minarca-shell will make use if it.
        args.add(String.format(
                "%s %s -oBatchMode=yes -oUserKnownHostsFile='%s' -oIdentitiesOnly=yes -i '%s' %%s %s",
                ssh,
                extraOptions,
                knownHostsFile,
                identityFile,
                path));
        // Add extra args.
        args.addAll(extraArgs);
        // Add remote host.
        args.add("minarca@" + this.remotehost + "::" + path);
        // Execute the command line.
        execute(args, workingDir, null);
    }

    /**
     * Run a self test.
     * 
     * @param path
     *            the repository name to be tested.
     * 
     * @throws APIException
     */
    public void testServer(String path) throws APIException, InterruptedException {
        // Run the test.
        LOGGER.info("test server");
        rdiffbackup(Compat.getRootsPath()[0], Arrays.asList("--test-server"), path);
    }
}
