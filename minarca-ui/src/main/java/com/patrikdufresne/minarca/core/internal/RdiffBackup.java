/*
 * Copyright (C) 2015, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.internal;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.apache.commons.io.IOUtils;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.SystemUtils;
import org.apache.commons.lang3.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.APIException;
import com.patrikdufresne.minarca.core.APIException.IdentityMissingException;
import com.patrikdufresne.minarca.core.APIException.KnownHostsMissingException;
import com.patrikdufresne.minarca.core.APIException.PlinkMissingException;
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
     * Executable name representing plink.
     */
    private static final String PLINK = "plink.exe";
    /**
     * True to accept any host key.
     */
    private static final String PROPERTY_ACCEPT_HOST_KEY = "minarca.accepthostkey";
    /**
     * Property used to define the location of putty. Mainly used for development.
     */
    private static final String PROPERTY_PUTTY_LOCATION = "putty.location";

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
    private static final String SSH = "ssh";

    static {
        if (SystemUtils.IS_OS_WINDOWS) {
            RDIFF_BACKUP = "rdiff-backup.exe";
        } else {
            // Otherwise Linux
            RDIFF_BACKUP = "rdiff-backup";
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
     * Return the location of the known_hosts file to be used for OpenSSH. Create it from ressources if it doesnt
     * exists.
     * 
     * @return
     */
    private static File getKnownHosts() {
        File f = new File(Compat.CONFIG_PATH, "known_hosts");
        if (!f.exists()) {
            try {
                InputStream in = RdiffBackup.class.getResourceAsStream("known_hosts");
                OutputStream out = new FileOutputStream(f);
                IOUtils.copy(in, out);
            } catch (IOException e) {
                // Swallow, nothing we can do here.
                LOGGER.error("fail to create known_hosts file", e);
                return null;
            }
        }
        return f;
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

    /**
     * Determine the location of ssh executable.
     * 
     * @return ssh location
     */
    private static File getSshLocation() {
        return Compat.searchFile(SSH, System.getProperty(PROPERTY_SSH_LOCATION), "/usr/bin/");
    }

    /**
     * The identify file (private key).
     */
    private File identityFile;

    /**
     * The remote host (minarca.net)
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
     * @param identityPath
     *            location where the identify is stored (should contain id_rsa or key.ppk)
     * @throws APIException
     */
    public RdiffBackup(String username, String remotehost, File identityFile) throws APIException {
        Validate.notEmpty(this.username = username);
        Validate.notEmpty(this.remotehost = remotehost);
        Validate.notNull(this.identityFile = identityFile);
        if (!identityFile.isFile() || !identityFile.canRead()) {
            throw new IdentityMissingException(identityFile);
        }
    }

    /**
     * This method is called when the host ssh key must be accepted.
     */
    private void acceptServerKey() throws APIException, InterruptedException {
        if (SystemUtils.IS_OS_WINDOWS) {
            acceptServerKeyPlink();
        }
        // Nothing to do. We use our how known_hosts.
    }

    /**
     * Accept host key for Plink.
     */
    private void acceptServerKeyPlink() throws APIException, InterruptedException {
        // Construct the command line.
        List<String> args = new ArrayList<String>();
        File plink = getPlinkLocation();
        if (plink == null) throw new PlinkMissingException();
        args.add(plink.toString());
        args.add("-2");
        args.add("-i");
        args.add(identityFile.toString());
        // Remote host
        args.add(this.username + "@" + this.remotehost);
        // Command line
        args.add("exit");

        // Create a prompt handle to accept of refused the key according to it's fingerprint.
        PromptHandler handler = new PromptHandler() {

            boolean acceptHostKey = getAcceptHostKey();

            @Override
            public String handle(String prompt) {
                if (prompt.contains("7d:c7:dd:d4:72:22:10:f4:a3:a5:b5:5d:de:2f:83:39")) {
                    acceptHostKey = true;
                } else if (prompt.contains("Store key in cache? (y/n)")) {
                    if (acceptHostKey) {
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
                args.add("--no-acls");
                args.add("--create-full-path");
            } else {
                args.add("--exclude-sockets");
            }
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
            if (output.contains("The server's host key is not cached in the registry.")) {
                // Plink Error.
                throw new UntrustedHostKey();
            } else if (output.contains("Host key verification failed.")) {
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
            LOGGER.warn("rdiff-backup process interupted", e);
            p.destroy();
            throw new InterruptedException("rdiff-backup process interupted");
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
        if (SystemUtils.IS_OS_WINDOWS) {
            File plink = getPlinkLocation();
            if (plink == null) throw new PlinkMissingException();
            args.add(String.format("%s -2 -batch -i \\\"%s\\\" %%s rdiff-backup --server", plink, identityFile));
            // -2 : Force SSHv2
            // batch : avoid user interaction
            // -i : identity file, ssh private key
        } else {
            File ssh = getSshLocation();
            if (ssh == null) throw new SshMissingException();
            File knownhosts = getKnownHosts();
            if (knownhosts == null) throw new KnownHostsMissingException();
            String extraOptions = "";
            if (getAcceptHostKey()) extraOptions = "-oStrictHostKeyChecking=no";
            args.add(
                    String.format(
                            "%s %s -oBatchMode=yes -oUserKnownHostsFile='%s' -i '%s' %%s rdiff-backup --server",
                            ssh,
                            extraOptions,
                            knownhosts,
                            identityFile));
        }
        // Add extra args.
        args.addAll(extraArgs);
        // Add remote host.
        args.add(this.username + "@" + this.remotehost + "::" + path);
        // Execute the command line.
        execute(args, workingDir, null);
    }

    /**
     * Run a self test.
     * 
     * @throws APIException
     */
    public void testServer() throws APIException, InterruptedException {
        // Run the test.
        LOGGER.info("test server");
        try {
            rdiffbackup(Compat.getRootsPath()[0], Arrays.asList("--test-server"), "/");
        } catch (UntrustedHostKey e) {
            // Try to accept the key
            acceptServerKey();
            // Then try to test server again
            rdiffbackup(Compat.getRootsPath()[0], Arrays.asList("--test-server"), "/");
        }

    }
}
