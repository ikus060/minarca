/*
 * Copyright (C) 2015, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core;

import static com.patrikdufresne.minarca.Localized._;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.Writer;
import java.security.InvalidKeyException;
import java.security.KeyPair;
import java.security.NoSuchAlgorithmException;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.InvalidKeySpecException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Properties;

import org.apache.commons.io.FileUtils;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.SystemUtils;
import org.jsoup.helper.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.APIException.ComputerNameAlreadyInUseException;
import com.patrikdufresne.minarca.core.APIException.LinkComputerException;
import com.patrikdufresne.minarca.core.APIException.MissConfiguredException;
import com.patrikdufresne.minarca.core.APIException.NotConfiguredException;
import com.patrikdufresne.minarca.core.APIException.UnsupportedOS;
import com.patrikdufresne.minarca.core.internal.Compat;
import com.patrikdufresne.minarca.core.internal.Keygen;
import com.patrikdufresne.minarca.core.internal.RdiffBackup;
import com.patrikdufresne.minarca.core.internal.Scheduler;
import com.patrikdufresne.minarca.core.internal.SchedulerTask;
import com.patrikdufresne.minarca.core.internal.SchedulerTask.Schedule;
import com.patrikdufresne.rdiffweb.core.Client;
import com.patrikdufresne.rdiffweb.core.RdiffwebException;

/**
 * This class is the main entry point to do everything related to minarca.
 * 
 * @author Patrik Dufresne
 * 
 */
public class API {

    /**
     * Base URL.
     */
    protected static final String BASE_URL = "https://www.minarca.net";

    /**
     * Filename used for configuration file. Notice, this is also read by batch file.
     */
    private static final String FILENAME_CONF = "minarca.properties";

    /**
     * Exclude filename.
     */
    private static final String FILENAME_EXCLUDES = "excludes";

    /**
     * Includes filename.
     */
    private static final String FILENAME_INCLUDES = "includes";

    /**
     * Singleton instance of API
     */
    private static API instance;

    /**
     * The logger.
     */
    private static final transient Logger LOGGER = LoggerFactory.getLogger(API.class);

    /**
     * Property name.
     */
    private static final String PROPERTY_COMPUTERNAME = "computername";

    /**
     * Property name.
     */
    private static final String PROPERTY_REMOTEHOST = "remotehost";

    /**
     * Property name.
     */
    private static final String PROPERTY_USERNAME = "username";

    /**
     * The remote host.
     */
    private static final String REMOTEHOST_DEFAULT = "minarca.net";

    /**
     * Used to check if the current running environment is valid. Check supported OS, check permissions, etc. May also
     * check running application version.
     * 
     * @throws APIException
     */
    public static void checkEnv() throws APIException {
        // Check OS
        if (!(SystemUtils.IS_OS_WINDOWS || SystemUtils.IS_OS_LINUX)) {
            LOGGER.warn("unsupported OS");
            throw new UnsupportedOS();
        }
        // TODO: Windows XP required Admin previledge.
        // Check user permission
        // if (!Compat.IS_ADMIN) {
        // LOGGER.warn("user is not admin");
        // throw new UnsufficientPermissons();
        // }
    }

    /**
     * Return the single instance of API.
     * 
     * @return
     */
    public static API instance() {
        if (instance == null) {
            instance = new API();
        }
        return instance;
    }

    /**
     * Reference to the configuration file.
     */
    private File confFile;

    /**
     * Reference to exclude file list.
     */
    private File excludesFile;

    /**
     * Reference to include file list.
     */
    private File includesFile;

    /**
     * Reference to the configuration.
     */
    private Properties properties;

    /**
     * Default constructor.
     */
    private API() {
        // Log the default charset
        LoggerFactory.getLogger(API.class).info("using default charset [{}]", Compat.CHARSET_DEFAULT.name());
        LoggerFactory.getLogger(API.class).info("using process charset [{}]", Compat.CHARSET_PROCESS.name());

        this.confFile = new File(Compat.CONFIG_PATH, FILENAME_CONF); // $NON-NLS-1$
        this.includesFile = new File(Compat.CONFIG_PATH, FILENAME_INCLUDES); // $NON-NLS-1$
        this.excludesFile = new File(Compat.CONFIG_PATH, FILENAME_EXCLUDES); // $NON-NLS-1$

        // Load the configuration
        this.properties = new Properties();
        try {
            LoggerFactory.getLogger(API.class).debug("reading config from [{}]", confFile);
            FileInputStream in = new FileInputStream(confFile);
            this.properties.load(in);
            in.close();
        } catch (IOException e) {
            LoggerFactory.getLogger(API.class).warn("can't load properties {}", confFile);
        }
    }

    /**
     * Used to start a backup task.
     * 
     * @throws APIException
     */
    public void backup() throws APIException {

        // Get the config value.
        String username = this.getUsername();
        String remotehost = this.getRemotehost();
        String computerName = this.getComputerName();

        // Compute the path.
        String path = "/home/" + username + "/" + computerName;

        // Get reference to the identity file to be used by ssh or plink.
        File identityFile = getIdentityFile();

        // Create a new instance of rdiff backup to test and run the backup.
        RdiffBackup rdiffbackup = new RdiffBackup(username, remotehost, path, identityFile);

        // Check the remote server.
        rdiffbackup.testServer();

        // Run backup.
        rdiffbackup.backup(excludesFile, includesFile);

        // TODO If it's our first backup for this computer, we need to refresh the repository list.

    }

    /**
     * Used to check if the configuration is OK. Called as a sanity check to make sure "minarca" is properly configured.
     * If not, it throw an exception.
     * 
     * @return
     */
    public void checkConfig() throws APIException {
        // Basic sanity check to make sure it's configured. If not, display the
        // setup dialog.
        if (StringUtils.isEmpty(getComputerName()) || StringUtils.isEmpty(getUsername())) {
            throw new NotConfiguredException(_("Minarca is not configured"));
        }
        // NOTICE: remotehosts is optional.
        // Check if SSH keys exists.
        File identityFile = getIdentityFile();
        if (!identityFile.isFile() || !identityFile.canRead()) {
            throw new NotConfiguredException(_("identity file doesn't exists or is not accessible"));
        }
        if (getIncludes().isEmpty() || getExcludes().isEmpty()) {
            throw new MissConfiguredException(_("includes or excludes pattern are missing"));
        }
    }

    /**
     * Establish connection to minarca web service.
     * 
     * @return a new client instance
     * 
     * @throws APIException
     *             if the connection can't be established.
     */
    public Client connect(String username, String password) throws APIException, IOException {
        // Create a new client instance.
        Client client = new Client(API.BASE_URL, username, password);

        // TODO Check version
        // client.getCurrentVersion();

        // Check connectivity
        try {
            client.check();
        } catch (RdiffwebException e) {
            LOGGER.error("connectivity check failed", e);
            throw new APIException(e.getMessage(), e);
        }

        return client;
    }

    /**
     * This method is called to sets the default configuration for includes, excludes and scheduled task.
     * 
     * @param force
     *            True to force setting the default. Otherwise, only set to default missing configuration.
     * @throws APIException
     */
    public void defaultConfig(boolean force) throws APIException {
        LOGGER.debug("restore default config");
        // Sets the default includes / excludes.
        if (force || getIncludes().isEmpty()) {
            List<GlobPattern> includes = new ArrayList<GlobPattern>();
            includes.addAll(GlobPattern.getDesktopPatterns());
            includes.addAll(GlobPattern.getDocumentsPatterns());
            includes.addAll(GlobPattern.getMusicPatterns());
            includes.addAll(GlobPattern.getPicturesPatterns());
            includes.addAll(GlobPattern.getVideosPatterns());
            setIncludes(includes);
        }
        if (force || getExcludes().isEmpty()) {
            List<GlobPattern> excludes = new ArrayList<GlobPattern>();
            excludes.addAll(GlobPattern.getOsPatterns());
            excludes.addAll(GlobPattern.getDownloadsPatterns());
            setExcludes(excludes);
        }

        // Delete & create schedule tasks.
        Scheduler scheduler = Scheduler.getInstance();
        if (force || !scheduler.exists()) {
            scheduler.create(SchedulerTask.Schedule.DAILY);
        }
    }

    /**
     * Return default browse URL for the current computer.
     * 
     * @return
     */
    public String getBrowseUrl() {
        return BASE_URL + "/browse/" + getComputerName();
    }

    /**
     * Friently named used to represent the computer being backuped.
     * 
     * @return the computer name.
     */
    public String getComputerName() {
        return this.properties.getProperty(PROPERTY_COMPUTERNAME);
    }

    /**
     * Return the exclude patterns used for the backup.
     * 
     * @return the list of pattern.
     */
    public List<GlobPattern> getExcludes() {
        try {
            LOGGER.debug("reading excludes from [{}]", excludesFile);
            return GlobPattern.readPatterns(excludesFile);
        } catch (IOException e) {
            LOGGER.warn("error reading excludes patterns", e);
            return Collections.emptyList();
        }
    }

    /**
     * Return the location of the identify file.
     * 
     * @return the identity file.
     */
    private File getIdentityFile() {
        if (SystemUtils.IS_OS_WINDOWS) {
            return new File(Compat.CONFIG_PATH, "key.ppk");
        }
        return new File(Compat.CONFIG_PATH, "id_rsa");
    }

    /**
     * Generate a finger print from id_rsa file.
     * 
     * @return the finger print.
     * @throws APIException
     */
    public String getIdentityFingerPrint() {
        File file = new File(Compat.CONFIG_PATH, "id_rsa.pub");
        if (!file.isFile() || !file.canRead()) {
            LOGGER.warn("public key [{}] is not accessible", file);
            return "";
        }
        try {
            RSAPublicKey publicKey = Keygen.fromPublicIdRsa(file);
            return Keygen.getFingerPrint(publicKey);
        } catch (InvalidKeySpecException | NoSuchAlgorithmException | IOException e) {
            LOGGER.warn("cannot read key [{}] ", file, e);
        }
        return "";
    }

    /**
     * Return the include patterns used for the backup.
     * 
     * @return the list of pattern.
     */
    public List<GlobPattern> getIncludes() {
        try {
            LOGGER.debug("reading includes from [{}]", includesFile);
            return GlobPattern.readPatterns(includesFile);
        } catch (IOException e) {
            LOGGER.warn("error reading includes patterns", e);
            return Collections.emptyList();
        }
    }

    /**
     * Return the remote host to be used for SSH communication.
     * <p>
     * Current implementation return the same SSH server. In future, this implementation might changed to request the
     * web server for a specific URL.
     * 
     * @return
     */
    protected String getRemotehost() {
        return this.properties.getProperty(PROPERTY_REMOTEHOST, REMOTEHOST_DEFAULT);
    }

    /**
     * Check if a backup task is running.
     * 
     * @return True if a backup task is running.
     * 
     * @throws APIException
     */
    public SchedulerTask getSchedulerTask() throws APIException {
        return Scheduler.getInstance().info();
    }

    /**
     * Get the username used for the backup (username used to authentication with SSH server).
     * 
     * @return
     */
    public String getUsername() {
        return this.properties.getProperty(PROPERTY_USERNAME);
    }

    /**
     * Register a new computer.
     * <p>
     * A successful link of this computer will generate a new configuration file.
     * <p>
     * This implementation will generate public and private keys for putty. The public key will be sent to minarca. The
     * computer name is added to the comments.
     * 
     * 
     * @param computername
     *            friendly name to represent this computer.
     * @param client
     *            reference to web client
     * @param force
     *            True to force usage of existing computer name.
     * @throws APIException
     *             if the keys can't be created.
     * @throws InterruptedException
     * @throws IllegalAccessException
     *             if the computer name is not valid.
     */
    public void link(String computername, Client client, boolean force) throws APIException, InterruptedException {
        Validate.notEmpty(computername);
        Validate.notNull(client);
        Validate.isTrue(computername.matches("[a-zA-Z][a-zA-Z0-9\\-\\.]*"));

        /*
         * Check if computer name is already in uses.
         */
        boolean exists = false;
        try {
            exists = client.getRepositoryInfo(computername) != null;
            if (!force && exists) {
                throw new ComputerNameAlreadyInUseException(computername);
            }
        } catch (IOException e) {
            throw new LinkComputerException(e);
        }

        /*
         * Generate the keys
         */
        LOGGER.debug("generating public and private key for {}", computername);
        File idrsaFile = new File(Compat.CONFIG_PATH, "id_rsa.pub");
        File identityFile = new File(Compat.CONFIG_PATH, "id_rsa");
        File puttyFile = new File(Compat.CONFIG_PATH, "key.ppk");
        String rsadata = null;
        try {
            // Generate a key pair.
            KeyPair pair = Keygen.generateRSA();
            // Generate a simple id_rsa.pub file.
            Keygen.toPublicIdRsa((RSAPublicKey) pair.getPublic(), computername, idrsaFile);
            // Generate a private key file.
            Keygen.toPrivatePEM((RSAPrivateKey) pair.getPrivate(), identityFile);
            // Generate a Putty private key file.
            Keygen.toPrivatePuttyKey(pair, computername, puttyFile);
            // Read RSA pub key.
            rsadata = FileUtils.readFileToString(idrsaFile);
        } catch (NoSuchAlgorithmException e) {
            throw new LinkComputerException(_("fail to generate the keys"), e);
        } catch (IOException e) {
            throw new LinkComputerException(_("fail to generate the keys"), e);
        } catch (InvalidKeyException e) {
            throw new LinkComputerException(_("fail to generate the keys"), e);
        }

        // Send SSH key to minarca server using web service.
        try {
            client.addSSHKey(computername, rsadata);
        } catch (IOException e) {
            throw new LinkComputerException(_("fail to send SSH key to Minarca"), e);
        }

        // Generate configuration file.
        LOGGER.debug("saving configuration [{}][{}][{}]", computername, client.getUsername(), getRemotehost());
        setUsername(client.getUsername());
        setComputerName(computername);
        setRemotehost(getRemotehost());

        // Create default schedule
        scheduleTask(Schedule.DAILY);

        // If the backup doesn't exists on the remote server, start an empty initial backup.
        if (!exists) {

            // Empty the include
            setIncludes(Arrays.asList(new GlobPattern(Compat.ROOT)));
            setExcludes(Arrays.asList(new GlobPattern(Compat.ROOT + "**")));

            // Run backup
            runBackup();

            // Refresh list of repositories (30sec)
            try {
                int attempt = 30;
                do {
                    Thread.sleep(1000);
                    attempt--;
                    client.updateRepositories();
                } while (attempt > 0 && !(exists = (client.getRepositoryInfo(computername) != null)));
            } catch (IOException e) {
                throw new LinkComputerException(e);
            }

            // Check if repository exists.
            if (!exists) {
                throw new LinkComputerException();
            }

            // Set encoding
            try {
                LOGGER.debug("updating repository [{}] encoding [{}]", computername, Compat.CHARSET_DEFAULT.toString());
                client.getRepositoryInfo(computername).setEncoding(Compat.CHARSET_DEFAULT.toString());
            } catch (Exception e) {
                LOGGER.warn("fail to configure repository encoding", e);
            }
        }
    }

    /**
     * Used to asynchronously start the backup process. This operation usually used the system scheduler to run the
     * backup task in background.
     * 
     * @throws APIException
     */
    public void runBackup() throws APIException {
        Scheduler.getInstance().run();
    }

    /**
     * Used to persist the configuration.
     * 
     * @throws IOException
     */
    private void save() throws IOException {
        LOGGER.debug("writing config to [{}]", confFile);
        Writer writer = Compat.openFileWriter(confFile, Compat.CHARSET_DEFAULT);
        this.properties.store(writer, "Copyright (C) 2015 Patrik Dufresne Service Logiciel inc.\r\n"
                + "Minarca backup configuration.\r\n"
                + "Please do not change this configuration file manually.");
        writer.close();
    }

    /**
     * Reschedule task.
     * 
     * @param schedule
     *            the new schedule.
     */
    public void scheduleTask(Schedule schedule) throws APIException {
        Scheduler.getInstance().create(schedule);
    }

    /**
     * Sets the computer name.
     * 
     * @param value
     * @throws APIException
     */
    public void setComputerName(String value) throws APIException {
        if (value == null) {
            this.properties.remove(PROPERTY_COMPUTERNAME);
        } else {
            this.properties.setProperty(PROPERTY_COMPUTERNAME, value);
        }
        try {
            save();
        } catch (IOException e) {
            throw new APIException(_("fail to save config"), e);
        }
    }

    /**
     * Sets a new exclude patern list.
     * 
     * @param patterns
     * @throws APIException
     */
    public void setExcludes(List<GlobPattern> patterns) throws APIException {
        try {
            LOGGER.debug("writing excludes to [{}]", excludesFile);
            GlobPattern.writePatterns(excludesFile, patterns);
        } catch (IOException e) {
            throw new APIException(_("fail to save config"), e);
        }
    }

    /**
     * Sets a new include pattern list.
     * 
     * @param patterns
     * @throws APIException
     */
    public void setIncludes(List<GlobPattern> patterns) throws APIException {
        try {
            LOGGER.debug("writing includes to [{}]", includesFile);
            GlobPattern.writePatterns(includesFile, patterns);
        } catch (IOException e) {
            throw new APIException(_("fail to save config"), e);
        }
    }

    /**
     * Sets remote host.
     * 
     * @param value
     * @throws APIException
     */
    public void setRemotehost(String value) throws APIException {
        if (value == null || value.equals(REMOTEHOST_DEFAULT)) {
            this.properties.remove(PROPERTY_REMOTEHOST);
        } else {
            this.properties.setProperty(PROPERTY_REMOTEHOST, value);
        }
        try {
            save();
        } catch (IOException e) {
            throw new APIException(_("fail to save config"), e);
        }
    }

    /**
     * Sets the username.
     * 
     * @param value
     * @throws APIException
     */
    public void setUsername(String value) throws APIException {
        if (value == null) {
            this.properties.remove(PROPERTY_USERNAME);
        } else {
            this.properties.setProperty(PROPERTY_USERNAME, value);
        }
        try {
            save();
        } catch (IOException e) {
            throw new APIException(_("fail to save config"), e);
        }
    }

    /**
     * Check if this computer is properly link to minarca.net.
     * 
     * @throws APIException
     */
    public void testServer() throws APIException {

        // Get the config value.
        String username = this.getUsername();
        String remotehost = this.getRemotehost();
        String computerName = this.getComputerName();

        // Compute the path.
        String path = "/home/" + username + "/" + computerName;

        // Get reference to the identity file to be used by ssh or plink.
        File identityFile = getIdentityFile();

        // Create a new instance of rdiff backup to test and run the backup.
        RdiffBackup rdiffbackup = new RdiffBackup(username, remotehost, path, identityFile);

        // Check the remote server.
        rdiffbackup.testServer();

    }

    /**
     * Used to unlink this computer.
     * 
     * @throws APIException
     */
    public void unlink() throws APIException {
        // To unlink, delete the configuration and schedule task.
        setComputerName(null);
        setUsername(null);
        setRemotehost(null);

        // TODO Remove RSA keys

        // TODO Remove RSA key from client too.

        // Delete task
        Scheduler scheduler = Scheduler.getInstance();
        scheduler.delete();
    }
}
