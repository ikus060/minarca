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

import org.apache.commons.io.FileUtils;
import org.apache.commons.lang3.StringUtils;
import org.jsoup.helper.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.API;
import com.patrikdufresne.minarca.core.APIException;

/**
 * Wrapper around plink command line.
 * <p>
 * This class is intended to hide all the complexity to communicate via ssh: locating plink, authentication, data
 * buffering.
 * 
 * @author Patrik Dufresne
 * 
 */
public class Plink extends SSH {
    /**
     * Known error return by plink.
     */
    private static final String ERROR_CONNECTION_ABANDONED = "Connection abandoned.";

    private static final transient Logger LOGGER = LoggerFactory.getLogger(Plink.class);

    /**
     * Executable name representing plink.
     */
    private static final String PLINK_EXE = "plink.exe";
    /**
     * Property used to define the location of putty. Mainly used for development.
     */
    private static final String PROPERTY_PUTTY_LOCATION = "putty.location";

    /**
     * Registry data (Hardcoded public key).
     */
    private static final String REG_DATA = "0x10001,0xe6a143f2d6946bee9bba486e7ce60a896985d2ab91065b26d9bf0872188540a56e76bf535f825a1e80506ca3c573a84fc590b4b4d75d2934adb4dbabcb55e07d1edb83ab9688fce8523f48f335ef55a1adaf5daba1ac6cf82709ab0d1570a3f67f5c91b4d7a30f7945c6e5f720911d75958413acc0bc6cd09418ee1f332a8466bfe10a31d116faffd51ed066045119708205a799817587bedd150620d71b62d481618eeefe39fbb7d098dddf83e6e163e3c1ef9edf70dcbf641cf1e36386b89c437452df2886d1f2ea3a0ba5aae76a17f9853b28521df7ff0f9920a5e4b74a64b8509050c9e619779f0fc738cd9b30a9262bea307338708ef583726cf68d7d4f";
    /**
     * Registry value (Hardcoded public key)
     */
    private static final String REG_VALUE = "rsa2@22:fente.patrikdufresne.com";

    /**
     * Execute "reg"
     * 
     * @param command
     * @throws APIException
     */
    private static void reg(String... args) throws APIException {
        List<String> command = new ArrayList<String>();
        command.add("reg.exe");
        if (args != null) {
            command.addAll(Arrays.asList(args));
        }
        LOGGER.debug("executing {}", StringUtils.join(command, " "));
        try {
            Process p = new ProcessBuilder().command(command).redirectErrorStream(true).start();
            StreamHandler sh = new StreamHandler(p);
            sh.start();
            if (p.waitFor() != 0) {
                throw new APIException(sh.getOutput());
            }
        } catch (IOException e) {
            throw new APIException("fail to create subprocess", e);
        } catch (InterruptedException e) {
            // Swallow. Should no happen
            LOGGER.warn("process interupted", e);
            Thread.currentThread().interrupt();
        }
    }

    /**
     * Password for authentication.
     */
    private String password;

    /**
     * The remote SSH server.
     */
    private String remoteHost;

    /**
     * The username.
     */
    private String user;

    /**
     * Create a new instance of ssh client.
     * 
     * @param remoteHost
     *            the remove host
     */
    public Plink(String remoteHost, String user, String password) {
        Validate.notNull(this.remoteHost = remoteHost);
        Validate.notNull(this.user = user);
        Validate.notNull(this.password = password);
    }

    /**
     * Add minarca host public key to registry.
     * <p>
     * PLink store the known host to registry. Since we are using current user and SYSTEM user to connect to minarca, we
     * need to add the key to both hives.
     * 
     * @throws APIException
     */
    @Override
    public void addKnownHosts() throws APIException {
        // Add key to SYSTEM user
        reg("add", "HKU\\S-1-5-18\\Software\\SimonTatham\\PuTTY\\SshHostKeys", "/v", REG_VALUE, "/d", REG_DATA, "/f");
        // Add key to current user
        reg("add", "HKCU\\Software\\SimonTatham\\PuTTY\\SshHostKeys", "/v", REG_VALUE, "/d", REG_DATA, "/f");
    }

    /**
     * Determine the location of plink.exe.
     * <p>
     * This implementation look into into the follow directory: putty location, local directory,
     */
    private File getPlinkLocation() {
        List<String> locations = new ArrayList<String>();
        String value = System.getProperty(PROPERTY_PUTTY_LOCATION);
        if (value != null) {
            locations.add(value);
        }
        locations.add("./putty-0.63/");
        locations.add("./bin/");
        locations.add(".");
        for (String location : locations) {
            File plink = new File(location, PLINK_EXE);
            if (plink.isFile() && plink.canRead()) {
                return plink;
            }
        }
        return null;
    }

    /**
     * Similar to ssh-copy-id command line. This method will send our public key to the ssh server.
     * <p>
     * This operation required the username and password, since the computer is not linked. This is the only operation
     * requiring a password.
     * 
     * @param password
     *            the password used to authenticate.
     * @param publicKey
     *            the public key (id_rsa.pub)
     * 
     * @throws APIException
     */
    public void sendPublicKey(File publicKey) throws APIException {
        Validate.notNull(this.password, "password is required for this operation");

        // Read public key
        String publickey;
        try {
            publickey = FileUtils.readFileToString(publicKey);
        } catch (IOException e1) {
            throw new APIException("fail to read public key");
        }

        // Get location of plink.
        File plink = getPlinkLocation();
        if (plink == null) {
            throw new APIException("missing plink");
        }

        // "C:\Program Files (x86)\minarca\putty-0.63\plink.exe"
        List<String> command = new ArrayList<String>();
        command.add(plink.getAbsolutePath());
        // username@fente.patrikfresne.com
        command.add(this.user + "@" + this.remoteHost);
        // the command to execute remotely.
        // the following is taken from ssh-copy-id
        command.add("umask 077 ; mkdir -p .ssh && echo '" + publickey + "' >> .ssh/authorized_keys");
        LOGGER.debug("executing {}", StringUtils.join(command, " "));

        try {
            // Execute the process.
            Process p = new ProcessBuilder().command(command).directory(API.getConfigDirFile()).redirectErrorStream(true).start();
            // Attach stream handle to answer a password when prompted
            StreamHandler sh = new StreamHandler(p, password);
            sh.start();
            // Wait for process to complete
            int returnCode = p.waitFor();
            String output = sh.getOutput();
            if (returnCode != 0 || output.contains(ERROR_CONNECTION_ABANDONED)) {
                throw new APIException(sh.getOutput());
            }
        } catch (IOException e) {
            throw new APIException("fail to create subprocess", e);
        } catch (InterruptedException e) {
            // Swallow. Should no happen
            LOGGER.warn("process interupted", e);
        }

    }
}
