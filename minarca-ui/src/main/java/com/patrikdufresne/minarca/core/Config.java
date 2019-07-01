package com.patrikdufresne.minarca.core;

import static com.patrikdufresne.minarca.Localized._;

import java.io.File;
import java.io.IOException;
import java.io.Writer;
import java.security.NoSuchAlgorithmException;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.InvalidKeySpecException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.List;
import java.util.Properties;

import org.apache.commons.configuration.ConfigurationException;
import org.apache.commons.configuration.PropertiesConfiguration;
import org.apache.commons.configuration.reloading.FileChangedReloadingStrategy;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.Validate;
import org.apache.commons.logging.impl.NoOpLog;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.Main;
import com.patrikdufresne.minarca.core.APIException.MissConfiguredException;
import com.patrikdufresne.minarca.core.APIException.NotConfiguredException;
import com.patrikdufresne.minarca.core.internal.Compat;
import com.patrikdufresne.minarca.core.internal.Keygen;
import com.patrikdufresne.minarca.core.internal.Scheduler;

/**
 * Class responsible to fetch and return configuration for the API.
 * 
 * @author Patrik Dufresne
 * 
 */
public class Config {

    /**
     * Filename used for configuration file. Notice, this is also read by batch file.
     */
    private static final String FILENAME_CONF = "minarca.properties";

    /**
     * Includes filename.
     */
    private static final String FILENAME_GLOB_PATTERNS = "patterns";;

    /**
     * Filename used for configuration file. Notice, this is also read by batch file.
     */
    private static final String FILENAME_STATUS = "status.properties";

    private static final transient Logger LOGGER = LoggerFactory.getLogger(Config.class);

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
    private static final String PROPERTY_LAST_SUCCESS = "lastsuccess";

    /**
     * Property name.
     */
    private static final String PROPERTY_REMOTEHOST = "remotehost";

    /**
     * Property name.
     */
    private static final String PROPERTY_REMOTEURL = "remoteurl";

    /**
     * Property name.
     */
    private static final String PROPERTY_REPOSITORY_NAME = "repositoryname";

    /**
     * Property name.
     */
    private static final String PROPERTY_SCHEDULE = "schedule";

    /**
     * Property name.
     */
    private static final String PROPERTY_USERNAME = "username";

    /**
     * Load properties.
     * 
     * @throws ConfigurationException
     * 
     * @throws APIException
     */
    private static PropertiesConfiguration load(File file) throws ConfigurationException {
        PropertiesConfiguration properties = new PropertiesConfiguration();
        properties = new PropertiesConfiguration(file);
        properties.setLogger(new NoOpLog());
        properties.setAutoSave(false);
        properties.setReloadingStrategy(new FileChangedReloadingStrategy());
        return properties;
    }

    /**
     * Reference to the configuration file.
     */
    private File confFile;

    /**
     * Reference to file patterns.
     */
    private File globPatternsFile;

    private List<GlobPattern> patterns = Collections.emptyList();

    /**
     * Reference to the configuration.
     */
    private PropertiesConfiguration properties;

    /**
     * Reference to the status.
     */
    protected PropertiesConfiguration status;

    /**
     * Reference to status file.
     */
    protected File statusFile;

    public Config() {
        this.confFile = new File(Compat.CONFIG_HOME, FILENAME_CONF); // $NON-NLS-1$
        this.globPatternsFile = new File(Compat.CONFIG_HOME, FILENAME_GLOB_PATTERNS); // $NON-NLS-1$
        this.statusFile = new File(Compat.DATA_HOME, FILENAME_STATUS); // $NON-NLS-1$
        // Load the configuration
        load();
    }

    /**
     * Return the remote URL to Minarca server.
     * 
     * @return
     */
    public String getBaseUrl() {
        return this.properties.getString(PROPERTY_REMOTEURL);
    }

    /**
     * Return the include patterns used for the backup.
     * 
     * @return the list of pattern.
     */
    public List<GlobPattern> getGlobPatterns() {
        return this.patterns;
    }

    public File getGlobPatternsFile() {
        return globPatternsFile;
    }

    /**
     * Generate a finger print from id_rsa file.
     * 
     * @return the finger print.
     * @throws APIException
     */
    public String getIdentityFingerPrint() {
        File file = getPublicKeyFile();
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
     * Return the location of the known_hosts file to be used for OpenSSH.
     * 
     * @return
     */
    public File getKnownHosts() {
        return new File(Compat.CONFIG_HOME, "known_hosts");
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
                if (date.getTime() < now.getTime() - (API.RUNNING_DELAY * 2)) {
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
     * Return the last successful backup date.
     * 
     * @return Date of last success or null.
     */
    public Date getLastSuccess() {
        try {
            Long value = status.getLong(PROPERTY_LAST_SUCCESS);
            return new Date(value.longValue());
        } catch (Exception e) {
            return null;
        }
    }

    /**
     * Return the location of the identify file.
     * 
     * @return the identity file.
     */
    protected File getPrivateKeyFile() {
        return new File(Compat.CONFIG_HOME, "id_rsa");
    }

    /**
     * Return the location of the public key.
     * 
     * @return
     */
    protected File getPublicKeyFile() {
        return new File(Compat.CONFIG_HOME, "id_rsa.pub");
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
        return this.properties.getString(PROPERTY_REMOTEHOST);
    }

    /**
     * Friendly named used to represent the repository being backup.
     * 
     * @return the repository name.
     */
    public String getRepositoryName() {
        return this.properties.getString(PROPERTY_REPOSITORY_NAME);
    }

    /**
     * Get the scheduling preferences.
     * 
     * @return The schedule
     * 
     */
    public Schedule getSchedule() {
        try {
            return Schedule.valueOf(this.properties.getString(PROPERTY_SCHEDULE));
        } catch (Exception e) {
            return Schedule.DAILY;
        }
    }

    /**
     * Get the username used for the backup (username used to authentication with SSH server).
     * 
     * @return
     */
    public String getUsername() {
        return this.properties.getString(PROPERTY_USERNAME);
    }

    public void load() {
        LOGGER.debug("reading properties from [{}]", this.confFile);
        try {
            this.properties = load(this.confFile);
        } catch (ConfigurationException e1) {
            LOGGER.warn("can't load properties {}", this.confFile);
        }
        LOGGER.debug("reading properties from [{}]", this.statusFile);
        try {
            this.status = load(this.statusFile);
        } catch (ConfigurationException e1) {
            LOGGER.warn("can't load properties {}", this.confFile);
        }
        LOGGER.debug("reading glob patterns from [{}]", this.globPatternsFile);
        try {
            this.patterns = GlobPattern.readPatterns(this.globPatternsFile);
        } catch (IOException e) {
            LOGGER.warn("can't glob patterns from {}", this.confFile);
        }
    }

    /**
     * Save all the configuration.
     * 
     * @throws APIException
     */
    public void save() throws APIException {
        try {
            this.properties.save();
        } catch (ConfigurationException e) {
            throw new APIException(_("fail to save config"), e);
        }
        try {
            LOGGER.debug("writing patterns to [{}]", globPatternsFile);
            GlobPattern.writePatterns(globPatternsFile, patterns);
        } catch (IOException e) {
            throw new APIException(_("fail to save config"), e);
        }
    }

    /**
     * Used to persist the configuration.
     * 
     * @throws IOException
     */
    private void save(File file, Properties properties) throws IOException {
        LOGGER.trace("writing config to [{}]", file);
        Writer writer = Compat.openFileWriter(file, Compat.CHARSET_DEFAULT);
        properties.store(writer, Main.getCopyrightText() + "\r\nMinarca backup configuration.\r\n" + "Please do not change this configuration file manually.");
        writer.close();
    }

    /**
     * Sets a new pattern list.
     * 
     * @param patterns
     * @throws APIException
     */
    public void setGlobPatterns(List<GlobPattern> patterns, boolean save) throws APIException {
        Validate.notNull(patterns);
        this.patterns = new ArrayList<>(patterns);
        if (save) save();
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
    protected void setLastStatus(LastResult state) throws APIException {
        Validate.notNull(state);
        Properties newStatus = new Properties();
        String now = Long.toString(new Date().getTime());
        newStatus.setProperty(PROPERTY_LAST_RESULT, state.toString());
        newStatus.setProperty(PROPERTY_LAST_DATE, now);
        if (LastResult.SUCCESS.equals(state)) {
            newStatus.setProperty(PROPERTY_LAST_SUCCESS, now);
        } else {
            Date d = getLastSuccess();
            if (d != null) {
                newStatus.setProperty(PROPERTY_LAST_SUCCESS, Long.toString(d.getTime()));
            }
        }
        try {
            save(this.statusFile, newStatus);
        } catch (IOException e) {
            throw new APIException(_("fail to save config"), e);
        }
        // Finally reload the status file.
        try {
            status.refresh();
        } catch (ConfigurationException e) {
            throw new APIException(_("fail to refresh config"), e);
        }
    }

    /**
     * Sets remote host.
     * 
     * @param value
     * @throws APIException
     */
    public void setRemotehost(String value, boolean save) throws APIException {
        this.properties.setProperty(PROPERTY_REMOTEHOST, value);
        if (save) save();
    }

    /**
     * Sets the repository name.
     * 
     * @param value
     * @throws APIException
     */
    public void setRepositoryName(String value, boolean save) throws APIException {
        this.properties.setProperty(PROPERTY_REPOSITORY_NAME, value);
        if (save) save();
    }

    /**
     * Define the scheduling preferences.
     * 
     * @param schedule
     *            the new schedule.
     */
    public void setSchedule(Schedule schedule, boolean save) throws APIException {
        Validate.notNull(schedule);
        this.properties.setProperty(PROPERTY_SCHEDULE, schedule.toString());
        if (save) save();
    }

    /**
     * Sets the username.
     * 
     * @param value
     * @throws APIException
     */
    public void setUsername(String value, boolean save) throws APIException {
        this.properties.setProperty(PROPERTY_USERNAME, value);
        if (save) save();
    }

}
