package com.patrikdufresne.minarca.core;

import static com.patrikdufresne.minarca.Localized._;

import java.io.File;
import java.io.IOException;
import java.io.Writer;
import java.security.NoSuchAlgorithmException;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.InvalidKeySpecException;
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
     * The remote host.
     */
    private static final String REMOTEHOST_DEFAULT = System.getProperty("minarca.remotehost", "minarca.net");

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
    protected PropertiesConfiguration status;

    /**
     * Reference to status file.
     */
    protected File statusFile;

    public Config() {
        this.confFile = new File(Compat.CONFIG_PATH, FILENAME_CONF); // $NON-NLS-1$
        this.globPatternsFile = new File(Compat.CONFIG_PATH, FILENAME_GLOB_PATTERNS); // $NON-NLS-1$
        this.statusFile = new File(Compat.CONFIG_PATH, FILENAME_STATUS); // $NON-NLS-1$

        // Load the configuration
        this.properties = load(this.confFile);
        this.status = load(this.statusFile);
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
        if (StringUtils.isEmpty(getRepositoryName()) || StringUtils.isEmpty(getUsername())) {
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
            setGlobPatterns(GlobPattern.DEFAULTS);
        }

        // Delete & create schedule tasks.
        Scheduler scheduler = Scheduler.getInstance();
        if (force || !scheduler.exists()) {
            scheduler.create();
        }
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
    protected File getIdentityFile() {
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
     * Friendly named used to represent the repository being backuped.
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

    /**
     * Load properties.
     * 
     * @throws APIException
     */
    private PropertiesConfiguration load(File file) {
        PropertiesConfiguration properties = new PropertiesConfiguration();
        try {
            LOGGER.trace("reading properties from [{}]", file);
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
    public void setRemotehost(String value) throws APIException {
        this.properties.setProperty(PROPERTY_REMOTEHOST, value);
        try {
            this.properties.save();
        } catch (ConfigurationException e) {
            throw new APIException(_("fail to save config"), e);
        }
    }

    /**
     * Sets the repository name.
     * 
     * @param value
     * @throws APIException
     */
    public void setRepositoryName(String value) throws APIException {
        this.properties.setProperty(PROPERTY_REPOSITORY_NAME, value);
        try {
            this.properties.save();
        } catch (ConfigurationException e) {
            throw new APIException(_("fail to save config"), e);
        }
    }

    /**
     * Define the scheduling preferences.
     * 
     * @param schedule
     *            the new schedule.
     */
    public void setSchedule(Schedule schedule) throws APIException {
        Validate.notNull(schedule);
        this.properties.setProperty(PROPERTY_SCHEDULE, schedule.toString());
        try {
            this.properties.save();
        } catch (ConfigurationException e) {
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
        this.properties.setProperty(PROPERTY_USERNAME, value);
        try {
            this.properties.save();
        } catch (ConfigurationException e) {
            throw new APIException(_("fail to save config"), e);
        }
    }

    public String getBaseUrl() {
        return BASE_URL;
    }

}
