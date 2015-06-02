/*
 * Copyright (c) 2014, Patrik Dufresne Service Logiciel. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.internal;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.Callable;

import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.SystemUtils;
import org.jsoup.helper.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.APIException;

/**
 * Utility class to run rdiffbackup command line.
 * 
 * @author Patrik Dufresne
 * 
 */
public class RdiffBackup {

    private static final String ERROR_CONNECTION_ABANDONED = "Connection abandoned.";

    private static final transient Logger LOGGER = LoggerFactory.getLogger(RdiffBackup.class);

    /**
     * Executable name representing plink.
     */
    private static final String PLINK_EXE = "plink.exe";
    /**
     * Property used to define the location of putty. Mainly used for development.
     */
    private static final String PROPERTY_PUTTY_LOCATION = "putty.location";

    /**
     * Property used to define the location of rdiff-backup.
     */
    private static final String PROPERTY_RDIFF_BACKUP_LOCATION = "putty.location";

    /**
     * Executable name to launch rdiff-backup (for current platform)
     */
    private static final String RDIFF_BACKUP;
    static {
        if (SystemUtils.IS_OS_WINDOWS) {
            RDIFF_BACKUP = "rdiff-backup.exe";
        } else if (SystemUtils.IS_OS_LINUX) {
            RDIFF_BACKUP = "rdiff-backup";
        } else {
            RDIFF_BACKUP = "rdiff-backup";
        }
    }

    /**
     * Registry data (Hardcoded public key).
     */
    private static final String REG_DATA = "0x10001,0xe6a143f2d6946bee9bba486e7ce60a896985d2ab91065b26d9bf0872188540a56e76bf535f825a1e80506ca3c573a84fc590b4b4d75d2934adb4dbabcb55e07d1edb83ab9688fce8523f48f335ef55a1adaf5daba1ac6cf82709ab0d1570a3f67f5c91b4d7a30f7945c6e5f720911d75958413acc0bc6cd09418ee1f332a8466bfe10a31d116faffd51ed066045119708205a799817587bedd150620d71b62d481618eeefe39fbb7d098dddf83e6e163e3c1ef9edf70dcbf641cf1e36386b89c437452df2886d1f2ea3a0ba5aae76a17f9853b28521df7ff0f9920a5e4b74a64b8509050c9e619779f0fc738cd9b30a9262bea307338708ef583726cf68d7d4f";
    /**
     * Registry value (Hardcoded public key)
     */
    private static final String REG_VALUE = "rsa2@22:fente.patrikdufresne.com";

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

    private File identityFile;

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
     * Add minarca host public key to registry.
     * <p>
     * PLink store the known host to registry. Since we are using current user and SYSTEM user to connect to minarca, we
     * need to add the key to both hives.
     * 
     * @throws APIException
     */
    public void addKnownHosts() throws APIException {
        // Add key to SYSTEM user
        OSUtils.reg("add", "HKU\\S-1-5-18\\Software\\SimonTatham\\PuTTY\\SshHostKeys", "/v", REG_VALUE, "/d", REG_DATA, "/f");
        // Add key to current user
        OSUtils.reg("add", "HKCU\\Software\\SimonTatham\\PuTTY\\SshHostKeys", "/v", REG_VALUE, "/d", REG_DATA, "/f");
    }

    /**
     * Run the backup with rdiff-backup.
     * 
     * @throws APIException
     */
    public void backup(File excludes, File includes) throws APIException {
        List<String> args = new ArrayList<String>();
        args.add("-v");
        args.add("5");
        if (SystemUtils.IS_OS_WINDOWS) {
            args.add("--no-hard-links");
            args.add("--exclude-symbolic-links");
            args.add("--no-acls");
            File plink = getPlinkLocation();
            args.add("--remote-schema");
            args.add(plink + " -batch -i '" + identityFile + "' %s rdiff-backup --server");
        } else {
            // TODO I'm questioning the compress here, since rdiff-backup is already compressing everything.
            args.add("--remote-schema");
            args.add("ssh -C -i '" + identityFile + "' %s rdiff-backup --server");
        }
        args.add("--exclude-globbing-filelist");
        args.add(excludes.toString());
        args.add("--include-globbing-filelist");
        args.add(includes.toString());
        if (SystemUtils.IS_OS_WINDOWS) {
            args.add("--exclude");
            args.add("C:/**");
            args.add("C:/");
        } else {
            args.add("--exclude");
            args.add("/*");
            args.add("/");
        }
        args.add(this.username + "@" + this.remotehost + "::" + this.path);
        rdiffbackup(args, new File("/"));
    }

    /**
     * Determine the location of plink.exe.
     * <p>
     * This implementation look into into the follow directory: putty location, local directory,
     */
    private File getPlinkLocation() {
        return OSUtils.getFileLocation(PLINK_EXE, System.getProperty(PROPERTY_PUTTY_LOCATION), "./putty-0.63/", "./bin/");
    }

    /**
     * Determine the location of rdiff-backup executable.
     * 
     * @return
     */
    private File getRdiffbackupLocation() {
        return OSUtils.getFileLocation(RDIFF_BACKUP, System.getProperty(PROPERTY_RDIFF_BACKUP_LOCATION), "./rdiff-backup-1.2.8/", "./bin/");
    }

    /**
     * Call the rdiff-backup executable with the given arguments.
     * 
     * @param args
     *            the arguments list.
     * @throws APIException
     */
    private void rdiffbackup(List<String> args, File wd) throws APIException {
        Validate.notNull(args);

        // Get location of rdiff-backup.
        File rdiffbackup = getRdiffbackupLocation();
        if (rdiffbackup == null) {
            throw new APIException("missing rdiff-backup");
        }
        // Build the command line.
        List<String> command = new ArrayList<String>();
        command.add(rdiffbackup.getAbsolutePath());
        command.addAll(args);

        LOGGER.debug("executing {}", StringUtils.join(command, " "));

        try {
            // Execute the process.
            Process p = new ProcessBuilder().command(command).directory(wd).redirectErrorStream(true).start();
            // Attach stream handle to answer a password when prompted
            StreamHandler sh = new StreamHandler(p);
            sh.start();
            // Wait for process to complete
            int returnCode = p.waitFor();
            String output = sh.getOutput();
            if (returnCode != 0) {
                throw new APIException(sh.getOutput());
            }
            if (output.contains(ERROR_CONNECTION_ABANDONED)) {
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
        List<String> args = new ArrayList<String>();
        args.add("--remote-schema");
        if (SystemUtils.IS_OS_WINDOWS) {
            File plink = getPlinkLocation();
            args.add(plink + " -batch -i '" + identityFile + "' %s rdiff-backup --server");
        } else {
            // TODO I'm questioning the compress here, since rdiff-backup is already compressing everything.
            args.add("ssh -C -i '" + identityFile + "' %s rdiff-backup --server");
        }
        args.add("--test-server");
        args.add(this.username + "@" + this.remotehost + "::" + this.path);
        rdiffbackup(args, new File("/"));
    }

}
