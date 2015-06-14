/*
 * Copyright (c) 2014, Patrik Dufresne Service Logiciel. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.internal;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.SystemUtils;
import org.jsoup.helper.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.APIException;

import static com.patrikdufresne.minarca.core.APIException.*;

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
     * Executable name representing plink.
     */
    private static final String PLINK = "plink.exe";
    /**
     * Property used to define the location of putty. Mainly used for development.
     */
    private static final String PROPERTY_PUTTY_LOCATION = "putty.location";

    /**
     * Property used to define the location of rdiff-backup.
     */
    private static final String PROPERTY_RDIFF_BACKUP_LOCATION = "rdiffbackup.location";

    /**
     * Executable name to launch rdiff-backup (for current platform)
     */
    private static final String RDIFF_BACKUP;
    static {
        if (SystemUtils.IS_OS_WINDOWS) {
            RDIFF_BACKUP = "rdiff-backup.exe";
        } else {
            // Otherwise Linux
            RDIFF_BACKUP = "rdiff-backup";
        }
    }

    /**
     * Determine the location of plink.exe.
     * <p>
     * This implementation look into into the follow directory: putty location, local directory,
     */
    private static File getPlinkLocation() {
        return Compat.searchFile(PLINK, System.getProperty(PROPERTY_PUTTY_LOCATION), "./putty-0.63/", "./bin/");
    }

    /**
     * Determine the location of rdiff-backup executable.
     * 
     * @return
     */
    private static File getRdiffbackupLocation() {
        return Compat.searchFile(RDIFF_BACKUP, System.getProperty(PROPERTY_RDIFF_BACKUP_LOCATION), "./rdiff-backup-1.2.8/", "./bin/");
    }

    private File identityFile;

    /**
     * The computer name to be backup.
     */
    private String path;

    /**
     * The remove host (minarca.net)
     */
    private String remotehost;

    /**
     * The username for authentication.
     */
    private String username;

    /**
     * Create a new instance of rdiffbackup.
     * 
     * @param username
     *            the username for authentication
     * @param remotehost
     *            the remote host (usually minarca.)
     * @param path
     *            the path where to backup file.
     * @param identityPath
     *            location where the identify is stored (should contain id_rsa or key.ppk)
     * @throws APIException
     */
    public RdiffBackup(String username, String remotehost, String path, File identityFile) throws APIException {
        Validate.notEmpty(this.username = username);
        Validate.notEmpty(this.remotehost = remotehost);
        Validate.notEmpty(this.path = path);
        Validate.notNull(this.identityFile = identityFile);
        if (!identityFile.isFile() || !identityFile.canRead()) {
            throw new APIException("invalid identity file: " + identityFile);
        }
    }

    /**
     * This method is called when the host ssh key must be accepted.
     */
    private void acceptServerKey() throws APIException {
        // Construct the command line.
        List<String> args = new ArrayList<String>();
        if (SystemUtils.IS_OS_WINDOWS) {
            File plink = getPlinkLocation();
            if (plink == null) throw new APIException.PlinkMissingException();
            args.add(plink.toString());
            args.add("-2");
            args.add("-i");
            args.add(identityFile.toString());
        } else {
            args.add("ssh");
            args.add("-i");
            args.add(identityFile.toString());
        }
        // Remote host
        args.add(this.username + "@" + this.remotehost);
        // Command line
        args.add("exit");

        // Create a prompt handle to accept of refused the key according to it's fingerprint.
        PromptHandler handler = new PromptHandler() {

            boolean accepthostkey = false;

            @Override
            public String handle(String prompt) {
                if (prompt.contains("ssh-rsa 2048 7d:c7:dd:d4:72:22:10:f4:a3:a5:b5:5d:de:2f:83:39")) {
                    accepthostkey = true;
                } else if (prompt.contains("Store key in cache? (y/n)")) {
                    if (accepthostkey) {
                        LOGGER.info("accepting remote host key");
                        return "y" + SystemUtils.LINE_SEPARATOR;
                    } else {
                        LOGGER.info("refusing remote host key");
                        return "n" + SystemUtils.LINE_SEPARATOR;
                    }
                }
                return null;
            }
        };
        LOGGER.info("try to accept remote host key");
        try {
            execute(args, null, handler);
        } catch (UntrustedHostKey e) {
            // Swallow exception.
        }
    }

    /**
     * Run the backup with rdiff-backup.
     * 
     * @throws APIException
     */
    public void backup(File excludes, File includes) throws APIException {
        // Get location of rdiff-backup.
        File rdiffbackup = getRdiffbackupLocation();
        if (rdiffbackup == null) {
            throw new APIException("missing rdiff-backup");
        }
        // Construct the command line.
        List<String> args = new ArrayList<String>();
        args.add(rdiffbackup.toString());
        args.add("-v");
        args.add("5");
        if (SystemUtils.IS_OS_WINDOWS) {
            args.add("--no-hard-links");
            args.add("--exclude-symbolic-links");
            args.add("--no-acls");
            File plink = getPlinkLocation();
            args.add("--remote-schema");
            args.add(plink + " -2 -batch -i \\\"" + identityFile + "\\\" %s rdiff-backup --server");
        } else {
            args.add("--remote-schema");
            args.add("ssh -i '" + identityFile + "' %s rdiff-backup --server");
        }
        args.add("--exclude-globbing-filelist");
        args.add(excludes.toString());
        args.add("--include-globbing-filelist");
        args.add(includes.toString());
        if (SystemUtils.IS_OS_WINDOWS) {
            args.add("--exclude");
            // C:/**
            args.add(Compat.ROOT.replace("\\", "/") + "**");
            // C:/
            args.add(Compat.ROOT.replace("\\", "/"));
        } else {
            args.add("--exclude");
            args.add("/*");
            args.add("/");
        }
        args.add(this.username + "@" + this.remotehost + "::" + this.path);
        // Run command.
        try {
            LOGGER.info("start backup");
            execute(args, Compat.ROOT_FILE, null);
        } catch (UntrustedHostKey e) {
            // Try to accept the key
            acceptServerKey();
            // Re run the operation
            execute(args, Compat.ROOT_FILE, null);
        }
    }

    /**
     * Call the rdiff-backup executable with the given arguments.
     * 
     * @param args
     *            the arguments list.
     * @throws APIException
     */
    private void execute(List<String> command, File workingDir, PromptHandler handler) throws APIException {
        Validate.notNull(command);
        Validate.isTrue(command.size() > 0);
        LOGGER.debug("executing {}", StringUtils.join(command, " "));
        try {
            // Execute the process.
            ProcessBuilder builder = new ProcessBuilder();
            if (workingDir != null) {
                builder.directory(workingDir);
            }
            Process p = builder.command(command).redirectErrorStream(true).start();
            // Attach stream handle to answer a password when prompted
            StreamHandler sh = new StreamHandler(p, handler);
            sh.start();
            // Wait for process to complete
            int returnCode = p.waitFor();
            String output = sh.getOutput();
            // Check for error message.
            if (output.contains("The server's host key is not cached in the registry.")) {
                throw new UntrustedHostKey();
            } else if (output.contains("Connection abandoned.")) {
                throw new APIException(sh.getOutput());
            }
            // Check return code,
            if (returnCode != 0) {
                throw new APIException(sh.getOutput());
            }
        } catch (IOException e) {
            throw new APIException("fail to create subprocess", e);
        } catch (InterruptedException e) {
            // Swallow. Should not happen
            LOGGER.warn("process interupted", e);
        }
    }

    /**
     * Run a self test.
     * 
     * @throws APIException
     */
    public void testServer() throws APIException {
        // Get location of rdiff-backup.
        File rdiffbackup = getRdiffbackupLocation();
        if (rdiffbackup == null) {
            throw new APIException("missing rdiff-backup");
        }
        // Construct the command line.
        List<String> args = new ArrayList<String>();
        args.add(rdiffbackup.toString());
        args.add("-v");
        args.add("5");
        args.add("--remote-schema");
        if (SystemUtils.IS_OS_WINDOWS) {
            File plink = getPlinkLocation();
            args.add(plink + " -2 -batch -i \\\"" + identityFile + "\\\" %s rdiff-backup --server");
            // -2 : Force SSHv2
            // batch : avoid user interaction
            // -i : identity file, ssh private key
        } else {
            // TODO I'm questioning the compress here, since rdiff-backup is already compressing everything.
            args.add("ssh -C -i '" + identityFile + "' %s rdiff-backup --server");
        }
        args.add("--test-server");
        args.add(this.username + "@" + this.remotehost + "::" + this.path);
        // Run the test.
        try {
            LOGGER.info("test server");
            execute(args, Compat.ROOT_FILE, null);
        } catch (UntrustedHostKey e) {
            // Try to accept the key
            acceptServerKey();
            // Re run the operation
            execute(args, Compat.ROOT_FILE, null);
        }

    }
}
