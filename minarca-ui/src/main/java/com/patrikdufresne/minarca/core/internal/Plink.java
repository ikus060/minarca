package com.patrikdufresne.minarca.core.internal;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import org.apache.commons.io.FileUtils;
import org.jsoup.helper.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.API;
import com.patrikdufresne.minarca.core.APIException;

/**
 * Wrapper arround plink command line.
 * <p>
 * This class is intented to hide all the complexity to communicate via ssh:
 * locating plink, authentication, data buffering.
 * 
 * @author ikus060-vm
 * 
 */
public class Plink extends SSH {

    private static final transient Logger LOGGER = LoggerFactory.getLogger(Plink.class);

    /**
     * Property used to define the location of putty. Mainly used for
     * development.
     */
    private static final String PROPERTY_PUTTY_LOCATION = "putty.location";
    /**
     * The remote SSH server.
     */
    private String remoteHost;
    /**
     * The username.
     */
    private String user;
    /**
     * Password for authentication.
     */
    private String password;

    /**
     * Executable name representing plink.
     */
    private static final String PLINK_EXE = "plink.exe";

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
     * Determine the location of plink.exe.
     * <p>
     * This implementation look into into the follow directory: putty location,
     * local directory,
     */
    private File getPlinkLocation() {
        List<String> locations = new ArrayList<String>();
        String value = System.getProperty(PROPERTY_PUTTY_LOCATION);
        if (value != null) {
            locations.add(value);
        }
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
     * Similar to ssh-copy-id command line. This method will send our public key
     * to the ssh server.
     * <p>
     * This operation required the username and password, since the computer is
     * not linked. This is the only operation requiring a password.
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

        // "C:\Program Files (x86)\retinobox\putty-0.63\plink.exe"
        List<String> args = new ArrayList<String>();
        args.add(plink.getAbsolutePath());
        // username@fente.patrikfresne.com
        args.add(this.user + "@" + this.remoteHost);
        // the command to execute remotely.
        // the following is taken from ssh-copy-id
        args.add("umask 077 ; mkdir -p .ssh && echo '" + publickey + "' >> .ssh/authorized_keys");

        try {
            // Execute the process.
            Process p = new ProcessBuilder().command(args).directory(API.getConfigDirFile()).redirectErrorStream(true).start();
            // Attach stream handle to answer a password when prompted
            StreamHandler sh = new StreamHandler(p, password);
            sh.start();
            // Wait for process to complete
            p.waitFor();
        } catch (IOException e) {
            throw new APIException("fail to create subprocess", e);
        } catch (InterruptedException e) {
            // Swallow. Should no happen
            LOGGER.warn("process interupted", e);
        }

    }

}
