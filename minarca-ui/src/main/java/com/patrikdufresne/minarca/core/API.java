/*
 * Copyright (C) 2015, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core;

import static com.patrikdufresne.minarca.Localized._;

import java.io.File;
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
import java.util.Date;
import java.util.List;
import java.util.Properties;

import org.apache.commons.configuration.ConfigurationException;
import org.apache.commons.configuration.PropertiesConfiguration;
import org.apache.commons.configuration.reloading.FileChangedReloadingStrategy;
import org.apache.commons.io.FileUtils;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.SystemUtils;
import org.apache.commons.lang3.Validate;
import org.apache.commons.logging.impl.NoOpLog;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.APIException.ComputerNameAlreadyInUseException;
import com.patrikdufresne.minarca.core.APIException.LinkComputerException;
import com.patrikdufresne.minarca.core.APIException.MissConfiguredException;
import com.patrikdufresne.minarca.core.APIException.NotConfiguredException;
import com.patrikdufresne.minarca.core.APIException.ScheduleNotFoundException;
import com.patrikdufresne.minarca.core.APIException.UnsupportedOS;
import com.patrikdufresne.minarca.core.internal.Compat;
import com.patrikdufresne.minarca.core.internal.Keygen;
import com.patrikdufresne.minarca.core.internal.RdiffBackup;
import com.patrikdufresne.minarca.core.internal.Scheduler;
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
    protected static final String BASE_URL = System.getProperty("minarca.url", "https://www.minarca.net");

    /**
     * Filename used for configuration file. Notice, this is also read by batch file.
     */
    private static final String FILENAME_CONF = "minarca.properties";

    /**
     * Includes filename.
     */
    private static final String FILENAME_GLOB_PATTERNS = "patterns";

    /**
     * Filename used for configuration file. Notice, this is also read by batch file.
     */
    private static final String FILENAME_STATUS = "status.properties";

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
    private static final String PROPERTY_LAST_DATE = "lastdate";

    /**
     * Property name.
     */
    private static final String PROPERTY_LAST_RESULT = "lastresult";

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
    private static final String REMOTEHOST_DEFAULT = System.getProperty("minarca.remotehost", "minarca.net");

    /**
     * Delay 5 sec.
     */
    private static final int RUNNING_DELAY = 5000;

    /**
     * Used to check if the current running environment is valid. Check supported OS, check permissions, etc. May also
     * check running application version.
     * 
     * @throws APIException
     */
    public static void checkEnv() throws APIException {
        // Check OS and VM version.
        LOGGER.info("{} {} {}", SystemUtils.OS_NAME, SystemUtils.OS_VERSION, SystemUtils.OS_ARCH);
        LOGGER.info("{} (build {}, {})", SystemUtils.JAVA_VM_INFO, SystemUtils.JAVA_VM_VERSION, SystemUtils.JAVA_VM_INFO);
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
     * Reference to file patterns.
     */
    private File globPatternsFile;

    /**
     * Reference to the configuration.
     */
    private PropertiesConfiguration properties;

    /**
     * Reference to the status.
     */
    private PropertiesConfiguration status;

    /**
     * Reference to status file.
     */
    private File statusFile;

    /**
     * Default constructor.
     */
    private API() {
        // Log the default charset
        LoggerFactory.getLogger(API.class).info("using default charset [{}]", Compat.CHARSET_DEFAULT.name());
        LoggerFactory.getLogger(API.class).info("using process charset [{}]", Compat.CHARSET_PROCESS.name());

        this.confFile = new File(Compat.CONFIG_PATH, FILENAME_CONF); // $NON-NLS-1$
        this.globPatternsFile = new File(Compat.CONFIG_PATH, FILENAME_GLOB_PATTERNS); // $NON-NLS-1$
        this.statusFile = new File(Compat.CONFIG_PATH, FILENAME_STATUS); // $NON-NLS-1$

        // Load the configuration
        this.properties = load(this.confFile);
        this.status = load(this.statusFile);
    }

    /**
     * Used to start a backup task.
     * 
     * @throws APIException
     */
    public void backup() throws APIException {

        Thread t = new Thread() {
            @Override
            public void run() {
                try {
                    while (true) {
                        try {
                            setLastStatus(LastResult.RUNNING);
                        } catch (APIException e) {
                            // Nothing to do.
                        }
                        sleep(RUNNING_DELAY);
                    }
                } catch (InterruptedException e) {
                    // Nothing to do.
                }
            }
        };
        t.setDaemon(true);
        t.start();

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

        // Read patterns
        List<GlobPattern> patterns;
        try {
            patterns = GlobPattern.readPatterns(globPatternsFile);
        } catch (IOException e) {
            t.interrupt();
            LOGGER.info("fail to read patterns");
            setLastStatus(LastResult.FAILURE);
            throw new APIException(_("fail to read selective backup settings"), e);
        }
        // Run backup.
        try {
            rdiffbackup.backup(patterns);
            t.interrupt();
            setLastStatus(LastResult.SUCCESS);
            LOGGER.info("backup SUCCESS");
        } catch (Exception e) {
            t.interrupt();
            setLastStatus(LastResult.FAILURE);
            LOGGER.info("backup FAILED", e);
            throw new APIException(_("Backup failed"), e);
        }

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
        // Don't verify patterns. See pdsl/minarca/#105
        // Instead, check if the files exists.
        if (!globPatternsFile.isFile()) {
            throw new MissConfiguredException(_("selective backup settings are missing"));
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
        // Sets the default patterns.
        if (force || getGlobPatterns().isEmpty()) {
            // Remove non-existing non-globing patterns.
            List<GlobPattern> patterns = new ArrayList<GlobPattern>();
            for (GlobPattern p : GlobPattern.DEFAULTS) {
                if (p.isFileExists() || p.isGlobbing()) {
                    patterns.add(p);
                }
            }
            setGlobPatterns(patterns);
        }

        // Delete & create schedule tasks.
        Scheduler scheduler = Scheduler.getInstance();
        if (force || !scheduler.exists()) {
            scheduler.create(Schedule.DAILY);
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
        return this.properties.getString(PROPERTY_COMPUTERNAME);
    }

    /**
     * Return the include patterns used for the backup.
     * 
     * @return the list of pattern.
     */
    public List<GlobPattern> getGlobPatterns() {
        try {
            LOGGER.debug("reading glob patterns from [{}]", globPatternsFile);
            return GlobPattern.readPatterns(globPatternsFile);
        } catch (IOException e) {
            LOGGER.warn("error reading glob patterns", e);
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
     * Retrieve the last result.
     * 
     * @return the last result.
     */
    public LastResult getLastResult() {
        try {
            String value = this.status.getString(PROPERTY_LAST_RESULT);
            if (value == null) {
                return LastResult.HAS_NOT_RUN;
            }
            LastResult result = LastResult.valueOf(value);
            if (LastResult.RUNNING.equals(result)) {
                Date now = new Date();
                Date date = getLastResultDate();
                if (date.getTime() < now.getTime() - (RUNNING_DELAY * 2)) {
                    return LastResult.STALE;
                }
            }
            return result;
        } catch (Exception e) {
            return LastResult.UNKNOWN;
        }
    }

    /**
     * Return the last backup date. (success or failure)
     * 
     * @return
     */
    public Date getLastResultDate() {
        try {
            Long value = status.getLong(PROPERTY_LAST_DATE);
            return new Date(value.longValue());
        } catch (Exception e) {
            return null;
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
        return this.properties.getString(PROPERTY_REMOTEHOST, REMOTEHOST_DEFAULT);
    }

    /**
     * Check if a backup task is running.
     * 
     * @return True if a backup task is running.
     * @throws ScheduleNotFoundException
     * 
     * @throws APIException
     */
    public Schedule getSchedule() throws ScheduleNotFoundException, APIException {
        return Scheduler.getInstance().getSchedule();
    }

    /**
     * Get the username used for the backup (username used to authentication with SSH server).
     * 
     * @return
     */
    public String getUsername() {
        return this.properties.getString(PROPERTY_USERNAME);
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
        setSchedule(Schedule.DAILY);

        // If the backup doesn't exists on the remote server, start an empty initial backup.
        if (!exists) {

            // Empty the include
            setGlobPatterns(Arrays.asList(new GlobPattern(true, Compat.ROOT), new GlobPattern(false, Compat.ROOT + "**")));

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
                LOGGER.warn("io error", e);
            }

            // Check if repository exists.
            if (!exists) {
                // Unset properties
                setUsername(null);
                setComputerName(null);
                setRemotehost(null);
                // Raise error.
                throw new LinkComputerException(_("initial backup is not successful"));
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
     * Load properties.
     * 
     * @throws APIException
     */
    private PropertiesConfiguration load(File file) {
        PropertiesConfiguration properties = new PropertiesConfiguration();
        try {
            LOGGER.debug("reading properties from [{}]", file);
            properties = new PropertiesConfiguration(file);
            properties.setLogger(new NoOpLog());
            properties.setAutoSave(false);
            properties.setReloadingStrategy(new FileChangedReloadingStrategy());
        } catch (ConfigurationException e) {
            LOGGER.warn("can't load properties {}", file);
        }
        return properties;
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
    private void save(File file, Properties properties) throws IOException {
        LOGGER.debug("writing config to [{}]", file);
        Writer writer = Compat.openFileWriter(file, Compat.CHARSET_DEFAULT);
        properties.store(writer, "Copyright (C) 2016 Patrik Dufresne Service Logiciel inc.\r\n"
                + "Minarca backup configuration.\r\n"
                + "Please do not change this configuration file manually.");
        writer.close();
    }

    /**
     * Sets the computer name.
     * 
     * @param value
     * @throws APIException
     */
    public void setComputerName(String value) throws APIException {
        this.properties.setProperty(PROPERTY_COMPUTERNAME, value);
        try {
            this.properties.save();
        } catch (ConfigurationException e) {
            throw new APIException(_("fail to save config"), e);
        }
    }

    /**
     * Sets a new pattern list.
     * 
     * @param patterns
     * @throws APIException
     */
    public void setGlobPatterns(List<GlobPattern> patterns) throws APIException {
        try {
            LOGGER.debug("writing patterns to [{}]", globPatternsFile);
            GlobPattern.writePatterns(globPatternsFile, patterns);
        } catch (IOException e) {
            throw new APIException(_("fail to save config"), e);
        }
    }

    /**
     * Set the last status.
     * 
     * @param state
     *            the right state.
     * @param date
     *            the date
     * @throws APIException
     */
    private void setLastStatus(LastResult state) throws APIException {
        Validate.notNull(state);
        Properties status = new Properties();
        status.setProperty(PROPERTY_LAST_RESULT, state.toString());
        status.setProperty(PROPERTY_LAST_DATE, Long.toString(new Date().getTime()));
        try {
            save(this.statusFile, status);
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
        this.properties.setProperty(PROPERTY_REMOTEHOST, value);
        try {
            this.properties.save();
        } catch (ConfigurationException e) {
            throw new APIException(_("fail to save config"), e);
        }
    }

    /**
     * Reschedule task.
     * 
     * @param schedule
     *            the new schedule.
     */
    public void setSchedule(Schedule schedule) throws APIException {
        Scheduler.getInstance().create(schedule);
    }

    /**
     * Sets the username.
     * 
     * @param value
     * @throws APIException
     */
    public void setUsername(String value) throws APIException {
        this.properties.setProperty(PROPERTY_USERNAME, value);
        try {
            this.properties.save();
        } catch (ConfigurationException e) {
            throw new APIException(_("fail to save config"), e);
        }
    }

    /**
     * Used to stop a running backup task.
     * 
     * @throws APIException
     * @throws ScheduleNotFoundException
     */
    public void stopBackup() throws ScheduleNotFoundException, APIException {
        Scheduler.getInstance().terminate();
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
